# core/skill_sandbox.py
"""Skill sandbox and marketplace"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BUILTIN_SKILLS = [
    {
        "name": "ha_control",
        "description": "HomeAssistant device control skill",
        "category": "ha_control",
        "trigger_patterns": ["开关", "打开", "关闭", "调", "设置"],
        "ha_commands": [{"entity_id": "switch.example", "action": "toggle"}],
        "response_template": "已执行设备控制",
    },
    {
        "name": "environment_report",
        "description": "Report current indoor environment",
        "category": "conversation",
        "trigger_patterns": ["环境", "温度", "湿度", "空气质量"],
        "response_template": "当前环境正常",
    },
]


class SkillPermission:
    def __init__(self, read_only=False, allowed_domains=None, max_actions_per_run=5,
                 require_approval=False, allow_dangerous=False):
        self.read_only = read_only
        self.allowed_domains = allowed_domains or []
        self.max_actions_per_run = max_actions_per_run
        self.require_approval = require_approval
        self.allow_dangerous = allow_dangerous


class SkillSandbox:
    """Safe execution environment for skills"""

    def __init__(self):
        self._ha_executor = None

    def set_ha_executor(self, executor):
        self._ha_executor = executor

    def execute_safe(self, commands, permission: SkillPermission):
        if not commands:
            return []
        if permission.read_only:
            return [{"success": False, "result": "Read-only mode"}]
        if len(commands) > permission.max_actions_per_run:
            return [{"success": False, "result": f"Too many commands ({len(commands)} > {permission.max_actions_per_run})"}]
        if not self._ha_executor:
            return [{"success": False, "result": "HA executor not configured"}]
        return self._ha_executor(commands)


class SkillMarketplace:
    """Marketplace for downloading/installing skills"""

    @staticmethod
    def list_available():
        return BUILTIN_SKILLS

    @staticmethod
    def get_builtin_skills():
        return BUILTIN_SKILLS

    @staticmethod
    def install_from_json(skill_data, skill_engine, auto_approve=False):
        try:
            from core.skill_engine import Skill
            skill = Skill(
                name=skill_data.get("name", ""),
                description=skill_data.get("description", ""),
                category=skill_data.get("category", "general"),
                trigger_patterns=skill_data.get("trigger_patterns", []),
                ha_commands=skill_data.get("ha_commands", []),
                response_template=skill_data.get("response_template", ""),
            )
            skill_id = skill_engine.register(skill)
            return {"success": True, "skill_id": skill_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def validate_skill_definition(skill_data):
        required = ["name", "description"]
        missing = [k for k in required if k not in skill_data]
        if missing:
            return {"valid": False, "missing": missing}
        return {"valid": True}


_sandbox: Optional[SkillSandbox] = None


def get_sandbox() -> SkillSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = SkillSandbox()
    return _sandbox
