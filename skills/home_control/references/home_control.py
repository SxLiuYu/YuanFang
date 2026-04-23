# references/home_control.py
"""
Home Control HA Command Builder
根据用户指令构建 HomeAssistant 命令
"""
import re


def parse_home_command(user_text: str) -> list[dict]:
    """
    从用户文本解析 HA 命令
    返回： [{"entity_id": "...", "action": "..."}, ...]
    """
    commands = []

    # 场景映射
    scene_map = {
        "晚安": ("scene.good_night", "activate_scene"),
        "睡觉": ("scene.good_night", "activate_scene"),
        "早安": ("scene.good_morning", "activate_scene"),
        "起床": ("scene.good_morning", "activate_scene"),
        "离家": ("scene.leaving_home", "activate_scene"),
        "出门": ("scene.leaving_home", "activate_scene"),
        "回家": ("scene.coming_home", "activate_scene"),
        "到家": ("scene.coming_home", "activate_scene"),
    }

    for keyword, (entity_id, action) in scene_map.items():
        if keyword in user_text:
            commands.append({"entity_id": entity_id, "action": action})
            return commands  # 场景命令优先

    # 设备命令
    light_devices = ["灯", "灯泡", "台灯", "客厅灯", "卧室灯", "厨房灯"]
    switch_devices = ["开关", "插座", "电器"]
    climate_devices = ["空调", "暖", "冷气"]
    other_devices = ["窗帘", "门锁", "热水器", "加湿器"]

    if any(d in user_text for d in light_devices):
        action = "turn_on" if "开" in user_text else "turn_off"
        entity_id = _extract_device_id(user_text, light_devices)
        if entity_id:
            commands.append({"entity_id": entity_id, "action": action})

    if any(d in user_text for d in climate_devices):
        action = "turn_on" if "开" in user_text else "turn_off"
        commands.append({"entity_id": "climate.home", "action": action})

    if "全屋" in user_text or "所有" in user_text:
        commands.append({"entity_id": "scene.all_off", "action": "activate_scene"})

    return commands


def _extract_device_id(text: str, device_list: list[str]) -> str:
    """从文本中提取设备 ID"""
    # 简化版：按关键词匹配
    room_map = {
        "客厅": "living_room",
        "卧室": "bedroom",
        "厨房": "kitchen",
        "书房": "study",
        "卫生间": "bathroom",
    }
    for room, room_id in room_map.items():
        if room in text:
            return f"light.{room_id}"

    # 默认客厅
    return "light.living_room"
