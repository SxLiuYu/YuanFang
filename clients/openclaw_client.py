"""
OpenClaw API Client
YuanFang 通过 HTTP 调用 OpenClaw 后端服务，不再嵌入源码副本
OpenClaw 后端应独立部署在 localhost:8082 或其他地址
"""
import os
import logging
import requests
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

OPENCLAW_BASE_URL = os.getenv("OPENCLAW_API_URL", "http://localhost:8082").rstrip("/")
OPENCLAW_TIMEOUT = int(os.getenv("OPENCLAW_TIMEOUT", "10"))


class OpenClawClient:
    """OpenClaw Family Assistant API 客户端"""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or OPENCLAW_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        logger.info(f"OpenClawClient init: {self.base_url}")

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            if method == "GET":
                resp = self.session.get(url, params=params, timeout=OPENCLAW_TIMEOUT)
            else:
                resp = self.session.post(url, json=data, timeout=OPENCLAW_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            logger.warning(f"OpenClaw 不可达: {self.base_url}")
            return {"success": False, "message": "OpenClaw service unavailable"}
        except requests.exceptions.HTTPError as e:
            logger.error(f"OpenClaw HTTP {e.response.status_code}: {e.response.text[:200]}")
            return {"success": False, "message": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"OpenClaw request failed: {e}")
            return {"success": False, "message": str(e)}

    def health(self) -> bool:
        r = self._request("GET", "/health")
        return r.get("success", False)

    def chat(self, message: str, session_id: str = "default") -> dict:
        return self._request("POST", "/api/v1/agent/chat",
                             {"message": message, "session_id": session_id})

    def smart_home_list_devices(self) -> dict:
        return self._request("GET", "/api/v1/smart-home/device/list")

    def smart_home_control(self, device_id: str, action: str, value: Any = None) -> dict:
        return self._request("POST", "/api/v1/smart-home/device/control",
                             {"device_id": device_id, "action": action, "value": value})

    def voice_command(self, text: str, context: dict = None) -> dict:
        return self._request("POST", "/api/v1/voice/command",
                             {"text": text, "context": context})

    def finance_add_transaction(self, amount: float, category: str, type: str, description: str = "") -> dict:
        return self._request("POST", "/api/v1/finance/transaction/add",
                             {"amount": amount, "category": category, "type": type, "description": description})

    def finance_daily_report(self, date: str = None) -> dict:
        return self._request("GET", "/api/v1/finance/report/daily", params={"date": date})

    def finance_monthly_report(self, month: str = None) -> dict:
        return self._request("GET", "/api/v1/finance/report/monthly", params={"month": month})

    def task_create(self, title: str, assignee: str = None) -> dict:
        return self._request("POST", "/api/v1/task/create",
                             {"title": title, "assignee": assignee})

    def task_list(self, status: str = None) -> dict:
        return self._request("GET", "/api/v1/task/list", params={"status": status})

    def shopping_add(self, name: str, quantity: int = 1) -> dict:
        return self._request("POST", "/api/v1/shopping/item/add",
                             {"name": name, "quantity": quantity})

    def shopping_list(self) -> dict:
        return self._request("GET", "/api/v1/shopping/list")

    def recipe_recommend(self, ingredients: str = None) -> dict:
        return self._request("GET", "/api/v1/recipe/recommend", params={"ingredients": ingredients})

    def health_record_metric(self, metric_type: str, value: float, unit: str) -> dict:
        return self._request("POST", "/api/v1/health/metrics/record",
                             {"metric_type": metric_type, "value": value, "unit": unit})

    def calendar_create_event(self, title: str, start_time: str) -> dict:
        return self._request("POST", "/api/v1/calendar/event/create",
                             {"title": title, "start_time": start_time})

    def calendar_today(self) -> dict:
        return self._request("GET", "/api/v1/calendar/today")

    def reminder_create(self, title: str, trigger_time: str = None, reminder_type: str = "time") -> dict:
        return self._request("POST", "/api/v1/reminder/create",
                             {"title": title, "trigger_time": trigger_time, "reminder_type": reminder_type})

    def analytics_health_score(self, user_id: str) -> dict:
        return self._request("GET", "/api/v1/analytics/health/score", params={"user_id": user_id})

    def analytics_finance_insights(self, user_id: str, period_days: int = 30) -> dict:
        return self._request("GET", "/api/v1/analytics/finance/insights",
                             params={"user_id": user_id, "period_days": period_days})

    def personal_location(self, latitude: float, longitude: float) -> dict:
        return self._request("POST", "/api/v1/personal/location",
                             {"latitude": latitude, "longitude": longitude})

    def personal_health_summary(self) -> dict:
        return self._request("GET", "/api/v1/personal/health/summary")

    def personal_payment_summary(self, month: str = None) -> dict:
        return self._request("GET", "/api/v1/personal/payment/summary", params={"month": month})


_client: Optional[OpenClawClient] = None


def get_openclaw_client() -> OpenClawClient:
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client