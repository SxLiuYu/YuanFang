"""
贾维斯智能家居意图识别与红外指令匹配
支持：空调（奥克斯）、电视（小米）、茶吧机控制
核心功能：
1. LLM意图解析 → 提取设备、动作、参数
2. 匹配预存红外码 → 返回给客户端发射
3. 支持自然语言指令，比如 "打开空调" "调到26度" "关闭电视"
"""
import json
import re
from typing import Optional, Dict, List, Tuple

# ============ 预存红外码库 ============
# 用户需要先学习遥控器编码，存在这里
# 格式: frequency, pattern (十六进制原始数据)
INFRARED_DATABASE = {
    "aox_ac": {
        "name": "奥克斯空调",
        "frequency": 38000,
        "codes": {
            "power_on": {"pattern": "", "description": "开机"},
            "power_off": {"pattern": "", "description": "关机"},
            "temp_16": {"pattern": "", "description": "16度"},
            "temp_17": {"pattern": "", "description": "17度"},
            "temp_18": {"pattern": "", "description": "18度"},
            "temp_19": {"pattern": "", "description": "19度"},
            "temp_20": {"pattern": "", "description": "20度"},
            "temp_21": {"pattern": "", "description": "21度"},
            "temp_22": {"pattern": "", "description": "22度"},
            "temp_23": {"pattern": "", "description": "23度"},
            "temp_24": {"pattern": "", "description": "24度"},
            "temp_25": {"pattern": "", "description": "25度"},
            "temp_26": {"pattern": "", "description": "26度"},
            "temp_27": {"pattern": "", "description": "27度"},
            "temp_28": {"pattern": "", "description": "28度"},
            "temp_29": {"pattern": "", "description": "29度"},
            "temp_30": {"pattern": "", "description": "30度"},
            "mode_cool": {"pattern": "", "description": "制冷模式"},
            "mode_heat": {"pattern": "", "description": "制热模式"},
            "mode_auto": {"pattern": "", "description": "自动模式"},
            "mode_dry": {"pattern": "", "description": "除湿模式"},
            "fan_low": {"pattern": "", "description": "风速低"},
            "fan_medium": {"pattern": "", "description": "风速中"},
            "fan_high": {"pattern": "", "description": "风速高"},
            "fan_auto": {"pattern": "", "description": "风速自动"},
            "swing_on": {"pattern": "", "description": "摆风开"},
            "swing_off": {"pattern": "", "description": "摆风关"},
        }
    },
    "xiaomi_tv": {
        "name": "小米电视",
        "frequency": 38000,
        "codes": {
            "power_on": {"pattern": "", "description": "开机"},
            "power_off": {"pattern": "", "description": "关机"},
            "volume_up": {"pattern": "", "description": "音量加"},
            "volume_down": {"pattern": "", "description": "音量减"},
            "mute": {"pattern": "", "description": "静音"},
            "channel_up": {"pattern": "", "description": "频道+"},
            "channel_down": {"pattern": "", "description": "频道-"},
            "input_hdmi1": {"pattern": "", "description": "HDMI 1"},
            "input_hdmi2": {"pattern": "", "description": "HDMI 2"},
        }
    },
    "aox_teabar": {
        "name": "奥克斯茶吧机",
        "frequency": 38000,
        "codes": {
            "power_on": {"pattern": "", "description": "开机"},
            "power_off": {"pattern": "", "description": "关机"},
            "boil_water": {"pattern": "", "description": "烧水"},
            "keep_warm": {"pattern": "", "description": "保温"},
            "hot": {"pattern": "", "description": "热水出水"},
            "warm": {"pattern": "", "description": "温水出水"},
            "stop": {"pattern": "", "description": "停止出水"},
        }
    }
}


# ============ 意图解析 ============
INTENT_PATTERNS = {
    "power_on": [
        r"打开|开机|启动|开|打开空调|打开电视|开机|打开茶吧机",
        r"打开(.*)",
    ],
    "power_off": [
        r"关闭|关机|关掉|关|关空调|关电视|关闭|关茶吧机",
        r"关闭(.*)|关掉(.*)",
    ],
    "set_temp": [
        r"调到|设置|改成|温度调到|降|升|到|温度设为.*度",
        r"([0-9]+)度|温度.*?([0-9]+)",
    ],
    "temp_up": [
        r"温度调高|升一度|调高一度|升温|加一度",
    ],
    "temp_down": [
        r"温度调低|降一度|调低一度|降温|减一度",
    ],
    "mode_cool": [
        r"制冷|冷风|冷气|制冷模式|开制冷",
    ],
    "mode_heat": [
        r"制热|暖风|热气|制热模式|开制热|取暖",
    ],
    "mode_dry": [
        r"除湿|抽湿|除湿模式|干燥",
    ],
    "mode_auto": [
        r"自动|自动模式",
    ],
    "fan_low": [
        r"小风|低风速|低速|风速低",
    ],
    "fan_medium": [
        r"中风|中风速|中速",
    ],
    "fan_high": [
        r"大风|高风速|高速|强风",
    ],
    "fan_auto": [
        r"自动风速|自动风",
    ],
    "volume_up": [
        r"音量大|大声点|音量加|增大音量|调大音量",
    ],
    "volume_down": [
        r"音量小|小声点|音量减|减小音量|调小音量",
    ],
    "mute": [
        r"静音|静音|关掉声音|把声音关了",
    ],
    "boil_water": [
        r"烧水|煮水|开始烧水|烧一壶",
    ],
    "hot_water": [
        r"热水|放热水|出水热水|热水出水",
    ],
    "warm_water": [
        r"温水|放温水|出水温水|温水出水",
    ],
    "stop_water": [
        r"停水|停止出水|关水",
    ],
}

DEVICE_KEYWORDS = {
    "aox_ac": ["空调", "奥克斯", "客厅空调", "卧室空调"],
    "xiaomi_tv": ["电视", "小米电视", "客厅电视", "小米"],
    "aox_teabar": ["茶吧机", "饮水机", "奥克斯茶吧机", "烧水机"],
}


def match_device(query: str) -> Optional[str]:
    """匹配意图中的设备"""
    for device_id, keywords in DEVICE_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                return device_id
    return None


def parse_intent(query: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    解析自然语言意图
    返回: (device_id, intent_code, temperature)
    """
    device_id = match_device(query)

    # 提取温度
    temp_match = re.search(r'([0-9]{1,2})度', query)
    target_temp = int(temp_match.group(1)) if temp_match else None

    # 匹配意图
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, query):
                return device_id, intent, target_temp

    return device_id, None, target_temp


def get_infrared_code(device_id: str, intent: str) -> Optional[Dict]:
    """从数据库获取红外编码"""
    dev = INFRARED_DATABASE.get(device_id)
    if not dev:
        return None
    code = dev["codes"].get(intent)
    if not code:
        return None
    return {
        "device": dev["name"],
        "frequency": dev["frequency"],
        "pattern": code["pattern"],
        "action": code["description"],
    }


def get_temperature_code(device_id: str, temp: int) -> Optional[Dict]:
    """获取温度设置对应的红外编码"""
    if 16 <= temp <= 30:
        return get_infrared_code(device_id, f"temp_{temp}")
    return None


def smart_home_tool(query: str) -> str:
    """工具入口函数 — 自然语言控制智能家居"""
    query = query.strip()
    device_id, intent, target_temp = parse_intent(query)

    if not device_id:
        return (
            "没听清控制哪个设备呢。\n"
            "支持的设备：奥克斯空调、小米电视、奥克斯茶吧机\n"
            f"你的指令：{query}"
        )

    dev_name = INFRARED_DATABASE[device_id]["name"]

    result_text = f"[{dev_name}] "
    ir_result = None

    # 处理温度设置
    if target_temp is not None and device_id == "aox_ac":
        code = get_temperature_code(device_id, target_temp)
        if code and code["pattern"]:
            result_text += f"设置温度 {target_temp}℃"
            ir_result = code
        elif code:
            result_text += f"已识别设置温度 {target_temp}℃，但红外码尚未学习，请先学习遥控器编码存入数据库"
        else:
            result_text += f"温度 {target_temp}℃ 超出范围 (16-30℃)"

    # 处理意图
    elif intent:
        code = get_infrared_code(device_id, intent)
        if code and code["pattern"]:
            result_text += f"{code['description']}"
            ir_result = code
        elif code:
            result_text += f"已识别 {code['description']}，但红外码尚未学习，请先学习遥控器编码存入数据库"
        else:
            result_text += f"未找到 '{intent}' 对应的红外指令"

    else:
        result_text = f"已识别设备 {dev_name}，但未理解操作意图。请说清楚指令，比如：'打开空调' '调到26度' '制冷'"

    # 如果找到了红外码，输出JSON格式给管道处理
    if ir_result:
        return json.dumps({
            "success": True,
            "infrared": ir_result,
            "message": result_text
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "success": False,
            "message": result_text
        }, ensure_ascii=False)


def add_infrared_code(device_id: str, intent: str, frequency: int, pattern: str) -> bool:
    """
    添加/更新红外编码到数据库（学习遥控器时调用）
    """
    if device_id not in INFRARED_DATABASE:
        return False
    if intent not in INFRARED_DATABASE[device_id]["codes"]:
        INFRARED_DATABASE[device_id]["codes"][intent] = {
            "pattern": pattern,
            "description": intent
        }
    else:
        INFRARED_DATABASE[device_id]["codes"][intent]["pattern"] = pattern
    INFRARED_DATABASE[device_id]["frequency"] = frequency
    return True


def list_learned_codes() -> str:
    """列出已学习的红外编码（用于调试）"""
    out = []
    for dev_id, dev in INFRARED_DATABASE.items():
        learned = [name for name, code in dev["codes"].items() if code["pattern"]]
        total = len(dev["codes"])
        out.append(f"- {dev['name']}: {len(learned)}/{total} 已学习")
        if learned:
            out.append(f"  已学: {', '.join(learned)}")
    return "\n".join(out)
