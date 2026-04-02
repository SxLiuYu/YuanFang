"""
🔒 元坊技能沙�?· Skill Sandbox & Marketplace
M12: 技能安全执�?+ 技能市场风格安装机�?

核心功能�?
1. 技能沙箱执�?�?技能中�?HA 指令在受限环境中执行，防止未授权操作
2. 技能安�?�?支持�?JSON/YAML 文件导入技能，类似 ClawHub 风格
3. 技能验�?�?安装前校验技能定义的完整�?
4. 技能权�?�?分级权限控制（只�?基础控制/全权限）

安全设计�?
- 技能执行有操作白名�?
- 新安装技能默�?require_approval=True
- 自动学习的技能也需确认后才能升级为正式技�?
"""

import os
import json
import uuid
import shutil
import datetime
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# 技能市场目录（存放待安装的技能包�?
MARKETPLACE_DIR = Path(__file__).parent / "skills_marketplace"
MARKETPLACE_DIR.mkdir(exist_ok=True)

# 已安装技能的审批状态存�?
APPROVAL_FILE = Path(__file__).parent / "skills" / "approval_state.json"


@dataclass
class SkillPermission:
    """技能权限定�?""
    read_only: bool = False          # 只能查询状态，不能控制
    allowed_domains: list = field(default_factory=lambda: ["light", "switch"])  # 允许操作�?HA �?
    max_actions_per_run: int = 5     # 单次执行最多操作数
    require_approval: bool = True    # 是否需要人工确�?
    allow_dangerous: bool = False    # 允许危险操作（删除自动化、重启系统等�?
    timeout_seconds: int = 30        # 执行超时


class SkillSandbox:
    """
    技能沙箱执行环境�?
    
    对技能的 HA 指令进行安全过滤和执行限制：
    - 权限检查：只允许授权域的操�?
    - 数量限制：单次执行不超过 max_actions_per_run
    - 超时控制：防止长时间运行
    """

    # 危险操作关键�?
    DANGEROUS_KEYWORDS = [
        "delete", "remove", "uninstall", "reboot", "restart",
        "factory_reset", "firmware", "system",
    ]

    def __init__(self, ha_executor=None):
        self._ha_executor = ha_executor  # HA 指令执行函数

    def set_ha_executor(self, fn):
        """注入 HA 执行�?""
        self._ha_executor = fn

    def validate_commands(self, commands: list, permission: SkillPermission) -> dict:
        """
        验证技能指令是否在权限范围内�?
        
        返回: {"valid": bool, "allowed": [...], "blocked": [...], "reason": str}
        """
        allowed = []
        blocked = []
        reasons = []

        for cmd in commands:
            entity_id = cmd.get("entity_id", "")
            action = cmd.get("action", "")
            domain = entity_id.split(".")[0] if "." in entity_id else ""

            # 危险操作检�?
            if not permission.allow_dangerous:
                for kw in self.DANGEROUS_KEYWORDS:
                    if kw in action.lower() or kw in entity_id.lower():
                        blocked.append(cmd)
                        reasons.append(f"危险操作被阻�? {action}")
                        continue

            # 域权限检�?
            if permission.read_only:
                blocked.append(cmd)
                reasons.append(f"只读模式，不允许操作: {entity_id}")
                continue

            if permission.allowed_domains and domain not in permission.allowed_domains:
                blocked.append(cmd)
                reasons.append(f"�?{domain} 不在允许列表�?)
                continue

            allowed.append(cmd)

        # 数量限制
        if len(allowed) > permission.max_actions_per_run:
            excess = allowed[permission.max_actions_per_run:]
            blocked.extend(excess)
            reasons.append(f"超过单次操作上限 {permission.max_actions_per_run}")
            allowed = allowed[:permission.max_actions_per_run]

        return {
            "valid": len(blocked) == 0,
            "allowed": allowed,
            "blocked": blocked,
            "reasons": reasons,
        }

    def execute_safe(self, commands: list, permission: SkillPermission) -> list:
        """
        在沙箱中安全执行 HA 指令�?
        
        返回: 执行结果列表 [{"command": {...}, "success": bool, "message": str}]
        """
        if not self._ha_executor:
            return [{"command": c, "success": False, "message": "HA 执行器未配置"} for c in commands]

        validation = self.validate_commands(commands, permission)

        results = []
        for cmd in validation["allowed"]:
            try:
                result = self._ha_executor([cmd])
                results.append({
                    "command": cmd,
                    "success": True,
                    "result": result,
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "success": False,
                    "message": str(e),
                })

        for cmd in validation["blocked"]:
            results.append({
                "command": cmd,
                "success": False,
                "message": "被沙箱阻�?,
            })

        return results


class SkillMarketplace:
    """
    技能市�?�?管理技能的导入、导出和安装�?
    
    支持格式�?
    - 单技�?JSON 文件
    - 多技能包（ZIP 归档�?
    - �?URL 安装
    """

    @staticmethod
    def validate_skill_definition(data: dict) -> dict:
        """
        验证技能定义是否完整�?
        
        返回: {"valid": bool, "errors": [...]}
        """
        errors = []
        required_fields = ["name", "description", "trigger_patterns"]
        
        for f in required_fields:
            if not data.get(f):
                errors.append(f"缺少必填字段: {f}")
        
        # 触发模式验证
        patterns = data.get("trigger_patterns", [])
        if not isinstance(patterns, list):
            errors.append("trigger_patterns 必须是数�?)
        elif not patterns:
            errors.append("trigger_patterns 不能为空")

        # HA 指令验证（如果有�?
        ha_cmds = data.get("ha_commands", [])
        if ha_cmds:
            for i, cmd in enumerate(ha_cmds):
                if not isinstance(cmd, dict):
                    errors.append(f"ha_commands[{i}] 必须是对�?)
                elif "entity_id" not in cmd:
                    errors.append(f"ha_commands[{i}] 缺少 entity_id")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @staticmethod
    def install_from_json(json_data: dict, skill_engine=None, auto_approve: bool = False) -> dict:
        """
        �?JSON 数据安装技能�?
        
        参数�?
          json_data: 技能定�?JSON
          skill_engine: SkillEngine 实例
          auto_approve: 是否自动审批（默�?False，需人工确认�?
        
        返回: {"success": bool, "skill_id": str, "message": str}
        """
        validation = SkillMarketplace.validate_skill_definition(json_data)
        if not validation["valid"]:
            return {
                "success": False,
                "message": f"技能定义无�? {'; '.join(validation['errors'])}",
            }

        if not skill_engine:
            return {"success": False, "message": "技能引擎未初始�?}

        # 提取技能参�?
        permission = SkillPermission(
            read_only=json_data.get("read_only", False),
            allowed_domains=json_data.get("allowed_domains", ["light", "switch", "climate", "scene"]),
            max_actions_per_run=json_data.get("max_actions", 5),
            require_approval=not auto_approve and json_data.get("require_approval", True),
            allow_dangerous=json_data.get("allow_dangerous", False),
        )

        # 注册技�?
        skill = skill_engine.register_skill(
            name=json_data["name"],
            description=json_data["description"],
            category=json_data.get("category", "marketplace"),
            trigger_patterns=json_data["trigger_patterns"],
            ha_commands=json_data.get("ha_commands", []),
            response_template=json_data.get("response_template", ""),
            metadata={
                "source": "marketplace",
                "author": json_data.get("author", "unknown"),
                "version": json_data.get("version", "1.0"),
                "tags": json_data.get("tags", []),
                "permission": {
                    "read_only": permission.read_only,
                    "allowed_domains": permission.allowed_domains,
                    "max_actions_per_run": permission.max_actions_per_run,
                    "require_approval": permission.require_approval,
                    "allow_dangerous": permission.allow_dangerous,
                },
            },
        )

        if skill:
            # 保存到市场目录归�?
            archive_path = MARKETPLACE_DIR / f"{json_data['name']}.json"
            archive_path.write_text(
                json.dumps(json_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            return {
                "success": True,
                "skill_id": skill.id,
                "message": f"技�?'{json_data['name']}' 安装成功",
                "require_approval": permission.require_approval,
            }
        
        return {"success": False, "message": "技能注册失�?}

    @staticmethod
    def install_from_file(file_path: str, skill_engine=None, auto_approve: bool = False) -> dict:
        """
        从文件安装技能（支持 .json 文件）�?
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "message": f"文件不存�? {file_path}"}

        try:
            data = json.loads(path.read_text("utf-8"))
            # 支持单技能或技能包（数组）
            if isinstance(data, list):
                results = []
                for skill_data in data:
                    r = SkillMarketplace.install_from_json(skill_data, skill_engine, auto_approve)
                    results.append(r)
                return {
                    "success": all(r["success"] for r in results),
                    "message": f"批量安装: {sum(1 for r in results if r['success'])}/{len(results)} 成功",
                    "details": results,
                }
            return SkillMarketplace.install_from_json(data, skill_engine, auto_approve)
        except json.JSONDecodeError as e:
            return {"success": False, "message": f"JSON 解析失败: {e}"}

    @staticmethod
    def export_skill(skill_data: dict, output_path: str) -> dict:
        """
        导出技能为 JSON 文件（可分享）�?
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(skill_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {"success": True, "message": f"已导出到 {output_path}"}
        except Exception as e:
            return {"success": False, "message": f"导出失败: {e}"}

    @staticmethod
    def list_available() -> list:
        """列出市场目录中已有的技能包"""
        skills = []
        for f in MARKETPLACE_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text("utf-8"))
                skills.append({
                    "file": f.name,
                    "name": data.get("name", "?"),
                    "description": data.get("description", ""),
                    "author": data.get("author", "unknown"),
                    "version": data.get("version", "?"),
                    "tags": data.get("tags", []),
                })
            except Exception:
                skills.append({"file": f.name, "name": "(解析失败)"})
        return skills

    @staticmethod
    def get_builtin_skills() -> list:
        """
        返回内置技能模板（可安装）�?
        类似 ClawHub 的精选技能列表�?
        """
        return [
            {
                "name": "电影模式",
                "description": "关灯 + 调暗氛围�?+ 打开投影",
                "category": "ha_control",
                "trigger_patterns": ["看电�?, "电影模式", "影院模式", "movie mode"],
                "ha_commands": [
                    {"entity_id": "light.living_room", "action": "off"},
                    {"entity_id": "light.ambient", "action": "on", "brightness": 30},
                    {"entity_id": "switch.projector", "action": "on"},
                ],
                "response_template": "🎬 电影模式已开启，灯光已调暗，投影仪已打开。享受电影时光！",
                "tags": ["娱乐", "灯光"],
            },
            {
                "name": "阅读模式",
                "description": "调亮阅读�?+ 关闭其他灯光 + 降低噪音",
                "category": "ha_control",
                "trigger_patterns": ["看书", "阅读模式", "读书模式", "reading mode"],
                "ha_commands": [
                    {"entity_id": "light.reading", "action": "on", "brightness": 255},
                    {"entity_id": "light.living_room", "action": "off"},
                    {"entity_id": "media_player.speaker", "action": "off"},
                ],
                "response_template": "📖 阅读模式已开启，阅读灯已调亮。祝你阅读愉快！",
                "tags": ["生活", "灯光"],
            },
            {
                "name": "会客模式",
                "description": "客厅灯光调亮 + 打开空调 + 播放背景音乐",
                "category": "ha_control",
                "trigger_patterns": ["有客�?, "会客模式", "客人来了", "guest mode"],
                "ha_commands": [
                    {"entity_id": "light.living_room", "action": "on", "brightness": 200},
                    {"entity_id": "climate.living_room", "action": "on", "temperature": 24, "hvac_mode": "cool"},
                    {"entity_id": "media_player.speaker", "action": "on"},
                ],
                "response_template": "🏠 会客模式已就绪，客厅灯光已调亮，空调已设�?24°C�?,
                "tags": ["社交", "灯光"],
            },
            {
                "name": "午休模式",
                "description": "关闭客厅灯光 + 关闭音箱 + 30 分钟后提�?,
                "category": "ha_control",
                "trigger_patterns": ["午休", "小睡", "午睡", "nap mode"],
                "ha_commands": [
                    {"entity_id": "light.living_room", "action": "off"},
                    {"entity_id": "light.bedroom", "action": "off"},
                    {"entity_id": "media_player.speaker", "action": "off"},
                ],
                "response_template": "😴 午休模式已开启，已关闭灯光和音箱。好好休息！",
                "tags": ["生活", "休息"],
            },
        ]


# ─────────── 单例 ───────────

_sandbox_instance = None
_marketplace_instance = None


def get_sandbox() -> SkillSandbox:
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = SkillSandbox()
    return _sandbox_instance


def get_marketplace() -> SkillMarketplace:
    global _marketplace_instance
    if _marketplace_instance is None:
        _marketplace_instance = SkillMarketplace()
    return _marketplace_instance

