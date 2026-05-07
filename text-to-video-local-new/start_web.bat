@echo off
setlocal enabledelayedexpansion

:: AI 视频生成器 - Web 服务启动脚本 (Windows 版)
:: 支持：CMD / PowerShell / Git Bash

echo.
echo ===============================================
echo   AI 视频生成器 - Web 服务
echo ===============================================
echo.

:: 检查 Python
echo [检查] Python 环境...
where python >nul 2>&1
if errorlevel 1 (
    where python3 >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [错误] 未找到 Python
        echo.
        echo 请先安装 Python 3.10 或更高版本:
        echo https://www.python.org/downloads/
        echo.
        echo 安装时请勾选 "Add Python to PATH"
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PY_VER=%%i
echo [OK] Python: %PY_VER%

:: 检查虚拟环境
if exist "venv\Scripts\python.exe" (
    echo [OK] 虚拟环境：已安装
    
    :: 激活虚拟环境
    call venv\Scripts\activate.bat
) else (
    echo [WARN] 虚拟环境：未安装
    echo.
    echo 提示：建议先运行 install.bat 创建虚拟环境
    echo.
)

:: 检查 Flask
echo.
echo [检查] Web 依赖...
%PYTHON_CMD% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Flask: 未安装，正在安装...
    pip install flask pillow -q
    if errorlevel 1 (
        echo [WARN] Flask: 安装失败，继续启动...
    ) else (
        echo [OK] Flask: 安装完成
    )
) else (
    echo [OK] Flask: 已安装
)

:: 启动服务
echo.
echo ===============================================
echo   启动 Web 服务
echo ===============================================
echo.
echo   访问地址:
echo     http://localhost:5000
echo     http://127.0.0.1:5000
echo.
echo   按 Ctrl+C 停止服务
echo.
echo ===============================================
echo.

cd /d "%~dp0"
%PYTHON_CMD% -m web.app

:: 错误处理
if errorlevel 1 (
    echo.
    echo ===============================================
    echo   [错误] 程序运行出错
    echo ===============================================
    echo.
    echo 可能的原因:
    echo   1. 端口 5000 被占用
    echo   2. 缺少依赖包
    echo   3. 配置文件错误
    echo.
    echo 建议:
    echo   1. 运行 start.bat check 检查安装
    echo   2. 重新运行 install.bat 安装依赖
    echo   3. 查看详细错误日志
    echo.
    pause
)
