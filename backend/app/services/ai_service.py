from groq import Groq
import cohere
from app.core.config import settings

try:
    # Initialize the Groq client for lightning-fast LLM inference loops
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
    
    # Use standard stable Client initialization
    cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY)
    
    print("✅ AI Engine services (Groq & Cohere) successfully initialized!")
    
except Exception as e:
    print(f"❌ Failed to initialize AI engine API connectors: {str(e)}")
    raise e

def get_text_embeddings(text_chunks: list[str]) -> list[list[float]]:
    """
    Sends a list of text chunks to Cohere's API and returns their mathematical vectors.
    """
    try:
        response = cohere_client.embed(
            texts=text_chunks,
            model="embed-english-v3.0",
            input_type="search_document"
        )
        # Standard cohere client returns embeddings directly inside the response object
        return response.embeddings
        
    except Exception as e:
        print(f"❌ Cohere embedding generation failed: {str(e)}")
        raise e

def rerank_documents(query: str, documents: list[dict], top_n: int = 5) -> list[dict]:
    """
    Uses Cohere's Cross-Encoder Reranker to dynamically score and sort retrieved text 
    chunks based on exact contextual relevance to the user's prompt.
    """
    try:
        doc_texts = [doc["text"] for doc in documents]
        
        if not doc_texts:
            return []
            
        response = cohere_client.rerank(
            query=query,
            documents=doc_texts,
            model="rerank-english-v3.0",
            top_n=top_n
        )
        
        reranked_results = []
        for result in response.results:
            original_doc = documents[result.index]
            original_doc["rerank_score"] = result.relevance_score
            reranked_results.append(original_doc)
            
        return reranked_results
        
    except Exception as e:
        print(f"❌ Cohere reranking process failed: {str(e)}")
        raise e