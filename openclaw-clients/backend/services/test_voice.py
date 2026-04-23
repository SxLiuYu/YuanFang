#!/usr/bin/env python3
"""
语音交互功能测试脚本
"""

import requests
import json
import os

BASE_URL = 'http://localhost:8082'

def check_edge_tts():
    """检查 edge-tts 安装"""
    print("=== 检查 edge-tts ===\n")
    
    import subprocess
    result = subprocess.run(['which', 'edge-tts'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ edge-tts 已安装：{result.stdout.strip()}\n")
        return True
    else:
        print("❌ edge-tts 未安装")
        print("   安装命令：pip install edge-tts\n")
        return False

def test_tts():
    """测试 TTS 语音生成"""
    print("=== 测试 TTS 语音生成 ===\n")
    
    test_texts = [
        "你好，这是语音测试",
        "第 1 步：鸡蛋打散，加少许盐搅拌均匀",
        "叮！煮鸡蛋时间到了！"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"{i}. 生成：{text}")
        response = requests.post(f'{BASE_URL}/api/voice/tts', json={
            'text': text
        })
        
        result = response.json()
        if result.get('success'):
            print(f"   ✅ 成功：{result['audio_path']}")
            print(f"   时长：{result['duration']}秒\n")
        else:
            print(f"   ❌ 失败：{result.get('error')}\n")

def test_voice_recognition():
    """测试语音指令识别"""
    print("=== 测试语音指令识别 ===\n")
    
    test_commands = [
        "下一步",
        "上一步",
        "重复这一步",
        "计时 5 分钟",
        "停止计时",
        "显示购物清单",
        "添加到清单 鸡蛋 5 个",
        "退出做菜模式"
    ]
    
    for cmd in test_commands:
        print(f"指令：{cmd}")
        response = requests.post(f'{BASE_URL}/api/voice/recognize', json={
            'text': cmd
        })
        
        result = response.json()
        if result.get('recognized'):
            print(f"   ✅ 识别：{result['command']}")
            print(f"   参数：{result.get('params', {})}\n")
        else:
            print(f"   ❌ 未识别\n")

def test_cooking_session():
    """测试做菜语音会话"""
    print("=== 测试做菜语音会话 ===\n")
    
    # 先创建一个测试菜谱
    print("1. 创建测试菜谱...")
    recipe_data = {
        'title': '语音测试菜',
        'ingredients': ['鸡蛋 2 个', '盐 适量'],
        'steps': [
            '鸡蛋打散',
            '加盐调味',
            '搅拌均匀',
            '下锅炒熟'
        ],
        'cook_time': 5,
        'difficulty': 'easy'
    }
    
    response = requests.post(f'{BASE_URL}/api/cooking/recipe/save', json=recipe_data)
    recipe_result = response.json()
    
    if not recipe_result.get('success'):
        print(f"   ❌ 菜谱创建失败：{recipe_result.get('error')}\n")
        return
    
    recipe_id = recipe_result['recipe_id']
    print(f"   ✅ 菜谱 ID: {recipe_id}\n")
    
    # 开始做菜会话
    print("2. 开始做菜语音会话...")
    response = requests.post(f'{BASE_URL}/api/voice/cooking/start', json={
        'recipe_id': recipe_id
    })
    
    result = response.json()
    if not result.get('success'):
        print(f"   ❌ 会话创建失败：{result.get('error')}\n")
        return
    
    session_id = result['session_id']
    print(f"   ✅ 会话 ID: {session_id}")
    print(f"   菜谱：{result['recipe_title']}")
    print(f"   步骤数：{result['total_steps']}")
    if result.get('intro_audio'):
        print(f"   介绍语音：{result['intro_audio']}\n")
    
    # 获取每一步的语音指导
    print("3. 获取每一步语音指导...")
    for i in range(result['total_steps']):
        response = requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/next')
        step_result = response.json()
        
        if step_result.get('success'):
            print(f"   步骤 {step_result['step']}/{step_result['total']}: {step_result['text']}")
            if step_result.get('audio_path'):
                print(f"      音频：{step_result['audio_path']}")
        else:
            print(f"   ❌ 步骤获取失败：{step_result.get('error')}")
    
    # 测试语音指令
    print("\n4. 测试语音指令...")
    voice_commands = [
        "上一步",
        "下一步",
        "计时 3 分钟",
        "退出"
    ]
    
    for cmd in voice_commands:
        print(f"   指令：{cmd}")
        response = requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/command', json={
            'text': cmd
        })
        
        result = response.json()
        print(f"      响应：{json.dumps(result, ensure_ascii=False, indent=2)}\n")
    
    # 获取会话状态
    print("5. 获取会话状态...")
    response = requests.get(f'{BASE_URL}/api/voice/cooking/{session_id}/status')
    status = response.json()
    print(f"   当前步骤：{status.get('current_step')}/{status.get('total_steps')}")
    print(f"   进度：{status.get('progress', 0) * 100:.1f}%\n")
    
    # 结束会话
    print("6. 结束会话...")
    response = requests.post(f'{BASE_URL}/api/voice/cooking/{session_id}/end')
    print(f"   结果：{response.json()}\n")

def test_timer_alert():
    """测试计时器提醒语音"""
    print("=== 测试计时器提醒语音 ===\n")
    
    response = requests.post(f'{BASE_URL}/api/voice/timer-alert', json={
        'timer_name': '煮鸡蛋'
    })
    
    result = response.json()
    if result.get('success'):
        print(f"✅ 生成成功：{result['audio_path']}")
    else:
        print(f"❌ 生成失败：{result.get('error')}")

if __name__ == '__main__':
    try:
        # 1. 检查 edge-tts
        has_edge_tts = check_edge_tts()
        
        # 2. 测试 TTS
        if has_edge_tts:
            test_tts()
        else:
            print("⚠️  跳过 TTS 测试（edge-tts 未安装）\n")
        
        # 3. 测试语音识别
        test_voice_recognition()
        
        # 4. 测试做菜会话
        test_cooking_session()
        
        # 5. 测试计时器提醒
        if has_edge_tts:
            test_timer_alert()
        
        print("\n✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到家庭助手 API（http://localhost:8082）")
        print("   请先启动服务：python3 family_services_api.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
