# AI 视频生成 - 快速启动指南 ⚡

> 3 分钟内完成安装和第一个视频生成

---

## 🎯 三步快速开始

### 第一步：系统扫描（1 分钟）

```bash
# 进入项目目录
cd text-to-video-local

# 扫描系统配置，生成最优方案
python3 scanner.py
```

**输出示例：**
```
======================================================================
 HARDWARE SCAN REPORT - 硬件扫描报告
======================================================================

【硬件摘要】
  CPU: Intel(R) Core(TM) i7-10700K (8 核)
  GPU 0: NVIDIA GeForce RTX 3080 (10.0GB)
  内存：32.0GB (可用：28.5GB)
  磁盘：256.0GB 可用 (SSD)
  网络：可用

【推荐方案】
  模式：GPU_MID_RANGE
  置信度：HIGH
  可用模型：modelscope, animatediff, svd
  下载优先级：modelscope → animatediff → svd

【优化建议】
  ✓ 建议使用 fp16 精度
  ✓ 启用 enable_model_cpu_offload()
======================================================================
```

### 第二步：一键安装（根据网络 5-30 分钟）

```bash
# 执行安装脚本
bash install.sh
```

**安装过程：**
```
[INFO] 步骤 1/6: 系统检测
[OK] Python: Python 3.10.12
[OK] 检测到 NVIDIA GPU: NVIDIA GeForce RTX 3080 (10.0GB)

[INFO] 步骤 2/6: 系统扫描
✓ 扫描报告已保存到：scan_report.json

[INFO] 步骤 3/6: 创建虚拟环境
✓ 虚拟环境已激活

[INFO] 步骤 4/6: 安装 PyTorch
✓ PyTorch GPU 版本安装完成

[INFO] 步骤 5/6: 安装依赖包
✓ 依赖安装完成

[INFO] 步骤 6/6: 下载模型
✓ modelscope 下载成功

===============================================
✓ 安装完成！
===============================================
```

### 第三步：生成第一个视频（30 秒）

```bash
# 激活虚拟环境
source venv/bin/activate

# 生成视频
python3 generation.py -m modelscope -p "一只猫在草地上奔跑" -o output.mp4
```

**输出：**
```
初始化视频生成器:
  - 模型：modelscope
  - 设备：cuda
  - 精度：float16

正在加载 modelscope 模型...
  - ModelScope 模型加载成功
  - 支持中文文本输入

开始生成视频:
  - 提示词：一只猫在草地上奔跑
  - 分辨率：256x256
  - 帧数：16
  - 帧率：8fps

生成完成！耗时：28.5 秒
视频已保存到：/path/to/output.mp4
```

🎉 **完成！查看生成的视频文件 `output.mp4`**

---

## 🚀 智能启动模式（推荐）

使用智能启动器自动选择最优配置：

```bash
# 自动根据扫描结果选择最优参数
python3 run.py -p "一只小狗在海滩上奔跑" -o demo.mp4
```

**交互模式（新手友好）：**
```bash
python3 run.py --interactive
```

**交互式提示：**
```
============================================================
 AI 视频生成 - 交互模式
============================================================

推荐配置:
  模式：gpu_mid_range
  可用模型：modelscope, animatediff, svd

请输入提示词（直接回车使用默认值）:
[一只猫在草地上奔跑] 一只小狗在海滩上奔跑

请选择模型:
  1. modelscope
  2. animatediff
  3. svd
[1] 

请输入输出文件名（直接回车使用默认值）:
[output.mp4] beach_dog.mp4

确认配置:
  模型：modelscope
  提示词：一只小狗在海滩上奔跑
  输出：beach_dog.mp4

开始生成？[Y/n] y
```

---

## 📦 Docker 快速部署

### GPU 模式

```bash
# 一行命令启动
docker run --gpus all -v ./outputs:/app/outputs video-generator:gpu-latest \
    python3 generation.py -m modelscope -p "测试视频" -o outputs/demo.mp4
```

### CPU 模式

```bash
docker run -v ./outputs:/app/outputs video-generator:cpu-latest \
    python3 generation.py -m modelscope --device cpu -p "测试视频" -o outputs/demo.mp4
```

### Docker Compose

```bash
# GPU 模式
docker-compose --profile gpu up video-generator-gpu

# 查看输出
docker-compose logs video-generator-gpu
```

---

## ⚙️ 常见场景

### 场景 1：快速测试

```bash
python3 run.py -p "测试" -o test.mp4
```

### 场景 2：高质量输出

```bash
python3 generation.py \
    -m cogvideox \
    -p "电影级画质，一只猫在花园中，4K 超高清" \
    -o high_quality.mp4 \
    -H 512 -W 512 \
    --steps 100 \
    --guidance-scale 9.0
```

### 场景 3：批量生成

```bash
# 创建批量脚本
cat > batch_generate.sh << 'EOF'
#!/bin/bash
prompts=(
    "一只猫在草地上奔跑"
    "一只狗在海滩上玩耍"
    "一只鸟在天空中飞翔"
)

for i in "${!prompts[@]}"; do
    python3 generation.py -m modelscope -p "${prompts[$i]}" -o "video_$i.mp4"
done
EOF

chmod +x batch_generate.sh
bash batch_generate.sh
```

### 场景 4：离线环境

```bash
# 【有网络环境】生成离线包
python3 scanner.py --generate-package --package-dir offline-package
bash install.sh

# 打包
tar -czf offline-package.tar.gz offline-package/

# 【离线环境】解压安装
tar -xzf offline-package.tar.gz
cd offline-package
bash install.sh --skip-scan
```

---

## 🔧 性能优化

### GPU 显存不足

```bash
# 降低分辨率
python3 generation.py -H 256 -W 256 ...

# 减少步数
python3 generation.py --steps 25 ...

# 缩短时长
python3 generation.py -d 2 ...
```

### CPU 模式太慢

```bash
# 最小配置
python3 generation.py \
    --device cpu \
    -H 128 -W 128 \
    --steps 20 \
    -d 2 \
    -p "简单测试"
```

### 使用优化配置

```bash
# 从扫描报告读取优化参数
python3 run.py --scan -p "优化后的生成"
```

---

## 📊 性能参考

| 配置 | 模型 | 分辨率 | 时长 | 耗时 |
|------|------|--------|------|------|
| RTX 3080 | ModelScope | 256x256 | 2 秒 | ~30 秒 |
| RTX 3080 | CogVideoX | 512x512 | 5 秒 | ~3 分钟 |
| CPU (i7) | ModelScope | 256x256 | 2 秒 | ~5 分钟 |
| CPU (i7) | ModelScope | 128x128 | 2 秒 | ~2 分钟 |

---

## ❓ 故障排查

### 问题 1：安装失败

```bash
# 查看详细日志
bash -x install.sh 2>&1 | tee install.log

# 手动安装依赖
pip3 install torch torchvision torchaudio
pip3 install -r requirements.txt
```

### 问题 2：模型下载慢

```bash
# 使用镜像站
export HF_ENDPOINT=https://hf-mirror.com
python3 download_models.py -m modelscope
```

### 问题 3：显存不足

```bash
# 查看 GPU 状态
nvidia-smi

# 清理显存
python3 -c "import torch; torch.cuda.empty_cache()"
```

---

## 📞 获取帮助

### 查看帮助

```bash
# 主程序帮助
python3 generation.py --help

# 扫描工具帮助
python3 scanner.py --help

# 下载工具帮助
python3 download_models.py --help
```

### 查看配置

```bash
# 显示当前推荐配置
python3 run.py --show-config

# 查看扫描报告
cat scan_report.json | python3 -m json.tool
```

---

## 🎓 下一步

安装成功后，可以：

1. 📖 阅读完整文档：`README_INSTALL.md`
2. 🧪 尝试不同模型：`python3 generation.py -m cogvideox ...`
3. 🎨 调整生成参数：`--steps`, `--guidance-scale`, `-H`, `-W`
4. 🌐 部署 Web UI（可选）
5. 🔄 批量生成视频

---

**祝使用愉快！🎬**
