@echo off
setlocal enabledelayedexpansion

:: AI Video Generator - Windows 一键安装脚本 (增强版)
:: 支持：CMD / PowerShell / Git Bash
:: 修复：变量作用域、错误处理、长路径支持

:: 启用长路径支持 (Windows 10 1607+)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f >nul 2>&1

echo ================================================
echo   AI Video Generator - Windows 安装程序
echo ================================================
echo.

:: ========== 配置变量 ==========
set INSTALL_DIR=%CD%
set LOG_FILE=%INSTALL_DIR%\install_log.txt
set ERROR_COUNT=0

:: 日志函数
:log
echo %~1 >> "%LOG_FILE%"
echo %~1
goto :eof

:: 错误处理函数
:check_error
if errorlevel 1 (
    log [ERROR] %~1
    set /a ERROR_COUNT+=1
    goto :eof
)
log [OK] %~1
goto :eof

:: ========== 步骤 1: 检查 Python ==========
echo.
echo [1/7] 检查 Python 环境...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo ================================================
    echo [ERROR] 未找到 Python
    echo ================================================
    echo.
    echo 请先安装 Python 3.10 或更高版本:
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选: "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
log Python %PYTHON_VER%

:: 检查 Python 版本 >= 3.10
python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARN] Python 版本低于 3.10，可能不兼容
    echo 当前版本：%PYTHON_VER%
    echo 推荐使用 Python 3.10 或更高版本
    echo.
)

:: ========== 步骤 2: 检查 pip ==========
echo.
echo [2/7] 检查 pip...
where pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 pip
    echo 请重新安装 Python 并确保勾选 pip
    pause
    exit /b 1
)
for /f "tokens=3" %%i in ('pip --version 2^>^&1') do set PIP_VER=%%i
log pip %PIP_VER%

:: ========== 步骤 3: 检测 GPU ==========
echo.
echo [3/7] 检测 GPU...
set HAS_GPU=false
set GPU_NAME=

where nvidia-smi >nul 2>&1
if errorlevel 1 (
    log 未检测到 NVIDIA GPU
) else (
    for /f "skip=1 tokens=1" %%i in ('nvidia-smi --query-gpu=name --format=csv,noheader 2^>^&1') do (
        set GPU_NAME=%%i
    )
    if not "!GPU_NAME!"=="" (
        set HAS_GPU=true
        log 检测到 NVIDIA GPU: !GPU_NAME!
        
        :: 检查显存
        for /f "skip=1 tokens=1" %%i in ('nvidia-smi --query-gpu=memory.total --format=csv,noheader 2^>^&1') do (
            set GPU_MEM=%%i
        )
        log GPU 显存：!GPU_MEM! MB
    ) else (
        log nvidia-smi 存在但无 GPU
    )
)

:: ========== 步骤 4: 检查磁盘空间 ==========
echo.
echo [4/7] 检查磁盘空间...
for /f "tokens=3" %%i in ('wmic logicaldisk where "DeviceID='%~d0'" get FreeSpace /value ^| find "FreeSpace"') do (
    set /a FREE_SPACE=%%i / 1073741824
)
log 可用磁盘空间：!FREE_SPACE! GB

if !FREE_SPACE! LSS 30 (
    echo [WARN] 磁盘空间不足 30GB，可能无法下载所有模型
) else (
    log 磁盘空间充足
)

:: ========== 步骤 5: 创建虚拟环境 ==========
echo.
echo [5/7] 创建虚拟环境...
if exist "venv" (
    echo [WARN] 虚拟环境已存在，将删除重建
    rmdir /s /q venv
    call :check_error "删除旧虚拟环境"
)

:: 创建时启用长路径
python -m venv venv --clear
call :check_error "创建虚拟环境"

:: 验证虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] 虚拟环境创建失败
    echo 请检查:
    echo   1. 磁盘空间是否充足
    echo   2. 是否有写入权限
    echo   3. 路径是否过长 (建议放在 C:\projects\)
    pause
    exit /b 1
)
log 虚拟环境创建成功

:: ========== 步骤 6: 安装 PyTorch ==========
echo.
echo [6/7] 安装 PyTorch...

:: 先升级 pip
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

:: 根据 GPU 选择版本
if "!HAS_GPU!"=="true" (
    echo [INFO] 安装 PyTorch GPU 版本 (CUDA 12.1)...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    call :check_error "安装 PyTorch GPU 版"
) else (
    echo [INFO] 安装 PyTorch CPU 版本...
    pip install torch torchvision torchaudio
    call :check_error "安装 PyTorch CPU 版"
)

:: 验证 PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}')" >nul 2>&1
call :check_error "验证 PyTorch"

:: ========== 步骤 7: 安装依赖 ==========
echo.
echo [7/7] 安装项目依赖...

:: 检查 requirements 文件
if exist "requirements-optimized.txt" (
    set REQ_FILE=requirements-optimized.txt
    echo [INFO] 使用优化配置：!REQ_FILE!
) else if exist "requirements.txt" (
    set REQ_FILE=requirements.txt
    echo [INFO] 使用标准配置：!REQ_FILE!
) else (
    echo [ERROR] 未找到 requirements 文件
    pause
    exit /b 1
)

:: 安装依赖 (捕获输出到日志)
pip install -r "!REQ_FILE!" >nul 2>&1
call :check_error "安装依赖包"

:: ========== 下载模型 ==========
echo.
echo 是否下载模型？
echo   Y - 下载模型 (推荐，需要约 10GB 空间)
echo   N - 跳过，稍后手动下载
set /p DOWNLOAD_MODELS="请输入选择 (Y/N): "

if /i "!DOWNLOAD_MODELS!"=="Y" (
    echo.
    echo 正在下载模型...
    if exist "download_models.py" (
        python download_models.py >> "!LOG_FILE!" 2>&1
        call :check_error "下载模型"
    ) else (
        echo [WARN] 未找到 download_models.py，跳过
    )
) else (
    echo [INFO] 跳过模型下载
)

:: ========== 完成 ==========
echo.
echo ================================================
if !ERROR_COUNT! GTR 0 (
    echo   安装完成 (有 !ERROR_COUNT! 个警告)
) else (
    echo   安装完成！
)
echo ================================================
echo.
echo 使用方法:
echo.
echo   1. 激活虚拟环境:
echo      call venv\Scripts\activate
echo.
echo   2. 测试运行:
echo      python generation.py --check
echo.
echo   3. 生成视频:
echo      python generation.py -m modelscope -p "一只猫在草地上奔跑" -o output.mp4
echo.
echo   4. 启动 Web 界面:
echo      python web\app.py
echo.
echo ================================================
echo 安装日志：!LOG_FILE!
echo ================================================
echo.
pause
