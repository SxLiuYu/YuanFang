"""
agents/hyper/meta_agent.py
Meta Agent — 分析 Task Agent 表现，生成改进策略
"""
import json

DEFAULT_MODEL = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"


def chat_with_finna(model, messages, temperature=0.7, json_mode=False):
    from core.llm_adapter import get_llm
    return get_llm().chat_simple(messages, model=model, temperature=temperature, json_mode=json_mode)


class MetaAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.name = "MetaAgent"

    def analyze_and_improve(self, task_result: dict) -> dict:
        task = task_result.get("task", "")
        response = task_result.get("response", "")

        meta_prompt = f"""你是一个自进化系统的 Meta Agent（元优化器）。
你的职责是：审视 Task Agent 的表现，生成"如何在未来做得更好"的策略。

[Task Agent 任务]
{task}

[Task Agent 回答]
{response}

[分析要求]
请从以下几个维度分析 Task Agent 的表现，并给出具体改进策略：

1. 回答质量：是否准确、完整、有条理？
2. 推理过程：逻辑是否严密？有没有遗漏关键信息？
3. 可改进点：哪类问题容易出错？哪些步骤可以优化？
4. 策略生成：生成一个具体的、可复用的"改进提示"，用于指导未来相似任务的执行

[输出格式] - 必须返回合法 JSON：
{{
  "quality_score": 1-10,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["弱点1", "弱点2"],
  "improvement_strategy": "具体的改进提示，应该像系统提示一样注入给未来的 Task Agent",
  "domain_hint": "这个任务属于什么领域/类型（用于检索相似任务）",
  "tags": ["标签1", "标签2"]
}}

只返回JSON，不要其他内容。"""

        messages = [{"role": "user", "content": meta_prompt}]
        raw_response = chat_with_finna(self.model, messages, temperature=0.3, json_mode=True)

        try:
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0]
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {
                "quality_score": 5,
                "strengths": ["部分完成"],
                "weaknesses": ["分析失败"],
                "improvement_strategy": "保持现有方式",
                "domain_hint": "general",
                "tags": ["general"]
            }
