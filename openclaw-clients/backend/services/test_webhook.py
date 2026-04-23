"""
天猫精灵 AI 技能 Webhook 测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8083/api/tmall/webhook"

def print_result(name, response):
    """打印测试结果"""
    print(f"\n{'='*50}")
    print(f"测试：{name}")
    print(f"{'='*50}")
    if response.status_code == 200:
        data = response.json()
        content = data.get('response', {}).get('prompts', [{}])[0].get('content', '')
        print(f"✅ 成功")
        print(f"回复：{content}")
    else:
        print(f"❌ 失败 - 状态码：{response.status_code}")
        print(f"响应：{response.text}")

def test_ai_chat():
    """测试 AI 对话"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "AIChat"},
        "query": "今天花了多少钱"
    }, timeout=5)
    print_result("AI 对话 - 查询账本", response)

def test_device_control():
    """测试设备控制"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "ControlDevice"},
        "slots": {
            "device_name": "客厅灯",
            "action": "打开"
        }
    }, timeout=5)
    print_result("设备控制 - 打开客厅灯", response)

def test_add_transaction():
    """测试语音记账"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "AddTransaction"},
        "slots": {
            "amount": "50",
            "category": "餐饮"
        },
        "query": "花了 50 块钱吃饭"
    }, timeout=5)
    print_result("语音记账 - 餐饮支出", response)

def test_create_task():
    """测试创建任务"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "CreateTask"},
        "slots": {
            "task_name": "洗碗",
            "assigned_to": "孩子",
            "points": "10"
        }
    }, timeout=5)
    print_result("创建任务 - 洗碗", response)

def test_query_weather():
    """测试天气查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "QueryWeather"},
        "slots": {
            "location": "北京"
        }
    }, timeout=5)
    print_result("天气查询 - 北京", response)

def test_query_schedule():
    """测试日程查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "QuerySchedule"}
    }, timeout=5)
    print_result("日程查询 - 今天", response)

def test_device_status():
    """测试设备状态查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "DeviceStatus"},
        "slots": {
            "device_name": "空调",
            "room": "客厅"
        }
    }, timeout=5)
    print_result("设备状态 - 客厅空调", response)

def test_query_tasks():
    """测试任务查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "QueryInfo"},
        "query": "有哪些待办任务"
    }, timeout=5)
    print_result("任务查询 - 待办列表", response)

def test_query_shopping():
    """测试购物清单查询"""
    response = requests.post(BASE_URL, json={
        "intent": {"name": "QueryInfo"},
        "query": "购物清单上有什么"
    }, timeout=5)
    print_result("购物清单查询", response)

if __name__ == '__main__':
    print("\n🚀 开始测试天猫精灵 AI 技能 Webhook\n")
    
    try:
        # 基础功能测试
        test_ai_chat()
        test_device_control()
        test_add_transaction()
        test_create_task()
        
        # 新增功能测试
        test_query_weather()
        test_query_schedule()
        test_device_status()
        
        # 查询功能测试
        test_query_tasks()
        test_query_shopping()
        
        print("\n" + "="*50)
        print("✅ 所有测试完成！")
        print("="*50 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到 Webhook 服务")
        print("请确保已启动服务：python3 tmall_ai_skill.py\n")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}\n")
