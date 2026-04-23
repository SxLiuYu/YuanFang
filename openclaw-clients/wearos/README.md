# OpenClaw Wear OS 客户端 - 增强版

OpenClaw 家庭助手的 Wear OS 智能手表客户端，支持基础增强功能。

## 功能特性

- 🎤 **语音识别** - 手表端语音输入
- 💬 **AI 对话** - DashScope API 集成
- 💾 **本地历史** - 最近对话本地保存
- ⌚ **手表优化** - 圆形屏幕适配，简洁 UI
- 🔋 **低功耗** - 优化的资源使用

## 增强功能（计划中）

- [ ] TTS 语音合成（手表扬声器）
- [ ] 多轮对话上下文
- [ ] 简易历史记录查看
- [ ] 快捷回复预设

## 系统要求

- Wear OS 3.0+
- Android Studio Hedgehog+
- 真机或 Wear OS 模拟器

## 快速开始

### 1. 打开项目
```bash
cd wearos
# 在 Android Studio 中打开此目录
```

### 2. 配置
- 连接 Wear OS 设备或启动模拟器
- 运行 app

### 3. 使用
- 点击麦克风按钮
- 对着手表说话
- 查看 AI 回复

## 配置 API 密钥

在设置中配置 DashScope API Key（需要先在手机配对应用中授权）。

## 项目结构

```
wearos/
├── app/
│   ├── src/main/
│   │   ├── java/com/openclaw/wearos/
│   │   │   └── MainActivity.java
│   │   ├── res/
│   │   │   ├── layout/activity_main.xml
│   │   │   └── values/
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
└── README.md
```

## 注意事项

- 手表屏幕小，UI 设计简洁
- 语音识别需要网络连接
- 建议在安静环境下使用
- API 密钥需要通过手机配对应用配置

## 下一步计划

- [ ] 通过手机同步配置 API 密钥
- [ ] 添加离线语音命令
- [ ] 支持快捷回复
- [ ] 添加并发症 (Complications)
- [ ] TTS 语音回复

## 许可证

MIT License
