# OpenClaw 桌面客户端 (Electron)

OpenClaw 家庭助手的跨平台桌面客户端，基于 Electron 构建。

## 功能特性

### 核心功能
- 💬 **AI 对话** - 多轮对话、上下文记忆
- 🎤 **语音输入** - Web Speech API 支持
- 🔊 **TTS 朗读** - 自动朗读 AI 回复
- 🔄 **跨设备同步** - WebSocket 实时同步

### 界面功能
- 📱 **多页面导航** - 对话、设备、任务、健康、购物、设置
- 🎨 **深色模式** - 支持明暗主题切换
- 🖥️ **系统托盘** - 最小化到托盘运行

### 系统集成
- ⌨️ **全局快捷键** - Ctrl+Shift+O 唤醒窗口
- 🔔 **系统通知** - 设备消息、同步状态通知
- 🚀 **开机自启动** - 可配置随系统启动

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+O` | 显示/隐藏窗口 |
| `Ctrl+Shift+V` | 语音输入 |
| `F2` | 语音输入 |
| `Enter` | 发送消息 |

## 安装与运行

### 1. 安装依赖
```bash
cd electron_desktop
npm install
```

### 2. 开发模式
```bash
npm start
```

### 3. 构建发布

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux

# 全平台
npm run build
```

构建产物在 `dist/` 目录。

## 使用说明

### 首次使用
1. 启动应用
2. 点击左侧「设置」
3. 配置 DashScope API Key
4. 保存设置

### 功能页面

| 页面 | 功能 |
|------|------|
| 💬 AI 对话 | 与 AI 进行多轮对话 |
| 📱 设备管理 | 查看在线设备 |
| 📋 家庭任务 | 管理家庭任务列表 |
| 🏥 健康档案 | 查看健康数据统计 |
| 🛒 购物清单 | 管理购物清单 |
| ⚙️ 设置 | 配置应用 |

## 项目结构

```
electron_desktop/
├── src/
│   ├── main.js          # Electron 主进程
│   ├── preload.js       # 预加载脚本
│   └── core/
│       └── concurrency/ # 并发处理
├── index.html           # 主界面
├── package.json         # 项目配置
└── README.md            # 说明文档
```

## 技术栈

- **框架**: Electron 28
- **UI**: 原生 HTML/CSS/JavaScript
- **语音**: Web Speech API
- **同步**: WebSocket
- **打包**: electron-builder

## 配置文件

应用配置保存在：
- Windows: `%APPDATA%/openclaw-desktop/settings.json`
- macOS: `~/Library/Application Support/openclaw-desktop/settings.json`
- Linux: `~/.config/openclaw-desktop/settings.json`

## 许可证

MIT License