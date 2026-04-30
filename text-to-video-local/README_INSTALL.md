# AI 视频生成 - 智能安装与部署指南

## 📋 目录

- [快速开始](#快速开始)
- [系统扫描](#系统扫描)
- [安装方式](#安装方式)
- [运行模式](#运行模式)
- [离线部署](#离线部署)
- [故障排查](#故障排查)

---

## 🚀 快速开始

### 方式一：一键安装（推荐）

```bash
# 1. 克隆或下载项目
cd text-to-video-local

# 2. 运行系统扫描（可选，但推荐）
python3 scanner.py

# 3. 执行一键安装
bash install.sh

# 4. 激活虚拟环境
source venv/bin/activate

# 5. 测试运行
python3 generation.py --check

# 6. 生成视频
python3 generation.py -m modelscope -p "一只猫在草地上奔跑" -o output.mp4
```

### 方式二：智能启动

```bash
# 自动根据系统配置选择最优参数
python3 run.py -p "一只小狗在海滩上奔跑" -o demo.mp4

# 交互模式（适合新手）
python3 run.py --interactive

# 先扫描再运行（确保最优配置）
python3 run.py --scan -p "测试视频"
```

---

## 🔍 系统扫描

### 扫描功能

`scanner.py` 会自动检测：

- ✅ CPU 型号和核心数
- ✅ GPU 型号和显存
- ✅ 内存容量
- ✅ 磁盘空间
- ✅ 网络状态
- ✅ CUDA/cuDNN 版本
- ✅ Python 环境

### 使用方法

```bash
# 完整扫描并生成报告
python3 scanner.py -o scan_report.json

# 生成离线包配置
python3 scanner.py --generate-package --package-dir offline-package

# 简洁模式
python3 scanner.py -q
```

### 扫描报告示例

```json
{
  "hardware": {
    "cpu_model": "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz",
    "cpu_cores": 8,
    "gpu_models": ["NVIDIA GeForce RTX 3080"],
    "gpu_memory_total": [10.0],
    "ram_total": 32.0,
    "disk_available": 256.5,
    "gpu_available": true
  },
  "recommendation": {
    "mode": "gpu_high_end",
    "confidence": "high",
    "suitable_models": ["modelscope", "animatediff", "cogvideox", "svd"],
    "download_priority": ["cogvideox", "svd", "animatediff", "modelscope"],
    "warnings": [],
    "optimization_tips": ["✓ 您的配置可以运行所有模型"]
  }
}
```

### 推荐方案说明

| 模式 | 说明 | 推荐模型 |
|------|------|----------|
| `gpu_high_end` | 高端 GPU (显存≥24GB) | 所有模型 |
| `gpu_mid_range` | 中端 GPU (显存 12-24GB) | ModelScope, AnimateDiff, SVD |
| `gpu_low_end` | 低端 GPU (显存 6-12GB) | ModelScope |
| `cpu_capable` | 无 GPU，内存≥16GB | ModelScope (CPU 模式) |
| `cpu_limited` | 无 GPU，内存<16GB | 不推荐运行 |

---

## 📦 安装方式

### 方式一：在线安装

```bash
bash install.sh
```

**步骤：**
1. 自动扫描系统
2. 创建虚拟环境
3. 安装 PyTorch（GPU/CPU 自适应）
4. 安装依赖
5. 下载推荐模型
6. 测试运行

### 方式二：离线安装

在有网络的环境中生成离线包，然后到无网络环境部署：

```bash
# 【有网络环境】
python3 scanner.py --generate-package --package-dir offline-package

# 打包离线包
cd offline-package
tar -czf offline-package.tar.gz .

# 拷贝到离线环境
scp offline-package.tar.gz user@offline-server:/path/to/

# 【离线环境】
tar -xzf offline-package.tar.gz
bash install.sh --skip-scan
```

### 方式三：Docker 部署

```bash
# 构建镜像
docker build -t video-gen:latest .

# GPU 模式运行
docker run --gpus all -v ./outputs:/app/outputs video-gen:latest \
    python3 generation.py -m modelscope -p "测试" -o outputs/demo.mp4

# CPU 模式运行
docker run -v ./outputs:/app/outputs video-gen:cpu \
    python3 generation.py -m modelscope --device cpu -p "测试"
```

---

## 🎯 运行模式

### 智能启动模式

```bash
# 自动选择最优配置
python3 run.py -p "一只猫在草地上奔跑"

# 指定模型
python3 run.py -m cogvideox -p "高质量视频"

# 交互模式（新手推荐）
python3 run.py --interactive
```

### 命令行模式

```bash
# 基础用法
python3 generation.py -m modelscope -p "提示词" -o output.mp4

# 高级参数
python3 generation.py \
    -m cogvideox \
    -p "一只猫在草地上奔跑，阳光明媚" \
    -n "模糊，变形" \
    -o output.mp4 \
    -d 5 \
    --fps 8 \
    -H 512 -W 512 \
    --steps 50 \
    --guidance-scale 7.5 \
    --seed 42
```

### 参数详解

```
-m, --model           模型名称 [modelscope|animatediff|cogvideox|svd]
-p, --prompt          文本提示词（必需）
-n, --negative-prompt 负向提示词
-o, --output          输出文件路径
-d, --duration        视频时长（秒）
--fps                 帧率（默认 8）
-H, --height          视频高度（默认 256）
-W, --width           视频宽度（默认 256）
--steps               推理步数（默认 50，越多质量越好）
--guidance-scale      引导系数（默认 7.5）
--seed                随机种子（可复现结果）
--device              设备 [cuda|cpu]
```

---

## 💾 离线部署

### 模型下载

```bash
# 下载推荐模型
python3 download_models.py --from-scan

# 下载指定模型
python3 download_models.py -m modelscope animatediff

# 下载所有模型
python3 download_models.py -m all --parallel 2

# 并行下载（需要稳定网络）
python3 download_models.py -m all --parallel 3 -o ./models
```

### 模型大小参考

| 模型 | 大小 | 推荐 GPU 显存 | CPU 兼容性 |
|------|------|--------------|-----------|
| ModelScope | 2.5GB | 6GB+ | ✅ |
| AnimateDiff | 8GB | 12GB+ | ✅ |
| CogVideoX-5B | 20GB | 16GB+ | ❌ |
| SVD | 12GB | 14GB+ | ✅ |

### 离线包结构

```
offline-package/
├── README.md                  # 部署指南
├── INSTALL_GUIDE.txt          # 详细安装步骤
├── requirements-optimized.txt # 优化的依赖配置
├── download_models.py         # 模型下载脚本
├── install.sh                 # 一键安装脚本
├── scanner.py                 # 系统扫描工具
├── generation.py              # 主程序
└── models/                    # 模型目录（可选包含）
    └── modelscope/
```

---

## 🔧 故障排查

### 常见问题

#### 1. PyTorch 安装失败

**症状：** `pip install torch` 报错

**解决：**
```bash
# 手动指定源
pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# 或升级到最新 pip
pip install --upgrade pip
```

#### 2. 模型下载失败

**症状：** 下载速度慢或超时

**解决：**
```bash
# 使用镜像站
export HF_ENDPOINT=https://hf-mirror.com
python3 download_models.py -m modelscope

# 或手动下载后放到 models 目录
```

#### 3. 显存不足 (OOM)

**症状：** `CUDA out of memory`

**解决：**
```bash
# 降低分辨率
python3 generation.py -H 256 -W 256 ...

# 减少推理步数
python3 generation.py --steps 25 ...

# 启用 CPU offload（在代码中）
pipeline.enable_model_cpu_offload()
```

#### 4. CPU 模式太慢

**症状：** 生成一个视频需要几十分钟

**解决：**
```bash
# 减少步数
python3 generation.py --steps 20 ...

# 降低分辨率和帧数
python3 generation.py -H 128 -W 128 --duration 2 ...

# 或考虑升级 GPU
```

### 日志查看

```bash
# 查看扫描日志
cat scan_report.json | python3 -m json.tool

# 查看安装日志
tail -f venv/pip.log
```

---

## 📞 技术支持

- 扫描报告：`scan_report.json`
- 安装日志：`venv/` 目录
- 模型缓存：`./models/` 或 `~/.cache/huggingface/`

---

## 🎓 进阶使用

### 多 GPU 并行

```python
# generation_multi_gpu.py
import torch
from accelerate import dispatch_model

device_map = {
    "text_encoder": "cuda:0",
    "unet": "cuda:1",
    "vae": "cuda:1",
}

dispatch_model(pipeline, device_map=device_map)
```

### 模型量化

```bash
# INT8 量化（减小 50% 显存）
pip install optimum
python3 quantize_model.py --model cogvideox --bits 8
```

### Web UI 集成

```bash
# 安装 Gradio
pip install gradio

# 启动 Web 界面
python3 webui.py
```

---

## 📝 更新日志

- **v1.0.0** - 初始版本
  - 系统扫描与自动推荐
  - 一键安装脚本
  - 智能启动器
  - 离线包生成

---

**最后更新**: 2026-04-30
