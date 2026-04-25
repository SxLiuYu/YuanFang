# services/daemon_mode.py
"""
KAIROS 守护进程 · KAIROS DaemonMode
后台运行：定期检查环境、处理自动化规则、记录观察
增强：主动服务 ProactiveMonitor（Hey Tuya 启发）
"""
import os
import time
import threading
import logging
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ProactiveMonitor:
    """
    主动监测服务 — DeepSeek V4 多尺度稀疏触发思路

    分层监测：
    - fast (60s): 传感器异常（烟雾/燃气/门窗/温度）
    - medium (300s): 能耗异常、设备离线、日程提醒
    - slow (3600s): 行为建议、场景推荐、快递/宠物等
    """

    def __init__(self, kairos_tools, rule_engine=None, memory=None, llm=None):
        self._tools = kairos_tools
        self._rule_engine = rule_engine
        self._memory = memory
        self._llm = llm

        # 多尺度监测间隔（稀疏触发 — 类 DSA 动态稀疏）
        self.check_intervals = {
            "fast": 60,      # 60s — 传感器异常
            "medium": 300,  # 5min — 能耗/设备状态
            "slow": 3600,   # 1hr — 行为建议/场景推荐
        }
        self.last_check = {k: 0 for k in self.check_intervals}

        # 通知去重（避免同一事件重复提醒）
        self._recent_alerts: dict[str, float] = {}  # key -> last_alert_time
        self._dedup_window = 600  # 10分钟内不重复提醒同一事件

    def _is_duplicate(self, key: str) -> bool:
        """去重检查"""
        now = time.time()
        if key in self._recent_alerts and now - self._recent_alerts[key] < self._dedup_window:
            return True
        self._recent_alerts[key] = now
        return False

    def _get_context(self) -> dict:
        """获取当前环境上下文"""
        try:
            from core import app_state as state
            nodes = state.get_nodes_copy()
        except Exception:
            nodes = {}
        return nodes

    # ─── Fast层：传感器异常 ───────────────────────────────────────

    def check_fast_events(self, context: dict) -> list:
        """快速层：烟雾/燃气/门窗/温度异常 — 立即告警"""
        alerts = []
        sensor_readings = context.get("sensor_readings", {})
        device_states = context.get("device_states", {})

        # 1. 烟雾/燃气检测（高优先级）
        for entity_id, reading in sensor_readings.items():
            unit = reading.get("unit", "")
            value = reading.get("value", 0)
            threshold = reading.get("threshold", 999)
            name = reading.get("friendly_name", entity_id)

            if unit in ("ppm",) and value > threshold:
                alert_key = f"gas_high_{entity_id}"
                if not self._is_duplicate(alert_key):
                    alerts.append({
                        "level": "critical",
                        "title": "⚠️ 燃气/烟雾告警",
                        "message": f"{name}检测到异常：{value}{unit}",
                        "voice": True,
                    })

            if unit in ("°C",) and value > 45:
                alert_key = f"temp_high_{entity_id}"
                if not self._is_duplicate(alert_key):
                    alerts.append({
                        "level": "critical",
                        "title": "⚠️ 温度异常",
                        "message": f"{name}温度过高：{value}°C，请检查",
                        "voice": True,
                    })

        # 2. 门窗长期开启（忘记关门）
        open_doors = [
            e for e, s in device_states.items()
            if "door" in e.lower() or "window" in e.lower()
        ]
        open_count = len(open_doors)
        alert_key = "doors_open"
        if open_count >= 3 and not self._is_duplicate(alert_key):
            alerts.append({
                "level": "warning",
                "title": "🚪 门窗提醒",
                "message": f"有{open_count}个门或窗户长时间开启",
                "voice": True,
            })

        # 3. 水浸检测
        for entity_id, reading in sensor_readings.items():
            if "water" in entity_id.lower() and reading.get("value") == "detected":
                alert_key = f"water_leak_{entity_id}"
                if not self._is_duplicate(alert_key):
                    alerts.append({
                        "level": "critical",
                        "title": "💧 水浸告警",
                        "message": f"检测到水浸：{reading.get('friendly_name', entity_id)}",
                        "voice": True,
                    })

        return alerts

    # ─── Medium层：能耗/设备状态 ────────────────────────────────

    def check_medium_events(self, context: dict) -> list:
        """中速层：设备离线/能耗异常/日程提醒"""
        alerts = []
        device_states = context.get("device_states", {})

        # 1. 设备离线（Home Assistant 设备）
        offline = [
            e for e, s in device_states.items()
            if s.get("state") in ("unavailable", "unknown")
        ]
        if offline:
            alert_key = f"devices_offline_{len(offline)}"
            if not self._is_duplicate(alert_key):
                device_list = ", ".join(offline[:3])
                suffix = "等" if len(offline) > 3 else ""
                alerts.append({
                    "level": "warning",
                    "title": "📡 设备离线",
                    "message": f"以下设备离线：{device_list}{suffix}，共{len(offline)}个",
                    "voice": False,
                })

        # 2. 能耗异常（如果有能耗传感器）
        power_sensors = {
            e: s for e, s in sensor_readings.items()
            if "power" in e.lower() or "energy" in e.lower()
        } if "sensor_readings" in context else {}
        for entity_id, reading in power_sensors.items():
            value = float(reading.get("value", 0))
            if value > 3000:  # 瞬时功率 > 3000W 视为异常
                alert_key = f"power_high_{entity_id}"
                if not self._is_duplicate(alert_key):
                    alerts.append({
                        "level": "warning",
                        "title": "⚡ 用电提醒",
                        "message": f"当前功率过高：{value}W，请检查是否忘关大功率电器",
                        "voice": True,
                    })

        return alerts

    # ─── Slow层：行为建议/场景推荐 ─────────────────────────────

    def generate_smart_suggestions(self, context: dict) -> list:
        """慢速层：基于行为模式的主动建议（DeepSeek V4 稀疏推理启发）"""
        alerts = []
        now = datetime.datetime.now()
        hour = now.hour

        # 只在低负载时生成建议（稀疏调用，不频繁）
        # 根据时间生成场景建议
        suggestions = []

        # 晨间建议（6-8点）
        if 6 <= hour <= 8:
            alert_key = "morning_scene"
            if not self._is_duplicate(alert_key):
                suggestions.append({
                    "level": "info",
                    "title": "🌅 晨间助手",
                    "message": "早！现在需要我帮你开灯、播报天气或查看日程吗？",
                    "voice": True,
                    "trigger_condition": "morning",
                })

        # 离开提醒（工作日 8-9点）
        if 8 <= hour <= 9 and now.weekday() < 5:
            alert_key = "leave_scene"
            if not self._is_duplicate(alert_key):
                suggestions.append({
                    "level": "info",
                    "title": "🏠 离家助手",
                    "message": "出门在即，需要我帮你关闭电器、调低空调或查看门锁状态吗？",
                    "voice": True,
                    "trigger_condition": "leave_home",
                })

        # 晚间建议（18-20点）
        if 18 <= hour <= 20:
            alert_key = "evening_scene"
            if not self._is_duplicate(alert_key):
                suggestions.append({
                    "level": "info",
                    "title": "🌙 晚间助手",
                    "message": "现在需要我帮你打开客厅灯光或播放轻音乐放松一下吗？",
                    "voice": True,
                    "trigger_condition": "evening",
                })

        # 睡眠提醒（22-23点）
        if 22 <= hour <= 23:
            alert_key = "sleep_scene"
            if not self._is_duplicate(alert_key):
                suggestions.append({
                    "level": "info",
                    "title": "😴 睡眠助手",
                    "message": "该休息了，需要我调暗灯光、关闭所有设备并设好闹钟吗？",
                    "voice": True,
                    "trigger_condition": "sleep",
                })

        alerts.extend(suggestions)
        return alerts

    # ─── 主循环 ─────────────────────────────────────────────────

    def run_cycle(self) -> list:
        """主循环 — 多尺度稀疏调度"""
        now = time.time()
        all_alerts = []
        context = self._get_context()

        # fast 层
        if now - self.last_check["fast"] >= self.check_intervals["fast"]:
            all_alerts.extend(self.check_fast_events(context))
            self.last_check["fast"] = now

        # medium 层
        if now - self.last_check["medium"] >= self.check_intervals["medium"]:
            all_alerts.extend(self.check_medium_events(context))
            self.last_check["medium"] = now

        # slow 层
        if now - self.last_check["slow"] >= self.check_intervals["slow"]:
            all_alerts.extend(self.generate_smart_suggestions(context))
            self.last_check["slow"] = now

        # 发送通知
        for alert in all_alerts:
            self._send_alert(alert, context)

        return all_alerts

    def _send_alert(self, alert: dict, context: dict):
        """发送告警：通知 + 语音播报"""
        if self._tools is None:
            return

        # SocketIO 通知
        self._tools.send_notification(
            title=alert["title"],
            message=alert["message"],
            level=alert["level"],
        )

        # 语音播报（如果用户在家）
        presence = context.get("presence", {})
        if alert.get("voice") and presence.get("home") == "home":
            self._voice_announce(alert["message"])

    def _voice_announce(self, message: str):
        """TTS 语音播报（通过 Jarvis 管线）"""
        try:
            from jarvis_pipeline import JarvisPipeline
            pipeline = JarvisPipeline()
            # 简短播报，不阻塞主循环
            threading.Thread(
                target=pipeline.speak,
                args=(message,),
                daemon=True
            ).start()
        except Exception as e:
            logger.debug(f"[ProactiveMonitor] TTS announce failed: {e}")


class KairosDaemon:
    """
    KAIROS 后台守护进程
    运行在独立线程，定期执行：
    1. 读取 HomeAssistant 设备状态
    2. 执行自动化规则检查
    3. 记录环境观察
    4. 异常检测和告警
    5. 主动服务监测（增强）
    """

    def __init__(self, interval: int = 60):
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._tools = None
        self._rule_engine = None
        self._observations = []
        self._last_run = None
        # 主动服务监控器
        self._proactive_monitor: ProactiveMonitor | None = None

    def set_tools(self, tools):
        self._tools = tools
        # 初始化主动服务（注入依赖）
        self._proactive_monitor = ProactiveMonitor(
            kairos_tools=tools,
            rule_engine=self._rule_engine,
        )

    def set_rule_engine(self, engine):
        self._rule_engine = engine

    def start(self):
        if self._running:
            logger.warning("[KAIROS] Already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"[KAIROS] Daemon started (interval={self.interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[KAIROS] Daemon stopped")

    def _run_loop(self):
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"[KAIROS] Tick error: {e}")
            time.sleep(self.interval)

    def _tick(self):
        """一次循环"""
        self._last_run = datetime.datetime.now().isoformat()
        logger.debug(f"[KAIROS] Tick at {self._last_run}")

        # 获取当前状态
        try:
            from core import app_state as state
            nodes = state.get_nodes_copy()
        except Exception:
            nodes = {}

        # 记录观察
        obs = {
            "timestamp": self._last_run,
            "device_states": nodes.get("device_states", {}),
            "sensor_readings": nodes.get("sensor_readings", {}),
        }
        self._observations.append(obs)
        if len(self._observations) > 1000:
            self._observations = self._observations[-500:]

        # 规则引擎检查
        if self._rule_engine:
            try:
                results = self._rule_engine.check_and_fire(nodes)
                for r in results:
                    logger.info(f"[KAIROS] Rule fired: {r}")
            except Exception as e:
                logger.error(f"[KAIROS] Rule check failed: {e}")

        # 环境异常检测
        if self._tools:
            try:
                anomalies = self._tools.check_and_remedy_environment(nodes, auto_execute=False)
                for a in anomalies:
                    logger.info(f"[KAIROS] Anomaly: {a}")
            except Exception as e:
                logger.error(f"[KAIROS] Anomaly check failed: {e}")

        # ── 主动服务监测（P0 增强）───────────────────────────────
        if self._proactive_monitor:
            try:
                proactive_alerts = self._proactive_monitor.run_cycle()
                for alert in proactive_alerts:
                    logger.info(f"[KAIROS] Proactive: {alert['title']} - {alert['message']}")
            except Exception as e:
                logger.error(f"[KAIROS] Proactive monitor failed: {e}")

    def status(self) -> dict:
        return {
            "running": self._running,
            "interval": self.interval,
            "last_run": self._last_run,
            "observations_count": len(self._observations),
            "proactive_enabled": self._proactive_monitor is not None,
        }

    def get_recent_observations(self, n: int = 20) -> list:
        return self._observations[-n:]

    def get_daily_log(self, date_str: str) -> list:
        """获取指定日期的日志"""
        logs = []
        for obs in self._observations:
            if date_str in obs.get("timestamp", ""):
                logs.append(obs)
        return logs
