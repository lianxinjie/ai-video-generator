# GPU+CPU 协调模式推荐方案

> 基于硬件档次智能推荐最优配置

---

## 🎯 硬件档次分类标准

### CPU 档次

| 档次 | 核心数 | 典型型号 | 适用场景 |
|------|--------|----------|----------|
| **高端** | 8 核 + | i7-10700K, i9-12900K, Ryzen 7/9 | 高质量视频生成、批量处理 |
| **中端** | 6 核 | i5-10600K, i5-12400, Ryzen 5 | 日常使用、中等负载 |
| **低端** | 4 核及以下 | i3, 老款 i5, 赛扬 | 基础功能、轻度使用 |

### GPU 档次

| 档次 | 显存 | 典型型号 | 适用场景 |
|------|------|----------|----------|
| **高端** | ≥12GB | RTX 3080/3090/4080/4090 | 4K 视频生成、高质量渲染 |
| **中端** | 6-12GB | RTX 2060/3060/3070 | 1080p 视频、中等质量 |
| **低端** | <6GB | GTX 1060/1650, RTX 3050 | 基础功能、快速测试 |

---

## 📊 七种协调模式详解

### 模式 1: 高端 GPU + 中端/高端 CPU ⭐⭐⭐⭐⭐

**模式名称**: `hybrid_high_end`

**典型配置**:
- GPU: RTX 3080 10GB / RTX 3090 24GB
- CPU: i7-10700K (8 核) / i9-12900K (16 核)
- 内存：32GB+

**推荐模型**:
- ✅ **CogVideoX-5B** (首选)
- ✅ **SVD** (图生视频)
- ✅ **AnimateDiff** (风格化)
- ✅ **ModelScope** (快速生成)

**优化建议**:
1. ✓ GPU 主导 + CPU 辅助模式
2. ✓ 文本编码预处理交由 CPU 处理
3. ✓ GPU 专注扩散采样和 VAE 解码
4. ✓ 启用 `enable_model_cpu_offload()`
5. ✓ 使用分辨率：512x512 或更高
6. ✓ 推理步数：50-100

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| CogVideoX-5B | 512×512 | 5 秒 | 2-3 分钟 |
| SVD | 512×512 | 5 秒 | 1.5-2 分钟 |
| ModelScope | 256×256 | 2 秒 | 20-30 秒 |

**优势**: 大内存优势，可同时加载多个模型组件，减少 CPU-GPU 数据传输延迟

---

### 模式 2: 中端 GPU + 中端 CPU ⭐⭐⭐⭐

**模式名称**: `hybrid_mid_range`

**典型配置**:
- GPU: RTX 3060 12GB / RTX 2060 6GB
- CPU: i5-10600K (6 核) / i5-12400 (6 核)
- 内存：16GB

**推荐模型**:
- ✅ **ModelScope** (首选)
- ✅ **AnimateDiff** (中等质量)
- ✅ **SVD** (图生视频)
- ⚠️ CogVideoX-5B (需降低配置)

**优化建议**:
1. ✓ 平衡模式 - 性能与质量兼顾
2. ✓ 启用 `enable_model_cpu_offload()` 和 `enable_vae_slicing()`
3. ✓ 文本编码在 CPU 执行，扩散采样在 GPU 执行
4. ✓ 使用 fp16 精度，减少显存占用
5. ✓ 推荐分辨率：
   - ModelScope: 512×512
   - AnimateDiff: 256×256

**不推荐的场景**:
- ⚠️ CogVideoX-5B 需要降低分辨率到 256×256 并启用 CPU offload

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| ModelScope | 512×512 | 5 秒 | 1-1.5 分钟 |
| AnimateDiff | 256×256 | 2 秒 | 30-45 秒 |
| ModelScope | 256×256 | 2 秒 | 20-30 秒 |

---

### 模式 3: 低端 GPU + 低端 CPU ⭐⭐⭐

**模式名称**: `hybrid_low_end`

**典型配置**:
- GPU: GTX 1060 3GB / GTX 1650 4GB
- CPU: i3-9100 (4 核) / 老款 i5 (4 核)
- 内存：8GB

**推荐模型**:
- ✅ **ModelScope** (唯一推荐)
- ❌ 不推荐 AnimateDiff / SVD / CogVideoX

**优化建议**:
1. ✓ 极简模式 - 确保稳定性优先
2. ✓ CPU 负责所有预处理
3. ✓ GPU 仅负责核心推理
4. ✓ **必须启用** `enable_model_cpu_offload()`
5. ✓ 推荐分辨率：256×256 或 128×128
6. ✓ 推理步数：20-30

**警告**:
- ⚠️ 显存和 CPU 性能都有限，视频生成速度较慢
- ⚠️ AnimateDiff 和 SVD 可能因资源不足失败
- ⚠️ 建议单个任务完成后等待系统冷却再进行下一个任务

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| ModelScope | 256×256 | 2 秒 | 1-2 分钟 |
| ModelScope | 128×128 | 2 秒 | 30-60 秒 |

---

### 模式 4: 中端 GPU + 低端 CPU ⚠️

**模式名称**: `gpu_mid_cpu_low`

**典型配置**:
- GPU: RTX 3060 12GB
- CPU: i3-9100 (4 核)
- 内存：16GB

**推荐模型**:
- ✅ **ModelScope** (首选)
- ✅ **AnimateDiff** (可尝试)
- ❌ 不推荐 CogVideoX / SVD

**优化建议**:
1. ✓ GPU 主导模式 - 减少 CPU 负担
2. ✓ 文本编码也尝试在 GPU 上执行 (如果显存允许)
3. ✓ 使用 `enable_model_cpu_offload()` 但减少 CPU 预处理
4. ✓ 推荐分辨率：256×256
5. ✓ 推理步数：25-35

**警告**:
- ⚠️ CPU 性能不足可能导致预处理时间较长
- ⚠️ CogVideoX-5B 和 SVD 不建议使用

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| ModelScope | 256×256 | 2 秒 | 45 秒 -1 分钟 |
| AnimateDiff | 256×256 | 2 秒 | 1-1.5 分钟 |

---

### 模式 5: 低端 GPU + 中端 CPU ⚠️

**模式名称**: `gpu_low_cpu_mid`

**典型配置**:
- GPU: GTX 1650 4GB
- CPU: i5-10600K (6 核)
- 内存：16GB

**推荐模型**:
- ✅ **ModelScope** (唯一推荐)
- ❌ 不推荐其他模型

**优化建议**:
1. ✓ CPU 辅助为主模式
2. ✓ 尽量让 CPU 承担预处理和后处理任务
3. ✓ GPU 仅用于核心扩散采样
4. ✓ **必须启用** `enable_model_cpu_offload()`
5. ✓ 推荐分辨率：256×256
6. ✓ 推理步数：20-30

**警告**:
- ⚠️ GPU 显存不足，无法运行大型模型
- ⚠️ 速度较慢，建议耐心等待

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| ModelScope | 256×256 | 2 秒 | 1.5-2 分钟 |

---

### 模式 6: 高端 GPU + 低端 CPU 🐢

**模式名称**: `gpu_high_cpu_low`

**典型配置**:
- GPU: RTX 3080 10GB / RTX 3090 24GB
- CPU: i3-9100 (4 核)
- 内存：16GB

**推荐模型**:
- ✅ **CogVideoX-5B** (可使用)
- ✅ **SVD** (可使用)
- ✅ **AnimateDiff** (可使用)
- ✅ **ModelScope** (快速)

**优化建议**:
1. ✓ GPU 全负荷模式 - 用 GPU 性能弥补 CPU 瓶颈
2. ✓ 尽量在 GPU 上执行所有可能的计算
3. ✓ CPU 仅处理最基础的 I/O 和后处理
4. ✓ 可使用 CogVideoX-5B，但预处理时间较长
5. ✓ 推荐分辨率：512×512

**警告**:
- ⚠️ CPU 可能成为瓶颈，特别是在批量生成时
- ⚠️ 建议单次生成，避免多任务并行

**性能预期**:
| 模型 | 分辨率 | 时长 | 预计耗时 |
|------|--------|------|----------|
| CogVideoX-5B | 512×512 | 5 秒 | 3-4 分钟 (含预处理) |
| ModelScope | 256×256 | 2 秒 | 20-30 秒 |

---

### 模式 7: 显存<6GB 🔴

**模式名称**: `gpu_very_low`

**典型配置**:
- GPU: GT 1030 2GB / 集成显卡
- CPU: 任意
- 内存：8GB

**推荐模型**:
- ✅ **ModelScope** (勉强可用)
- ❌ 不推荐其他所有模型

**优化建议**:
1. ✓ **必须启用** `--cpu-offload` 参数
2. ✓ 强烈建议使用 CPU 模式
3. ✓ 降低分辨率到 128×128
4. ✓ 减少推理步数到 15-20

**警告**:
- ⚠️ 显存严重不足 (<6GB)，视频生成可能失败
- ⚠️ 强烈建议使用 CPU offload 模式或考虑升级硬件

---

## 🎮 使用示例

### 查看自己的硬件档次

```bash
# 运行系统扫描
python3 scanner.py

# 查看结果
cat scan_report.json | python3 -m json.tool
```

### 示例输出

```
【硬件档次评估】
  CPU 等级：MID (中端 - 平衡性能与质量)
  GPU 等级：HIGH (高端 - 适合高质量视频生成)

【推荐方案】
  模式：HYBRID_HIGH_END
  置信度：HIGH
  可用模型：cogvideox, svd, animatediff, modelscope
  下载优先级：cogvideox → svd → animatediff → modelscope

【优化建议】
  ✓ 【高端 GPU+ 中端 CPU】推荐模式：GPU 主导 + CPU 辅助
  ✓ 文本编码预处理交由 CPU 处理，GPU 专注扩散采样和 VAE 解码
  ✓ 推荐使用 CogVideoX-5B，可开启全部性能选项
  ✓ 启用 enable_model_cpu_offload() 进一步优化显存
  ✓ 建议分辨率：512x512 或更高，steps: 50-100
```

### 根据推荐运行

```bash
# 智能启动模式（自动应用最优配置）
python3 run.py -p "一只猫在草地上奔跑" -o output.mp4

# 手动指定参数（基于推荐）
python3 generation.py \
    -m cogvideox \
    -p "一只猫在草地上奔跑" \
    -o output.mp4 \
    -H 512 -W 512 \
    --steps 50 \
    --guidance-scale 7.5
```

---

## 📈 各模式性能对比

| 模式 | CPU | GPU | 推荐模型 | 2 秒视频耗时 | 质量上限 |
|------|-----|-----|----------|-----------|----------|
| hybrid_high_end | i7 8 核 | RTX 3080 | CogVideoX | 2-3 分钟 | ⭐⭐⭐⭐⭐ |
| hybrid_mid_range | i5 6 核 | RTX 3060 | ModelScope | 1-1.5 分钟 | ⭐⭐⭐⭐ |
| hybrid_low_end | i3 4 核 | GTX 1650 | ModelScope | 1-2 分钟 | ⭐⭐⭐ |
| gpu_mid_cpu_low | i3 4 核 | RTX 3060 | ModelScope | 45 秒 -1 分钟 | ⭐⭐⭐ |
| gpu_low_cpu_mid | i5 6 核 | GTX 1650 | ModelScope | 1.5-2 分钟 | ⭐⭐⭐ |
| gpu_high_cpu_low | i3 4 核 | RTX 3080 | CogVideoX | 3-4 分钟 | ⭐⭐⭐⭐⭐ |
| gpu_very_low | 任意 | GT 1030 | ModelScope | 3-5 分钟 | ⭐⭐ |

---

## 🎯 快速参考表

| GPU 档次 | CPU 档次 | 推荐模式 | 首选模型 |
|----------|----------|----------|----------|
| 高端 | 中/高 | hybrid_high_end | CogVideoX-5B |
| 中端 | 中/高 | hybrid_mid_range | ModelScope |
| 低端 | 低端 | hybrid_low_end | ModelScope |
| 中端 | 低端 | gpu_mid_cpu_low | ModelScope |
| 低端 | 中端 | gpu_low_cpu_mid | ModelScope |
| 高端 | 低端 | gpu_high_cpu_low | CogVideoX-5B |
| <6GB | 任意 | gpu_very_low | ModelScope |

---

## 🔧 优化技巧通用指南

### 所有模式通用

1. **启用 CPU offload**
   ```python
   pipeline.enable_model_cpu_offload()
   ```

2. **使用 fp16 精度** (GPU 模式)
   ```python
   pipeline = CogVideoXPipeline.from_pretrained(
       "THUDM/CogVideoX-5b",
       torch_dtype=torch.float16
   )
   ```

3. **启用 VAE 切片**
   ```python
   pipeline.enable_vae_slicing()
   ```

4. **启用 xformers 加速** (NVIDIA GPU)
   ```python
   pipeline.enable_xformers_memory_efficient_attention()
   ```

### 根据瓶颈优化

**CPU 瓶颈**:
- 增加 `--steps` 而不是降低分辨率
- 使用 GPU 主导模式
- 减少批量任务数量

**GPU 瓶颈**:
- 降低分辨率 (`-H 256 -W 256`)
- 减少推理步数 (`--steps 25`)
- 启用 CPU offload

**内存瓶颈**:
- 关闭其他应用
- 使用较小的批处理大小
- 启用 gradient checkpointing

---

**根据您的需求选择合适的模式，最大化利用硬件资源！🚀**
