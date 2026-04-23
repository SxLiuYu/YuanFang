# OpenClaw 统一配置管理 + Android 自动化

**创建时间**: 2026-02-28  
**状态**: 🚀 进行中

---

## 📋 项目概览

### 目标 1: 统一配置管理
- ✅ 定义跨平台配置文件格式
- ✅ Android 导入/导出功能
- ✅ 二维码分享配置
- 🔄 其他平台适配

### 目标 2: Android 自动化场景
- ✅ 自动化规则引擎
- ✅ 基础触发器（时间、电量、充电、GPS）
- ✅ 核心场景（早晨、低电量、睡前、通勤）
- 🔄 场景配置 UI

---

## 🗂️ 配置文件格式

### openclaw-config.json

```json
{
  "version": "1.0",
  "profile_name": "老于的配置",
  "created_at": "2026-02-28T07:40:00+08:00",
  
  "core": {
    "api_key": "sk-xxx",
    "api_provider": "dashscope",
    "model": "qwen-max",
    "websocket_url": "ws://localhost:8080",
    "context_length": 20
  },
  
  "tts": {
    "enabled": true,
    "voice": "zh-CN-XiaoxiaoNeural",
    "speed": 1.0,
    "volume": 0.8
  },
  
  "automation": {
    "enabled": true,
    "rules": [
      {
        "id": "morning_routine",
        "name": "☀️ 早晨提醒",
        "enabled": true,
        "triggers": [
          {"type": "time", "time": "07:00"},
          {"type": "power", "state": "unplugged"}
        ],
        "actions": [
          {"type": "speak", "template": "weather_commute"},
          {"type": "notify", "title": "日程提醒", "data": "calendar_today"}
        ]
      },
      {
        "id": "low_battery",
        "name": "🔋 低电量提醒",
        "enabled": true,
        "triggers": [
          {"type": "battery", "level_below": 20}
        ],
        "actions": [
          {"type": "notify", "title": "电量低", "message": "建议充电"},
          {"type": "speak", "text": "电量低于 20%，建议充电"}
        ]
      },
      {
        "id": "bedtime",
        "name": "🌙 睡前提醒",
        "enabled": true,
        "triggers": [
          {"type": "time", "time": "23:00"},
          {"type": "power", "state": "plugged"}
        ],
        "actions": [
          {"type": "speak", "template": "tomorrow_weather"},
          {"type": "notify", "title": "明日日程", "data": "calendar_tomorrow"}
        ]
      },
      {
        "id": "commute",
        "name": "🚇 通勤播报",
        "enabled": true,
        "triggers": [
          {"type": "time", "time": "08:00"},
          {"type": "location", "leaving": "home"}
        ],
        "actions": [
          {"type": "speak", "template": "news_brief"},
          {"type": "notify", "title": "路况", "data": "traffic"}
        ]
      }
    ]
  },
  
  "ui": {
    "theme": "dark",
    "language": "zh-CN",
    "font_size": "medium"
  }
}
```

---

## 📱 Android 实现计划

### 1. 配置管理模块

**文件**: `ConfigManager.java`
- 读取/写入 JSON 配置
- 导入/导出功能
- 二维码生成/识别
- 配置验证

### 2. 自动化引擎

**文件**: `AutomationEngine.java`
- 规则解析
- 触发器监听
- 动作执行
- 状态管理

### 3. 触发器实现

| 触发器 | 实现方式 |
|--------|---------|
| 时间 | WorkManager / AlarmManager |
| 电量 | BroadcastReceiver (BATTERY_CHANGED) |
| 充电 | BroadcastReceiver (ACTION_POWER_CONNECTED/DISCONNECTED) |
| GPS 围栏 | GeofencingClient |
| 网络变化 | ConnectivityManager |
| 应用使用 | UsageStatsManager |

### 4. 动作实现

| 动作 | 实现方式 |
|------|---------|
| 语音播报 | TTS |
| 通知推送 | NotificationManager |
| 打开应用 | Intent |
| 发送消息 | DashScopeService |
| 执行脚本 | 预留接口 |

---

## 🗓️ 开发计划

### Day 1 (2026-02-28) ✅
- [x] 项目规划
- [x] ConfigManager 基础实现
- [x] 配置文件导入/导出
- [x] 自动化引擎框架
- [x] ConfigActivity UI
- [x] 后台服务 + 开机自启
- [x] 默认自动化规则

### Day 2 (2026-03-01)
- [ ] 触发器测试（时间、电量、充电）
- [ ] 动作执行测试（TTS、通知）
- [ ] 2 个核心场景实测
- [ ] 二维码扫描集成

### Day 3 (2026-03-02)
- [ ] GPS 围栏触发器
- [ ] 剩余场景实现
- [ ] 规则配置 UI 优化

### Day 4 (2026-03-03)
- [ ] 全场景测试
- [ ] 文档完善
- [ ] 编译发布

---

## 📊 进度追踪

```
统一配置管理：[========..] 80%
Android 自动化：[======....] 60%
总体进度：      [=======...] 70%
```

---

## 🔗 相关文件

- `android/app/src/main/java/com/openclaw/homeassistant/ConfigManager.java` (新建)
- `android/app/src/main/java/com/openclaw/homeassistant/AutomationEngine.java` (新建)
- `android/app/src/main/java/com/openclaw/homeassistant/AutomationBootReceiver.java` (新建)
- `openclaw-config-schema.json` (配置文件 schema)
