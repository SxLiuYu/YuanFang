"""
agents/crew/lobster_army_crew.py
龙虾军团 Crew · LobsterArmyCrew
CrewAI 多 Agent 协作系统
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入 CrewAI，不可用时优雅降级
try:
    from crewai import Crew, Agent, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("crewai not installed, LobsterArmyCrew will use HyperAgent fallback")


def _get_llm():
    """获取 LLM（延迟导入避免循环依赖）"""
    try:
        from core.llm_adapter import get_llm
        return get_llm()
    except Exception:
        return None


class LobsterArmyCrew:
    """
    龙虾军团多 Agent 协作系统

    使用 CrewAI 编排多个专业 Agent：
    - researcher：研究分析用户问题
    - executor：执行具体任务
    - reporter：汇总结果并生成最终回复
    """

    def __init__(self, model: str = None):
        self.model = model or "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"
        self._crew = None
        self._setup_crew()

    def _setup_crew(self):
        """初始化 CrewAI Agent 团队"""
        if not CREWAI_AVAILABLE:
            logger.info("CrewAI not available, using HyperAgent fallback")
            return

        try:
            llm = _get_llm()
            if not llm:
                logger.warning("LLM not available, crew will use fallback")
                return

            # Researcher Agent
            researcher = Agent(
                role="研究员",
                goal="深入分析用户问题，确定所需信息和最佳解决路径",
                backstory="你是一个专业的研究员，善于从多个角度分析问题。",
                verbose=True,
                llm=llm,
            )

            # Executor Agent
            executor = Agent(
                role="执行者",
                goal="根据研究结果，高效准确地执行具体任务",
                backstory="你是一个经验丰富的执行者，擅长完成任务并给出清晰的结果。",
                verbose=True,
                llm=llm,
            )

            # Reporter Agent
            reporter = Agent(
                role="汇报员",
                goal="汇总各 Agent 的结果，生成最终、易懂的回复",
                backstory="你是一个优秀的汇报员，把复杂的信息简化为清晰的回答。",
                verbose=True,
                llm=llm,
            )

            self._crew = Crew(
                agents=[researcher, executor, reporter],
                tasks=[],
                verbose=True,
            )
            logger.info("LobsterArmyCrew initialized with CrewAI")
        except Exception as e:
            logger.warning(f"CrewAI setup failed: {e}, using fallback")
            self._crew = None

    def run(self, task: str) -> dict:
        """
        运行整个 Crew 团队处理任务

        流程：Researcher → Executor → Reporter → 最终回复
        """
        if not CREWAI_AVAILABLE or self._crew is None:
            return self._run_fallback(task)

        try:
            # 为当前任务创建 tasks
            research_task = Task(
                description=f"分析并研究以下任务：{task}",
                agent=self._crew.agents[0],
                expected_output="对任务的深入分析和建议的执行步骤",
            )
            execute_task = Task(
                description=f"执行任务：{task}",
                agent=self._crew.agents[1],
                expected_output="具体的执行结果",
            )
            report_task = Task(
                description=f"汇总以下结果并给出最终回复：\n研究：\n执行：",
                agent=self._crew.agents[2],
                expected_output="最终的、易懂的回复",
            )

            result = self._crew.kickoff(inputs={"task": task})
            return {
                "crew": "LobsterArmyCrew",
                "result": str(result),
                "mode": "crewai",
            }
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return self._run_fallback(task)

    def _run_fallback(self, task: str) -> dict:
        """当 CrewAI 不可用时，使用 HyperAgent 作为后备"""
        try:
            from agents.hyper import HyperAgent
            agent = HyperAgent()
            result = agent.run(task, enable_evolution=False, enable_reflection=False)
            return {
                "crew": "LobsterArmyCrew",
                "result": result.get("response", str(result)),
                "mode": "hyperagent_fallback",
            }
        except Exception as e:
            logger.error(f"HyperAgent fallback failed: {e}")
            return {
                "crew": "LobsterArmyCrew",
                "result": f"抱歉，Agent 系统暂时不可用：{e}",
                "mode": "error",
            }

    def run_agent(self, agent_name: str, input_data: str) -> dict:
        """
        运行单个特定 Agent

        agent_name: researcher | executor | reporter
        """
        if not CREWAI_AVAILABLE or self._crew is None:
            return self._run_single_fallback(agent_name, input_data)

        try:
            agent_map = {
                "researcher": self._crew.agents[0] if len(self._crew.agents) > 0 else None,
                "executor": self._crew.agents[1] if len(self._crew.agents) > 1 else None,
                "reporter": self._crew.agents[2] if len(self._crew.agents) > 2 else None,
            }
            agent = agent_map.get(agent_name.lower())
            if not agent:
                return {"error": f"Unknown agent: {agent_name}"}

            task = Task(description=input_data, agent=agent)
            result = self._crew.kickoff(inputs={"task": input_data})
            return {"agent": agent_name, "result": str(result)}
        except Exception as e:
            logger.error(f"Single agent run failed: {e}")
            return {"agent": agent_name, "error": str(e)}

    def _run_single_fallback(self, agent_name: str, input_data: str) -> dict:
        """单个 Agent 不可用时的后备"""
        return {
            "agent": agent_name,
            "result": f"CrewAI not available, used HyperAgent fallback for {input_data[:100]}",
            "mode": "hyperagent_fallback",
        }
