# tests/memory_tests/test_vector.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestVectorMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_store_without_llm(self, temp_dir, monkeypatch):
        import memory.vector as mv
        mv.VECTORS_FILE = temp_dir / "vectors.json"
        from memory.vector import VectorMemory
        mem = VectorMemory(llm_fn=None)
        entry = mem.store("用户问了天气问题", {"type": "qa"})
        assert entry["id"] is not None
        assert entry["embedding"] is None  # No LLM

    def test_search_fallback(self, temp_dir, monkeypatch):
        import memory.vector as mv
        mv.VECTORS_FILE = temp_dir / "vectors.json"
        from memory.vector import VectorMemory
        mem = VectorMemory(llm_fn=None)
        mem.store("北京今天天气晴朗", {"type": "weather"})
        results = mem.search("天气怎么样", top_k=1)
        assert len(results) >= 1
        assert "text" in results[0]

    def test_cosine_sim(self, temp_dir, monkeypatch):
        import memory.vector as mv
        mv.VECTORS_FILE = temp_dir / "vectors.json"
        from memory.vector import VectorMemory
        mem = VectorMemory(llm_fn=None)
        # Identical vectors
        sim = mem._cosine_sim([1.0, 0.0], [1.0, 0.0])
        assert sim == 1.0
        # Orthogonal vectors
        sim = mem._cosine_sim([1.0, 0.0], [0.0, 1.0])
        assert sim == 0.0
