# Text-to-Video Local Deployment - 项目文件索引

## 核心文件

| 文件名 | 说明 | 重要性 |
|-------|------|--------|
| `generation.py` | 主程序，包含视频生成器 CLI | ⭐⭐⭐⭐⭐ |
| `requirements.txt` | Python 依赖列表 | ⭐⭐⭐⭐⭐ |
| `config.yaml` | 配置文件模板 | ⭐⭐⭐⭐ |

## 文档

| 文件名 | 说明 | 推荐阅读顺序 |
|-------|------|-----------|
| `QUICKSTART.md` | **5 分钟快速上手指南** | 1️⃣ |
| `README.md` | 项目概述和模型对比 | 2️⃣ |
| `EXAMPLES.md` | **使用示例和提示词模板** | 3️⃣ |
| `HARDWARE_GUIDE.md` | **硬件配置详细指南** | 4️⃣ |

## 部署脚本

| 文件名 | 平台 | 说明 |
|-------|------|------|
| `start.sh` | Linux / macOS | Bash 快速启动脚本 |
| `start.bat` | Windows | 批处理启动脚本（带菜单） |
| `Dockerfile` | 跨平台 | Docker 镜像构建文件 |
| `docker-compose.yml` | 跨平台 | Docker Compose 配置 |

## 其他

| 文件名 | 说明 |
|-------|------|
| `.gitignore` | Git 忽略配置 |
| `LICENSE` | MIT 许可证 |

## 目录结构

```
text-to-video-local/
├── generation.py          # 主程序入口
├── requirements.txt       # Python 依赖
├── config.yaml           # 配置文件
├── .gitignore           # Git 配置
├── LICENSE              # 许可证
│
├── README.md            # 项目说明
├── QUICKSTART.md        # 快速开始
├── EXAMPLES.md          # 使用示例
├── HARDWARE_GUIDE.md    # 硬件配置指南
│
├── start.sh             # Linux/macOS 启动脚本
├── start.bat            # Windows 启动脚本
├── Dockerfile           # Docker 镜像
└── docker-compose.yml   # Docker Compose

# 运行时自动创建的目录
├── models/              # 模型缓存目录（运行时创建）
└── outputs/             # 输出视频目录（运行时创建）
```

## 新手必读

如果你是第一次使用：

1. **阅读 [QUICKSTART.md](./QUICKSTART.md)** - 5 分钟快速上手
2. **运行安装脚本**：
   - Linux/macOS: `./start.sh setup`
   - Windows: 运行 `start.bat` 选择选项 1
3. **生成示例视频**：
   - Linux/macOS: `./start.sh demo`
   - Windows: 运行 `start.bat` 选择选项 4
4. **阅读 [EXAMPLES.md](./EXAMPLES.md)** - 学习如何编写提示词

## 开发者指南

### 项目架构

```
generation.py
├── VideoGenerator 类      # 核心视频生成器
│   ├── __init__()        # 初始化
│   ├── load_model()      # 加载模型
│   ├── generate()        # 生成视频
│   └── _save_video()     # 保存视频
│
├── CLI 命令              # 命令行接口
│   ├── generate          # 生成视频
│   └── check             # 检查环境
│
└── 模型支持
    ├── ModelScope        # 阿里达摩院模型
    ├── AnimateDiff       # 基于 SD 的动画模型
    ├── CogVideoX         # 纯 Transformer 模型
    └── SVD               # Stable Video Diffusion
```

### 添加新模型

1. 在 `VideoGenerator` 类中添加新的加载方法
2. 在 `generate()` 方法中添加对应的生成逻辑
3. 更新 CLI 的 `--model` 选项
4. 更新文档

### 性能优化建议

- 使用 `torch.compile`（PyTorch 2.0+）
- 启用 `xformers` 注意力优化
- 使用 Flash Attention（A100/H100）
- 实现模型量化（INT8/FP8）

## 硬件配置快速参考

### 最低配置
- GPU: RTX 3060 12GB
- 内存：32GB
- 存储：500GB SSD

### 推荐配置
- GPU: RTX 4090 24GB
- 内存：64GB
- 存储：1TB NVMe SSD

### 专业配置
- GPU: 2× RTX 4090 或 2× A100
- 内存：128GB+
- 存储：2TB+ NVMe SSD

详细配置请参考 [HARDWARE_GUIDE.md](./HARDWARE_GUIDE.md)

## 版本历史

### v1.0.0 (2026-04-29)
- ✅ 支持 ModelScope 模型
- ✅ 支持 AnimateDiff 模型
- ✅ 支持 CogVideoX-5B 模型
- ✅ 支持 Stable Video Diffusion
- ✅ 中文提示词优化
- ✅ 一键安装脚本
- ✅ Docker 支持
- ✅ 详细硬件配置指南

## 许可证

MIT License - 详见 [LICENSE](./LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！
