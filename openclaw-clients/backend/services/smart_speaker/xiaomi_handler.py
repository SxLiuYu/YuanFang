#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小爱同学技能回调处理
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """处理小爱请求"""
    intent = request_body.get("intent", {})
    intent_name = intent.get("name", "")
    slots = intent.get("slots", {})
    
    logger.info(f"Xiaomi intent: {intent_name}")
    
    # 路由处理（类似天猫精灵）
    if intent_name == "chat":
        return await _handle_chat(slots)
    elif intent_name == "smart_home_control":
        return await _handle_smart_home(slots)
    elif intent_name == "account_query":
        return await _handle_account(slots)
    else:
        return _default_response()

async def _handle_chat(slots: Dict) -> Dict[str, Any]:
    from .. import chat_service
    query = slots.get("query", {}).get("value", "你好")
    result = await chat_service.chat(query, session_id="xiaomi_default", voice_output=True)
    
    return {
        "to_speak": {"text": result["text"]},
        "to_display": {"type": "txt", "text": result["text"]}
    }

async def _handle_smart_home(slots: Dict) -> Dict[str, Any]:
    from .. import smart_home_service
    device = slots.get("device", {}).get("value", "")
    action = slots.get("action", {}).get("value", "")
    await smart_home_service.control_device(device, action)
    
    return {
        "to_speak": {"text": f"已{action}{device}"}
    }

async def _handle_account(slots: Dict) -> Dict[str, Any]:
    from .. import finance_service
    result = await finance_service.get_daily_report()
    
    return {
        "to_speak": {"text": f"今天收入{result['income']}元，支出{result['expense']}元"}
    }

def _default_response() -> Dict[str, Any]:
    return {
        "to_speak": {"text": "抱歉，我还没学会这个功能"}
    }
