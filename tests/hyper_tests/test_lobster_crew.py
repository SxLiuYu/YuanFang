# tests/hyper_tests/test_lobster_crew.py
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestLobsterArmyCrew:
    def test_crew_init(self):
        from agents.crew.lobster_army_crew import LobsterArmyCrew
        crew = LobsterArmyCrew()
        assert crew is not None
        assert crew._crew is None  # crewai not installed

    def test_crew_fallback(self):
        from agents.crew.lobster_army_crew import LobsterArmyCrew
        crew = LobsterArmyCrew()
        result = crew._run_fallback("测试任务")
        assert "crew" in result
        assert "result" in result
        assert result["mode"] in ["hyperagent_fallback", "error"]

    def test_crew_status(self):
        from agents.crew.base import CrewBase
        crew_base = CrewBase()
        status = crew_base.status()
        assert "name" in status
        assert status["name"] == "CrewBase"
        assert "agents_count" in status

    def test_crew_run_returns_dict(self):
        from agents.crew.lobster_army_crew import LobsterArmyCrew
        crew = LobsterArmyCrew()
        result = crew.run("测试任务")
        assert isinstance(result, dict)
        assert "crew" in result
        assert "result" in result
        assert "mode" in result

    def test_single_agent_fallback(self):
        from agents.crew.lobster_army_crew import LobsterArmyCrew
        crew = LobsterArmyCrew()
        result = crew.run_agent("researcher", "测试输入")
        assert "agent" in result
        assert result["agent"] == "researcher"
