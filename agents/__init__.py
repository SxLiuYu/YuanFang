# agents/__init__.py
from agents.hyper import TaskAgent, MetaAgent, EvolutionaryMemory, HyperAgent

# CrewAI导入（带异常处理，避免CrewAI兼容性问题影响启动）
try:
    from agents.crew import LobsterArmyCrew
    CREW_AVAILABLE = True
except Exception:
    LobsterArmyCrew = None
    CREW_AVAILABLE = False

# 三省六部制（基于HyperAgent，推荐使用）
try:
    from agents.crew.six_provinces import SixProvincesSystem
    SIX_PROVINCES_AVAILABLE = True
except Exception:
    SixProvincesSystem = None
    SIX_PROVINCES_AVAILABLE = False

__all__ = [
    "TaskAgent",
    "MetaAgent",
    "EvolutionaryMemory",
    "HyperAgent",
    "LobsterArmyCrew",
    "SixProvincesSystem",
]
