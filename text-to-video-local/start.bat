@echo off
setlocal enabledelayedexpansion

:: AI Video Generator - Windows 启动脚本

echo ================================================
echo   AI Video Generator - 启动脚本
echo ================================================
echo.

:: 检查虚拟环境
if not exist "venv" (
    echo [ERROR] 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)
echo [OK] 虚拟环境存在

:: 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未找到
    pause
    exit /b 1
)
echo [OK] Python: 
python --version

:: 检查 FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARN] FFmpeg 未安装
) else (
    echo [OK] FFmpeg 已安装
)

:: 获取启动模式
set MODE=%1
if "%MODE%"=="" set MODE=web

echo.
echo ================================================
echo   启动服务：%MODE%
echo ================================================
echo.

if "%MODE%"=="web" (
    python web\app.py
) else if "%MODE%"=="personal" (
    python personal_mode\run.py -m personal %*
) else if "%MODE%"=="hybrid" (
    python personal_mode\run.py -m hybrid %*
) else if "%MODE%"=="collaborative" (
    python personal_mode\run.py -m collaborative %*
) else if "%MODE%"=="check" (
    python generation.py --check
) else (
    echo [ERROR] 未知模式：%MODE%
    echo 可用模式：web, personal, hybrid, collaborative, check
    pause
    exit /b 1
)
