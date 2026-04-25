from fastapi import APIRouter
import logging
from typing import Optional, Any
from services.smart_home_service import smart_home_service
from shared import success_response, error_response, SmartHomeControlRequest

router = APIRouter(prefix="/api/v1/smart-home", tags=["smart-home"])

@router.post("/device/control")
async def smart_home_control(request: SmartHomeControlRequest):
    try:
        result = await smart_home_service.control_device(
            device_id=request.device_id, action=request.action, value=request.value
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/device/list")
async def smart_home_device_list():
    try:
        result = await smart_home_service.list_devices()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/device/status")
async def smart_home_device_status(device_id: str):
    try:
        result = await smart_home_service.get_device_status(device_id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/scene/activate")
async def smart_home_scene_activate(scene_id: str):
    try:
        result = await smart_home_service.activate_scene(scene_id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/energy/report")
async def smart_home_energy_report():
    try:
        result = await smart_home_service.get_energy_report()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))