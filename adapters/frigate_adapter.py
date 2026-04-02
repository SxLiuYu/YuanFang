# adapters/frigate_adapter.py
"""
Frigate NVR adapter
"""
import os
import logging
import urllib.request
import urllib.error
import json

logger = logging.getLogger(__name__)

FRIGATE_URL = os.getenv("FRIGATE_URL", "http://localhost:5000")
FRIGATE_API_KEY = os.getenv("FRIGATE_API_KEY", "")


class FrigateAdapter:
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = (base_url or FRIGATE_URL or "http://localhost:5000").rstrip("/")
        self.api_key = api_key or FRIGATE_API_KEY or ""

    def _request(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            logger.error(f"Frigate HTTP {e.code}: {body[:100]}")
            return {}
        except Exception as e:
            logger.error(f"Frigate request failed: {e}")
            return {}

    def get_cameras(self) -> list[dict]:
        return self._request("/api/cameras") or {}

    def get_snapshot(self, camera_name: str, bbox: list = None) -> bytes | None:
        path = f"/api/{camera_name}/snapshot"
        if bbox:
            x1, y1, x2, y2 = bbox
            path += f"?bbox={x1},{y1},{x2},{y2}"
        url = f"{self.base_url}{path}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read()
        except Exception as e:
            logger.error(f"Frigate snapshot failed: {e}")
            return None

    def get_events(self, camera_name: str = None, limit: int = 20) -> list[dict]:
        path = f"/api/events?limit={limit}"
        if camera_name:
            path += f"&camera={camera_name}"
        return self._request(path) or []

    def get_detection_status(self) -> dict:
        return self._request("/api/status")


_frigate = None


def get_frigate_adapter() -> FrigateAdapter:
    global _frigate
    if _frigate is None:
        _frigate = FrigateAdapter()
    return _frigate
