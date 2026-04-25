#!/usr/bin/env python3
"""直接测试FinnA API - 硬编码正确的模型"""

import os
import json
import urllib.request
import urllib.error
import ssl

from dotenv import load_dotenv
load_dotenv()

API_BASE = "https://www.finna.com.cn/v1"
API_KEY = os.getenv("FINNA_API_KEY", "")
MODEL = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"

print(f"🔍 测试 FinnA API")
print(f"   API Base: {API_BASE}")
print(f"   Model: {MODEL}")
print()

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

print(f"📤 发送请求...")

try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print("✅ 成功！")
        print(f"   完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"💬 回答: {content}")
        
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"❌ HTTP错误 {e.code}: {body}")
except Exception as e:
    print(f"❌ 错误: {e}")
