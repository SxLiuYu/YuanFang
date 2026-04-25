#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理 - 基于 pydantic-settings
支持环境变量、配置文件、默认值多级配置
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AliyunAIConfig(BaseSettings):
    """阿里云 AI 配置"""
    api_key: str = ""
    model: str = "qwen-max"


class OpenAIConfig(BaseSettings):
    """OpenAI 配置"""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"


class AnthropicConfig(BaseSettings):
    """Anthropic 配置"""
    api_key: str = ""
    model: str = "claude-3-sonnet-20240229"


class OllamaConfig(BaseSettings):
    """Ollama 本地配置"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"


class FinnAConfig(BaseSettings):
    """FinnA API 配置"""
    base_url: str = "https://api.finna.com.cn/v1"
    api_key: str = ""
    default_model: str = "deepseek-community/deepseek-v3.1"


class SpeechToTextConfig(BaseSettings):
    """语音识别配置"""
    enabled: bool = True
    provider: str = "aliyun"
    aliyun: AliyunAIConfig = AliyunAIConfig(model="paraformer-realtime")


class TextToSpeechConfig(BaseSettings):
    """语音合成配置"""
    enabled: bool = True
    provider: str = "aliyun"
    voice: str = "longxiaochun"
    aliyun: AliyunAIConfig = AliyunAIConfig(model="sambert-zhina-v1")


class AIChatConfig(BaseSettings):
    """AI 对话配置"""
    enabled: bool = True
    provider: str = "finna"
    model: str = "deepseek-v3.1"
    temperature: float = 0.7
    max_tokens: int = 2048
    finna: FinnAConfig = FinnAConfig()
    aliyun: AliyunAIConfig = AliyunAIConfig()
    openai: OpenAIConfig = OpenAIConfig()
    anthropic: AnthropicConfig = AnthropicConfig()
    ollama: OllamaConfig = OllamaConfig()


class VideoUnderstandingConfig(BaseSettings):
    """视频理解配置"""
    enabled: bool = False
    provider: str = "aliyun"
    model: str = "qwen-vl-max"
    aliyun: AliyunAIConfig = AliyunAIConfig()


class PlatformConfig(BaseSettings):
    """平台配置"""
    enabled: bool = True


class SmartSpeakerSkillConfig(BaseSettings):
    """智能音箱技能配置"""
    enabled: bool = False
    skill_id: str = ""
    skill_secret: str = ""
    app_id: str = ""
    app_secret: str = ""
    client_id: str = ""
    client_secret: str = ""
    skill_token: str = ""
    bridge_name: str = "OpenClaw Home"
    pin: str = "031-45-154"


class StorageConfig(BaseSettings):
    """存储配置"""
    type: str = "sqlite"
    path: str = "./data/openclaw.db"
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class SecurityConfig(BaseSettings):
    """安全配置"""
    require_token: bool = False
    api_token: str = ""
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])


class FeaturesConfig(BaseSettings):
    """功能模块开关"""
    smart_home: bool = True
    finance: bool = True
    task: bool = True
    shopping: bool = True
    recipe: bool = True
    health: bool = True
    calendar: bool = True
    photo: bool = False
    education: bool = True
    pet: bool = True
    vehicle: bool = True
    home: bool = True
    medication: bool = True
    service: bool = True
    entertainment: bool = True
    security: bool = True
    communication: bool = True
    report: bool = True


class JarvisVoiceConfig(BaseSettings):
    """Jarvis 语音助手配置"""
    omlx_base_url: str = "http://localhost:4560"
    omlx_auth: str = "jarvis-local"
    default_model: str = "Qwen3.5-4B-MLX-4bit"
    kokoro_model: str = "prince-canuma/Kokoro-82M"
    default_voice: str = "af_heart"
    output_dir: str = "~/YuanFang/data/audio"
    vad_threshold: float = 0.5
    vad_min_samples: float = 0.3  # 秒
    sample_rate: int = 16000
    chunk_size: int = 5120
    interruption_threshold: float = 0.15
    min_interruption_interval: float = 0.5


class AppConfig(BaseSettings):
    """应用全局配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="yuanfang_"
    )

    # 全局设置
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # 功能模块
    features: FeaturesConfig = FeaturesConfig()

    # AI 服务
    speech_to_text: SpeechToTextConfig = SpeechToTextConfig()
    text_to_speech: TextToSpeechConfig = TextToSpeechConfig()
    ai_chat: AIChatConfig = AIChatConfig()
    video_understanding: VideoUnderstandingConfig = VideoUnderstandingConfig()

    # 平台
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)

    # 智能音箱
    smart_speaker_skills: Dict[str, SmartSpeakerSkillConfig] = Field(default_factory=dict)

    # 存储
    storage: StorageConfig = StorageConfig()

    # 安全
    security: SecurityConfig = SecurityConfig()

    # Jarvis 语音助手
    jarvis_voice: JarvisVoiceConfig = JarvisVoiceConfig()

    # 服务器
    server_host: str = "0.0.0.0"
    server_port: int = 5000

    # Qdrant 向量数据库
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        return v.upper()

    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return Path(__file__).parent.parent / "data"

    def get_config_dir(self) -> Path:
        """获取配置目录"""
        return Path(__file__).parent.parent / "config"


def load_yaml_config() -> Dict[str, Any]:
    """加载 YAML 配置文件（兼容旧格式）"""
    config_paths = [
        Path(__file__).parent.parent / "config" / "config.yaml",
        Path(__file__).parent.parent / "config" / "config.example.yaml",
    ]
    for path in config_paths:
        if path.exists():
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    return {}


def replace_env_vars(obj: Any, env: Dict[str, str] = None) -> Any:
    """替换环境变量占位符 ${VAR_NAME}"""
    if env is None:
        env = os.environ

    if isinstance(obj, dict):
        return {k: replace_env_vars(v, env) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_env_vars(item, env) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        return env.get(var_name, obj)
    return obj


# 全局单例实例
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置单例"""
    global _config_instance
    if _config_instance is None:
        # 先加载 YAML 兼容旧配置
        yaml_config = load_yaml_config()
        yaml_config = replace_env_vars(yaml_config)

        # 使用 YAML 配置初始化 pydantic-settings
        # pydantic-settings 会自动合并环境变量覆盖
        _config_instance = AppConfig.model_validate(yaml_config)

    return _config_instance


# 快捷导出
config = get_config()
