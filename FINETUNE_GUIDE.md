# 🧠 夜间微调系统 - 完整指南

## 📊 当前进度

| 指标 | 数值 |
|------|------|
| **样本总数** | 53 条 ✅ |
| **最低要求** | 50 条 ✅ |
| **目标样本** | 100-200 条（更好）⭐ |
| **模型** | Qwen3.5-2B-MLX-4bit |

---

## 📦 文件清单

| 文件 | 说明 |
|------|------|
| `conversation_to_samples.py` | 对话转样本 |
| `quick_accumulate.py` | 快速生成模拟样本（已用！） |
| `model_distillation.py` | 模型蒸馏系统 |
| `night_finetune_scheduler.py` | 夜间微调调度器 |
| `finetune_qwen35_qlora.py` | QLoRA微调脚本（参考） |
| `README_Finetune.md` | 完整文档 |

---

## 📂 数据文件位置

```bash
/Users/sxliuyu/YuanFang/finetuning_data/
├── all_samples.jsonl       # 主数据文件（53条）
├── batch_fast.jsonl        # 快速积累的50条
├── conversation_samples_*.jsonl
└── finetune.log            # 运行日志
```

---

## 🚀 下一步操作

### 方案A：继续积累样本（推荐！）⭐

```bash
# 1. 生成更多模拟样本（加速积累）
python quick_accumulate.py

# 2. 或者用真实对话积累（更高质量）
python conversation_to_samples.py

# 3. 查看样本统计
wc -l ~/yuanfang/finetuning_data/all_samples.jsonl

# 4. 随机抽取5-10条看看
head -20 ~/yuanfang/finetuning_data/all_samples.jsonl | python -m json.tool
```

**目标：积累100-200条高质量样本！**

---

### 方案B：设置夜间微调任务（晚上11点-早上7点）

```bash
# 1. 编辑 crontab
crontab -e

# 2. 添加以下内容（每10分钟检查一次）
*/10 23-6 * * * /Users/sxliuyu/YuanFang/night_finetune_scheduler.py

# 3. 保存并退出
```

**说明：**
- `*/10`: 每10分钟检查一次
- `23-6`: 晚上11点到早上7点
- `* * *`: 每天

---

### 方案C：手动微调（现在就可以开始！）

```bash
# 1. 准备数据文件（确保至少50条样本）
ls -lh ~/yuanfang/finetuning_data/all_samples.jsonl

# 2. QLoRA微调（Mac Mini上运行，只需4-6GB内存）
python -m mlx_lm.tuner.finetune \
    --model mlx-community/Qwen3.5-2B-MLX-4bit \
    --lora_rank 8 \
    --learning_rate 1e-4 \
    --batch_size 2 \
    --epochs 3 \
    --data ~/yuanfang/finetuning_data/all_samples.jsonl

# 3. 或者用更简单的命令（取决于你的环境）
mlx-lm finetune \
    --model Qwen3.5-2B \
    --lora_rank 8 \
    --data all_samples.jsonl

# 4. 预计时间（53条样本）：~10-20分钟
```

---

## 📊 预期效果

| 样本量 | 微调时间 | 预期效果 |
|--------|----------|----------|
| **50条** | ~10分钟 | 简单问题效果明显 ✅ |
| **100条** | ~20分钟 | 一般问题明显改善 ⭐⭐ |
| **200条** | ~40分钟 | 复杂问题接近大模型 ⭐⭐⭐ |

---

## 💡 关键参数

```yaml
模型：mlx-community/Qwen3.5-2B-MLX-4bit
LoRA rank: 8 (或16)
Learning rate: 1e-4
Batch size: 2-4
Epochs: 3-5
数据文件：/Users/sxliuyu/YuanFang/finetuning_data/all_samples.jsonl
```

---

## ⚠️ 注意事项

1. ✅ **样本质量 > 数量** - 高质量样本比大量低质样本更好
2. ✅ **夜间运行** - 避开白天使用高峰期
3. ✅ **电量充足** - 建议插电运行
4. ✅ **定期备份** - `cp -r finetuning_data ~/backup/finetune_$(date +%Y%m%d)`

---

## 🎯 下一步建议

1. ✅ **现在就可以开始** - `python quick_accumulate.py`
2. ⏳ **积累100条** - 达到50条即可开始微调
3. 🌙 **晚上运行** - `crontab` 设置定时任务  
4. ✨ **测试效果** - 对比微调前后的回答

---

## 📝 当前状态

- ✅ **样本积累**：53条（满足最低要求）
- ⏳ **夜间微调**：调度器已准备好，等待23:00
- ⏳ **QLoRA微调**：配置完成，等待数据文件

---

## 🎉 总结

现在就开始积累经验！用 `quick_accumulate.py` 生成更多样本，或者等待夜间自动运行。

**开始时间：2026-04-21 18:45**  
**目标：积累100条样本 + QLoRA微调（晚上11点-早上7点）**

---

**提示：2B模型更小更快！50条样本约10分钟，100条约20分钟！**
