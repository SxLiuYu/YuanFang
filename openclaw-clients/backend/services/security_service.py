#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安全监控服务框架"""
import logging
from typing import Dict, Any
logger = logging.getLogger(__name__)
async def get_door_status() -> Dict[str, Any]: return {"locked": True}
async def unlock_door() -> Dict[str, Any]: return {"status": "unlocked"}
async def get_camera_stream(camera_id: str) -> Dict[str, Any]: return {"stream_url": f"rtsp://camera/{camera_id}"}
async def get_alarm_status() -> Dict[str, Any]: return {"armed": False}
