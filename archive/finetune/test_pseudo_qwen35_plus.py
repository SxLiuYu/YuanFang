#!/usr/bin/env python3
"""测试伪Qwen3.5 Plus 完整版 - 带RAG"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pseudo_qwen35_plus import (
    PseudoQwen35Plus, 
    SimpleRAGRetriever
)
from simple_llm_client_omlx import SimpleLLMClient

# 示例知识库
KNOWLEDGE_BASE = {
    "Python性能优化": """
Python性能优化关键点：
1. 使用profiler找到瓶颈（cProfile, line_profiler）
2. 优化数据结构：用set代替list做成员检查
3. 使用JIT编译器：Numba, PyPy
4. 向量化运算：NumPy代替循环
5. 使用__slots__节省内存
6. 批量IO代替单条
7. 多进程/多线程
""",
    "Numba使用": """
Numba是Python的JIT编译器：
- 用@jit装饰器加速函数
- nopython模式最快
- 支持NumPy数组
- 自动并行化
""",
    "Python内存优化": """
Python内存优化：
- __slots__: 减少对象内存占用
- generator: 惰性生成，不占用全部内存
- weakref: 弱引用，避免内存泄漏
- array模块: 紧凑数组
"""
}

def main():
    print("="*60)
    print("🧠 伪Qwen3.5 Plus - 完整版 (带RAG)")
    print("="*60)
    print()
    
    # 1. 初始化oMLX客户端
    print("🔧 初始化oMLX客户端...")
    llm_client = SimpleLLMClient(api_key="omlx")
    
    # 2. 初始化RAG检索器（示例知识库）
    print("📚 初始化RAG检索器...")
    rag_retriever = SimpleRAGRetriever(KNOWLEDGE_BASE)
    print("   知识库包含:", ", ".join(KNOWLEDGE_BASE.keys()))
    
    # 3. 初始化伪Qwen3.5 Plus完整版
    print("🤖 初始化伪Qwen3.5 Plus完整版...")
    pseudo_qwen = PseudoQwen35Plus(
        llm_client=llm_client,
        rag_retriever=rag_retriever
    )
    print("✅ 初始化完成！")
    print()
    
    # 4. 测试问题（这个问题会触发RAG）
    query = "如何优化Python代码的性能？请结合profiler、Numba、内存优化等方面，给出具体的方法和代码示例。"
    
    print(f"🤔 用户问题: {query}")
    print()
    
    # 5. 调用伪Qwen3.5 Plus完整版
    # 先用2步思考 + 自我反思 + RAG
    answer = pseudo_qwen.chat(
        query=query,
        enable_rag=True,
        num_thought_steps=2,
        enable_self_critique=True
    )
    
    # 6. 打印思考过程
    print("\n" + "="*60)
    print("🧐 完整思考过程:")
    print("="*60)
    pseudo_qwen.print_thought_trace()
    
    # 7. 打印最终答案
    print("\n" + "="*60)
    print("✨ 最终答案（伪Qwen3.5 Plus 完整版）:")
    print("="*60)
    print(answer)
    print("="*60 + "\n")
    
    print("🎉 完整版测试完成！")
    print()
    print("💡 提示：你可以替换KNOWLEDGE_BASE为你自己的知识库！")


if __name__ == '__main__':
    main()
