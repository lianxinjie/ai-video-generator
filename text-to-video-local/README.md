# AI 视频生成系统 🎬

> 智能检测 · 一键安装 · 离线部署 · 多模型支持

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 特性亮点

### ⚡ 智能检测与推荐
- 🔍 自动扫描硬件配置（CPU/GPU/内存/磁盘）
- 🎯 基于硬件生成最优安装和运行方案
- 📊 提供详细的性能评估和优化建议

### 🚀 一键安装
- 📦 全自动化安装流程
- 🖥️ GPU/CPU自适应配置
- 🌐 在线/离线双模式支持
- 🎨 个性化依赖配置生成

### 💾 离线部署
- 📥 智能模型下载器（支持断点续传）
- 📦 离线包自动生成
- 🔄 批量并行下载
- ✅ 已存在模型自动检测

### 🎭 多模型支持
- **ModelScope** - 阿里达摩院模型，支持中文
- **AnimateDiff** - 基于 Stable Diffusion
- **CogVideoX-5B** - 清华高质量 Transformer 模型
- **SVD** - Stability AI 图生视频

### 🎮 多种运行模式
- 🖱️ 交互模式 (新手友好)
- 🤖 智能自动模式
- ⌨️ 命令行模式 (高级用户)
- 🐳 Docker 容器化部署
- 💻 **个人电脑模式** - 低显存 GPU 专用 (1-8GB)

---

## 🚀 快速开始

### 三步生成第一个视频

```bash
# 1. 扫描系统配置
python3 scanner.py

# 2. 一键安装
bash install.sh

# 3. 生成视频
python3 run.py -p "一只猫在草地上奔跑" -o output.mp4
```

🎉 **完成！**查看生成的 `output.mp4` 文件

---

## 💻 个人电脑模式 (新增)

专为低显存 GPU(1-8GB) 设计，通过**分段生成 + 合并**的方式，用时间换性能。

### 快速开始

```bash
# 生成 5 秒视频 (每段 0.5 秒，共 10 段)
python3 personal_mode/generate.py -p "蝴蝶在花丛中飞舞" -d 5 -c 0.5

# 查看进度
python3 personal_mode/generate.py status --project-dir ./projects/default

# 从断点继续
python3 personal_mode/generate.py resume --project-dir ./projects/default
```

### 核心特性

- ✅ **分段生成**: 将长视频分成多个短片段依次生成
- ✅ **资源监控**: 实时监控 GPU/CPU/内存，超过阈值自动暂停
- ✅ **断点续传**: 关机后再开机可从中断处继续
- ✅ **智能等待**: 资源紧张时自动暂停，恢复后继续
- ✅ **视频合并**: 自动生成完整视频，支持过渡效果

### GTX 1050 2GB 优化配置

```bash
python3 personal_mode/generate.py \
  -p "蝴蝶飞舞" \
  -d 3 \
  -c 0.5 \
  --resolution 384x384 \
  --gpu-threshold 70 \
  --model modelscope
```

详细文档：[personal_mode/README.md](personal_mode/README.md)

---

## 📋 完整文档

| 文档 | 描述 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | ⚡ 3 分钟快速开始指南 |
| [README_INSTALL.md](README_INSTALL.md) | 📦 详细安装和部署指南 |
| [README_FEATURES.md](README_FEATURES.md) | 🎯 完整功能说明 |

---

## 🎯 核心工具

### 1. 系统扫描器 (`scanner.py`)

```bash
# 扫描硬件，生成最优方案
python3 scanner.py -o scan_report.json

# 生成离线包
python3 scanner.py --generate-package --package-dir offline-package
```

**输出示例：**
```
【推荐方案】
  模式：GPU_MID_RANGE (置信度：HIGH)
  可用模型：modelscope, animatediff, svd
  优化建议：启用 fp16 精度，使用 CPU offload
```

### 2. 智能下载器 (`download_models.py`)

```bash
# 从扫描报告读取推荐
python3 download_models.py --from-scan

# 并行下载多个模型
python3 download_models.py -m all --parallel 2
```

### 3. 一键安装 (`install.sh`)

```bash
# 全自动安装
bash install.sh

# 跳过模型下载
bash install.sh --skip-models
```

### 4. 智能启动器 (`run.py`)

```bash
# 自动选择最优配置
python3 run.py -p "生成视频" -o output.mp4

# 交互模式
python3 run.py --interactive
```

---

## 📊 硬件要求

### 最低配置
- **CPU**: 4 核心
- **内存**: 8GB
- **磁盘**: 30GB 可用空间
- **GPU**: 可选（无 GPU 使用 CPU 模式）

### 推荐配置
- **CPU**: 8 核心+
- **内存**: 16GB+
- **GPU**: NVIDIA RTX 3060 12GB+
- **磁盘**: 100GB+ SSD

### 理想配置
- **CPU**: 16 核心+
- **内存**: 32GB+
- **GPU**: NVIDIA RTX 3080 10GB+
- **磁盘**: 500GB+ NVMe SSD

---

## 🎭 支持模型对比

| 模型 | 大小 | 最低显存 | CPU 兼容 | 特点 |
|------|------|----------|---------|------|
| **ModelScope** | 2.5GB | 6GB | ✅ | 支持中文，快速 |
| **AnimateDiff** | 8GB | 12GB | ✅ | 可定制性强 |
| **CogVideoX-5B** | 20GB | 16GB | ❌ | 高质量 |
| **SVD** | 12GB | 14GB | ✅ | 图生视频 |

---

## 🐳 Docker 部署

### GPU 模式
```bash
docker run --gpus all -v ./outputs:/app/outputs video-generator:gpu-latest \
    python3 generation.py -m modelscope -p "测试" -o outputs/demo.mp4
```

### CPU 模式
```bash
docker run -v ./outputs:/app/outputs video-generator:cpu-latest \
    python3 generation.py -m modelscope --device cpu -p "测试" -o outputs/demo.mp4
```

### Docker Compose
```bash
# GPU 模式
docker-compose --profile gpu up video-generator-gpu

# 查看日志
docker-compose logs -f video-generator-gpu
```

---

## ⚙️ 高级功能

### 模型量化
```bash
# INT8 量化（减少 50% 显存）
python3 model_quantize.py -m modelscope --bits 8 -o quantized/
```

### 批量生成
```bash
cat > prompts.txt << EOF
一只猫在草地上奔跑
一只狗在海滩上玩耍
一只鸟在天空中飞翔
EOF

while IFS= read -r prompt; do
    python3 generation.py -m modelscope -p "$prompt" -o "video_$(date +%s).mp4"
done < prompts.txt
```

---

## 📈 性能参考

| 配置 | 模型 | 分辨率 | 时长 | 耗时 |
|------|------|--------|------|------|
| RTX 3080 | ModelScope | 256×256 | 2 秒 | ~30 秒 |
| RTX 3080 | CogVideoX | 512×512 | 5 秒 | ~3 分钟 |
| CPU i7 | ModelScope | 256×256 | 2 秒 | ~5 分钟 |
| CPU i7 | ModelScope | 128×128 | 2 秒 | ~2 分钟 |

---

## 🔧 故障排查

### 显存不足
```bash
# 降低分辨率
python3 generation.py -H 256 -W 256 ...

# 减少推理步数
python3 generation.py --steps 25 ...
```

### 下载慢
```bash
# 使用镜像站
export HF_ENDPOINT=https://hf-mirror.com
python3 download_models.py -m modelscope
```

### 安装失败
```bash
# 手动安装
pip3 install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

pip3 install -r requirements.txt
```

---

## 📞 获取帮助

```bash
# 查看帮助
python3 generation.py --help
python3 scanner.py --help

# 查看配置
python3 run.py --show-config

# 查看扫描报告
cat scan_report.json | python3 -m json.tool
```

---

## 📦 依赖

**核心依赖:**
- PyTorch 2.0+
- diffusers 0.24+
- transformers 4.35+
- accelerate 0.24+
- modelscope 1.9+

**可选依赖:**
- xformers (NVIDIA GPU 加速)
- triton (AMD GPU 支持)
- onnxruntime (推理加速)

完整依赖列表：[requirements.txt](requirements.txt)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- **ModelScope** - 阿里达摩院
- **AnimateDiff** - Guoyi Wang
- **CogVideoX** - 清华大学
- **Stable Video Diffusion** - Stability AI
- **HuggingFace** 🤗

---

## 📬 更新日志

### v1.0.0 (2026-04-30)

**新增功能:**
- ✅ 系统扫描与智能推荐
- ✅ 一键安装脚本
- ✅ 智能模型下载器
- ✅ 智能启动器
- ✅ 模型量化工具
- ✅ Docker 支持
- ✅ 离线包生成

**支持的模型:**
- ModelScope Text-to-Video
- AnimateDiff
- CogVideoX-5B
- Stable Video Diffusion

---

## 🎬 开始创作

```bash
# 现在就生成你的第一个 AI 视频！
python3 run.py --interactive
```

**祝你使用愉快！** 🎉

---

## 代码质量保证

### 自动检查

在提交代码前，运行以下检查：

```bash
# 检查 Python 语法和导入
python check_code_quality.py

# 检查语法（快速）
python -m py_compile web/app.py
```

### 常见问题防范

1. **缺少导入**：使用任何模块前先检查是否已导入
2. **语法错误**：使用 `ast.parse()` 验证
3. **路径错误**：使用 `Path()` 而非字符串拼接
4. **超时保护**：所有网络请求和外部调用设置超时

