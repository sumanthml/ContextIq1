import uuid
import re

from qdrant_client.http import models
from app.core.security import get_tenant_vector_hash
from app.services.ai_service import get_text_embeddings
from app.services.vector_store import qdrant_client

def semantic_sentence_chunker(text: str, max_chunk_size: int = 500, overlap_sentences: int = 1) -> list[str]:
    """
    Splits text cleanly along complete sentence boundaries instead of cutting mid-word,
    ensuring small, single-line fact components are preserved inside vector profiles.
    """
    # Split text blocks cleanly at sentence boundaries (. ! ?)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if not sentence:
            continue
        sentence_len = len(sentence)
        
        # If a single sentence exceeds limits by itself, push it anyway to protect context data
        if current_length + sentence_len > max_chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Create overlapping context window based on previous lines
            current_chunk = current_chunk[-overlap_sentences:] if len(current_chunk) > overlap_sentences else current_chunk
            current_length = sum(len(s) for s in current_chunk) + len(current_chunk)
            
        current_chunk.append(sentence)
        current_length += sentence_len + 1
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

from app.services.hybrid_search import bm25_store

def ingest_user_document(user_id: str, document_name: str, raw_text: str, collection_name: str = "contextiq_knowledge"):
    """
    Processes raw text document input into embeddings, attaches cryptographic tenant hashes,
    uploads vectors to Qdrant, and indexes text chunks into local BM25 keyword store.
    """
    # 1. Generate the secure cryptographic hash for the user workspace
    tenant_hash = get_tenant_vector_hash(user_id)
    
    # 2. Break down the text document using complete semantic lines
    text_chunks = semantic_sentence_chunker(raw_text)
    if not text_chunks:
        print("⚠️ Document ingestion skipped: No valid text strings extracted.")
        return
        
    # 3. Add to BM25 sparse keyword store
    try:
        bm25_store.add_documents(user_id, document_name, text_chunks)
        print(f"✅ BM25 keyword index populated with {len(text_chunks)} chunks for: {document_name}")
    except Exception as bm_err:
        print(f"⚠️ BM25 indexing error: {bm_err}")

    # 4. Batch convert the text chunks into mathematical vectors via Cohere
    vectors = get_text_embeddings(text_chunks)
    
    # 5. Construct the Qdrant point objects packed with aligned multi-tenant payload rules
    points = []
    for i, (chunk, vector) in enumerate(zip(text_chunks, vectors)):
        point_id = str(uuid.uuid4())
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "tenant_owner": tenant_hash,     # 🔒 Strict multi-tenant hardware shield key
                    "file_name": document_name,      # 🚀 Aligned graph lookup key
                    "text": chunk,                   # The actual text snippet fed to the LLM context
                    "chunk_index": i
                }
            )
        )
        
    # 6. Mass upload coordinate arrays up to Qdrant cluster/local storage
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"✅ Ingestion successful! {len(points)} segments uploaded for file: {document_name}")
        
    except Exception as e:
        print(f"❌ Critical error pushing points to Qdrant: {str(e)}")
        raise e