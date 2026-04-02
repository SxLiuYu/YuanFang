"""
agents/hyper/task_agent.py
Task Agent — 执行具体任务的 Agent
"""
import datetime
from typing import Optional

DEFAULT_MODEL = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"


def chat_with_finna(model, messages, temperature=0.7, json_mode=False):
    from core.llm_adapter import get_llm
    return get_llm().chat_simple(messages, model=model, temperature=temperature, json_mode=json_mode)


class TaskAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.name = "TaskAgent"
        self.history = []

    def reset_history(self):
        self.history = []

    def add_system_prompt(self, prompt: str):
        self.history.insert(0, {"role": "system", "content": prompt})

    def query(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        response = chat_with_finna(self.model, self.history)
        self.history.append({"role": "assistant", "content": response})
        return response

    def execute(self, task: str, context: Optional[str] = None, personality_context: Optional[str] = None) -> dict:
        self.reset_history()

        system_prompt = """你是一个专业的 AI 助手，负责高效准确地完成用户任务。
始终尽力给出最好的回答。如果不确定，明确说明。
回答用中文，简洁有条理。"""
        if personality_context:
            system_prompt = personality_context
        self.add_system_prompt(system_prompt)

        if context:
            user_message = task + f"\n\n[改进策略参考] 过去相似任务的经验：\n{context}\n\n请结合以上经验完成任务。"
        else:
            user_message = task

        response = self.query(user_message)

        return {
            "task": task,
            "response": response,
            "model": self.model,
            "timestamp": datetime.datetime.now().isoformat()
        }
