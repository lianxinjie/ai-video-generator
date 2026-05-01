# 个人电脑模式 - 视频分段生成系统

## 概述

专为低显存 GPU(1-8GB) 设计的视频生成方案，通过**分段生成 + 合并**的方式，用时间换性能。

### 核心特性

- ✅ **分段生成**: 将长视频分成多个短片段依次生成
- ✅ **资源监控**: 实时监控 GPU/CPU/内存/磁盘，超过阈值自动暂停
- ✅ **断点续传**: 关机后再开机可从中断处继续
- ✅ **智能等待**: 资源紧张时自动暂停，恢复后继续
- ✅ **视频合并**: 自动生成完整视频，支持过渡效果
- ✅ **AI 卸载**: 可选豆包 API 优化提示词，分担本地计算

---

## 快速开始

### 1. 安装依赖

```bash
cd text-to-video-local/personal_mode
pip install -r requirements.txt
```

### 2. 基础使用

```bash
# 生成 5 秒视频 (每段 0.5 秒，共 10 段)
python personal_mode/generate.py -p "蝴蝶在花丛中飞舞" -d 5 -c 0.5
```

### 3. 查看项目状态

```bash
python personal_mode/generate.py status --project-dir ./projects/butterfly
```

### 4. 合并视频

```bash
python personal_mode/generate.py merge --project-dir ./projects/butterfly --output final.mp4
```

---

## 详细配置

### 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p, --prompt` | 基础提示词 (必填) | - |
| `-d, --duration` | 总时长 (秒) | 5.0 |
| `-c, --chunk-duration` | 每段时长 (秒) | 0.5 |
| `-o, --output` | 输出文件名 | final_video.mp4 |
| `--project-dir` | 项目目录 | ./projects/default |
| `--gpu-threshold` | GPU 显存阈值 (%) | 75.0 |
| `--resolution` | 分辨率 (宽 x 高) | 512x512 |
| `--fps` | 帧率 | 8 |
| `-m, --model` | 模型选择 | modelscope |
| `--merge/--no-merge` | 是否合并视频 | --merge |
| `--transition` | 添加过渡效果 | --no-transition |
| `--cleanup` | 合并后删除片段 | --no-cleanup |
| `--ai-enhance` | AI 优化提示词 | --no-ai-enhance |

### 硬件推荐配置

| 配置 | 最低 | 推荐 | 理想 |
|------|------|------|------|
| GPU 显存 | 2GB | 4GB | 8GB+ |
| 系统内存 | 8GB | 16GB | 32GB |
| 磁盘空间 | 10GB | 50GB | 100GB+ |
| CPU 核心 | 4 核 | 8 核 | 12 核+ |

### GTX 1050 2GB 优化配置

```bash
python personal_mode/generate.py \
  -p "蝴蝶飞舞" \
  -d 3 \
  -c 0.5 \
  --resolution 384x384 \
  --gpu-threshold 70 \
  --fps 8 \
  --model modelscope
```

---

## 使用示例

### 示例 1: 基础使用

```bash
# 生成 5 秒视频
python personal_mode/generate.py -p "一只猫在草地上奔跑" -d 5
```

### 示例 2: 自定义分辨率

```bash
# 降低分辨率减少显存占用
python personal_mode/generate.py -p "风景" -d 5 --resolution 256x256
```

### 示例 3: 添加过渡效果

```bash
# 合并时添加淡入淡出效果
python personal_mode/generate.py -p "城市夜景" -d 10 --transition
```

### 示例 4: 使用 AnimateDiff 模型

```bash
# 使用 AnimateDiff 生成动画风格视频
python personal_mode/generate.py -p "卡通女孩微笑" -m animatediff
```

---

## 断点续传

### 场景 1: 生成中途关机

1. 程序会自动保存所有进度到 `projects/<dir>/tasks.json`
2. 重新开机后运行相同命令:

```bash
python personal_mode/generate.py -p "蝴蝶飞舞" -d 5
```

3. 程序会自动识别未完成的任务并继续

### 场景 2: 资源不足暂停

1. 当 GPU 显存超过 75% 时自动暂停
2. 等待资源恢复后自动继续
3. 可通过 `--gpu-threshold` 调整阈值

---

## 项目结构

```
projects/
└── default/
    ├── checkpoints/        # 检查点文件
    │   ├── chunk_001.json
    │   ├── chunk_002.json
    │   └── ...
    ├── chunk_001.mp4       # 视频片段
    ├── chunk_002.mp4
    ├── ...
    ├── tasks.json          # 任务状态
    ├── metadata.json       # 项目元数据
    ├── generation_report.txt  # 生成报告
    └── final_video.mp4     # 合并后的视频
```

---

## 资源监控

### 监控指标

- **GPU 显存**: 超过阈值自动暂停
- **GPU 温度**: 超过 80°C 自动暂停
- **CPU 使用率**: 超过 85% 自动暂停
- **系统内存**: 超过 80% 自动暂停
- **磁盘空间**: 超过 90% 自动暂停

### 暂停行为

1. 暂停当前任务
2. 清理 GPU 缓存
3. 等待 60 秒后检查资源
4. 资源恢复后继续执行

---

## AI 计算卸载 (可选)

### 配置豆包 API

```bash
export DOUBAO_API_KEY="your-api-key"
```

### 使用 AI 优化提示词

```bash
python personal_mode/generate.py -p "蝴蝶飞舞" --ai-enhance
```

### AI 功能

- 提示词优化
- 过渡建议
- 参数推荐

---

## 故障排查

### 问题 1: 显存不足

```bash
# 降低分辨率
--resolution 256x256

# 减少每段时长
--chunk-duration 0.3

# 降低 GPU 阈值
--gpu-threshold 65
```

### 问题 2: 任务连续失败

检查日志:
```bash
cat projects/default/*.log
```

清理检查点重新开始:
```bash
rm -rf projects/default/checkpoints/*
rm projects/default/tasks.json
```

### 问题 3: FFmpeg 未找到

安装 FFmpeg:

**Windows:**
```bash
winget install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## 性能预估

### GTX 1050 2GB 配置

| 总时长 | 分段数 | 每段时长 | 预估时间 |
|--------|--------|----------|----------|
| 3 秒 | 6 | 0.5 秒 | 15-20 分钟 |
| 5 秒 | 10 | 0.5 秒 | 25-35 分钟 |
| 10 秒 | 20 | 0.5 秒 | 50-70 分钟 |

### 优化建议

1. 使用较小分辨率 (256x256 或 384x384)
2. 减少推理步数 (15-25 步)
3. 较短的分段时长 (0.3-0.5 秒)
4. 及时清理 GPU 缓存

---

## 与现有代码集成

### 使用现有 VideoGenerator

```python
from generation import VideoGenerator
from personal_mode.task_manager import TaskScheduler

# 初始化和现有代码相同的 VideoGenerator
generator = VideoGenerator(
    model_name='modelscope',
    device='cuda'
)
generator.load_model()

# 使用个人模式任务调度器
scheduler = TaskScheduler(
    project_dir='./projects/test',
    pipeline=generator.pipeline
)

# 创建并执行任务
scheduler.create_tasks(total_duration=5.0, base_prompt="小猫奔跑")
scheduler.run_all_tasks()

# 合并结果
scheduler.merge_results(output_name="final.mp4")
```

---

## 高级功能

### 自定义监控阈值

```python
from personal_mode.monitor import ResourceMonitor

monitor = ResourceMonitor(
    gpu_memory_threshold=70.0,   # GPU 显存 70%
    gpu_temp_threshold=75.0,     # GPU 温度 75°C
    cpu_threshold=80.0,          # CPU 80%
    memory_threshold=75.0        # 内存 75%
)
```

### 添加背景音乐

```python
from personal_mode.merger import VideoMerger

merger = VideoMerger('./projects/default')
merger.add_background_music(
    video_file='final_video.mp4',
    music_file='bgm.mp3',
    output_file='final_with_music.mp4'
)
```

---

## 贡献与反馈

- 问题反馈：提交 Issue
- 功能建议：提交 Feature Request
- 代码贡献：提交 Pull Request

---

## 许可证

MIT License
