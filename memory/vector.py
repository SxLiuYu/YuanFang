"""
memory/vector.py
向量记忆 · VectorMemory
轻量级 embedding 检索，无需 Qdrant
"""
import json
import datetime
import logging
import uuid
import math
import os
from pathlib import Path

logger = logging.getLogger(__name__)

VECTORS_FILE = Path(__file__).parent / "vectors.json"

def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class VectorMemory:
    MAX_VECTORS = 300

    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn
        self.api_base = os.getenv("FINNA_API_BASE", "https://www.finna.com.cn/v1")
        self.api_key = os.getenv("FINNA_API_KEY", "")
        self.vectors = self._load()

    def _load(self) -> list:
        return _load_json(VECTORS_FILE, [])

    def _save(self):
        _save_json(VECTORS_FILE, self.vectors)

    def _cosine_sim(self, a: list, b: list) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _get_embedding(self, text: str):
        if self.llm_fn is None:
            return None
        try:
            return self.llm_fn(text)
        except Exception as e:
            logger.error(f"[VectorMemory] embedding 失败: {e}")
            return None

    def store(self, text: str, metadata: dict = None):
        embedding = self._get_embedding(text)
        entry = {
            "id": str(uuid.uuid4())[:8],
            "text": text[:300],
            "embedding": embedding,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.vectors.append(entry)
        if len(self.vectors) > self.MAX_VECTORS:
            self.vectors = self.vectors[-self.MAX_VECTORS:]
        self._save()
        return entry

    def search(self, query: str, top_k: int = 5) -> list:
        query_embedding = self._get_embedding(query)
        scored = []
        for v in self.vectors:
            if query_embedding and v.get("embedding"):
                sim = self._cosine_sim(query_embedding, v["embedding"])
                scored.append({**v, "score": sim})
            else:
                q_lower = query.lower()
                text_lower = (v.get("text") or "").lower()
                overlap = len(set(q_lower) & set(text_lower))
                scored.append({**v, "score": overlap * 0.1})
        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored[:top_k]

    def auto_store_interaction(self, user_input: str, ai_response: str):
        text = f"用户: {user_input[:100]} | 元芳: {ai_response[:100]}"
        self.store(text, {"type": "conversation"})
