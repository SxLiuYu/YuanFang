# services/daemon_mode.py
"""
KAIROS 守护进程 · KAIROS DaemonMode
后台运行：定期检查环境、处理自动化规则、记录观察
"""
import os
import time
import threading
import logging
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class KairosDaemon:
    """
    KAIROS 后台守护进程
    运行在独立线程，定期执行：
    1. 读取 HomeAssistant 设备状态
    2. 执行自动化规则检查
    3. 记录环境观察
    4. 异常检测和告警
    """

    def __init__(self, interval: int = 60):
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._tools = None
        self._rule_engine = None
        self._observations = []
        self._last_run = None

    def set_tools(self, tools):
        self._tools = tools

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

    def status(self) -> dict:
        return {
            "running": self._running,
            "interval": self.interval,
            "last_run": self._last_run,
            "observations_count": len(self._observations),
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
