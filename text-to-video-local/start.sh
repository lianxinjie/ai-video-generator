#!/bin/bash
#===============================================================================
# AI Video Generator - 跨平台统一启动脚本
# 支持：Linux / macOS / Windows (Git Bash) / WSL
#===============================================================================

set -e

# 检测操作系统
detect_os() {
    OS=$(uname -s 2>/dev/null || echo "Windows")
    case "$OS" in
        "Linux")    OS_NAME="linux";;
        "Darwin")   OS_NAME="macos";;
        *)          OS_NAME="windows";;
    esac
    echo "检测到操作系统：$OS_NAME ($OS)"
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        echo "❌ 虚拟环境不存在，请先运行安装脚本"
        echo "   Linux/macOS: bash install.sh"
        echo "   Windows: install.bat"
        exit 1
    fi
    echo "✅ 虚拟环境存在"
}

# 激活虚拟环境
activate_venv() {
    echo "激活虚拟环境..."
    if [ "$OS_NAME" = "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    echo "✅ 虚拟环境已激活"
}

# 检查依赖
check_dependencies() {
    echo "检查关键依赖..."
    
    # Python
    if ! command -v python &> /dev/null; then
        echo "❌ Python 未找到"
        exit 1
    fi
    echo "   ✅ Python: $(python --version)"
    
    # FFmpeg (警告但不阻止)
    if ! command -v ffmpeg &> /dev/null; then
        echo "   ⚠️  FFmpeg 未安装 (部分功能不可用)"
    else
        echo "   ✅ FFmpeg: $(ffmpeg -version | head -1)"
    fi
}

# 启动服务
start_service() {
    MODE=${1:-web}
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  启动服务：$MODE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    case "$MODE" in
        web)
            echo "启动 Web 服务..."
            python web/app.py
            ;;
        personal)
            echo "启动个人模式..."
            python personal_mode/run.py -m personal "$@"
            ;;
        hybrid)
            echo "启动混合模式..."
            python personal_mode/run.py -m hybrid "$@"
            ;;
        collaborative)
            echo "启动协同模式..."
            python personal_mode/run.py -m collaborative "$@"
            ;;
        check)
            echo "检查安装..."
            python generation.py --check
            ;;
        *)
            echo "未知模式：$MODE"
            echo "可用模式：web, personal, hybrid, collaborative, check"
            exit 1
            ;;
    esac
}

# 显示帮助
show_help() {
    echo "AI Video Generator - 启动脚本"
    echo ""
    echo "用法：bash start.sh [模式] [参数]"
    echo ""
    echo "模式:"
    echo "  web           启动 Web 界面 (默认)"
    echo "  personal      个人模式"
    echo "  hybrid        混合模式"
    echo "  collaborative 协同模式"
    echo "  check         检查安装"
    echo ""
    echo "示例:"
    echo "  bash start.sh web                    # 启动 Web 服务"
    echo "  bash start.sh hybrid -p '提示词'     # 混合模式生成"
    echo "  bash start.sh check                  # 检查安装状态"
    echo ""
    echo "跨平台支持:"
    echo "  ✅ Linux:      bash start.sh"
    echo "  ✅ macOS:      bash start.sh"
    echo "  ✅ Windows:    bash start.sh (Git Bash)"
    echo "  ✅ Windows:    .\\start.bat (CMD/PowerShell)"
}

# 主程序
main() {
    echo "==============================================="
    echo "  AI Video Generator - 启动脚本"
    echo "==============================================="
    echo ""
    
    # 帮助
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # 检测和启动
    detect_os
    check_venv
    activate_venv
    check_dependencies
    start_service "$@"
}

main "$@"
