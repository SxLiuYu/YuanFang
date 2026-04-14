"""
agents/hyper/improvement_loop.py
SelfImprovingAgent 风格迭代反馈环
参考 NullLabTests/SelfImprovingAgent 的机制：
- 迭代生成 → 执行 → 反馈 → 改进 → 再执行
- 直到满足质量标准或达到最大迭代次数
"""
import ast
import logging
import time
import io
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def _chat_llm(prompt: str, model: str = "qwen3-235b-a22b", temperature: float = 0.5) -> str:
    from core.llm_adapter import get_llm
    messages = [{"role": "user", "content": prompt}]
    return get_llm().chat_simple(messages, model=model, temperature=temperature)


class ImprovementLoop:
    """
    迭代改进循环
    对于需要代码生成或精确输出的任务，使用迭代反馈环不断改进
    """

    def __init__(self, max_iterations: int = 5, quality_threshold: float = 8.0):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.iteration_history = []

    def _extract_code(self, response: str) -> Optional[str]:
        """从 LLM 响应中提取代码"""
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        if "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        # 没有代码块，尝试直接返回
        return response.strip() if len(response.strip()) < 2000 else ""

    def _execute_code(self, code: str) -> dict:
        """安全执行 Python 代码，返回结果"""
        output = io.StringIO()
        errors = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        start = time.time()
        try:
            sys.stdout = output
            sys.stderr = errors
            exec(code, {"__name__": "__improvement_loop__"})
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return {
                "success": True,
                "output": output.getvalue(),
                "error": "",
                "duration": time.time() - start,
            }
        except SyntaxError as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return {
                "success": False,
                "output": output.getvalue(),
                "error": f"SyntaxError: {e}",
                "duration": time.time() - start,
            }
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return {
                "success": False,
                "output": output.getvalue(),
                "error": f"{type(e).__name__}: {e}",
                "duration": time.time() - start,
            }

    def _evaluate_output(self, output: str, expected: str = "") -> float:
        """评估输出质量（0-10）"""
        if not expected:
            return 7.0  # 无预期时给基础分
        if expected.strip() in output.strip():
            return 10.0
        # 简单相似度评估
        overlap = len(set(expected.split()) & set(output.split())) / max(len(set(expected.split())), 1)
        return overlap * 10

    def run(self, task: str, expected_output: str = "", context: str = "") -> dict:
        """
        迭代改进循环主入口
        流程：生成 → 执行 → 评估 → 反馈 → 改进 → 直到质量达标或达到最大迭代
        """
        current_code = ""
        history = []

        prompt = f"""你是代码生成专家。请为以下任务生成 Python 代码。

任务：{task}
{('附加上下文：' + context) if context else ''}

要求：
- 输出完整可执行的 Python 代码
- 用 ```python ... ``` 包裹
- 不要解释，直接输出代码"""

        for i in range(self.max_iterations):
            iteration = i + 1
            logger.info(f"[ImprovementLoop] 迭代 {iteration}/{self.max_iterations}")

            # 生成代码
            if i == 0:
                response = _chat_llm(prompt, temperature=0.5)
            else:
                # 带反馈的改进
                feedback_prompt = f"""以下代码执行后有问题，请修复：

任务：{task}
上次代码：
```python
{current_code}
```

执行输出：{history[-1]['execution_result']['output'] if history else 'N/A'}
错误信息：{history[-1]['execution_result']['error'] if history else 'N/A'}

请生成修复后的代码，直接用 ```python ... ``` 包裹。"""
                response = _chat_llm(feedback_prompt, temperature=0.3)

            code = self._extract_code(response)
            if not code:
                logger.warning(f"[ImprovementLoop] 迭代 {iteration} 无法提取代码")
                continue

            # 执行代码
            exec_result = self._execute_code(code)

            # 评估质量
            if expected_output:
                quality = self._evaluate_output(exec_result["output"], expected_output)
            elif exec_result["success"]:
                quality = 8.0
            else:
                quality = 3.0

            history.append({
                "iteration": iteration,
                "code": code,
                "response": response,
                "execution_result": exec_result,
                "quality": quality,
            })

            logger.info(f"[ImprovementLoop] 迭代 {iteration}: quality={quality:.1f}, success={exec_result['success']}")

            # 达到阈值或成功且无错误则停止
            if quality >= self.quality_threshold:
                logger.info(f"[ImprovementLoop] 质量达标 ({quality:.1f})，停止迭代")
                break
            if exec_result["success"] and not exec_result["error"] and quality >= 7.0:
                logger.info(f"[ImprovementLoop] 执行成功且质量可接受，停止迭代")
                break

        # 选择最佳结果
        best = max(history, key=lambda h: h["quality"]) if history else {
            "iteration": 0,
            "code": "",
            "execution_result": {"success": False, "output": "", "error": "No iterations"},
            "quality": 0,
        }

        return {
            "task": task,
            "best_code": best["code"],
            "best_quality": best["quality"],
            "iterations_used": len(history),
            "history": history,
            "final_output": best["execution_result"]["output"],
            "final_error": best["execution_result"]["error"],
            "success": best["execution_result"]["success"],
        }
