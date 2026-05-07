#!/bin/bash
#===============================================================================
# AI 视频生成器 - Web 服务启动脚本 (跨平台版)
# 支持：Linux / macOS / WSL / Git Bash
#===============================================================================

echo ""
echo "==============================================="
echo "  AI 视频生成器 - Web 服务"
echo "==============================================="
echo ""

# 检测操作系统 (改进版)
detect_os() {
    case "$(uname -s 2>/dev/null)" in
        "Linux")
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "WSL"
                return
            fi
            echo "Linux"
            ;;
        "Darwin")
            echo "macOS"
            ;;
        "MSYS"*|"MINGW"*)
            echo "Git Bash"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

OS=$(detect_os)
echo "操作系统：$OS"
echo ""

# 检查 Python
echo "📦 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ 错误：未找到 Python"
    echo ""
    echo "请先安装 Python 3.10 或更高版本"
    if [ "$OS" = "macOS" ]; then
        echo "  安装命令：brew install python@3.11"
    elif [ "$OS" = "Linux" ] || [ "$OS" = "WSL" ]; then
        echo "  安装命令：sudo apt install python3 python3-pip"
    fi
    echo ""
    exit 1
fi

echo "  ✓ Python: $($PYTHON_CMD --version)"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "  ✓ 虚拟环境：已安装"
    
    # 激活虚拟环境
    if [ "$OS" = "Git Bash" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
else
    echo "  ⚠️  虚拟环境：未安装"
    echo ""
    echo "提示：建议先运行安装脚本创建虚拟环境"
    if [ -f "install.sh" ]; then
        echo "  命令：bash install.sh"
    fi
    echo ""
fi

# 检查 Flask
echo ""
echo "📦 检查 Web 依赖..."
if $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "  ✓ Flask: 已安装"
else
    echo "  ⚠️  Flask: 未安装，正在安装..."
    $PYTHON_CMD -m pip install flask pillow -q
    if [ $? -eq 0 ]; then
        echo "  ✓ Flask: 安装完成"
    else
        echo "  ⚠️  Flask: 安装失败，继续启动..."
    fi
fi

# 获取 IP 地址
get_ip() {
    if [ "$OS" = "macOS" ]; then
        ipconfig getifaddr en0 2>/dev/null || echo "localhost"
    elif [ "$OS" = "Linux" ] || [ "$OS" = "WSL" ]; then
        hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost"
    else
        echo "localhost"
    fi
}

LOCAL_IP=$(get_ip)

# 启动服务
echo ""
echo "==============================================="
echo "  🚀 启动 Web 服务"
echo "==============================================="
echo ""
echo "  访问地址:"
echo "    本地：http://localhost:5000"
echo "    局域网：http://${LOCAL_IP}:5000"
echo ""
echo "  按 Ctrl+C 停止服务"
echo ""
echo "==============================================="
echo ""

# 启动 (禁用 reloader 避免某些系统问题)
cd "$(dirname "$0")"
$PYTHON_CMD -m web.app
