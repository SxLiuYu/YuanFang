#!/bin/bash
# OpenClaw Family Assistant - 后端服务启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║   OpenClaw Family Assistant - 后端服务                  ║"
echo "║   版本：1.0.0                                          ║"
echo "╚════════════════════════════════════════════════════════╝"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3"
    exit 1
fi

echo "✓ Python 版本：$(python3 --version)"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 创建数据目录
mkdir -p data audio

# 启动服务
echo ""
echo "🚀 启动服务..."
echo "   API: http://localhost:8082"
echo "   文档：http://localhost:8082/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 main.py
