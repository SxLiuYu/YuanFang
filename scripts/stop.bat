@echo off
chcp 65001 >nul
echo ================================================
echo  🦞 龙虾军团停止脚本
echo ================================================

echo 停止 Flask 服务...
taskkill /f /im python.exe 2>nul
echo  Flask ✅

echo 停止 Docker 容器...
wsl docker stop lobster-qdrant lobster-redis 2>nul
echo  Docker ✅

echo.
echo ================================================
echo  已全部停止
echo ================================================
pause
