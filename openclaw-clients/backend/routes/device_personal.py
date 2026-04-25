from fastapi import APIRouter, Request
import logging
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from services.device_auth_service import device_auth_service
from services.personal_data_service import get_service as get_personal_service
from shared import success_response, error_response

router = APIRouter(tags=["device-personal"])

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = "Unknown Device"
    device_model: Optional[str] = "Unknown"

class DeviceConfirmRequest(BaseModel):
    temp_id: str
    confirm_code: str

# Device Auth
@router.post("/device/register")
async def device_register(request: DeviceRegisterRequest):
    try:
        result = device_auth_service.register_device(
            device_id=request.device_id,
            device_name=request.device_name or "Unknown Device",
            device_model=request.device_model or "Unknown")
        return JSONResponse(content={"success": True, **result})
    except Exception as e:
        logging.error(f"Device register error: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@router.post("/device/confirm")
async def device_confirm(request: DeviceConfirmRequest):
    try:
        result = device_auth_service.confirm_device(
            temp_id=request.temp_id, confirm_code=request.confirm_code)
        return JSONResponse(content={"success": result.get("confirmed", False), **result})
    except Exception as e:
        logging.error(f"Device confirm error: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@router.get("/device/status")
async def device_status(device_id: str):
    try:
        return success_response(device_auth_service.check_device_status(device_id))
    except Exception as e:
        return error_response(str(e))

@router.get("/device/stats")
async def device_stats():
    try:
        return success_response(device_auth_service.get_stats())
    except Exception as e:
        return error_response(str(e))

@router.post("/device/logout")
async def device_logout(request: DeviceRegisterRequest):
    try:
        return success_response({"logged_out": device_auth_service.logout_device(request.device_id)})
    except Exception as e:
        return error_response(str(e))

@router.get("/device/debug/pending")
async def device_debug_pending():
    try:
        pending = []
        for temp_id, data in device_auth_service.pending_confirmations.items():
            pending.append({"temp_id": temp_id, "device_id": data.device_id,
                            "device_name": data.device_name, "confirm_code": data.confirm_code,
                            "expires_at": data.expires_at.isoformat()})
        return success_response({"pending": pending})
    except Exception as e:
        return error_response(str(e))

# Personal Data
@router.post("/api/v1/personal/location")
async def personal_location(request: Request):
    try:
        body = await request.json()
        service = get_personal_service()
        result = service.record_location(
            latitude=body.get('latitude'), longitude=body.get('longitude'),
            accuracy=body.get('accuracy', 10.0))
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/personal/location/history")
async def personal_location_history(hours: int = 24):
    return success_response(get_personal_service().get_location_history(hours))

@router.get("/api/v1/personal/location/stats")
async def personal_location_stats(days: int = 7):
    return success_response(get_personal_service().get_location_stats(days))

@router.post("/api/v1/personal/location/place")
async def add_known_place(request: Request):
    try:
        body = await request.json()
        service = get_personal_service()
        result = service.add_known_place(
            name=body.get('name'), place_type=body.get('place_type'),
            latitude=body.get('latitude'), longitude=body.get('longitude'),
            radius=body.get('radius', 100))
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/personal/health/summary")
async def personal_health_summary():
    return success_response(get_personal_service().get_health_summary())

@router.get("/api/v1/personal/health/history")
async def personal_health_history(days: int = 7):
    return success_response(get_personal_service().get_health_history(days))

@router.get("/api/v1/personal/payment/summary")
async def personal_payment_summary(month: str = None):
    return success_response(get_personal_service().get_payment_summary(month))

@router.post("/api/v1/personal/payment/history")
async def personal_payment_history(days: int = 30):
    return success_response(get_personal_service().get_payment_history(days))