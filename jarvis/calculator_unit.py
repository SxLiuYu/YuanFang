"""
Calculator & Unit Converter — 计算器和单位转换工具
支持数学计算、长度/重量/温度/时间等单位转换
"""

import math
import re
from typing import Optional, Tuple


def calculate_expression(expr_text: str) -> str:
    """计算数学表达式"""
    expr = expr_text
    # 清理表达式
    expr = expr.replace("乘以", "*").replace("乘", "*")
    expr = expr.replace("除以", "/").replace("除", "/")
    expr = expr.replace("加", "+").replace("减", "-")
    expr = expr.replace("的平方", "**2").replace("平方", "**2")
    expr = expr.replace("平方根", "sqrt(").replace("根号", "sqrt(")
    # 给根号补括号  sqrt 16 → sqrt(16)
    import re
    expr = re.sub(r'sqrt\s+(\d+)', r'sqrt(\1)', expr)
    # 如果开头是sqrt(但没有闭合，补一个)在末尾
    if 'sqrt(' in expr and expr.count('(') > expr.count(')'):
        expr += ')'
    expr = expr.replace("π", "pi").replace("pi", "pi")
    
    # 提取数字和运算符
    expr = re.sub(r'[^\d\.\+\-\*\/\(\)\s\w]', '', expr)
    
    try:
        # 安全计算 — 只允许基本运算
        allowed_names = {
            'sqrt': math.sqrt,
            'pow': math.pow,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'pi': math.pi,
            'e': math.e,
        }
        result = eval(expr, {"__builtins__": None}, allowed_names)
        # 格式化结果
        if isinstance(result, float):
            if result.is_integer():
                return f"结果是 {int(result)}"
            else:
                return f"结果是 {result:.6g}"
        return f"结果是 {result}"
    except Exception as e:
        return f"计算失败：{str(e)}"


# 单位转换映射
UNIT_CONVERSION = {
    # 长度
    ("米",): {
        "千米": 0.001,
        "公里": 0.001,
        "厘米": 100,
        "公分": 100,
        "毫米": 1000,
        "米": 1,
        "英寸": 39.3701,
        "英尺": 3.28084,
        "尺": 3,
        "里": 0.002,
    },
    ("千米", "公里"): {
        "米": 1000,
    },
    ("厘米", "公分"): {
        "米": 0.01,
        "毫米": 10,
        "英寸": 0.393701,
    },
    ("英寸"): {
        "厘米": 2.54,
        "米": 0.0254,
    },
    ("英尺"): {
        "厘米": 30.48,
        "米": 0.3048,
        "英寸": 12,
    },
    # 重量
    ("千克", "公斤"): {
        "克": 1000,
        "斤": 2,
        "公斤": 1,
        "千克": 1,
        "磅": 2.20462,
        "盎司": 35.274,
    },
    ("克"): {
        "千克": 0.001,
        "斤": 0.002,
    },
    ("斤"): {
        "千克": 0.5,
        "克": 500,
    },
    ("磅"): {
        "千克": 0.453592,
        "克": 453.592,
    },
    # 温度
    ("摄氏度", "c", "摄氏"): {
        "华氏度": lambda x: x * 9/5 + 32,
        "开尔文": lambda x: x + 273.15,
        "f": lambda x: x * 9/5 + 32,
    },
    ("华氏度", "f", "华氏"): {
        "摄氏度": lambda x: (x - 32) * 5/9,
        "c": lambda x: (x - 32) * 5/9,
    },
    # 面积
    ("平方米"): {
        "平方英尺": 10.7639,
        "亩": 0.0015,
    },
    # 体积
    ("升"): {
        "毫升": 1000,
        "加仑": 0.264172,
    },
    ("毫升"): {
        "升": 0.001,
    },
    # 时间
    ("小时"): {
        "分钟": 60,
        "秒": 3600,
        "天": 1/24,
    },
    ("分钟"): {
        "小时": 1/60,
        "秒": 60,
    },
    ("天"): {
        "小时": 24,
    },
}


def normalize_unit(unit: str) -> str:
    """标准化单位名称"""
    unit_map = {
        "公里": "千米",
        "千米": "千米",
        "公分": "厘米",
        "厘米": "厘米",
        "公尺": "米",
        "米": "米",
        "公斤": "千克",
        "千克": "千克",
        "华氏": "华氏度",
        "摄氏": "摄氏度",
        "c": "摄氏度",
        "f": "华氏度",
    }
    for k, v in unit_map.items():
        if k in unit:
            return v
    return unit


def find_conversion(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    """查找转换"""
    from_norm = normalize_unit(from_unit)
    to_norm = normalize_unit(to_unit)
    
    if from_norm == to_norm:
        return value
    
    # 找匹配的转换
    for keys, conv in UNIT_CONVERSION.items():
        if from_norm in keys or from_unit in keys:
            if to_norm in conv:
                factor = conv[to_norm]
                if callable(factor):
                    return factor(value)
                else:
                    return value * factor
            # 反向查找？
            for rev_keys, rev_conv in UNIT_CONVERSION.items():
                if to_norm in rev_keys:
                    if from_norm in rev_conv:
                        # 可以转成 base unit 然后转出去...这里简化
                        pass
    
    return None


def parse_conversion_request(text: str) -> Optional[Tuple[float, str, str]]:
    """解析转换请求：'100米等于多少厘米'"""
    text_orig = text
    # 提取数字
    match = re.search(r'(\d+(\.\d+)?)', text)
    if not match:
        return None
    value = float(match.group(1))
    
    # 分割成"X单位" + "等于Y单位"
    if "等于" in text_orig:
        parts = text_orig.split("等于", 1)
        left_part = parts[0]
        right_part = parts[1]
    elif "换成" in text_orig:
        parts = text_orig.split("换成", 1)
        left_part = parts[0]
        right_part = parts[1]
    elif "转" in text_orig:
        parts = text_orig.split("转", 1)
        left_part = parts[0]
        right_part = parts[1]
    else:
        left_part = text_orig
        right_part = text_orig
    
    # 提取两个单位
    units = []
    unit_words = ["摄氏度", "华氏度", "千克", "公里", "厘米", "毫米", "英寸", "英尺", "平方米", "平方英尺",  "千克", "公斤", "摄氏度", "华氏度", "小时", "分钟", "米", "克", "斤", "磅", "天"]
    unit_words.sort(key=len, reverse=True)
    
    # 左边找from单位
    from_unit = None
    for word in unit_words:
        if word in left_part:
            from_unit = word
            break
    
    # 右边找to单位
    to_unit = None
    for word in unit_words:
        if word in right_part:
            to_unit = word
            break
    
    if from_unit and to_unit:
        return value, from_unit, to_unit
    
    return None


def bmi_calculate(height_cm: float, weight_kg: float) -> str:
    """计算BMI"""
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "体重偏轻，建议适当增重"
    elif 18.5 <= bmi < 24:
        category = "体重正常，继续保持"
    elif 24 <= bmi < 28:
        category = "体重偏重，建议适当运动"
    else:
        category = "肥胖，建议减重，加强锻炼"
    
    return f"BMI指数是 {bmi:.1f}，{category}"


def calculator_handler(text: str) -> Optional[str]:
    """计算器和单位转换意图处理"""
    text = text.lower().strip()
    
    # BMI计算
    if "bmi" in text or ("体质指数" in text or ("身高体重" in text)):
        # 解析："身高175体重70 bmi"
        match_height = re.search(r'(身高|高)\s*(\d+(\.\d+)?)', text)
        match_weight = re.search(r'(体重|重)\s*(\d+(\.\d+)?)', text)
        if match_height and match_weight:
            height = float(match_height.group(2))
            weight = float(match_weight.group(2))
            return bmi_calculate(height, weight)
        return None
    
    # 单位转换匹配
    conversion_keywords = ["等于多少", "转换成", "转成", "等于", "换算"]
    for kw in conversion_keywords:
        if kw in text:
            parsed = parse_conversion_request(text)
            if parsed:
                value, from_u, to_u = parsed
                result = find_conversion(value, from_u, to_u)
                if result is not None:
                    return f"{value} {from_u} = {result:.4g} {to_u}"
            return "无法解析单位转换，请确认单位，格式像\"100米等于多少厘米\""
    
    # 计算器匹配: "计算"开头就是计算
    text = text.replace("计算", "").strip()
    if text.startswith("计算"):
        expr = text[2:].strip()
    elif any(op in text for op in ["加", "减", "乘", "除以", "根号", "平方"]):
        expr = text
    else:
        return None
    
    if expr:
        return calculate_expression(expr)
    
    return None