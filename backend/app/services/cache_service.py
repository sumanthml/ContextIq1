import hashlib
import time
from typing import Optional, Dict, Any

class QueryResponseCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 86400):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def _make_key(self, user_id: str, file_name: Optional[str], prompt: str) -> str:
        raw_key = f"{user_id}:{(file_name or '').strip().lower()}:{prompt.strip().lower()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        
    def get(self, user_id: str, file_name: Optional[str], prompt: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(user_id, file_name, prompt)
        entry = self._cache.get(key)
        if not entry:
            return None
            
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            return None
            
        print(f"⚡ CACHE HIT: Returning pre-computed RAG response for key {key[:8]}")
        return entry["response"]
        
    def set(self, user_id: str, file_name: Optional[str], prompt: str, response_data: Dict[str, Any]) -> None:
        if len(self._cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
            
        key = self._make_key(user_id, file_name, prompt)
        self._cache[key] = {
            "timestamp": time.time(),
            "response": response_data
        }

query_cache = QueryResponseCache()
