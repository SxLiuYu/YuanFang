"""
贾维斯场景模式 — 一句话触发多个设备操作
支持：晚安模式、离家模式、观影模式、会客模式等
"""
import json
from typing import Dict, List, Optional

# 场景定义数据库
# 每个场景包含多个红外指令
SCENE_DATABASE = {
    "good_night": {
        "name": "晚安模式",
        "description": "睡觉前 — 关灯、开空调、关电视",
        "commands": [
            {"device": "light_living_room", "action": "power_off"},
            {"device": "light_bedroom", "action": "power_off"},
            {"device": "xiaomi_tv", "action": "power_off"},
            {"device": "aox_ac", "action": "temp_26"},
        ],
    },
    "leave_home": {
        "name": "离家模式",
        "description": "出门 — 关闭所有电器、空调、灯",
        "commands": [
            {"device": "xiaomi_tv", "action": "power_off"},
            {"device": "aox_ac", "action": "power_off"},
            {"device": "aox_teabar", "action": "power_off"},
            # 所有灯关闭...
        ],
    },
    "watch_movie": {
        "name": "观影模式",
        "description": "看电影 — 开电视、调暗灯光",
        "commands": [
            {"device": "xiaomi_tv", "action": "power_on"},
            {"device": "light_living_room", "action": "dim"},
        ],
    },
    "meet_guest": {
        "name": "会客模式",
        "description": "客人来了 — 开所有灯、打开空调",
        "commands": [
            {"device": "light_living_room", "action": "power_on"},
            {"device": "light_bedroom", "action": "power_on"},
            {"device": "aox_ac", "action": "power_on"},
        ],
    },
    "work": {
        "name": "工作模式",
        "description": "开始工作 — 开台灯、空调调至舒适温度",
        "commands": [
            {"device": "light_desk", "action": "power_on"},
            {"device": "aox_ac", "action": "temp_25"},
        ],
    },
    "morning": {
        "name": "早安模式",
        "description": "起床 — 开窗帘灯、开茶吧机烧水",
        "commands": [
            {"device": "light_curtain", "action": "power_on"},
            {"device": "aox_teabar", "action": "boil_water"},
        ],
    },
}

# 关键词匹配
SCENE_KEYWORDS = {
    "good_night": ["晚安", "睡觉", "晚安模式", "我要睡觉了", "准备睡觉"],
    "leave_home": ["离家", "出门", "我走了", "离家模式", "出去一下"],
    "watch_movie": ["观影", "看电影", "电影模式", "观影模式", "打开电视看电影"],
    "meet_guest": ["会客", "客人来了", "开门", "会客模式", "朋友来了"],
    "work": ["工作", "上班", "开始工作", "工作模式"],
    "morning": ["早安", "早上好", "起床", "早安模式", "起床了"],
}


def match_scene(query: str) -> Optional[str]:
    """匹配场景意图"""
    for scene_id, keywords in SCENE_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                return scene_id
    return None


def get_scene_commands(scene_id: str) -> Optional[List[Dict]]:
    """获取场景的所有指令"""
    scene = SCENE_DATABASE.get(scene_id)
    if not scene:
        return None
    return scene["commands"]


def get_scene_info(scene_id: str) -> Optional[Dict]:
    """获取场景信息"""
    return SCENE_DATABASE.get(scene_id)


def list_scenes() -> str:
    """列出所有已定义场景"""
    out = []
    for scene_id, scene in SCENE_DATABASE.items():
        out.append(f"- {scene['name']}: {scene['description']}")
    return "\n".join(out)


def execute_scene(scene_id: str) -> Dict:
    """
    执行场景 — 收集所有需要发送的红外指令
    返回给上层处理发送
    """
    info = get_scene_info(scene_id)
    commands = get_scene_commands(scene_id)
    if not commands:
        return {
            "success": False,
            "message": f"场景 {scene_id} 未定义"
        }
    
    # 收集所有红外指令
    from jarvis.smart_home_intent import INFRARED_DATABASE, get_infrared_code
    infrared_list = []
    missing = []
    
    for cmd in commands:
        device_id = cmd["device"]
        action = cmd["action"]
        code = get_infrared_code(device_id, action)
        if code and code["pattern"]:
            infrared_list.append(code)
        else:
            if device_id in INFRARED_DATABASE:
                dev_name = INFRARED_DATABASE[device_id]["name"]
                missing.append(f"{dev_name} - {action}")
            else:
                missing.append(f"{device_id} - {action}")
    
    scene_name = info["name"] if info else scene_id
    result_msg = f"执行【{scene_name}】: "
    
    if not infrared_list and not missing:
        result_msg += "没有要执行的指令"
    elif infrared_list and not missing:
        result_msg += f"所有 {len(infrared_list)} 个指令已就绪"
    elif missing and not infrared_list:
        result_msg += f"所有 {len(missing)} 个指令未学习红外码"
    else:
        result_msg += f"{len(infrared_list)} 就绪，{len(missing)} 未学习"
    
    return {
        "success": len(infrared_list) > 0 or not missing,
        "message": result_msg,
        "scene_name": scene_name,
        "infrared_list": infrared_list,
        "missing": missing
    }
