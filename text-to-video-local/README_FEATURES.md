# AI 视频生成系统 - 功能总览

## 📁 项目结构

```
text-to-video-local/
├── generation.py              # 主程序 - 视频生成核心
├── scanner.py                 # 系统扫描与最优方案推荐 ⭐ NEW
├── download_models.py         # 智能模型下载器 ⭐ NEW
├── run.py                     # 智能启动器 ⭐ NEW
├── install.sh                 # 一键安装脚本 ⭐ NEW
├── model_quantize.py          # 模型量化工具 ⭐ NEW
├── requirements.txt           # Python 依赖
├── config.yaml                # 配置文件
├── Dockerfile                 # Docker 镜像构建
├── docker-compose.yml         # Docker 编排配置
├── README_INSTALL.md          # 安装指南
├── QUICKSTART.md              # 快速开始指南
└── README_FEATURES.md         # 本文档
```

---

## 🎯 核心功能模块

### 1. 系统扫描器 (`scanner.py`)

**功能：** 自动检测硬件配置，生成最优安装和运行方案

**特性：**
- ✅ CPU/GPU 型号和性能检测
- ✅ 内存和磁盘空间分析
- ✅ CUDA/cuDNN 版本识别
- ✅ Python 环境检查
- ✅ 网络连通性测试
- ✅ 智能推荐模型和配置
- ✅ 生成个性化离线包

**使用示例：**
```bash
# 完整扫描
python3 scanner.py -o scan_report.json

# 生成离线包
python3 scanner.py --generate-package --package-dir offline-package

# 查看报告
cat scan_report.json | python3 -m json.tool
```

**输出示例：**
```json
{
  "recommendation": {
    "mode": "gpu_mid_range",
    "suitable_models": ["modelscope", "animatediff", "svd"],
    "download_priority": ["modelscope", "animatediff", "svd"],
    "optimization_tips": ["启用 fp16 精度", "使用 CPU offload"],
    "estimated_time_minutes": 15.5
  }
}
```

---

### 2. 智能模型下载器 (`download_models.py`)

**功能：** 根据系统扫描结果，智能下载推荐的模型

**特性：**
- ✅ 支持从扫描报告读取推荐
- ✅ 多模型并行下载
- ✅ 断点续传
- ✅ 自动检查已存在模型
- ✅ HuggingFace 和 ModelScope 双源支持
- ✅ 下载进度显示

**使用示例：**
```bash
# 从扫描报告读取推荐
python3 download_models.py --from-scan

# 下载指定模型
python3 download_models.py -m modelscope animatediff

# 并行下载
python3 download_models.py -m all --parallel 2

# 检查已下载模型
python3 download_models.py --check-only
```

---

### 3. 一键安装脚本 (`install.sh`)

**功能：** 全自动化安装流程

**特性：**
- ✅ 系统环境自动检测
- ✅ 虚拟环境创建
- ✅ PyTorch GPU/CPU 自适应安装
- ✅ 依赖自动安装
- ✅ 模型自动下载
- ✅ 安装后测试

**安装步骤：**
```bash
# 标准安装
bash install.sh

# 跳过扫描（已有报告）
bash install.sh --skip-scan

# 跳过模型下载
bash install.sh --skip-models
```

**安装流程：**
```
步骤 1/6: 系统检测
  ✓ 检查 Python 环境
  ✓ 检查 pip
  ✓ 检测操作系统
  ✓ 检测 GPU
  ✓ 检查磁盘空间

步骤 2/6: 系统扫描
  ✓ 生成 scan_report.json
  ✓ 创建 offline-package/

步骤 3/6: 创建虚拟环境
  ✓ 创建 venv/
  ✓ 激活虚拟环境

步骤 4/6: 安装 PyTorch
  ✓ 根据 GPU 情况选择 GPU/CPU 版本

步骤 5/6: 安装依赖包
  ✓ 安装 requirements-optimized.txt

步骤 6/6: 下载模型
  ✓ 根据推荐下载模型

✓ 安装完成！执行测试...
```

---

### 4. 智能启动器 (`run.py`)

**功能：** 根据系统扫描结果，自动选择最优运行参数

**特性：**
- ✅ 自动选择最优模型
- ✅ 自动选择 GPU/CPU 模式
- ✅ 自动应用优化参数
- ✅ 交互模式（新手友好）
- ✅ 扫描后启动

**使用示例：**
```bash
# 自动模式（智能选择最优配置）
python3 run.py -p "一只猫在草地上奔跑" -o output.mp4

# 交互模式
python3 run.py --interactive

# 先扫描再运行
python3 run.py --scan -p "测试视频"

# 显示配置
python3 run.py --show-config
```

**智能选择逻辑：**
```
检测到 RTX 3080 (10GB)
  → 推荐模式：gpu_mid_range
  → 可选模型：modelscope, animatediff, svd
  → 优化参数：--height 512 --width 512 --steps 50
  → 自动应用：enable_model_cpu_offload()
```

---

### 5. 主程序 (`generation.py`)

**功能：** 视频生成核心程序

**支持的模型：**
| 模型 | 大小 | 推荐显存 | 特点 |
|------|------|----------|------|
| ModelScope | 2.5GB | 6GB+ | 支持中文，快速 |
| AnimateDiff | 8GB | 12GB+ | 基于 SD，可定制 |
| CogVideoX-5B | 20GB | 16GB+ | 高质量，Transformer |
| SVD | 12GB | 14GB+ | 图生视频 |

**命令行参数：**
```bash
python3 generation.py \
    -m modelscope                # 模型名称
    -p "一只猫在草地上奔跑"       # 提示词
    -n "模糊，变形"              # 负向提示词
    -o output.mp4                # 输出文件
    -d 5                         # 时长（秒）
    --fps 8                      # 帧率
    -H 256 -W 256                # 分辨率
    --steps 50                   # 推理步数
    --guidance-scale 7.5         # 引导系数
    --seed 42                    # 随机种子
    --device cuda                # 设备
```

---

### 6. 模型量化工具 (`model_quantize.py`)

**功能：** 减小模型显存占用，提升推理速度

**特性：**
- ✅ INT8 量化（减少 50% 显存）
- ✅ FP16 量化（保持精度）
- ✅ ONNX 格式转换（加速推理）
- ✅ 量化后性能测试

**使用示例：**
```bash
# INT8 量化
python3 model_quantize.py -m modelscope --bits 8 -o quantized/

# FP16 量化
python3 model_quantize.py -m cogvideox --bits 16 -o quantized/

# ONNX 转换
python3 model_quantize.py -m modelscope --onnx -o onnx_models/
```

---

## 🎯 GPU+CPU 协调模式 (新增!)

系统会根据您的硬件配置自动选择最优的协调模式：

### 协调模式速查表

| GPU 档次 | CPU 档次 | 模式名称 | 推荐模型 | 优化策略 |
|----------|----------|----------|----------|----------|
| **高端** (≥12GB) | **中/高** (6 核+) | `hybrid_high_end` | CogVideoX-5B | GPU 主导 + CPU 辅助 |
| **中端** (6-12GB) | **中/高** (6 核+) | `hybrid_mid_range` | ModelScope | 平衡模式 |
| **低端** (<6GB) | **低端** (4 核) | `hybrid_low_end` | ModelScope | 极简模式 |
| **中端** (6-12GB) | **低端** (4 核) | `gpu_mid_cpu_low` | ModelScope | GPU 主导 |
| **低端** (<6GB) | **中端** (6 核) | `gpu_low_cpu_mid` | ModelScope | CPU 辅助为主 |
| **高端** (≥12GB) | **低端** (4 核) | `gpu_high_cpu_low` | CogVideoX-5B | GPU 全负荷 |
| **<6GB** | 任意 | `gpu_very_low` | ModelScope | 极限模式 |

### 硬件档次标准

**GPU 档次**:
- **高端**: RTX 3080/3090/4080/4090 (显存≥12GB)
- **中端**: RTX 2060/3060/3070 (显存 6-12GB)
- **低端**: GTX 1060/1650/RTX 3050 (显存<6GB)

**CPU 档次**:
- **高端**: i7-10700K/i9-12900K/Ryzen 7/9 (8 核+)
- **中端**: i5-10600K/i5-12400/Ryzen 5 (6 核)
- **低端**: i3/老款 i5/赛扬 (4 核及以下)

### 查看您的协调模式

```bash
python3 scanner.py
```

**输出示例**:
```
【硬件档次评估】
  CPU 等级：MID (中端 - 平衡性能与质量)
  GPU 等级：HIGH (高端 - 适合高质量视频生成)

【推荐方案】
  模式：HYBRID_HIGH_END
  置信度：HIGH
  可用模型：cogvideox, svd, animatediff, modelscope
```

📚 **详细协调模式指南**: 查看 `HYBRID_MODE_GUIDE.md`

---

## 🚀 三种部署模式对比

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **Docker** | 生产环境，CI/CD | 隔离性好，易迁移 | 需要 Docker |
| **虚拟环境** | 开发，测试 | 灵活，易调试 | 依赖系统 Python |
| **离线包** | 无网络环境 | 完全离线 | 包体积大 |

---

## 💡 智能推荐系统

### 推荐逻辑

```python
# 伪代码示例
if gpu_available and vram >= 24GB and ram >= 32GB:
    mode = "gpu_high_end"
    models = ALL_MODELS
    priority = ["cogvideox", "svd", "animatediff", "modelscope"]
    
elif gpu_available and vram >= 12GB and ram >= 16GB:
    mode = "gpu_mid_range"
    models = ["modelscope", "animatediff", "svd"]
    priority = ["modelscope", "animatediff", "svd"]
    tips.append("启用 enable_model_cpu_offload()")
    
elif gpu_available and vram >= 6GB:
    mode = "gpu_low_end"
    models = ["modelscope"]
    tips.append("降低分辨率到 256x256")
    tips.append("减少 steps 到 25-30")
    
elif ram >= 16GB:
    mode = "cpu_capable"
    models = ["modelscope"]
    tips.append("使用 CPU 模式")
    tips.append("减少 steps 到 20")
    
else:
    mode = "cpu_limited"
    models = []
    warnings.append("系统资源不足，建议升级硬件")
```

---

## 📊 性能优化矩阵

| 优化项 | 显存节省 | 速度提升 | 质量影响 | 推荐场景 |
|--------|----------|----------|----------|----------|
| FP16 精度 | 50% | 2-3x | 微降 | 所有 GPU |
| CPU Offload | 30-40% | -10% | 无 | 显存不足 |
| Xformers | 20% | 1.5-2x | 无 | NVIDIA GPU |
| 降低分辨率 | 75% | 3-4x | 明显 | 快速测试 |
| 减少 Steps | 线性 | 线性 | 明显 | 草稿生成 |
| INT8 量化 | 50% | 1.2-1.5x | 微降 | 生产部署 |

---

## 🎯 典型使用场景

### 场景 1: 快速原型测试

```bash
# 使用智能启动器，自动选择最快配置
python3 run.py --scan -p "快速测试" -o test.mp4
```

### 场景 2: 高质量视频生成

```bash
python3 generation.py \
    -m cogvideox \
    -p "电影级画质，精细细节，4K" \
    -o masterpiece.mp4 \
    -H 512 -W 512 \
    --steps 100 \
    --guidance-scale 9.0
```

### 场景 3: 批量生产

```bash
# 创建批量脚本
cat > batch.sh << 'EOF'
#!/bin/bash
while IFS= read -r prompt; do
    python3 generation.py \
        -m modelscope \
        -p "$prompt" \
        -o "output_$(date +%s).mp4" \
        -d 3
done < prompts.txt
EOF

bash batch.sh
```

### 场景 4: 离线部署

```bash
# 1. 生成离线包
python3 scanner.py --generate-package --package-dir offline-package

# 2. 打包
tar -czf offline.tar.gz offline-package/

# 3. 离线环境部署
tar -xzf offline.tar.gz
cd offline-package && bash install.sh --skip-scan
```

---

## 🔍 故障诊断工具

### 系统扫描

```bash
python3 scanner.py
# 生成 scan_report.json，包含完整硬件和推荐信息
```

### 环境检查

```bash
# 查看扫描报告
cat scan_report.json

# 测试安装
python3 generation.py --check
```

### 性能监控

```bash
# GPU 监控
watch -n 1 nvidia-smi

# 内存监控
watch -n 1 free -h
```

---

## 📈 版本特性

### v1.0.0 (2026-04-30)

**新增功能:**
- ✅ 系统扫描器 `scanner.py`
- ✅ 智能模型下载器 `download_models.py`
- ✅ 智能启动器 `run.py`
- ✅ 一键安装脚本 `install.sh`
- ✅ 模型量化工具 `model_quantize.py`
- ✅ Docker 支持
- ✅ 离线包生成

**支持的模型:**
- ModelScope Text-to-Video
- AnimateDiff
- CogVideoX-5B
- Stable Video Diffusion

---

## 🎓 最佳实践

1. **先扫描再安装**
   ```bash
   python3 scanner.py  # 生成最优配置
   bash install.sh     # 自动应用推荐
   ```

2. **使用智能启动器**
   ```bash
   python3 run.py --scan  # 扫描并自动选择最优
   ```

3. **GPU 显存不足时**
   - 启用 CPU offload
   - 降低分辨率
   - 使用 INT8 量化
   - 选择小型模型

4. **批量生成时**
   - 多线程处理
   - 监控 GPU 温度
   - 定期清理显存

---

## 📞 技术支持

- 快速开始：`QUICKSTART.md`
- 安装指南：`README_INSTALL.md`
- 扫描报告：`scan_report.json`
- 离线包：`offline-package/`

---

**祝使用愉快！🎬**
