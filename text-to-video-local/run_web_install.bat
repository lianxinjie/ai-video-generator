@echo off
chcp 65001 >nul
title AI 视频生成器 - Web 安装器
cls

echo ============================================
echo   AI 视频生成器 - Web 安装器
echo ============================================
echo.
echo 正在启动 Web 安装界面...
echo.
echo 浏览器将自动打开：http://localhost:8081
echo.
echo 按 Ctrl+C 可停止服务器
echo.

python "%~dp0install_web.py"

pause
