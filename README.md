# 元芳 (YuanFang)

> 以 AI 驱动的数字生命体为核心的智能家居控制平台

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 是什么

元芳是一个本地化的 AI Agent 系统，以"数字生命体"为核心理念——它不是工具，而是一个会记住你、理解你、适应你、随着时间推移越来越懂你的老朋友。

元芳运行在 Windows 电脑上作为中央大脑，通过手机（Termux）和智能家居设备作为触手，实现：
- 🧠 **人格引擎** — 有情绪、有性格、会漂移的数字生命
- 💾 **记忆系统** — 情感记忆 + 场景记忆，越聊越懂你
- 🤖 **多 Agent 协作** — 指挥官/研究员/执行者/哨兵/进化官
- 🧬 **自进化** — HyperAgent 自我反思、策略进化
- 🏠 **智能家居** — Home Assistant 设备控制
- 📱 **手机节点** — Termux 传感器实时推送
- 💬 **Web 控制台** — 深海科技风 Dashboard
- 🎤 **语音交互** — 语音识别 + 语音合成
- 🔮 **唤醒词** — "元芳" 语音唤醒，端侧离线检测
- 👁️ **视觉识别** — 图片分析

## 🏗️ 系统架构

```
                    ┌─────────────────────────────┐
                    │      元芳主服务 :8000        │
                    │  Flask + SocketIO + 人格引擎   │
                    └──────────────┬──────────────┘
                                   │
         ┌─────────────┬─────────┴──┬──────────────┬──────────────┐
         ▼             ▼            ▼              ▼              ▼
 ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ 传感器节点  │ │ 唤醒节点  │ │  AI 模型  │ │   HA     │ │ Dashboard│
 │ Termux WS  │ │ 🔮 离线   │ │ DS/Kimi  │ │  设备    │ │  Web UI  │
 └────────────┘ │ Porcupine│ └──────────┘ └──────────┘ └──────────┘
                └──────────┘
```

## 🤖 Agent 团队

| 代号 | 名称 | 职责 | 模型 |
|------|------|------|------|
| Commander | 指挥官 | 任务拆解、战略决策 | DeepSeek V3.1 |
| Researcher | 研究员 | 信息检索、深度分析 | Kimi K2 |
| Executor | 执行者 | 快速执行、操作落地 | DeepSeek V3.1 |
| Sensor | 哨兵 | 环境感知、节点管理 | Kimi K2 |
| Hyper | 进化官 | 自我反思、策略进化 | DeepSeek V3.1 |

## 🚀 快速启动

### 环境要求
- Python 3.11+
- Windows / Linux / WSL
- Docker (Qdrant + Redis，可选)

### 安装依赖

```bash
pip install flask flask-socketio python-dotenv requests websocket-client

# 或一键安装
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填写你的 API Key 和其他配置
```

### 启动服务

```bash
# 启动可选依赖服务 (Docker)
docker run -d --name lobster-qdrant -p 127.0.0.1:6333:6333 qdrant/qdrant:v1.7.0
docker run -d --name lobster-redis -p 127.0.0.1:6379:6379 redis:7-alpine

# 启动元芳
python main.py
```

打开浏览器访问: **http://localhost:8000** → Dashboard 控制台

## 📁 目录结构

```
yuanfang/
├── main.py                  # Flask 主服务入口
├── dashboard.html           # Web 控制台 UI
├── personality.py           # 人格引擎（情绪/性格/风格）
├── memory_system.py         # 记忆系统（情感+场景）
├── hyper_agents.py          # 自进化 Agent 系统
├── crew.py                  # 多 Agent 协作入口
├── agents/                  # Agent 实现
│   └── __init__.py          # Commander/Researcher/Executor/Sensor/HyperAgent
├── adapters/                # 外部系统适配器
│   ├── __init__.py
│   └── homeassistant.py     # Home Assistant 适配器
├── termux_sensor_client.py  # Termux 传感器客户端 v3（HTTP/WS）
├── wake_word.py             # 唤醒词引擎（Porcupine 封装）
├── wake_client.py           # 跨平台唤醒守护进程（手机/PC）
├── memory_store/            # 记忆数据（自动创建）
├── evolution_memory/        # 进化记忆（自动创建）
├── .env.example             # 配置模板
├── start.bat                # Windows 启动脚本
├── start_wake.bat           # PC 端唤醒守护启动脚本
└── .env                     # 环境配置 (勿上传)
```

## 🔑 API 接口

### 核心接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容聊天 |
| GET | `/api/health` | 健康检查 |
| GET | `/` | Dashboard 页面 |

### 人格引擎
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/personality/status` | 人格状态 |
| POST | `/api/personality/mood` | 更新情绪 |
| POST | `/api/personality/drift` | 触发情绪漂移 |

### 记忆系统
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/memory/report` | 完整记忆报告 |
| GET | `/api/memory/emotional` | 情感记忆查询 |
| GET | `/api/memory/scene` | 场景记忆查询 |
| POST | `/api/memory/scene/snapshot` | 手动场景快照 |

### Home Assistant
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ha/ping` | HA 连接检测 |
| GET | `/api/ha/summary` | 设备摘要 |
| GET | `/api/ha/states` | 实体状态列表 |
| POST | `/api/ha/light` | 灯光控制 |
| POST | `/api/ha/climate` | 空调控制 |
| GET | `/api/ha/scenes` | 场景列表 |
| POST | `/api/ha/scene/activate` | 激活场景 |

### Agent 接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/crew` | 多 Agent 协作 |
| POST | `/api/agent/<name>` | 单个 Agent 调用 |
| POST | `/api/hyper/run` | HyperAgent 进化 |
| GET | `/api/hyper/status` | 进化状态 |

### 设备命令
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/commands/send` | 发送命令到节点 |
| GET | `/api/commands/pending/<id>` | 节点轮询命令 |
| POST | `/api/commands/complete` | 上报执行结果 |

### WebSocket 事件
| 事件 | 方向 | 说明 |
|------|------|------|
| `register` | 客户端→服务 | 传感器节点注册 |
| `wake_register` | 客户端→服务 | 唤醒节点注册 |
| `sensor_update` | 客户端→服务 | 传感器数据 |
| `voice_wake` | 客户端→服务 | 唤醒节点发送语音 |
| `command` | 服务→客户端 | 下发指令 |
| `voice_response` | 服务→唤醒节点 | TTS 音频回复 |
| `sensor_realtime` | 服务→客户端 | 广播传感器更新 |
| `scene_update` | 服务→客户端 | 广播场景变化 |
| `node_online` | 服务→客户端 | 节点上线通知 |
| `chat_message` | 服务→客户端 | 广播语音对话内容 |

## 📱 节点部署

### Termux 传感器节点

```bash
# 在 Termux 中安装依赖
pkg update && pkg install python termux-api
pip install websocket-client

# WebSocket 实时模式（推荐）
python termux_sensor_client.py --server ws://<主机IP>:8000 --node-id my_phone

# HTTP 轮询模式（兼容）
python termux_sensor_client.py --server http://<主机IP>:8000 --interval 60
```

### Termux 语音节点

```bash
python termux_voice_client.py --server http://<主机IP>:8000 --node-id voice_01
```

### 🔮 语音唤醒节点

在手机或电脑上部署唤醒守护进程，检测到唤醒词后自动录音对话。

**准备工作：**
1. 到 [Picovoice Console](https://console.picovoice.ai/) 注册，获取免费 Access Key
2. 在 Console 中创建唤醒词 "元芳"，下载 `.ppn` 文件
3. 下载中文语言模型 `.pv` 文件: [GitHub](https://github.com/Picovoice/porcupine/tree/master/lib/common)

**手机端 (Termux)：**
```bash
pip install pvporcupine websocket-client pulseaudio sox

# 启动唤醒守护
python wake_client.py --server ws://<主机IP>:8000 --node-id wake_phone_01
```

**电脑端 (Windows)：**
```cmd
pip install pvporcupine sounddevice websocket-client python-dotenv
start_wake.bat
```

**配置 (.env)：**
```env
PORCUPINE_ACCESS_KEY=your_key_here
WAKE_WORD_PPN=/path/to/元芳.ppn       # 自定义唤醒词文件
PORCUPINE_MODEL=/path/to/porcupine_params_zh.pv  # 中文模型
WAKE_WORD_SENSITIVITY=0.5
RECORD_SECONDS=5
```

## 🔧 配置说明

复制 `.env.example` 为 `.env` 并填写：

| 变量 | 说明 | 必填 |
|------|------|------|
| `FINNA_API_KEY` | FinnA API 密钥 | ✅ |
| `FINNA_API_BASE` | FinnA API 地址 | 默认即可 |
| `PORT` | 服务端口 | 默认 8000 |
| `HOME_WIFI` | 家庭 WiFi SSID | 在家检测用 |
| `HA_URL` | Home Assistant 地址 | HA 控制用 |
| `HA_TOKEN` | HA 长效访问令牌 | HA 控制用 |
| `PORCUPINE_ACCESS_KEY` | Picovoice 唤醒词 Key | 唤醒词用 |
| `WAKE_WORD_PPN` | 唤醒词 .ppn 文件路径 | 唤醒词用 |
| `WAKE_WORD_SENSITIVITY` | 唤醒灵敏度 (0~1) | 默认 0.5 |

## 📝 License

MIT
