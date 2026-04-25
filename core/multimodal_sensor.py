# core/multimodal_sensor.py
"""
多模态感知融合 — MultimodalSensorFusion
Hey Tuya Personal VAD 启发，DeepSeek V4 多尺度特征融合思路

融合来源：
- 麦克风（VAD 能量/语音识别）
- 摄像头（人员存在/姿态/表情）
- 手机传感器（加速度/陀螺仪/位置/环境光）
- 红外探头（在家检测）

融合策略：
- 时间对齐：滑动时间窗口内多模态事件对齐
- 空间关联：摄像头人员位置 × 麦克风声源方向
- 置信度加权：各模态独立置信度 → 加权融合判断
"""
import time
import threading
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger(__name__)


# ============ 数据结构 ============

@dataclass
class SensorEvent:
    """统一传感器事件格式"""
    source: str          # 'mic' | 'camera' | 'phone' | 'ir' | 'presence'
    event_type: str     # 事件类型
    timestamp: float
    confidence: float   # 0.0-1.0
    raw_data: dict      # 原始数据
    fused: bool = False # 是否已被融合

    def __lt__(self, other):
        return self.timestamp < other.timestamp


@dataclass
class PresenceState:
    """在家状态融合结果"""
    is_home: bool
    confidence: float
    primary_source: str   # 主要判定来源
    last_update: float
    details: dict = field(default_factory=dict)


# ============ 多模态融合引擎 ============

class MultimodalFusion:
    """
    多模态感知融合引擎
    时间窗口内对齐多源传感器事件，输出高置信度判断
    """

    def __init__(self, window_seconds: float = 5.0):
        self.window_seconds = window_seconds
        self.events: deque = deque(maxlen=500)  # 最近500条事件
        self.presence = PresenceState(
            is_home=False,
            confidence=0.0,
            primary_source="unknown",
            last_update=0.0,
        )
        self._callbacks: list[Callable] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ──── 事件注入 ────

    def inject_mic(self, vad_level: float, speech_detected: bool, audio_energy: float):
        """注入麦克风/VAD 事件"""
        self._add_event(SensorEvent(
            source="mic",
            event_type="speech" if speech_detected else "silence",
            timestamp=time.time(),
            confidence=min(vad_level / 0.5, 1.0),
            raw_data={"vad_level": vad_level, "energy": audio_energy},
        ))

    def inject_camera(self, person_detected: bool, count: int = 0,
                     face_encoding: list = None, emotion: str = None):
        """注入摄像头事件（人员检测/表情）"""
        self._add_event(SensorEvent(
            source="camera",
            event_type="person_detected" if person_detected else "no_person",
            timestamp=time.time(),
            confidence=0.95 if person_detected else 0.8,
            raw_data={"count": count, "emotion": emotion, "has_face": face_encoding is not None},
        ))

    def inject_phone(self, activity: str, stationary: bool,
                     battery_level: float, charging: bool):
        """
        注入手机传感器事件
        activity: 'still' | 'walking' | 'running' | 'in_vehicle'
        """
        self._add_event(SensorEvent(
            source="phone",
            event_type=f"activity_{activity}",
            timestamp=time.time(),
            confidence=0.85,
            raw_data={
                "activity": activity,
                "stationary": stationary,
                "battery": battery_level,
                "charging": charging,
            },
        ))

    def inject_ir(self, motion_detected: bool, raw_value: float):
        """注入红外传感器事件（在家检测探头）"""
        self._add_event(SensorEvent(
            source="ir",
            event_type="motion" if motion_detected else "idle",
            timestamp=time.time(),
            confidence=0.9 if motion_detected else 0.7,
            raw_data={"motion": motion_detected, "raw": raw_value},
        ))

    def inject_presence(self, is_home: bool, confidence: float, source: str = "manual"):
        """直接注入在家状态（来自 app_state.nodes）"""
        with self._lock:
            self.presence = PresenceState(
                is_home=is_home,
                confidence=confidence,
                primary_source=source,
                last_update=time.time(),
            )

    # ──── 内部 ────

    def _add_event(self, event: SensorEvent):
        with self._lock:
            self.events.append(event)
        # 触发融合
        fused = self._fuse()
        if fused:
            self._notify(fused)

    def _get_window(self) -> list[SensorEvent]:
        """获取时间窗口内的事件"""
        now = time.time()
        return [e for e in self.events if now - e.timestamp <= self.window_seconds]

    # ──── 融合逻辑（DeepSeek V4 多尺度启发） ────

    def _fuse(self) -> Optional[PresenceState]:
        """
        多尺度融合：
        - 微观尺度（0-2s）：声音+动作 → 有人在活动
        - 中观尺度（2-10s）：多模态持续性 → 确认在家
        - 宏观尺度（>10s）：设备状态 + 行为模式 → 长期判断
        """
        now = time.time()
        window = self._get_window()
        if not window:
            return None

        # 1. 各模态最近一条事件的置信度
        latest = {}
        for e in reversed(window):
            if e.source not in latest:
                latest[e.source] = e

        # 2. 在家判断矩阵
        home_signals = []

        # 麦克风：有语音 → 强在家信号
        if "mic" in latest:
            e = latest["mic"]
            if e.event_type == "speech" and e.confidence > 0.4:
                home_signals.append(("mic", 0.9, "检测到语音"))

        # 摄像头：有人 → 强在家信号
        if "camera" in latest:
            e = latest["camera"]
            if e.event_type == "person_detected":
                home_signals.append(("camera", 0.95, f"检测到{latest['camera'].raw_data.get('count',1)}人"))

        # 红外：检测到移动 → 在家
        if "ir" in latest:
            e = latest["ir"]
            if e.event_type == "motion":
                home_signals.append(("ir", 0.85, "红外检测到移动"))

        # 手机：静止且充电 → 可能在沙发/床
        if "phone" in latest:
            e = latest["phone"]
            if e.event_type == "activity_still" and e.raw_data.get("charging"):
                home_signals.append(("phone", 0.6, "手机静止充电中"))

        # 3. 加权融合（DeepSeek V4 动态计算分配启发）
        if not home_signals:
            # 无强信号 → 降低置信度
            new_confidence = max(0.0, self.presence.confidence * 0.9)
            new_source = "no_signal_decay"
        else:
            total_weight = sum(s[1] for s in home_signals)
            weighted = sum(s[1] for s in home_signals) / len(home_signals)
            new_confidence = min(1.0, weighted + 0.1)  # 轻微boost
            new_source = ",".join(s[0] for s in home_signals)

        is_home = new_confidence > 0.5

        new_state = PresenceState(
            is_home=is_home,
            confidence=new_confidence,
            primary_source=new_source,
            last_update=now,
            details={"signals": [(s[2], s[1]) for s in home_signals]},
        )

        # 状态变化 → 更新
        if (is_home != self.presence.is_home or
            abs(new_confidence - self.presence.confidence) > 0.2):
            with self._lock:
                self.presence = new_state
            return new_state

        return None  # 无显著变化

    # ──── 状态查询 ────

    def get_presence(self) -> PresenceState:
        with self._lock:
            return self._presence_copy()

    def _presence_copy(self) -> PresenceState:
        p = self.presence
        return PresenceState(
            is_home=p.is_home,
            confidence=p.confidence,
            primary_source=p.primary_source,
            last_update=p.last_update,
            details=dict(p.details),
        )

    def get_recent_events(self, seconds: float = 30) -> list:
        """获取最近N秒的事件"""
        now = time.time()
        with self._lock:
            return [e for e in self.events if now - e.timestamp <= seconds]

    # ──── 回调 ────

    def on_presence_change(self, callback: Callable[[PresenceState], None]):
        """注册在家状态变化回调"""
        self._callbacks.append(callback)

    def _notify(self, state: PresenceState):
        for cb in self._callbacks:
            try:
                cb(state)
            except Exception as e:
                logger.error(f"[MultimodalFusion] callback error: {e}")

    # ──── 后台运行 ────

    def start(self):
        """启动后台衰减检查线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("[MultimodalFusion] started")

    def _run_loop(self):
        while self._running:
            time.sleep(5)
            # 定期检查置信度衰减（长时间无信号）
            with self._lock:
                if time.time() - self.presence.last_update > 60:
                    self.presence = PresenceState(
                        is_home=False,
                        confidence=0.0,
                        primary_source="timeout",
                        last_update=self.presence.last_update,
                    )

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)


# ============ 全局实例 ============

_fusion: Optional[MultimodalFusion] = None


def get_fusion() -> MultimodalFusion:
    global _fusion
    if _fusion is None:
        _fusion = MultimodalFusion()
    return _fusion
