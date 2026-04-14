# agents/hyper/__init__.py
from agents.hyper.task_agent import TaskAgent
from agents.hyper.meta_agent import MetaAgent
from agents.hyper.evolutionary_memory import EvolutionaryMemory
from agents.hyper.hyper_agent import HyperAgent
from agents.hyper.self_modifier import SelfModifier
from agents.hyper.agent_team import AgentTeam, SubAgent
from agents.hyper.improvement_loop import ImprovementLoop
from agents.hyper.paper_strategies import PaperStrategyEngine, get_paper_engine

__all__ = [
    "TaskAgent",
    "MetaAgent",
    "EvolutionaryMemory",
    "HyperAgent",
    "SelfModifier",
    "AgentTeam",
    "SubAgent",
    "ImprovementLoop",
    "PaperStrategyEngine",
    "get_paper_engine",
]
