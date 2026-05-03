@echo off
setlocal enabledelayedexpansion

:: AI Video Generator - Windows 一键安装脚本
:: PowerShell/CMD双支持

echo ================================================
echo   AI Video Generator - Windows 安装程序
echo ================================================
echo.

:: 检查 Python
echo [1/6] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: 检查 pip
echo [2/6] 检查 pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 pip
    pause
    exit /b 1
)
pip --version
echo.

:: 检测 GPU
echo [3/6] 检测 GPU...
set HAS_GPU=false
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [INFO] 未检测到 NVIDIA GPU，将使用 CPU 模式
) else (
    echo [OK] 检测到 NVIDIA GPU
    set HAS_GPU=true
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)
echo.

:: 创建虚拟环境
echo [4/6] 创建虚拟环境...
if exist "venv" (
    echo [WARN] 虚拟环境已存在，将删除重建
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo [ERROR] 创建虚拟环境失败
    pause
    exit /b 1
)
echo [OK] 虚拟环境创建完成
echo.

:: 激活虚拟环境
echo [5/6] 安装依赖...
call venv\Scripts\activate.bat

if "%HAS_GPU%"=="true" (
    echo [INFO] 安装 PyTorch GPU 版本...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [INFO] 安装 PyTorch CPU 版本...
    pip install torch torchvision torchaudio
)

echo [INFO] 安装项目依赖...
if exist "requirements-optimized.txt" (
    pip install -r requirements-optimized.txt
) else if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [ERROR] 未找到 requirements 文件
    pause
    exit /b 1
)
echo.

:: 下载模型
echo [6/6] 下载模型...
if exist "download_models.py" (
    python download_models.py
) else (
    echo [WARN] 跳过模型下载
)
echo.

:: 完成
echo ================================================
echo   安装完成！
echo ================================================
echo.
echo 使用方法:
echo   1. 激活虚拟环境:
echo      call venv\Scripts\activate
echo.
echo   2. 测试运行:
echo      python generation.py --check
echo.
echo   3. 生成视频:
echo      python generation.py -m modelscope -p "提示词" -o output.mp4
echo.
echo ================================================
pause
