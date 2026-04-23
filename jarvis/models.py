"""
贾维斯 AI 模型配置和管理模块

支持多个 FinnA API 模型：
- DeepSeek V3.1 (主力) - 自然语言理解、对话
- Kimi K2 (备选) - 多任务处理
- Qwen3-VL-32B (视觉) - 图像理解
- CosyVoice2 (语音) - TTS/ASR
- GLM-4.6 (保留) - 备选模型
"""

import time
from typing import Optional, Dict, Any
from litellm import completion
import json

class JarvisModels:
    """贾维斯 AI 模型管理器"""
    
    # FinnA API 模型配置
    MODELS = {
        "deepseek-v3.1": {
            "app": "app-d678VU1DyYuPJe6Lo6CuGLpE",
            "model": "deepseek-v3.1",
            "description": "主力模型 - 自然语言理解、对话",
            "capabilities": ["chat", "nlu", "reasoning"]
        },
        "kimi-k2": {
            "app": "app-Yo4TLaMAahNgyqV13XC9gH4l",
            "model": "kimi-k2",
            "description": "备选模型 - 多任务处理",
            "capabilities": ["multi-task", "reasoning"]
        },
        "qwen-vl-32b": {
            "app": "app-ucXhF6nom3gCiD9iMbGdvCV8",
            "model": "qwen-vl-32b",
            "description": "视觉模型 - 图像理解",
            "capabilities": ["vision", "multi-modal"]
        },
        "cosyvoice2": {
            "app": "app-BqyKsTO4Om3JGoPCTkJX080J",
            "model": "cosyvoice2",
            "description": "语音模型 - TTS/ASR",
            "capabilities": ["tts", "asr"]
        },
        "glm-4.6": {
            "app": "app-U65474o4sIpsFoUh2iMm38Pl",
            "model": "glm-4.6",
            "description": "保留模型 - 备选",
            "capabilities": ["chat"]
        },
        "qwen-32b": {
            "app": "app-6OzRGg93TfuDOny9NUnKMvQU",
            "model": "qwen-32b",
            "description": "保留模型 - 备选",
            "capabilities": ["chat"]
        }
    }
    
    def __init__(self):
        self.current_model = None
        self.model_cache: Dict[str, Any] = {}
    
    def get_model(self, model_name: str) -> Dict[str, Any]:
        """获取模型配置"""
        return self.MODELS.get(model_name)
    
    def list_models(self) -> Dict[str, Any]:
        """列出所有可用模型"""
        return self.MODELS
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return list(self.MODELS.keys())[0]
    
    async def chat(
        self, 
        model_name: str, 
        messages: list, 
        temperature: float = 0.7
    ) -> str:
        """
        调用模型对话 API
        
        Args:
            model_name (str): 模型名称
            messages (list): 消息列表 [{role, content}]
            temperature (float): 温度参数
        
        Returns:
            str: AI 回复内容
        """
        model_config = self.get_model(model_name)
        
        if not model_config:
            raise ValueError(f"未知模型：{model_name}")
        
        try:
            response = await completion(
                model=model_config["app"],
                messages=messages,
                temperature=temperature,
                timeout=30.0  # 防止超时
            )
            
            if isinstance(response, list) and response:
                return response[0]["content"]
            
            return str(response) if isinstance(response, dict) else response
            
        except Exception as e:
            # 日志记录（实际应用中应使用 logging 模块）
            print(f"[贾维斯] 模型调用失败：{model_name} - {str(e)}")
            raise
    
    async def understand_intent(self, text: str) -> Dict[str, Any]:
        """
        理解用户意图
        
        Args:
            text (str): 用户输入文本
        
        Returns:
            dict: {intent, parameters, confidence}
        """
        model = self.get_model("deepseek-v3.1")
        
        # 构建意图识别提示词
        prompt = f"""你是一个智能助手，请分析以下用户问题：
用户输入："{text}"

请按以下格式输出 JSON:
{{
  "intent": "意图类型 (如：search, weather, calendar, file, system)",
  "parameters": {{参数}},
  "confidence": 0-1 之间的置信度分数，
  "suggested_actions": ["建议操作 1", "建议操作 2"]
}}

只返回 JSON，不要其他文本。
"""
        
        response = await self.chat(model["app"], [{"role": "user", "content": prompt}])
        
        # 解析 JSON 响应
        try:
            result = json.loads(response)
            return {
                "intent": result.get("intent", "unknown"),
                "parameters": result.get("parameters", {}),
                "confidence": result.get("confidence", 0.5),
                "suggested_actions": result.get("suggested_actions", [])
            }
        except json.JSONDecodeError:
            return {
                "intent": "unknown",
                "parameters": {},
                "confidence": 0.5,
                "suggested_actions": ["未知意图"]
            }
    
    async def generate_embedding(self, text: str) -> list:
        """生成文本嵌入向量"""
        # 使用嵌入模型（实际应用中可使用 embedding 专用 API）
        # 这里简化处理，返回示例向量
        return [0.1, -0.3, 0.5, 0.2]
