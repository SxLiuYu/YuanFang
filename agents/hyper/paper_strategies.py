"""
agents/hyper/paper_strategies.py
Awesome-Self-Evolving-Agents 学术论文知识库集成
从自进化 Agent 论文中提取最新策略，注入 MetaAgent 的改进决策
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# 关键论文的策略摘要（手动整理，后续可自动爬取更新）
PAPER_STRATEGIES = {
    "DGM_Darwin_Godel_Machine": {
        "title": "Darwin-Gödel Machine: Self-Improving AI via Genetic & Gödelian Self-Modification",
        "key_insight": "递归自我改进的关键：AI 系统通过经验驱动的变异和验证来优化自身的元算法。自我修改比被动的策略检索效果更好。",
        "strategy": "让 MetaAgent 不仅检索记忆策略，还要主动生成并测试新的元策略（meta-strategy），用实验反馈验证其有效性。",
        "applicable_to": "evolutionary_memory",  # 对应 YuanFang 模块
    },
    "MASLab": {
        "title": "MASLab: A Unified and Comprehensive Codebase for LLM-based Multi-Agent Systems",
        "key_insight": "多Agent系统的统一架构框架，核心是 Agent 间的通信协议和任务分解模式。",
        "strategy": "为 HyperAgent 的 AgentTeam 增加标准化的 agent 间通信协议，参考 MASLab 的消息格式和状态同步机制。",
        "applicable_to": "agent_team",
    },
    "Symbolic_Learning": {
        "title": "Symbolic Learning Enables Self-Evolving Agents",
        "key_insight": "符号学习使自进化 Agent 能够通过符号规则的可解释变化来实现自我改进，比纯神经方法更具可控性。",
        "strategy": "在 EvolutionaryMemory 中增加符号规则层：存储可解释的 if-then 规则，而不仅是嵌入向量。",
        "applicable_to": "evolutionary_memory",
    },
    "Agentic_RPO": {
        "title": "Agentic Reinforced Policy Optimization (Agentic RPO)",
        "key_insight": "用强化学习思路优化 Agent 策略：让 Agent 生成多种行动方案，用 Reward 模型打分，用排序损失训练策略模型。",
        "strategy": "给 MetaAgent 增加行动方案评分机制：为 Task Agent 的输出生成多个替代方案，评分后用最好的策略更新记忆。",
        "applicable_to": "meta_agent",
    },
    "SEAgent": {
        "title": "SEAgent: Self-Evolving Computer Use Agent with Autonomous Learning",
        "key_insight": "自进化计算机使用 Agent，能从每次计算机操作的成功/失败中学习，自主改进操作策略。",
        "strategy": "增加操作历史反馈：记录每次工具调用的成功/失败，用这些经验自动更新工具使用的系统提示词。",
        "applicable_to": "task_agent",
    },
    "AutoFlow": {
        "title": "AutoFlow: Automated Workflow Generation for LLM Agents",
        "key_insight": "自动生成 Agent 工作流的框架：通过 LLM 分析任务图谱，自动生成最优的工具调用序列。",
        "strategy": "给 HyperAgent 增加工作流自动生成能力：根据任务描述自动决定工具调用顺序和依赖关系。",
        "applicable_to": "hyper_agent",
    },
}


class PaperStrategyEngine:
    """
    论文策略引擎 — 从学术论文中提取的自进化 Agent 策略
    用这些最新研究来增强 MetaAgent 的改进决策
    """

    def __init__(self):
        self.strategies = PAPER_STRATEGIES
        self.used_strategies = []

    def get_relevant_strategies(self, task_type: str, improvement_hints: list) -> list:
        """
        根据任务类型和当前改进线索，返回最相关的论文策略
        """
        relevant = []

        for key, strategy in self.strategies.items():
            applicable = strategy["applicable_to"]
            # 简单关键词匹配
            if any(kw in task_type or kw in " ".join(improvement_hints)
                   for kw in [applicable, task_type, "evolution", "agent", "memory"]):
                relevant.append(strategy)

        return relevant[:3]  # 最多返回3个

    def inject_into_prompt(self, task_type: str, improvement_hints: list, base_prompt: str) -> str:
        """
        将论文策略注入到 LLM prompt 中
        MetaAgent 在做改进决策时调用此方法
        """
        strategies = self.get_relevant_strategies(task_type, improvement_hints)
        if not strategies:
            return base_prompt

        strategies_text = "\n\n".join(
            f"[{s['title']}]\n启发: {s['key_insight']}\n应用建议: {s['strategy']}"
            for s in strategies
        )

        enhanced_prompt = f"""{base_prompt}

[最新学术论文启发 — 可选择性应用]
{strategies_text}
"""
        self.used_strategies.extend([s["title"] for s in strategies])
        return enhanced_prompt

    def get_strategy_report(self) -> dict:
        """获取当前已使用的策略报告"""
        return {
            "total_strategies": len(self.strategies),
            "used_count": len(self.used_strategies),
            "used_strategies": list(set(self.used_strategies)),
        }


# 全局单例
_paper_engine: Optional[PaperStrategyEngine] = None


def get_paper_engine() -> PaperStrategyEngine:
    global _paper_engine
    if _paper_engine is None:
        _paper_engine = PaperStrategyEngine()
    return _paper_engine
