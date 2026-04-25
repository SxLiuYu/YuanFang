#!/usr/bin/env python3
"""
对话转微调样本
- 从当前对话中提取高质量问答对
- 转成标准微调格式
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def extract_qa_pairs_from_conversation(
    conversation: List[Dict],
    min_answer_length: int = 100,
    max_answer_length: int = 4000
) -> List[Dict]:
    """
    从对话历史中提取问答对
    
    Args:
        conversation: 对话历史，格式: [{"role": "user", "content": "..."}, ...]
        min_answer_length: 最小回答长度（过滤太短的）
        max_answer_length: 最大回答长度（过滤太长的）
    
    Returns:
        问答对列表
    """
    qa_pairs = []
    
    i = 0
    while i < len(conversation) - 1:
        msg1 = conversation[i]
        msg2 = conversation[i + 1]
        
        # 找 user -> assistant 模式
        if msg1.get("role") == "user" and msg2.get("role") == "assistant":
            question = msg1.get("content", "").strip()
            answer = msg2.get("content", "").strip()
            
            # 过滤
            if (len(question) > 5 and 
                min_answer_length <= len(answer) <= max_answer_length and
                not answer.startswith("[错误]") and
                not answer.startswith("[HTTP错误]")):
                
                qa_pairs.append({
                    "messages": [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer}
                    ],
                    "metadata": {
                        "extracted_at": datetime.now().isoformat(),
                        "question_length": len(question),
                        "answer_length": len(answer)
                    }
                })
            
            i += 2  # 跳过这对
        else:
            i += 1
    
    return qa_pairs


def save_to_jsonl(data: List[Dict], output_path: str):
    """保存为jsonl格式"""
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    print("="*60)
    print("💬 对话转微调样本")
    print("="*60)
    print()
    
    # 示例：模拟一段对话（实际应该从session获取）
    sample_conversation = [
        {"role": "user", "content": "如何优化Python代码的性能？"},
        {"role": "assistant", "content": """# Python代码性能优化指南

## 1. 使用profiler找到瓶颈
```python
import cProfile
cProfile.run('your_function()')
```

## 2. 优化数据结构
- 用`set`代替`list`做成员检查
- 用`collections.defaultdict`
- 用`itertools`避免中间列表

## 3. 使用JIT编译器
```python
from numba import jit

@jit(nopython=True)
def fast_function(x):
    return x * x
```

希望这些方法能帮到你！"""},
        
        {"role": "user", "content": "伪Qwen3.5 Plus是什么？"},
        {"role": "assistant", "content": """伪Qwen3.5 Plus是一个增强系统：
- 问题分析
- RAG知识检索
- 深度思维链推理（3-5步）
- 自我反思/批评
- 最终优化输出

用小模型+思维链，模仿大模型的效果！"""},
        
        {"role": "user", "content": "什么是知识蒸馏？"},
        {"role": "assistant", "content": """知识蒸馏就是：
1. 大模型（老师）生成高质量回答
2. 小模型（学生）学习这些回答
3. 持续积累经验
4. 小模型越来越好

就像老师教学生，慢慢学生就能自己答题了！"""},
    ]
    
    print(f"📋 示例对话包含 {len(sample_conversation)} 条消息")
    print()
    
    # 提取问答对
    print("🔍 提取问答对...")
    qa_pairs = extract_qa_pairs_from_conversation(sample_conversation)
    print(f"✅ 提取了 {len(qa_pairs)} 个高质量问答对")
    print()
    
    # 显示样本
    print("📝 样本预览:")
    print("-" * 60)
    for i, pair in enumerate(qa_pairs[:3]):
        q = pair["messages"][0]["content"][:50]
        a = pair["messages"][1]["content"][:80]
        print(f"{i+1}. Q: {q}...")
        print(f"   A: {a}...")
        print()
    print("-" * 60)
    print()
    
    # 保存
    output_path = Path("~/yuanfang/finetuning_data").expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"conversation_samples_{timestamp}.jsonl"
    
    save_to_jsonl(qa_pairs, str(output_file))
    print(f"💾 已保存到: {output_file}")
    
    # 同时追加到主数据文件
    main_data_file = output_path / "all_samples.jsonl"
    with open(main_data_file, "a", encoding="utf-8") as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    
    print(f"📚 已追加到主数据文件: {main_data_file}")
    
    # 统计
    if main_data_file.exists():
        total = sum(1 for _ in open(main_data_file, "r", encoding="utf-8"))
        print(f"📊 主数据文件累计: {total} 个样本")
    
    print()
    print("✅ 完成！")


if __name__ == "__main__":
    main()
