#!/usr/bin/env python3
"""调试：看看最终的prompt是什么"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pseudo_qwen35 import PseudoQwen35Plus
from simple_llm_client_mock import SimpleLLMClient


# 测试直接看_generate_final_answer的prompt
def test_final_prompt():
    print("="*60)
    print("🔍 调试：最终prompt是什么？")
    print("="*60)
    
    llm_client = SimpleLLMClient()
    pseudo_qwen = PseudoQwen35Plus(llm_client=llm_client)
    
    # 模拟一些thoughts
    from pseudo_qwen35 import ThoughtStep
    pseudo_qwen.thought_history = [
        ThoughtStep(1, "analyze", "问题分析完成", 0.0),
        ThoughtStep(2, "reason", "思考1", 0.0),
        ThoughtStep(3, "reason", "思考2", 0.0),
        ThoughtStep(4, "critic", "自我批评", 0.0),
    ]
    
    # 直接调用_generate_final_answer，打印prompt
    query = "如何优化Python代码的性能？"
    rag_context = ""
    
    # 构建最终prompt（从pseudo_qwen35.py复制）
    thoughts_str = "\n".join([
        f"[步骤 {t.step_num} - {t.step_type}]\n{t.content}\n"
        for t in pseudo_qwen.thought_history
    ])
    
    final_prompt = f"""你是一个专业、友好的AI助手（模仿Qwen3.5 Plus的风格）。

请基于以下所有思考，给用户一个高质量的最终答案：

用户问题：{query}

完整思考过程：
{thoughts_str}

参考知识：
{rag_context if rag_context else '（无）'}

要求：
1. 答案要全面、准确、有深度
2. 语言自然、友好
3. 结构清晰、易读
4. 如果有代码，要规范并带注释
5. 如果是分析，要有理有据
6. 不要暴露你的"思考过程"，只给最终答案

请输出最终答案："""
    
    print("\n最终的prompt是：\n")
    print("-" * 60)
    print(final_prompt)
    print("-" * 60)
    print()
    
    # 看看mock客户端会返回什么
    print("Mock客户端的回复：")
    print("-" * 60)
    print(llm_client.chat(final_prompt))
    print("-" * 60)


if __name__ == '__main__':
    test_final_prompt()
