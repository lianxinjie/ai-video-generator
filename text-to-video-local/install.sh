#!/bin/bash
#===============================================================================
# AI Video Generator - 智能一键安装脚本 (增强版)
# 支持：Linux / macOS / WSL / Git Bash
# 改进：GPU 检测、错误处理、Homebrew 检查
#===============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 错误处理
trap 'log_error "安装失败，请检查日志"; exit 1' ERR

# 打印横幅
print_banner() {
    echo "==============================================="
    echo "  AI Video Generator - 智能安装程序"
    echo "==============================================="
    echo ""
}

# ========== 步骤 1: 系统检测 ==========
echo ""
log_info "步骤 1/8: 系统检测"
echo "-----------------------------------------------"

# 检测操作系统
IS_MACOS=false
IS_LINUX=false
IS_WSL=false

case "$(uname -s)" in
    "Darwin")
        IS_MACOS=true
        log_success "macOS"
        ;;
    "Linux")
        IS_LINUX=true
        # 检测 WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            IS_WSL=true
            log_success "WSL (Windows Subsystem for Linux)"
        else
            log_success "Linux"
        fi
        ;;
    *)
        # Git Bash on Windows
        if [[ "$OSTYPE" == "msys" ]]; then
            log_warn "检测到 Git Bash，建议使用 install.bat"
        else
            log_warn "未知系统：$(uname -s)"
        fi
        ;;
esac

# ========== 步骤 2: 检查 Python ==========
echo ""
log_info "步骤 2/8: 检查 Python"
echo "-----------------------------------------------"

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log_error "未找到 Python"
    echo ""
    if $IS_MACOS; then
        echo "macOS 安装方法:"
        echo "  brew install python@3.11"
    elif $IS_LINUX; then
        echo "Linux 安装方法:"
        echo "  sudo apt install python3 python3-pip  # Ubuntu/Debian"
        echo "  sudo yum install python3 python3-pip  # CentOS/RHEL"
    fi
    echo ""
    exit 1
fi

PYTHON_CMD=$(command -v python3 &> /dev/null && echo "python3" || echo "python")
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log_success "$PYTHON_VERSION"

# 检查版本 >= 3.10
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "9")
if [ "$PYTHON_MINOR" -lt 10 ]; then
    log_warn "Python 版本 < 3.10，可能不兼容某些功能"
fi

# ========== 步骤 3: 检查 pip ==========
echo ""
log_info "步骤 3/8: 检查 pip"
echo "-----------------------------------------------"

if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    log_error "未找到 pip"
    exit 1
fi

PIP_CMD=$(command -v pip3 &> /dev/null && echo "pip3" || echo "pip")
log_success "$($PIP_CMD --version)"

# ========== 步骤 4: macOS Homebrew 检查 ==========
if $IS_MACOS; then
    echo ""
    log_info "步骤 4/8: 检查 Homebrew (macOS)"
    echo "-----------------------------------------------"
    
    if ! command -v brew &> /dev/null; then
        log_warn "Homebrew 未安装"
        echo ""
        echo "建议安装 Homebrew:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
    else
        log_success "Homebrew 已安装"
        
        # 检查并安装 FFmpeg
        if ! command -v ffmpeg &> /dev/null; then
            log_info " FFmpeg 未安装，正在安装..."
            brew install ffmpeg || log_warn "FFmpeg 安装失败，可手动安装"
        else
            log_success "FFmpeg 已安装"
        fi
    fi
fi

# ========== 步骤 5: GPU 检测 ==========
echo ""
log_info "步骤 5/8: 检测 GPU"
echo "-----------------------------------------------"

HAS_GPU=false
GPU_TYPE=""

if $IS_LINUX; then
    # 检查 NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        NVIDIA_OUTPUT=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "")
        if [ -n "$NVIDIA_OUTPUT" ] && ! echo "$NVIDIA_OUTPUT" | grep -q "NVIDIA-SMI has failed"; then
            HAS_GPU=true
            GPU_TYPE="NVIDIA"
            log_success "检测到 NVIDIA GPU: $NVIDIA_OUTPUT"
        fi
    fi
    
    # 检查 NVIDIA 驱动是否加载
    if [ -d "/proc/driver/nvidia" ]; then
        log_success "NVIDIA 驱动已加载"
    fi
    
elif $IS_MACOS; then
    # 检查 Apple Silicon
    if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple M[1-9]"; then
        HAS_GPU=true
        GPU_TYPE="Apple Silicon"
        log_success "检测到 Apple Silicon (MPS 加速)"
    else
        # Intel Mac
        log_info "Intel Mac (无 GPU 加速)"
    fi
fi

if ! $HAS_GPU; then
    log_warn "未检测到 GPU，将使用 CPU 模式"
fi

# ========== 步骤 6: 检查磁盘空间 ==========
echo ""
log_info "步骤 6/8: 检查磁盘空间"
echo "-----------------------------------------------"

if $IS_MACOS || $IS_LINUX || $IS_WSL; then
    DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//g' | sed 's/M//g' | cut -d'.' -f1)
    log_info "可用磁盘空间：${DISK_AVAIL}GB"
    
    if [ "${DISK_AVAIL:-0}" -lt 30 ]; then
        log_warn "磁盘空间不足 30GB，可能无法下载所有模型"
    else
        log_success "磁盘空间充足"
    fi
fi

# ========== 步骤 7: 创建虚拟环境 ==========
echo ""
log_info "步骤 7/8: 创建虚拟环境"
echo "-----------------------------------------------"

if [ -d "venv" ]; then
    log_warn "虚拟环境已存在，将覆盖"
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
log_success "虚拟环境创建完成"

# 激活虚拟环境
if $IS_MACOS || $IS_LINUX || $IS_WSL; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi
log_success "虚拟环境已激活"

# 升级 pip
pip install --upgrade pip -q
log_success "pip 已升级"

# ========== 步骤 8: 安装依赖 ==========
echo ""
log_info "步骤 8/8: 安装依赖"
echo "-----------------------------------------------"

# 安装 PyTorch
log_info "安装 PyTorch..."

if [ "$HAS_GPU" = true ]; then
    if [ "$GPU_TYPE" = "NVIDIA" ]; then
        log_info "检测到 NVIDIA GPU，安装 CUDA 版本..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    elif [ "$GPU_TYPE" = "Apple Silicon" ]; then
        log_info "检测到 Apple Silicon，安装 MPS 版本..."
        pip install torch torchvision torchaudio
    fi
else
    log_info "安装 CPU 版本..."
    pip install torch torchvision torchaudio
fi

# 验证 PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}')" && log_success "PyTorch 安装成功" || log_warn "PyTorch 验证失败"

# 安装项目依赖
if [ -f "requirements-optimized.txt" ]; then
    REQ_FILE="requirements-optimized.txt"
    log_info "使用优化配置：$REQ_FILE"
elif [ -f "requirements.txt" ]; then
    REQ_FILE="requirements.txt"
    log_info "使用标准配置：$REQ_FILE"
else
    log_error "未找到 requirements 文件"
    exit 1
fi

pip install -r "$REQ_FILE" && log_success "依赖安装完成" || log_warn "依赖安装部分失败"

# ========== 下载模型 (可选) ==========
echo ""
read -p "是否下载模型？(Y/N, 默认 Y): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [ -z "$REPLY" ]; then
    log_info "下载模型..."
    if [ -f "download_models.py" ]; then
        python download_models.py || log_warn "模型下载失败"
    else
        log_warn "未找到 download_models.py"
    fi
else
    log_info "跳过模型下载"
fi

# ========== 测试安装 ==========
echo ""
log_info "测试安装..."
echo "-----------------------------------------------"

python generation.py --check 2>&1 | head -20 || log_warn "测试失败，但安装可能仍然可用"

# ========== 完成 ==========
echo ""
echo "==============================================="
log_success "安装完成！"
echo "==============================================="
echo ""
echo "使用方法:"
echo ""
echo "  1. 激活虚拟环境:"
if $IS_MACOS || $IS_LINUX || $IS_WSL; then
    echo "     source venv/bin/activate"
else
    echo "     source venv/Scripts/activate"
fi
echo ""
echo "  2. 测试运行:"
echo "     python generation.py --check"
echo ""
echo "  3. 启动 Web 界面:"
echo "     python web/app.py"
echo ""
echo "  4. 生成视频:"
echo "     python generation.py -m modelscope -p \"一只猫在草地上奔跑\" -o output.mp4"
echo ""
echo "==============================================="
echo ""
