"""
循环深度推理引擎 (Recurrent-Depth Reasoner)
基于 OpenMythos 的 RDT 架构思想 + DeepSeek-R1 的思考链机制

核心思想：
- 模拟深度思考过程，不是一次性回答，而是反复迭代
- 每一轮都基于前一轮的结果继续深入
- 自适应计算时间：简单问题快速回答，复杂问题深度思考
- 思考质量评估：动态决定何时停止思考
"""
from __future__ import annotations
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from .config import MythosConfig
from .act_controller import QualityAssessment, AdaptiveComputationTimeController

logger = logging.getLogger(__name__)


class StepType(Enum):
    """思考步骤类型"""
    PRELUDE = "prelude"      # 序曲：理解问题
    REASONING = "reasoning"  # 推理：深度思考
    CODA = "coda"            # 尾声：总结答案


@dataclass
class ReasoningStep:
    """单个思考步骤"""
    step_index: int
    step_type: StepType
    content: str
    quality: float = 0.0
    duration: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ReasoningResult:
    """完整的推理结果"""
    query: str
    steps: List[ReasoningStep]
    final_answer: str
    overall_quality: float = 0.0
    total_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RecurrentDepthReasoner:
    """
    循环深度推理引擎
    
    架构：
        Prelude → [Reasoning]×T → Coda
        
        - Prelude: 理解问题，制定思考计划
        - Reasoning: 循环推理，反复深入
        - Coda: 整理最终答案
    """
    
    def __init__(
        self,
        config: MythosConfig,
        llm_call_fn: Callable[[str, Any], str],
    ):
        self.config = config
        self.llm_call_fn = llm_call_fn
        logger.info(f"[RecurrentDepthReasoner] 初始化完成")
    
    def reason(
        self,
        query: str,
        n_steps: int = 4,
        expert_prompt: str = "",
        act_controller: Optional[AdaptiveComputationTimeController] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> ReasoningResult:
        """
        执行深度推理
        
        Args:
            query: 用户查询
            n_steps: 思考步数
            expert_prompt: 专家提示词
            act_controller: 自适应计算时间控制器
            stream_callback: 流式回调
            **kwargs: 传递给 LLM 的参数
        
        Returns:
            ReasoningResult - 完整推理结果
        """
        start_time = time.time()
        steps: List[ReasoningStep] = []
        
        logger.info(f"[Reasoner] 开始推理: {query[:50]}...")
        
        # 1. Prelude: 理解问题
        prelude_step = self._prelude(query, expert_prompt, stream_callback, **kwargs)
        steps.append(prelude_step)
        
        # 2. Looped Reasoning: 循环推理
        current_thought = prelude_step.content
        early_terminated = False
        
        for i in range(n_steps):
            # 执行推理步骤
            reasoning_step = self._reasoning_step(
                query=query,
                current_thought=current_thought,
                step_index=i + 1,
                total_steps=n_steps,
                expert_prompt=expert_prompt,
                stream_callback=stream_callback,
                **kwargs,
            )
            steps.append(reasoning_step)
            current_thought = reasoning_step.content
            
            # 评估思考质量，决定是否提前终止
            if act_controller:
                assessment = act_controller.assess_quality(steps, len(steps) - 1)
                if assessment.should_stop:
                    logger.info(f"[Reasoner] 提前终止: {assessment.reason}")
                    early_terminated = True
                    break
        
        # 3. Coda: 总结答案
        coda_step = self._coda(
            query=query,
            all_thoughts=[s.content for s in steps],
            expert_prompt=expert_prompt,
            stream_callback=stream_callback,
            **kwargs,
        )
        steps.append(coda_step)
        
        # 计算总体质量
        total_time = time.time() - start_time
        overall_quality = self._compute_overall_quality(steps)
        
        result = ReasoningResult(
            query=query,
            steps=steps,
            final_answer=coda_step.content,
            overall_quality=overall_quality,
            total_time=total_time,
            metadata={
                "n_planned_steps": n_steps,
                "n_actual_steps": len(steps),
                "early_terminated": early_terminated,
            },
        )
        
        logger.info(f"[Reasoner] 推理完成: {len(steps)} 步, {total_time:.2f}s")
        return result
    
    def _prelude(
        self,
        query: str,
        expert_prompt: str,
        stream_callback: Optional[Callable],
        **kwargs,
    ) -> ReasoningStep:
        """序曲：理解问题"""
        start = time.time()
        
        prompt = self._build_prelude_prompt(query, expert_prompt)
        
        if stream_callback:
            stream_callback("📍 理解问题中...")
        
        content = self.llm_call_fn(prompt, **kwargs)
        
        duration = time.time() - start
        return ReasoningStep(
            step_index=0,
            step_type=StepType.PRELUDE,
            content=content,
            duration=duration,
            quality=0.7,  # 序曲默认质量
        )
    
    def _reasoning_step(
        self,
        query: str,
        current_thought: str,
        step_index: int,
        total_steps: int,
        expert_prompt: str,
        stream_callback: Optional[Callable],
        **kwargs,
    ) -> ReasoningStep:
        """执行单个推理步骤"""
        start = time.time()
        
        prompt = self._build_reasoning_prompt(
            query, current_thought, step_index, total_steps, expert_prompt
        )
        
        if stream_callback:
            stream_callback(f"🤔 深度思考中... ({step_index}/{total_steps})")
        
        content = self.llm_call_fn(prompt, **kwargs)
        
        duration = time.time() - start
        return ReasoningStep(
            step_index=step_index,
            step_type=StepType.REASONING,
            content=content,
            duration=duration,
            quality=0.8,  # 推理步骤质量
        )
    
    def _coda(
        self,
        query: str,
        all_thoughts: List[str],
        expert_prompt: str,
        stream_callback: Optional[Callable],
        **kwargs,
    ) -> ReasoningStep:
        """尾声：总结答案"""
        start = time.time()
        
        prompt = self._build_coda_prompt(query, all_thoughts, expert_prompt)
        
        if stream_callback:
            stream_callback("✅ 整理最终答案...")
        
        content = self.llm_call_fn(prompt, **kwargs)
        
        duration = time.time() - start
        return ReasoningStep(
            step_index=len(all_thoughts),
            step_type=StepType.CODA,
            content=content,
            duration=duration,
            quality=0.9,  # 总结质量较高
        )
    
    def _build_prelude_prompt(self, query: str, expert_prompt: str) -> str:
        """构建序曲提示词"""
        base = """请仔细分析以下问题，理解它的核心：

问题：{query}

请用清晰的语言：
1. 重述这个问题的核心
2. 指出解决这个问题的关键点
3. 简要说明你的思考方向

不要直接给出最终答案，先理解问题。"""
        
        prompt = base.format(query=query)
        
        if expert_prompt:
            prompt = f"{expert_prompt}\n\n{prompt}"
        
        return prompt
    
    def _build_reasoning_prompt(
        self,
        query: str,
        current_thought: str,
        step_index: int,
        total_steps: int,
        expert_prompt: str,
    ) -> str:
        """构建推理提示词"""
        base = """基于之前的思考，继续深入分析：

原问题：{query}

当前思考：
{current_thought}

这是第 {step}/{total} 轮思考。请：
1. 基于当前思考继续深入
2. 发现新的角度或遗漏的点
3. 进行验证或修正
4. 逐步接近最终答案

请继续你的思考过程："""
        
        prompt = base.format(
            query=query,
            current_thought=current_thought,
            step=step_index,
            total=total_steps,
        )
        
        if expert_prompt:
            prompt = f"{expert_prompt}\n\n{prompt}"
        
        return prompt
    
    def _build_coda_prompt(
        self,
        query: str,
        all_thoughts: List[str],
        expert_prompt: str,
    ) -> str:
        """构建尾声提示词"""
        thoughts_text = "\n\n".join([f"思考 {i+1}:\n{t}" for i, t in enumerate(all_thoughts)])
        
        base = """基于完整的思考过程，请给出最终答案：

原问题：{query}

完整思考过程：
{thoughts}

请：
1. 综合所有思考
2. 给出清晰、完整的最终答案
3. 确保答案准确、有条理

最终答案："""
        
        prompt = base.format(query=query, thoughts=thoughts_text)
        
        if expert_prompt:
            prompt = f"{expert_prompt}\n\n{prompt}"
        
        return prompt
    
    def _compute_overall_quality(self, steps: List[ReasoningStep]) -> float:
        """计算总体质量分数"""
        if not steps:
            return 0.0
        
        # 后面的步骤权重更高
        total_weight = 0.0
        weighted_sum = 0.0
        
        for i, step in enumerate(steps):
            weight = (i + 1) / len(steps)  # 线性增加权重
            total_weight += weight
            weighted_sum += step.quality * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
