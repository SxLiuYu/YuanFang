"""
memory/system.py
统一记忆管理 · MemorySystem
"""
from memory.emotional import EmotionalMemory
from memory.scene import SceneMemory
from memory.vector import VectorMemory


class MemorySystem:
    def __init__(self, llm_fn=None):
        self.emotional = EmotionalMemory()
        self.scene = SceneMemory()
        self.vector = VectorMemory(llm_fn)

    def record_interaction(self, user_input: str, agent_response: str, emotion: str = "neutral"):
        content = f"用户: {user_input[:80]} | 元芳: {agent_response[:80]}"
        intensity_map = {
            "positive": 0.7, "negative": 0.8, "surprise": 0.9,
            "gratitude": 0.6, "neutral": 0.3
        }
        intensity = intensity_map.get(emotion, 0.3)
        self.emotional.add(content, emotion, intensity)
        try:
            self.vector.auto_store_interaction(user_input, agent_response)
        except Exception:
            pass

    def auto_snapshot(self, nodes_data: dict):
        scene_type = self.scene.predict_next()
        self.scene.snapshot(scene_type, nodes_data)
        return scene_type

    def get_context_summary(self) -> str:
        emotion_summary = self.emotional.summary()
        predicted_scene = self.scene.predict_next()
        recent_scenes = self.scene.recent(3)
        scene_note = f"预测当前场景: {predicted_scene}"
        if recent_scenes:
            scene_note += f"，上次快照: {recent_scenes[0]['timestamp'][:16]}"
        return f"{emotion_summary}。{scene_note}"

    def full_report(self) -> dict:
        return {
            "emotional": {
                "total": len(self.emotional.entries),
                "stats": self.emotional.emotion_stats(),
                "recent": self.emotional.recent(5),
                "summary": self.emotional.summary(),
            },
            "scene": {
                "total": len(self.scene.scenes),
                "stats": self.scene.stats(),
                "recent": self.scene.recent(3),
                "predicted_current": self.scene.predict_next(),
            }
        }


_memory: "MemorySystem | None" = None

def get_memory() -> "MemorySystem":
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory
