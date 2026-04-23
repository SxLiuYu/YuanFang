"""
Weather Outfit Suggestion — 天气穿搭建议
根据今天天气温度，推荐穿什么衣服
"""

import json
import os
from typing import Optional


def get_outfit_suggestion(city: str = "北京") -> str:
    """根据天气给出穿搭建议"""
    try:
        import requests
        # 使用wttr.in获取JSON格式天气
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # 获取当前温度
        current_temp = float(data["current_condition"][0]["temp_C"])
        
        # 获取当日最高最低
        daily = data["weather"][0]
        min_temp = float(daily["mintempC"])
        max_temp = float(daily["maxtempC"])
        
        # 根据温度区间给出穿搭建议
        if max_temp >= 28:
            suggestion = f"""🎽 今日{city}气温 {min_temp}°C ~ {max_temp}°C，天气炎热：
建议穿短袖T恤、短裤、裙子等夏季衣物，注意防晒降温，多喝温水。"""
        elif 20 <= max_temp < 28:
            suggestion = f"""👕 今日{city}气温 {min_temp}°C ~ {max_temp}°C，舒适温暖：
建议穿长袖T恤、薄衬衫、薄外套，早晚稍凉可以带个开衫。"""
        elif 15 <= max_temp < 20:
            suggestion = f"""🧥 今日{city}气温 {min_temp}°C ~ {max_temp}°C，天气凉爽：
建议穿薄风衣、夹克、长袖卫衣，里面搭配衬衫或者T恤，方便穿脱。"""
        elif 5 <= max_temp < 15:
            suggestion = f"""🧶 今日{city}气温 {min_temp}°C ~ {max_temp}°C，天气偏凉：
建议穿毛衣、线衫加外套，或者厚风衣，怕冷可以戴围巾。"""
        else:
            suggestion = f"""🧥 今日{city}气温 {min_temp}°C ~ {max_temp}°C，天气寒冷：
建议穿厚羽绒服或者棉服，搭配毛衣、秋裤，注意保暖手和脖子。"""
        
        # 添加天气状况
        weather_desc = data["current_condition"][0]["weatherDesc"][0]["value"]
        suggestion += f"\n\n今日天气状况：{weather_desc}"
        
        return suggestion
        
    except Exception as e:
        return f"获取天气失败，无法给出穿搭建议：{str(e)}"


def outfit_suggestion_handler(text: str) -> Optional[str]:
    """穿搭建议意图处理"""
    text = text.lower().strip()
    
    keywords = [
        "穿什么", "穿什么衣服", "推荐穿什么", "穿搭建议",
        "今天穿什么", "出门穿什么", "穿搭推荐"
    ]
    
    for kw in keywords:
        if kw in text:
            # 提取城市，默认北京
            import re
            # 找城市名
            city = "北京"
            # 简单匹配："北京今天穿什么" → 北京
            words = text.replace("今天", "").replace("穿什么", "").replace("衣服", "").replace("穿搭", "").replace("建议", "").replace("推荐", "").replace("出门", "").strip()
            if words:
                city = words
            return get_outfit_suggestion(city)
    
    return None