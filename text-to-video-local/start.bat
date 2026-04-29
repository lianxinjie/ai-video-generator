@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Text-to-Video Local Deployment
REM 快速启动脚本 (Windows 版本)

set "PYTHON_EXE=python"
set "VENV_DIR=venv"

echo ========================================
echo Text-to-Video Local Deployment
echo Windows 快速启动脚本
echo ========================================
echo.

:menu
echo 请选择要执行的操作:
echo.
echo  1. 安装环境和依赖
echo  2. 检查系统环境
echo  3. 生成视频
echo  4. 运行示例
echo  5. 清理缓存
echo  6. 退出
echo.
set /p "choice=请输入选项 (1-6): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto check
if "%choice%"=="3" goto generate
if "%choice%"=="4" goto demo
if "%choice%"=="5" goto clean
if "%choice%"=="6" goto end

echo 无效的选项，请重新输入
echo.
goto menu

:setup
echo.
echo [安装环境]
echo.

REM 检查 Python
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10 或更高版本
    pause
    goto menu
)

echo [信息] Python 已安装
%PYTHON_EXE% --version

REM 创建虚拟环境
if not exist "%VENV_DIR%" (
    echo [信息] 创建虚拟环境...
    %PYTHON_EXE% -m venv %VENV_DIR%
    echo [成功] 虚拟环境创建完成
) else (
    echo [信息] 虚拟环境已存在
)

REM 激活虚拟环境
call %VENV_DIR%\Scripts\activate.bat

REM 安装依赖
echo [信息] 安装 Python 依赖...
pip install --upgrade pip
pip install -r requirements.txt
echo [成功] 依赖安装完成

REM 创建目录
if not exist "models" mkdir models
if not exist "outputs" mkdir outputs
echo [成功] 目录创建完成

echo.
echo [成功] 环境安装完成!
echo.
echo 使用方法:
echo   call venv\Scripts\activate.bat
echo   python generation.py generate --model modelscope --prompt "你的提示词" --output test.mp4
echo.
pause
goto menu

:check
echo.
echo [检查环境]
echo.

call %VENV_DIR%\Scripts\activate.bat 2>nul
python generation.py check

echo.
pause
goto menu

:generate
echo.
echo [生成视频]
echo.

if not exist "%VENV_DIR%" (
    echo [错误] 虚拟环境不存在，请先运行安装
    pause
    goto menu
)

call %VENV_DIR%\Scripts\activate.bat

echo 请输入提示词:
set /p "prompt=提示词： "

echo 请选择模型:
echo   1. modelscope (推荐，支持中文)
echo   2. animatediff (动漫风格)
echo   3. cogvideox (高质量)
set /p "model_choice=模型 (1-3): "

if "%model_choice%"=="1" set "model=modelscope"
if "%model_choice%"=="2" set "model=animatediff"
if "%model_choice%"=="3" set "model=cogvideox"

set /p "duration=时长 (秒，默认 3): "
if "%duration%"=="" set "duration=3"

set "timestamp=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "timestamp=%timestamp: =0%"
set "output=outputs/video_%timestamp%.mp4"

echo.
echo [信息] 开始生成视频...
python generation.py generate --model %model% --prompt "%prompt%" --output %output% --duration %duration%

if errorlevel 1 (
    echo [错误] 生成失败
) else (
    echo [成功] 生成完成！视频保存到：%output%
)

echo.
pause
goto menu

:demo
echo.
echo [运行示例]
echo.

if not exist "%VENV_DIR%" (
    echo [错误] 虚拟环境不存在，请先运行安装
    pause
    goto menu
)

call %VENV_DIR%\Scripts\activate.bat

if not exist "outputs" mkdir outputs

echo [信息] 生成示例视频...
python generation.py generate ^
    --model modelscope ^
    --prompt "一只可爱的小猫在草地上玩耍" ^
    --output outputs/demo.mp4 ^
    --duration 3 ^
    --height 256 ^
    --width 256

echo [成功] 示例生成完成!
echo 视频保存在：outputs\demo.mp4
echo.
pause
goto menu

:clean
echo.
echo [清理缓存]
echo.

if exist "__pycache__" rmdir /s /q __pycache__
echo [已清理] __pycache__

if exist "outputs" (
    echo [提示] 是否删除 outputs 目录下的所有 mp4 文件？(Y/N)
    set /p "del_confirm="
    if /i "!del_confirm!"=="Y" (
        del /q outputs\*.mp4
        echo [已清理] outputs\*.mp4
    )
)

echo [成功] 清理完成
echo.
pause
goto menu

:end
echo.
echo 再见!
echo.
exit /b 0
