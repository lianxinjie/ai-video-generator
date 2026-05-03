#!/bin/bash

echo "============================================"
echo "  AI 视频生成器 - Python 一键安装"
echo "============================================"
echo ""

# 检查是否已安装 Python
if command -v python3 &> /dev/null; then
    echo "[✓] Python3 已安装:"
    python3 --version
    echo ""
    read -p "按回车键退出..."
    exit 0
fi

if command -v python &> /dev/null; then
    version=$(python --version 2>&1)
    if [[ $version == *"Python 3."* ]]; then
        echo "[✓] Python 已安装:"
        echo $version
        echo ""
        read -p "按回车键退出..."
        exit 0
    fi
fi

echo "[!] 未检测到 Python 3，开始自动安装..."
echo ""

# 检测操作系统
OS="$(uname -s)"

case "$OS" in
    Darwin)
        echo "[1/2] 检测到 macOS，使用 Homebrew 安装..."
        if command -v brew &> /dev/null; then
            echo "[→] 发现 Homebrew，正在安装 Python 3.11..."
            brew install python@3.11
            if [ $? -eq 0 ]; then
                echo "[✓] Python 安装成功!"
                echo ""
                echo "请重新运行：python3 quick_start.py"
                exit 0
            fi
        else
            echo "[!] Homebrew 未安装"
            echo ""
            echo "请先安装 Homebrew:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo ""
            echo "或者手动安装 Python:"
            echo "  访问：https://www.python.org/downloads/macos/"
            open "https://www.python.org/downloads/macos/"
            exit 1
        fi
        ;;
    
    Linux)
        # 检测包管理器
        if command -v apt-get &> /dev/null; then
            echo "[1/2] 检测到 Ubuntu/Debian，使用 apt 安装..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
            if [ $? -eq 0 ]; then
                echo "[✓] Python 安装成功!"
                echo ""
                python3 --version
                echo ""
                echo "请重新运行：python3 quick_start.py"
                exit 0
            fi
        elif command -v yum &> /dev/null; then
            echo "[1/2] 检测到 CentOS/RHEL，使用 yum 安装..."
            sudo yum install -y python3 python3-pip
            if [ $? -eq 0 ]; then
                echo "[✓] Python 安装成功!"
                echo ""
                python3 --version
                echo ""
                echo "请重新运行：python3 quick_start.py"
                exit 0
            fi
        elif command -v dnf &> /dev/null; then
            echo "[1/2] 检测到 Fedora，使用 dnf 安装..."
            sudo dnf install -y python3 python3-pip
            if [ $? -eq 0 ]; then
                echo "[✓] Python 安装成功!"
                echo ""
                python3 --version
                echo ""
                echo "请重新运行：python3 quick_start.py"
                exit 0
            fi
        else
            echo "[!] 未检测到支持的包管理器"
            echo ""
            echo "请手动安装 Python:"
            echo "  Ubuntu/Debian: sudo apt install python3"
            echo "  CentOS/RHEL: sudo yum install python3"
            echo "  Fedora: sudo dnf install python3"
            exit 1
        fi
        ;;
    
    *)
        echo "[!] 未知操作系统：$OS"
        echo ""
        echo "请手动安装 Python:"
        echo "  访问：https://www.python.org/downloads/"
        exit 1
        ;;
esac

echo "[!] 自动安装失败，请手动安装"
echo ""
echo "访问：https://www.python.org/downloads/"
exit 1
