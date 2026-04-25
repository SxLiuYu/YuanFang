#!/usr/bin/env python3
"""
夜间微调执行脚本
- 检查样本数量
- 调用 mlx-lm LoRA 微调
- 记录日志
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 配置
MODEL_NAME = "mlx-community/Qwen3.5-2B-MLX-4bit"
DATA_PATH = Path("/Users/sxliuyu/YuanFang/finetuning_data/all_samples.jsonl")
OUTPUT_DIR = Path("/Users/sxliuyu/YuanFang/finetuned_models/qwen35-2b-lora")
LOG_FILE = Path("/Users/sxliuyu/YuanFang/finetuning_data/finetune.log")
MIN_SAMPLES = 50
LORA_RANK = 8
LEARNING_RATE = "1e-4"
BATCH_SIZE = 2
EPOCHS = 3


def log(msg: str):
    """写日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_samples() -> int:
    """统计样本数"""
    if not DATA_PATH.exists():
        return 0
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def run_finetune():
    """执行微调"""
    log("="*50)
    log("🌙 夜间微调开始")
    log("="*50)
    
    # 1. 检查样本数
    sample_count = count_samples()
    log(f"📊 样本数: {sample_count}")
    
    if sample_count < MIN_SAMPLES:
        log(f"⚠️ 样本不足 ({sample_count} < {MIN_SAMPLES})，跳过微调")
        return False
    
    # 2. 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"📂 输出目录: {OUTPUT_DIR}")
    
    # 3. 准备微调数据（转换格式）
    # mlx-lm tuner 需要 train.jsonl 格式
    train_data_path = DATA_PATH.parent / "train.jsonl"
    
    # 直接复制（已经是jsonl格式）
    import shutil
    shutil.copy2(DATA_PATH, train_data_path)
    log(f"📝 训练数据: {train_data_path} ({sample_count} 条)")
    
    # 4. 检查 mlx_lm 是否可用
    try:
        result = subprocess.run(
            ["python", "-c", "import mlx_lm; print(mlx_lm.__version__)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            log("❌ mlx_lm 未安装，尝试安装...")
            subprocess.run(
                ["pip", "install", "mlx-lm"],
                capture_output=True, text=True, timeout=120
            )
    except Exception as e:
        log(f"⚠️ mlx_lm 检查失败: {e}")
    
    # 5. 运行微调
    log("🚀 开始 QLoRA 微调...")
    log(f"   模型: {MODEL_NAME}")
    log(f"   LoRA rank: {LORA_RANK}")
    log(f"   Learning rate: {LEARNING_RATE}")
    log(f"   Batch size: {BATCH_SIZE}")
    log(f"   Epochs: {EPOCHS}")
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "mlx_lm.tuner",
        "--model", MODEL_NAME,
        "--data", str(DATA_PATH.parent),
        "--output", str(OUTPUT_DIR),
        "--lora-rank", str(LORA_RANK),
        "--learning-rate", LEARNING_RATE,
        "--batch-size", str(BATCH_SIZE),
        "--epochs", str(EPOCHS),
    ]
    
    log(f"🔧 命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=8 * 3600  # 8小时超时
        )
        
        if result.returncode == 0:
            log("✅ 微调成功！")
            log(f"输出: {OUTPUT_DIR}")
        else:
            log(f"❌ 微调失败: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        log("⚠️ 微调超时（8小时）")
        return False
    except Exception as e:
        log(f"❌ 微调异常: {e}")
        
        # 如果 mlx_lm.tuner 不可用，用备用方案
        log("📋 备用方案：手动运行以下命令")
        log(f"  python -m mlx_lm.tuner \\")
        log(f"    --model {MODEL_NAME} \\")
        log(f"    --data {DATA_PATH.parent} \\")
        log(f"    --output {OUTPUT_DIR} \\")
        log(f"    --lora-rank {LORA_RANK} \\")
        log(f"    --learning-rate {LEARNING_RATE} \\")
        log(f"    --batch-size {BATCH_SIZE} \\")
        log(f"    --epochs {EPOCHS}")
        return False
    
    log("="*50)
    log("🌙 夜间微调结束")
    log("="*50)
    return True


if __name__ == "__main__":
    run_finetune()
