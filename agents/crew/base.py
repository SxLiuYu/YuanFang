"""
agents/crew/base.py
Crew 基类
"""
import logging

logger = logging.getLogger(__name__)


class CrewBase:
    """所有 Crew 的基类，定义通用接口"""

    def __init__(self):
        self.name = "CrewBase"
        self.agents = []
        self.tasks = []

    def add_agent(self, agent):
        self.agents.append(agent)
        return self

    def add_task(self, task):
        self.tasks.append(task)
        return self

    def execute(self, input_data: str) -> dict:
        """执行入口，由子类实现"""
        raise NotImplementedError

    def status(self) -> dict:
        return {
            "name": self.name,
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
        }
