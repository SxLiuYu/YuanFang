"""
agents/hyper/agent_team.py
Miguel 风格多 Agent 协作模块
参考 soulfir/miguel 的 Agno Team 架构：
- Coordinator (主调度) + Coder + Researcher + Analyst 子Agent
- 每个子Agent有独立上下文，避免上下文污染
- 子Agent可创建新工具、修改自身提示词
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


def _chat_llm(prompt: str, model: str = "qwen3-235b-a22b", temperature: float = 0.7) -> str:
    from core.llm_adapter import get_llm
    messages = [{"role": "user", "content": prompt}]
    return get_llm().chat_simple(messages, model=model, temperature=temperature)


class SubAgent:
    """独立子Agent，每个有自己专注的角色和上下文"""

    def __init__(self, name: str, role: str, goal: str, backstory: str, model: str = "qwen3-235b-a22b"):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.model = model
        self.tools = []

    def run(self, task: str, context: str = "") -> dict:
        """执行子Agent任务"""
        system_prompt = f"""你是 {self.role}。

目标：{self.goal}
背景：{self.backstory}

{('附加上下文: ' + context) if context else ''}

请执行任务，直接返回结果。"""

        start = time.time()
        response = _chat_llm(f"{system_prompt}\n\n任务：{task}\n\n结果：", model=self.model, temperature=0.7)
        duration = time.time() - start

        return {
            "agent": self.name,
            "role": self.role,
            "response": response,
            "duration_sec": round(duration, 2),
        }


class AgentTeam:
    """
    多Agent协作团队 — Miguel 风格
    协调器（HyperAgent）负责任务分解和调度
    专业化子Agent执行具体工作
    """

    def __init__(self, model: str = "qwen3-235b-a22b"):
        self.model = model
        self.coder = SubAgent(
            name="Coder",
            role="编码专家",
            goal="编写、调试、优化代码。能读源码、理解架构、写高质量实现。",
            backstory="你是一个经验丰富的软件工程师，精通 Python、架构设计、性能优化。",
            model=model,
        )
        self.researcher = SubAgent(
            name="Researcher",
            role="研究员",
            goal="深入调研主题，从多信息源综合分析，给出有深度的研究结论。",
            backstory="你是一个专业的研究员，善于多角度分析问题，挖掘深层原因。",
            model=model,
        )
        self.analyst = SubAgent(
            name="Analyst",
            role="分析师",
            goal="分析数据、文件、日志，找出规律、异常和改进机会。",
            backstory="你是一个严谨的数据分析师，擅长从复杂信息中提炼洞察。",
            model=model,
        )
        self.coordinator = SubAgent(
            name="Coordinator",
            role="协调员",
            goal="分解复杂任务，分派给最合适的子Agent，整合结果给出最终答案。",
            backstory="你是一个经验丰富的技术协调者，善于把复杂任务拆解为可执行的子任务。",
            model=model,
        )
        logger.info("AgentTeam 初始化完成: Coordinator + Coder + Researcher + Analyst")

    def run(self, task: str, enable_delegation: bool = True) -> dict:
        """
        主入口：协调器判断是否需要分解任务
        - 简单任务：直接执行
        - 复杂任务：分解后并行/串行调度子Agent
        """
        # 判断任务复杂度
        is_complex = any(kw in task for kw in [
            "分析", "研究", "调研", "设计", "实现", "构建", "比较",
            "调查", "优化", "架构", "多步", "复杂"
        ])

        if not enable_delegation or not is_complex:
            # 简单任务：协调器直接处理
            result = self.coordinator.run(task)
            return {
                "mode": "direct",
                "coordinator_result": result,
                "sub_agents_used": [],
            }

        # 复杂任务：协调器先分析如何分解
        plan_prompt = f"""分析以下任务，判断如何分解为子任务：

任务：{task}

如果任务可以分解为多个独立子任务，请用以下格式回答（只返回 JSON）：
{{
  "strategy": "parallel" 或 "sequential"，
  "tasks": [
    {{"agent": "Coder|Researcher|Analyst", "description": "具体任务描述"}},
    ...
  ]
}}

如果任务不需要分解（已是单一职责），回答：
{{
  "strategy": "direct",
  "tasks": []
}}

只返回 JSON。"""

        plan_raw = _chat_llm(plan_prompt, temperature=0.3)
        import json
        try:
            if "```json" in plan_raw:
                plan_raw = plan_raw.split("```json")[1].split("```")[0]
            plan = json.loads(plan_raw.strip())
        except:
            plan = {"strategy": "direct", "tasks": []}

        strategy = plan.get("strategy", "direct")
        sub_tasks = plan.get("tasks", [])

        if strategy == "direct" or not sub_tasks:
            result = self.coordinator.run(task)
            return {
                "mode": "direct",
                "coordinator_result": result,
                "sub_agents_used": [],
            }

        # 执行子任务
        agent_map = {
            "Coder": self.coder,
            "Researcher": self.researcher,
            "Analyst": self.analyst,
        }

        sub_results = []
        if strategy == "parallel":
            # 并行执行（简化串行，实际可 multiprocessing）
            for st in sub_tasks:
                agent = agent_map.get(st["agent"], self.coordinator)
                r = agent.run(st["description"])
                sub_results.append(r)
        else:
            # 串行执行，上下文累积
            context = ""
            for st in sub_tasks:
                agent = agent_map.get(st["agent"], self.coordinator)
                r = agent.run(st["description"], context=context)
                sub_results.append(r)
                context += f"\n[{agent.name} 结果]\n{r['response']}"

        # 协调器整合
        integration_prompt = f"""整合以下子Agent的执行结果，给出最终答案：

原始任务：{task}

子Agent结果：
{chr(10).join(f"[{r['agent']}] {r['response']}" for r in sub_results)}

请给出完整、一致的最终回答。
"""

        final = _chat_llm(integration_prompt, temperature=0.5)

        return {
            "mode": "team",
            "strategy": strategy,
            "sub_results": sub_results,
            "final_response": final,
            "sub_agents_used": [r["agent"] for r in sub_results],
        }
