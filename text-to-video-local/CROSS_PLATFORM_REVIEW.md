# 跨平台脚本审查报告

## 🔴 严重问题 (Critical)

### Windows (install.bat)

#### 问题 1: 虚拟环境激活后变量丢失
```batch
call venv\Scripts\activate.bat
if "%HAS_GPU%"=="true" (  # ❌ HAS_GPU 变量在激活后已丢失
```
**原因**: `call` 命令会创建新的作用域，之前设置的变量会丢失
**影响**: 总是安装 CPU 版本 PyTorch
**严重性**: 🔴 高

#### 问题 2: 错误处理不完整
```batch
pip install torch torchvision torchaudio --index-url ...
# ❌ 没有检查 errorlevel
```
**影响**: 安装失败但脚本继续执行
**严重性**: 🔴 高

#### 问题 3: 长路径问题
```batch
python -m venv venv  # ❌ Windows 默认 260 字符路径限制
```
**影响**: 深层目录结构会失败
**严重性**: 🟡 中

#### 问题 4: PowerShell 兼容性问题
```batch
@echo off  # ❌ 在 PowerShell 中运行会显示警告
```
**影响**: PowerShell 用户可能需要手动切换到 CMD
**严重性**: 🟡 中

### Windows (start.bat)

#### 问题 1: 参数传递错误
```batch
python personal_mode\run.py -m hybrid %*  # ❌ %*可能包含引号问题
```
**影响**: 带空格的提示词会被拆分
**严重性**: 🟡 中

#### 问题 2: 虚拟环境激活检查
```batch
call venv\Scripts\activate.bat
# ❌ 没有验证是否激活成功
```
**严重性**: 🟡 中

### Linux/macOS (install.sh)

#### 问题 1: GPU 检测不完善
```bash
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "")
    if [ -n "$GPU_INFO" ]; then  # ❌ 有命令但无 GPU 也会通过
```
**严重性**: 🟢 低

#### 问题 2: macOS GPU 检测
```bash
sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple M"
# ❌ Intel Mac 会返回空字符串但不报错
```
**严重性**: 🟢 低

### Linux/macOS (start.sh)

#### 问题 1: Windows Git Bash 路径
```bash
if [ "$OS_NAME" = "windows" ]; then
    source venv/Scripts/activate  # ✅ 正确
else
    source venv/bin/activate
fi
```
**状态**: ✅ 正确

---

## 📋 需要修复的问题清单

### Windows install.bat (优先级：🔴 高)
- [ ] 修复变量作用域问题
- [ ] 添加错误处理 (errorlevel 检查)
- [ ] 启用长路径支持
- [ ] 改进 PowerShell 兼容性
- [ ] 添加日志输出
- [ ] 检查 Visual C++ 运行库

### Windows start.bat (优先级：🟡 中)
- [ ] 修复参数传递
- [ ] 验证虚拟环境激活
- [ ] 添加超时处理

### Linux/macOS install.sh (优先级：🟢 低)
- [ ] 改进 GPU 检测逻辑
- [ ] 添加 Homebrew 检查 (macOS)
- [ ] 优化错误提示

### Linux/macOS start.sh (优先级：🟢 低)
- [ ] 已经是正确的

---

## 📊 测试矩阵

| 测试项 | Windows | Linux | macOS | 状态 |
|--------|---------|-------|-------|------|
| Python 检查 | ⚠️ | ✅ | ✅ | 需修复 |
| pip 检查 | ⚠️ | ✅ | ✅ | 需修复 |
| GPU 检测 | ❌ | ⚠️ | ⚠️ | 需修复 |
| 虚拟环境 | ❌ | ✅ | ✅ | 需修复 |
| PyTorch 安装 | ❌ | ✅ | ✅ | 需修复 |
| 依赖安装 | ⚠️ | ✅ | ✅ | 需修复 |
| 模型下载 | ⚠️ | ✅ | ✅ | 需测试 |

---

**审查日期**: 2026-05-03
**审查者**: AI Code Reviewer
**总体评估**: Windows 需要紧急修复，Linux/macOS 基本可用
