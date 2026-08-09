import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

def _tokenize(text: str) -> List[str]:
    # Lowercase & split into alphanumeric terms
    return re.findall(r'\w+', text.lower())

class BM25IndexStore:
    def __init__(self):
        # Maps (user_id, file_name) -> list of {"text": str, "doc": str, "chunk_index": int}
        self.documents_store: Dict[str, List[Dict[str, Any]]] = {}
        self.bm25_indices: Dict[str, BM25Okapi] = {}
        
    def add_documents(self, user_id: str, file_name: str, chunks: List[str]) -> None:
        key = f"{user_id}:{file_name}"
        docs = [{"text": chunk, "doc": file_name, "chunk_index": i} for i, chunk in enumerate(chunks)]
        self.documents_store[key] = docs
        
        tokenized_corpus = [_tokenize(chunk) for chunk in chunks]
        if tokenized_corpus:
            self.bm25_indices[key] = BM25Okapi(tokenized_corpus)
            
    def search(self, user_id: str, file_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        key = f"{user_id}:{file_name}"
        if key not in self.bm25_indices or key not in self.documents_store:
            return []
            
        index = self.bm25_indices[key]
        docs = self.documents_store[key]
        
        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []
            
        scores = index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc_copy = dict(docs[idx])
                doc_copy["bm25_score"] = float(scores[idx])
                results.append(doc_copy)
        return results

bm25_store = BM25IndexStore()

def reciprocal_rank_fusion(sparse_results: List[Dict[str, Any]], dense_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
    """
    Merges sparse BM25 search rankings and dense Qdrant vector rankings
    using Reciprocal Rank Fusion (RRF) math scoring.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}
    
    for rank, doc in enumerate(sparse_results):
        text = doc["text"]
        scores[text] = scores.get(text, 0.0) + (1.0 / (k + rank + 1))
        doc_map[text] = doc
        
    for rank, doc in enumerate(dense_results):
        text = doc["text"]
        scores[text] = scores.get(text, 0.0) + (1.0 / (k + rank + 1))
        if text not in doc_map:
            doc_map[text] = doc
            
    sorted_texts = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    
    fused_results = []
    for text in sorted_texts:
        doc = dict(doc_map[text])
        doc["rrf_score"] = scores[text]
        fused_results.append(doc)
        
    return fused_results
