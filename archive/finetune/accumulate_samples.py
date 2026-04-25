#!/usr/bin/env python3
"""
从当前对话积累更多样本
- 提取高质量问答对
- 保存到微调数据文件
"""

import json
from pathlib import Path


def extract_from_session_log(session_log_path):
    """从会话日志中提取问答对"""
    qa_pairs = []
    
    with open(session_log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 简单解析：找 user -> assistant 模式
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 查找用户消息
        if "user" in line.lower():
            question = line.replace("user:", "").strip()
            
            # 找对应的回答（下一行）
            if i + 1 < len(lines):
                answer = lines[i+1].strip().replace("assistant:", "").strip()
                
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
                            "source": "session_log"
                        }
                    })
            
            i += 2
        else:
            i += 1
    
    return qa_pairs


def main():
    print("="*60)
    print("💬 从会话日志积累样本")
    print("="*60)
    
    # 示例：从最近的对话中提取样本
    # 实际使用时，可以从 session history 获取完整对话
    
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

用小模型 + 思维链，模仿大模型的效果！"""},
        
        {"role": "user", "content": "什么是知识蒸馏？"},
        {"role": "assistant", "content": """知识蒸馏就是：
1. 大模型（老师）生成高质量回答
2. 小模型（学生）学习这些回答
3. 持续积累经验
4. 小模型越来越好

就像老师教学生，慢慢学生就能自己答题了！"""},
    ]
    
    # 提取问答对
    qa_pairs = extract_from_session_log(None)  # 这里简化，直接用示例
    
    print(f"📋 共提取 {len(qa_pairs)} 个问答对")
    
    # 保存
    output_dir = Path("~/yuanfang/finetuning_data").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    samples_file = output_dir / "accumulated_samples.jsonl"
    
    # 追加到主文件
    with open(samples_file, "a", encoding="utf-8") as f:
        for pair in qa_pairs:
            # 确保是 chat format
            data = {
                "messages": [
                    {"role": "user", "content": pair["messages"][0]["content"]},
                    {"role": "assistant", "content": pair["messages"][1]["content"]}
                ]
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    print(f"💾 已追加到主数据文件：{samples_file}")
    
    # 统计总数
    main_data = output_dir / "all_samples.jsonl"
    if main_data.exists():
        with open(main_data, "r", encoding="utf-8") as f:
            total = sum(1 for _ in f)
        print(f"📊 主数据文件累计：{total}个样本")


if __name__ == "__main__":
    main()
