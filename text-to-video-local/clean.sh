#!/bin/bash
# 项目清理脚本
# 自动清理无用代码和文件

set -e

echo "============================================================"
echo "项目清理脚本"
echo "============================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "当前工作目录: $(pwd)"
echo ""

# 计数器
CLEANED_DIRS=0
CLEANED_FILES=0

# 1. 清理 Python 缓存
echo "【1/8】清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo "  ✓ 清理 __pycache__ 目录" || true
find . -name "*.pyc" -delete 2>/dev/null && echo "  ✓ 清理 .pyc 文件" || true
find . -name "*.pyo" -delete 2>/dev/null && echo "  ✓ 清理 .pyo 文件" || true
((CLEANED_DIRS++)) || true

# 2. 清理临时文件
echo "【2/8】清理临时文件..."
find . -name "*.tmp" -delete 2>/dev/null && echo "  ✓ 清理 .tmp 文件" || true
find . -name "*.temp" -delete 2>/dev/null && echo "  ✓ 清理 .temp 文件" || true
find . -name "*.log" -delete 2>/dev/null && echo "  ✓ 清理 .log 文件" || true
((CLEANED_FILES++)) || true

# 3. 清理备份文件
echo "【3/8】清理备份文件..."
find . -name "*.bak" -delete 2>/dev/null && echo "  ✓ 清理 .bak 文件" || true
find . -name "*.backup" -delete 2>/dev/null && echo "  ✓ 清理 .backup 文件" || true
find . -name "*~" -delete 2>/dev/null && echo "  ✓ 清理临时编辑器文件" || true
((CLEANED_FILES++)) || true

# 4. 清理 IDE 配置
echo "【4/8】清理 IDE 配置..."
rm -rf .idea/ 2>/dev/null && echo "  ✓ 清理 .idea 目录" || true
rm -rf .vscode/ 2>/dev/null && echo "  ✓ 清理 .vscode 目录" || true
find . -name "*.swp" -delete 2>/dev/null && echo "  ✓ 清理 .swp 文件" || true
find . -name "*.swo" -delete 2>/dev/null && echo "  ✓ 清理 .swo 文件" || true
((CLEANED_DIRS++)) || true

# 5. 清理测试文件
echo "【5/8】清理测试文件..."
find . -maxdepth 1 -name "test_*.py" -delete 2>/dev/null && echo "  ✓ 清理顶层测试文件" || true
rm -rf pytest_cache/ 2>/dev/null && echo "  ✓ 清理 pytest_cache" || true
rm -rf .pytest_cache/ 2>/dev/null && echo "  ✓ 清理 .pytest_cache" || true
rm -f .coverage 2>/dev/null && echo "  ✓ 清理 .coverage" || true
rm -rf htmlcov/ 2>/dev/null && echo "  ✓ 清理 htmlcov" || true
((CLEANED_FILES++)) || true

# 6. 清理构建产物
echo "【6/8】清理构建产物..."
rm -rf dist/ 2>/dev/null && echo "  ✓ 清理 dist 目录" || true
rm -rf build/ 2>/dev/null && echo "  ✓ 清理 build 目录" || true
rm -rf *.egg-info/ 2>/dev/null && echo "  ✓ 清理 egg-info" || true
((CLEANED_DIRS++)) || true

# 7. 清理文档缓存
echo "【7/8】清理文档缓存..."
rm -f COMMIT_MSG.txt 2>/dev/null && echo "  ✓ 清理 COMMIT_MSG.txt" || true
rm -f *.md.bak 2>/dev/null && echo "  ✓ 清理备份文档" || true
((CLEANED_FILES++)) || true

# 8. 清理空目录
echo "【8/8】清理空目录..."
find . -type d -empty -not -path "./.git*" -delete 2>/dev/null && echo "  ✓ 清理空目录" || true
((CLEANED_DIRS++)) || true

echo ""
echo "============================================================"
echo "清理完成！"
echo "============================================================"
echo "清理统计:"
echo "  目录：${CLEANED_DIRS} 类"
echo "  文件：${CLEANED_FILES} 类"
echo ""

# 验证清理结果
echo "验证清理结果..."
REMAINING=$(find . -name "__pycache__" -o -name "*.pyc" -o -name "*.tmp" -o -name "*.bak" | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "  ✅ 清理彻底，无残留"
else
    echo "  ⚠️ 仍有 $REMAINING 个文件未清理"
fi

echo ""
echo "当前目录状态:"
echo "  文件数：$(find . -type f | wc -l)"
echo "  目录数：$(find . -type d | wc -l)"
echo ""
