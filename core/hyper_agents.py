"""
core/hyper_agents.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.hyper_agents is deprecated, use agents.hyper instead", DeprecationWarning, stacklevel=2)

from agents.hyper.task_agent import TaskAgent
from agents.hyper.meta_agent import MetaAgent
from agents.hyper.evolutionary_memory import EvolutionaryMemory
from agents.hyper.hyper_agent import HyperAgent

__all__ = ["TaskAgent", "MetaAgent", "EvolutionaryMemory", "HyperAgent"]
