"""
Mythos 优化模块

集成了深度思考 + MoE 专家路由的 Agent 优化方案

主要组件：
- MythosLLMAdapter: 主适配器，整合所有功能
- RecurrentDepthReasoner: 循环深度推理引擎
- ExpertRouter: 专家路由系统
- AdaptiveComputationTimeController: 自适应计算时间控制器
- MythosConfig: 配置管理

使用示例：
```python
from mythos_optimizer import MythosLLMAdapter, MythosConfig

# 创建适配器
config = MythosConfig()
adapter = MythosLLMAdapter(config=config)

# 使用深度思考模式
response = adapter.chat_with_reasoning(
    "如何优化Python性能？",
    use_depth=True,
    use_router=True,
)

# 直接代理到原LLM
response = adapter.chat("你好")
```
"""
from __future__ import annotations
import logging
from typing import Any, List, Dict, Optional, Union, Callable

from .config import MythosConfig
from .reasoner import RecurrentDepthReasoner, ReasoningResult, ReasoningStep
from .router import ExpertRouter, RoutingDecision, Expert
from .act_controller import (
    AdaptiveComputationTimeController,
    ComplexityEstimate,
    QualityAssessment,
)

# 配置日志
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "1.0.0"
__author__ = "Mythos Team"

__all__ = [
    "MythosLLMAdapter",
    "MythosConfig",
    "RecurrentDepthReasoner",
    "ExpertRouter",
    "AdaptiveComputationTimeController",
    "ReasoningResult",
    "ReasoningStep",
    "RoutingDecision",
    "Expert",
    "ComplexityEstimate",
    "QualityAssessment",
]


class MythosLLMAdapter:
    """
    Mythos LLM 适配器
    
    核心功能：
    1. 透明代理 - 可以完全替代原 LLMAdapter
    2. 深度思考 - 可选的循环深度推理
    3. 专家路由 - 智能专家选择
    4. 自适应计算 - 根据任务复杂度动态调整
    
    使用方式：
    ```python
    # 创建适配器（包装原LLM）
    adapter = MythosLLMAdapter(
        base_llm=original_llm_adapter,
        config=MythosConfig(),
    )
    
    # 直接使用（透明代理）
    response = adapter.chat("你好")
    
    # 使用深度思考
    response = adapter.chat_with_reasoning("复杂问题...")
    ```
    """
    
    def __init__(
        self,
        base_llm: Optional[Any] = None,
        config: Optional[MythosConfig] = None,
        llm_call_fn: Optional[Callable] = None,
    ):
        """
        初始化 Mythos 适配器
        
        Args:
            base_llm: 原始 LLM 适配器（可选）
            config: Mythos 配置（可选）
            llm_call_fn: 直接的 LLM 调用函数（可选，替代 base_llm）
                签名: fn(prompt: str, **kwargs) -> str
        """
        self.config = config or MythosConfig()
        self.base_llm = base_llm
        self.llm_call_fn = llm_call_fn
        
        # 初始化核心组件
        self.reasoner = RecurrentDepthReasoner(self.config, self._call_llm_internal)
        self.router = ExpertRouter(self.config)
        self.act_controller = AdaptiveComputationTimeController(self.config)
        
        # 状态
        self.last_reasoning_result: Optional[ReasoningResult] = None
        self.last_routing_decision: Optional[RoutingDecision] = None
        
        self._init_logger()
    
    def _init_logger(self):
        """初始化日志"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _call_llm_internal(self, prompt: str, **kwargs) -> str:
        """
        内部调用 LLM
        
        优先使用 llm_call_fn，其次使用 base_llm.chat
        """
        if self.llm_call_fn:
            return self.llm_call_fn(prompt, **kwargs)
        
        if self.base_llm:
            if hasattr(self.base_llm, "chat"):
                return self.base_llm.chat(prompt, **kwargs)
            elif hasattr(self.base_llm, "__call__"):
                return self.base_llm(prompt, **kwargs)
        
        # 如果没有 LLM，返回错误
        raise ValueError(
            "没有可用的 LLM。请提供 base_llm 或 llm_call_fn。"
        )
    
    # ============================================================
    # 核心接口：透明代理模式
    # ============================================================
    
    def chat(
        self,
        message: str,
        **kwargs,
    ) -> str:
        """
        透明代理：直接调用原始 LLM
        
        这个方法保持与原 LLMAdapter 完全一致的接口
        """
        if self.config.auto_use_depth:
            # 自动模式：根据复杂度决定是否使用深度思考
            estimate = self.act_controller.estimate_complexity(message)
            if estimate.complexity_score > self.config.auto_depth_threshold:
                self.logger.info(f"[Mythos] 自动启用深度思考 (复杂度: {estimate.complexity_score:.2f})")
                return self.chat_with_reasoning(message, **kwargs)
        
        # 直接代理
        return self._call_llm_internal(message, **kwargs)
    
    def __call__(self, message: str, **kwargs) -> str:
        """支持直接调用"""
        return self.chat(message, **kwargs)
    
    # ============================================================
    # 增强接口：深度思考模式
    # ============================================================
    
    def chat_with_reasoning(
        self,
        message: str,
        use_depth: bool = True,
        use_router: bool = True,
        custom_steps: Optional[int] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """
        带深度思考的聊天
        
        Args:
            message: 用户消息
            use_depth: 是否使用深度推理
            use_router: 是否使用专家路由
            custom_steps: 自定义思考步数（覆盖自动计算）
            stream_callback: 流式回调函数，接收思考过程
            **kwargs: 传递给 LLM 的其他参数
        
        Returns:
            str - 最终回答
        """
        self.logger.info(f"[Mythos] 开始处理: {message[:50]}...")
        
        # 1. 复杂度评估
        estimate = self.act_controller.estimate_complexity(message)
        self.logger.info(f"[Mythos] 复杂度评估: {estimate.difficulty_level} ({estimate.complexity_score:.2f})")
        
        # 2. 专家路由
        routing_decision = None
        expert_prompt = ""
        if use_router and self.config.use_moe:
            routing_decision = self.router.route(message)
            self.last_routing_decision = routing_decision
            self.logger.info(f"[Mythos] 选择专家: {routing_decision.selected_experts}")
            expert_prompt = self.router.build_expert_prompt(routing_decision.selected_experts)
        
        # 3. 确定思考步数
        if custom_steps is not None:
            n_steps = custom_steps
        else:
            n_steps = estimate.estimated_steps
        
        n_steps = max(
            self.config.min_reasoning_steps,
            min(n_steps, self.config.max_thinking_steps)
        )
        self.logger.info(f"[Mythos] 计划思考步数: {n_steps}")
        
        # 4. 深度推理
        if use_depth and self.config.use_recurrent_depth:
            reasoning_result = self.reasoner.reason(
                query=message,
                n_steps=n_steps,
                expert_prompt=expert_prompt,
                act_controller=self.act_controller,
                stream_callback=stream_callback,
                **kwargs,
            )
            self.last_reasoning_result = reasoning_result
            
            self.logger.info(f"[Mythos] 思考完成: {len(reasoning_result.steps)} 步")
            self.logger.info(f"[Mythos] 思考质量: {reasoning_result.overall_quality:.2f}")
            
            return reasoning_result.final_answer
        
        # 5. 无深度思考模式（仅专家路由）
        full_prompt = message
        if expert_prompt:
            full_prompt = f"{expert_prompt}\n\n用户问题：{message}"
        
        return self._call_llm_internal(full_prompt, **kwargs)
    
    # ============================================================
    # 便捷方法
    # ============================================================
    
    def get_last_reasoning(self) -> Optional[ReasoningResult]:
        """获取最后一次的思考结果"""
        return self.last_reasoning_result
    
    def get_last_routing(self) -> Optional[RoutingDecision]:
        """获取最后一次的路由决策"""
        return self.last_routing_decision
    
    def print_reasoning_trace(self, result: Optional[ReasoningResult] = None):
        """打印思考过程追踪"""
        result = result or self.last_reasoning_result
        if not result:
            print("没有可用的思考结果")
            return
        
        print("\n" + "=" * 60)
        print("🧠 Mythos 深度思考追踪")
        print("=" * 60)
        print(f"原始问题: {result.query}")
        print(f"总步数: {len(result.steps)} | 质量: {result.overall_quality:.2f}")
        print("-" * 60)
        
        for i, step in enumerate(result.steps):
            print(f"\n📍 步骤 {i + 1} ({step.step_type.value})")
            print(f"   质量: {step.quality:.2f} | 时间: {step.duration:.2f}s")
            print(f"   内容:\n{step.content}\n")
        
        print("-" * 60)
        print("✅ 最终答案:")
        print(result.final_answer)
        print("=" * 60 + "\n")
    
    def add_expert(self, expert: Expert):
        """动态添加专家"""
        self.router.add_expert(expert)
    
    def list_experts(self) -> List[Expert]:
        """列出所有专家"""
        return self.router.list_experts()
    
    # ============================================================
    # 配置管理
    # ============================================================
    
    def set_config(self, **kwargs):
        """动态更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"[Mythos] 配置更新: {key} = {value}")
    
    def enable_depth(self):
        """启用深度思考"""
        self.config.use_recurrent_depth = True
    
    def disable_depth(self):
        """禁用深度思考"""
        self.config.use_recurrent_depth = False
    
    def enable_moe(self):
        """启用专家路由"""
        self.config.use_moe = True
    
    def disable_moe(self):
        """禁用专家路由"""
        self.config.use_moe = False
    
    def set_act_mode(self, mode: str):
        """设置 ACT 模式"""
        assert mode in ["conservative", "balanced", "aggressive"]
        self.config.act_mode = mode
