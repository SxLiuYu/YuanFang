@echo off
chcp 65001 >nul
title 元芳唤醒守护 - PC端

echo ===================================================
echo   🔮 元芳唤醒守护进程 - PC端
echo ===================================================
echo.

set PYTHONIOENCODING=utf-8

REM 检查依赖
python -c "import pvporcupine" 2>nul
if errorlevel 1 (
    echo [!] 正在安装依赖...
    pip install pvporcupine sounddevice websocket-client python-dotenv
    echo.
)

REM 加载 .env
for /f "tokens=1,2 delims==" %%a in (.env 2>nul) do (
    if not "%%a"=="" if not "%%b"=="" set "%%a=%%b"
)

REM 检查配置
if "%PORCUPINE_ACCESS_KEY%"=="" (
    echo ❌ 错误: PORCUPINE_ACCESS_KEY 未配置
    echo    请在 .env 中设置或在 https://console.picovoice.ai/ 获取
    pause
    exit /b 1
)

set SERVER=ws://localhost:8000
set NODE_ID=wake_pc_01

echo 服务端: %SERVER%
echo 节点ID: %NODE_ID%
echo 唤醒词: %WAKE_WORD_PPN% 
if "%WAKE_WORD_PPN%"=="" echo           ^(使用内置备选词: %FALLBACK_KEYWORD%^)
echo.

python wake_client.py --server %SERVER% --node-id %NODE_ID% --record-seconds 5

pause
