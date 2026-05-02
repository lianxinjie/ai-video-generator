#!/bin/bash
# AI 视频生成器 - Web 服务启动脚本

echo ""
echo "================================================================"
echo "  AI 视频生成器 - Web 服务"
echo "================================================================"
echo ""

# 检查 Flask 是否安装
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠ 检测到 Flask 未安装，正在安装..."
    pip3 install flask
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
