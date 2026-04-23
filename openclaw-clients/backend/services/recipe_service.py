#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""做菜助手服务"""
import logging
from typing import Dict, Any, List
logger = logging.getLogger(__name__)

_recipes = [
    {"id": 1, "name": "红烧肉", "difficulty": "medium", "time": 60},
    {"id": 2, "name": "番茄炒蛋", "difficulty": "easy", "time": 15},
    {"id": 3, "name": "宫保鸡丁", "difficulty": "medium", "time": 30}
]
_timers: List[Dict] = []

async def recommend(ingredients: str = None) -> Dict[str, Any]:
    return {"recipes": _recipes}

async def search(keyword: str) -> Dict[str, Any]:
    results = [r for r in _recipes if keyword in r["name"]]
    return {"recipes": results}

async def get_detail(recipe_id: str) -> Dict[str, Any]:
    for r in _recipes:
        if str(r["id"]) == recipe_id:
            return r
    return {"error": "Recipe not found"}

async def start_timer(minutes: int, label: str = None) -> Dict[str, Any]:
    import time
    timer = {"id": len(_timers) + 1, "minutes": minutes, "label": label, "start_time": time.time()}
    _timers.append(timer)
    return timer
