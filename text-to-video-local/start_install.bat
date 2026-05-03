@echo off
chcp 65001 >nul
title AI 视频生成器 - 开始安装

echo ============================================
echo   AI 视频生成器 - 一键安装
echo ============================================
echo.
echo 正在检查环境...
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python 已安装
    python --version
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Python3 已安装
        python3 --version
    ) else (
        echo [!] Python 未安装
        echo.
        echo 正在运行 Python 安装程序...
        call install_python.bat
        exit /b
    )
)

echo.
echo ============================================
echo   开始安装项目依赖
echo ============================================
echo.

pip install flask pillow psutil

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   ✅ 安装完成！
    echo ============================================
    echo.
    echo 正在启动应用...
    echo.
    python quick_start.py
) else (
    echo.
    echo [!] 安装失败，请检查网络连接
    pause
)
