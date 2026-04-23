# 🎤 语音/视频交互架构设计

**版本**: v1.0  
**设计日期**: 2026-03-15  
**目标**: 统一语音/视频输入输出，支持多平台灵活配置

---

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户配置层 (config.yaml)                     │
│  - 启用/禁用功能                                                 │
│  - API Key 配置                                                  │
│  - 平台选择                                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   统一接口层 (Unified API)                       │
│  - /api/v1/voice/input    - 语音输入处理                         │
│  - /api/v1/voice/output   - 语音输出 (TTS)                       │
│  - /api/v1/video/input    - 视频输入处理                         │
│  - /api/v1/agent/chat     - AI 对话                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     能力适配层 (Adapters)                        │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  语音识别   │   TTS 合成   │  视频理解   │    AI 对话            │
│  (STT)      │             │  (Vision)   │    (LLM)              │
├─────────────┼─────────────┼─────────────┼───────────────────────┤
│ • 阿里云    │ • 阿里云    │ • 阿里云    │ • 阿里云 DashScope    │
│ • 百度      │ • 百度      │ • Google    │ • OpenAI              │
│ • Google    │ • Google    │ • Azure     │ • Anthropic           │
│ • Azure     │ • Azure     │             │ • 本地模型            │
│ • 本地      │ • 本地      │             │                       │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     客户端 SDK (Client SDK)                      │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Android  │   iOS    │   Web    │ Windows  │  macOS   │  Watch   │
│  Java    │  Swift   │   JS     │   C#     │  Swift   │  WatchOS │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## ⚙️ 配置文件设计

### `config.yaml` - 主配置文件

```yaml
# ==================== 全局开关 ====================
enabled: true
debug: false
log_level: INFO

# ==================== 语音识别 (STT) ====================
speech_to_text:
  enabled: true
  provider: aliyun  # aliyun | baidu | google | azure | local
  language: zh-CN
  sample_rate: 16000
  
  # 阿里云配置
  aliyun:
    api_key: "${DASHSCOPE_API_KEY}"  # 支持环境变量
    model: paraformer-realtime
    
  # 百度配置
  baidu:
    app_id: ""
    api_key: ""
    secret_key: ""
    
  # Google 配置
  google:
    api_key: ""
    model: latest_long
    
  # 本地配置 (Vosk)
  local:
    model_path: "./models/vosk-model-small-cn"

# ==================== 语音合成 (TTS) ====================
text_to_speech:
  enabled: true
  provider: aliyun  # aliyun | baidu | google | azure | elevenlabs | local
  voice: "longxiaochun"  # 音色
  speed: 1.0
  volume: 50
  
  aliyun:
    api_key: "${DASHSCOPE_API_KEY}"
    model: sambert-zhina-v1
    
  elevenlabs:
    api_key: ""
    voice_id: ""
    
  local:
    engine: "espeak"  # espeak | festival | piper

# ==================== 视频理解 (Vision) ====================
video_understanding:
  enabled: false
  provider: aliyun  # aliyun | google | azure | ollama
  max_duration: 60  # 秒
  frame_rate: 1
  
  aliyun:
    api_key: "${DASHSCOPE_API_KEY}"
    model: qwen-vl-max
    
  google:
    api_key: ""
    model: gemini-pro-vision
    
  ollama:
    base_url: "http://localhost:11434"
    model: "llava"

# ==================== AI 对话 (LLM) ====================
ai_chat:
  enabled: true
  provider: aliyun  # aliyun | openai | anthropic | ollama
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 2048
  
  aliyun:
    api_key: "${DASHSCOPE_API_KEY}"
    
  openai:
    api_key: ""
    base_url: "https://api.openai.com/v1"
    
  anthropic:
    api_key: ""
    
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen2.5:7b"

# ==================== 平台特定配置 ====================
platforms:
  android:
    enabled: true
    use_native_stt: false  # 使用系统 STT
    use_native_tts: false  # 使用系统 TTS
    
  ios:
    enabled: true
    use_native_stt: false
    use_native_tts: false
    
  web:
    enabled: true
    use_web_speech_api: false  # 使用浏览器 Web Speech API
    
  windows:
    enabled: true
    use_native_stt: false
    use_native_tts: false
    
  macos:
    enabled: true
    use_native_stt: false
    use_native_tts: false
    
  watchos:
    enabled: false
    force_cloud: true  # 手表端强制使用云端处理
    
  smart_speaker:
    enabled: false
    providers:
      - tmall  # 天猫精灵
      - xiaomi # 小爱同学
      - baidu  # 小度

# ==================== 智能音箱技能配置 ====================
smart_speaker_skills:
  tmall:
    enabled: false
    skill_id: ""
    skill_secret: ""
    
  xiaomi:
    enabled: false
    skill_id: ""
    skill_secret: ""
    
  baidu:
    enabled: false
    skill_id: ""
    skill_secret: ""

# ==================== 高级功能 ====================
advanced:
  # 多轮对话上下文
  conversation_memory:
    enabled: true
    max_turns: 10
    storage: "sqlite"  # sqlite | redis | memory
    
  # 语音唤醒词
  wake_word:
    enabled: false
    word: "你好小助手"
    sensitivity: 0.7
    
  # 离线模式
  offline_mode:
    enabled: false
    fallback_to_cloud: true
    
  # 隐私模式
  privacy:
    log_audio: false
    store_transcripts: true
    anonymize: false
```

---

## 🔌 API 接口设计

### 基础 URL
```
http://localhost:8082/api/v1
```

### 1. 语音输入 (STT)

```http
POST /voice/input
Content-Type: multipart/form-data

{
  "audio": <file>,
  "format": "wav|mp3|ogg|flac",
  "language": "zh-CN|en-US|...",
  "provider": "aliyun|baidu|..."  # 可选，覆盖配置
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "text": "今天天气怎么样",
    "confidence": 0.95,
    "duration": 2.3,
    "provider": "aliyun"
  }
}
```

### 2. 语音输出 (TTS)

```http
POST /voice/output
Content-Type: application/json

{
  "text": "今天天气晴朗",
  "voice": "longxiaochun",
  "format": "mp3|wav|ogg",
  "speed": 1.0
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "audio_url": "/audio/tts_20260315_123456.mp3",
    "duration": 3.2,
    "provider": "aliyun"
  }
}
```

### 3. 视频输入 (Vision)

```http
POST /video/input
Content-Type: multipart/form-data

{
  "video": <file>,
  "prompt": "描述这个视频的内容",
  "max_frames": 60
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "description": "视频中显示了一个人在厨房做饭...",
    "frames_analyzed": 45,
    "provider": "aliyun"
  }
}
```

### 4. AI 对话

```http
POST /agent/chat
Content-Type: application/json

{
  "message": "今天天气怎么样",
  "session_id": "user_123",
  "context": [],  # 历史对话
  "voice_input": true,  # 是否返回语音
  "voice_output": true
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "text": "今天天气晴朗，气温 25 度...",
    "audio_url": "/audio/response_123.mp3",
    "session_id": "user_123",
    "turn_id": 42
  }
}
```

### 5. 流式语音对话 (WebSocket)

```javascript
// 客户端连接
const ws = new WebSocket('ws://localhost:8082/ws/chat?session_id=user_123');

// 发送音频流
ws.send(audioChunk);

// 接收响应
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  // { type: 'transcript'|'response'|'audio', data: ... }
};
```

---

## 📱 客户端 SDK 设计

### Android (Kotlin)

```kotlin
val client = OpenClawClient(
    baseUrl = "http://your-server:8082",
    configPath = "config.yaml"
)

// 语音对话
val response = client.voiceChat(
    audioFile = audioFile,
    enableVideo = false
)

// 播放响应
client.playAudio(response.audioUrl)
```

### iOS (Swift)

```swift
let client = OpenClawClient(
    baseURL: URL(string: "http://your-server:8082")!,
    configPath: "config.yaml"
)

// 语音对话
client.voiceChat(audio: audioData) { response in
    playAudio(response.audioUrl)
}
```

### Web (JavaScript)

```javascript
const client = new OpenClawClient({
    baseUrl: 'http://your-server:8082',
    configPath: '/config.yaml'
});

// 使用麦克风
const response = await client.voiceChatFromMic();
await client.playAudio(response.audioUrl);
```

---

## 🚀 快速开始

### 1. 最小化配置 (仅 AI 对话)

```yaml
enabled: true

ai_chat:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"  # 你的 DashScope API Key
```

### 2. 完整语音对话配置

```yaml
enabled: true

speech_to_text:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"

text_to_speech:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"

ai_chat:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"
```

### 3. 启用智能音箱集成

```yaml
smart_speaker_skills:
  tmall:
    enabled: true
    skill_id: "your_tmall_skill_id"
    skill_secret: "your_secret"
    
  xiaomi:
    enabled: true
    skill_id: "your_xiaomi_skill_id"
    skill_secret: "your_secret"
```

---

## 📂 文件结构

```
openclaw-clients/
├── backend/
│   ├── services/
│   │   ├── voice_service.py      # 语音处理服务
│   │   ├── video_service.py      # 视频处理服务
│   │   ├── chat_service.py       # AI 对话服务
│   │   └── adapter/
│   │       ├── stt_aliyun.py
│   │       ├── stt_baidu.py
│   │       ├── tts_aliyun.py
│   │       └── ...
│   └── config/
│       └── config.example.yaml   # 配置模板
├── android/
│   └── app/src/main/java/...
│       └── sdk/
│           └── OpenClawClient.kt
├── ios/
│   └── OpenClawClients/
│       └── SDK/
│           └── OpenClawClient.swift
├── web/
│   └── js/
│       └── openclaw-client.js
├── docs/
│   ├── VOICE-VIDEO-ARCHITECTURE.md  # 本文档
│   └── API.md                       # 详细 API 文档
└── config/
    ├── config.example.yaml          # 配置模板
    └── config.yaml                  # 实际配置 (gitignore)
```

---

## ✅ 下一步

1. **创建配置模板** - `config.example.yaml`
2. **实现后端适配层** - 各 provider 的 adapter
3. **更新客户端 SDK** - 集成统一接口
4. **创建智能音箱技能包** - 天猫精灵/小爱同学
5. **编写部署文档** - 一键部署脚本

---

**设计原则:**
- 🔧 配置驱动 - 所有功能通过配置文件启用/禁用
- 🔌 插件化 - 新增 provider 只需添加 adapter
- 🔐 安全 - API Key 支持环境变量
- 📱 跨平台 - 统一接口，各平台 SDK 封装
- 🌐 离线友好 - 支持本地模型 fallback
