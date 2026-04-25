#!/usr/bin/env python3
"""测试oMLX API key"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_llm_client_omlx import SimpleLLMClient

def main():
    print("="*60)
    print("🧪 测试oMLX API")
    print("="*60)
    print()
    
    # 设置API key
    api_key = "omlx"
    print(f"🔑 使用API key: {api_key}")
    print()
    
    # 初始化oMLX客户端
    client = SimpleLLMClient(api_key=api_key)
    
    # 测试简单对话
    print("\n" + "="*60)
    print("🤔 测试问题: 你好，请简单介绍一下自己")
    print("="*60)
    
    response = client.chat("你好，请简单介绍一下自己（不超过50字）", temperature=0.7, max_tokens=100)
    
    print(f"\n💬 回答:\n{response}")
    print()
    
    if "错误" not in response and "HTTP错误" not in response:
        print("✅ oMLX API测试成功！")
    else:
        print("❌ oMLX API测试失败，请检查API key")


if __name__ == '__main__':
    main()
