"""
专家路由系统 (Expert Router)
借鉴 DeepSeekMoE 的设计思想：
- 共享专家（Shared Experts）：始终激活，捕获通用知识
- 路由专家（Routed Experts）：稀疏激活，每个 token/请求只激活 top-K
- 细粒度专家分割：每个专家有小的隐藏维度，激活更多专家时保持 FLOPs 不变

在 Agent 层面的实现：
- 共享专家：通用对话、工具调用等基础能力
- 路由专家：编程、分析、创意、研究等专业能力
- 路由机制：根据任务类型智能选择专家组合
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
import re

from .config import MythosConfig

logger = logging.getLogger(__name__)


@dataclass
class Expert:
    """专家定义"""
    id: str
    name: str
    specialty: List[str]
    description: str = ""
    is_shared: bool = False
    prompt_template: Optional[str] = None
    
    def __post_init__(self):
        if self.prompt_template is None:
            self.prompt_template = self._default_prompt()
    
    def _default_prompt(self) -> str:
        """默认提示词模板"""
        specialties = ", ".join(self.specialty)
        return (
            f"你是 {self.name}。"
            f"你的专长领域：{specialties}。"
            f"请从你的专业角度来分析和回答问题。"
        )


@dataclass
class RoutingDecision:
    """路由决策"""
    query: str
    selected_experts: List[str]
    routing_scores: Dict[str, float]
    shared_experts: List[str]
    routed_experts: List[str]
    confidence: float = 0.0


class ExpertRouter:
    """
    专家路由器
    
    核心机制：
    1. 任务类型分析 - 分析查询的类型和特征
    2. 专家匹配 - 将任务与专家专长匹配
    3. 路由评分 - 为每个专家计算匹配分数
    4. Top-K 选择 - 选择分数最高的 K 个路由专家
    5. 专家组合 - 共享专家 + 路由专家
    """
    
    def __init__(self, config: MythosConfig):
        self.config = config
        self.experts: Dict[str, Expert] = {}
        self._load_experts_from_config()
        logger.info(f"[ExpertRouter] 初始化完成，加载专家: {list(self.experts.keys())}")
    
    def _load_experts_from_config(self):
        """从配置加载专家"""
        if not self.config.experts:
            return
        
        for i, expert_config in enumerate(self.config.experts):
            is_shared = i < self.config.n_shared_experts
            expert = Expert(
                id=expert_config["id"],
                name=expert_config["name"],
                specialty=expert_config["specialty"],
                is_shared=is_shared,
            )
            self.experts[expert.id] = expert
    
    def add_expert(self, expert: Expert):
        """动态添加专家"""
        self.experts[expert.id] = expert
        logger.info(f"[ExpertRouter] 添加专家: {expert.id}")
    
    def route(self, query: str, custom_selector: Optional[Callable] = None) -> RoutingDecision:
        """
        执行专家路由
        
        Args:
            query: 用户查询
            custom_selector: 自定义选择器函数
        
        Returns:
            RoutingDecision - 路由决策结果
        """
        # 任务类型分析
        task_type = self._analyze_task_type(query)
        
        # 如果有自定义选择器，使用它
        if custom_selector:
            selected = custom_selector(query, task_type, self.experts)
            return self._build_decision(query, selected, {})
        
        # 默认路由逻辑
        routing_scores = self._compute_routing_scores(query, task_type)
        selected_experts = self._select_top_experts(routing_scores)
        
        return self._build_decision(query, selected_experts, routing_scores)
    
    def _analyze_task_type(self, query: str) -> Dict[str, float]:
        """
        分析任务类型
        
        返回：各类任务的得分字典
        """
        query_lower = query.lower()
        
        # 关键词匹配
        task_keywords = {
            "code": ["代码", "编程", "python", "javascript", "函数", "类", "bug", "调试", "write code", "programming", "debug", "function", "class"],
            "analysis": ["分析", "数据", "统计", "数学", "计算", "分析一下", "analysis", "data", "statistics", "math", "calculate"],
            "creative": ["写", "创作", "故事", "诗", "文案", "创意", "write", "create", "story", "poem", "creative"],
            "research": ["研究", "论文", "学术", "科学", "查找", "资料", "research", "paper", "academic", "science", "find"],
            "planning": ["计划", "规划", "安排", "任务", "项目", "plan", "schedule", "task", "project"],
            "learning": ["学习", "教学", "解释", "教程", "teach", "explain", "tutorial", "learn"],
            "tool": ["工具", "api", "集成", "自动化", "tool", "api", "integration", "automation"],
        }
        
        scores = {}
        for task_type, keywords in task_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1.0
            scores[task_type] = score
        
        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        return scores
    
    def _compute_routing_scores(
        self,
        query: str,
        task_type_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """
        计算每个专家的路由分数
        
        借鉴 DeepSeekMoE 的门控机制：
        - 共享专家始终获得基础分数
        - 路由专家根据任务匹配度获得分数
        """
        scores = {}
        query_lower = query.lower()
        
        for expert_id, expert in self.experts.items():
            score = 0.0
            
            # 共享专家获得基础分数
            if expert.is_shared:
                score = 0.5
            
            # 专长匹配
            for specialty in expert.specialty:
                if specialty in query_lower:
                    score += 0.3
            
            # 任务类型匹配
            for task_type, task_score in task_type_scores.items():
                if task_type in expert.specialty:
                    score += task_score * 0.5
            
            scores[expert_id] = score
        
        return scores
    
    def _select_top_experts(self, routing_scores: Dict[str, float]) -> List[str]:
        """
        选择 Top-K 专家
        
        策略：
        1. 所有共享专家自动入选
        2. 从路由专家中选择分数最高的
        """
        # 分离共享专家和路由专家
        shared = [eid for eid, expert in self.experts.items() if expert.is_shared]
        routed = [eid for eid, expert in self.experts.items() if not expert.is_shared]
        
        # 对路由专家按分数排序
        routed_with_scores = [(eid, routing_scores.get(eid, 0.0)) for eid in routed]
        routed_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择 Top-K 路由专家
        k_needed = self.config.n_experts_per_tok - len(shared)
        selected_routed = [eid for eid, score in routed_with_scores[:k_needed]]
        
        return shared + selected_routed
    
    def _build_decision(
        self,
        query: str,
        selected_experts: List[str],
        routing_scores: Dict[str, float],
    ) -> RoutingDecision:
        """构建路由决策对象"""
        shared = [eid for eid in selected_experts if self.experts[eid].is_shared]
        routed = [eid for eid in selected_experts if not self.experts[eid].is_shared]
        
        # 计算置信度
        if routing_scores:
            max_score = max(routing_scores.values())
            confidence = min(1.0, max_score / 2.0)  # 归一化到 0-1
        else:
            confidence = 0.5
        
        return RoutingDecision(
            query=query,
            selected_experts=selected_experts,
            routing_scores=routing_scores,
            shared_experts=shared,
            routed_experts=routed,
            confidence=confidence,
        )
    
    def build_expert_prompt(self, expert_ids: List[str], base_prompt: str = "") -> str:
        """
        构建专家组合提示词
        
        将多个专家的提示词组合起来
        """
        prompts = []
        
        for expert_id in expert_ids:
            if expert_id in self.experts:
                prompts.append(self.experts[expert_id].prompt_template)
        
        if not prompts:
            return base_prompt
        
        expert_prompt = "\n\n".join(prompts)
        
        if base_prompt:
            return f"{expert_prompt}\n\n{base_prompt}"
        
        return expert_prompt
    
    def get_expert(self, expert_id: str) -> Optional[Expert]:
        """获取专家"""
        return self.experts.get(expert_id)
    
    def list_experts(self) -> List[Expert]:
        """列出所有专家"""
        return list(self.experts.values())
