"""
core/rule_engine.py
规则引擎 · RuleEngine
场景自动化：条件 → 动作 执行
"""
import os
import re
import json
import logging
import datetime
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

RULES_DIR = Path(__file__).parent.parent / "data" / "rules"
RULES_DIR.mkdir(parents=True, exist_ok=True)
RULES_FILE = RULES_DIR / "rules.json"


class Rule:
    """单条自动化规则"""
    def __init__(self, rule_id: str, name: str, condition: dict,
                 action: list, enabled: bool = True, priority: int = 0):
        self.id = rule_id
        self.name = name
        self.condition = condition   # {"type": "time"|"device"|"sensor", ...}
        self.action = action          # [{"entity_id": "...", "action": "turn_on"}, ...]
        self.enabled = enabled
        self.priority = priority
        self.last_triggered = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "condition": self.condition,
            "action": self.action, "enabled": self.enabled,
            "priority": self.priority, "last_triggered": self.last_triggered,
        }


class RuleEngine:
    """
    场景自动化规则引擎
    支持：
    - 时间触发（cron 表达式或时间段）
    - 设备状态触发（传感器/开关变化）
    - 组合条件（与/或）
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._ha_executor: Optional[Callable] = None
        self._notify_fn: Optional[Callable] = None
        self._skill_engine_fn: Optional[Callable] = None
        self._load_rules()

    def _load_rules(self):
        if RULES_FILE.exists():
            try:
                data = json.loads(RULES_FILE.read_text("utf-8"))
                for rid, rdata in data.get("rules", {}).items():
                    self._rules[rid] = Rule(**rdata)
                logger.info(f"[RuleEngine] Loaded {len(self._rules)} rules")
            except Exception as e:
                logger.warning(f"[RuleEngine] Load failed: {e}")

    def _save_rules(self):
        data = {"rules": {rid: r.to_dict() for rid, r in self._rules.items()}}
        RULES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_ha_executor(self, fn: Callable):
        self._ha_executor = fn

    def set_notify_fn(self, fn: Callable):
        self._notify_fn = fn

    def set_skill_engine_fn(self, fn: Callable):
        self._skill_engine_fn = fn

    # ──── 条件评估 ────

    def evaluate_condition(self, condition: dict, context: dict) -> bool:
        """评估条件是否满足"""
        ctype = condition.get("type", "")

        if ctype == "time_range":
            now = datetime.datetime.now()
            start = condition.get("start", "00:00")
            end = condition.get("end", "23:59")
            current_min = now.hour * 60 + now.minute
            start_h, start_m = map(int, start.split(":"))
            end_h, end_m = map(int, end.split(":"))
            start_min = start_h * 60 + start_m
            end_min = end_h * 60 + end_m
            return start_min <= current_min <= end_min

        elif ctype == "device_state":
            entity_id = condition.get("entity_id")
            expected_state = condition.get("state")
            actual = context.get("device_states", {}).get(entity_id, {})
            return actual.get("state") == expected_state

        elif ctype == "sensor_above":
            entity_id = condition.get("entity_id")
            threshold = condition.get("threshold", 0)
            actual = context.get("sensor_readings", {}).get(entity_id, {}).get("value", 0)
            return actual > threshold

        elif ctype == "presence":
            zone = condition.get("zone", "home")
            state = context.get("presence", {}).get(zone, "away")
            return state == condition.get("expected", "home")

        elif ctype == "and":
            return all(self.evaluate_condition(c, context) for c in condition.get("conditions", []))

        elif ctype == "or":
            return any(self.evaluate_condition(c, context) for c in condition.get("conditions", []))

        return False

    # ──── 规则执行 ────

    def check_and_fire(self, context: dict) -> list[dict]:
        """检查所有规则的条件，满足则执行"""
        results = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            try:
                if self.evaluate_condition(rule.condition, context):
                    result = self._execute_rule(rule)
                    results.append({"rule": rule.name, "result": result})
                    rule.last_triggered = datetime.datetime.now().isoformat()
                    self._save_rules()
            except Exception as e:
                logger.error(f"[RuleEngine] Rule {rule.name} failed: {e}")
                results.append({"rule": rule.name, "error": str(e)})
        return results

    def _execute_rule(self, rule: Rule) -> dict:
        """执行规则动作"""
        if not self._ha_executor:
            return {"executed": False, "reason": "no HA executor"}

        try:
            ha_results = self._ha_executor(rule.action)
            success_count = sum(1 for r in ha_results if r.get("success"))
            return {
                "executed": True,
                "total": len(rule.action),
                "success": success_count,
                "details": ha_results,
            }
        except Exception as e:
            logger.error(f"[RuleEngine] Execute failed: {e}")
            return {"executed": False, "error": str(e)}

    # ──── 规则管理 ────

    def add_rule(self, rule: Rule) -> str:
        self._rules[rule.id] = rule
        self._save_rules()
        logger.info(f"[RuleEngine] Added rule: {rule.name}")
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._save_rules()
            return True
        return False

    def enable_rule(self, rule_id: str, enabled: bool = True):
        if rule_id in self._rules:
            self._rules[rule_id].enabled = enabled
            self._save_rules()

    def list_rules(self, enabled_only: bool = False) -> list[dict]:
        rules = [r.to_dict() for r in self._rules.values()]
        if enabled_only:
            rules = [r for r in rules if r["enabled"]]
        return rules


def _parse_ha_command(text: str) -> list[dict]:
    """从文本中解析 HA 命令"""
    import re
    if not text:
        return []
    pattern = r'\{[\s\S]*?\}'
    matches = re.findall(pattern, text)
    results = []
    for m in matches:
        try:
            results.append(json.loads(m))
        except Exception:
            pass
    return results


def _load_builtin_rules() -> list[Rule]:
    """内置规则示例"""
    now = datetime.datetime.now()
    return [
        Rule(
            rule_id="晚安关灯",
            name="晚安自动关灯",
            condition={"type": "time_range", "start": "23:00", "end": "06:00"},
            action=[{"entity_id": "scene.good_night", "action": "activate_scene"}],
            enabled=False,
            priority=1,
        ),
        Rule(
            rule_id="离家模式",
            name="出门自动切换离家模式",
            condition={"type": "presence", "zone": "home", "expected": "away"},
            action=[{"entity_id": "scene.leaving_home", "action": "activate_scene"}],
            enabled=False,
            priority=2,
        ),
    ]


_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    global _engine
    if _engine is None:
        _engine = RuleEngine()
    return _engine
