# OpenClaw CLI - 手机数据接入命令行工具

让 OpenClaw 接入你的手机数据，提供智能服务。

## 安装

```bash
cd cli
pip install -r requirements.txt
pip install -e .
```

## 快速开始

### 1. 启动后端服务

```bash
cd ../backend
python main.py
```

### 2. 使用CLI

```bash
# 查看帮助
python cli.py --help

# 检查服务状态
python cli.py status

# AI对话
python cli.py chat "你好"

# 同步位置
python cli.py sync location --lat 39.9042 --lng 116.4074

# 同步健康数据
python cli.py sync health --steps 5000 --sleep 7.5

# 同步支付（自动记账）
python cli.py sync payment --amount 50 --merchant "美团外卖"

# 同步日程
python cli.py sync calendar --title "开会" --date 2025-03-20 --time 10:00

# 查看报告
python cli.py report daily

# 进入交互模式
python cli.py interactive
```

## 功能列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `chat` | AI对话 | `openclaw chat "你好"` |
| `sync location` | 同步位置 | `openclaw sync location --lat 39.9 --lng 116.4` |
| `sync health` | 同步健康 | `openclaw sync health --steps 5000` |
| `sync payment` | 同步支付 | `openclaw sync payment --amount 50 --merchant 美团` |
| `sync calendar` | 同步日程 | `openclaw sync calendar --title 开会 --date 2025-03-20` |
| `report` | 查看报告 | `openclaw report daily` |
| `status` | 服务状态 | `openclaw status` |
| `interactive` | 交互模式 | `openclaw interactive` |

## 数据采集器

CLI 提供了模拟的数据采集器，用于测试：

### 位置采集器
```python
from collectors import LocationCollector

collector = LocationCollector()
collector.set_place('home')  # 设置为家
location = collector.get_current_location()
```

### 健康采集器
```python
from collectors import HealthCollector

collector = HealthCollector()
health = collector.get_today_health()
trends = collector.analyze_trends()
```

### 通知采集器（支付识别）
```python
from collectors import NotificationCollector

collector = NotificationCollector()
notification = collector.simulate_payment_notification(50, "美团外卖")
```

## 配置

配置文件位于 `~/.openclaw/config.json`

```json
{
  "server": "http://localhost:8082",
  "sync_interval": 300,
  "data_types": {
    "location": true,
    "health": true,
    "calendar": true,
    "notification": false
  },
  "privacy": {
    "local_only": true,
    "encrypt": true,
    "auto_clean_days": 30
  }
}
```

## 隐私保护

- **完全本地存储**: 所有数据存储在本地
- **用户控制**: 可以开启/关闭任意数据类型的采集
- **透明可见**: 随时查看采集的数据
- **自动清理**: 可设置自动清理过期数据

## 下一步

完成CLI原型测试后，将开发Flutter App，接入真实手机数据。

---

**OpenClaw** - 你的智能家庭助手