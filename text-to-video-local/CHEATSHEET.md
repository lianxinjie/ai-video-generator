# AI 视频生成 - 快速参考卡片 🚀

## ⚡ 30 秒快速开始

```bash
# 1. 进入项目
cd text-to-video-local

# 2. 扫描系统
python3 scanner.py

# 3. 一键安装
bash install.sh

# 4. 激活环境
source venv/bin/activate

# 5. 生成视频
python3 run.py -p "一只猫在草地上奔跑" -o output.mp4
```

---

## 📝 命令速查表

### 系统扫描
```bash
python3 scanner.py                    # 快速扫描
python3 scanner.py -o report.json     # 保存报告
python3 scanner.py --generate-package # 生成离线包
```

### 安装
```bash
bash install.sh              # 一键安装
bash install.sh --skip-scan  # 跳过扫描
bash install.sh --skip-models # 跳过模型下载
```

### 模型下载
```bash
python3 download_models.py --from-scan    # 从报告读取
python3 download_models.py -m modelscope  # 下载指定模型
python3 download_models.py -m all -j 2    # 并行下载
python3 download_models.py --check-only   # 检查已下载
```

### 视频生成
```bash
python3 generation.py -m modelscope -p "提示词" -o output.mp4
python3 run.py -p "提示词"                  # 智能启动
python3 run.py --interactive               # 交互模式
```

### Docker
```bash
docker run --gpus all -v ./outputs:/app/outputs video-gen:latest
docker-compose --profile gpu up           # GPU 模式
docker-compose --profile cpu up           # CPU 模式
```

---

## 🎯 参数速查

### 主程序参数
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --model | -m | 模型名称 | modelscope |
| --prompt | -p | 提示词 | 必需 |
| --negative-prompt | -n | 负向提示词 | "" |
| --output | -o | 输出文件 | output.mp4 |
| --duration | -d | 时长 (秒) | 自动 |
| --fps | | 帧率 | 8 |
| --height | -H | 高度 | 256 |
| --width | -W | 宽度 | 256 |
| --steps | | 推理步数 | 50 |
| --guidance-scale | | 引导系数 | 7.5 |
| --seed | | 随机种子 | 随机 |
| --device | | 设备 | 自动 |

### 示例命令
```bash
python3 generation.py -m modelscope \
    -p "一只猫在草地上奔跑，阳光明媚" \
    -n "模糊，变形" \
    -o my_video.mp4 \
    -d 5 \
    --fps 8 \
    -H 512 -W 512 \
    --steps 50 \
    --guidance-scale 7.5 \
    --seed 42
```

---

## 🔧 性能优化速查

### 显存不足
```bash
# 降低分辨率
-H 256 -W 256

# 减少步数
--steps 25

# 缩短时长
-d 2

# CPU offload (代码中)
pipeline.enable_model_cpu_offload()
```

### CPU 模式
```bash
# 快速模式
--device cpu --steps 20 -H 128 -W 128

# 使用镜像站下载
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 📊 硬件推荐速查

| 配置 | 推荐模型 | 参数建议 |
|------|----------|----------|
| RTX 3090+ | CogVideoX | -H 512 -W 512 --steps 100 |
| RTX 3070 | AnimateDiff | -H 512 -W 512 --steps 50 |
| RTX 2060 | ModelScope | -H 256 -W 256 --steps 50 |
| GTX 1060 | ModelScope | -H 256 -W 256 --steps 25 |
| CPU only | ModelScope | -H 128 -W 128 --steps 20 |

---

## 🐛 故障排查速查

### CUDA OOM
```bash
nvidia-smi  # 查看显存
# 解决：-H 256 -W 256 --steps 25
```

### 下载失败
```bash
export HF_ENDPOINT=https://hf-mirror.com
python3 download_models.py -m modelscope
```

### 导入错误
```bash
pip install --upgrade pip
pip install torch diffusers transformers
```

---

## 📁 文件结构速查

```
text-to-video-local/
├── scanner.py              # 系统扫描
├── download_models.py      # 模型下载
├── run.py                  # 智能启动
├── install.sh              # 一键安装
├── generation.py           # 视频生成
├── model_quantize.py       # 模型量化
├── README.md               # 主文档
├── QUICKSTART.md           # 快速开始
└── requirements.txt        # 依赖
```

---

## 🐳 Docker 速查

```bash
# 构建镜像
docker build -t video-gen:latest .

# GPU 运行
docker run --gpus all -v ./outputs:/app/outputs video-gen:latest \
    python3 generation.py -m modelscope -p "测试" -o outputs/demo.mp4

# CPU 运行
docker run -v ./outputs:/app/outputs video-gen:cpu \
    python3 generation.py -m modelscope --device cpu -p "测试"

# 查看日志
docker logs -f video-gen-gpu
```

---

## 💡 常用提示词

```
基础:
- "一只猫在草地上奔跑"
- "一只狗在海滩上玩耍"
- "一只鸟在天空中飞翔"

高质量:
- "电影级画质，精细细节，4K 超高清"
- "专业摄影，自然光线，高清"
- "动画风格，宫崎骏风格，精美"

负向:
- "模糊，变形，低质量"
- "扭曲，噪声，artifacts"
```

---

## 📞 帮助命令

```bash
python3 generation.py --help
python3 scanner.py --help
python3 download_models.py --help
python3 run.py --help
bash install.sh --help
```

---

## 📖 文档索引

- **快速开始**: `QUICKSTART.md`
- **安装指南**: `README_INSTALL.md`
- **功能总览**: `README_FEATURES.md`
- **项目总览**: `PROJECT_OVERVIEW.md`

---

**祝你使用愉快！🎬**
