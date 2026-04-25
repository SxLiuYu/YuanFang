#!/usr/bin/env python3
"""测试伪Qwen3.5 Plus - 自动查看思考过程"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pseudo_qwen35 import PseudoQwen35Plus
from simple_llm_client_mock import SimpleLLMClient

def main():
    print("="*60)
    print("🧠 伪Qwen3.5 Plus - 完整流程展示")
    print("="*60)
    print()
    
    # 1. 初始化Mock LLM客户端
    print("🔧 初始化Mock LLM客户端...")
    llm_client = SimpleLLMClient()
    
    # 2. 初始化伪Qwen3.5 Plus
    print("🤖 初始化伪Qwen3.5 Plus...")
    pseudo_qwen = PseudoQwen35Plus(
        llm_client=llm_client,
        rag_retriever=None  # 暂时不用RAG
    )
    print("✅ 初始化完成！")
    print()
    
    # 3. 测试问题
    query = "如何优化Python代码的性能？请给出具体的方法和代码示例。"
    
    print(f"🤔 用户问题: {query}")
    print()
    
    # 4. 调用伪Qwen3.5 Plus（用2步思考，快一点）
    answer = pseudo_qwen.chat(
        query=query,
        enable_rag=False,
        num_thought_steps=2
    )
    
    # 5. 打印思考过程（自动展示）
    print("\n" + "="*60)
    print("🧐 完整思考过程:")
    print("="*60)
    pseudo_qwen.print_thought_trace()
    
    # 6. 打印最终答案
    print("\n" + "="*60)
    print("✨ 最终答案（伪Qwen3.5 Plus风格）:")
    print("="*60)
    print(answer)
    print("="*60 + "\n")
    
    print("🎉 完整流程展示完成！")
    print()
    print("💡 提示：等你拿到oMLX API key后，把simple_llm_client_mock换成simple_llm_client_omlx即可！")


if __name__ == '__main__':
    main()
