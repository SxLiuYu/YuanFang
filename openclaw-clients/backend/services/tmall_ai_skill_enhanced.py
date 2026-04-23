import logging
logger = logging.getLogger(__name__)
"""
天猫精灵 AI 技能 - 增强版
新增功能：天气查询、日程管理、家庭设备状态查询
"""

from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# 配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-xxxxx')
FAMILY_SERVICE_URL = "http://localhost:8082"

# 系统提示词
SYSTEM_PROMPT = """
你是一个家庭 AI 助手，可以帮助用户：
1. 控制智能家居设备（灯、空调、窗帘等）
2. 管理家庭账本（记账、查询预算）
3. 管理家庭任务（创建任务、查看进度）
4. 管理购物清单（添加物品、补货提醒）
5. 查询天气和日程安排

请用简洁友好的语气回复，每次回复不超过 50 字。
"""

@app.route('/api/tmall/webhook', methods=['POST'])
def tmall_webhook():
    """天猫精灵技能 Webhook"""
    data = request.json
    
    # 解析请求
    intent = data.get('intent', {})
    intent_name = intent.get('name')
    slots = intent.get('slots', {})
    query_text = data.get('query', '')
    
    logger.info(f"[{datetime.now()}] 收到意图：{intent_name}, 查询：{query_text}")
    
    # 根据意图处理
    if intent_name == 'AIChat':
        return handle_ai_chat(query_text)
    elif intent_name == 'ControlDevice':
        return handle_device_control(slots)
    elif intent_name == 'QueryInfo':
        return handle_query(query_text)
    elif intent_name == 'AddTransaction':
        return handle_add_transaction(slots, query_text)
    elif intent_name == 'CreateTask':
        return handle_create_task(slots)
    elif intent_name == 'QueryWeather':
        return handle_query_weather(slots)
    elif intent_name == 'QuerySchedule':
        return handle_query_schedule()
    elif intent_name == 'DeviceStatus':
        return handle_device_status(slots)
    else:
        return handle_ai_chat(query_text)

# ========== 新增功能 ==========

def handle_query_weather(slots):
    """查询天气"""
    location = slots.get('location', '北京')
    
    # 调用天气 API
    weather = get_weather(location)
    
    response_text = f"{location}今天{weather['weather']}，{weather['temp']}，{weather['hint']}"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

def handle_query_schedule():
    """查询日程安排"""
    # 调用日历 API（简化实现）
    events = get_today_schedule()
    
    if not events:
        response_text = "今天没有安排"
    else:
        event_list = ', '.join(events[:3])
        response_text = f"今天有{len(events)}个安排：{event_list}"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

def handle_device_status(slots):
    """查询设备状态"""
    device_name = slots.get('device_name', '')
    room = slots.get('room', '')
    
    # 查询设备状态
    status = get_device_status(device_name, room)
    
    if status:
        response_text = f"{device_name}当前{status['state']}"
        if 'temperature' in status:
            response_text += f"，温度{status['temperature']}度"
    else:
        response_text = f"未找到设备：{device_name}"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

# ========== 原有功能 ==========

def handle_ai_chat(query_text):
    """AI 对话（调用通义千问）"""
    response = call_dashscope(query_text)
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response
                }
            ]
        }
    })

def handle_device_control(slots):
    """设备控制"""
    device_name = slots.get('device_name', '')
    action = slots.get('action', '')
    room = slots.get('room', '')
    value = slots.get('value', '')
    
    device_id = f"TM_{device_name}"
    control_device(device_id, action, value if value else None)
    
    response_text = f"好的，已{action}{device_name}"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

def handle_query(query_text):
    """查询信息"""
    prompt = f"""
    用户查询：{query_text}
    
    请判断用户想查询什么（只返回类别名称）：
    - 家庭账本（预算、支出）
    - 家庭任务（待办、进度）
    - 购物清单
    - 其他
    """
    
    category = call_dashscope(prompt, max_tokens=20)
    
    if '账本' in category or '预算' in category or '支出' in category:
        result = query_finance()
    elif '任务' in category:
        result = query_tasks()
    elif '购物' in category or '清单' in category:
        result = query_shopping()
    else:
        result = "暂时不支持这个查询"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': result
                }
            ]
        }
    })

def handle_add_transaction(slots, query_text):
    """添加交易记录"""
    amount = slots.get('amount', '')
    category = slots.get('category', '')
    
    if not amount or not category:
        prompt = f"""
        从这句话提取金额和分类：{query_text}
        返回 JSON 格式：{{"amount": 数字，"category": "分类"}}
        """
        result = call_dashscope(prompt, max_tokens=50)
    
    if amount:
        add_transaction(float(amount), category or "其他", query_text)
    
    response_text = f"好的，已记录{category or '支出'}{amount}元"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

def handle_create_task(slots):
    """创建任务"""
    task_name = slots.get('task_name', '')
    assigned_to = slots.get('assigned_to', '')
    points = slots.get('points', '10')
    
    create_task(task_name, assigned_to, int(points))
    
    response_text = f"好的，已创建任务：{task_name}，完成后获得{points}积分"
    
    return jsonify({
        'version': '1.0',
        'response': {
            'prompts': [
                {
                    'datatype': 'text',
                    'content': response_text
                }
            ]
        }
    })

# ========== 工具函数 ==========

def call_dashscope(prompt, max_tokens=500):
    """调用通义千问 API"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    headers = {
        'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'qwen-turbo',
        'input': {
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ]
        },
        'parameters': {
            'max_tokens': max_tokens,
            'temperature': 0.7
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        result = response.json()
        
        if result.get('status_code') == 200:
            return result['output']['text']
        else:
            return "抱歉，我暂时无法回答这个问题"
    except Exception as e:
        logger.error(f"调用通义千问失败：{e}")
        return "抱歉，网络开小差了"

def get_weather(location='北京'):
    """获取天气信息"""
    try:
        # 使用 wttr.in 天气 API
        response = requests.get(f"http://wttr.in/{location}?format=j1", timeout=3)
        data = response.json()
        
        current = data['current_condition'][0]
        weather = current['weatherDesc'][0]['value']
        temp = current['temp_C']
        feels_like = current['FeelsLikeC']
        humidity = current['humidity']
        wind = current['windspeedKmph']
        
        # 生成穿衣建议
        temp_int = int(temp)
        if temp_int < 10:
            hint = "注意保暖，穿厚外套"
        elif temp_int < 20:
            hint = "温度适宜，穿长袖"
        else:
            hint = "天气温暖，穿短袖即可"
        
        return {
            'weather': weather,
            'temp': f"{temp}℃（体感{feels_like}℃）",
            'humidity': f"湿度{humidity}%",
            'wind': f"风力{wind}km/h",
            'hint': hint
        }
    except Exception as e:
        logger.error(f"获取天气失败：{e}")
        return {
            'weather': '未知',
            'temp': '未知',
            'hint': '抱歉，天气数据暂时无法获取'
        }

def get_today_schedule():
    """获取今日日程"""
    # 简化实现，实际应接入日历 API
    return [
        "10:00 团队会议",
        "15:00 项目评审",
        "19:00 健身"
    ]

def get_device_status(device_name, room=''):
    """获取设备状态"""
    try:
        response = requests.get(f"{FAMILY_SERVICE_URL}/api/smarthome/devices", timeout=3)
        devices = response.json().get('devices', [])
        
        for device in devices:
            if device_name in device['device_name']:
                return {
                    'state': '开启' if device['is_online'] else '关闭',
                    'temperature': 26 if device['device_type'] == 'aircon' else None
                }
        return None
    except Exception as e:
        logger.error(f"查询设备状态失败：{e}")
        return None

# ========== 家庭服务 API 调用 ==========

def control_device(device_id, action, value=None):
    """控制设备"""
    try:
        url = f"{FAMILY_SERVICE_URL}/api/smarthome/control"
        payload = {'device_id': device_id, 'action': action}
        if value:
            payload['value'] = value
        response = requests.post(url, json=payload, timeout=3)
        return response.json()
    except Exception as e:
        logger.error(f"控制设备失败：{e}")
        return None

def add_transaction(amount, category, note=""):
    """添加交易记录"""
    try:
        url = f"{FAMILY_SERVICE_URL}/api/finance/transaction"
        payload = {
            'amount': amount,
            'type': 'expense',
            'category': category,
            'note': note
        }
        response = requests.post(url, json=payload, timeout=3)
        return response.json()
    except Exception as e:
        logger.error(f"添加交易失败：{e}")
        return None

def query_finance():
    """查询家庭账本"""
    try:
        response = requests.get(f"{FAMILY_SERVICE_URL}/api/finance/stats", timeout=3)
        data = response.json()
        stats = data.get('stats', {})
        total = sum(stats.values())
        return f"本月总支出{total}元。餐饮{stats.get('餐饮', 0)}元，交通{stats.get('交通', 0)}元。"
    except Exception as e:
        return "抱歉，账本数据暂时无法获取"

def query_tasks():
    """查询任务"""
    try:
        response = requests.get(f"{FAMILY_SERVICE_URL}/api/tasks?status=pending", timeout=3)
        data = response.json()
        tasks = data.get('tasks', [])
        if not tasks:
            return "目前没有待办任务"
        task_list = ', '.join([t['task_name'] for t in tasks[:3]])
        return f"有{len(tasks)}个待办任务：{task_list}"
    except Exception as e:
        return "抱歉，任务数据暂时无法获取"

def query_shopping():
    """查询购物清单"""
    try:
        response = requests.get(f"{FAMILY_SERVICE_URL}/api/shopping/list", timeout=3)
        data = response.json()
        items = data.get('items', [])
        if not items:
            return "购物清单是空的"
        item_list = ', '.join([i['item_name'] for i in items[:5]])
        return f"购物清单有：{item_list}"
    except Exception as e:
        return "抱歉，购物清单暂时无法获取"

def create_task(task_name, assigned_to, points=10):
    """创建任务"""
    try:
        url = f"{FAMILY_SERVICE_URL}/api/tasks"
        payload = {
            'task_name': task_name,
            'assigned_to': assigned_to,
            'points': points
        }
        response = requests.post(url, json=payload, timeout=3)
        return response.json()
    except Exception as e:
        logger.error(f"创建任务失败：{e}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, ssl_context='adhoc', debug=True)
