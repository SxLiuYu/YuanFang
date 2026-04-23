"""
Quick Notes & Misc Tools 快速备忘工具模块
包含：
- 购物清单 (shopping list)
- 信息备忘 (info memo: 密码、WiFi、物品位置等)
- 快递追踪 (express tracking)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# 数据文件存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SHOPPING_LIST_FILE = os.path.join(DATA_DIR, "shopping_list.json")
INFO_MEMO_FILE = os.path.join(DATA_DIR, "info_memo.json")


def _ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_json(file_path: str, default: dict) -> dict:
    """加载JSON文件"""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(file_path: str, data: dict) -> bool:
    """保存JSON文件"""
    _ensure_data_dir()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


# ============ 购物清单 ============

def add_shopping_item(item: str) -> str:
    """添加购物项"""
    data = _load_json(SHOPPING_LIST_FILE, {"items": []})
    # 去重
    if item.strip() not in [i.strip() for i in data["items"]]:
        data["items"].append(item.strip())
        _save_json(SHOPPING_LIST_FILE, data)
        return f"已添加到购物清单：{item}"
    else:
        return f"{item} 已经在购物清单里了"


def remove_shopping_item(item: str) -> str:
    """移除购物项"""
    data = _load_json(SHOPPING_LIST_FILE, {"items": []})
    original_len = len(data["items"])
    data["items"] = [i for i in data["items"] if i.strip() != item.strip()]
    if len(data["items"]) < original_len:
        _save_json(SHOPPING_LIST_FILE, data)
        return f"已从购物清单移除：{item}"
    else:
        return f"购物清单里没有找到：{item}"


def clear_shopping_list() -> str:
    """清空购物清单"""
    data = {"items": []}
    _save_json(SHOPPING_LIST_FILE, data)
    return "购物清单已清空"


def list_shopping_items() -> str:
    """列出所有购物项"""
    data = _load_json(SHOPPING_LIST_FILE, {"items": []})
    items = data["items"]
    if not items:
        return "购物清单是空的"
    return "购物清单：\n" + "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])


# ============ 信息备忘（密码/物品位置等） ============

def set_memo(key: str, value: str) -> str:
    """保存信息备忘"""
    data = _load_json(INFO_MEMO_FILE, {"memos": {}})
    data["memos"][key.strip()] = value.strip()
    _save_json(INFO_MEMO_FILE, data)
    return f"已记住：{key} = {value}"


def get_memo(key: str) -> str:
    """获取信息备忘"""
    data = _load_json(INFO_MEMO_FILE, {"memos": {}})
    memos = data["memos"]
    if not memos:
        return "还没有保存任何信息"
    if key.strip() in memos:
        return f"{key}：{memos[key.strip()]}"
    # 模糊搜索
    matches = [k for k in memos if key.strip() in k]
    if matches:
        return "\n".join([f"{k}：{memos[k]}" for k in matches])
    return f"没有找到关于 '{key}' 的信息"


def delete_memo(key: str) -> str:
    """删除信息备忘"""
    data = _load_json(INFO_MEMO_FILE, {"memos": {}})
    if key.strip() in data["memos"]:
        del data["memos"][key.strip()]
        _save_json(INFO_MEMO_FILE, data)
        return f"已删除：{key}"
    return f"没有找到：{key}"


def list_all_memos() -> str:
    """列出所有备忘"""
    data = _load_json(INFO_MEMO_FILE, {"memos": {}})
    memos = data["memos"]
    if not memos:
        return "还没有保存任何信息"
    return "已保存信息：\n" + "\n".join([f"- {key}: {value}" for key, value in memos.items()])


# ============ 快递查询 ============

def express_tracking(number: str) -> str:
    """快递查询 - 调用搜索工具"""
    # 这个函数会在tools.py中封装调用_search
    if not number.strip():
        return "请提供快递单号，比如'查一下快递 7894561230'"
    # 这里只存储查询记录，实际查询由搜索工具执行
    return f"正在查询快递 {number}..."


# ============ 手机找机（发送响铃指令到Termux节点） ============

def find_my_phone() -> str:
    """
    让手机最大音量响铃+震动，帮助你找到它
    通过WebSocket发送指令到Termux手机节点
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    try:
        from services.notification_hub import get_notification_hub
        hub = get_notification_hub()
        
        # 发送command到所有节点，执行响铃震动
        command = {
            "action": "find_my_phone",
            "payload": {
                "max_volume": True,
                "ring": True,
                "vibrate": True,
                "keep_on": 10  # 持续10秒
            }
        }
        
        # 广播给所有节点
        hub.broadcast("command", command)
        
        return "已发送响铃指令到手机，仔细听铃声吧！"
    except Exception as e:
        return f"发送指令失败：{e}，请确保Termux节点已连接"


# ============ 意图匹配封装（供语音pipeline调用） ============

def quick_tools_handler(text: str) -> Optional[str]:
    """
    快速工具意图处理，匹配成功返回响应，失败返回None
    """
    text = text.lower().strip()
    
    # 购物清单匹配
    if any(w in text for w in ["买", "购物清单", "加购物", "记着买"]):
        # 提取物品 - "帮我买牛奶" -> 牛奶
        # 算法：去掉关键词，剩下的就是物品
        for kw in ["帮我买", "给我买", "记着买", "添加购物", "加购物", "购物清单添加", "买"]:
            if text.startswith(kw):
                item = text[len(kw):].strip()
                if item:
                    return add_shopping_item(item)
        if "清" in text and "购物清单" in text:
            return clear_shopping_list()
        if ("删" in text or "移除" in text) and "购物" in text:
            # 删XX
            for kw in ["删除", "移除", "去掉"]:
                if kw in text:
                    idx = text.index(kw) + len(kw)
                    item = text[idx:].strip()
                    if item:
                        return remove_shopping_item(item)
        if ("看" in text or "列" in text or "有什么" in text) and "购物" in text:
            return list_shopping_items()
    
    # 手机找机匹配
    if any(w in text for w in ["找手机", "我的手机在哪", "手机找不到了", "响铃", "我的手机呢"]):
        return find_my_phone()

    # 生日纪念日匹配（要放在备忘前面，避免"记住妈妈生日"被备忘截胡）
    from jarvis.birthday_reminder import birthday_reminder_handler
    birthday_result = birthday_reminder_handler(text)
    if birthday_result is not None:
        return birthday_result

    # 信息备忘匹配
    if ("记住" in text or "记下来" in text) and "是" in text:
        # "记住wifi密码是123456"
        try:
            idx = text.index("是")
            key = text[:idx].replace("记住", "").replace("记下来", "").replace("帮我", "").strip()
            value = text[idx+1:].strip()
            if key and value:
                return set_memo(key, value)
        except:
            pass
    # 信息备忘匹配 — 查询
    if ("是什么" in text or "在哪里" in text or "在哪" in text) or \
       ("告诉我" in text or "查询" in text or "什么是" in text):
        # "wifi密码是什么" -> "wifi密码"
        key = text.replace("是什么", "").replace("告诉我", "").replace("查询", "").replace("在哪里", "").replace("在哪", "").strip()
        if key and not "快递" in key:
            return get_memo(key)
    if ("删除" in text or "去掉" in text) and "信息" in text:
        key = text.replace("删除", "").replace("去掉", "").replace("信息", "").strip()
        if key:
            return delete_memo(key)
    if ("列出" in text or "全部" in text) and ("信息" in text or "备忘" in text):
        return list_all_memos()
    
    # 快递查询匹配
    if ("快递" in text or "物流" in text):
        # 提取单号 - 找数字串
        import re
        numbers = re.findall(r'\d{6,}', text.replace(" ", ""))
        if numbers:
            return express_tracking(numbers[0])
        else:
            return "请提供快递单号，我才能帮你查询"
    
    # 健康提醒（喝水/站立）匹配
    from jarvis.health_reminder import health_reminder_handler
    health_result = health_reminder_handler(text)
    if health_result is not None:
        return health_result
    
    # 回家欢迎报告
    from jarvis.welcome_report import welcome_home_handler
    welcome_result = welcome_home_handler(text)
    if welcome_result is not None:
        return welcome_result
    
    # 天气穿搭建议
    from jarvis.outfit_suggestion import outfit_suggestion_handler
    outfit_result = outfit_suggestion_handler(text)
    if outfit_result is not None:
        return outfit_result
    
    # 菜谱推荐
    from jarvis.recipe_recommendation import recipe_handler
    recipe_result = recipe_handler(text)
    if recipe_result is not None:
        return recipe_result
    
    return None