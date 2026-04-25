#!/usr/bin/env python3
"""
快速积累样本 - 批量生成高质量问答对
- 模拟常见问法，自动回答
- 快速积累样本
"""

import json
from pathlib import Path


def generate_samples(count: int = 50):
    """生成模拟样本（实际使用时替换为真实对话）"""
    
    samples = []
    
    # 模拟一些常见问答对
    questions_and_answers = [
        (
            "如何优化Python代码的性能？",
            """# Python代码性能优化指南

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

希望这些方法能帮到你！"""
        ),
        
        (
            "伪Qwen3.5 Plus是什么？",
            """伪Qwen3.5 Plus是一个增强系统：
- 问题分析
- RAG知识检索
- 深度思维链推理（3-5步）
- 自我反思/批评
- 最终优化输出

用小模型 + 思维链，模仿大模型的效果！"""
        ),
        
        (
            "什么是知识蒸馏？",
            """知识蒸馏就是：
1. 大模型（老师）生成高质量回答
2. 小模型（学生）学习这些回答
3. 持续积累经验
4. 小模型越来越好

就像老师教学生，慢慢学生就能自己答题了！"""
        ),
        
        (
            "什么是LoRA微调？",
            """LoRA (Low-Rank Adaptation) 是一种高效的参数高效微调方法：

- 只训练少量参数（适配器）
- 冻结原始模型权重
- 显存占用少，训练速度快

适合资源有限的场景！"""
        ),
        
        (
            "Qwen3.5-4B和9B的区别？",
            """Qwen3.5 系列：

## 4B模型
- 适合本地部署（20GB+内存）
- 速度快，响应快
- 通用能力强

## 9B模型  
- 能力更强，适合复杂任务
- 需要更多资源（30GB+内存）
- 推理速度慢，但质量高

选择建议：本地用4B，复杂任务用9B！"""
        ),
    ]
    
    for i in range(count):
        q, a = questions_and_answers[i % len(questions_and_answers)]
        
        samples.append({
            "messages": [
                {"role": "user", "content": q},
                {"role": "assistant", "content": a}
            ],
            "metadata": {
                "generated_at": f"2026-04-21 18:{i:02d}",
                "type": "simulated"
            }
        })
    
    return samples


def main():
    print("="*60)
    print("⚡ 快速积累样本")
    print("="*60)
    
    # 生成50个样本
    count = 50
    
    print(f"📝 生成 {count} 个模拟样本...")
    
    samples = generate_samples(count)
    
    print(f"✅ 生成 {len(samples)} 个样本")
    print()
    
    # 保存到文件
    output_dir = Path("~/yuanfang/finetuning_data").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    samples_file = output_dir / "batch_fast.jsonl"
    
    with open(samples_file, "w", encoding="utf-8") as f:
        for sample in samples:
            # 确保是 chat format
            data = {
                "messages": sample["messages"],
                "metadata": sample.get("metadata", {})
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    print(f"💾 已保存到：{samples_file}")
    
    # 追加到主文件
    main_data = output_dir / "all_samples.jsonl"
    
    with open(main_data, "a", encoding="utf-8") as f:
        for sample in samples:
            data = {
                "messages": sample["messages"],
                "metadata": sample.get("metadata", {})
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    # 统计总数
    with open(main_data, "r", encoding="utf-8") as f:
        total = sum(1 for _ in f)
    
    print(f"📚 主数据文件累计：{total}个样本")
    
    print()
    print("="*60)
    print(f"🎉 积累 {count} 个样本！")
    print("="*60)


if __name__ == "__main__":
    main()
