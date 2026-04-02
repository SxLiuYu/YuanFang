@echo off
chcp 65001 >nul
echo ================================================
echo  🦞 龙虾军团启动脚本
echo ================================================

REM 启动 WSL Docker
echo [1/3] 启动 Docker (WSL)...
wsl docker start lobster-qdrant lobster-redis 2>nul
if %errorlevel% neq 0 (
    echo 启动 Qdrant 和 Redis...
    wsl docker run -d --name lobster-qdrant -p 127.0.0.1:6333:6333 -p 127.0.0.1:6334:6334 -v /home/ubuntu/lobster-army-data/qdrant:/qdrant/storage qdrant/qdrant:v1.7.0 2>nul
    wsl docker run -d --name lobster-redis -p 127.0.0.1:6379:6379 redis:7-alpine 2>nul
)

REM 等待服务就绪
echo [2/3] 等待服务启动...
timeout /t 3 /nobreak >nul

REM 检查服务状态
wsl curl -s http://localhost:6333/collections >nul 2>&1
if %errorlevel% equ 0 (
    echo     Qdrant  ✅
) else (
    echo     Qdrant  ❌
)

REM 启动 Flask
echo [3/3] 启动 Flask 服务...
start /min cmd /c "cd /d %~dp0 ^&^& python main.py"

echo.
echo ================================================
echo  启动完成！
echo  Flask: http://localhost:8000
echo  Qdrant: http://localhost:6333
echo ================================================
pause
