#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天猫精灵技能回调处理
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理天猫精灵请求
    
    天猫精灵协议：
    https://open.aligenie.com/doc
    """
    intent = request_body.get("intent", {})
    intent_name = intent.get("name", "")
    slots = intent.get("slots", {})
    
    logger.info(f"Tmall intent: {intent_name}, slots: {slots}")
    
    # 路由到不同意图处理
    if intent_name == "chat":
        return await _handle_chat(slots)
    elif intent_name == "smart_home_control":
        return await _handle_smart_home(slots)
    elif intent_name == "account_query":
        return await _handle_account(slots)
    elif intent_name == "task_management":
        return await _handle_task(slots)
    elif intent_name == "shopping_list":
        return await _handle_shopping(slots)
    elif intent_name == "recipe_help":
        return await _handle_recipe(slots)
    else:
        return _default_response()

async def _handle_chat(slots: Dict) -> Dict[str, Any]:
    """聊天意图"""
    # 调用 AI 对话服务
    from .. import chat_service
    
    query = slots.get("query", {}).get("value", "你好")
    result = await chat_service.chat(query, session_id="tmall_default", voice_output=True)
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": result["text"],
            "actions": []
        },
        "sessionAttributes": {}
    }

async def _handle_smart_home(slots: Dict) -> Dict[str, Any]:
    """智能家居控制"""
    from .. import smart_home_service
    
    device = slots.get("device", {}).get("value", "")
    action = slots.get("action", {}).get("value", "")
    
    # 调用设备控制
    result = await smart_home_service.control_device(device, action)
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": f"已{action}{device}",
            "actions": []
        }
    }

async def _handle_account(slots: Dict) -> Dict[str, Any]:
    """账单查询"""
    from .. import finance_service
    
    result = await finance_service.get_daily_report()
    
    speech = f"今天收入{result['income']}元，支出{result['expense']}元"
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": speech
        }
    }

async def _handle_task(slots: Dict) -> Dict[str, Any]:
    """任务管理"""
    from .. import task_service
    
    task_title = slots.get("task", {}).get("value", "")
    result = await task_service.create_task(task_title)
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": f"已添加任务：{task_title}"
        }
    }

async def _handle_shopping(slots: Dict) -> Dict[str, Any]:
    """购物清单"""
    from .. import shopping_service
    
    item = slots.get("item", {}).get("value", "")
    await shopping_service.add_item(item)
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": f"已添加{item}到购物清单"
        }
    }

async def _handle_recipe(slots: Dict) -> Dict[str, Any]:
    """菜谱帮助"""
    from .. import recipe_service
    
    ingredient = slots.get("ingredient", {}).get("value", "")
    result = await recipe_service.recommend(ingredient)
    
    speech = "推荐菜谱：" + ", ".join([r.get("name", "") for r in result.get("recipes", [])])
    
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": speech
        }
    }

def _default_response() -> Dict[str, Any]:
    """默认响应"""
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "speech": "抱歉，我还没学会这个功能"
        }
    }
