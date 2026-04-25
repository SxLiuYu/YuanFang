#!/usr/bin/env python3
"""
保存当前对话为微调样本
- 提取问答对
- 保存到数据文件
"""

import json
from pathlib import Path


def save_conversation_samples(conversation: list, output_dir: str):
    """保存对话为样本"""
    
    # 提取问答对（user -> assistant）
    qa_pairs = []
    
    i = 0
    while i < len(conversation) - 1:
        msg1 = conversation[i]
        msg2 = conversation[i + 1]
        
        # 找 user -> assistant 模式
        if msg1.get("role") == "user" and msg2.get("role") == "assistant":
            question = msg1.get("content", "").strip()
            answer = msg2.get("content", "").strip()
            
            # 过滤：回答要有一定长度，且不是错误信息
            if (len(question) > 5 and 
                len(answer) >= 100 and
                not answer.startswith("[错误]") and
                not answer.startswith("[HTTP错误]")):
                
                qa_pairs.append({
                    "messages": [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer}
                    ],
                    "metadata": {
                        "extracted_at": "2026-04-21 18:30",
                        "source": "current_conversation"
                    }
                })
            
            i += 2  # 跳过这对
        else:
            i += 1
    
    return qa_pairs


def main():
    print("="*60)
    print("💬 保存当前对话为样本")
    print("="*60)
    
    # 示例：当前对话（实际应该从 session history 获取）
    conversation = [
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

用小模型 + 思维链，模仿大模型的效果！"""},
        
        {"role": "user", "content": "什么是知识蒸馏？"},
        {"role": "assistant", "content": """知识蒸馏就是：
1. 大模型（老师）生成高质量回答
2. 小模型（学生）学习这些回答
3. 持续积累经验
4. 小模型越来越好

就像老师教学生，慢慢学生就能自己答题了！"""},
    ]
    
    print(f"📋 当前对话包含 {len(conversation)} 条消息")
    print()
    
    # 提取问答对
    print("🔍 提取高质量问答对...")
    qa_pairs = save_conversation_samples(conversation, "/Users/sxliuyu/YuanFang/finetuning_data")
    
    print(f"✅ 提取了 {len(qa_pairs)} 个高质量问答对")
    print()
    
    # 显示样本预览
    if qa_pairs:
        print("📝 样本预览:")
        for i, pair in enumerate(qa_pairs[:3]):
            q = pair["messages"][0]["content"][:50]
            a = pair["messages"][1]["content"][:80]
            print(f"{i+1}. Q: {q}...")
            print(f"   A: {a}...")
            print()
    
    # 保存
    output_dir = Path("/Users/sxliuyu/YuanFang/finetuning_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    samples_file = output_dir / "batch_1.jsonl"
    
    with open(samples_file, "w", encoding="utf-8") as f:
        for pair in qa_pairs:
            # 确保是 chat format
            data = {
                "messages": [
                    {"role": "user", "content": pair["messages"][0]["content"]},
                    {"role": "assistant", "content": pair["messages"][1]["content"]}
                ],
                "metadata": pair.get("metadata", {})
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    print(f"💾 已保存到：{samples_file}")
    
    # 统计总数（追加到主文件）
    main_data = output_dir / "all_samples.jsonl"
    
    with open(main_data, "a", encoding="utf-8") as f:
        for pair in qa_pairs:
            data = {
                "messages": [
                    {"role": "user", "content": pair["messages"][0]["content"]},
                    {"role": "assistant", "content": pair["messages"][1]["content"]}
                ]
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    print(f"📚 已追加到主数据文件：{main_data}")
    
    # 统计总数
    with open(main_data, "r", encoding="utf-8") as f:
        total = sum(1 for _ in f)
    
    print(f"📊 主数据文件累计：{total}个样本")
    
    print()
    print("="*60)
    print("✅ 完成！")


if __name__ == "__main__":
    main()
