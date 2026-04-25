from fastapi import APIRouter
import logging
from typing import Optional
from services.health_service import health_service
from services.calendar_service import calendar_service
from shared import success_response, error_response

router = APIRouter(tags=["health-calendar"])

@router.post("/api/v1/health/metrics/record")
async def health_metrics_record(metric_type: str, value: float, unit: str, date: Optional[str] = None):
    try:
        result = await health_service.record_metric(metric_type=metric_type, value=value, unit=unit, date=date)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/health/metrics/history")
async def health_metrics_history(metric_type: str, days: Optional[int] = 30):
    try:
        result = await health_service.get_history(metric_type, days)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/health/exercise/stats")
async def health_exercise_stats(days: Optional[int] = 7):
    try:
        result = await health_service.get_exercise_stats(days)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/api/v1/health/report/generate")
async def health_report_generate(period: str = "weekly"):
    try:
        result = await health_service.generate_report(period)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/api/v1/calendar/event/create")
async def calendar_event_create(title: str, start_time: str, end_time: Optional[str] = None,
                                 description: Optional[str] = None, reminder: Optional[int] = 30):
    try:
        result = await calendar_service.create_event(
            title=title, start_time=start_time, end_time=end_time,
            description=description, reminder=reminder
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/calendar/event/list")
async def calendar_event_list(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        result = await calendar_service.list_events(start_date, end_date)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/calendar/today")
async def calendar_today():
    try:
        result = await calendar_service.get_today()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/calendar/countdown")
async def calendar_countdown(event_name: str):
    try:
        result = await calendar_service.get_countdown(event_name)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))