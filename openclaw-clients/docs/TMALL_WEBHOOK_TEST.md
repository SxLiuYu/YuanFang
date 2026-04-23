# 测试天猫精灵 AI 技能 Webhook

## 快速测试

### 1. 启动服务

```bash
cd /home/admin/.openclaw/workspace/openclaw-clients/backend/services
export DASHSCOPE_API_KEY="sk-xxxxx"
python3 tmall_ai_skill.py
```

### 2. 测试接口

```bash
# 测试 AI 对话
curl -X POST http://localhost:8083/api/tmall/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "AIChat"},
    "query": "今天花了多少钱"
  }'

# 测试设备控制
curl -X POST http://localhost:8083/api/tmall/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "ControlDevice"},
    "slots": {
      "device_name": "客厅灯",
      "action": "打开"
    }
  }'

# 测试语音记账
curl -X POST http://localhost:8083/api/tmall/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "AddTransaction"},
    "slots": {
      "amount": "50",
      "category": "餐饮"
    },
    "query": "花了 50 块钱吃饭"
  }'

# 测试天气查询
curl -X POST http://localhost:8083/api/tmall/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "QueryWeather"},
    "slots": {
      "location": "北京"
    }
  }'
```

### 3. 预期响应

```json
{
  "version": "1.0",
  "response": {
    "prompts": [
      {
        "datatype": "text",
        "content": "本月总支出 1580 元。餐饮 680 元，交通 320 元。"
      }
    ]
  }
}
```

---

## 完整测试脚本

```python
# test_webhook.py

import requests

BASE_URL = "http://localhost:8083/api/tmall/webhook"

def test_ai_chat():
    """测试 AI 对话"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "AIChat"},
        "query": "今天花了多少钱"
    })
    print("AI 对话测试:", response.json())

def test_device_control():
    """测试设备控制"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "ControlDevice"},
        "slots": {
            "device_name": "客厅灯",
            "action": "打开"
        }
    })
    print("设备控制测试:", response.json())

def test_weather():
    """测试天气查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "QueryWeather"},
        "slots": {"location": "北京"}
    })
    print("天气查询测试:", response.json())

if __name__ == '__main__':
    test_ai_chat()
    test_device_control()
    test_weather()
```

运行：
```bash
python3 test_webhook.py
```

---

## 天猫精灵真机测试

### 1. 配置技能

访问：https://skill.aliyun.com/

- 创建自定义技能「家庭助手」
- 配置 5 个意图
- Webhook URL: `https://你的服务器：8083/api/tmall/webhook`

### 2. 测试指令

对天猫精灵说：

- "天猫精灵，打开家庭助手，今天花了多少钱"
- "天猫精灵，打开家庭助手，把客厅灯打开"
- "天猫精灵，打开家庭助手，花了 50 块钱吃饭"
- "天猫精灵，打开家庭助手，北京今天天气怎么样"
- "天猫精灵，打开家庭助手，今天有哪些安排"

### 3. 查看日志

```bash
# 服务端日志
tail -f /path/to/tmall_ai_skill.log

# 天猫精灵技能平台日志
# 访问：https://skill.aliyun.com/console/log
```

---

## 常见问题

### Q: 通义千问 API 调用失败？
A: 检查 `DASHSCOPE_API_KEY` 是否正确，确保账户有余额。

### Q: Webhook 无法访问？
A: 确保服务器有公网 IP，或使用 ngrok 内网穿透：
```bash
ngrok http 8083 --scheme=https
```

### Q: 意图识别不准确？
A: 在技能平台添加更多训练语料，优化意图配置。

---

**测试通过后，就可以在天猫精灵技能平台提交审核了！** 🎉
