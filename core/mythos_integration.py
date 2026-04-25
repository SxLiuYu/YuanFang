"""
Mythos 优化模块集成
透明包装现有的 LLMAdapter，添加深度思考 + MoE 专家路由功能

使用方式：
```python
from core.mythos_integration import get_mythos_llm

# 获取增强版 LLM（自动包装原有的 LLMAdapter）
llm = get_mythos_llm()

# 透明代理（和原来一样用）
response = llm.chat_simple([{"role": "user", "content": "你好"}])

# 或者使用深度思考模式
response = llm.chat_with_reasoning("如何优化Python性能？")
```
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Callable

# 导入 Mythos 模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mythos_optimizer import (
    MythosLLMAdapter,
    MythosConfig,
)

from core.llm_adapter import LLMAdapter, get_llm

logger = logging.getLogger(__name__)


class MythosEnhancedLLM:
    """
    Mythos 增强版 LLM
    
    透明包装现有的 LLMAdapter，提供：
    - 完全兼容的原有接口
    - 可选的深度思考功能
    - 可选的专家路由功能
    """
    
    def __init__(
        self,
        base_llm: Optional[LLMAdapter] = None,
        config: Optional[MythosConfig] = None,
        auto_enable: bool = False,
    ):
        """
        初始化 Mythos 增强版 LLM
        
        Args:
            base_llm: 原有的 LLMAdapter（如果不提供，会自动获取）
            config: Mythos 配置（可选）
            auto_enable: 是否自动启用深度思考（基于复杂度）
        """
        self.base_llm = base_llm or get_llm()
        self.config = config or MythosConfig(auto_use_depth=auto_enable)
        
        # 创建 Mythos 适配器
        self._mythos_adapter = MythosLLMAdapter(
            base_llm=None,
            config=self.config,
            llm_call_fn=self._call_base_llm,
        )
        
        # 状态
        self._last_reasoning_result = None
        self._last_routing_decision = None
        
        logger.info(f"[MythosEnhancedLLM] 初始化完成，auto_enable={auto_enable}")
    
    def _call_base_llm(self, prompt: str, **kwargs) -> str:
        """
        调用底层 LLM
        
        将 Mythos 的简单 prompt 调用转换为原有的 chat_simple 格式
        """
        messages = [{"role": "user", "content": prompt}]
        
        # 提取可能的参数
        temperature = kwargs.get("temperature", 0.7)
        model = kwargs.get("model", None)
        max_tokens = kwargs.get("max_tokens", 2048)
        
        return self.base_llm.chat_simple(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    # ============================================================
    # 原有接口的透明代理（完全兼容）
    # ============================================================
    
    def chat_simple(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        max_tokens: int = 2048,
    ) -> str:
        """
        简单对话接口（透明代理）
        
        如果启用了 auto_use_depth，会根据复杂度自动决定是否使用深度思考
        """
        # 提取用户消息
        user_message = self._extract_user_message(messages)
        
        # 如果启用了自动模式，且不是函数调用/JSON模式，尝试使用深度思考
        if (
            self.config.auto_use_depth and
            user_message and
            not json_mode and
            len(messages) <= 3  # 简单对话场景
        ):
            try:
                return self.chat_with_reasoning(
                    message=user_message,
                    model=model,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"[Mythos] 深度思考失败，回退到普通模式: {e}")
        
        # 回退到原有模式
        return self.base_llm.chat_simple(
            messages=messages,
            model=model,
            temperature=temperature,
            json_mode=json_mode,
            max_tokens=max_tokens,
        )
    
    def chat_with_functions(
        self,
        messages: list,
        functions: list = None,
        model: str = None,
        temperature: float = 0.3,
    ):
        """带函数调用的对话接口（透明代理）"""
        # 函数调用场景不使用深度思考
        return self.base_llm.chat_with_functions(
            messages=messages,
            functions=functions,
            model=model,
            temperature=temperature,
        )
    
    def chat_stream(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        callback=None,
    ):
        """流式对话接口（透明代理）"""
        # 流式场景不使用深度思考
        return self.base_llm.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            callback=callback,
        )
    
    def embed(self, text: str, model: str = "text-embedding-ada-002") -> list:
        """获取 embedding（透明代理）"""
        return self.base_llm.embed(text, model)
    
    def models(self) -> list:
        """列出可用模型（透明代理）"""
        return self.base_llm.models()
    
    # ============================================================
    # Mythos 增强接口
    # ============================================================
    
    def chat_with_reasoning(
        self,
        message: str,
        use_depth: bool = True,
        use_router: bool = True,
        custom_steps: Optional[int] = None,
        model: str = None,
        temperature: float = 0.7,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        带深度思考的聊天
        
        Args:
            message: 用户消息
            use_depth: 是否使用深度推理
            use_router: 是否使用专家路由
            custom_steps: 自定义思考步数
            model: 模型名称
            temperature: 温度参数
            stream_callback: 流式回调
        
        Returns:
            str - 最终回答
        """
        # 临时设置参数
        original_temp = None
        if hasattr(self.base_llm, "default_model") and model:
            original_temp = self.base_llm.default_model
            self.base_llm.default_model = model
        
        try:
            response = self._mythos_adapter.chat_with_reasoning(
                message=message,
                use_depth=use_depth,
                use_router=use_router,
                custom_steps=custom_steps,
                stream_callback=stream_callback,
                temperature=temperature,
            )
            
            # 保存结果
            self._last_reasoning_result = self._mythos_adapter.get_last_reasoning()
            self._last_routing_decision = self._mythos_adapter.get_last_routing()
            
            return response
            
        finally:
            if original_temp:
                self.base_llm.default_model = original_temp
    
    def get_last_reasoning(self):
        """获取最后一次的思考结果"""
        return self._last_reasoning_result
    
    def get_last_routing(self):
        """获取最后一次的路由决策"""
        return self._last_routing_decision
    
    def print_reasoning_trace(self):
        """打印思考过程追踪"""
        self._mythos_adapter.print_reasoning_trace(self._last_reasoning_result)
    
    # ============================================================
    # 配置管理
    # ============================================================
    
    def enable_auto_depth(self):
        """启用自动深度思考"""
        self.config.auto_use_depth = True
        logger.info("[Mythos] 已启用自动深度思考")
    
    def disable_auto_depth(self):
        """禁用自动深度思考"""
        self.config.auto_use_depth = False
        logger.info("[Mythos] 已禁用自动深度思考")
    
    def enable_depth(self):
        """启用深度思考功能"""
        self.config.use_recurrent_depth = True
    
    def disable_depth(self):
        """禁用深度思考功能"""
        self.config.use_recurrent_depth = False
    
    def enable_moe(self):
        """启用专家路由"""
        self.config.use_moe = True
    
    def disable_moe(self):
        """禁用专家路由"""
        self.config.use_moe = False
    
    # ============================================================
    # 辅助方法
    # ============================================================
    
    def _extract_user_message(self, messages: list) -> Optional[str]:
        """从消息列表中提取用户消息"""
        if not messages:
            return None
        
        # 找最后一个用户消息
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        
        return None


# ============================================================
# 全局单例
# ============================================================

_mythos_llm: Optional[MythosEnhancedLLM] = None


def get_mythos_llm(
    auto_enable: bool = False,
    config: Optional[MythosConfig] = None,
) -> MythosEnhancedLLM:
    """
    获取 Mythos 增强版 LLM（全局单例）
    
    Args:
        auto_enable: 是否自动启用深度思考
        config: 自定义配置（可选）
    
    Returns:
        MythosEnhancedLLM - 增强版 LLM 实例
    """
    global _mythos_llm
    
    if _mythos_llm is None:
        _mythos_llm = MythosEnhancedLLM(
            auto_enable=auto_enable,
            config=config,
        )
    elif config is not None:
        # 如果提供了新配置，更新
        _mythos_llm.config = config
    
    return _mythos_llm


def reset_mythos_llm():
    """重置 Mythos LLM 单例"""
    global _mythos_llm
    _mythos_llm = None
    logger.info("[Mythos] 已重置单例")
