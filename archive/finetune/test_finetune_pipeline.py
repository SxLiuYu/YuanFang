#!/usr/bin/env python3
"""
完整测试流程：从对话积累到微调准备
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime


def test_pipeline():
    print("="*60)
    print("🧪 完整测试流程")
    print("="*60)
    
    # Step 1: 对话转样本
    print("\n📝 Step 1: 对话转样本")
    print("-" * 60)
    
    # 模拟一段对话（实际应该从 session history 获取）
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
    ]
    
    # 提取问答对
    from conversation_to_samples import extract_qa_pairs_from_conversation, save_to_jsonl
    
    qa_pairs = extract_qa_pairs_from_conversation(sample_conversation)
    
    print(f"✅ 提取了 {len(qa_pairs)} 个高质量问答对")
    
    # Step 2: 保存到数据文件
    print("\n💾 Step 2: 保存样本")
    print("-" * 60)
    
    output_path = Path("~/yuanfang/finetuning_data").expanduser() / "test_samples.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_to_jsonl(qa_pairs, str(output_path))
    
    # Step 3: 检查样本数量
    print("\n📊 Step 3: 统计样本")
    print("-" * 60)
    
    samples_file = Path("~/yuanfang/finetuning_data").expanduser() / "all_samples.jsonl"
    
    if samples_file.exists():
        with open(samples_file, "r", encoding="utf-8") as f:
            samples = [json.loads(line) for line in f if line.strip()]
        print(f"✅ 当前样本数：{len(samples)}")
        
        if len(samples) >= 50:
            print("✅ 样本充足，可以开始微调！")
        else:
            print(f"⏳ 样本不足 ({len(samples)}条)，继续积累...")
    else:
        print("⚠️ 数据文件不存在，创建中...")
    
    # Step 4: 查看配置信息
    print("\n🔧 Step 4: QLoRA微调配置")
    print("-" * 60)
    
    model_name = "mlx-community/Qwen3.5-2B-MLX-4bit"
    lora_rank = 8
    learning_rate = "1e-4"
    batch_size = 2
    epochs = 3
    
    print(f"""模型配置:
- 模型：{model_name}
- LoRA rank: {lora_rank}
- Learning rate: {learning_rate}
- Batch size: {batch_size}
- Epochs: {epochs}

数据文件：{samples_file if samples_file.exists() else "待创建"}
""")
    
    # Step 5: 预计时间
    print("\n⏱️  Step 5: 预计时间")
    print("-" * 60)
    
    print(f"""样本量：{len(samples)}条
平均回答长度：~300 字符

QLoRA微调时间估算:
- 50条样本：~10分钟
- 100条样本：~20分钟  
- 500条样本：~1小时
""")
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_pipeline()
