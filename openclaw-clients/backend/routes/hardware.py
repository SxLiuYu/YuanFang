from fastapi import APIRouter, Request
import logging
from services.hardware_service import (
    hardware_service, DeviceRegister, DeviceControl, WatchDataSync, SpeakerCommand
)
from shared import success_response, error_response

router = APIRouter(prefix="/api/v1/hardware", tags=["hardware"])

@router.get("/devices")
async def get_hardware_devices(device_type: str = None, status: str = None):
    try:
        result = await hardware_service.get_devices(device_type, status)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get hardware devices error: {e}")
        return error_response(str(e))

@router.post("/devices")
async def register_hardware_device(request: DeviceRegister):
    try:
        result = await hardware_service.register_device(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Register hardware device error: {e}")
        return error_response(str(e))

@router.get("/devices/{device_id}")
async def get_hardware_device(device_id: str):
    try:
        result = await hardware_service.get_device(device_id)
        if result:
            return success_response(result)
        return error_response("设备不存在", 404)
    except Exception as e:
        logging.error(f"Get hardware device error: {e}")
        return error_response(str(e))

@router.post("/devices/{device_id}/control")
async def control_hardware_device(device_id: str, request: DeviceControl):
    try:
        request.device_id = device_id
        result = await hardware_service.control_device(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Control hardware device error: {e}")
        return error_response(str(e))

@router.post("/devices/watch/sync")
async def sync_watch_data(request: WatchDataSync):
    try:
        result = await hardware_service.sync_watch_data(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Sync watch data error: {e}")
        return error_response(str(e))

@router.get("/devices/{device_id}/watch/data")
async def get_watch_data(device_id: str, user_id: str = None, days: int = 7):
    try:
        result = await hardware_service.get_watch_data(device_id, user_id, days)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get watch data error: {e}")
        return error_response(str(e))

@router.get("/devices/{device_id}/watch/summary")
async def get_health_summary(device_id: str, user_id: str):
    try:
        result = await hardware_service.get_health_summary(device_id, user_id)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get health summary error: {e}")
        return error_response(str(e))

@router.post("/devices/speaker/command")
async def send_speaker_command(request: SpeakerCommand):
    try:
        result = await hardware_service.send_speaker_command(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Send speaker command error: {e}")
        return error_response(str(e))

@router.get("/bluetooth/scan")
async def scan_bluetooth_devices():
    try:
        result = await hardware_service.scan_bluetooth_devices()
        return success_response(result)
    except Exception as e:
        logging.error(f"Scan bluetooth devices error: {e}")
        return error_response(str(e))

@router.post("/bluetooth/pair")
async def pair_bluetooth_device(device_id: str, device_name: str, device_type: str):
    try:
        result = await hardware_service.pair_bluetooth_device(device_id, device_name, device_type)
        return success_response(result)
    except Exception as e:
        logging.error(f"Pair bluetooth device error: {e}")
        return error_response(str(e))