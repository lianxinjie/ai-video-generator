#!/bin/bash

# Text-to-Video Local Deployment
# 快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python3，请先安装 Python 3.10 或更高版本"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 版本：$PYTHON_VERSION"
}

# 检查 CUDA
check_cuda() {
    print_info "检查 CUDA 环境..."
    if ! command -v nvidia-smi &> /dev/null; then
        print_warning "未找到 nvidia-smi，将使用 CPU 模式运行（速度较慢）"
        return 1
    else
        echo "GPU 信息:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        return 0
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "创建 Python 虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    else
        print_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
}

# 安装依赖
install_deps() {
    print_info "安装 Python 依赖..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到 requirements.txt"
        exit 1
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "依赖安装完成"
}

# 创建必要目录
create_dirs() {
    print_info "创建必要目录..."
    mkdir -p models outputs
    
    print_success "目录创建完成"
}

# 检查环境
check_env() {
    print_info "运行环境检查..."
    python3 generation.py check
    
    if [ $? -eq 0 ]; then
        print_success "环境检查通过"
    else
        print_error "环境检查失败"
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "使用方法:"
    echo ""
    echo "  $0 [command]"
    echo ""
    echo "可用命令:"
    echo "  setup     安装环境和依赖"
    echo "  check     检查系统环境"
    echo "  generate  生成视频（需要额外参数）"
    echo "  demo      运行示例生成"
    echo "  clean     清理缓存"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 setup"
    echo "  $0 generate --model modelscope --prompt '一只小猫' --output test.mp4"
    echo "  $0 demo"
    echo ""
}

# 运行示例生成
run_demo() {
    print_info "运行示例生成..."
    
    python3 generation.py generate \
        --model modelscope \
        --prompt "一只可爱的小猫在草地上玩耍" \
        --output outputs/demo_$(date +%Y%m%d_%H%M%S).mp4 \
        --duration 3 \
        --height 256 \
        --width 256
    
    print_success "示例生成完成，视频保存在 outputs/ 目录"
}

# 清理缓存
clean_cache() {
    print_info "清理缓存..."
    
    rm -rf __pycache__
    rm -rf venv
    rm -rf outputs/*.mp4
    
    print_success "清理完成"
}

# 主函数
main() {
    case "$1" in
        setup)
            print_info "开始安装环境..."
            check_python
            check_cuda
            create_venv
            install_deps
            create_dirs
            check_env
            print_success "环境安装完成！"
            echo ""
            print_info "使用方法:"
            echo "  source venv/bin/activate"
            echo "  python generation.py generate --model modelscope --prompt '你的提示词' --output test.mp4"
            ;;
        
        check)
            check_python
            check_cuda
            check_env
            ;;
        
        generate)
            if [ ! -d "venv" ]; then
                print_error "虚拟环境不存在，请先运行: $0 setup"
                exit 1
            fi
            source venv/bin/activate
            shift
            python3 generation.py generate "$@"
            ;;
        
        demo)
            if [ ! -d "venv" ]; then
                print_error "虚拟环境不存在，请先运行: $0 setup"
                exit 1
            fi
            source venv/bin/activate
            create_dirs
            run_demo
            ;;
        
        clean)
            clean_cache
            ;;
        
        help|--help|-h)
            show_help
            ;;
        
        *)
            if [ -n "$1" ]; then
                print_error "未知命令：$1"
            fi
            show_help
            ;;
    esac
}

# 运行主函数
main "$@"
