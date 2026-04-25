#!/usr/bin/env python3
"""简单的LLM客户端 - 使用本地oMLX服务"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class SimpleLLMClient:
    """简单的LLM客户端封装 - 使用oMLX"""
    
    def __init__(self, model="Qwen3.5-4B-MLX-4bit", api_key=None):
        self.model = model
        self.api_base = "http://localhost:4560/v1"
        self.api_key = api_key or os.getenv("OMLX_API_KEY", "omlx")
        
        print(f"🔧 初始化oMLX客户端")
        print(f"   API: {self.api_base}")
        print(f"   模型: {self.model}")
        print(f"   API Key: {'已设置' if self.api_key else '未设置'}")
    
    def chat(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """聊天 - 使用oMLX的OpenAI兼容API"""
        
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        
        try:
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"❌ HTTP错误 {e.code}: {body}")
            return f"[HTTP错误 {e.code}] {body[:200]}"
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return f"[错误] {str(e)}"


def test_client():
    """测试客户端"""
    print("="*60)
    print("🧪 测试oMLX客户端")
    print("="*60)
    
    # 试试不用API key先
    print("\n1️⃣  尝试不使用API key...")
    client = SimpleLLMClient(api_key="")
    
    response = client.chat("你好，请简单介绍一下自己。", temperature=0.7, max_tokens=100)
    print(f"\n💬 响应: {response[:100]}...")
    
    # 如果需要API key，提示用户
    if "API key required" in response or "authentication_error" in response:
        print("\n" + "="*60)
        print("⚠️  需要API key！")
        print("请设置环境变量 OMLX_API_KEY，或者在初始化时传入 api_key 参数")
        print("或者访问 http://localhost:4560/admin 来获取/设置API key")
        print("="*60)
    
    return client


if __name__ == '__main__':
    test_client()
