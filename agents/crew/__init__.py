# agents/crew/__init__.py
# CrewAI导入（带异常处理）
try:
    from agents.crew.lobster_army_crew import LobsterArmyCrew
    CREW_AVAILABLE = True
except Exception:
    LobsterArmyCrew = None
    CREW_AVAILABLE = False

__all__ = ["LobsterArmyCrew"]
