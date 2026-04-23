# tests/memory/test_emotional.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestEmotionalMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_add_entry(self, temp_dir, monkeypatch):
        import memory.emotional as me
        me.EMOTIONAL_FILE = temp_dir / "emotional.json"
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        entry = mem.add("用户问好", "positive", 0.7)
        assert entry["emotion"] == "positive"
        assert entry["intensity"] == 0.7
        assert "id" in entry

    def test_recall_by_emotion(self, temp_dir, monkeypatch):
        import memory.emotional as me
        me.EMOTIONAL_FILE = temp_dir / "emotional.json"
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        mem.add("测试1", "positive", 0.5)
        mem.add("测试2", "negative", 0.8)
        mem.add("测试3", "positive", 0.9)
        results = mem.recall("positive")
        assert len(results) == 2

    def test_summary(self, temp_dir, monkeypatch):
        import memory.emotional as me
        me.EMOTIONAL_FILE = temp_dir / "emotional.json"
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        summary = mem.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_emotion_stats(self, temp_dir, monkeypatch):
        import memory.emotional as me
        me.EMOTIONAL_FILE = temp_dir / "emotional.json"
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        mem.add("p1", "positive", 0.5)
        mem.add("p2", "positive", 0.6)
        mem.add("n1", "negative", 0.7)
        stats = mem.emotion_stats()
        assert stats["positive"] == 2
        assert stats["negative"] == 1
