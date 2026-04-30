# AI 视频生成系统 - 项目总览 📊

**项目位置**: `/workspace/text-to-video-local/`

---

## 📁 文件清单

### 核心工具（6 个）⭐ NEW

| 文件 | 大小 | 功能 | 状态 |
|------|------|------|------|
| `scanner.py` | 33KB | 系统扫描与最优方案推荐 | ✅ 已创建 |
| `download_models.py` | 12KB | 智能模型下载器 | ✅ 已创建 |
| `run.py` | 8.6KB | 智能启动器 | ✅ 已创建 |
| `install.sh` | 11KB | 一键安装脚本 | ✅ 已创建 |
| `model_quantize.py` | 5.5KB | 模型量化工具 | ✅ 已创建 |
| `generation.py` | 14KB | 视频生成主程序 | ✓ 已有 |

### 文档（7 个）

| 文件 | 大小 | 描述 |
|------|------|------|
| `README.md` | 6.6KB | 📘 项目主文档 |
| `QUICKSTART.md` | 7.0KB | ⚡ 3 分钟快速开始 |
| `README_INSTALL.md` | 8.0KB | 📦 安装指南 |
| `README_FEATURES.md` | 9.9KB | 🎯 功能总览 |
| `PROJECT_OVERVIEW.md` | 本文件 | 📊 项目总览 |
| `EXAMPLES.md` | 7.7KB | 💡 使用示例 |
| `HARDWARE_GUIDE.md` | 9.0KB | 🔧 硬件指南 |

### 配置文件（4 个）

| 文件 | 描述 |
|------|------|
| `requirements.txt` | Python 依赖清单 |
| `config.yaml` | 主程序配置 |
| `Dockerfile` | Docker 镜像构建 |
| `docker-compose.yml` | Docker 编排配置 |

### 脚本（2 个）

| 文件 | 描述 |
|------|------|
| `start.sh` | Linux/Mac 快速启动 |
| `start.bat` | Windows 快速启动 |

---

## 🎯 使用流程图

```
用户需求
   ↓
┌─────────────────────────────────┐
│  1. 系统扫描 (scanner.py)       │
│  - 检测硬件配置                 │
│  - 生成最优方案                 │
│  - 输出：scan_report.json       │
└─────────────────────────────────┘
   ↓
┌─────────────────────────────────┐
│  2. 一键安装 (install.sh)       │
│  - 创建虚拟环境                 │
│  - 安装 PyTorch (GPU/CPU)       │
│  - 安装依赖                     │
│  - 下载模型                     │
└─────────────────────────────────┘
   ↓
┌───────────┬───────────┬───────────┐
│ 方式 A    │ 方式 B    │ 方式 C    │
│ run.py    │ Docker    │ 手动命令  │
└───────────┴───────────┴───────────┘
   ↓
┌─────────────────────────────────┐
│  3. 生成视频                    │
│  python3 generation.py ...      │
└─────────────────────────────────┘
   ↓
output.mp4
```

---

## 🚀 三种典型使用场景

### 场景一：新手用户（交互模式）

```bash
cd /workspace/text-to-video-local

# 1. 扫描系统
python3 scanner.py

# 2. 一键安装
bash install.sh

# 3. 激活环境
source venv/bin/activate

# 4. 交互模式生成视频
python3 run.py --interactive

# 跟随提示操作即可！
```

**预计耗时**: 15-30 分钟（含下载模型）

---

### 场景二：熟练用户（命令行模式）

```bash
cd /workspace/text-to-video-local

# 1. 扫描并生成离线包
python3 scanner.py --generate-package --package-dir offline-package

# 2. 快速安装
bash install.sh

# 3. 直接生成
python3 generation.py \
    -m modelscope \
    -p "一只猫在草地上奔跑" \
    -o output.mp4 \
    -d 5 \
    --fps 8 \
    -H 512 -W 512 \
    --steps 50
```

**预计耗时**: 1-2 分钟（不含安装）

---

### 场景三：生产部署（Docker 模式）

```bash
cd /workspace/text-to-video-local

# 1. 构建镜像
docker build -t video-gen:latest .

# 2. 运行（GPU）
docker run --gpus all -v ./outputs:/app/outputs video-gen:latest \
    python3 generation.py -m modelscope -p "测试" -o outputs/demo.mp4

# 3. 批量处理
docker-compose --profile gpu up -d video-generator-gpu
```

**预计耗时**: 5 分钟（首次构建）

---

## 📊 智能推荐系统

### 扫描结果示例

```
======================================================================
 HARDWARE SCAN REPORT
======================================================================

【硬件摘要】
  CPU: Intel i7-10700K (8 核)
  GPU: NVIDIA RTX 3080 (10.0GB)
  内存：32.0GB
  磁盘：256GB SSD
  网络：可用

【推荐方案】
  模式：gpu_mid_range
  置信度：high
  可用模型：modelscope, animatediff, svd
  下载优先级：modelscope → animatediff → svd

【优化建议】
  ✓ 启用 fp16 精度
  ✓ 使用 enable_model_cpu_offload()
  ✓ 推荐分辨率：512x512

【警告】
  ⚠ CogVideoX-5B 可能需要降低分辨率
======================================================================
```

### 推荐逻辑

```python
显存 ≥ 24GB + 内存 ≥ 32GB
  → gpu_high_end → 所有模型

显存 ≥ 12GB + 内存 ≥ 16GB
  → gpu_mid_range → modelscope, animatediff, svd

显存 ≥ 6GB + 内存 ≥ 8GB
  → gpu_low_end → modelscope

无 GPU + 内存 ≥ 16GB
  → cpu_capable → modelscope (CPU 模式)

内存 < 8GB
  → cpu_limited → 不推荐运行
```

---

## 🎭 模型选择指南

### ModelScope（默认推荐）
- **优点**: 小（2.5GB）、快、支持中文
- **适合**: 快速测试、中文内容、低配置
- **推荐配置**: RTX 2060+, 8GB 内存

### AnimateDiff
- **优点**: 基于 SD 生态、可定制、ControlNet 支持
- **适合**: 风格化视频、动画生成
- **推荐配置**: RTX 3070+, 16GB 内存

### CogVideoX-5B
- **优点**: 高质量、Transformer 架构
- **适合**: 高质量视频、专业应用
- **推荐配置**: RTX 3090+, 32GB 内存

### Stable Video Diffusion
- **优点**: 图生视频、Stability AI 出品
- **适合**: 图像转视频、视频编辑
- **推荐配置**: RTX 3080+, 24GB 内存

---

## 🛠️ 高级功能

### 1. 离线部署

```bash
# 有网络环境生成离线包
python3 scanner.py --generate-package --package-dir offline-package

# 打包
tar -czf offline.tar.gz offline-package/

# 离线环境解压部署
tar -xzf offline.tar.gz
cd offline-package
bash install.sh --skip-scan
```

### 2. 模型量化

```bash
# INT8 量化（减少 50% 显存）
python3 model_quantize.py -m modelscope --bits 8 -o quantized/

# ONNX 转换（加速推理）
python3 model_quantize.py -m modelscope --onnx -o onnx_models/
```

### 3. 批量生成

```bash
#!/bin/bash
prompts=("提示词 1" "提示词 2" "提示词 3")

for i in "${!prompts[@]}"; do
    python3 generation.py \
        -m modelscope \
        -p "${prompts[$i]}" \
        -o "video_$i.mp4" \
        -d 3
done
```

---

## 📈 性能参考表

| 配置 | 模型 | 分辨率 | 时长 | 耗时 | 显存占用 |
|------|------|--------|------|------|----------|
| RTX 3080 | ModelScope | 256×256 | 2s | 30s | 4GB |
| RTX 3080 | ModelScope | 512×512 | 5s | 2min | 8GB |
| RTX 3080 | CogVideoX | 512×512 | 5s | 3min | 14GB |
| RTX 3090 | CogVideoX | 768×768 | 5s | 5min | 20GB |
| CPU i7 | ModelScope | 256×256 | 2s | 5min | N/A |
| CPU i7 | ModelScope | 128×128 | 2s | 2min | N/A |

---

## 🔍 故障诊断

### 问题排查流程

```
问题发生
   ↓
1. 查看扫描报告
   cat scan_report.json
   
2. 检查 GPU 状态
   nvidia-smi
   
3. 检查显存
   python3 -c "import torch; print(torch.cuda.mem_get_info())"
   
4. 查看日志
   tail -f venv/pip.log (安装问题)
   
5. 联系支持
   附上 scan_report.json
```

### 常见问题速查

| 问题 | 解决方案 |
|------|----------|
| CUDA OOM | 降低分辨率、减少 steps、启用 offload |
| 下载慢 | 使用镜像站：`export HF_ENDPOINT=...` |
| 安装失败 | 升级 pip、手动安装 PyTorch |
| CPU 太慢 | 降低配置、减少 steps、缩小时长 |

---

## 📞 获取帮助

### 帮助命令

```bash
python3 generation.py --help      # 主程序帮助
python3 scanner.py --help         # 扫描工具帮助
python3 download_models.py --help # 下载工具帮助
python3 run.py --help             # 启动器帮助
```

### 文档索引

- 快速开始 → `QUICKSTART.md`
- 安装指南 → `README_INSTALL.md`
- 功能总览 → `README_FEATURES.md`
- 硬件指南 → `HARDWARE_GUIDE.md`
- 使用示例 → `EXAMPLES.md`

### 配置文件

- 系统扫描 → `scan_report.json` (运行后生成)
- 离线包 → `offline-package/` (运行后生成)

---

## 🎯 下一步

### 新手路径
```
1. 阅读 QUICKSTART.md
2. 运行 python3 scanner.py
3. 执行 bash install.sh
4. 尝试 python3 run.py --interactive
```

### 开发者路径
```
1. 阅读 README_FEATURES.md
2. 研究 scanner.py 源码
3. 自定义优化策略
4. 扩展支持新模型
```

### 部署工程师路径
```
1. 阅读 Docker 配置
2. 构建生产镜像
3. 配置 CI/CD
4. 批量部署
```

---

## 📝 版本信息

**版本**: v1.0.0  
**发布日期**: 2026-04-30  
**Python**: 3.10+  
**PyTorch**: 2.0+  
**许可证**: MIT

---

## 🙏 致谢

感谢以下开源项目:
- ModelScope (阿里达摩院)
- AnimateDiff (Guoyi Wang)
- CogVideoX (清华大学)
- Stable Video Diffusion (Stability AI)
- HuggingFace 🤗

---

**开始创作你的 AI 视频吧！🎬**
