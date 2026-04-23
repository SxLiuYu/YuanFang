"""
Mythos 配置模块
集成深度思考 + MoE 专家路由的 Agent 优化方案
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class MythosConfig:
    """
    Mythos 优化器核心配置
    
    核心功能开关：
        use_recurrent_depth: 是否使用循环深度推理（默认 True）
        use_moe: 是否使用 MoE 专家路由（默认 True）
        auto_use_depth: 是否自动根据复杂度启用深度思考（默认 False）
        auto_depth_threshold: 自动启用深度思考的复杂度阈值（默认 0.5）
    
    循环深度推理 (Recurrent-Depth Reasoning):
        max_thinking_steps: 最大思考步数（默认 10）
        min_reasoning_steps: 最少推理步数（默认 2）
        early_termination_threshold: 提前终止的质量阈值（默认 0.7）
    
    专家路由 (Expert Routing):
        n_experts: 总专家数量（默认 8）
        n_shared_experts: 始终激活的共享专家数量（默认 2）
        n_experts_per_tok: 每个请求激活的专家数（默认 4）
    
    自适应计算时间 (ACT):
        act_mode: ACT 模式 - "conservative" | "balanced" | "aggressive"（默认 "balanced"）
    
    其他:
        verbose: 是否输出详细日志（默认 False）
    """
    # 核心功能开关
    use_recurrent_depth: bool = True
    use_moe: bool = True
    auto_use_depth: bool = False
    auto_depth_threshold: float = 0.5
    
    # 循环深度推理
    max_thinking_steps: int = 10
    min_reasoning_steps: int = 2
    early_termination_threshold: float = 0.7
    
    # 兼容性：旧参数名
    max_loop_iters: int = 10
    min_loop_iters: int = 2
    act_threshold: float = 0.99
    
    # 专家路由
    n_experts: int = 8
    n_shared_experts: int = 2
    n_experts_per_tok: int = 4
    
    # 自适应计算时间
    act_mode: str = "balanced"  # "conservative", "balanced", "aggressive"
    
    # 其他
    enable_latent_space: bool = True
    enable_stability_injection: bool = True
    verbose: bool = False
    
    # 专家定义（可以动态添加）
    experts: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        # 兼容性映射
        if self.max_loop_iters != 10 and self.max_thinking_steps == 10:
            self.max_thinking_steps = self.max_loop_iters
        if self.min_loop_iters != 2 and self.min_reasoning_steps == 2:
            self.min_reasoning_steps = self.min_loop_iters
        
        if self.experts is None:
            # 默认专家配置
            self.experts = [
                {"id": "general", "name": "通用专家", "specialty": ["general", "chat", "conversation"]},
                {"id": "coding", "name": "编程专家", "specialty": ["code", "programming", "debug", "python", "javascript"]},
                {"id": "analysis", "name": "分析专家", "specialty": ["analysis", "data", "statistics", "math"]},
                {"id": "creative", "name": "创意专家", "specialty": ["creative", "writing", "story", "poem"]},
                {"id": "research", "name": "研究专家", "specialty": ["research", "paper", "academic", "science"]},
                {"id": "planning", "name": "规划专家", "specialty": ["plan", "schedule", "task", "project"]},
                {"id": "learning", "name": "教学专家", "specialty": ["teach", "explain", "tutorial", "learn"]},
                {"id": "tool", "name": "工具专家", "specialty": ["tool", "api", "integration", "automation"]},
            ]
    
    def get_expert_for_task(self, task_type: str) -> List[str]:
        """根据任务类型获取合适的专家"""
        if not self.experts:
            return []
        
        task_lower = task_type.lower()
        selected = []
        
        # 先找匹配的专家
        for expert in self.experts:
            for specialty in expert.get("specialty", []):
                if specialty in task_lower:
                    selected.append(expert["id"])
                    break
        
        # 如果不够，添加共享专家（前 n_shared_experts 个）
        if len(selected) < self.n_experts_per_tok:
            for expert in self.experts[:self.n_shared_experts]:
                if expert["id"] not in selected:
                    selected.append(expert["id"])
                    if len(selected) >= self.n_experts_per_tok:
                        break
        
        return selected[:self.n_experts_per_tok]


# 预设配置
def get_config(mode: str = "balanced") -> MythosConfig:
    """
    获取预设配置
    
    Args:
        mode: 配置模式
            - "fast": 快速模式（思考少，专家少）
            - "balanced": 平衡模式（默认）
            - "deep": 深度模式（思考多，专家多）
            - "research": 研究模式（最多思考，最多专家）
    """
    configs = {
        "fast": MythosConfig(
            max_thinking_steps=4,
            min_reasoning_steps=1,
            n_experts=4,
            n_shared_experts=1,
            n_experts_per_tok=2,
            act_mode="aggressive",
            early_termination_threshold=0.6,
        ),
        "balanced": MythosConfig(
            max_thinking_steps=8,
            min_reasoning_steps=2,
            n_experts=8,
            n_shared_experts=2,
            n_experts_per_tok=4,
            act_mode="balanced",
            early_termination_threshold=0.7,
        ),
        "deep": MythosConfig(
            max_thinking_steps=12,
            min_reasoning_steps=3,
            n_experts=12,
            n_shared_experts=2,
            n_experts_per_tok=5,
            act_mode="conservative",
            early_termination_threshold=0.8,
        ),
        "research": MythosConfig(
            max_thinking_steps=16,
            min_reasoning_steps=4,
            n_experts=16,
            n_shared_experts=3,
            n_experts_per_tok=6,
            act_mode="conservative",
            early_termination_threshold=0.85,
            verbose=True,
        ),
    }
    return configs.get(mode, configs["balanced"])
