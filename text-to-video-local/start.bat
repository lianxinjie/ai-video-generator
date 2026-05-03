@echo off
setlocal enabledelayedexpansion

:: AI Video Generator - Windows 启动脚本 (增强版)
:: 支持：CMD / PowerShell / Git Bash

echo ================================================
echo   AI Video Generator - 启动脚本
echo ================================================
echo.

:: ========== 检查虚拟环境 ==========
if not exist "venv\Scripts\python.exe" (
    echo ================================================
    echo [ERROR] 虚拟环境不存在
    echo ================================================
    echo.
    echo 请先运行安装脚本:
    echo   install.bat
    echo.
    echo 或者手动创建虚拟环境:
    echo   python -m venv venv
    echo.
    pause
    exit /b 1
)
echo [OK] 虚拟环境存在

:: ========== 激活虚拟环境 ==========
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 验证激活
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 虚拟环境激活失败
    echo 请尝试手动激活:
    echo   call venv\Scripts\activate
    pause
    exit /b 1
)
echo [OK] 虚拟环境已激活

:: ========== 检查 Python 版本 ==========
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 不可用
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [OK] Python: !PY_VER!

:: ========== 检查 FFmpeg (可选) ==========
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARN] FFmpeg 未安装
    echo 部分功能可能不可用
    echo 安装方法：choco install ffmpeg
) else (
    echo [OK] FFmpeg 已安装
)

:: ========== 获取启动模式 ==========
set MODE=%~1
if "!MODE!"=="" set MODE=web

:: 移除第一个参数，保留后续参数
shift
set ARGS=
:collect_args
if "%~1"=="" goto :start_service
set ARGS=!ARGS! %1
shift
goto :collect_args

:: ========== 启动服务 ==========
:start_service
echo.
echo ================================================
echo   启动模式：!MODE!
echo ================================================
echo.

if /i "!MODE!"=="web" (
    echo 启动 Web 服务...
    echo 访问地址：http://localhost:5000
    echo.
    python web\app.py
    
) else if /i "!MODE!"=="personal" (
    echo 启动个人模式...
    python personal_mode\run.py -m personal !ARGS!
    
) else if /i "!MODE!"=="hybrid" (
    echo 启动混合模式...
    python personal_mode\run.py -m hybrid !ARGS!
    
) else if /i "!MODE!"=="collaborative" (
    echo 启动协同模式...
    python personal_mode\run.py -m collaborative !ARGS!
    
) else if /i "!MODE!"=="check" (
    echo 检查安装状态...
    python generation.py --check
    
) else if /i "!MODE!"=="help" (
    echo.
    echo 用法：start.bat [模式] [参数]
    echo.
    echo 模式:
    echo   web           - 启动 Web 界面 (默认)
    echo   personal      - 个人模式
    echo   hybrid        - 混合模式
    echo   collaborative - 协同模式
    echo   check         - 检查安装
    echo   help          - 显示帮助
    echo.
    echo 示例:
    echo   start.bat web
    echo   start.bat hybrid -p "提示词" -o output.mp4
    echo   start.bat check
    echo.
    
) else (
    echo.
    echo ================================================
    echo [ERROR] 未知模式：!MODE!
    echo ================================================
    echo.
    echo 可用模式：
    echo   web           - Web 界面
    echo   personal      - 个人模式
    echo   hybrid        - 混合模式
    echo   collaborative - 协同模式
    echo   check         - 检查安装
    echo   help          - 帮助信息
    echo.
    echo 使用 "start.bat help" 查看详细帮助
    echo.
    pause
    exit /b 1
)

:: ========== 错误处理 ==========
if errorlevel 1 (
    echo.
    echo ================================================
    echo [ERROR] 程序运行出错
    echo ================================================
    echo.
    echo 错误代码：!errorlevel!
    echo.
    echo 可能的问题:
    echo   1. 虚拟环境未正确激活
    echo   2. 缺少依赖包
    echo   3. 模型文件不存在
    echo.
    echo 建议操作:
    echo   1. 运行 "start.bat check" 检查安装
    echo   2. 重新运行 install.bat 安装依赖
    echo   3. 查看详细错误日志
    echo.
    pause
    exit /b 1
)
