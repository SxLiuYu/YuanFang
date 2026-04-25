#!/usr/bin/env python3
"""使用伪Qwen3.5 Plus的示例"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pseudo_qwen35 import PseudoQwen35Plus
from simple_llm_client import SimpleLLMClient

def main():
    print("="*60)
    print("🧠 伪Qwen3.5 Plus - 测试")
    print("="*60)
    print()
    
    # 1. 初始化LLM客户端（用你现有的LLMAdapter）
    print("🔧 初始化LLM客户端...")
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
    test_queries = [
        "如何优化Python代码的性能？请给出具体的方法和代码示例。",
        "什么是AI Agent？它和普通的LLM有什么区别？",
        "给我解释一下RAG（检索增强生成）的工作原理。",
    ]
    
    print("📝 选择测试问题：")
    for i, q in enumerate(test_queries):
        print(f"  {i+1}. {q[:50]}...")
    print()
    
    # 默认用第1个，或者你可以改
    query_idx = 0
    query = test_queries[query_idx]
    
    print(f"🤔 用户问题: {query}\n")
    
    # 4. 调用伪Qwen3.5 Plus
    answer = pseudo_qwen.chat(
        query=query,
        enable_rag=False,
        num_thought_steps=2  # 先用2步，快一点
    )
    
    # 5. 打印思考过程（可选，调试用）
    print("\n" + "="*60)
    print("🧐 是否查看完整思考过程？(y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            pseudo_qwen.print_thought_trace()
    except:
        print("\n跳过思考过程展示")
    
    # 6. 打印最终答案
    print("\n" + "="*60)
    print("✨ 最终答案（伪Qwen3.5 Plus风格）:")
    print("="*60)
    print(answer)
    print("="*60 + "\n")
    
    print("🎉 测试完成！")
    print()
    print("💡 提示：你可以修改 use_pseudo_qwen.py 来测试不同的问题！")


def quick_test():
    """快速测试（不展示思考过程）"""
    llm_client = SimpleLLMClient()
    pseudo_qwen = PseudoQwen35Plus(llm_client=llm_client)
    
    query = "什么是Python装饰器？请用简单的语言解释，并给一个代码示例。"
    
    print(f"🤔 快速测试: {query}")
    answer = pseudo_qwen.chat(query, enable_rag=False, num_thought_steps=2)
    
    print("\n✨ 答案:")
    print(answer)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_test()
    else:
        main()
