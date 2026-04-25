# skills/mlx_voice/references/__init__.py
"""
MLX Voice 触手 — 引用模块
导出主要接口供外部调用
"""
from .mlx_voice import (
    transcribe,
    chat,
    speak,
    voice_pipeline,
    health_check,
    DEFAULT_VOICE,
    OUTPUT_DIR,
)

__all__ = [
    "transcribe",
    "chat", 
    "speak",
    "voice_pipeline",
    "health_check",
    "DEFAULT_VOICE",
    "OUTPUT_DIR",
]