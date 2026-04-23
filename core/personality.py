"""
core/personality.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.personality is deprecated, use personality.engine instead", DeprecationWarning, stacklevel=2)

from personality.engine import PersonalityEngine, get_personality

__all__ = ["PersonalityEngine", "get_personality"]
