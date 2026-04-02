@echo off
title 贾维斯 - 语音助手
cd /d %~dp0
echo ================================
echo    贾维斯 AI 语音助手
echo ================================
echo.
echo 启动模式:
echo   1 - 唤醒词模式 (说"贾维斯"唤醒)
echo   2 - 持续监听模式
echo   3 - 文字交互模式
echo.
choice /c 123 /m "选择模式"

if errorlevel 3 goto text
if errorlevel 2 goto continuous
if errorlevel 1 goto wakeword

:wakeword
echo.
echo [模式] 唤醒词模式 - 说"贾维斯"唤醒我
python voice_chat.py --wake-word
goto end

:continuous
echo.
echo [模式] 持续监听模式
python voice_chat.py --continuous
goto end

:text
echo.
echo [模式] 文字交互模式
python jarvis.py
goto end

:end
pause
