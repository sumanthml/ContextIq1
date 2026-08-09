import json
import re
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import START, END, StateGraph
from app.services.ai_service import groq_client, cohere_client, rerank_documents
from app.core.security import get_tenant_vector_hash
from app.services.vector_store import qdrant_client
from app.services.hybrid_search import bm25_store, reciprocal_rank_fusion
from qdrant_client.http import models

# ==========================================
# 1. State Definition
# ==========================================
class AgentState(TypedDict):
    user_id: str
    query: str
    file_filter: Optional[str]  # Captures active focused document identifier
    optimized_queries: List[str]
    retrieved_documents: List[dict]
    needs_web_fallback: bool
    generation: str

# Helper to detect document-level summary / overview questions
SUMMARY_KEYWORDS = {"summary", "summarize", "overview", "about", "what is this", "what does it say", "explain this", "key points", "main ideas", "content"}

def is_summary_query(prompt: str) -> bool:
    low = prompt.lower()
    return any(kw in low for kw in SUMMARY_KEYWORDS)

# ==========================================
# 2. Graph Node Functions
# ==========================================
def rewrite_query_node(state: AgentState) -> dict:
    """
    Transforms messy user input into clean search query variations.
    """
    print("🔍 Analyzing user query intent & expanding terms...")
    
    system_prompt = (
        "You are a strict backend query conversion engine. Your sole task is to take a raw user search query "
        "and generate a list of optimized keyword variants for a database lookup.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. You MUST respond with a strictly valid JSON object.\n"
        "2. The JSON object MUST contain exactly one key named \"queries\".\n"
        "3. The value of \"queries\" MUST be a clean list array of 2 to 3 strings.\n"
        "4. Do NOT output markdown ticks, explanations, or any other keys."
    )
    
    user_content = f"Convert this query to a valid JSON object with a \"queries\" array: '{state['query']}'"
    
    try:
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        raw_output = chat_completion.choices[0].message.content
        result = json.loads(raw_output)
        queries = result.get("queries", [state["query"]])
        
        if not isinstance(queries, list) or len(queries) == 0:
            queries = [state["query"]]
            
        if state["query"] not in queries:
            queries.insert(0, state["query"])
            
        return {"optimized_queries": queries}
    except Exception as e:
        print(f"⚠️ Query rewriter fallback: {e}")
        return {"optimized_queries": [state["query"]]}

def retrieve_documents_node(state: AgentState) -> dict:
    """
    Performs multi-tenant Hybrid Search (BM25 + Qdrant Vectors) followed by Cohere Reranking.
    """
    print("🗂️ Scanning secure personalized document vault with Hybrid Search + Cohere Reranker...")
    user_id = state["user_id"]
    tenant_hash = get_tenant_vector_hash(user_id)
    active_file = state.get("file_filter", None)
    
    dense_matches = []
    sparse_matches = []
    seen_chunks = set()
    
    # 1. Sparse BM25 Keyword Search
    if active_file and str(active_file).strip() and active_file != "None":
        for target_query in state["optimized_queries"]:
            bm25_hits = bm25_store.search(user_id, active_file, target_query, top_k=5)
            sparse_matches.extend(bm25_hits)
            
    # 2. Dense Vector Search in Qdrant
    for target_query in state["optimized_queries"]:
        try:
            embed_resp = cohere_client.embed(
                texts=[target_query], 
                model="embed-english-v3.0",
                input_type="search_query"
            )
            
            if hasattr(embed_resp.embeddings, "float"):
                vector = embed_resp.embeddings.float[0]
            elif isinstance(embed_resp.embeddings, list):
                vector = embed_resp.embeddings[0]
            else:
                vector = list(embed_resp.embeddings)[0]
            
            must_conditions = [
                models.FieldCondition(key="tenant_owner", match=models.MatchValue(value=tenant_hash))
            ]
            
            if active_file and str(active_file).strip() and active_file != "None":
                must_conditions.append(
                    models.Filter(
                        should=[
                            models.FieldCondition(key="file_name", match=models.MatchValue(value=str(active_file))),
                            models.FieldCondition(key="document_name", match=models.MatchValue(value=str(active_file)))
                        ]
                    )
                )
                
            search_results = qdrant_client.search(
                collection_name="contextiq_knowledge",
                query_vector=vector,
                query_filter=models.Filter(must=must_conditions),
                limit=10
            )
            
            for hit in search_results:
                text = hit.payload.get("text", "").strip()
                doc_name = hit.payload.get("file_name") or hit.payload.get("document_name") or "Workspace_Document"
                if text and text not in seen_chunks:
                    seen_chunks.add(text)
                    dense_matches.append({"text": text, "doc": doc_name})
                    
        except Exception as err:
            print(f"❌ Qdrant vector search warning: {err}")
            continue

    # 🚀 DOCUMENT SUMMARY OVERVIEW FIX: If an active file is focused and prompt is summary-based, fetch all/top file chunks!
    if active_file and is_summary_query(state["query"]):
        print(f"📋 Overview query detected for active file '{active_file}'. Fetching document chunks for summary...")
        try:
            dummy_vector = [0.0] * 1024
            file_chunks = qdrant_client.search(
                collection_name="contextiq_knowledge",
                query_vector=dummy_vector,
                query_filter=models.Filter(must=[
                    models.FieldCondition(key="tenant_owner", match=models.MatchValue(value=tenant_hash)),
                    models.Filter(should=[
                        models.FieldCondition(key="file_name", match=models.MatchValue(value=str(active_file))),
                        models.FieldCondition(key="document_name", match=models.MatchValue(value=str(active_file)))
                    ])
                ]),
                limit=15
            )
            for hit in file_chunks:
                text = hit.payload.get("text", "").strip()
                doc_name = hit.payload.get("file_name") or hit.payload.get("document_name") or str(active_file)
                if text and text not in seen_chunks:
                    seen_chunks.add(text)
                    dense_matches.append({"text": text, "doc": doc_name})
        except Exception as sum_err:
            print(f"⚠️ Document overview chunk fetch warning: {sum_err}")

    # 3. Reciprocal Rank Fusion (RRF)
    hybrid_candidates = reciprocal_rank_fusion(sparse_matches, dense_matches)
    if not hybrid_candidates and dense_matches:
        hybrid_candidates = dense_matches

    # 4. Cohere Cross-Encoder Reranking
    if hybrid_candidates:
        print(f"🎯 Reranking top {len(hybrid_candidates)} candidate chunks with Cohere Cross-Encoder...")
        try:
            final_docs = rerank_documents(state["query"], hybrid_candidates, top_n=5)
        except Exception as rerank_err:
            print(f"⚠️ Cohere rerank warning ({rerank_err}), using top candidate list.")
            final_docs = hybrid_candidates[:5]
    else:
        final_docs = []
        
    print(f"📊 Extraction phase completed. Total refined chunks selected: {len(final_docs)}")
    return {"retrieved_documents": final_docs}

def evaluate_context_node(state: AgentState) -> dict:
    """
    Audits the retrieved context quality.
    """
    print("🧠 Critically grading retrieved context items...")
    active_file = state.get("file_filter", None)
    
    # If active file context is selected and chunks exist, evaluate as valid context!
    if state["retrieved_documents"]:
        if active_file or is_summary_query(state["query"]):
            return {"needs_web_fallback": False}

    if not state["retrieved_documents"]:
        return {"needs_web_fallback": True}
        
    context = "\n".join([f"Content: {d['text']}" for d in state["retrieved_documents"]])
    
    system_prompt = (
        "You are a strict data auditing agent. Review the provided context fragments and decide "
        "if they contain sufficient facts or context to answer or summarize the query.\n"
        "Reply with a simple JSON object containing a boolean key: \"is_relevant\"."
    )
    
    user_content = f"Query: {state['query']}\nContext:\n{context}\n\nEvaluate and return JSON object."
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        grade = json.loads(completion.choices[0].message.content)
        return {"needs_web_fallback": not grade.get("is_relevant", False)}
    except Exception:
        return {"needs_web_fallback": False}

def generate_answer_node(state: AgentState) -> dict:
    """
    Synthesizes facts into a clean answer with clean, non-repetitive citation badges.
    """
    print("✍️ Generating final response matrix...")
    
    if state["needs_web_fallback"]:
        system_prompt = (
            "You are a helpful AI assistant. State clearly that the user's workspace documents do not contain specific details for this query, "
            "then answer completely based on your general knowledge."
        )
        user_content = state["query"]
    else:
        context = "\n".join([f"[{d['doc']}]: {d['text']}" for d in state["retrieved_documents"]])
        system_prompt = (
            "You are ContextIQ, an expert workspace document assistant.\n"
            "INSTRUCTIONS:\n"
            "1. Answer the prompt thoroughly and accurately using ONLY the context data below.\n"
            "2. If summarizing a document or answering a query, provide clear bullet points or paragraphs.\n"
            "3. Add a single, clean citation badge like '[Filename.pdf]' at the end of key findings or summarized sections. "
            "Do NOT append citation brackets to every single sentence or line."
        )
        user_content = f"Context Data:\n{context}\n\nUser Question: {state['query']}"
        
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    return {"generation": completion.choices[0].message.content}

# ==========================================
# 3. LangGraph Engine Compilation
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("rewrite_query", rewrite_query_node)
workflow.add_node("retrieve_documents", retrieve_documents_node)
workflow.add_node("evaluate_context", evaluate_context_node)
workflow.add_node("generate_answer", generate_answer_node)

workflow.add_edge(START, "rewrite_query")
workflow.add_edge("rewrite_query", "retrieve_documents")
workflow.add_edge("retrieve_documents", "evaluate_context")
workflow.add_edge("evaluate_context", "generate_answer")
workflow.add_edge("generate_answer", END)

contextiq_agent = workflow.compile()