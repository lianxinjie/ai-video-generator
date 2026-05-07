#!/bin/bash
# 提交前代码质量检查

echo "============================================================"
echo "  代码提交前质量检查"
echo "============================================================"
echo ""

FAILED=0

# 1. Python 语法检查
echo "1️⃣  Python 语法检查..."
if python3 -m py_compile web/app.py 2>&1; then
    echo "   ✅ 语法检查通过"
else
    echo "   ❌ 语法检查失败"
    FAILED=1
fi

# 2. 导入检查
echo ""
echo "2️⃣  导入模块检查..."
if python3 check_code_quality.py web/app.py 2>&1 | grep -q "所有文件检查通过"; then
    echo "   ✅ 导入检查通过"
else
    echo "   ⚠️  导入检查有警告"
fi

# 3. 检查是否有 TODO 注释
echo ""
echo "3️⃣  检查未完成代码..."
TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX" --include="*.py" web/ 2>/dev/null | wc -l)
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "   ⚠️  发现 $TODO_COUNT 个 TODO/FIXME 注释"
else
    echo "   ✅ 无未完成代码"
fi

# 4. 检查调试代码
echo ""
echo "4️⃣  检查调试代码..."
DEBUG_COUNT=$(grep -r "import pdb\|pdb.set_trace()\|print.*DEBUG" --include="*.py" web/ 2>/dev/null | wc -l)
if [ "$DEBUG_COUNT" -gt 0 ]; then
    echo "   ⚠️  发现 $DEBUG_COUNT 处调试代码"
else
    echo "   ✅ 无调试代码"
fi

echo ""
echo "============================================================"
if [ $FAILED -eq 0 ]; then
    echo "  ✅ 所有检查通过，可以提交"
else
    echo "  ❌ 有检查失败，请修复后再提交"
    exit 1
fi
echo "============================================================"
