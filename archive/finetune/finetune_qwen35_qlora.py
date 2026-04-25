#!/usr/bin/env python3
"""
Qwen3.5-4B QLoRA微调脚本
使用MLX + LoRA，在Mac Mini上就能跑！
"""

import sys
import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TrainingConfig:
    """微调配置"""
    # 模型（改用2B）
    model_name: str = "mlx-community/Qwen3.5-2B-MLX-4bit"
    output_dir: str = "~/yuanfang/finetuned_models/qwen35-4b-lora"
    
    # LoRA配置
    lora_rank: int = 8  # LoRA秩，8/16/32都可以
    lora_alpha: int = 16  # 通常是rank的2倍
    lora_dropout: float = 0.05
    target_modules: List[str] = None  # None=自动选择
    
    # 训练参数
    learning_rate: float = 1e-4
    batch_size: int = 4
    num_epochs: int = 3
    max_steps: int = None
    warmup_steps: int = 100
    
    # 数据
    train_data_path: str = "finetuning_data.jsonl"
    val_data_path: str = None
    max_seq_len: int = 2048


def load_jsonl_data(path: str) -> List[Dict]:
    """加载jsonl格式数据"""
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def prepare_data_for_mlx(data: List[Dict], tokenizer, max_seq_len: int = 2048):
    """
    准备MLX格式数据
    
    输入格式（chat format）:
    {
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你？"}
        ]
    }
    """
    from mlx_lm.tuner import DataCollator
    
    # 转换为MLX需要的格式
    formatted_data = []
    
    for item in data:
        if "messages" in item:
            # Chat format
            formatted = tokenizer.apply_chat_template(
                item["messages"],
                tokenize=True,
                add_generation_prompt=False
            )
            formatted_data.append({"input_ids": formatted})
        elif "prompt" in item and "completion" in item:
            # Prompt-completion format
            text = item["prompt"] + item["completion"]
            formatted = tokenizer(text)
            formatted_data.append({"input_ids": formatted["input_ids"]})
    
    return formatted_data


def run_qlora_finetune(config: TrainingConfig):
    """运行QLoRA微调"""
    print("="*60)
    print("🧠 Qwen3.5-4B QLoRA 微调")
    print("="*60)
    print()
    
    # 1. 检查MLX-LoRA是否可用
    print("🔧 检查依赖...")
    try:
        import mlx.core as mx
        import mlx.nn as nn
        from mlx_lm import load, LoRALinear
        print("✅ MLX/MLX-LM 已安装")
    except ImportError:
        print("❌ 需要安装 mlx-lm")
        print("   运行: pip install mlx-lm")
        return False
    
    # 2. 加载数据
    print(f"📚 加载训练数据: {config.train_data_path}")
    if not os.path.exists(config.train_data_path):
        print(f"❌ 数据文件不存在: {config.train_data_path}")
        print("   先用 model_distillation.py 生成一些数据！")
        return False
    
    train_data = load_jsonl_data(config.train_data_path)
    print(f"   加载了 {len(train_data)} 条训练数据")
    
    # 3. 加载模型
    print(f"🤖 加载模型: {config.model_name}")
    model, tokenizer = load(config.model_name)
    print("✅ 模型加载成功")
    
    # 4. 准备数据
    print("📝 准备训练数据...")
    train_dataset = prepare_data_for_mlx(train_data, tokenizer, config.max_seq_len)
    
    # 5. 设置LoRA
    print(f"🔧 配置LoRA (rank={config.lora_rank}, alpha={config.lora_alpha})")
    
    # 这里简化，实际需要用mlx_lm的LoRA接口
    # 完整实现需要用 mlx_lm.tuner 模块
    
    print("\n" + "="*60)
    print("📋 完整的微调步骤（实际使用时）:")
    print("="*60)
    print()
    print("1. 生成/准备微调数据:")
    print("   python model_distillation.py  # 积累经验")
    print()
    print("2. 导出微调数据:")
    print("   distiller.export_finetuning_data('data.jsonl')")
    print()
    print("3. 用MLX-LoRA微调:")
    print("   完整代码见: https://github.com/ml-explore/mlx-examples/tree/main/lora")
    print()
    print("4. 合并LoRA权重（可选）:")
    print("   lora fuse --model base_model --adapter adapter_path")
    print()
    print("="*60)
    
    return True


def quick_start_guide():
    """快速开始指南"""
    print("="*60)
    print("🚀 Qwen3.5-4B 微调 - 快速开始")
    print("="*60)
    print()
    
    print("📦 环境准备:")
    print("  pip install mlx-lm")
    print()
    
    print("📝 数据格式（二选一）:")
    print()
    print("  格式1: Chat format（推荐）")
    print("  {")
    print('    "messages": [')
    print('      {"role": "user", "content": "问题..."},')
    print('      {"role": "assistant", "content": "回答..."}')
    print("    ]")
    print("  }")
    print()
    print("  格式2: Prompt-Completion")
    print("  {")
    print('    "prompt": "问题...",')
    print('    "completion": "回答..."')
    print("  }")
    print()
    
    print("🔧 推荐配置:")
    print("  LoRA rank: 8 或 16")
    print("  Batch size: 4 或 8")
    print("  Learning rate: 1e-4 或 5e-5")
    print("  Epochs: 3-5")
    print()
    
    print("💡 提示:")
    print("  - 先用 model_distillation.py 积累经验数据")
    print("  - 100-500条样本就能看到效果")
    print("  - 1000+条样本效果更好")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        quick_start_guide()
    else:
        config = TrainingConfig()
        run_qlora_finetune(config)
