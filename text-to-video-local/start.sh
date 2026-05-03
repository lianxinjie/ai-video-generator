#!/bin/bash
#===============================================================================
# AI Video Generator - 跨平台统一启动脚本 (增强版)
# 支持：Linux / macOS / Windows (Git Bash) / WSL
# 改进：错误处理、参数传递、虚拟环境验证
#===============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 错误处理
handle_error() {
    log_error "$1"
    echo ""
    echo "建议操作:"
    echo "  1. 运行 'bash start.sh check' 检查安装"
    echo "  2. 重新运行 install.sh 安装依赖"
    echo ""
    exit 1
}

# 检测操作系统
detect_os() {
    OS=$(uname -s 2>/dev/null || echo "Windows")
    case "$OS" in
        "Linux")
            OS_NAME="linux"
            if grep -qi microsoft /proc/version 2>/dev/null; then
                OS_NAME="wsl"
            fi
            ;;
        "Darwin")   OS_NAME="macos";;
        "MSYS"*|"MINGW"*) OS_NAME="windows";;
        *)          OS_NAME="unknown";;
    esac
    log_info "操作系统：$OS_NAME ($OS)"
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        log_error "虚拟环境不存在"
        echo ""
        echo "请先运行安装脚本:"
        echo "  Linux/macOS: bash install.sh"
        echo "  Windows: install.bat"
        echo ""
        exit 1
    fi
    log_success "虚拟环境存在"
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    
    if [ "$OS_NAME" = "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # 验证激活
    if ! command -v python &> /dev/null; then
        handle_error "虚拟环境激活失败"
    fi
    log_success "虚拟环境已激活"
}

# 检查依赖
check_dependencies() {
    log_info "检查关键依赖..."
    
    # Python
    PYTHON_VER=$(python --version 2>&1)
    log_success "Python: $PYTHON_VER"
    
    # FFmpeg (警告但不阻止)
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1)
        log_success "FFmpeg: $FFMPEG_VER"
    else
        log_warn "FFmpeg 未安装 (部分功能不可用)"
        if [ "$OS_NAME" = "macos" ]; then
            echo "   安装方法：brew install ffmpeg"
        elif [ "$OS_NAME" = "linux" ] || [ "$OS_NAME" = "wsl" ]; then
            echo "   安装方法：sudo apt install ffmpeg"
        fi
    fi
    
    # PyTorch
    python -c "import torch; print(f'   PyTorch: {torch.__version__}')" 2>/dev/null || log_warn "PyTorch 未安装"
}

# 启动服务
start_service() {
    MODE=${1:-web}
    shift || true
    ARGS="$@"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  启动服务：$MODE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    case "$MODE" in
        web)
            log_info "启动 Web 服务..."
            log_info "访问地址：http://localhost:5000"
            echo ""
            python web/app.py
            ;;
        personal)
            log_info "启动个人模式..."
            python personal_mode/run.py -m personal $ARGS
            ;;
        hybrid)
            log_info "启动混合模式..."
            python personal_mode/run.py -m hybrid $ARGS
            ;;
        collaborative)
            log_info "启动协同模式..."
            python personal_mode/run.py -m collaborative $ARGS
            ;;
        check)
            log_info "检查安装..."
            python generation.py --check
            ;;
        scan)
            log_info "系统扫描..."
            if [ -f "scanner.py" ]; then
                python scanner.py
            else
                log_warn "未找到 scanner.py"
            fi
            ;;
        help|-h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知模式：$MODE"
            echo ""
            echo "可用模式:"
            echo "  web           - 启动 Web 界面 (默认)"
            echo "  personal      - 个人模式"
            echo "  hybrid        - 混合模式"
            echo "  collaborative - 协同模式"
            echo "  check         - 检查安装"
            echo "  scan          - 系统扫描"
            echo ""
            echo "使用 'bash start.sh help' 查看详细帮助"
            echo ""
            exit 1
            ;;
    esac
}

# 显示帮助
show_help() {
    echo ""
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
    echo "  scan          系统扫描"
    echo ""
    echo "示例:"
    echo "  bash start.sh web                    # 启动 Web 服务"
    echo "  bash start.sh hybrid -p '提示词'     # 混合模式生成"
    echo "  bash start.sh check                  # 检查安装状态"
    echo "  bash start.sh scan                   # 扫描系统配置"
    echo ""
    echo "跨平台支持:"
    echo "  ✅ Linux:      bash start.sh"
    echo "  ✅ macOS:      bash start.sh"
    echo "  ✅ Windows:    bash start.sh (Git Bash)"
    echo "  ✅ WSL:        bash start.sh"
    echo ""
}

# 主程序
main() {
    echo "==============================================="
    echo "  AI Video Generator - 启动脚本"
    echo "==============================================="
    echo ""
    
    detect_os
    check_venv
    activate_venv
    check_dependencies
    start_service "$@"
}

main "$@"
