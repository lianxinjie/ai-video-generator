@echo off
chcp 65001 >nul
title AI 视频生成器 - 一键安装

:: 输出到日志文件
set LOGFILE=install_progress.log
echo AI 视频生成器 - 安装进度 > %LOGFILE%
echo 开始时间：%date% %time% >> %LOGFILE%
echo ============================================ >> %LOGFILE%

:: 使用 more 显示进度
cls
echo ============================================
echo   AI 视频生成器 - 一键安装
echo ============================================
echo.

echo [1/4] 正在检查 Python 环境...
echo [1/4] 正在检查 Python 环境... >> %LOGFILE%
timeout /t 1 >nul

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    echo [✓] Python 已安装：%PYVER%
    echo [✓] Python 已安装：%PYVER% >> %LOGFILE%
    goto :check_deps
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python3 --version 2^>^&1') do set PYVER=%%i
    echo [✓] Python3 已安装：%PYVER%
    echo [✓] Python3 已安装：%PYVER% >> %LOGFILE%
    goto :check_deps
)

:: Python 未安装，运行安装脚本
echo [!] Python 未安装，正在安装...
echo [!] Python 未安装，正在安装... >> %LOGFILE%
timeout /t 2 >nul
call install_python.bat
if %errorlevel% neq 0 (
    echo [!] Python 安装失败，按回车键退出... >> %LOGFILE%
    echo [!] Python 安装失败
    pause
    exit /b 1
)

:check_deps
echo.
echo [2/4] 正在安装项目依赖...
echo [2/4] 正在安装项目依赖... >> %LOGFILE%

:: 安装依赖
echo 正在执行：pip install flask pillow psutil >> %LOGFILE%
pip install flask pillow psutil 2>&1 | tee -a %LOGFILE%

if %errorlevel% neq 0 (
    echo.
    echo [!] 依赖安装失败
    echo [!] 依赖安装失败 >> %LOGFILE%
    echo 完成时间：%date% %time% >> %LOGFILE%
    echo.
    echo 按回车键退出...
    pause
    exit /b 1
)

echo.
echo [✓] 依赖安装完成
echo [✓] 依赖安装完成 >> %LOGFILE%
timeout /t 1 >nul

echo.
echo [3/4] 安装完成！
echo [✓] 安装完成！ >> %LOGFILE%
timeout /t 1 >nul

echo.
echo ============================================
echo   正在启动应用...
echo ============================================
echo 正在启动应用... >> %LOGFILE%
echo 完成时间：%date% %time% >> %LOGFILE%
timeout /t 2 >nul

:: 启动应用
python quick_start.py
if %errorlevel% neq 0 (
    echo [!] 应用启动失败 >> %LOGFILE%
)

:: 如果应用退出，保持窗口打开
echo.
echo ============================================
echo   应用已退出
echo ============================================
echo.
echo 按回车键关闭窗口...
pause >nul
