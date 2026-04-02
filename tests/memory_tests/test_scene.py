# tests/memory_tests/test_scene.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestSceneMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_snapshot(self, temp_dir, monkeypatch):
        import memory.scene as ms
        ms.SCENE_FILE = temp_dir / "scenes.json"
        from memory.scene import SceneMemory
        mem = SceneMemory()
        entry = mem.snapshot("morning", {"light": "on", "temp": 22}, "起床")
        assert entry["scene_type"] == "morning"
        assert entry["state"]["light"] == "on"

    def test_predict_next(self, temp_dir, monkeypatch):
        import memory.scene as ms
        ms.SCENE_FILE = temp_dir / "scenes.json"
        from memory.scene import SceneMemory
        mem = SceneMemory()
        predicted = mem.predict_next()
        assert isinstance(predicted, str)
        assert predicted in ["morning", "work", "evening", "sleep"]

    def test_stats(self, temp_dir, monkeypatch):
        import memory.scene as ms
        ms.SCENE_FILE = temp_dir / "scenes.json"
        from memory.scene import SceneMemory
        mem = SceneMemory()
        mem.snapshot("morning", {})
        mem.snapshot("morning", {})
        mem.snapshot("evening", {})
        stats = mem.stats()
        assert stats["morning"] == 2
        assert stats["evening"] == 1

    def test_recent(self, temp_dir, monkeypatch):
        import memory.scene as ms
        ms.SCENE_FILE = temp_dir / "scenes.json"
        from memory.scene import SceneMemory
        mem = SceneMemory()
        mem.snapshot("morning", {"a": 1})
        mem.snapshot("work", {"b": 2})
        recent = mem.recent(1)
        assert len(recent) == 1
