@echo off
chcp 65001 >nul
echo ============================================
echo   AI 视频生成器 - Python 一键安装
echo ============================================
echo.

REM 检查是否已安装 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Python 已安装:
    python --version
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 0
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Python3 已安装:
    python3 --version
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 0
)

echo [!] 未检测到 Python，开始自动安装...
echo.

REM 方法 1: 尝试使用 winget (Windows 10/11)
echo [1/3] 尝试使用 winget 安装...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo [→] 发现 winget，正在安装 Python 3.11...
    winget install Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
    if %errorlevel% equ 0 (
        echo [✓] Python 安装成功!
        echo.
        echo 请重新打开此页面或刷新即可
        pause
        exit /b 0
    )
)

REM 方法 2: 使用官方安装器
echo [2/3] winget不可用，将下载官方安装器...
echo.
echo [→] 正在下载 Python 安装器...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'}"
if %errorlevel% equ 0 (
    echo [✓] 下载完成，正在安装...
    echo.
    echo [!] 安装程序即将启动
    echo [!] 请确保勾选 "Add Python to PATH"
    echo.
    timeout /t 3 /nobreak >nul
    start "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    echo [→] 安装程序已启动，请稍候...
    echo.
    echo 安装完成后请重新运行 quick_start.py
    pause
    exit /b 0
)

REM 方法 3: 手动安装
echo [3/3] 自动安装失败，请手动安装:
echo.
echo 1. 访问：https://www.python.org/downloads/
echo 2. 下载 Python 3.11 或更高版本
echo 3. 运行安装程序
echo 4. **重要**: 勾选 "Add Python to PATH"
echo 5. 点击 "Install Now"
echo.
start https://www.python.org/downloads/
echo 已在浏览器中打开下载页面
echo.
pause
