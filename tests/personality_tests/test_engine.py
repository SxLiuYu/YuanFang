# tests/personality/test_engine.py
import pytest
import tempfile
import shutil
from pathlib import Path
import importlib

class TestPersonalityEngine:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_get_system_prompt_returns_string(self, temp_dir, monkeypatch):
        import personality.engine as pe
        pe.PERSONALITY_FILE = temp_dir / "personality_state.json"
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        prompt = engine.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "元芳" in prompt

    def test_update_mood(self, temp_dir, monkeypatch):
        import personality.engine as pe
        pe.PERSONALITY_FILE = temp_dir / "personality_state.json"
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        engine.update_mood("excited", energy_delta=0.1, stress_delta=-0.05)
        assert engine.state["emotion"]["mood"] == "excited"
        assert engine.state["emotion"]["energy"] > 0.8

    def test_detect_emotion_positive(self, temp_dir, monkeypatch):
        import personality.engine as pe
        pe.PERSONALITY_FILE = temp_dir / "personality_state.json"
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        emotion = engine.detect_emotion("这个真棒，太厉害了！", "确实很强！")
        assert emotion == "positive"

    def test_detect_emotion_negative(self, temp_dir, monkeypatch):
        import personality.engine as pe
        pe.PERSONALITY_FILE = temp_dir / "personality_state.json"
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        emotion = engine.detect_emotion("坏了，出问题了", "我来处理")
        assert emotion == "negative"

    def test_get_status(self, temp_dir, monkeypatch):
        import personality.engine as pe
        pe.PERSONALITY_FILE = temp_dir / "personality_state.json"
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        status = engine.get_status()
        assert "name" in status
        assert "mood" in status
        assert "energy" in status
        assert status["name"] == "元芳"
