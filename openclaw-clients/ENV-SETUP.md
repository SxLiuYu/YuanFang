# 环境变量配置指南

本文档说明 OpenClaw 各平台客户端的环境变量配置方式。

## 环境变量清单

| 变量名 | 说明 | 必需 | 示例值 |
|--------|------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key | ✅ | `sk-xxxxxx` |
| `TAVILY_API_KEY` | Tavily 搜索 API Key（默认搜索服务） | ✅ | `tvly-dev-xxxxxx` |
| `OPENCLAW_SERVER_URL` | OpenClaw 设备服务器地址 | ✅ | `https://api.openclaw.ai` |
| `OPENCLAW_CHAT_URL` | OpenClaw 聊天服务器地址 | ✅ | `https://chat.openclaw.ai` |
| `DEBUG_MODE` | Python 调试模式开关 | ⚪ | `true` / `false` |
| `BOCHA_API_KEY` | 博查新闻 API Key | ⚪ | `sk-xxxxxx` |
| `LOG_LEVEL` | 日志级别 | ⚪ | `INFO` / `DEBUG` |

---

## 各平台配置方式

### Android 原生

#### 方式 1: local.properties (推荐)
在 `android/local.properties` 中配置：
```properties
openclaw.server.url=https://api.openclaw.ai
openclaw.chat.url=https://chat.openclaw.ai
```

#### 方式 2: BuildConfig (已配置)
在 `android/app/build.gradle` 中已配置默认值：
```gradle
buildConfigField "String", "DEFAULT_SERVER_URL", "\"https://api.openclaw.ai\""
buildConfigField "String", "DEFAULT_CHAT_SERVER_URL", "\"https://chat.openclaw.ai\""
```

#### 方式 3: 运行时配置
用户可以在 App 设置界面输入服务器地址和 API Key，使用 `SecureConfig` 加密存储。

---

### Flutter 移动端

#### 配置步骤
1. 复制环境变量模板：
   ```bash
   cp flutter_mobile/.env.example flutter_mobile/.env
   ```

2. 编辑 `.env` 文件：
   ```env
   OPENCLAW_SERVER_URL=https://api.openclaw.ai
   ```

3. 确认 `.env` 在 `.gitignore` 中（已配置）

---

### Electron 桌面端

#### 配置步骤
1. 复制环境变量模板：
   ```bash
   cp electron_desktop/.env.example electron_desktop/.env
   ```

2. 编辑 `.env` 文件：
   ```env
   OPENCLAW_DEVICE_URL=https://api.openclaw.ai
   OPENCLAW_CHAT_URL=https://chat.openclaw.ai
   OPENCLAW_API_KEY=sk-xxxxxx
   ```

3. 环境变量优先级：
   - 系统环境变量 > `.env` 文件 > 默认值

---

### Web 客户端

#### 配置方式
Web 客户端通过界面配置：
1. 打开 `web/index.html`
2. 点击"设置"展开配置面板
3. 输入服务器地址
4. 点击"保存设置"

配置保存在 `localStorage` 中。

---

### Python 后端

#### 方式 1: 系统环境变量 (推荐)
```bash
# Linux/macOS
export DASHSCOPE_API_KEY=sk-xxxxxx
export DEBUG_MODE=false

# Windows CMD
set DASHSCOPE_API_KEY=sk-xxxxxx
set DEBUG_MODE=false

# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxxxx"
$env:DEBUG_MODE="false"
```

#### 方式 2: .env 文件
在 `backend/services/` 目录创建 `.env` 文件：
```env
DASHSCOPE_API_KEY=sk-xxxxxx
DEBUG_MODE=false
```

#### 方式 3: systemd 服务配置
```ini
# /etc/systemd/system/openclaw.service
[Service]
Environment="DASHSCOPE_API_KEY=sk-xxxxxx"
Environment="DEBUG_MODE=false"
ExecStart=/usr/bin/python3 /path/to/main.py
```

---

## 本地开发环境搭建

### 1. 克隆项目
```bash
git clone https://github.com/SxLiuYu/openclaw-clients.git
cd openclaw-clients
```

### 2. 配置后端
```bash
cd backend/services
cp .env.example .env
# 编辑 .env 填入 API Key
pip install -r requirements.txt
python family_services_api.py
```

### 3. 配置 Android
```bash
cd android
# 编辑 local.properties 配置服务器地址
./gradlew assembleDebug
```

### 4. 配置 Flutter
```bash
cd flutter_mobile
cp .env.example .env
# 编辑 .env
flutter pub get
flutter run
```

### 5. 配置 Electron
```bash
cd electron_desktop
cp .env.example .env
# 编辑 .env
npm install
npm start
```

---

## 生产环境部署

### 服务器端
```bash
# 设置环境变量
export DASHSCOPE_API_KEY=<生产环境 Key>
export DEBUG_MODE=false

# 使用 systemd 管理服务
sudo systemctl enable openclaw-backend
sudo systemctl start openclaw-backend
```

### 客户端
- 使用 HTTPS 确保通信安全
- API Key 通过服务端代理，不暴露给客户端
- 使用正规的 SSL 证书

---

## 安全注意事项

1. **禁止提交 .env 文件到 Git** - 已在 `.gitignore` 中配置
2. **禁止在代码中硬编码 API Key** - 已修复
3. **定期轮换 API Key** - 建议每 90 天
4. **生产环境禁用 DEBUG 模式** - `DEBUG_MODE=false`
5. **使用 HTTPS** - 所有服务器地址使用 https://

---

## 故障排查

### Android 编译失败
```bash
# 清理构建缓存
cd android
./gradlew clean
./gradlew assembleDebug
```

### Flutter 运行失败
```bash
# 清理缓存
flutter clean
flutter pub get
flutter run
```

### 后端 API 调用失败
1. 检查 `DASHSCOPE_API_KEY` 是否正确设置
2. 检查网络连接
3. 查看日志：`tail -f /var/log/openclaw.log`