# adapters/ha_adapter.py
from __future__ import annotations
"""
HomeAssistant 适配器 · HA Adapter
与 HomeAssistant REST API 交互
"""
import os
import logging
import urllib.request
import urllib.error
import json

logger = logging.getLogger(__name__)

HA_BASE = os.getenv("HA_BASE_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")


class HAAdapter:
    """HomeAssistant REST API 客户端"""

    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = (base_url or HA_BASE or "http://localhost:8123").rstrip("/")
        self.token = token or HA_TOKEN or ""
        self._states_cache = {}

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.error(f"HA HTTP {e.code}: {e.read().decode()[:200]}")
            return {}
        except Exception as e:
            logger.error(f"HA request failed: {e}")
            return {}

    def get_state(self, entity_id: str) -> dict:
        return self._request("GET", f"/api/states/{entity_id}")

    def call_service(self, domain: str, service: str, data: dict = None) -> dict:
        payload = data or {}
        return self._request("POST", f"/api/services/{domain}/{service}", payload)

    def list_devices(self) -> list:
        states = self._request("GET", "/api/states") or []
        return [{"entity_id": s.get("entity_id"), "state": s.get("state"),
                 "attributes": s.get("attributes", {})} for s in states]


_ha: HAAdapter | None = None


def get_ha_adapter() -> HAAdapter:
    global _ha
    if _ha is None:
        _ha = HAAdapter()
    return _ha
