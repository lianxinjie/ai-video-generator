# 快速开始指南

## 5 分钟快速上手

### 方式一：使用启动脚本（推荐）

#### Linux / macOS

```bash
# 1. 进入项目目录
cd text-to-video-local

# 2. 运行安装脚本
./start.sh setup

# 3. 生成示例视频
./start.sh demo

# 4. 查看生成的视频
ls -lh outputs/
```

#### Windows

```cmd
# 1. 进入项目目录
cd text-to-video-local

# 2. 运行安装脚本
start.bat

# 3. 选择选项 1 安装环境

# 4. 选择选项 4 运行示例
```

### 方式二：手动安装

#### 1. 环境要求

- Python 3.10 或更高版本
- NVIDIA GPU（推荐，显存至少 8GB）
- CUDA 11.8 或更高版本
- 50GB 可用磁盘空间

#### 2. 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd text-to-video-local

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p models outputs
```

#### 3. 检查环境

```bash
# 检查 GPU 和 CUDA
python generation.py check
```

#### 4. 生成第一个视频

```bash
# 使用 ModelScope 模型（推荐，支持中文）
python generation.py generate \
  --model modelscope \
  --prompt "一只可爱的小猫在草地上玩耍" \
  --output example.mp4 \
  --duration 3

# 观看生成的视频
# Linux:
mpv example.mp4
# Windows:
start example.mp4
# macOS:
open example.mp4
```

## 使用 Docker（可选）

如果不想手动安装依赖，可以使用 Docker：

```bash
# 1. 构建镜像
docker-compose build

# 2. 生成视频
docker-compose run --rm text-to-video generate \
  --model modelscope \
  --prompt "一只可爱的小猫" \
  --output /app/outputs/test.mp4 \
  --duration 3

# 3. 查看生成的视频
# 视频将保存在 ./outputs/ 目录
ls -lh outputs/
```

## 下一步

- 阅读 [EXAMPLES.md](./EXAMPLES.md) 了解更多使用示例
- 阅读 [HARDWARE_GUIDE.md](./HARDWARE_GUIDE.md) 了解硬件配置要求
- 尝试不同的模型和提示词

## 常见问题

### Q: 提示词应该怎么写？

**A:** 提示词应该详细描述你想生成的视频内容，包括：
- 主体（什么物体/人物/动物）
- 动作（在做什么）
- 环境（在哪里）
- 风格（什么艺术风格）

示例：
- "一只可爱的熊猫宝宝在竹林中吃竹子，阳光透过竹叶，温馨治愈"
- "壮丽的瀑布，水花飞溅，彩虹出现，自然风光纪录片风格"
- "未来城市夜景，飞行器穿梭，霓虹灯光，赛博朋克风格"

### Q: 生成速度慢怎么办？

**A:** 可以尝试以下方法：
1. 降低分辨率（`--height 256 --width 256`）
2. 减少帧数（`--duration 2`）
3. 减少推理步数（`--steps 25`）
4. 使用更强大的 GPU

### Q: 显存不足怎么办？

**A:** 
1. 使用半精度（默认已启用 `float16`）
2. 降低分辨率和帧数
3. 启用 CPU offload（可能会更慢）
4. 使用云端 GPU 服务

### Q: 视频质量不够好？

**A:**
1. 增加推理步数（`--steps 60` 或更高）
2. 提高分辨率（`--height 512 --width 512`）
3. 优化提示词描述，更详细具体
4. 尝试不同的模型

## 支持的模型

| 模型 | 特点 | 显存需求 | 中文支持 |
|-----|------|---------|---------|
| **modelscope** | 阿里达摩院，中文优化 | 8GB+ | ⭐⭐⭐⭐⭐ |
| **animatediff** | 基于 SD，动漫风格 | 12GB+ | ⭐⭐⭐ |
| **cogvideox** | 纯 Transformer，高质量 | 16GB+ | ⭐⭐⭐⭐ |
| **stable_video_diffusion** | 图生视频 | 16GB+ | ⭐⭐⭐ |

## 获取帮助

遇到问题？可以尝试：

1. 查看本快速开始指南
2. 阅读 [EXAMPLES.md](./EXAMPLES.md) 详细示例
3. 阅读 [README.md](./README.md) 项目说明
4. 查看项目 Issues

祝你使用愉快！🎬
