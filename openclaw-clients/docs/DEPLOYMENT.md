# OpenClaw 部署指南

**版本**: v1.0  
**更新日期**: 2026-03-19

---

## 目录

1. [部署概述](#一部署概述)
2. [后端部署](#二后端部署)
3. [Windows 客户端部署](#三windows-客户端部署)
4. [生产环境配置](#四生产环境配置)
5. [监控与维护](#五监控与维护)

---

## 一、部署概述

### 1.1 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户终端                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Windows 应用  │  │ Flutter 应用  │  │   Web 应用   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      反向代理 (Nginx)                        │
│                   SSL 终止、负载均衡                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     应用服务器 (FastAPI)                      │
│                   Gunicorn + Uvicorn Workers                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据存储 (SQLite)                        │
│                   family.db / hardware.db / ...              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 环境要求

**后端服务器**：
- 操作系统：Linux (Ubuntu 20.04+) 或 Windows Server 2019+
- Python：3.10+
- 内存：≥ 2GB
- 磁盘：≥ 10GB
- 网络：公网 IP，开放 443 端口

**Windows 客户端**：
- 操作系统：Windows 10 1809+ 或 Windows 11
- .NET Runtime：8.0+
- 内存：≥ 4GB
- 磁盘：≥ 100MB

---

## 二、后端部署

### 2.1 本地开发环境部署

```bash
# 1. 克隆代码
git clone https://github.com/SxLiuYu/openclaw-clients.git
cd openclaw-clients/backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置
cp ../config/config.example.yaml ../config/config.yaml
# 编辑 config.yaml，填入 API Key

# 5. 启动
python main.py
```

### 2.2 生产环境部署（Linux）

**方式 1：直接部署**

```bash
# 1. 安装系统依赖
sudo apt update
sudo apt install python3.10 python3.10-venv nginx

# 2. 创建应用用户
sudo useradd -m -s /bin/bash openclaw

# 3. 切换用户
sudo su - openclaw

# 4. 克隆代码
git clone https://github.com/SxLiuYu/openclaw-clients.git
cd openclaw-clients/backend

# 5. 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]

# 7. 配置
cp ../config/config.example.yaml ../config/config.yaml
# 编辑配置文件

# 8. 测试启动
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8082
```

**方式 2：Docker 部署**

```bash
# 1. 构建 Docker 镜像
cd backend
docker build -t openclaw-backend:1.0 .

# 2. 运行容器
docker run -d \
  --name openclaw-backend \
  -p 8082:8082 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/../config:/app/config \
  openclaw-backend:1.0

# 3. 查看日志
docker logs -f openclaw-backend
```

**方式 3：Docker Compose 部署**

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8082:8082"
    volumes:
      - ./data:/app/data
      - ../config:/app/config
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    restart: unless-stopped
```

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2.3 Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/openclaw
server {
    listen 80;
    server_name api.openclaw.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.openclaw.com;
    
    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/api.openclaw.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.openclaw.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件缓存
    location /static/ {
        alias /home/openclaw/openclaw-clients/backend/static/;
        expires 30d;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.4 Systemd 服务配置

```ini
# /etc/systemd/system/openclaw-backend.service
[Unit]
Description=OpenClaw Backend API
After=network.target

[Service]
Type=notify
User=openclaw
Group=openclaw
WorkingDirectory=/home/openclaw/openclaw-clients/backend
Environment="PATH=/home/openclaw/openclaw-clients/backend/venv/bin"
ExecStart=/home/openclaw/openclaw-clients/backend/venv/bin/gunicorn \
  main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8082 \
  --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable openclaw-backend
sudo systemctl start openclaw-backend
sudo systemctl status openclaw-backend
```

---

## 三、Windows 客户端部署

### 3.1 构建发布版本

```bash
# 1. 进入项目目录
cd windows-desktop/OpenClaw.Desktop

# 2. 发布为自包含应用
dotnet publish -c Release -r win-x64 --self-contained

# 或发布为单文件
dotnet publish -c Release -r win-x64 --self-contained /p:PublishSingleFile=true
```

**输出位置**：
```
bin/Release/net8.0-windows/win-x64/publish/
├── OpenClaw.Desktop.exe
├── appsettings.json
└── ...其他依赖文件
```

### 3.2 创建安装包

**方式 1：MSIX 打包**（推荐）

需要 Visual Studio 2022 和 Windows Application Packaging Project。

**方式 2：Inno Setup**

```ini
; setup.iss
[Setup]
AppName=OpenClaw Desktop
AppVersion=1.0.0
DefaultDirName={pf}\OpenClaw Desktop
DefaultGroupName=OpenClaw Desktop
OutputBaseFilename=OpenClaw-Desktop-Setup

[Files]
Source: "bin\Release\net8.0-windows\win-x64\publish\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\OpenClaw Desktop"; Filename: "{app}\OpenClaw.Desktop.exe"
Name: "{commondesktop}\OpenClaw Desktop"; Filename: "{app}\OpenClaw.Desktop.exe"

[Run]
Filename: "{app}\OpenClaw.Desktop.exe"; Description: "Launch OpenClaw Desktop"; Flags: nowait postinstall skipifsilent
```

```bash
# 编译安装包
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
```

### 3.3 配置客户端

**appsettings.json**：
```json
{
  "ApiBaseUrl": "https://api.openclaw.com",
  "EnableDebugMode": false,
  "AutoStart": true,
  "MinimizeToTray": true
}
```

### 3.4 分发方式

1. **直接分发**：将 publish 文件夹打包为 ZIP
2. **安装包分发**：使用 MSIX 或 Inno Setup 创建安装程序
3. **Microsoft Store**：上传到 Microsoft Store

---

## 四、生产环境配置

### 4.1 环境变量

**后端环境变量**：
```bash
# .env
DASHSCOPE_API_KEY=sk-xxxxx
DATABASE_URL=sqlite:///data/openclaw.db
SECRET_KEY=your-secret-key
DEBUG=false
LOG_LEVEL=INFO
```

**客户端配置**：
```json
// appsettings.json
{
  "ApiBaseUrl": "https://api.openclaw.com",
  "EnableDebugMode": false,
  "Timeout": 30000
}
```

### 4.2 数据备份

**自动备份脚本**：
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/openclaw"
DATE=$(date +%Y%m%d_%H%M%S)
DATA_DIR="/home/openclaw/openclaw-clients/data"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
tar -czf $BACKUP_DIR/openclaw_$DATE.tar.gz -C $DATA_DIR .

# 删除 7 天前的备份
find $BACKUP_DIR -name "openclaw_*.tar.gz" -mtime +7 -delete

echo "Backup completed: openclaw_$DATE.tar.gz"
```

**设置定时任务**：
```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /home/openclaw/scripts/backup.sh >> /var/log/openclaw-backup.log 2>&1
```

### 4.3 日志管理

**日志轮转配置**（`/etc/logrotate.d/openclaw`）：
```
/var/log/openclaw/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 openclaw openclaw
    sharedscripts
    postrotate
        systemctl reload openclaw-backend > /dev/null 2>&1 || true
    endscript
}
```

---

## 五、监控与维护

### 5.1 健康检查

**API 健康检查端点**：
```bash
# 检查服务状态
curl http://localhost:8082/health

# 响应
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

### 5.2 监控脚本

**服务监控脚本**：
```bash
#!/bin/bash
# monitor.sh

SERVICE="openclaw-backend"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/health)

if [ "$RESPONSE" != "200" ]; then
    echo "Service $SERVICE is unhealthy!"
    systemctl restart $SERVICE
    # 发送告警邮件
    echo "Service restarted at $(date)" | mail -s "OpenClaw Alert" admin@example.com
fi
```

**设置定时检查**：
```bash
# 每 5 分钟检查一次
*/5 * * * * /home/openclaw/scripts/monitor.sh
```

### 5.3 性能优化

**Gunicorn 配置优化**：
```bash
# 根据服务器配置调整
# Workers = (2 * CPU_cores) + 1

gunicorn main:app \
  -w 9 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8082 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

**Nginx 性能优化**：
```nginx
# 在 http 块中添加
worker_processes auto;
worker_connections 1024;

# 启用 gzip 压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 连接优化
keepalive_timeout 65;
client_max_body_size 10M;
```

### 5.4 安全加固

**1. 防火墙配置**：
```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

**2. 定期更新**：
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

**3. SSL 证书更新**：
```bash
# 使用 Let's Encrypt
sudo certbot renew
```

---

## 附录

### A. 常用命令

```bash
# 服务管理
sudo systemctl start openclaw-backend
sudo systemctl stop openclaw-backend
sudo systemctl restart openclaw-backend
sudo systemctl status openclaw-backend

# 查看日志
sudo journalctl -u openclaw-backend -f

# Docker 管理
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose restart

# 数据库管理
sqlite3 data/family.db
sqlite> .tables
sqlite> SELECT * FROM family_groups;
```

### B. 故障排查

**问题 1：服务启动失败**
```bash
# 检查日志
sudo journalctl -u openclaw-backend -n 50

# 检查端口占用
sudo lsof -i :8082

# 检查文件权限
ls -la /home/openclaw/openclaw-clients/backend
```

**问题 2：API 响应慢**
```bash
# 检查资源使用
top
htop

# 检查数据库大小
du -h data/*.db

# 优化数据库
sqlite3 data/family.db "VACUUM;"
```

**问题 3：内存泄漏**
```bash
# 监控内存
watch -n 1 'ps aux | grep python'

# 重启服务
sudo systemctl restart openclaw-backend
```

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19