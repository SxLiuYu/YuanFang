"""
📹 Frigate 摄像头适配器
通过 Frigate REST API 获取摄像头事件和实时状态。

支持功能：
- 获取摄像头列表和状态
- 获取检测事件（人/车/动物等）
- 获取快照和视频片段
- 事件通知集成（检测到人/车时触发通知）

使用方式：
  from adapters.frigate_adapter import FrigateAdapter, get_frigate
  frigate = get_frigate()
  events = frigate.get_recent_events(label="person")
"""

import os
import json
import time
import urllib.request


class FrigateAdapter:
    """Frigate NVR 摄像头适配器"""

    def __init__(self, base_url=None):
        self.base_url = (base_url or os.getenv("FRIGATE_URL", "http://localhost:5000")).rstrip("/")
        self._cameras = []
        self._last_events_fetch = 0
        self._events_cache = []

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _request(self, endpoint: str) -> dict:
        """发送 API 请求"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError:
            return {"error": f"Frigate 不可用 ({self.base_url})"}
        except Exception as e:
            return {"error": str(e)}

    def get_stats(self) -> dict:
        """获取 Frigate 系统状态"""
        return self._request("stats")

    def get_cameras(self) -> list:
        """获取摄像头列表"""
        stats = self.get_stats()
        if "error" in stats:
            return []
        cameras = []
        for cam_id, cam_info in stats.get("cameras", {}).items():
            cameras.append({
                "camera_id": cam_id,
                "name": cam_id,
                "fps": cam_info.get("camera_fps", 0),
                "detect_fps": cam_info.get("detect_fps", 0),
                "process_fps": cam_info.get("process_fps", 0),
                "pid": cam_info.get("capture_pid", 0),
                "active": cam_info.get("capture_pid", 0) > 0,
            })
        self._cameras = cameras
        return cameras

    def get_config(self) -> dict:
        """获取 Frigate 配置"""
        return self._request("config")

    def get_events(self, cameras: list = None, label: str = None,
                   after: float = None, before: float = None,
                   limit: int = 25, has_clip: bool = None,
                   has_snapshot: bool = None) -> list:
        """
        获取检测事件。

        参数：
          cameras: 摄像头列表过滤
          label: 检测标签过滤 (person / car / dog / cat / ...)
          after: 起始时间 (Unix timestamp)
          before: 结束时间
          limit: 最大返回数量
          has_clip: 是否有视频片段
          has_snapshot: 是否有快照
        """
        params = []
        if cameras:
            for cam in cameras:
                params.append(f"cameras={cam}")
        if label:
            params.append(f"label={label}")
        if after:
            params.append(f"after={after}")
        if before:
            params.append(f"before={before}")
        if limit:
            params.append(f"limit={limit}")
        if has_clip is not None:
            params.append(f"has_clip={str(has_clip).lower()}")
        if has_snapshot is not None:
            params.append(f"has_snapshot={str(has_snapshot).lower()}")

        endpoint = "events"
        if params:
            endpoint += "?" + "&".join(params)

        result = self._request(endpoint)
        if isinstance(result, list):
            self._events_cache = result
            self._last_events_fetch = time.time()
            return result
        return []

    def get_recent_events(self, label: str = None, minutes: int = 60,
                          limit: int = 10) -> list:
        """获取最近的检测事件（便捷方法）"""
        after = time.time() - minutes * 60
        return self.get_events(label=label, after=after, limit=limit)

    def get_event(self, event_id: str) -> dict:
        """获取单个事件详情"""
        return self._request(f"events/{event_id}")

    def get_snapshot_url(self, event_id: str, camera: str = None) -> str:
        """获取事件快照 URL"""
        if camera:
            return f"{self.base_url}/api/{camera}/{event_id}/snapshot.jpg"
        return f"{self.base_url}/api/events/{event_id}/snapshot.jpg"

    def get_clip_url(self, event_id: str, camera: str = None) -> str:
        """获取事件视频片段 URL"""
        if camera:
            return f"{self.base_url}/api/{camera}/{event_id}/clip.mp4"
        return f"{self.base_url}/api/events/{event_id}/clip.mp4"

    def get_latest_detections(self, camera: str) -> dict:
        """获取摄像头最新检测结果"""
        return self._request(f"{camera}/latest detections")

    def get_active_zones(self, camera: str) -> list:
        """获取摄像头当前活动区域"""
        return self._request(f"{camera}/active zones")

    def get_summary(self, minutes: int = 60) -> dict:
        """
        获取检测摘要。

        返回按标签分组的事件统计，用于系统概览。
        """
        events = self.get_recent_events(minutes=minutes, limit=100)
        summary = {
            "total": len(events),
            "by_label": {},
            "by_camera": {},
            "recent": [],
        }

        for evt in events:
            label = evt.get("label", "unknown")
            cam = evt.get("camera", "unknown")
            summary["by_label"][label] = summary["by_label"].get(label, 0) + 1
            summary["by_camera"][cam] = summary["by_camera"].get(cam, 0) + 1

        # 最近 5 条
        summary["recent"] = [
            {
                "event_id": e.get("id", ""),
                "camera": e.get("camera", ""),
                "label": e.get("label", ""),
                "top_score": e.get("top_score", 0),
                "start_time": e.get("start_time", 0),
                "has_clip": e.get("has_clip", False),
                "has_snapshot": e.get("has_snapshot", False),
            }
            for e in events[:5]
        ]

        return summary


# ─────────── 单例 ───────────

_frigate_instance = None


def get_frigate() -> FrigateAdapter:
    global _frigate_instance
    if _frigate_instance is None:
        _frigate_instance = FrigateAdapter()
    return _frigate_instance
