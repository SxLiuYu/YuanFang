# tests/hyper_tests/test_evolutionary_memory.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestEvolutionaryMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_store_and_retrieve(self, temp_dir, monkeypatch):
        import agents.hyper.evolutionary_memory as em
        original_dir = em.EVOLUTION_DIR
        em.EVOLUTION_DIR = temp_dir
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        EvolutionaryMemory._instance = None
        try:
            mem = EvolutionaryMemory(storage_dir=temp_dir)
            improvement = {
                "quality_score": 8,
                "strengths": ["回答准确"],
                "weaknesses": ["不够详细"],
                "improvement_strategy": "增加解释",
                "domain_hint": "qa",
                "tags": ["general", "qa"]
            }
            mem.store(improvement, "测试任务摘要")
            retrieved = mem.retrieve("测试任务", top_k=1)
            assert len(retrieved) >= 1
            assert retrieved[0]["quality_score"] == 8
        finally:
            em.EVOLUTION_DIR = original_dir

    def test_get_context(self, temp_dir, monkeypatch):
        import agents.hyper.evolutionary_memory as em
        original_dir = em.EVOLUTION_DIR
        em.EVOLUTION_DIR = temp_dir
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        try:
            mem = EvolutionaryMemory(storage_dir=temp_dir)
            improvement = {
                "quality_score": 9,
                "strengths": ["很好"],
                "weaknesses": [],
                "improvement_strategy": "继续保持",
                "domain_hint": "code",
                "tags": ["code"]
            }
            mem.store(improvement, "写代码任务")
            context = mem.get_context("写代码")
            assert context is None or isinstance(context, str)
        finally:
            em.EVOLUTION_DIR = original_dir

    def test_evolution_report_empty(self, temp_dir, monkeypatch):
        import agents.hyper.evolutionary_memory as em
        original_dir = em.EVOLUTION_DIR
        em.EVOLUTION_DIR = temp_dir
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        try:
            mem = EvolutionaryMemory(storage_dir=temp_dir)
            report = mem.evolution_report()
            assert report["total_strategies"] == 0
            assert "message" in report
        finally:
            em.EVOLUTION_DIR = original_dir

    def test_evolution_report_with_data(self, temp_dir, monkeypatch):
        import agents.hyper.evolutionary_memory as em
        original_dir = em.EVOLUTION_DIR
        em.EVOLUTION_DIR = temp_dir
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        try:
            mem = EvolutionaryMemory(storage_dir=temp_dir)
            mem.store({"quality_score": 7, "domain_hint": "test", "tags": ["test"], "strengths": [], "weaknesses": [], "improvement_strategy": "ok"}, "任务1")
            report = mem.evolution_report()
            assert report["total_strategies"] == 1
            assert report["average_quality_score"] == 7.0
        finally:
            em.EVOLUTION_DIR = original_dir
