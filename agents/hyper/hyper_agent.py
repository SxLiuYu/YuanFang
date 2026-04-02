"""
agents/hyper/hyper_agent.py
HyperAgent — 自进化 Agent 系统，整合 Task + Meta + EvolutionaryMemory
"""
import logging
from agents.hyper.task_agent import TaskAgent
from agents.hyper.meta_agent import MetaAgent
from agents.hyper.evolutionary_memory import EvolutionaryMemory

logger = logging.getLogger(__name__)


class HyperAgent:
    def __init__(self):
        self.task_agent = TaskAgent()
        self.meta_agent = MetaAgent()
        self.memory = EvolutionaryMemory()
        self.evolution_count = 0
        logger.info("HyperAgent 初始化完成")

    def run(self, task: str, enable_evolution: bool = True, enable_reflection: bool = True,
             personality_context=None, memory_system=None) -> dict:
        logger.info(f"\n{'='*50}\nHyperAgent 任务: {task[:50]}{'...' if len(task) > 50 else ''}\n{'='*50}")

        context = None
        if enable_reflection:
            context = self.memory.get_context(task)
            if context:
                logger.info(f"检索到相关策略")

        logger.info("Task Agent 执行...")
        task_result = self.task_agent.execute(task, context=context, personality_context=personality_context)

        improvement = None
        if enable_reflection and enable_evolution:
            logger.info("Meta Agent 反思分析中...")
            improvement = self.meta_agent.analyze_and_improve(task_result)

            if improvement:
                logger.info(f"   质量评分: {improvement.get('quality_score', '?')}/10")
                self.memory.store(improvement, task[:100])
                self.evolution_count += 1

        if memory_system:
            try:
                memory_system.record_interaction(task, task_result["response"], "neutral")
            except Exception as e:
                logger.error(f"记忆记录失败: {e}")

        return {
            "task": task,
            "response": task_result["response"],
            "model": task_result["model"],
            "improvement": improvement,
            "evolution_count": self.evolution_count,
            "timestamp": task_result["timestamp"]
        }

    def status(self) -> dict:
        report = self.memory.evolution_report()
        return {
            "evolution_count": self.evolution_count,
            "memory_stats": report
        }
