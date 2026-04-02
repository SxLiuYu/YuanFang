"""
⚙️ 元芳自动化规则引�?· RuleEngine
基于条件触发自动执行智能家居动作�?

支持的触发条件：
- 传感器阈值（温度/湿度/电量�?
- 时间触发（定�?周期�?
- 设备状态变�?
- 用户离家/回家
- 情绪异常

支持的执行动作：
- HA 设备控制
- 场景激�?
- 发送通知
- 触发已有技�?
- 自定义脚�?

�?KAIROS 守护进程集成：daemon tick 时自动检查规则�?
"""

import os
import json
import uuid
import datetime
import time
import threading
import logging
import re
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# 规则存储目录
RULE_DIR = Path(__file__).parent / "rules"
RULE_DIR.mkdir(exist_ok=True)

RULE_INDEX_FILE = RULE_DIR / "rule_index.json"
RULE_LOG_DIR = RULE_DIR / "logs"
RULE_LOG_DIR.mkdir(exist_ok=True)


class Rule:
    """自动化规则定�?""

    def __init__(self, name: str, description: str = "",
                 trigger_type: str = "sensor_threshold",
                 trigger_config: dict = None,
                 actions: list = None,
                 cooldown_minutes: int = 30,
                 priority: int = 5,
                 enabled: bool = True,
                 metadata: dict = None):
        """
        Args:
            name: 规则名称
            description: 规则描述
            trigger_type: 触发类型
                - sensor_threshold: 传感器阈值触�?
                - time_schedule: 定时触发
                - device_state: 设备状态变化触�?
                - user_presence: 用户在离家触�?
                - emotion_alert: 情绪异常触发
                - scene_change: 场景切换触发
            trigger_config: 触发条件配置（因类型而异�?
            actions: 执行动作列表 [{"type": "ha_control/notify/skill/scene", ...}]
            cooldown_minutes: 冷却时间（分钟），同一规则触发间隔
            priority: 优先�?1-10，数字越大优先级越高
            enabled: 是否启用
        """
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.trigger_type = trigger_type
        self.trigger_config = trigger_config or {}
        self.actions = actions or []
        self.cooldown_minutes = cooldown_minutes
        self.priority = priority
        self.enabled = enabled
        self.metadata = metadata or {}

        # 运行时状�?
        self.last_triggered = None
        self.trigger_count = 0
        self.success_count = 0
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "trigger_config": self.trigger_config,
            "actions": self.actions,
            "cooldown_minutes": self.cooldown_minutes,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
            "success_count": self.success_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        rule = cls.__new__(cls)
        for k, v in data.items():
            setattr(rule, k, v)
        return rule

    def can_trigger(self) -> bool:
        """检查是否满足冷却条�?""
        if not self.enabled:
            return False
        if self.last_triggered is None:
            return True
        try:
            last = datetime.datetime.fromisoformat(self.last_triggered)
            elapsed = (datetime.datetime.now() - last).total_seconds() / 60
            return elapsed >= self.cooldown_minutes
        except Exception:
            return True

    def record_trigger(self, success: bool = True):
        """记录触发"""
        self.last_triggered = datetime.datetime.now().isoformat()
        self.trigger_count += 1
        if success:
            self.success_count += 1
        self.updated_at = self.last_triggered


class RuleEngine:
    """
    自动化规则引擎�?

    核心能力�?
    1. 规则 CRUD 管理
    2. 条件评估（检查传感器数据、时间、设备状态等是否满足触发条件�?
    3. 动作执行（调�?HA 适配器、发送通知、触发技能）
    4. 冷却管理
    5. 执行日志
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._lock = threading.Lock()
        self._execution_logs = []
        self._max_logs = 200
        self._ha_executor = None
        self._notify_fn = None
        self._skill_engine_fn = None
        self._load_index()

    # ─────────── 依赖注入 ───────────

    def set_ha_executor(self, fn: Callable):
        """注入 HA 指令执行函数（来�?main._execute_ha_commands�?""
        self._ha_executor = fn

    def set_notify_fn(self, fn: Callable):
        """注入通知函数（来�?kairos_tools.send_notification�?""
        self._notify_fn = fn

    def set_skill_engine_fn(self, fn: Callable):
        """注入技能引擎获取函数（来自 get_skill_engine�?""
        self._skill_engine_fn = fn

    # ─────────── 规则管理 ───────────

    def _load_index(self):
        if RULE_INDEX_FILE.exists():
            try:
                data = json.loads(RULE_INDEX_FILE.read_text("utf-8"))
                for rule_id, rule_data in data.get("rules", {}).items():
                    self._rules[rule_id] = Rule.from_dict(rule_data)
                print(f"[规则引擎] 加载�?{len(self._rules)} 条规�?)
            except Exception as e:
                print(f"[规则引擎] 加载失败: {e}")

    def _save_index(self):
        data = {"rules": {}}
        for rid, rule in self._rules.items():
            data["rules"][rid] = rule.to_dict()
        RULE_INDEX_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def add_rule(self, rule: Rule) -> str:
        """添加规则"""
        with self._lock:
            self._rules[rule.id] = rule
            self._save_index()
        print(f"[规则引擎] 新增规则: {rule.name} ({rule.id})")
        return rule.id

    def update_rule(self, rule_id: str, updates: dict) -> bool:
        """更新规则"""
        with self._lock:
            rule = self._rules.get(rule_id)
            if not rule:
                return False
            for k, v in updates.items():
                if k in ("id", "created_at"):
                    continue
                setattr(rule, k, v)
            rule.updated_at = datetime.datetime.now().isoformat()
            self._save_index()
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""
        with self._lock:
            if rule_id in self._rules:
                name = self._rules[rule_id].name
                del self._rules[rule_id]
                self._save_index()
                print(f"[规则引擎] 删除规则: {name} ({rule_id})")
                return True
        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def list_rules(self, enabled_only: bool = False) -> list[dict]:
        rules = []
        for rule in self._rules.values():
            if enabled_only and not rule.enabled:
                continue
            rules.append(rule.to_dict())
        return sorted(rules, key=lambda x: (-x.get("priority", 5), x.get("name", "")))

    def toggle_rule(self, rule_id: str, enabled: bool = None) -> bool:
        """启用/禁用规则（不�?enabled 则切换）"""
        rule = self._rules.get(rule_id)
        if not rule:
            return False
        rule.enabled = enabled if enabled is not None else not rule.enabled
        rule.updated_at = datetime.datetime.now().isoformat()
        self._save_index()
        return True

    # ─────────── 条件评估 ───────────

    def evaluate(self, context: dict = None) -> list[dict]:
        """
        评估所有启用的规则，返回满足条件且不在冷却中的规则列表�?

        context 应包含：
        - nodes: 节点传感器数�?{node_id: data}
        - ha_states: HA 设备状态（可选）
        - user_presence: 用户是否在家（可选）
        - emotion_summary: 情感摘要（可选）
        - scene: 当前场景（可选）
        """
        context = context or {}
        triggered = []

        for rule in self._rules.values():
            if not rule.enabled or not rule.can_trigger():
                continue

            try:
                if self._evaluate_trigger(rule, context):
                    triggered.append({
                        "rule": rule,
                        "matched_conditions": self._get_matched_conditions(rule, context),
                    })
            except Exception as e:
                self._log_execution(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    status="evaluation_error",
                    detail=str(e),
                )

        # 按优先级排序
        triggered.sort(key=lambda x: x["rule"].priority, reverse=True)
        return triggered

    def _evaluate_trigger(self, rule: Rule, context: dict) -> bool:
        """评估单个规则的触发条�?""
        ttype = rule.trigger_type
        tconfig = rule.trigger_config

        if ttype == "sensor_threshold":
            return self._check_sensor_threshold(tconfig, context)
        elif ttype == "time_schedule":
            return self._check_time_schedule(tconfig)
        elif ttype == "device_state":
            return self._check_device_state(tconfig, context)
        elif ttype == "user_presence":
            return self._check_user_presence(tconfig, context)
        elif ttype == "emotion_alert":
            return self._check_emotion_alert(tconfig, context)
        elif ttype == "scene_change":
            return self._check_scene_change(tconfig, context)
        else:
            print(f"[规则引擎] 未知触发类型: {ttype}")
            return False

    def _check_sensor_threshold(self, config: dict, context: dict) -> bool:
        """传感器阈值检�?""
        nodes = context.get("nodes", {})
        sensor_type = config.get("sensor_type", "temperature")  # temperature/humidity/battery/light
        operator = config.get("operator", ">")  # > / < / >= / <= / == / !=
        threshold = float(config.get("threshold", 0))
        node_filter = config.get("node_id", "")  # 可选，指定节点

        for node_id, data in nodes.items():
            if node_filter and node_id != node_filter:
                continue
            sensors = data.get("sensors", {})
            value = sensors.get(sensor_type)
            if value is None:
                continue
            try:
                value = float(value)
                if self._compare(value, operator, threshold):
                    return True
            except (ValueError, TypeError):
                continue
        return False

    def _check_time_schedule(self, config: dict) -> bool:
        """定时触发检�?""
        now = datetime.datetime.now()

        # 检查时间条�?
        trigger_time = config.get("time", "")  # "HH:MM" 格式
        if trigger_time:
            try:
                h, m = map(int, trigger_time.split(":"))
                if now.hour != h or now.minute != m:
                    return False
            except (ValueError, AttributeError):
                pass

        # 检查星期条�?
        weekdays = config.get("weekdays", [])  # [0,1,2,...6] 0=周一
        if weekdays and now.weekday() not in weekdays:
            return False

        return True

    def _check_device_state(self, config: dict, context: dict) -> bool:
        """设备状态变化检�?""
        ha_states = context.get("ha_states", {})
        entity_id = config.get("entity_id", "")
        expected_state = config.get("state", "on")
        operator = config.get("operator", "==")

        if not entity_id or not ha_states:
            return False

        for entity in ha_states:
            if entity.get("entity_id") == entity_id:
                actual = entity.get("state", "")
                return self._compare_str(actual, operator, expected_state)
        return False

    def _check_user_presence(self, config: dict, context: dict) -> bool:
        """用户在离家检�?""
        presence = context.get("user_presence", {})
        is_home = presence.get("is_home", None)

        if is_home is None:
            return False

        expected = config.get("home", True)  # True=在家时触�? False=离家时触�?
        return is_home == expected

    def _check_emotion_alert(self, config: dict, context: dict) -> bool:
        """情绪异常检�?""
        emotion = context.get("emotion_summary", {})
        if not isinstance(emotion, dict):
            return False

        metric = config.get("metric", "negative_ratio")  # negative_ratio
        threshold = float(config.get("threshold", 0.3))
        operator = config.get("operator", ">")

        value = emotion.get(metric)
        if value is None:
            return False

        try:
            return self._compare(float(value), operator, threshold)
        except (ValueError, TypeError):
            return False

    def _check_scene_change(self, config: dict, context: dict) -> bool:
        """场景切换检�?""
        scene = context.get("scene", "")
        expected_scene = config.get("scene", "")
        if not expected_scene or not scene:
            return False
        return scene == expected_scene

    def _get_matched_conditions(self, rule: Rule, context: dict) -> list[str]:
        """获取匹配到的具体条件描述"""
        conditions = []
        ttype = rule.trigger_type
        tconfig = rule.trigger_config

        if ttype == "sensor_threshold":
            sensor_type = tconfig.get("sensor_type", "?")
            operator = tconfig.get("operator", ">")
            threshold = tconfig.get("threshold", "?")
            node = tconfig.get("node_id", "任意节点")
            sensor_names = {"temperature": "温度", "humidity": "湿度", "battery": "电量", "light": "光照"}
            conditions.append(f"{sensor_names.get(sensor_type, sensor_type)} {operator} {threshold} ({node})")

        elif ttype == "time_schedule":
            time_str = tconfig.get("time", "定时")
            conditions.append(f"时间到达 {time_str}")

        elif ttype == "device_state":
            conditions.append(f"设备 {tconfig.get('entity_id', '?')} 状态满足条�?)

        elif ttype == "user_presence":
            home = tconfig.get("home", True)
            conditions.append("用户在家" if home else "用户离家")

        elif ttype == "emotion_alert":
            conditions.append(f"情绪指标异常")

        elif ttype == "scene_change":
            conditions.append(f"场景切换�?{tconfig.get('scene', '?')}")

        return conditions

    @staticmethod
    def _compare(value, operator, threshold) -> bool:
        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        fn = ops.get(operator)
        return fn(value, threshold) if fn else False

    @staticmethod
    def _compare_str(value, operator, expected) -> bool:
        if operator == "==":
            return value == expected
        elif operator == "!=":
            return value != expected
        return False

    # ─────────── 动作执行 ───────────

    def execute_triggered(self, triggered: list[dict]) -> list[dict]:
        """执行满足条件的规�?""
        results = []
        for item in triggered:
            rule = item["rule"]
            matched = item["matched_conditions"]
            result = self._execute_rule(rule, matched)
            results.append(result)
        return results

    def _execute_rule(self, rule: Rule, matched_conditions: list[str]) -> dict:
        """执行单个规则的所有动�?""
        exec_results = []
        success = True

        for action in rule.actions:
            try:
                action_type = action.get("type", "")
                action_result = self._execute_action(action)
                exec_results.append({
                    "type": action_type,
                    "success": action_result.get("success", False),
                    "detail": action_result.get("detail", ""),
                })
                if not action_result.get("success", False):
                    success = False
            except Exception as e:
                exec_results.append({
                    "type": action.get("type", "?"),
                    "success": False,
                    "detail": str(e),
                })
                success = False

        rule.record_trigger(success)

        # 记录日志
        log_entry = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "status": "success" if success else "partial_fail",
            "matched_conditions": matched_conditions,
            "actions": exec_results,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self._log_execution(**log_entry)

        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "success": success,
            "actions": exec_results,
        }

    def _execute_action(self, action: dict) -> dict:
        """执行单个动作"""
        action_type = action.get("type", "")

        if action_type == "ha_control":
            return self._action_ha_control(action)
        elif action_type == "scene":
            return self._action_scene(action)
        elif action_type == "notify":
            return self._action_notify(action)
        elif action_type == "skill":
            return self._action_skill(action)
        elif action_type == "script":
            return self._action_script(action)
        else:
            return {"success": False, "detail": f"未知动作类型: {action_type}"}

    def _action_ha_control(self, action: dict) -> dict:
        """HA 设备控制动作"""
        if not self._ha_executor:
            return {"success": False, "detail": "HA 执行器未注入"}

        commands = action.get("commands", [])
        if not commands:
            return {"success": False, "detail": "未指�?HA 指令"}

        try:
            results = self._ha_executor(commands)
            success_count = sum(1 for r in results if r.get("success"))
            return {
                "success": success_count == len(results),
                "detail": f"执行 {success_count}/{len(results)} �?HA 指令",
            }
        except Exception as e:
            return {"success": False, "detail": str(e)}

    def _action_scene(self, action: dict) -> dict:
        """场景激活动�?""
        entity_id = action.get("entity_id", "")
        if not entity_id:
            return {"success": False, "detail": "未指定场�?entity_id"}

        # �?HA executor 执行场景
        if self._ha_executor:
            try:
                results = self._ha_executor([{"entity_id": entity_id, "action": "activate_scene"}])
                return {
                    "success": results[0].get("success", False) if results else False,
                    "detail": f"场景 {entity_id} 激活结�?,
                }
            except Exception as e:
                return {"success": False, "detail": str(e)}

        return {"success": False, "detail": "HA 执行器未注入"}

    def _action_notify(self, action: dict) -> dict:
        """发送通知动作"""
        if not self._notify_fn:
            return {"success": False, "detail": "通知函数未注�?}

        title = action.get("title", "规则触发通知")
        message = action.get("message", "自动化规则已触发")
        level = action.get("level", "info")

        try:
            self._notify_fn(title=title, message=message, level=level)
            return {"success": True, "detail": f"通知已发�? {title}"}
        except Exception as e:
            return {"success": False, "detail": str(e)}

    def _action_skill(self, action: dict) -> dict:
        """触发技能动�?""
        skill_name = action.get("skill_name", "")
        if not skill_name:
            return {"success": False, "detail": "未指定技能名�?}

        if not self._skill_engine_fn:
            return {"success": False, "detail": "技能引擎未注入"}

        try:
            engine = self._skill_engine_fn()
            skill_result = engine.try_execute(skill_name, self._ha_executor)
            if skill_result:
                return {
                    "success": skill_result.get("ha_executed", True),
                    "detail": f"技�?{skill_name} 执行完成",
                }
            return {"success": False, "detail": f"未匹配到技�? {skill_name}"}
        except Exception as e:
            return {"success": False, "detail": str(e)}

    def _action_script(self, action: dict) -> dict:
        """自定义脚本动作（预留给未来扩展）"""
        script_path = action.get("path", "")
        if not script_path:
            return {"success": False, "detail": "未指定脚本路�?}
        return {"success": False, "detail": "自定义脚本暂未实�?}

    # ─────────── 执行日志 ───────────

    def _log_execution(self, **kwargs):
        entry = {**kwargs, "ts": datetime.datetime.now().isoformat()}
        self._execution_logs.append(entry)
        if len(self._execution_logs) > self._max_logs:
            self._execution_logs = self._execution_logs[-self._max_logs:]

        # 持久�?
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file = RULE_LOG_DIR / f"executions_{today}.json"
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text("utf-8"))
            logs.append(entry)
            if len(logs) > 500:
                logs = logs[-500:]
            log_file.write_text(
                json.dumps(logs, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"日志写入失败: {e}")

    def get_execution_logs(self, n: int = 20, rule_id: str = None) -> list:
        """获取执行日志"""
        logs = self._execution_logs[-n:]
        if rule_id:
            logs = [l for l in logs if l.get("rule_id") == rule_id]
        return logs

    # ─────────── 统计报告 ───────────

    def report(self) -> dict:
        """生成规则引擎报告"""
        total = len(self._rules)
        enabled = sum(1 for r in self._rules.values() if r.enabled)
        total_triggers = sum(r.trigger_count for r in self._rules.values())
        total_success = sum(r.success_count for r in self._rules.values())

        # 按触发类型分�?
        by_type = {}
        for rule in self._rules.values():
            t = rule.trigger_type
            if t not in by_type:
                by_type[t] = {"count": 0, "triggers": 0}
            by_type[t]["count"] += 1
            by_type[t]["triggers"] += rule.trigger_count

        return {
            "total_rules": total,
            "enabled_rules": enabled,
            "disabled_rules": total - enabled,
            "total_triggers": total_triggers,
            "total_success": total_success,
            "success_rate": round(total_success / total_triggers * 100, 1) if total_triggers > 0 else 0,
            "by_trigger_type": by_type,
            "recent_logs": self.get_execution_logs(5),
        }


# ─────────── 预置规则 ───────────

def _create_builtin_rules() -> list[Rule]:
    """创建预置的常用规�?""
    return [
        Rule(
            name="高温预警",
            description="室内温度超过 30°C 时发送通知并建议开空调",
            trigger_type="sensor_threshold",
            trigger_config={
                "sensor_type": "temperature",
                "operator": ">",
                "threshold": 30,
            },
            actions=[
                {"type": "notify", "title": "🌡�?高温预警", "message": "室内温度超过 30°C，建议开启空�?, "level": "warning"},
            ],
            cooldown_minutes=60,
            priority=8,
        ),
        Rule(
            name="低电量提�?,
            description="传感器节点电量低�?15% 时提醒充�?,
            trigger_type="sensor_threshold",
            trigger_config={
                "sensor_type": "battery",
                "operator": "<",
                "threshold": 15,
            },
            actions=[
                {"type": "notify", "title": "🔋 低电�?, "message": "节点电量不足 15%，请及时充电", "level": "warning"},
            ],
            cooldown_minutes=120,
            priority=7,
        ),
        Rule(
            name="定时晚安",
            description="每天 22:30 自动提醒晚安",
            trigger_type="time_schedule",
            trigger_config={
                "time": "22:30",
            },
            actions=[
                {"type": "notify", "title": "🌙 晚安提醒", "message": "已经 22:30 了，准备休息�?, "level": "info"},
                {"type": "scene", "entity_id": "scene.good_night"},
            ],
            cooldown_minutes=720,  # 12 小时
            priority=6,
        ),
        Rule(
            name="离家自动关灯",
            description="检测到用户离家时关闭所有灯�?,
            trigger_type="user_presence",
            trigger_config={
                "home": False,
            },
            actions=[
                {"type": "scene", "entity_id": "scene.all_lights_off"},
                {"type": "notify", "title": "🚪 离家模式", "message": "检测到你已离家，已关闭所有灯�?, "level": "info"},
            ],
            cooldown_minutes=30,
            priority=8,
        ),
        Rule(
            name="情绪低落通知",
            description="当负面情绪占比超�?30% 时主动关�?,
            trigger_type="emotion_alert",
            trigger_config={
                "metric": "negative_ratio",
                "operator": ">",
                "threshold": 0.3,
            },
            actions=[
                {"type": "notify", "title": "💙 情绪关心", "message": "最近似乎心情不太好，需要我做什么吗�?, "level": "info"},
            ],
            cooldown_minutes=240,
            priority=5,
        ),
    ]


# ─────────── 全局单例 ───────────

_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    """获取全局规则引擎实例"""
    global _engine
    if _engine is None:
        _engine = RuleEngine()
        # 注册预置规则（如果还没有�?
        if not _engine._rules:
            for rule in _create_builtin_rules():
                _engine.add_rule(rule)
    return _engine

