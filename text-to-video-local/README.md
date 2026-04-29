# Text-to-Video Local Deployment

可本地部署的智能文生视频程序

## 支持的模型

本项目支持多种开源文生视频模型：

| 模型名称 | 架构类型 | 显存需求 | 中文支持 | 部署难度 | 适用场景 |
|---------|---------|---------|---------|---------|---------|
| **AnimateDiff** | 基于 Stable Diffusion 的时序扩散模型 | 12GB+ | 中等 | 简单 | 短视频生成、动画制作 |
| **ModelScope** | 阿里达摩院文本到视频合成 | 8GB+ | 优秀 | 简单 | 中文内容生成 |
| **CogVideoX-5B** | 纯 Transformer 架构 | 16GB+ (单卡) / 2×A100 80G | 良好 | 中等 | 高质量视频生成 |
| **Open-Sora-Plan** | Sora 技术路线复现 | 4×A100 80G | 良好 | 困难 | 长时序高质量视频 |
| **Stable Video Diffusion** | Stability AI 视频扩散模型 | 16GB+ | 中等 | 中等 | 图生视频 |

## 硬件配置要求

### 入门级配置（推荐 AnimateDiff / ModelScope）

适合个人开发者和小型项目

- **GPU**: NVIDIA RTX 3090 (24GB) / RTX 4090 (24GB) / RTX 4080 (16GB)
- **显存**: 最低 12GB，推荐 24GB
- **CPU**: Intel i7 / AMD Ryzen 7 及以上
- **内存**: 32GB DDR4/DDR5
- **存储**: 500GB NVMe SSD（模型文件约 20-30GB）
- **系统**: Ubuntu 20.04+ / Windows 11 with WSL2
- **CUDA**: 11.8+

**预估价格**:
- RTX 4080 (16GB): ¥8,000-10,000
- RTX 4090 (24GB): ¥15,000-18,000
- 二手 RTX 3090 (24GB): ¥5,000-7,000

### 专业级配置（推荐 CogVideoX-5B）

适合研究机构和企业

- **GPU**: 2× NVIDIA A100 (40GB/80GB) 或 2× RTX 4090 (24GB)
- **显存**: 80GB+ (双卡)
- **CPU**: Intel Xeon / AMD EPYC, 32 核以上
- **内存**: 128GB+ ECC DDR4
- **存储**: 2TB NVMe SSD
- **系统**: Ubuntu 22.04 LTS
- **CUDA**: 12.1+
- **NVLink**: 推荐（双卡通信优化）

**预估价格**:
- 2× RTX 4090: ¥30,000-36,000
- 2× A100 40GB: ¥120,000-150,000

### 顶级配置（推荐 Open-Sora-Plan）

适合大规模视频生成服务

- **GPU**: 4× NVIDIA A100 (80GB) 或 4× H100 (80GB)
- **显存**: 320GB+
- **CPU**: AMD EPYC 7763 / Intel Xeon Platinum, 64 核以上
- **内存**: 512GB+ ECC DDR4
- **存储**: 4TB NVMe SSD (RAID 0)
- **系统**: Ubuntu 22.04 LTS
- **CUDA**: 12.1+
- **网络**: 10GbE 或 InfiniBand（多卡通信）

**预估价格**:
- 4× RTX 4090: ¥60,000-72,000
- 4× A100 80GB: ¥300,000-400,000+

## 快速开始

### 1. 环境检查

```bash
# 检查 GPU
nvidia-smi

# 检查 CUDA 版本
nvcc --version

# 检查 Python 版本
python3 --version
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux / macOS
# 或
venv\Scripts\activate  # Windows

# 安装基础依赖
pip install -r requirements.txt
```

### 3. 运行示例

```bash
python generation.py \
  --model modelscope \
  --prompt "一只可爱的小猫在草地上玩耍" \
  --output output/video.mp4 \
  --duration 5
```

## 目录结构

```
text-to-video-local/
├── generation.py          # 主程序
├── requirements.txt       # Python 依赖
├── config.yaml           # 配置文件
├── models/              # 模型管理
│   └── __init__.py
├── utils/               # 工具函数
│   ├── video_processor.py
│   └── text_encoder.py
└── examples/            # 示例输出
    └── sample_output.mp4
```

## 性能参考

### 生成速度（以 16 帧 256×256 视频为例）

| 硬件配置 | 生成时间 | 模型 |
|---------|---------|------|
| RTX 4090 | 2-3 分钟 | AnimateDiff |
| RTX 4090 | 5-8 分钟 | CogVideoX-5B |
| RTX 3090 | 3-5 分钟 | AnimateDiff |
| 2× A100 80G | 1-2 分钟 | CogVideoX-5B |
| 4× A100 80G | 30-60 秒 | Open-Sora-Plan |

## 注意事项

1. **显存优化**: 使用 `--fp16` 或`--quantize`参数可减少显存占用
2. **批量生成**: 建议使用 `batch_size=1` 避免显存溢出
3. **视频长度**: 初始建议使用 16-24 帧，后续可尝试更长视频
4. **分辨率**: 256×256 为默认，可根据显存调整

## 许可证

MIT License
