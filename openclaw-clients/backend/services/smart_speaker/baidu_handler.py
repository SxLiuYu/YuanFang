#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小度音箱回调处理"""
import logging
from typing import Dict, Any
logger = logging.getLogger(__name__)
async def handle(request_body: Dict[str, Any]) -> Dict[str, Any]:
    intent = request_body.get("intent", {}).get("name", "")
    logger.info(f"Baidu intent: {intent}")
    return {"version": "1.0", "response": {"output": {"speech": {"text": "收到"}}}}
