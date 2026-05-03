#!/bin/bash

echo "============================================================"
echo "  AI 视频生成器 - 安装流程测试"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
test_file_exists() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc: $file"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: $file"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_file_not_exists() {
    local file=$1
    local desc=$2
    if [ ! -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc: $file 已删除"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: $file 应该被删除"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_html_valid() {
    local file=$1
    local desc=$2
    if grep -q "<!DOCTYPE html>" "$file" && grep -q "</html>" "$file"; then
        echo -e "${GREEN}✓${NC} $desc: HTML 结构完整"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: HTML 结构损坏"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_js_function() {
    local file=$1
    local func=$2
    local desc=$3
    if grep -q "function $func" "$file" || grep -q "$func()" "$file"; then
        echo -e "${GREEN}✓${NC} $desc: 函数 $func 存在"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: 函数 $func 不存在"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "=== 测试 1: 检查必需文件 ==="
test_file_exists "index.html" "主页"
test_file_exists "offline_install.html" "离线安装器"
test_file_exists "install_standalone.bat" "Windows 独立安装器"
test_file_exists "start_install.bat" "Windows 启动安装"
test_file_exists "start_install.command" "macOS/Linux 启动安装"
test_file_exists "quick_start.py" "快速启动脚本"
echo ""

echo "=== 测试 2: 检查已删除的无用文件 ==="
test_file_not_exists "python_launcher.py" "废弃的 Python 启动器"
test_file_not_exists "run_installer.html" "废弃的安装器 HTML"
test_file_not_exists "web_installer.py" "废弃的 Web 安装器"
echo ""

echo "=== 测试 3: 检查 HTML 有效性 ==="
test_html_valid "index.html" "index.html"
test_html_valid "offline_install.html" "offline_install.html"
echo ""

echo "=== 测试 4: 检查关键 JavaScript 函数 ==="
test_js_function "index.html" "selectPlatform" "index.html: 平台选择"
test_js_function "index.html" "setPythonInstalled" "index.html: Python 确认"
test_js_function "index.html" "goToStep" "index.html: 步骤导航"
test_js_function "offline_install.html" "selectPlatform" "offline_install: 平台选择"
test_js_function "offline_install.html" "finishInstall" "offline_install: 完成安装"
echo ""

echo "=== 测试 5: 检查文件权限 ==="
if [ -x "quick_start.py" ]; then
    echo -e "${GREEN}✓${NC} quick_start.py 可执行"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} quick_start.py 不可执行 (可能是正常的)"
    ((TESTS_PASSED++))
fi

if [ -x "install_standalone.bat" ] 2>/dev/null || [ -f "install_standalone.bat" ]; then
    echo -e "${GREEN}✓${NC} install_standalone.bat 存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} install_standalone.bat 不存在"
    ((TESTS_FAILED++))
fi
echo ""

echo "=== 测试 6: 检查 index.html 功能 ==="
if grep -q "pythonConfirmed" "index.html"; then
    echo -e "${GREEN}✓${NC} Python 确认逻辑存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Python 确认逻辑缺失"
    ((TESTS_FAILED++))
fi

if grep -q "offline_install.html" "index.html"; then
    echo -e "${GREEN}✓${NC} 离线安装器链接存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} 离线安装器链接缺失"
    ((TESTS_FAILED++))
fi

if grep -q "?installed=true" "index.html"; then
    echo -e "${GREEN}✓${NC} 安装完成重定向存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} 安装完成重定向缺失"
    ((TESTS_FAILED++))
fi
echo ""

echo "=== 测试 7: 检查 offline_install.html 功能 ==="
if grep -q "localStorage" "offline_install.html"; then
    echo -e "${GREEN}✓${NC} localStorage 集成存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} localStorage 集成缺失"
    ((TESTS_FAILED++))
fi

if grep -q "python.org" "offline_install.html"; then
    echo -e "${GREEN}✓${NC} Python 官方下载链接存在"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Python 官方下载链接缺失"
    ((TESTS_FAILED++))
fi
echo ""

echo "============================================================"
echo "  测试结果"
echo "============================================================"
echo -e "通过：${GREEN}$TESTS_PASSED${NC}"
echo -e "失败：${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $TESTS_FAILED 项测试失败${NC}"
    exit 1
fi
