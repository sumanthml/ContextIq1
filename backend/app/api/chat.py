import json
import asyncio
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from app.core.security import verify_user_token
from app.agent.graph import contextiq_agent
from app.services.db_service import save_chat_message, get_chat_history
from app.services.cache_service import query_cache
from app.services.ai_service import groq_client

router = APIRouter(prefix="/chat", tags=["Chat Engine"])

@router.post("/query")
async def query_agentic_rag(
    prompt: str = Body(..., embed=True),
    file_context_filter: str = Body(None, embed=True),
    current_user_id: str = Depends(verify_user_token)
):
    """
    Executes LangGraph RAG reasoning loops, strictly passing targeted filename
    context isolation filters down into vector search logic states with LRU caching.
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    # 1. Check LRU Cache
    cached = query_cache.get(current_user_id, file_context_filter, prompt)
    if cached:
        return cached

    try:
        # Save user message to persistent DB
        if file_context_filter:
            save_chat_message(current_user_id, file_context_filter, "user", prompt)

        initial_state = {
            "user_id": current_user_id,
            "query": prompt,
            "file_filter": file_context_filter,
            "optimized_queries": [],
            "retrieved_documents": [],
            "needs_web_fallback": False,
            "generation": ""
        }
        final_output = contextiq_agent.invoke(initial_state)
        answer = final_output.get("generation", "No context generated.")

        # Save assistant generation to persistent DB
        if file_context_filter:
            save_chat_message(current_user_id, file_context_filter, "assistant", answer)

        response_payload = {
            "query": prompt,
            "answer": answer,
            "meta": {
                "expanded_search_terms": final_output.get("optimized_queries", []),
                "fallback_triggered": final_output.get("needs_web_fallback", False),
                "sources": [
                    {"doc": d.get("doc"), "snippet": d.get("text")[:200]}
                    for d in final_output.get("retrieved_documents", [])
                ]
            }
        }

        # Cache final payload
        query_cache.set(current_user_id, file_context_filter, prompt, response_payload)
        return response_payload

    except Exception as e:
        print(f"❌ Agent query exception: {e}")
        raise HTTPException(status_code=500, detail=f"Agent process execution fault: {str(e)}")


@router.post("/stream")
async def stream_agentic_rag(
    prompt: str = Body(..., embed=True),
    file_context_filter: str = Body(None, embed=True),
    current_user_id: str = Depends(verify_user_token)
):
    """
    Streams Llama-3.3 answer tokens in real time via Server-Sent Events (SSE).
    Yields JSON events token-by-token followed by final metadata frame.
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    async def event_generator():
        try:
            # Log user prompt
            if file_context_filter:
                save_chat_message(current_user_id, file_context_filter, "user", prompt)

            initial_state = {
                "user_id": current_user_id,
                "query": prompt,
                "file_filter": file_context_filter,
                "optimized_queries": [],
                "retrieved_documents": [],
                "needs_web_fallback": False,
                "generation": ""
            }

            # Run retrieval & evaluation nodes
            state = dict(initial_state)
            from app.agent.graph import rewrite_query_node, retrieve_documents_node, evaluate_context_node
            state.update(rewrite_query_node(state))
            state.update(retrieve_documents_node(state))
            state.update(evaluate_context_node(state))

            # Send telemetry metadata first
            sources = [
                {"doc": d.get("doc"), "snippet": d.get("text")}
                for d in state.get("retrieved_documents", [])
            ]
            meta_event = {
                "event": "meta",
                "queries": state.get("optimized_queries", []),
                "fallback": state.get("needs_web_fallback", False),
                "sources": sources
            }
            yield f"data: {json.dumps(meta_event)}\n\n"

            # Prepare prompts for streaming
            if state["needs_web_fallback"]:
                sys_prompt = "You are a helpful workspace companion. Answer the user prompt directly."
                u_content = prompt
            else:
                context = "\n".join([f"[{d['doc']}]: {d['text']}" for d in state.get("retrieved_documents", [])])
                sys_prompt = (
                    "You are ContextIQ, an expert workspace document assistant.\n"
                    "INSTRUCTIONS:\n"
                    "1. Answer thoroughly using ONLY the context data below.\n"
                    "2. Add a single clean citation badge like '[Filename.pdf]' at the end of key points or summary sections. Do NOT repeat citations on every sentence."
                )
                u_content = f"Context Data:\n{context}\n\nUser Question: {prompt}"

            # Stream LLM tokens
            completion_stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": u_content}
                ],
                stream=True
            )

            full_answer = ""
            for chunk in completion_stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_answer += delta
                    token_event = {"event": "token", "delta": delta}
                    yield f"data: {json.dumps(token_event)}\n\n"
                    await asyncio.sleep(0.01)

            # Save full assistant response
            if file_context_filter:
                save_chat_message(current_user_id, file_context_filter, "assistant", full_answer)

            end_event = {"event": "done", "full_answer": full_answer}
            yield f"data: {json.dumps(end_event)}\n\n"

        except Exception as err:
            err_event = {"event": "error", "message": str(err)}
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history")
async def get_file_chat_history(
    file_name: str = Query(...),
    current_user_id: str = Depends(verify_user_token)
):
    """
    Returns structured, chronologically sorted conversation logs.
    """
    return get_chat_history(current_user_id, file_name)