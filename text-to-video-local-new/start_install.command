#!/bin/bash
# macOS/Linux 一键安装启动脚本

echo "============================================"
echo "  AI 视频生成器 - 一键安装"
echo "============================================"
echo ""
echo "正在检查环境..."
echo ""

# 检查 Python
if command -v python3 &> /dev/null; then
    echo "[✓] Python3 已安装"
    python3 --version
elif command -v python &> /dev/null; then
    version=$(python --version 2>&1)
    if [[ $version == *"Python 3."* ]]; then
        echo "[✓] Python 已安装"
        echo $version
    else
        echo "[!] Python 未安装"
        echo ""
        echo "正在运行 Python 安装程序..."
        bash install_python.sh
        exit $?
    fi
else
    echo "[!] Python 未安装"
    echo ""
    echo "正在运行 Python 安装程序..."
    bash install_python.sh
    exit $?
fi

echo ""
echo "============================================"
echo "  开始安装项目依赖"
echo "============================================"
echo ""

python3 -m pip install flask pillow psutil

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "  ✅ 安装完成！"
    echo "============================================"
    echo ""
    echo "正在启动应用..."
    echo ""
    python3 quick_start.py
else
    echo ""
    echo "[!] 安装失败，请检查网络连接"
    exit 1
fi
