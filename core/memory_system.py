"""
core/memory_system.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.memory_system is deprecated, use memory.system instead", DeprecationWarning, stacklevel=2)

from memory.system import MemorySystem, get_memory

__all__ = ["MemorySystem", "get_memory"]
