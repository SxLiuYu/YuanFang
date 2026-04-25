#!/bin/bash
# 夜间微调脚本 - crontab 调用
# 用法: 添加到 crontab: 0 23 * * * /Users/sxliuyu/YuanFang/finetune_cron.sh

# 激活环境
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 进入项目目录
cd /Users/sxliuyu/YuanFang

# 运行微调
/usr/bin/python3 run_night_finetune.py >> /Users/sxliuyu/YuanFang/finetuning_data/finetune.log 2>&1

# 完成通知
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 夜间微调完成" >> /Users/sxliuyu/YuanFang/finetuning_data/finetune.log
