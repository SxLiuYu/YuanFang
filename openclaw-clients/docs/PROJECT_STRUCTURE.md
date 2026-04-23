# OpenClaw Clients 项目结构

## 📁 目录结构

```
openclaw-clients/
├── 📱 客户端平台
│   ├── android/              # Android 原生客户端 (Java)
│   │   ├── app/
│   │   │   ├── src/main/
│   │   │   │   ├── java/com/openclaw/homeassistant/
│   │   │   │   │   ├── 核心服务层 (Services)
│   │   │   │   │   ├── UI 层 (Activities)
│   │   │   │   │   └── 工具类 (Utils)
│   │   │   │   ├── res/      # 资源文件
│   │   │   │   └── AndroidManifest.xml
│   │   │   └── build.gradle
│   │   └── build.gradle
│   │
│   ├── ios/                  # iOS 原生客户端 (Swift + SwiftUI)
│   ├── web/                  # Web 客户端 (HTML/CSS/JS)
│   ├── flutter_mobile/       # Flutter 跨平台移动端
│   ├── smart_speaker/        # 智能音箱 Python 客户端
│   ├── wearos/              # Wear OS 智能手表
│   └── electron_desktop/    # Electron 桌面客户端
│
├── 🔧 后端服务
│   └── backend/services/
│       ├── family_services_api.py    # 家庭服务 REST API
│       ├── tmall_ai_skill.py         # 天猫精灵 AI 技能 (基础版)
│       ├── tmall_ai_skill_enhanced.py # 天猫精灵 AI 技能 (增强版)
│       └── test_webhook.py           # Webhook 测试脚本
│
├── 📚 文档
│   ├── docs/
│   │   ├── FEATURE_PROPOSAL.md       # 功能设计提案
│   │   ├── TMALL_GENIE_SETUP.md      # 天猫精灵设备接入指南
│   │   ├── TMALL_AI_SKILL.md         # AI 技能开发教程
│   │   └── TMALL_WEBHOOK_TEST.md     # Webhook 测试文档
│   │
│   ├── QUICKSTART.md                 # 快速开始指南
│   ├── IMPLEMENTATION_SUMMARY.md     # 实现总结
│   └── README.md                     # 项目说明
│
├── ⚙️ 配置文件
│   ├── .gitignore                    # Git 忽略文件
│   ├── .github/
│   │   └── ISSUE_TEMPLATE/
│   │       ├── feature_request.md    # 功能需求模板
│   │       └── bug_report.md         # Bug 报告模板
│   └── requirements.txt              # Python 依赖 (待创建)
│
└── 📦 其他
    ├── aliyun-function/              # 阿里云函数计算
    ├── CHANGELOG-*.md               # 变更日志
    └── *.md                          # 各种文档
```

---

## 🎯 核心模块

### Android 服务层 (8 个核心 Service)

| 服务 | 功能 | 文件 |
|------|------|------|
| **SmartHomeService** | 智能家居统一控制 | `SmartHomeService.java` |
| **FinanceService** | 家庭账本管理 | `FinanceService.java` |
| **TaskService** | 家庭任务板 | `TaskService.java` |
| **ShoppingService** | 智能购物清单 | `ShoppingService.java` |
| **DashScopeService** | 通义千问 AI 对话 | `DashScopeService.java` |
| **DeviceDataService** | 设备数据读取 | `DeviceDataService.java` |
| **AutomationService** | 自动化引擎 | `AutomationService.java` |
| **SmartReminderService** | 智能提醒 | `SmartReminderService.java` |

### Android UI 层 (12 个 Activity)

| Activity | 功能 |
|----------|------|
| `MainActivity` | 主界面 |
| `OpenClawChatActivity` | AI 对话界面 |
| `SmartHomeActivity` | 智能家居控制 (待实现) |
| `FinanceActivity` | 家庭账本 (待实现) |
| `FamilyTasksActivity` | 任务板 (待实现) |
| `ShoppingListActivity` | 购物清单 (待实现) |
| `DeviceManagerActivity` | 设备管理 |
| `SettingsActivity` | 设置 |
| `HistoryActivity` | 历史记录 |
| `HealthRemindersActivity` | 健康提醒 |
| `AutomationRulesActivity` | 自动化规则 |
| `AutomationLogActivity` | 自动化日志 |

### 后端 API

| 服务 | 端口 | 功能 |
|------|------|------|
| **family_services_api.py** | 8082 | 家庭服务 REST API |
| **tmall_ai_skill_enhanced.py** | 8083 | 天猫精灵 AI 技能 Webhook |

---

## 📊 代码统计

| 类型 | 数量 | 行数 |
|------|------|------|
| Java Service | 8 个 | ~2500 行 |
| Java Activity | 12 个 | ~3000 行 |
| Python 后端 | 4 个 | ~1200 行 |
| UI 布局 XML | 16 个 | ~2000 行 |
| 文档 Markdown | 20+ 个 | ~5000 行 |

**总计**: ~13700 行代码

---

## 🔗 依赖关系

```
┌─────────────────────────────────────┐
│         用户设备 (7 平台)            │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│      Android Services (核心层)       │
│  SmartHome | Finance | Task | Shop  │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│       后端 API (Flask, 8082)        │
│   家庭服务 API + 数据持久化          │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│      第三方服务集成                  │
│  - 天猫精灵 IoT (tmall)             │
│  - 通义千问 AI (DashScope)          │
│  - 飞书 Webhook (通知)              │
│  - 天气 API (wttr.in)               │
└─────────────────────────────────────┘
```

---

## 🚀 开发规范

### 命名约定

- **Service 类**: `XxxService.java` (如 `SmartHomeService`)
- **Activity 类**: `XxxActivity.java` (如 `MainActivity`)
- **布局文件**: `activity_xxx.xml` (如 `activity_main.xml`)
- **后端 API**: `xxx_service.py` (如 `family_services_api.py`)

### 代码组织

```
Android:
- Service 层：纯业务逻辑，无 UI 依赖
- Activity 层：UI 展示 + 用户交互
- Utils 层：工具类

Backend:
- 每个服务独立运行
- RESTful API 设计
- 统一错误处理
```

---

## 📝 待办事项

### 高优先级
- [ ] 创建 4 个家庭服务 Activity 实现类
- [ ] 添加 `requirements.txt`
- [ ] 配置 GitHub Actions 自动构建
- [ ] 完善单元测试

### 中优先级
- [ ] 米家/涂鸦 API 对接
- [ ] 电商价格爬取
- [ ] 数据可视化图表

### 低优先级
- [ ] 云端同步
- [ ] 多语言支持
- [ ] 主题定制

---

**最后更新**: 2026-03-04  
**版本**: v1.5
