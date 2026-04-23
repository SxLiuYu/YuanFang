# tests/memory_tests/test_system.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestMemorySystem:
    @pytest.fixture
    def mem(self, monkeypatch):
        import memory.emotional, memory.scene, memory.vector
        d = tempfile.mkdtemp()
        p = Path(d)
        memory.emotional.EMOTIONAL_FILE = p / "emotional.json"
        memory.scene.SCENE_FILE = p / "scenes.json"
        memory.vector.VECTORS_FILE = p / "vectors.json"
        from memory.system import MemorySystem
        yield MemorySystem(llm_fn=None)
        shutil.rmtree(d)

    def test_record_interaction(self, mem):
        mem.record_interaction("今天天气真好", "是的，很适合出门", "positive")
        report = mem.emotional.emotion_stats()
        assert report["positive"] == 1

    def test_get_context_summary(self, mem):
        summary = mem.get_context_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_full_report(self, mem):
        report = mem.full_report()
        assert "emotional" in report
        assert "scene" in report
        assert "total" in report["emotional"]
        assert "total" in report["scene"]

    def test_auto_snapshot(self, mem):
        scene = mem.auto_snapshot({"light": "on", "temp": 22})
        assert scene in ["morning", "work", "evening", "sleep"]
