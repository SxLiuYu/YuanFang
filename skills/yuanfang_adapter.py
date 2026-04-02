# skills/yuanfang_adapter.py
"""
Superpowers Skill 适配器 · YuanFang Skill Adapter
将 Superpowers skill 格式转换为 SkillEngine 可用格式
支持：SKILL.md 解析 + references/ 代码注入
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional

from core.skill_engine import Skill, get_skill_engine

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent


class SuperpowersSkillAdapter:
    """
    Superpowers Skill → YuanFang SkillEngine 适配器

    Superpowers skill 格式：
    skills/{name}/
      SKILL.md           # 描述（when_to_use, steps, references/）
      references/        # YuanFang-specific 实现文件

    适配器职责：
    1. 解析 SKILL.md 提取 trigger_patterns + description
    2. 生成 ha_commands 或 response_template
    3. 注册到 SkillEngine
    """

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or SKILLS_DIR
        self._skill_engine = None

    def _get_skill_engine(self):
        if self._skill_engine is None:
            self._skill_engine = get_skill_engine()
        return self._skill_engine

    def parse_skill_md(self, skill_dir: Path) -> dict:
        """
        解析 SKILL.md 文件，提取 skill 信息
        """
        md_file = skill_dir / "SKILL.md"
        if not md_file.exists():
            return {}

        content = md_file.read_text(encoding="utf-8")
        info = {}

        # 提取 name
        name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if name_match:
            info["name"] = name_match.group(1).strip()

        # 提取 description
        desc_match = re.search(r"## When to Use\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if desc_match:
            info["description"] = desc_match.group(1).strip()

        # 提取 trigger_patterns（从 steps 中提取关键词）
        steps_match = re.search(r"## Steps\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1)
            # 提取命令词和关键词
            patterns = []
            for line in steps_text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    pattern = re.sub(r"^[-*\d.)\s]+", "", line).strip()
                    if pattern and 2 <= len(pattern) <= 20:
                        patterns.append(pattern)
            info["trigger_patterns"] = patterns[:5]  # 最多5个

        # 提取 category
        category_match = re.search(r"Category:\s*(\w+)", content)
        if category_match:
            info["category"] = category_match.group(1)
        else:
            info["category"] = "conversation"

        return info

    def load_references(self, skill_dir: Path) -> dict:
        """
        加载 references/ 目录下的 YuanFang-specific 实现
        返回：{filename: content}
        """
        refs = {}
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for f in refs_dir.iterdir():
                if f.is_file() and f.suffix in [".py", ".md", ".json"]:
                    refs[f.name] = f.read_text(encoding="utf-8")
        return refs

    def import_from_directory(self, skill_dir: Path) -> Optional[Skill]:
        """
        从 Superpowers skill 目录导入并注册到 SkillEngine
        """
        skill_info = self.parse_skill_md(skill_dir)
        if not skill_info.get("name"):
            logger.warning(f"[SkillAdapter] No name found in {skill_dir}")
            return None

        skill = Skill(
            name=skill_info["name"],
            description=skill_info.get("description", ""),
            category=skill_info.get("category", "general"),
            trigger_patterns=skill_info.get("trigger_patterns", []),
            ha_commands=skill_info.get("ha_commands", []),
            response_template=skill_info.get("response_template", ""),
        )

        # 加载 references
        refs = self.load_references(skill_dir)
        if refs:
            skill.metadata["references"] = list(refs.keys())

        # 注册
        engine = self._get_skill_engine()
        skill_id = engine.register(skill)
        logger.info(f"[SkillAdapter] Imported {skill.name} ({skill_id})")
        return skill

    def import_all(self) -> list[Skill]:
        """
        自动扫描 skills_dir 并导入所有 Superpowers skills
        """
        imported = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skill = self.import_from_directory(item)
                if skill:
                    imported.append(skill)
        logger.info(f"[SkillAdapter] Imported {len(imported)} skills from {self.skills_dir}")
        return imported


def load_superpowers_skills() -> list[Skill]:
    """
    便捷函数：加载所有 Superpowers skills
    """
    adapter = SuperpowersSkillAdapter()
    return adapter.import_all()
