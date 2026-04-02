@echo off
chcp 65001 >nul
echo ================================================
echo  🦞 龙虾军团状态检查
echo ================================================

echo.
echo [Docker 容器]
wsl docker ps --format "  {{.Names}}: {{.Status}}" 2>nul

echo.
echo [Flask 服务]
curl.exe -s http://localhost:8000/api/health 2>nul
if %errorlevel% equ 0 (
    echo  ✅ 运行中
) else (
    echo  ❌ 未运行
)

echo.
echo [Qdrant]
curl.exe -s http://localhost:6333/collections 2>nul
if %errorlevel% equ 0 (
    echo  ✅ 运行中
) else (
    echo  ❌ 未运行
)

echo.
echo ================================================
pause
