#!/usr/bin/env python3
"""直接测试FinnA API"""

import os
import json
import urllib.request
import urllib.error
import ssl

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("FINNA_API_BASE", "https://www.finna.com.cn/v1").rstrip("/")
API_KEY = os.getenv("FINNA_API_KEY", "")
MODEL = os.getenv("DEFAULT_MODEL", "Pro/deepseek-ai/DeepSeek-V3.1-Terminus")

print(f"🔍 测试 FinnA API")
print(f"   API Base: {API_BASE}")
print(f"   Model: {MODEL}")
print()


def test_chat_completions():
    """测试 /chat/completions 端点"""
    url = f"{API_BASE}/chat/completions"
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下自己（不超过50字）"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    
    print(f"📤 发送请求到: {url}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False)[:200]}...")
    print()
    
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print("✅ 成功！")
            print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"💬 回答: {content}")
            
            return True
            
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP错误 {e.code}: {body}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_simple_endpoint():
    """测试简单的端点（不带模型前缀）"""
    # 试试直接用模型名作为路径
    url = f"{API_BASE}/{MODEL}"
    
    payload = {
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    
    print(f"\n🔍 测试端点2: {url}")
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ 成功！响应: {json.dumps(result, ensure_ascii=False)[:500]}")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


if __name__ == "__main__":
    # 先测试标准的OpenAI格式
    success = test_chat_completions()
    
    if not success:
        print("\n" + "="*60)
        print("试试其他端点格式...")
        test_simple_endpoint()
