#!/bin/bash
#===============================================================================
# 跨平台兼容性测试脚本

set -e

echo "==============================================="
echo "  跨平台兼容性测试"
echo "==============================================="
echo ""

# 检测系统
OS=$(uname -s 2>/dev/null || echo "Windows")
case "$OS" in
    "Linux")  
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "测试平台：WSL"
            PLATFORM="wsl"
        else
            echo "测试平台：Linux"
            PLATFORM="linux"
        fi
        ;;
    "Darwin")   
        echo "测试平台：macOS"
        PLATFORM="macos"
        ;;
    "MSYS"*|"MINGW"*) 
        echo "测试平台：Windows (Git Bash)"
        PLATFORM="windows_bash"
        ;;
    *)          
        echo "测试平台：未知 ($OS)"
        PLATFORM="unknown"
        ;;
esac

echo ""
RESULTS=()

# ========== 测试 1: Python 环境 ==========
echo -n "[1/8] Python 环境... "
if command -v python3 &> /dev/null || command -v python &> /dev/null; then
    PY_CMD=$(command -v python3 &> /dev/null && echo "python3" || echo "python")
    PY_VER=$($PY_CMD --version 2>&1)
    echo "✅ $PY_VER"
    RESULTS+=("✅")
else
    echo "❌ 未找到 Python"
    RESULTS+=("❌")
fi

# ========== 测试 2: pip ==========
echo -n "[2/8] pip... "
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    PIP_CMD=$(command -v pip3 &> /dev/null && echo "pip3" || echo "pip")
    echo "✅ $($PIP_CMD --version | head -1)"
    RESULTS+=("✅")
else
    echo "❌ 未找到 pip"
    RESULTS+=("❌")
fi

# ========== 测试 3: 虚拟环境 ==========
echo -n "[3/8] 虚拟环境... "
if [ -d "venv" ]; then
    echo "✅ 存在"
    RESULTS+=("✅")
else
    echo "❌ 不存在 (请先运行安装脚本)"
    RESULTS+=("❌")
fi

# ========== 测试 4: FFmpeg ==========
echo -n "[4/8] FFmpeg... "
if command -v ffmpeg &> /dev/null; then
    echo "✅ $(ffmpeg -version 2>&1 | head -1)"
    RESULTS+=("✅")
else
    echo "⚠️  未安装 (可选)"
    RESULTS+=("⚠️")
fi

# ========== 测试 5: GPU 检测 ==========
echo -n "[5/8] GPU 检测... "
if [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "wsl" ]; then
    if command -v nvidia-smi &> /dev/null; then
        GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        if [ -n "$GPU" ]; then
            echo "✅ NVIDIA: $GPU"
            RESULTS+=("✅")
        else
            echo "⚠️  驱动问题"
            RESULTS+=("⚠️")
        fi
    else
        echo "ℹ️  无 NVIDIA GPU (使用 CPU)"
        RESULTS+=("ℹ️")
    fi
elif [ "$PLATFORM" = "macos" ]; then
    if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple M"; then
        echo "✅ Apple Silicon (MPS)"
        RESULTS+=("✅")
    else
        echo "ℹ️  Intel Mac (无 GPU 加速)"
        RESULTS+=("ℹ️")
    fi
else
    echo "ℹ️  跳过"
    RESULTS+=("ℹ️")
fi

# ========== 测试 6: 安装脚本语法 ==========
echo -n "[6/8] 安装脚本语法... "
if [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "macos" ] || [ "$PLATFORM" = "wsl" ]; then
    if bash -n install.sh 2>/dev/null; then
        echo "✅ install.sh 语法正确"
        RESULTS+=("✅")
    else
        echo "❌ install.sh 语法错误"
        RESULTS+=("❌")
    fi
else
    echo "ℹ️  跳过 (Git Bash)"
    RESULTS+=("ℹ️")
fi

# ========== 测试 7: 启动脚本语法 ==========
echo -n "[7/8] 启动脚本语法... "
if bash -n start.sh 2>/dev/null; then
    echo "✅ start.sh 语法正确"
    RESULTS+=("✅")
else
    echo "❌ start.sh 语法错误"
    RESULTS+=("❌")
fi

# ========== 测试 8: 关键文件 ==========
echo -n "[8/8] 关键文件... "
MISSING=()
for file in "web/app.py" "personal_mode/run.py" "generation.py"; do
    if [ ! -f "$file" ]; then
        MISSING+=("$file")
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    echo "✅ 所有关键文件存在"
    RESULTS+=("✅")
else
    echo "❌ 缺少：${MISSING[*]}"
    RESULTS+=("❌")
fi

# ========== 汇总 ==========
echo ""
echo "==============================================="
echo "  测试结果汇总"
echo "==============================================="
echo ""

PASS=0
WARN=0
INFO=0
FAIL=0

for r in "${RESULTS[@]}"; do
    case "$r" in
        "✅") ((PASS++)) || true ;;
        "⚠️") ((WARN++)) || true ;;
        "ℹ️") ((INFO++)) || true ;;
        "❌") ((FAIL++)) || true ;;
    esac
done

TOTAL=${#RESULTS[@]}

echo "平台：$PLATFORM ($(uname -s))"
echo ""
echo "结果:"
echo "  ✅ 通过：$PASS"
echo "  ⚠️  警告：$WARN"
echo "  ℹ️  信息：$INFO"
echo "  ❌ 失败：$FAIL"
echo ""

if [ $FAIL -gt 0 ]; then
    SCORE=$(( (PASS * 100) / TOTAL ))
    echo "评分：$SCORE%"
    echo ""
    echo "❌ 存在失败项，请修复后重试"
    exit 1
else
    SCORE=$(( (PASS * 100) / TOTAL ))
    echo "评分：$SCORE%"
    echo ""
    echo "✅ 所有必要测试通过！"
    exit 0
fi
