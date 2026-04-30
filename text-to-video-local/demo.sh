#!/bin/bash
# AI 视频生成系统 - 演示脚本
# 用于快速展示所有功能

set -e

echo "=========================================="
echo "AI Video Generator - 演示脚本"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_section() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
}

log_step() {
    echo -e "${GREEN}→ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 帮助
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "用法：bash demo.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --scan      演示系统扫描"
    echo "  --install   演示一键安装"
    echo "  --download  演示模型下载"
    echo "  --run       演示智能启动"
    echo "  --all       演示全部功能"
    echo "  --help      显示帮助"
    exit 0
fi

# 功能选择
DEMO_MODE="${1:---all}"

# 1. 系统扫描演示
if [ "$DEMO_MODE" = "--scan" ] || [ "$DEMO_MODE" = "--all" ]; then
    log_section "【演示 1】系统扫描"
    
    log_step "运行系统扫描..."
    log_info "这将检测您的 CPU、GPU、内存、磁盘等硬件配置"
    
    python3 scanner.py -o demo_scan_report.json
    
    echo ""
    log_info "✓ 扫描完成！报告已保存到：demo_scan_report.json"
    echo ""
    echo "查看报告:"
    echo "  cat demo_scan_report.json | python3 -m json.tool"
fi

# 2. 安装演示
if [ "$DEMO_MODE" = "--install" ] || [ "$DEMO_MODE" = "--all" ]; then
    log_section "【演示 2】一键安装"
    
    log_step "开始一键安装流程..."
    log_info "这包括：创建虚拟环境 → 安装 PyTorch → 安装依赖 → 下载模型"
    echo ""
    echo "注意：此演示仅显示安装流程，实际安装约需 15-30 分钟"
    echo "按 Ctrl+C 可随时中断"
    echo ""
    
    # 读取安装脚本（仅显示，不实际执行）
    head -50 install.sh
    echo "... (安装脚本内容)"
    
    echo ""
    log_info "实际安装命令：bash install.sh"
fi

# 3. 下载演示
if [ "$DEMO_MODE" = "--download" ] || [ "$DEMO_MODE" = "--all" ]; then
    log_section "【演示 3】智能模型下载"
    
    log_step "显示模型下载帮助..."
    python3 download_models.py --help
    
    echo ""
    log_info "常用下载命令:"
    echo "  python3 download_models.py --from-scan    # 从扫描报告读取"
    echo "  python3 download_models.py -m modelscope  # 下载单个模型"
    echo "  python3 download_models.py -m all -j 2    # 并行下载所有"
fi

# 4. 运行演示
if [ "$DEMO_MODE" = "--run" ] || [ "$DEMO_MODE" = "--all" ]; then
    log_section "【演示 4】智能启动"
    
    log_step "运行智能启动器..."
    log_info "这将自动选择最优模型和参数"
    
    python3 run.py --show-config
    
    echo ""
    log_info "启动视频生成命令:"
    echo "  python3 run.py -p \"一只猫在草地上奔跑\" -o output.mp4"
    echo ""
    log_info "交互模式 (适合新手):"
    echo "  python3 run.py --interactive"
fi

# 完成
log_section "演示完成"

echo ""
echo "下一步:"
echo "  1. 系统扫描：python3 scanner.py"
echo "  2. 一键安装：bash install.sh"
echo "  3. 生成视频：python3 run.py -p \"提示词\" -o output.mp4"
echo ""
echo "文档:"
echo "  QUICKSTART.md - 3 分钟快速开始"
echo "  README_INSTALL.md - 详细安装指南"
echo "  CHEATSHEET.md - 命令速查表"
echo ""
echo "=========================================="
