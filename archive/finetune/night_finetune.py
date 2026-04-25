#!/usr/bin/env python3
"""
夜间微调脚本
- 23:00 - 早上7:00自动运行
- 积累样本 + QLoRA微调
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_distillation import ModelDistillationSystem
from simple_llm_client_omlx import SimpleLLMClient


class NightFinetuneScheduler:
    """夜间微调调度器"""
    
    def __init__(self, model_name="mlx-community/Qwen3.5-2B-MLX-4bit"):
        self.model_name = model_name
        self.storage_path = Path("~/yuanfang/finetuning_data").expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def check_time(self):
        """检查是否在运行时间（23:00-7:00）"""
        now = datetime.now()
        hour = now.hour
        
        # 23:00 - 早上7:00
        return hour >= 23 or hour < 7
    
    def should_run(self):
        """检查是否应该运行"""
        # 检查时间
        if not self.check_time():
            print("⏰ 不在运行时间（23:00-7:00），跳过...")
            return False
        
        # 检查数据文件是否存在
        data_file = self.storage_path / "all_samples.jsonl"
        if not data_file.exists():
            print("⚠️  数据文件不存在，请先运行 sample_accumulator.py")
            return False
        
        # 检查样本数量
        with open(data_file, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        
        if count < 50:
            print(f"⚠️  样本不足 ({count}条)，至少需要50条...")
            return False
        
        print(f"✅ 所有检查通过，共 {count} 个样本")
        return True
    
    def run_finetune(self):
        """运行微调"""
        print("="*60)
        print("🌙 夜间微调开始")
        print("="*60)
        
        # 1. 统计当前样本数
        data_file = self.storage_path / "all_samples.jsonl"
        with open(data_file, "r", encoding="utf-8") as f:
            current_count = sum(1 for _ in f)
        
        print(f"📊 当前样本数：{current_count}")
        
        # 2. 初始化客户端（实际使用时用真实oMLX）
        llm_client = SimpleLLMClient(api_key="omlx")
        
        # 3. 初始化蒸馏系统
        print("🧠 初始化模型蒸馏系统...")
        distiller = ModelDistillationSystem(
            teacher_model=llm_client,
            student_model=None  # 这里用 mock，实际微调时替换为2B模型
        )
        
        # 4. 导出微调数据
        print("📝 导出微调数据...")
        output_path = self.storage_path / "finetune_data.jsonl"
        
        # 检查样本是否足够
        with open(data_file, "r", encoding="utf-8") as f:
            samples = [json.loads(line) for line in f]
        
        if len(samples) < 50:
            print(f"❌ 样本不足，需要至少50条")
            print("   当前:", len(samples), "条")
            return False
        
        # 取最新的100条样本（质量更好的）
        print(f"📚 选取最近 {min(100, len(samples))} 条样本...")
        recent_samples = samples[-min(100, len(samples)):]
        
        # 转成微调格式（chat format）
        with open(output_path, "w", encoding="utf-8") as f:
            for sample in recent_samples:
                # 确保是 chat format
                messages = [
                    {"role": "user", "content": sample["messages"][0]["content"]},
                    {"role": "assistant", "content": sample["messages"][1]["content"]}
                ]
                data = {
                    "messages": messages,
                    "metadata": sample.get("metadata", {})
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        print(f"✅ 已导出 {len(recent_samples)} 条微调数据")
        
        # 5. 实际微调（这里简化，用占位符）
        print()
        print("🔧 下一步：运行 QLoRA 微调")
        print("="*60)
        print("运行命令:")
        print(f"  mlx-lm finetune \\\n")
        print(f"    --model {self.model_name}")
        print(f"    --lora_rank 8")
        print(f"    --learning_rate 1e-4")
        print(f"    --batch_size 2")
        print(f"    --epochs 3")
        print(f"    --data {output_path}")
        print("="*60)
        
        return True
    
    def show_progress(self):
        """显示学习进度"""
        data_file = self.storage_path / "all_samples.jsonl"
        
        if not data_file.exists():
            print("⚠️  数据文件不存在")
            return
        
        with open(data_file, "r", encoding="utf-8") as f:
            samples = [json.loads(line) for line in f]
        
        print(f"📊 样本统计:")
        print(f"   总样本数：{len(samples)}")
        
        # 统计回答长度分布
        if len(samples) > 0:
            lengths = [len(s["messages"][1]["content"]) for s in samples]
            avg_len = sum(lengths) / len(samples)
            print(f"   平均回答长度：{avg_len:.0f} chars")
        
        print()


def main():
    """主函数"""
    scheduler = NightFinetuneScheduler(
        model_name="mlx-community/Qwen3.5-2B-MLX-4bit"
    )
    
    print("="*60)
    print("🌙 夜间微调调度器")
    print("="*60)
    
    # 检查是否应该运行
    if not scheduler.should_run():
        return False
    
    print()
    
    # 显示进度
    scheduler.show_progress()
    
    # 运行微调准备
    print()
    print("🚀 开始准备微调...")
    
    # TODO: 实际运行 QLoRA 微调
    # 这里用占位符，真实使用时替换为实际微调命令
    
    print()
    print("="*60)
    print("✅ 夜间微调准备完成！")
    print()
    print("💡 提示:")
    print("   - 样本需要达到50条以上")
    print("   - 实际微调用: mlx-lm finetune --data data.jsonl")
    print("="*60)


if __name__ == "__main__":
    main()
