# OpenClaw iOS 客户端

OpenClaw 家庭助手的 iOS 原生客户端，使用 SwiftUI 构建。

## 功能特性

- 🎤 **语音识别** - 使用 Siri Speech Framework 进行语音输入
- 💬 **AI 对话** - 集成 DashScope API（通义千问）
- 🔌 **WebSocket** - 支持实时服务器通信
- 💾 **本地存储** - API 密钥和设置自动保存
- 🎨 **现代化 UI** - SwiftUI 构建，支持深色模式
- 📱 **响应式设计** - 适配 iPhone 和 iPad

## 系统要求

- iOS 15.0+
- Xcode 14.0+
- Swift 5.7+

## 快速开始

### 1. 打开项目
```bash
cd ios
open OpenClawClients.xcodeproj
```

### 2. 配置签名
- 在 Xcode 中选择项目
- 选择 Target → Signing & Capabilities
- 选择你的开发团队

### 3. 运行应用
- 选择设备或模拟器
- 点击 Run (⌘R)

### 4. 配置 API
- 首次运行后，点击右上角设置图标
- 输入 DashScope API Key
- 可选：配置 WebSocket 服务器地址

## 项目结构

```
ios/OpenClawClients/
├── OpenClawClientsApp.swift    # 应用入口
├── Models/
│   └── Message.swift           # 消息数据模型
├── ViewModels/
│   └── ChatViewModel.swift     # 视图模型（业务逻辑）
├── Views/
│   └── ContentView.swift       # 主界面视图
├── Info.plist                  # 应用配置
└── Assets.xcassets             # 资源文件
```

## 使用说明

### 语音对话
1. 点击"开始语音"按钮
2. 对着设备说话
3. 自动识别并发送到 AI
4. 查看 AI 回复

### 文字输入
1. 在输入框输入文字
2. 点击发送按钮
3. 查看 AI 回复

### 设置
- **DashScope API Key**: 阿里云 DashScope API 密钥
- **WebSocket 地址**: 可选的 WebSocket 服务器地址

## 权限说明

应用需要以下权限：
- **麦克风**：用于语音识别
- **语音识别**：将语音转换为文字

## 技术栈

- **UI 框架**: SwiftUI
- **架构模式**: MVVM
- **语音识别**: Speech Framework (SFSpeechRecognizer)
- **网络**: URLSession (WebSocket + HTTP)
- **数据存储**: UserDefaults

## 下一步计划

- [ ] 添加语音合成 (TTS)
- [ ] 支持多轮对话上下文
- [ ] 添加历史记录功能
- [ ] 支持自定义主题
- [ ] Widget 小组件支持

## 许可证

MIT License
