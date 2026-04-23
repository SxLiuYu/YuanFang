# OpenClaw Backend Service

OpenClaw 家庭服务后端 API，提供智能家居、家庭账本、任务板、购物清单等功能。

## 📦 快速部署

### 方式一：一键部署脚本（推荐）

```bash
./deploy.sh
```

### 方式二：Docker Compose

```bash
# 基础部署（仅后端服务）
docker compose up -d --build

# 含 Redis 缓存
docker compose --profile with-redis up -d --build

# 含 PostgreSQL 数据库
docker compose --profile with-postgres up -d --build
```

### 方式三：手动构建

```bash
# 构建镜像
docker build -t openclaw-backend .

# 运行容器
docker run -d \
  --name openclaw-backend \
  -p 8082:8082 \
  -v backend-data:/app/services/data \
  openclaw-backend
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| FLASK_ENV | production | 运行环境 |
| FLASK_DEBUG | 0 | 调试模式 |
| PYTHONPATH | /app/services | Python 路径 |

### 端口

- **8082**: 后端 API 服务

### 数据卷

- `backend-data`: 持久化数据（数据库、缓存等）
- `backend-logs`: 日志文件
- `redis-data`: Redis 数据（如启用）
- `postgres-data`: PostgreSQL 数据（如启用）

## 📋 API 端点

主要服务运行在 `http://localhost:8082`

### 健康检查
- `GET /health` - 服务健康状态

### 家庭服务
- 智能家居设备管理
- 家庭账本
- 任务板
- 购物清单

### AI 服务
- 小红书搜索
- 语音交互
- 做菜推荐

## 🔍 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重建服务
docker compose up -d --build

# 清理所有资源
docker compose down -v
```

## 🛠️ 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
cd services
python family_services_api.py
```

## 📁 项目结构

```
backend/
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
├── .dockerignore          # Docker 忽略文件
├── deploy.sh              # 一键部署脚本
├── README.md              # 本文档
├── requirements.txt       # Python 依赖
└── services/              # 服务代码
    ├── family_services_api.py        # 主 API 服务
    ├── cooking_service.py            # 做菜服务
    ├── voice_interaction_service.py  # 语音交互服务
    ├── xiaohongshu_search_service.py # 小红书搜索服务
    └── ... (其他服务模块)
```

## ⚠️ 注意事项

1. 首次启动可能需要几分钟下载镜像
2. 确保端口 8082 未被占用
3. 生产环境请修改默认密码
4. 定期备份数据卷

## 📞 支持

如有问题，请查看日志或联系开发团队。

```bash
# 查看详细日志
docker compose logs -f openclaw-backend
```
