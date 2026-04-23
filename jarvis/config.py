"""
贾维斯配置文件管理模块
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class JarvisConfig:
    """贾维斯配置管理器"""
    
    @staticmethod
    def get_api_url():
        """获取 API 地址"""
        return os.getenv("JARVIS_API_URL", "http://localhost:8001")
    
    @staticmethod
    def get_local_model_config():
        """获取本地模型配置"""
        return {
            "api_base": os.getenv("LOCAL_MODEL_API_BASE", "http://localhost:4560/v1"),
            "model_name": os.getenv("LOCAL_MODEL_NAME", "qwen3.5-4b-mlx"),
            "api_key": "EMPTY"  # 本地模型不需要API key
        }
    
    @staticmethod
    def get_voice_config():
        """获取语音配置"""
        return {
            "tts": {"model": "kokoro", "endpoint": "http://localhost:8000/api/tts"},
            "asr": {"model": "mlx-whisper", "endpoint": "http://localhost:8000/api/asr"},
        }

# 全局配置实例
config = JarvisConfig()
