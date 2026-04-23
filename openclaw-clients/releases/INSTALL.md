# 📦 OpenClaw Clients 家庭助手 - 完整安装指南

**版本**: v1.0  
**更新日期**: 2026-03-15  
**支持平台**: Android, iOS, Web, Windows, macOS, WatchOS, 智能音箱

---

## 🎯 快速开始（3 分钟）

### 步骤 1: 获取 API Key
访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/) 获取 API Key

### 步骤 2: 配置
```bash
cd openclaw-clients
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml，填入 API Key
```

### 步骤 3: 启动后端
```bash
cd backend
./deploy.sh
# 或 docker compose up -d
```

### 步骤 4: 使用客户端
- **Web**: 浏览器打开 `web/dist/index_enhanced.html`
- **Android**: 安装 APK
- **iOS**: Xcode 编译
- **智能音箱**: 在对应平台创建技能

---

## 📋 目录结构

```
openclaw-clients/
├── config/                      # 配置文件
│   ├── config.example.yaml      # 配置模板
│   └── config.yaml              # 实际配置（需创建）
├── backend/                     # 后端服务
│   ├── services/                # 服务代码
│   ├── Dockerfile               # Docker 配置
│   ├── docker-compose.yml       # 一键部署
│   └── deploy.sh                # 部署脚本
├── android/                     # Android 客户端
├── ios/                         # iOS 客户端
├── flutter_mobile/              # Flutter 跨平台
├── web/                         # Web 客户端
├── smart_speaker_skills/        # 智能音箱技能
│   ├── tmall/                   # 天猫精灵
│   ├── xiaomi/                  # 小爱同学
│   ├── baidu/                   # 小度
│   └── ...                      # 其他平台
├── docs/                        # 文档
│   ├── VOICE-VIDEO-ARCHITECTURE.md
│   ├── FAMILY-SERVICES-FULL.md
│   └── API.md
└── releases/                    # 安装包
    └── INSTALL.md               # 本文档
```

---

## 🔧 后端服务部署

### 方式 1: Docker Compose（推荐）

```bash
cd backend

# 基础部署（SQLite）
docker compose up -d

# 完整部署（PostgreSQL + Redis）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

访问：http://localhost:8082

### 方式 2: 本地部署

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 或生产环境
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 方式 3: 使用部署脚本

```bash
cd backend
./deploy.sh
# 按提示选择部署模式
```

---

## 📱 客户端安装

### Android

#### 方式 1: 直接安装 APK
```bash
# 下载 APK
releases/android/OpenClawClients-v1.0.apk

# 在手机上安装
adb install OpenClawClients-v1.0.apk
```

#### 方式 2: 自行编译
```bash
cd android

# 配置 API Key（可选）
echo "DASHSCOPE_API_KEY=sk-xxx" >> local.properties

# 编译
./gradlew assembleDebug

# APK 位置
app/build/outputs/apk/debug/app-debug.apk
```

### iOS

```bash
cd ios

# 打开 Xcode 项目
open OpenClawClients.xcodeproj

# Xcode 中：
# 1. 选择团队签名
# 2. 修改 Bundle ID
# 3. 运行或 Archive
```

### Flutter（跨平台）

```bash
cd flutter_mobile

# 获取依赖
flutter pub get

# 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行
flutter run

# 构建 APK
flutter build apk

# 构建 iOS
flutter build ios
```

### Web

```bash
# 方式 1: 直接打开
open web/dist/index_enhanced.html

# 方式 2: 本地服务器
cd web/dist
python -m http.server 8080
# 访问 http://localhost:8080

# 方式 3: Nginx 部署
sudo cp nginx.conf /etc/nginx/sites-available/openclaw
sudo ln -s /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Windows/macOS 桌面

```bash
# 使用 Electron 版本
cd electron_desktop

# 安装依赖
npm install

# 开发模式
npm start

# 打包
npm run build
```

---

## 🔌 智能音箱技能配置

### 天猫精灵

1. 访问 https://open.aligenie.com/
2. 创建技能 → 自定义技能
3. 填写技能信息
4. 配置意图（使用 `smart_speaker_skills/tmall/skill.yaml`）
5. Webhook URL: `https://your-server.com/api/v1/smart-speaker/tmall`
6. 提交审核

### 小爱同学

1. 访问 https://developers.xiaoai.mi.com/
2. 创建技能 → 对话技能
3. 配置意图（使用 `smart_speaker_skills/xiaomi/skill.yaml`）
4. Webhook URL: `https://your-server.com/api/v1/smart-speaker/xiaomi`
5. 提交审核

### 其他平台

参考 `smart_speaker_skills/README.md`

---

## ⚙️ 配置文件说明

### 最小化配置

```yaml
enabled: true

ai_chat:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"  # 必填
```

### 完整配置

```yaml
enabled: true
debug: false

# 语音识别
speech_to_text:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"

# 语音合成
text_to_speech:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"

# AI 对话
ai_chat:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"

# 功能模块
features:
  smart_home: true
  finance: true
  task: true
  # ... 其他模块
```

### 环境变量

```bash
# 推荐：使用环境变量存储 API Key
export DASHSCOPE_API_KEY="sk-xxx"
export OPENCLAW_API_TOKEN="your_token"
```

---

## 🎤 语音功能启用

### 启用语音输入输出

```yaml
speech_to_text:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"
    model: paraformer-realtime

text_to_speech:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"
    model: sambert-zhina-v1
    voice: "longxiaochun"
```

### 启用视频理解

```yaml
video_understanding:
  enabled: true
  provider: aliyun
  aliyun:
    api_key: "sk-xxx"
    model: qwen-vl-max
```

---

## 🔐 安全配置

### 启用 API Token 验证

```yaml
security:
  require_token: true
  api_token: "${OPENCLAW_API_TOKEN}"
```

### CORS 配置

```yaml
security:
  cors_origins:
    - "https://your-domain.com"
    - "http://localhost:3000"
```

---

## 📊 功能模块启用

在配置文件中启用/禁用功能：

```yaml
features:
  smart_home: true       # 智能家居
  finance: true          # 家庭财务
  task: true             # 任务管理
  shopping: true         # 购物清单
  recipe: true           # 做菜助手
  health: true           # 健康档案
  calendar: true         # 日程管理
  photo: false           # 家庭相册
  education: true        # 儿童教育
  pet: true              # 宠物照顾
  vehicle: true          # 车辆管理
  home: true             # 房屋维护
  medication: true       # 用药提醒
  service: true          # 生活服务
  entertainment: true    # 家庭娱乐
  security: true         # 安全监控
  communication: true    # 家庭通讯
  report: true           # 数据报表
```

---

## 🧪 测试

### API 测试

```bash
# 测试 AI 对话
curl -X POST http://localhost:8082/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 测试语音合成
curl -X POST http://localhost:8082/api/v1/voice/output \
  -H "Content-Type: application/json" \
  -d '{"text": "你好"}'
```

### 客户端测试

1. 启动后端服务
2. 打开客户端
3. 设置 → 输入服务器地址
4. 测试语音对话

---

## 🐛 常见问题

### 后端启动失败

```bash
# 检查端口占用
lsof -i :8082

# 查看日志
docker compose logs backend
```

### API Key 无效

- 确认 API Key 正确
- 检查环境变量是否生效
- 查看 DashScope 控制台配额

### 客户端无法连接

- 确认后端服务运行
- 检查防火墙设置
- 确认服务器地址正确

### 智能音箱技能审核失败

- 检查意图配置完整
- 确保 Webhook 可公网访问
- 提供测试账号

---

## 📚 相关文档

- [语音/视频架构](../docs/VOICE-VIDEO-ARCHITECTURE.md)
- [家庭服务功能全集](../docs/FAMILY-SERVICES-FULL.md)
- [智能音箱集成指南](../smart_speaker_skills/README.md)
- [API 详细文档](../backend/README.md)

---

## 🆘 获取帮助

- GitHub Issues: https://github.com/SxLiuYu/openclaw-clients/issues
- 文档：https://github.com/SxLiuYu/openclaw-clients/tree/main/docs

---

**祝你使用愉快！** 🎉
