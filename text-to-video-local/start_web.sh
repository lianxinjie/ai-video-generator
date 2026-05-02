#!/bin/bash
# AI 视频生成器 - Web 服务启动脚本

echo ""
echo "================================================================"
echo "  AI 视频生成器 - Web 服务"
echo "================================================================"
echo ""

# 检查并安装依赖
echo "📦 检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "  → 安装 Flask..."
    pip3 install flask
fi

if ! python3 -c "from PIL import Image" 2>/dev/null; then
    echo "  → 安装 Pillow (图片处理)..."
    pip3 install pillow
fi

# 启动 Web 服务
echo "🚀 启动 Web 服务..."
echo ""
echo "访问地址：http://localhost:5000"
echo "API 文档：http://localhost:5000/api/docs (待实现)"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd "$(dirname "$0")"
python3 web/app.py
