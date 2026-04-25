#!/usr/bin/env python3
"""
夜间微调调度器 - cron job 管理
- 每天23:00-7:00自动运行
- 积累样本 + QLoRA微调
"""

import os
import sys
from pathlib import Path
from datetime import datetime, time, timedelta


class NightFinetuneScheduler:
    """夜间微调调度器"""
    
    def __init__(self, model_name="mlx-community/Qwen3.5-2B-MLX-4bit"):
        self.model_name = model_name
        self.storage_path = Path("~/yuanfang").expanduser() / "finetuning_data"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def should_run(self):
        """检查是否应该运行（23:00-7:00）"""
        now = datetime.now()
        
        # 检查时间范围（23:00-7:00）
        if now.hour < 23 or (now.hour >= 7 and now.minute > 0):
            return False
        
        # 如果是23:00-6:59，检查是否已经运行过
        if now.hour >= 23 or (now.hour < 7):
            # 检查是否已经运行过（看时间戳）
            log_file = self.storage_path / "finetune.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    last_run = [line for line in f if "last run at" in line.lower()][0]
                try:
                    last_time = datetime.strptime(last_run.split(":")[1].strip(), "%Y-%m-%d %H:%M")
                    # 如果已经运行过，跳过
                    if last_time >= now:
                        return False
                except:
                    pass
        
        return True
    
    def run(self):
        """运行夜间微调任务"""
        print("="*60)
        print("🌙 夜间微调任务")
        print("="*60)
        
        now = datetime.now()
        last_run_line = f"last run at: {now.strftime('%Y-%m-%d %H:%M')}\n"
        
        # 记录运行时间
        log_file = self.storage_path / "finetune.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(last_run_line)
        
        print(f"⏰ 运行时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 统计样本数
        samples_file = self.storage_path / "all_samples.jsonl"
        
        print("📊 样本统计:")
        if samples_file.exists():
            with open(samples_file, "r", encoding="utf-8") as f:
                samples = [json.loads(line) for line in f if line.strip()]
            print(f"   总样本数：{len(samples)}")
            
            # 检查是否需要微调（至少50条）
            if len(samples) >= 50:
                print(f"   ✅ 样本充足 ({len(samples)}条)，准备微调...")
                
                # TODO: 实际运行微调
                print()
                print("🔧 QLoRA 微调命令:")
                print("="*60)
                print("运行以下命令（替换实际参数）:")
                print(f"  mlx-lm finetune \\\n")
                print("    --model {self.model_name}")
                print(f"    --lora_rank 8")
                print("    --learning_rate 1e-4")
                print("    --batch_size 2")
                print("    --epochs 3-5")
                print(f"    --data {samples_file}")
                print("="*60)
            else:
                print(f"   ⏳ 样本不足 ({len(samples)}条)，继续积累...")
                print("   目标：至少50条样本")
        else:
            print("   ⚠️  数据文件不存在，请先运行 sample_accumulator.py")
        
        print()
        print("="*60)


def setup_cron():
    """设置 cron job"""
    print("="*60)
    print("🕐 设置定时任务")
    print("="*60)
    
    # cron格式：minute hour day month weekday command
    
    # 每天23:00-7:00运行
    # * 0 */1 -1/6 @reboot (简化版)
    
    print()
    print("⚠️  Cron job 配置（手动添加）:")
    print()
    print("打开 crontab: crontab -e")
    print()
    print("添加以下内容:")
    print("  */10 23-6 * * * /path/to/night_finetune_cron.py")
    print()
    print("说明:")
    print("  - */10: 每10分钟")
    print("  - 23-6: 晚上11点到早上7点")
    print("  - * * *: 每天")
    print()
    
    print("="*60)


def main():
    """主函数"""
    scheduler = NightFinetuneScheduler()
    
    print("="*60)
    print("🌙 夜间微调调度器")
    print("="*60)
    
    # 检查是否应该运行
    if scheduler.should_run():
        print()
        print("✅ 时间合适，准备运行...")
    else:
        print()
        print("⏰ 时间不合适，跳过...")
    
    # 显示配置信息
    print()
    print("📋 当前配置:")
    print(f"   模型：{scheduler.model_name}")
    print(f"   数据目录：{scheduler.storage_path}")
    
    # 设置定时任务（实际使用时手动添加）
    print()
    print("💡 提示：")
    print("   - 手动添加 cron job: crontab -e")
    print("   - 或使用 watchdog 自动监控")


if __name__ == "__main__":
    main()
