#!/bin/bash
# OpenClaw Backend Service - 一键部署脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  OpenClaw Backend Service 部署脚本"
echo "========================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：Docker 未安装"
    echo "   请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker 已安装: $(docker --version)"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误：Docker Compose 未安装"
    echo "   请先安装 Docker Compose"
    exit 1
fi
echo "✅ Docker Compose 已安装"

echo ""
echo "选择部署模式:"
echo "  1) 基础模式 (仅后端服务)"
echo "  2) 完整模式 (后端 + Redis)"
echo "  3) 数据库模式 (后端 + PostgreSQL)"
echo "  4) 停止服务"
echo "  5) 查看日志"
echo "  6) 重建服务"
echo ""
read -p "请输入选项 (1-6, 默认: 1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "🚀 启动基础模式..."
        docker compose up -d --build
        ;;
    2)
        echo ""
        echo "🚀 启动完整模式 (含 Redis)..."
        docker compose --profile with-redis up -d --build
        ;;
    3)
        echo ""
        echo "🚀 启动数据库模式 (含 PostgreSQL)..."
        docker compose --profile with-postgres up -d --build
        ;;
    4)
        echo ""
        echo "🛑 停止所有服务..."
        docker compose down
        ;;
    5)
        echo ""
        echo "📋 查看服务日志..."
        docker compose logs -f
        ;;
    6)
        echo ""
        echo "🔄 重建服务..."
        docker compose down
        docker compose up -d --build
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "  部署完成!"
echo "========================================"
echo ""
echo "服务访问地址:"
echo "  - 后端 API: http://localhost:8082"
echo ""
echo "常用命令:"
echo "  - 查看状态：docker compose ps"
echo "  - 查看日志：docker compose logs -f"
echo "  - 停止服务：docker compose down"
echo "  - 重启服务：docker compose restart"
echo ""
