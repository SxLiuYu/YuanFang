"""
memory/emotional.py
情感记忆 · EmotionalMemory
"""
import json
import datetime
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

EMOTIONAL_FILE = Path(__file__).parent / "emotional.json"

def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class EmotionalMemory:
    MAX_ENTRIES = 500

    def __init__(self):
        self.entries: list = _load_json(EMOTIONAL_FILE, [])

    def add(self, content: str, emotion: str, intensity: float = 0.5, source: str = "user"):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "content": content[:200],
            "emotion": emotion,
            "intensity": max(0.0, min(1.0, intensity)),
            "source": source,
        }
        self.entries.append(entry)
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries.sort(key=lambda x: (x["intensity"], x["timestamp"]))
            self.entries = self.entries[50:]
        _save_json(EMOTIONAL_FILE, self.entries)
        return entry

    def recall(self, emotion: str = None, top_k: int = 10) -> list:
        results = self.entries
        if emotion:
            results = [e for e in results if e.get("emotion") == emotion]
        results = sorted(results, key=lambda x: x.get("intensity", 0), reverse=True)
        return results[:top_k]

    def recent(self, n: int = 20) -> list:
        return sorted(self.entries, key=lambda x: x["timestamp"], reverse=True)[:n]

    def emotion_stats(self) -> dict:
        stats = {}
        for e in self.entries:
            em = e.get("emotion", "neutral")
            stats[em] = stats.get(em, 0) + 1
        return stats

    def summary(self) -> str:
        recent = self.recent(10)
        if not recent:
            return "暂无情感记忆"
        emotions = [e["emotion"] for e in recent]
        dominant = max(set(emotions), key=emotions.count)
        mood_map = {
            "positive": "最近互动以积极愉快为主",
            "negative": "最近有一些负面互动，需要关注",
            "neutral":  "最近互动比较平淡",
            "surprise": "最近有不少令人意外的事项",
            "gratitude":"最近收到不少感谢和正面反馈",
        }
        return mood_map.get(dominant, f"最近情感偏于{dominant}")
