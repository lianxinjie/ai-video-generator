#!/bin/bash
#===============================================================================
# AI Video Generator - 智能一键安装脚本
# 根据系统扫描结果自动选择最优安装方案
#===============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印横幅
print_banner() {
    echo "==============================================="
    echo "  AI Video Generator - 智能安装程序"
    echo "==============================================="
    echo ""
}

# 检查 Python
check_python() {
    log_info "检查 Python 环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1)
    log_success "Python: $PYTHON_VERSION"
    
    # 检查版本 >= 3.10
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$PYTHON_MINOR" -lt 10 ]; then
        log_warn "Python 版本 < 3.10，可能不兼容某些功能"
    fi
}

# 检查 pip
check_pip() {
    log_info "检查 pip..."
    
    if ! command -v pip3 &> /dev/null; then
        log_error "未找到 pip3"
        exit 1
    fi
    
    PIP_VERSION=$(pip3 --version)
    log_success "pip: $PIP_VERSION"
}

# 检测系统
detect_system() {
    log_info "检测操作系统..."
    
    SYSTEM=$(uname -s)
    
    case "$SYSTEM" in
        "Darwin")
            log_success "macOS"
            IS_MACOS=true
            IS_LINUX=false
            ;;
        "Linux")
            log_success "Linux"
            IS_MACOS=false
            IS_LINUX=true
            ;;
        *)
            log_warn "未知系统: $SYSTEM，尝试继续安装"
            IS_MACOS=false
            IS_LINUX=false
            ;;
    esac
}

# 检查 GPU 驱动
check_gpu() {
    log_info "检测 GPU..."
    
    HAS_GPU=false
    
    if $IS_LINUX; then
        # 检查 NVIDIA
        if command -v nvidia-smi &> /dev/null; then
            GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "")
            if [ -n "$GPU_INFO" ]; then
                HAS_GPU=true
                log_success "检测到 NVIDIA GPU: $GPU_INFO"
            fi
        fi
    elif $IS_MACOS; then
        # 检查 Apple Silicon
        if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple M"; then
            HAS_GPU=true
            log_success "检测到 Apple Silicon (MPS 加速)"
        fi
    fi
    
    if ! $HAS_GPU; then
        log_warn "未检测到 GPU，将使用 CPU 模式"
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    # 获取可用空间 (GB)
    if $IS_MACOS || $IS_LINUX; then
        DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//g' | sed 's/M//g' | cut -d'.' -f1)
    else
        DISK_AVAIL=50  # 默认值
    fi
    
    log_info "可用磁盘空间：${DISK_AVAIL}GB"
    
    if [ "$DISK_AVAIL" -lt 30 ]; then
        log_warn "磁盘空间不足 30GB，可能无法下载所有模型"
    else
        log_success "磁盘空间充足"
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建虚拟环境..."
    
    if [ -d "venv" ]; then
        log_warn "虚拟环境已存在，将覆盖"
        rm -rf venv
    fi
    
    python3 -m venv venv
    log_success "虚拟环境创建完成"
    
    # 激活虚拟环境
    if $IS_MACOS || $IS_LINUX; then
        source venv/bin/activate
    else
        source venv/Scripts/activate
    fi
    
    log_success "虚拟环境已激活"
}

# 安装 PyTorch
install_pytorch() {
    log_info "安装 PyTorch..."
    
    # 尝试从扫描报告读取 GPU 状态
    HAS_GPU_REPORT=false
    if [ -f "scan_report.json" ]; then
        if grep -q '"gpu_available": true' scan_report.json; then
            HAS_GPU_REPORT=true
        fi
    fi
    
    if $HAS_GPU || $HAS_GPU_REPORT; then
        log_info "检测到 GPU，安装 PyTorch GPU 版本..."
        
        # 根据系统选择安装命令
        if $IS_LINUX; then
            pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        elif $IS_MACOS; then
            # macOS 使用 MPS
            pip3 install torch torchvision torchaudio
        else
            pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        fi
        
        log_success "PyTorch GPU 版本安装完成"
    else
        log_info "安装 PyTorch CPU 版本..."
        pip3 install torch torchvision torchaudio
        log_success "PyTorch CPU 版本安装完成"
    fi
}

# 安装依赖
install_dependencies() {
    log_info "安装依赖包..."
    
    # 检查使用哪个 requirements 文件
    if [ -f "requirements-optimized.txt" ]; then
        REQ_FILE="requirements-optimized.txt"
        log_info "使用优化配置文件：$REQ_FILE"
    elif [ -f "requirements.txt" ]; then
        REQ_FILE="requirements.txt"
    else
        log_error "未找到 requirements 文件"
        exit 1
    fi
    
    pip3 install -r "$REQ_FILE"
    
    log_success "依赖安装完成"
}

# 下载模型
download_models() {
    log_info "下载模型..."
    
    # 检查是否有扫描报告
    if [ -f "scan_report.json" ]; then
        log_info "从扫描报告读取推荐模型..."
        python3 download_models.py --from-scan --parallel 2
    else
        # 默认下载 ModelScope
        log_info "使用默认模型配置..."
        python3 download_models.py -m modelscope --parallel 1
    fi
}

# 测试运行
test_installation() {
    log_info "测试安装..."
    
    echo ""
    python3 generation.py --check
    
    if [ $? -eq 0 ]; then
        log_success "测试通过！"
    else
        log_warn "测试失败，但安装可能仍然可用"
    fi
}

# 主函数
main() {
    print_banner
    
    # 参数解析
    SKIP_SCAN=false
    SKIP_MODELS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-scan)
                SKIP_SCAN=true
                shift
                ;;
            --skip-models)
                SKIP_MODELS=true
                shift
                ;;
            --help|-h)
                echo "用法：bash install.sh [选项]"
                echo ""
                echo "选项:"
                echo "  --skip-scan     跳过系统扫描"
                echo "  --skip-models   跳过模型下载"
                echo "  --help, -h      显示帮助"
                exit 0
                ;;
            *)
                log_error "未知参数：$1"
                exit 1
                ;;
        esac
    done
    
    START_TIME=$(date +%s)
    
    # 步骤 1: 系统检测
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 1/6: 系统检测"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    check_python
    check_pip
    detect_system
    check_gpu
    check_disk_space
    
    # 步骤 2: 系统扫描
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 2/6: 系统扫描"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if ! $SKIP_SCAN; then
        if [ -f "scanner.py" ]; then
            log_info "运行系统扫描..."
            python3 scanner.py --generate-package --package-dir offline-package
        else
            log_warn "未找到 scanner.py，跳过扫描"
        fi
    else
        log_info "跳过系统扫描"
    fi
    
    # 步骤 3: 创建环境
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 3/6: 创建虚拟环境"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    create_venv
    
    # 步骤 4: 安装 PyTorch
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 4/6: 安装 PyTorch"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    install_pytorch
    
    # 步骤 5: 安装依赖
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 5/6: 安装依赖包"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    install_dependencies
    
    # 步骤 6: 下载模型
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "步骤 6/6: 下载模型"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if ! $SKIP_MODELS; then
        download_models
    else
        log_info "跳过模型下载"
    fi
    
    # 测试
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "执行安装测试"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    test_installation
    
    # 完成
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "==============================================="
    log_success "安装完成！"
    echo "==============================================="
    echo ""
    echo "总耗时：$((DURATION / 60)) 分 $((DURATION % 60)) 秒"
    echo ""
    echo "使用方法:"
    echo "  1. 激活虚拟环境:"
    if $IS_MACOS || $IS_LINUX; then
        echo "     source venv/bin/activate"
    else
        echo "     venv\\Scripts\\activate"
    fi
    echo ""
    echo "  2. 测试运行:"
    echo "     python3 generation.py --check"
    echo ""
    echo "  3. 生成视频:"
    echo "     python3 generation.py -m modelscope -p \"一只猫在草地上奔跑\" -o output.mp4"
    echo ""
    echo "==============================================="
    echo ""
}

# 执行
main "$@"
