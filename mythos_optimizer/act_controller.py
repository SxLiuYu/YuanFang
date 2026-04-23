"""
自适应计算时间控制器 (Adaptive Computation Time Controller)

借鉴 Ouroboros 和 DeepSeek-R1 的自适应计算时间机制：
- 动态决定推理深度，不需要固定的思考步数
- 根据任务复杂度自动调整思考深度
- 简单问题快速响应，复杂问题深度思考

在 Agent 层面的实现：
- 任务复杂度分析
- 思考步数预测
- 思考质量评估
- 提前终止机制
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
import re
import time
import hashlib

from .config import MythosConfig
from typing import Any, List

# 避免循环依赖，只使用类型提示时才导入
try:
    from .reasoner import ReasoningStep
except ImportError:
    ReasoningStep = Any

logger = logging.getLogger(__name__)


@dataclass
class ComplexityEstimate:
    """复杂度评估结果"""
    query: str
    complexity_score: float  # 0.0 - 1.0
    estimated_steps: int
    estimated_tokens: int
    reasoning: str
    difficulty_level: str  # "simple", "medium", "complex", "very_complex"


@dataclass
class QualityAssessment:
    """思考质量评估"""
    step_index: int
    quality_score: float  # 0.0 - 1.0
    coherence_score: float
    progress_score: float
    completeness_score: float
    should_stop: bool
    reason: str
    suggestions: List[str]


class AdaptiveComputationTimeController:
    """
    自适应计算时间控制器
    
    核心功能：
    1. 任务复杂度分析 - 分析查询的复杂度
    2. 推理步数预测 - 基于复杂度预测需要的步数
    3. 思考质量评估 - 评估每一步思考的质量
    4. 提前终止决策 - 决定是否可以提前终止
    5. 思考深度调整 - 动态调整思考深度
    """
    
    def __init__(self, config: MythosConfig):
        self.config = config
        self.cache: Dict[str, ComplexityEstimate] = {}
        self._init_patterns()
        logger.info(f"[ACTController] 初始化完成，配置: {config.act_mode}")
    
    def _init_patterns(self):
        """初始化模式匹配规则"""
        # 简单问题模式
        self.simple_patterns = [
            r"^(是|否|对|错|好的|谢谢|你好|hi|hello)",
            r"^(请问|什么是|告诉我|解释一下)\s*([A-Za-z\u4e00-\u9fa5]{1,10})\s*[？?。.]?$",
            r"^(现在|今天|昨天|明天)\s*(几点|几号|星期几)",
        ]
        
        # 复杂问题模式
        self.complex_patterns = [
            r"(代码|编程|实现|开发|系统|架构|设计)\s*(.*)\s*(怎么做|如何|怎样)",
            r"(分析|研究|探讨|对比|比较|评估)\s*(.*)\s*(.*)",
            r"(问题|错误|bug|异常)\s*(.*)\s*(排查|解决|修复)",
            r"(计划|规划|方案|策略)\s*(.*)\s*(制定|设计)",
        ]
        
        # 质量评估关键词
        self.quality_keywords = {
            "good": ["因此", "所以", "综上所述", "结论", "已完成", "解决", "正确", "验证", "测试通过"],
            "bad": ["可能", "大概", "也许", "不确定", "不知道", "无法", "错误", "失败", "有问题"],
            "progress": ["首先", "其次", "然后", "接着", "下一步", "继续", "完成了", "实现了"],
        }
    
    def estimate_complexity(self, query: str, use_cache: bool = True) -> ComplexityEstimate:
        """
        评估查询的复杂度
        
        Args:
            query: 用户查询
            use_cache: 是否使用缓存
        
        Returns:
            ComplexityEstimate - 复杂度评估结果
        """
        # 检查缓存
        cache_key = self._get_cache_key(query)
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # 计算复杂度分数
        complexity_score = self._compute_complexity_score(query)
        
        # 确定难度等级
        if complexity_score < 0.25:
            difficulty_level = "simple"
            estimated_steps = 2
            estimated_tokens = 512
        elif complexity_score < 0.5:
            difficulty_level = "medium"
            estimated_steps = 4
            estimated_tokens = 1024
        elif complexity_score < 0.75:
            difficulty_level = "complex"
            estimated_steps = 6
            estimated_tokens = 2048
        else:
            difficulty_level = "very_complex"
            estimated_steps = 10
            estimated_tokens = 4096
        
        # 生成推理理由
        reasoning = self._generate_complexity_reasoning(query, complexity_score)
        
        estimate = ComplexityEstimate(
            query=query,
            complexity_score=complexity_score,
            estimated_steps=estimated_steps,
            estimated_tokens=estimated_tokens,
            reasoning=reasoning,
            difficulty_level=difficulty_level,
        )
        
        # 缓存结果
        self.cache[cache_key] = estimate
        
        return estimate
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.strip().lower().encode()).hexdigest()
    
    def _compute_complexity_score(self, query: str) -> float:
        """计算复杂度分数（0.0 - 1.0）"""
        score = 0.0
        query_lower = query.strip().lower()
        query_length = len(query)
        
        # 长度因子
        if query_length > 200:
            score += 0.3
        elif query_length > 100:
            score += 0.2
        elif query_length > 50:
            score += 0.1
        
        # 简单模式匹配
        for pattern in self.simple_patterns:
            if re.match(pattern, query_lower):
                score -= 0.2
                break
        
        # 复杂模式匹配
        for pattern in self.complex_patterns:
            if re.search(pattern, query_lower):
                score += 0.2
                break
        
        # 特殊词汇
        complex_words = ["系统", "架构", "设计", "实现", "开发", "分析", "研究", "对比", "评估", "规划", "方案", "策略", "问题", "排查", "解决", "优化"]
        for word in complex_words:
            if word in query_lower:
                score += 0.05
        
        # 标点符号数量（多问号/感叹号通常表示复杂问题）
        if query.count("?") + query.count("？") > 1:
            score += 0.1
        
        # 限制范围
        score = max(0.0, min(1.0, score))
        
        return score
    
    def _generate_complexity_reasoning(self, query: str, score: float) -> str:
        """生复杂度推理理由"""
        reasons = []
        
        query_length = len(query)
        if query_length > 100:
            reasons.append(f"查询较长（{query_length}字符）")
        
        for pattern in self.complex_patterns:
            if re.search(pattern, query.lower()):
                reasons.append("检测到复杂任务关键词")
                break
        
        if score < 0.3:
            reasons.append("属于简单问题，适合快速响应")
        elif score > 0.7:
            reasons.append("属于复杂问题，需要深度思考")
        
        return " | ".join(reasons) if reasons else "标准复杂度评估"
    
    def assess_quality(
        self,
        steps: List[ReasoningStep],
        current_step: int,
    ) -> QualityAssessment:
        """
        评估思考质量
        
        Args:
            steps: 所有思考步骤
            current_step: 当前步骤索引
        
        Returns:
            QualityAssessment - 质量评估结果
        """
        if current_step < 0 or current_step >= len(steps):
            return QualityAssessment(
                step_index=current_step,
                quality_score=0.5,
                coherence_score=0.5,
                progress_score=0.5,
                completeness_score=0.5,
                should_stop=False,
                reason="无效步骤",
                suggestions=[],
            )
        
        step_content = steps[current_step].content.lower()
        
        # 连贯性评分
        coherence_score = self._assess_coherence(steps, current_step)
        
        # 进展评分
        progress_score = self._assess_progress(steps, current_step)
        
        # 完整性评分
        completeness_score = self._assess_completeness(step_content)
        
        # 综合质量分数
        quality_score = (
            coherence_score * 0.3 +
            progress_score * 0.4 +
            completeness_score * 0.3
        )
        
        # 决定是否应该停止
        should_stop, reason, suggestions = self._decide_early_termination(
            quality_score, current_step, len(steps), step_content
        )
        
        return QualityAssessment(
            step_index=current_step,
            quality_score=quality_score,
            coherence_score=coherence_score,
            progress_score=progress_score,
            completeness_score=completeness_score,
            should_stop=should_stop,
            reason=reason,
            suggestions=suggestions,
        )
    
    def _assess_coherence(self, steps: List[ReasoningStep], current_step: int) -> float:
        """评估连贯性"""
        if current_step == 0:
            return 0.6
        
        score = 0.5
        current_content = steps[current_step].content.lower()
        prev_content = steps[current_step - 1].content.lower()
        
        # 检查是否有连接词
        connectives = ["因此", "所以", "接着", "然后", "但是", "然而", "另外", "此外"]
        for conn in connectives:
            if conn in current_content:
                score += 0.1
        
        # 检查内容关联度（简单的关键词重叠）
        current_words = set(current_content)
        prev_words = set(prev_content)
        overlap = len(current_words & prev_words)
        if overlap > 5:
            score += 0.2
        elif overlap > 2:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_progress(self, steps: List[ReasoningStep], current_step: int) -> float:
        """评估进展"""
        score = 0.5
        content = steps[current_step].content.lower()
        
        # 进展关键词
        for word in self.quality_keywords["progress"]:
            if word in content:
                score += 0.15
        
        # 完成标记
        complete_markers = ["完成", "结束", "总结", "结论", "因此"]
        for marker in complete_markers:
            if marker in content:
                score += 0.2
        
        return min(1.0, score)
    
    def _assess_completeness(self, content: str) -> float:
        """评估完整性"""
        score = 0.5
        
        # 积极关键词
        for word in self.quality_keywords["good"]:
            if word in content:
                score += 0.1
        
        # 消极关键词
        for word in self.quality_keywords["bad"]:
            if word in content:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _decide_early_termination(
        self,
        quality_score: float,
        current_step: int,
        total_steps: int,
        content: str,
    ) -> Tuple[bool, str, List[str]]:
        """
        决定是否提前终止
        
        Returns:
            (should_stop, reason, suggestions)
        """
        suggestions = []
        reason = ""
        should_stop = False
        
        # 配置阈值
        min_steps = self.config.min_reasoning_steps
        quality_threshold = self.config.early_termination_threshold
        
        # 还没到最少步数，不终止
        if current_step < min_steps - 1:
            reason = f"还未达到最少步数（{min_steps}）"
            return False, reason, ["继续思考"]
        
        # 质量足够高，可以终止
        if quality_score >= quality_threshold:
            should_stop = True
            reason = f"思考质量足够高（{quality_score:.2f} >= {quality_threshold}）"
            suggestions = ["可以进入输出阶段"]
        
        # 检查是否有明确的完成标记
        complete_markers = ["总结", "结论", "因此", "综上所述"]
        for marker in complete_markers:
            if marker in content:
                if quality_score >= 0.6:
                    should_stop = True
                    reason = f"检测到完成标记：{marker}"
                    suggestions = ["整理最终答案"]
                break
        
        # 达到最大步数，强制终止
        if current_step >= self.config.max_thinking_steps - 1:
            should_stop = True
            reason = f"已达到最大思考步数（{self.config.max_thinking_steps}）"
            suggestions = ["强制进入输出阶段"]
        
        # 如果质量很低，建议调整
        if quality_score < 0.4 and not should_stop:
            suggestions.append("尝试从不同角度分析")
            suggestions.append("检查是否有遗漏的关键点")
        
        return should_stop, reason, suggestions
    
    def get_optimal_steps(self, query: str) -> int:
        """
        获取最优的思考步数
        
        这是一个便捷方法，基于复杂度评估返回推荐的步数
        """
        estimate = self.estimate_complexity(query)
        
        # 根据模式调整
        if self.config.act_mode == "conservative":
            return min(estimate.estimated_steps + 2, self.config.max_thinking_steps)
        elif self.config.act_mode == "aggressive":
            return max(estimate.estimated_steps - 1, self.config.min_reasoning_steps)
        else:  # balanced
            return estimate.estimated_steps
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("[ACTController] 缓存已清空")
