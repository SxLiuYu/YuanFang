"""
services/evolution_scheduler.py
定时自进化调度器 — 定期运行 HyperAgent 任务，触发 MetaAgent 反思改进
"""
from __future__ import annotations
import os
import time
import threading
import logging
import datetime
import random

logger = logging.getLogger(__name__)

# 默认进化任务池 — 覆盖不同能力域
DEFAULT_EVOLUTION_TASKS = [
    "用 Python 写一个函数，判断给定字符串是否是回文串，要求代码简洁优雅",
    "解释一下什么是 RESTful API，设计原则有哪些",
    "分析一下为什么比特币早期的矿工能获得大量奖励，这公平吗",
    "给出一个提升代码可读性的具体方案，列举5个最佳实践",
    "用递归和迭代两种方式实现斐波那契数列，比较它们的时间和空间复杂度",
    "解释什么是函数式编程，Python 中有哪些函数式编程的特性和工具",
    "设计一个简单的任务队列系统，需要支持任务提交、执行、查询结果",
    "分析：大语言模型（LLM）有哪些已知的局限性和幻觉问题，如何缓解",
    "写一个算法来检测代码中的循环依赖",
    "解释什么是微服务架构，它相比单体架构有哪些优缺点",
    "用 Python 实现一个 LRU 缓存，了解其底层数据结构",
    "分析：为什么在分布式系统中时钟同步是一个难题，有什么解决方案",
]


class EvolutionScheduler:
    """
    定时自进化调度器
    运行在独立线程，定期触发 HyperAgent 的自进化流程：
    1. 从任务池选择任务
    2. 用 HyperAgent 执行（enable_evolution=True）
    3. MetaAgent 反思并存储改进策略
    """

    def __init__(self, interval_hours: float = 1, tasks_per_cycle: int = 3):
        """
        Args:
            interval_hours: 每次进化周期的间隔（小时）
            tasks_per_cycle: 每个周期执行多少个任务
        """
        self.interval_seconds = int(interval_hours * 3600)
        self._interval_hours = interval_hours  # store for status
        self.tasks_per_cycle = tasks_per_cycle
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_run = None
        self._total_runs = 0
        self._evolution_count = 0
        self._custom_tasks = None

        # 可配置的任务池（通过 env 或 set_tasks 设置）
        env_tasks = os.getenv("EVOLUTION_TASKS", "").strip()
        if env_tasks:
            self._custom_tasks = [t.strip() for t in env_tasks.split("|") if t.strip()]

    def set_tasks(self, tasks: list[str]):
        """设置自定义任务池"""
        self._custom_tasks = tasks

    def _get_tasks(self) -> list[str]:
        """获取本次周期要执行的任务"""
        pool = self._custom_tasks if self._custom_tasks else DEFAULT_EVOLUTION_TASKS
        if len(pool) <= self.tasks_per_cycle:
            return pool
        return random.sample(pool, self.tasks_per_cycle)

    def _run_cycle(self, max_retries: int = 2):
        """执行一次进化周期（带重试）"""
        import time as _time
        from agents.hyper import HyperAgent
        from core.personality import get_personality
        from core.memory_system import get_memory

        def _run_task_with_retry(task: str, attempt: int = 0) -> dict | None:
            agent = HyperAgent()
            personality = get_personality()
            memory = get_memory()
            context = memory.get_context_summary()
            personality_prompt = personality.get_system_prompt(context)

            try:
                result = agent.run(
                    task,
                    enable_evolution=True,
                    enable_reflection=True,
                    personality_context=personality_prompt,
                    memory_system=memory
                )
                improvement = result.get("improvement")
                if improvement:
                    score = improvement.get("quality_score", "?")
                    domain = improvement.get("domain_hint", "unknown")
                    logger.info(f"[Evolution] task done — domain={domain}, score={score}/10")
                else:
                    logger.info(f"[Evolution] task done — no improvement generated")
                return result
            except Exception as e:
                if attempt < max_retries:
                    wait = 2 ** attempt * 5
                    logger.warning(f"[Evolution] task failed (attempt {attempt+1}): {e}, retrying in {wait}s...")
                    _time.sleep(wait)
                    return _run_task_with_retry(task, attempt + 1)
                else:
                    logger.error(f"[Evolution] task failed after {max_retries+1} attempts: {e}")
                    return None

        tasks = self._get_tasks()
        agent = HyperAgent()
        personality = get_personality()
        memory = get_memory()
        context = memory.get_context_summary()
        personality_prompt = personality.get_system_prompt(context)

        results = []
        for task in tasks:
            result = _run_task_with_retry(task)
            if result:
                results.append(result)

        self._evolution_count = agent.evolution_count
        return results

    def start(self):
        if self._running:
            logger.warning("[EvolutionScheduler] Already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"[EvolutionScheduler] Started (interval={self.interval_seconds}s, tasks/cycle={self.tasks_per_cycle})")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[EvolutionScheduler] Stopped")

    def _run_loop(self):
        while self._running:
            try:
                self._last_run = datetime.datetime.now().isoformat()
                self._total_runs += 1
                logger.info(f"[EvolutionScheduler] Cycle #{self._total_runs} started at {self._last_run}")
                self._run_cycle()
                logger.info(f"[EvolutionScheduler] Cycle #{self._total_runs} completed, total evolutions stored: {self._evolution_count}")
            except Exception as e:
                logger.error(f"[EvolutionScheduler] Cycle error: {e}")
            time.sleep(self.interval_seconds)

    def trigger_now(self) -> dict:
        """手动立即触发一次进化周期"""
        logger.info("[EvolutionScheduler] Manual trigger started")
        results = self._run_cycle()
        self._last_run = datetime.datetime.now().isoformat()
        self._total_runs += 1
        return {
            "runs": self._total_runs,
            "last_run": self._last_run,
            "evolution_count": self._evolution_count,
            "tasks_executed": len(results)
        }

    def status(self) -> dict:
        return {
            "running": self._running,
            "interval_hours": self._interval_hours,
            "interval_seconds": self.interval_seconds,
            "tasks_per_cycle": self.tasks_per_cycle,
            "total_runs": self._total_runs,
            "last_run": self._last_run,
            "stored_evolutions": self._evolution_count,
            "custom_tasks": self._custom_tasks is not None
        }


# 全局实例
_evolution_scheduler: EvolutionScheduler | None = None


def get_evolution_scheduler() -> EvolutionScheduler:
    global _evolution_scheduler
    if _evolution_scheduler is None:
        interval = float(os.getenv("EVOLUTION_INTERVAL_HOURS", "1"))
        tasks = int(os.getenv("EVOLUTION_TASKS_PER_CYCLE", "3"))
        _evolution_scheduler = EvolutionScheduler(interval_hours=interval, tasks_per_cycle=tasks)
    return _evolution_scheduler
