# 天猫精灵接入大模型指南

## 🎯 目标

让天猫精灵不仅能控制设备，还能：
- 🤖 智能对话（基于通义千问）
- 📅 查询家庭账本、任务状态
- 🏠 理解自然语言控制设备
- 💡 主动提醒（天气、预算、补货）

---

## 🏗️ 架构设计

```
┌──────────────┐
│  天猫精灵    │
│  (语音识别)  │
└──────────────┘
       ↓
┌──────────────┐
│  阿里云技能  │
│  (意图识别)  │
└──────────────┘
       ↓
┌──────────────┐
│  Webhook     │
│  (你的服务器) │
└──────────────┘
       ↓
┌──────────────┐
│  通义千问    │
│  (AI 处理)    │
└──────────────┘
       ↓
┌──────────────┐
│  家庭服务    │
│  (执行操作)  │
└──────────────┘
```

---

## 📋 第一步：创建天猫精灵技能

### 1. 访问技能开发平台

https://skill.aliyun.com/

### 2. 创建新技能

1. 点击「创建技能」
2. 选择「自定义技能」
3. 填写技能信息：
   - **技能名称**: 家庭助手
   - **唤醒词**: 打开家庭助手
   - **图标**: 上传 Logo

### 3. 配置意图

#### 意图 1: 智能对话

```json
{
  "intent_name": "AIChat",
  "description": "与 AI 助手自由对话",
  "slots": [],
  "samples": [
    "今天天气怎么样",
    "我还有多少预算",
    "家里有哪些任务",
    "牛奶快喝完了吗",
    "帮我记一下花了 50 块钱吃饭"
  ]
}
```

#### 意图 2: 设备控制（自然语言）

```json
{
  "intent_name": "ControlDevice",
  "description": "语音控制智能设备",
  "slots": [
    {
      "name": "device_name",
      "type": "STRING",
      "required": true
    },
    {
      "name": "action",
      "type": "STRING",
      "required": true
    },
    {
      "name": "room",
      "type": "STRING"
    }
  ],
  "samples": [
    "打开{device_name}",
    "关闭{device_name}",
    "把{device_name}调到{value}",
    "{room}的{device_name}开了吗"
  ]
}
```

#### 意图 3: 查询类

```json
{
  "intent_name": "QueryInfo",
  "description": "查询家庭信息",
  "slots": [
    {
      "name": "query_type",
      "type": "STRING"
    }
  ],
  "samples": [
    "今天花了多少钱",
    "这个月预算还剩多少",
    "有哪些待办任务",
    "购物清单上有什么"
  ]
}
```

---

## 🔧 第二步：配置 Webhook

### 1. 准备服务器

需要公网可访问的 HTTPS 地址：

```bash
# 使用 ngrok 快速测试
ngrok http 8082

# 或使用已有服务器
# https://your-domain.com/api/tmall/webhook
```

### 2. 在技能平台配置 Webhook

- **Webhook URL**: `https://your-server.com/api/tmall/webhook`
- **请求方式**: POST
- **数据格式**: JSON

---

## 💻 第三步：实现 Webhook 服务

### 完整代码示例

```python
# file: tmall_ai_skill.py

from flask import Flask, request, jsonify
import requests
import hashlib
import time

app = Flask(__name__)

# 配置
DASHSCOPE_API_KEY = "sk-xxxxx"  # 通义千问 API Key
TMALL_SKILL_ID = "your_skill_id"

# 系统提示词
SYSTEM_PROMPT = """
你是一个家庭 AI 助手，可以帮助用户：
1. 控制智能家居设备（灯、空调、窗帘等）
2. 管理家庭账本（记账、查询预算）
3. 管理家庭任务（创建任务、查看进度）
4. 管理购物清单（添加物品、补货提醒）

请用简洁友好的语气回复，每次回复不超过 50 字。
如果用户想控制设备，请返回 JSON 格式的控制指令。
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
    
    print(f"收到意图：{intent_name}, 查询：{query_text}")
    
    # 根据意图处理
    if intent_name == 'AIChat':
        return handle_ai_chat(query_text)
    elif intent_name == 'ControlDevice':
        return handle_device_control(slots)
    elif intent_name == 'QueryInfo':
        return handle_query(query_text)
    else:
        return handle_ai_chat(query_text)

def handle_ai_chat(query_text):
    """AI 对话（调用通义千问）"""
    
    # 调用通义千问 API
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
    
    # 调用家庭服务 API 控制设备
    # device_id = find_device_by_name(device_name, room)
    # control_device(device_id, action)
    
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
    
    # 调用通义千问理解查询意图
    prompt = f"""
    用户查询：{query_text}
    
    请判断用户想查询什么：
    - 家庭账本（预算、支出）
    - 家庭任务（待办、进度）
    - 购物清单
    - 其他
    
    只返回类别名称。
    """
    
    category = call_dashscope(prompt, max_tokens=20)
    
    # 根据类别查询数据
    if '账本' in category or '预算' in category:
        result = query_finance()
    elif '任务' in category:
        result = query_tasks()
    elif '购物' in category:
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
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if result.get('status_code') == 200:
        return result['output']['text']
    else:
        return "抱歉，我暂时无法回答这个问题"

def query_finance():
    """查询家庭账本"""
    # 调用本地 API
    response = requests.get('http://localhost:8082/api/finance/stats')
    data = response.json()
    
    stats = data.get('stats', {})
    total = sum(stats.values())
    
    return f"本月总支出{total}元。餐饮{stats.get('餐饮', 0)}元，交通{stats.get('交通', 0)}元。"

def query_tasks():
    """查询任务"""
    response = requests.get('http://localhost:8082/api/tasks?status=pending')
    data = response.json()
    
    tasks = data.get('tasks', [])
    if not tasks:
        return "目前没有待办任务"
    
    task_list = ', '.join([t['task_name'] for t in tasks[:3]])
    return f"有{len(tasks)}个待办任务：{task_list}"

def query_shopping():
    """查询购物清单"""
    response = requests.get('http://localhost:8082/api/shopping/list')
    data = response.json()
    
    items = data.get('items', [])
    if not items:
        return "购物清单是空的"
    
    item_list = ', '.join([i['item_name'] for i in items[:5]])
    return f"购物清单有：{item_list}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, ssl_context='adhoc')
```

---

## 🔌 第四步：对接家庭服务

### 修改 Webhook 调用本地 API

```python
# 在 tmall_ai_skill.py 中添加

FAMILY_SERVICE_URL = "http://localhost:8082"

def control_device(device_id, action, value=None):
    """控制设备"""
    url = f"{FAMILY_SERVICE_URL}/api/smarthome/control"
    payload = {
        'device_id': device_id,
        'action': action
    }
    if value:
        payload['value'] = value
    
    response = requests.post(url, json=payload)
    return response.json()

def add_transaction(amount, category, note=""):
    """添加交易记录"""
    url = f"{FAMILY_SERVICE_URL}/api/finance/transaction"
    payload = {
        'amount': amount,
        'type': 'expense',
        'category': category,
        'note': note
    }
    response = requests.post(url, json=payload)
    return response.json()

def create_task(task_name, assigned_to, points=10):
    """创建任务"""
    url = f"{FAMILY_SERVICE_URL}/api/tasks"
    payload = {
        'task_name': task_name,
        'assigned_to': assigned_to,
        'points': points
    }
    response = requests.post(url, json=payload)
    return response.json()
```

---

## 🎤 第五步：测试语音交互

### 测试场景 1: 智能对话

**你说**: "天猫精灵，打开家庭助手，今天花了多少钱"

**天猫精灵**: "本月总支出 1580 元。餐饮 680 元，交通 320 元，购物 580 元。"

### 测试场景 2: 设备控制

**你说**: "天猫精灵，打开家庭助手，把客厅灯打开"

**天猫精灵**: "好的，已打开客厅灯"

### 测试场景 3: 语音记账

**你说**: "天猫精灵，打开家庭助手，帮我记一下花了 50 块钱吃饭"

**天猫精灵**: "好的，已记录餐饮支出 50 元"

### 测试场景 4: 任务管理

**你说**: "天猫精灵，打开家庭助手，给孩子创建一个任务，洗碗奖励 10 积分"

**天猫精灵**: "好的，已创建任务：洗碗，完成后获得 10 积分"

---

## 🚀 进阶功能

### 1. 多轮对话上下文

```python
# 使用 Redis 存储对话上下文
import redis
r = redis.Redis()

def get_context(user_id):
    return r.get(f"context:{user_id}")

def save_context(user_id, context):
    r.setex(f"context:{user_id}", 300, context)  # 5 分钟过期
```

### 2. 主动提醒

```python
# 定时任务推送提醒
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=8, minute=30)
def morning_reminder():
    # 推送天气、预算、任务提醒
    send_notification("早上好！今天气温 25℃，本月预算剩余 2000 元")

scheduler.start()
```

### 3. 个性化语音

```python
# 使用 ElevenLabs 或 Azure TTS 生成个性化语音
def generate_voice(text, voice_id="warm_female"):
    url = "https://api.elevenlabs.io/v1/text-to-speech"
    # ...
```

---

## 📊 完整流程图

```
用户语音
   ↓
天猫精灵语音识别
   ↓
意图识别（阿里云 NLP）
   ↓
Webhook → 你的服务器
   ↓
┌──────────────────────┐
│  通义千问 AI 处理      │
│  - 理解自然语言       │
│  - 提取关键信息       │
│  - 生成回复           │
└──────────────────────┘
   ↓
调用家庭服务 API
   ↓
执行操作（控制设备/记账/查任务）
   ↓
返回语音回复
   ↓
天猫精灵播放
```

---

## 🔐 安全配置

### 1. Webhook 签名验证

```python
def verify_signature(request_body, signature, timestamp):
    """验证天猫精灵请求签名"""
    secret = "your_webhook_secret"
    
    sign_str = f"{timestamp}{secret}"
    expected_sign = hashlib.sha256(sign_str.encode()).hexdigest()
    
    return signature == expected_sign
```

### 2. API Key 管理

```python
# 使用环境变量
import os
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
TMALL_APP_KEY = os.getenv('TMALL_APP_KEY')
```

---

## 📚 参考文档

- **天猫精灵技能开发**: https://skill.aliyun.com/doc
- **通义千问 API**: https://help.aliyun.com/zh/dashscope/
- **IoT 设备对接**: https://iot.taobao.com/doc

---

## 🎉 快速启动

```bash
# 1. 安装依赖
pip3 install flask requests dashscope redis

# 2. 配置环境变量
export DASHSCOPE_API_KEY="sk-xxxxx"
export TMALL_APP_KEY="your_app_key"

# 3. 启动服务
python3 tmall_ai_skill.py

# 4. 内网穿透（测试用）
ngrok http 8083

# 5. 在技能平台配置 Webhook URL
# https://xxxx.ngrok.io/api/tmall/webhook
```

---

**配置完成后，你的天猫精灵就能用 AI 大模型对话了！** 🎊

[[reply_to_current]]
