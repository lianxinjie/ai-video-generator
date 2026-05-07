#!/bin/bash
# Windows PowerShell 快速修复脚本

echo "======================================================="
echo " AI 视频生成器 - Windows 环境快速修复"
echo "======================================================="
echo ""

# 检查 Python
python --version || { echo "❌ Python 未安装"; exit 1; }

# 检查虚拟环境
if [ -f "venv/Scripts/activate" ]; then
    echo "✅ 发现虚拟环境，激活它"
    source venv/Scripts/activate
fi

# 安装依赖
echo ""
echo "安装 Python 依赖..."
pip install flask pillow psutil requests --quiet --break-system-packages

# 运行诊断
echo ""
echo "运行路由诊断..."
python diagnose_routes.py

echo ""
echo "======================================================="
echo " 启动命令:"
echo "  python web/app.py"
echo "======================================================="
echo ""
echo "然后在浏览器访问：http://127.0.0.1:5000/setup"
echo "点击'开始安装依赖'按钮"
echo ""
echo "如果仍然 404，请检查:"
echo "  1. 浏览器控制台的完整错误信息"
echo "  2. 网络请求的完整 URL"
echo "  3. 请求方法 (GET 还是 POST)"
