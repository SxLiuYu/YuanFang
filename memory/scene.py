"""
memory/scene.py
场景记忆 · SceneMemory
"""
import json
import datetime
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

SCENE_FILE = Path(__file__).parent / "scenes.json"

def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SceneMemory:
    MAX_SCENES = 200

    def __init__(self):
        self.scenes: list = _load_json(SCENE_FILE, [])

    def snapshot(self, scene_type: str, state: dict, note: str = ""):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "scene_type": scene_type,
            "weekday": datetime.datetime.now().strftime("%A"),
            "hour": datetime.datetime.now().hour,
            "state": state,
            "note": note[:100],
        }
        self.scenes.append(entry)
        if len(self.scenes) > self.MAX_SCENES:
            self.scenes = self.scenes[-self.MAX_SCENES:]
        _save_json(SCENE_FILE, self.scenes)
        return entry

    def recall_scene(self, scene_type: str, top_k: int = 5) -> list:
        results = [s for s in self.scenes if s.get("scene_type") == scene_type]
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)[:top_k]

    def predict_next(self) -> str:
        hour = datetime.datetime.now().hour
        if 6 <= hour < 9:
            return "morning"
        elif 9 <= hour < 18:
            return "work"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "sleep"

    def recent(self, n: int = 10) -> list:
        return sorted(self.scenes, key=lambda x: x["timestamp"], reverse=True)[:n]

    def stats(self) -> dict:
        stats = {}
        for s in self.scenes:
            st = s.get("scene_type", "unknown")
            stats[st] = stats.get(st, 0) + 1
        return stats
