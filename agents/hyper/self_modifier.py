"""
agents/hyper/self_modifier.py
Ouroboros 风格自我修改模块
参考 ouroboros/apply_patch.py + tools/control.py 实现
"""
import ast
import logging
import subprocess
import hashlib
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

GIT_TOKEN = os.environ.get("GIT_TOKEN", "")
GIT_USER = "SxLiuYu"
REPO_URL = "https://github.com/SxLiuYu/YuanFang.git"

# 自身源码文件列表（HyperAgent + 相关模块）
SELF_SOURCE_FILES = [
    "agents/hyper/hyper_agent.py",
    "agents/hyper/meta_agent.py",
    "agents/hyper/task_agent.py",
    "agents/hyper/evolutionary_memory.py",
    "agents/hyper/agent_team.py",
    "agents/hyper/improvement_loop.py",
    "agents/hyper/self_modifier.py",
]


def _chat_llm(prompt: str, model: str = "qwen3-235b-a22b") -> str:
    """调用 FinnA LLM"""
    from core.llm_adapter import get_llm
    messages = [{"role": "user", "content": prompt}]
    return get_llm().chat_simple(messages, model=model, temperature=0.3)


class SelfModifier:
    """
    自我修改器 — 读取自身源码、生成改进补丁、验证应用、提交 git
    参考 Ouroboros 的自进化机制：
    1. read_own_source() — 读取当前源码
    2. generate_patch() — LLM 基于任务执行结果生成改进代码
    3. apply_and_validate() — 语法检查 + 测试，失败回滚
    4. git_commit_push() — 提交并推送到 GitHub
    """

    def __init__(self, repo_dir: str = None):
        self.repo_dir = Path(repo_dir or "/Users/sxliuyu/YuanFang")
        self.improvements_count = 0
        self.last_improvement_hash = ""

    def read_own_source(self, rel_path: str) -> str:
        """读取自身源码文件"""
        path = self.repo_dir / rel_path
        if not path.exists():
            return f"# File not found: {rel_path}"
        return path.read_text(encoding="utf-8")

    def generate_patch(self, task_result: dict, target_file: str) -> str:
        """
        调用 LLM 基于任务执行结果生成代码改进补丁
        使用 Ouroboros 的 V4A patch 格式
        """
        current_code = self.read_own_source(target_file)

        prompt = f"""你是一个自我进化 AI 系统的代码改进器。
基于以下任务执行结果，分析并改进目标源码。

[任务]
{task_result.get('task', '')}

[执行结果]
{task_result.get('response', '')}

[质量评分]
{task_result.get('improvement', {}).get('quality_score', 'N/A')}/10

[可改进点]
{task_result.get('improvement', {}).get('weaknesses', [])}

[目标文件]
{target_file}

[当前源码]
```python
{current_code}
```

请生成改进后的完整源码文件内容，使用以下 JSON 格式返回（不要用 markdown 包裹）：
{{
  "file": "{target_file}",
  "reasoning": "简要说明改进思路",
  "new_code": "完整的新代码内容"
}}

只返回 JSON，不要其他内容。"""

        raw = _chat_llm(prompt)
        # 解析 JSON 响应
        import json
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            data = json.loads(raw.strip())
            return data.get("new_code", "")
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"[SelfModifier] JSON 解析失败: {e}, raw[:200]: {raw[:200]}")
            return ""

    def apply_and_validate(self, rel_path: str, new_code: str) -> bool:
        """
        应用代码变更并验证
        1. 语法检查（ast.parse）
        2. 导入检查
        3. 失败则回滚
        """
        path = self.repo_dir / rel_path
        # 备份
        backup_path = path.with_suffix(".py.bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

        try:
            # 语法检查
            ast.parse(new_code)

            # 写入新代码
            path.write_text(new_code, encoding="utf-8")

            # 导入检查
            module_name = str(path.relative_to(self.repo_dir)).replace("/", ".").replace(".py", "")
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                try:
                    importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(importlib.util.module_from_spec(spec))
                except Exception as e:
                    raise ImportError(f"Import check failed: {e}")

            # 清理备份
            backup_path.unlink(missing_ok=True)
            logger.info(f"[SelfModifier] 成功更新 {rel_path}")
            return True

        except SyntaxError as e:
            logger.warning(f"[SelfModifier] 语法错误，回滚: {e}")
            self._rollback(rel_path)
            return False
        except ImportError as e:
            logger.warning(f"[SelfModifier] 导入错误，回滚: {e}")
            self._rollback(rel_path)
            return False
        except Exception as e:
            logger.warning(f"[SelfModifier] 验证失败，回滚: {e}")
            self._rollback(rel_path)
            return False

    def _rollback(self, rel_path: str) -> None:
        """回滚到备份"""
        path = self.repo_dir / rel_path
        backup_path = path.with_suffix(".py.bak")
        if backup_path.exists():
            backup_path.rename(path)
            logger.info(f"[SelfModifier] 已回滚 {rel_path}")

    def git_commit_push(self, rel_path: str, message: str) -> bool:
        """提交并推送变更到 GitHub"""
        try:
            # 配置 git
            subprocess.run(["git", "config", "user.name", GIT_USER], cwd=self.repo_dir, check=True)
            subprocess.run(["git", "config", "user.email", f"{GIT_USER}@users.noreply.github.com"], cwd=self.repo_dir, check=True)

            # 添加文件
            subprocess.run(["git", "add", rel_path], cwd=self.repo_dir, check=True)

            # 提交
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.warning(f"[SelfModifier] 提交失败: {result.stderr}")
                return False

            # 推送
            remote = f"https://{GIT_TOKEN}@github.com/{GIT_USER}/YuanFang.git"
            result = subprocess.run(
                ["git", "push", remote, "HEAD:main", "--quiet"],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.warning(f"[SelfModifier] 推送失败: {result.stderr}")
                return False

            logger.info(f"[SelfModifier] 已提交并推送: {message}")
            return True

        except Exception as e:
            logger.error(f"[SelfModifier] Git 操作失败: {e}")
            return False

    def try_self_improve(self, task_result: dict) -> Optional[dict]:
        """
        尝试自我改进的主入口
        由 HyperAgent.run() 在任务执行后调用
        返回改进结果 dict 或 None
        """
        improvement = task_result.get("improvement", {})
        quality_score = improvement.get("quality_score", 5)

        # 只在质量分数较低时触发自我修改（保护机制）
        if quality_score >= 8:
            logger.info("[SelfModifier] 质量分数 >= 8，跳过自我修改")
            return None

        # 选择最需要改进的文件
        weaknesses = improvement.get("weaknesses", [])
        target_file = "agents/hyper/meta_agent.py"  # 默认

        if any("记忆" in w or "memory" in w.lower() for w in weaknesses):
            target_file = "agents/hyper/evolutionary_memory.py"
        elif any("执行" in w or "task" in w.lower() for w in weaknesses):
            target_file = "agents/hyper/task_agent.py"
        elif any("进化" in w or "evolve" in w.lower() for w in weaknesses):
            target_file = "agents/hyper/hyper_agent.py"

        # 生成改进代码
        new_code = self.generate_patch(task_result, target_file)
        if not new_code:
            logger.warning("[SelfModifier] 未生成有效补丁")
            return None

        # 应用并验证
        if not self.apply_and_validate(target_file, new_code):
            return None

        # Git 提交
        code_hash = hashlib.md5(new_code.encode()).hexdigest()[:8]
        message = f"self-improve: auto-evolution cycle {self.improvements_count + 1} [{code_hash}]"
        pushed = self.git_commit_push(target_file, message)

        self.improvements_count += 1
        self.last_improvement_hash = code_hash

        result = {
            "file": target_file,
            "hash": code_hash,
            "committed": pushed,
            "count": self.improvements_count,
        }
        logger.info(f"[SelfModifier] 自我改进完成: {result}")
        return result
