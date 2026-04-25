#!/usr/bin/env python3
"""简单的LLM客户端 - 使用本地MLX模型"""

import sys
import os

# 确保能导入core模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class SimpleLLMClient:
    """简单的LLM客户端封装 - 使用本地MLX模型"""
    
    def __init__(self, model="mlx-community/Qwen3.5-4B-MLX-4bit"):
        self.model = model
        print(f"🔧 初始化MLX客户端，模型: {model}")
        try:
            import mlx_lm
            self.mlx_lm = mlx_lm
            print("✅ MLX加载成功！")
        except ImportError:
            print("⚠️  mlx-lm未安装，先安装...")
            os.system(f"{sys.executable} -m pip install mlx-lm")
            import mlx_lm
            self.mlx_lm = mlx_lm
            print("✅ MLX安装并加载成功！")
    
    def chat(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """聊天 - 使用本地MLX模型"""
        try:
            # 构建Qwen3.5的聊天模板
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # 使用mlx_lm.generate
            response = self.mlx_lm.generate(
                self.model,
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature,
                verbose=False
            )
            
            # mlx_lm.generate返回的是(prompt + response)，我们只需要response部分
            # 简单处理：去掉prompt部分（如果response包含prompt）
            if response.startswith(prompt):
                response = response[len(prompt):]
            
            return response.strip()
            
        except Exception as e:
            print(f"⚠️  MLX调用出错: {e}")
            import traceback
            traceback.print_exc()
            return f"[错误] {str(e)}"


def test_client():
    """测试客户端"""
    print("🔍 测试MLX SimpleLLMClient...")
    client = SimpleLLMClient()
    
    response = client.chat("你好，请简单介绍一下自己。", temperature=0.7, max_tokens=128)
    print(f"✅ 测试响应: {response[:100]}...")
    
    return client


if __name__ == '__main__':
    test_client()
