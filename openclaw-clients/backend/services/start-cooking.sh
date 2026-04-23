#!/bin/bash
# 家庭助手 - 做菜功能快速启动

echo "🍳 家庭助手 - 做菜功能"
echo "======================"
echo ""

# 检查依赖
echo "1. 检查依赖..."
python3 -c "import flask" 2>/dev/null && echo "   ✅ Flask" || echo "   ❌ Flask 未安装"
python3 -c "import flask_cors" 2>/dev/null && echo "   ✅ Flask-CORS" || echo "   ❌ Flask-CORS 未安装"
python3 -c "from xiaohongshu_search_service import XiaoHongShuSearchService" 2>/dev/null && echo "   ✅ 小红书搜索服务" || echo "   ❌ 小红书搜索服务"
echo ""

# 检查小红书 MCP
echo "2. 检查小红书 MCP 服务..."
docker ps 2>/dev/null | grep -q xiaohongshu-mcp && echo "   ✅ xiaohongshu-mcp 运行中" || echo "   ⚠️  xiaohongshu-mcp 未运行"
echo ""

# 启动服务
echo "3. 启动家庭助手 API..."
echo "   端口：8082"
echo "   按 Ctrl+C 停止"
echo ""

cd $(dirname $0)
python3 family_services_api.py
