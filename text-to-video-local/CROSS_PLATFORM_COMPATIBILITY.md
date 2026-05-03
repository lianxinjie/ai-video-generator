# 跨平台兼容性指南

## 📊 系统支持总览

| 系统 | 个人模式 | 混合模式 | 协同模式 | Web 模式 | 一键部署 | 支持等级 |
|------|---------|---------|---------|---------|---------|---------|
| **Linux** | ✅ | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ 完全支持 |
| **Windows** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⭐⭐⭐⭐ 良好支持 |
| **macOS** | ✅ | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ 良好支持 |
| **iOS** | ❌ | ❌ | ⚠️ | ✅ | ❌ | ⭐⭐ Web 访问 |

---

## 🖥️ 各系统详细说明

### 1. Linux (推荐 ⭐⭐⭐⭐⭐)

**优势**:
- ✅ 完整支持所有功能
- ✅ CUDA GPU 加速原生支持
- ✅ 多进程 fork 模式效率高
- ✅ FFmpeg 原生支持
- ✅ 一键安装脚本完整支持

**安装方法**:
```bash
# 一键安装
bash install.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-optimized.txt
python3 download_models.py
```

**运行模式**:
```bash
# 个人模式
python3 personal_mode/run.py -m personal

# 混合模式
python3 personal_mode/run.py -m hybrid

# 协同模式
python3 personal_mode/run.py -m collaborative

# Web 模式
python3 web/app.py
```

**支持的系统**:
- Ubuntu 20.04+
- Debian 11+
- CentOS 8+
- Fedora 35+
- Arch Linux

---

### 2. Windows (⭐⭐⭐⭐)

**优势**:
- ✅ 所有模式功能正常
- ✅ CUDA GPU 支持良好
- ✅ PowerShell/CMD 双支持

**限制**:
- ⚠️ install.sh 需要 Git Bash 或 WSL
- ⚠️ 多进程使用 spawn 模式，稍慢
- ⚠️ 路径分隔符需注意

**安装方法**:

#### 方法 A: 使用 Git Bash (推荐)
```bash
# 安装 Git for Windows (包含 Git Bash)
# https://git-scm.com/download/win

# 在 Git Bash 中运行
bash install.sh
```

#### 方法 B: 使用 PowerShell
```powershell
# 创建虚拟环境
python -m venv venv
venv\Scripts\Activate

# 安装 PyTorch (GPU 版本)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装依赖
pip install -r requirements-optimized.txt

# 下载模型
python download_models.py
```

#### 方法 C: 使用 WSL2 (最推荐)
```bash
# 在 WSL2 中安装 Ubuntu
# 然后按 Linux 方法安装
bash install.sh
```

**运行模式**:
```powershell
# 激活虚拟环境
venv\Scripts\Activate

# 个人模式
python personal_mode\run.py -m personal

# 混合模式
python personal_mode\run.py -m hybrid

# Web 模式
python web\app.py
```

**注意事项**:
1. 路径使用反斜杠 `\` 或 Python 的 `pathlib`
2. FFmpeg 需要单独安装：`choco install ffmpeg`
3. 建议使用 Windows Terminal

---

### 3. macOS (⭐⭐⭐⭐)

**优势**:
- ✅ 所有模式功能正常
- ✅ Apple Silicon (M1/M2/M3) MPS 加速
- ✅ Unix 环境，兼容性好

**限制**:
- ⚠️ NVIDIA GPU 不支持 (需 CUDA)
- ⚠️ 部分模型可能无 macOS 优化版本

**安装方法**:
```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 FFmpeg
brew install ffmpeg

# 一键安装
bash install.sh
```

**Apple Silicon 优化**:
```bash
# 安装 PyTorch MPS 版本
pip install torch torchvision torchaudio

# PyTorch 会自动使用 MPS 加速
# 无需额外配置
```

**运行模式**:
```bash
# 激活虚拟环境
source venv/bin/activate

# 所有模式
python3 personal_mode/run.py -m hybrid
python3 web/app.py
```

**支持的 macOS 版本**:
- macOS 12.0+ (Monterey)
- macOS 13.0+ (Ventura) - 推荐
- macOS 14.0+ (Sonoma)

---

### 4. iOS (⭐⭐ - 仅 Web 访问)

**限制**:
- ❌ 无法运行 Python (除非越狱)
- ❌ 无法本地执行安装脚本
- ❌ 无法使用 FFmpeg
- ❌ 无法使用 GPU 加速

**可用方案**:

#### 方案 A: Web 浏览器访问 (推荐)
```
1. 在 Linux/Windows/macOS上部署Web服务
2. iOS设备通过Safari访问
3. 所有功能通过Web界面操作
```

**iOS 访问步骤**:
```
1. 在服务器上启动 Web 服务:
   python3 web/app.py

2. iOS 设备访问:
   http://服务器IP:5000

3. 使用 Web 界面:
   - 硬件检测
   - 一键启动
   - 任务管理
   - 视频下载
```

#### 方案 B: 快捷指令调用 API
```javascript
// iOS 快捷指令示例
URL: http://服务器IP:5000/api/quick-start
方法：POST
Header: Content-Type: application/json
Body: {"prompt":"xxx","mode":"personal"}
```

#### 方案 C: Pyto (高级用户)
```python
# 使用 Pyto App 运行 Python (功能受限)
# 不推荐：缺少 FFmpeg 等关键依赖
```

---

## 🔧 一键部署脚本的自适应能力

### 当前支持的自适应功能

| 检测项 | Linux | Windows | macOS | 自适应行为 |
|--------|-------|---------|-------|-----------|
| **系统检测** | ✅ | ⚠️ | ✅ | 根据 uname 选择安装命令 |
| **Python 版本** | ✅ | ✅ | ✅ | 检查 >=3.10 |
| **GPU 检测** | ✅ | ❌ | ✅ | NVIDIA/CUDA vs Apple MPS |
| **虚拟环境** | ✅ | ✅ | ✅ | venv/bin vs venv\\Scripts |
| **PyTorch 版本** | ✅ | ✅ | ✅ | CUDA vs CPU vs MPS |
| **路径分隔符** | ✅ | ⚠️ | ✅ | 使用 pathlib 自动处理 |
| **FFmpeg 安装** | ✅ | ❌ | ✅ | apt/yum vs 手动 |

### install.sh 自适应逻辑

```bash
# 1. 系统检测
SYSTEM=$(uname -s)
case "$SYSTEM" in
    "Darwin")   IS_MACOS=true ;;
    "Linux")    IS_LINUX=true ;;
    *)          IS_WINDOWS=true ;;
esac

# 2. GPU 检测
if $IS_LINUX && command -v nvidia-smi; then
    # Linux + NVIDIA CUDA
    pip install torch --index-url https://download.pytorch.org/whl/cu121
elif $IS_MACOS && sysctl -n machdep.cpu.brand_string | grep -q "Apple M"; then
    # macOS + Apple Silicon MPS
    pip install torch  # 自动使用 MPS
else
    # CPU 模式
    pip install torch
fi

# 3. 虚拟环境激活
if $IS_MACOS || $IS_LINUX; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi
```

### 缺失的自适应功能

| 功能 | 当前状态 | 需要补充 |
|------|---------|---------|
| Windows 批处理版本 | ❌ | install.bat |
| Windows GPU 检测 | ❌ | nvidia-smi PowerShell |
| Windows FFmpeg 安装 | ❌ | choco/scoop 集成 |
| iOS Web 部署指南 | ❌ | 添加文档 |
| Docker 容器部署 | ❌ | Dockerfile |

---

## 📦 推荐部署方案

### 场景 1: 个人开发 (Linux/Windows/macOS)
```bash
# 本地安装所有模式
bash install.sh
python3 personal_mode/run.py -m hybrid
```

### 场景 2: 团队协作 (跨平台)
```bash
# 服务器部署 (Linux)
bash install.sh
python3 web/app.py  # 0.0.0.0:5000

# 团队成员通过浏览器访问
# Windows/macOS/iOS 均可使用
```

### 场景 3: 生产环境
```bash
# Docker 部署 (推荐)
docker build -t ai-video .
docker run -p 5000:5000 --gpus all ai-video

# 或 Kubernetes
kubectl apply -f k8s/
```

---

## 🐛 已知问题和解决方案

### Windows 问题

**问题 1**: `bash: command not found`
```powershell
# 解决：安装 Git Bash 或使用 WSL2
# https://git-scm.com/download/win
```

**问题 2**: 路径错误 `FileNotFoundError: [Errno 2] No such file`
```python
# 错误：open("data/file.txt")
# 正确：
from pathlib import Path
Path("data") / "file.txt"
```

**问题 3**: FFmpeg 不可用
```powershell
# 使用 Chocolatey 安装
choco install ffmpeg
```

### macOS 问题

**问题 1**: `torch` 无法使用 GPU
```bash
# 检查是否 Apple Silicon
sysctl -n machdep.cpu.brand_string

# PyTorch 会自动使用 MPS，无需额外配置
python3 -c "import torch; print(torch.backends.mps.is_available())"
```

**问题 2**: 权限错误
```bash
# 给予执行权限
chmod +x install.sh
```

### iOS 问题

**问题**: 无法运行 Python
```
解决方案：使用 Web 模式
1. 在服务器上部署
2. iOS 通过 Safari 访问 Web 界面
```

---

## ✅ 兼容性检查清单

### 部署前检查

- [ ] Python 3.10+ 已安装
- [ ] pip 已安装
- [ ] 磁盘空间 >= 30GB
- [ ] 网络连接正常

### Linux 额外检查

- [ ] GCC 编译器可用：`gcc --version`
- [ ] FFmpeg 可用：`ffmpeg -version`
- [ ] (可选) NVIDIA 驱动：`nvidia-smi`

### Windows 额外检查

- [ ] Git Bash 或 WSL2 已安装
- [ ] Visual C++ 运行库已安装
- [ ] FFmpeg 已安装 (可选)

### macOS 额外检查

- [ ] Xcode Command Line Tools: `xcode-select --install`
- [ ] Homebrew 已安装
- [ ] FFmpeg: `brew install ffmpeg`

---

## 📞 技术支持

### 系统兼容性反馈

如遇到跨平台问题，请提供：

1. **系统信息**:
   ```bash
   uname -a  # Linux/macOS
   systeminfo  # Windows
   ```

2. **Python 环境**:
   ```bash
   python3 --version
   pip3 --version
   ```

3. **错误日志**:
   ```bash
   # 运行测试
   python3 generation.py --check 2>&1 | tee error.log
   ```

---

**文档版本**: 1.0  
**最后更新**: 2026-05-03  
**维护者**: AI Video Generator Team
