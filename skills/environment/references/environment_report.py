# references/environment_report.py
"""
Environment Report Generator · 环境报告生成器
从 KAIROS 工具和传感器数据生成环境摘要
"""
from typing import Optional


def format_environment_report(
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    aqi: Optional[int] = None,
    co2: Optional[int] = None,
    pm25: Optional[float] = None,
    noise: Optional[float] = None,
) -> str:
    """
    格式化环境报告
    
    Args:
        temperature: 温度 (°C)
        humidity: 湿度 (%)
        aqi: 空气质量指数
        co2: CO2 浓度 (ppm)
        pm25: PM2.5 (μg/m³)
        noise: 噪音 (dB)
    
    Returns:
        格式化的环境报告文本
    """
    lines = ["当前环境："]

    # 温度
    if temperature is not None:
        comfort = "舒适"
        if temperature > 30:
            comfort = "偏热，建议开空调"
        elif temperature > 28:
            comfort = "微热"
        elif temperature < 15:
            comfort = "偏冷，建议开暖气"
        elif temperature < 18:
            comfort = "微凉"
        lines.append(f"🌡️ 温度：{temperature}°C（{comfort}）")
    else:
        lines.append("🌡️ 温度：暂无数据")

    # 湿度
    if humidity is not None:
        hum_desc = "适宜"
        if humidity > 80:
            hum_desc = "偏湿，建议开除湿"
        elif humidity > 70:
            hum_desc = "微湿"
        elif humidity < 30:
            hum_desc = "偏干，建议开加湿器"
        elif humidity < 40:
            hum_desc = "微干"
        lines.append(f"💧 湿度：{humidity}%（{hum_desc}）")
    else:
        lines.append("💧 湿度：暂无数据")

    # 空气质量
    if aqi is not None:
        aqi_levels = [
            (0, 50, "优", "🍃"),
            (51, 100, "良", "🙂"),
            (101, 150, "轻度污染", "😐"),
            (151, 200, "中度污染", "😷"),
            (201, 300, "重度污染", "🤢"),
            (301, 500, "严重污染", "⚠️"),
        ]
        aqi_desc, aqi_emoji = "未知", ""
        for low, high, desc, emoji in aqi_levels:
            if low <= aqi <= high:
                aqi_desc = desc
                aqi_emoji = emoji
                break
        lines.append(f"🌬️ 空气质量：{aqi}（{aqi_emoji} {aqi_desc}）")
    else:
        lines.append("🌬️ 空气质量：暂无数据")

    # PM2.5
    if pm25 is not None:
        pm_desc = "优" if pm25 <= 35 else ("良" if pm25 <= 75 else ("轻度" if pm25 <= 115 else "较差"))
        lines.append(f"🌫️ PM2.5：{pm25} μg/m³（{pm_desc}）")

    # CO2
    if co2 is not None:
        co2_desc = "正常" if co2 <= 800 else ("偏高" if co2 <= 1200 else "过高，建议通风")
        lines.append(f"💨 CO2：{co2} ppm（{co2_desc}）")

    # 噪音
    if noise is not None:
        noise_desc = "安静" if noise <= 40 else ("正常" if noise <= 60 else ("较吵" if noise <= 75 else "很吵"))
        lines.append(f"🔊 噪音：{noise} dB（{noise_desc}）")

    return "\n".join(lines)


def get_environment_suggestions(
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    aqi: Optional[int] = None,
    co2: Optional[int] = None,
) -> list[str]:
    """
    根据环境数据生成建议
    
    Returns:
        建议列表
    """
    suggestions = []

    if temperature is not None:
        if temperature > 28:
            suggestions.append("建议开启空调降温")
        elif temperature < 18:
            suggestions.append("建议开启暖气或空调制热")
    
    if humidity is not None:
        if humidity > 70:
            suggestions.append("建议开启除湿模式")
        elif humidity < 40:
            suggestions.append("建议开启加湿器")
    
    if aqi is not None and aqi > 100:
        suggestions.append("空气质量不佳，建议关闭门窗并开启新风/空气净化器")
    
    if co2 is not None and co2 > 1000:
        suggestions.append("CO2 浓度偏高，建议开窗通风换气")

    return suggestions
