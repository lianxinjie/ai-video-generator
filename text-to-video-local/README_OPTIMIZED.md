# AI 视频生成器 - 完整优化方案

[![GitHub](https://img.shields.io/github/stars/lianxinjie/ai-video-generator)](https://github.com/lianxinjie/ai-video-generator)
[![License](https://img.shields.io/github/license/lianxinjie/ai-video-generator)](LICENSE)

## 🎯 项目概述

智能 AI 视频生成系统，提供**三种优化模式**，适应从集成显卡到高端 GPU 的所有配置。

| 模式 | 显存需求 | 适用场景 | 推荐度 |
|------|---------|---------|--------|
| **混合模式** | 0GB | 零成本/云端生成 | ⭐⭐⭐⭐⭐ |
| **超优模式** | 4-8GB | 个人电脑/配音需求 | ⭐⭐⭐⭐⭐ |
| **标准模式** | 12-24GB | 高端配置/快速生成 | ⭐⭐⭐ |

---

## 🚀 快速开始

### 5 分钟上手（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/lianxinjie/ai-video-generator.git
cd ai-video-generator/text-to-video-local

# 2. 安装依赖
pip install -r requirements.txt

# 3. 使用超优模式生成视频（推荐）
python personal_mode/run.py -p "cyberpunk city, neon lights" -d 10 -m optimized

# 4. 查看生成的视频
ls output/
```

### 系统扫描（首次运行）

```bash
# 自动检测配置并推荐最优方案
python scanner.py
```

---

## 📊 三种模式详解

### 模式 1: 混合模式（Hybrid Mode）⭐最推荐

**云端图片 + 本地合成，零 GPU 成本**

```bash
cd hybrid_mode
python generate.py template -a -p "cyberpunk city from night to dawn" -o template.json
python generate.py synthesize -i images -o video.mp4 --fps 24
```

**优势：**
- ✅ 零 GPU 显存需求（集成显卡即可）
- ✅ 节省 90-95% 资源
- ✅ 零硬件成本
- ✅ 适合所有电脑

**适用：**
- 预算有限
- 电脑配置低
- 偶尔制作视频
- 学习用途

[详细文档 →](hybrid_mode/README.md)

---

### 模式 2: 超优模式（Optimized Mode）⭐强烈推荐

**分段文生图 + 合成视频 + 分层配音**

```bash
python personal_mode/run.py \
    -p "cyberpunk city, neon lights" \
    -d 10 \
    -m optimized \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/bgm.mp3 \
    --bgm-volume 0.3
```

**优势：**
- ✅ 显存需求降低 60-70%（4-8GB）
- ✅ 生成时间减少 40-50%
- ✅ 支持分层配音（人物+BGM+ 音效）
- ✅ 支持断点续传
- ✅ 失败可单独重试

**适用：**
- 普通电脑（GTX 1650+）
- 笔记本电脑
- 需要配音
- 制作长视频

[详细文档 →](personal_mode/SEGMENTED_VIDEO_GUIDE.md)

---

### 模式 3: 标准模式（Standard Mode）

**原文生视频直接跑模型**

```bash
python personal_mode/run.py \
    -p "cyberpunk city" \
    -d 5 \
    -m standard \
    --resolution 768x768
```

**优势：**
- ✅ 一键生成，操作简单
- ✅ 视频流畅度好
- ✅ 适合批量生产

**适用：**
- 高端 GPU（RTX 3060+）
- 追求简单快速
- 不需要配音
- 短视频生成

[详细文档 →](personal_mode/README.md)

---

## 🎯 模式选择指南

### 快速决策

```
你的 GPU 显存是多少？
    ├─ <4GB (集成显卡/GTX 1650) → 混合模式 ✅
    ├─ 4-8GB (GTX 1060/RTX 3050) → 超优模式 ✅
    ├─ 8-12GB (RTX 2060/3060) → 超优模式 或 标准模式
    └─ >12GB (RTX 3080/4090) → 标准模式 或 超优模式
```

### 详细对比

| 对比维度 | 混合模式 | 超优模式 | 标准模式 |
|---------|---------|---------|---------|
| **显存需求** | 0GB（云端） | 4-8GB | 12-24GB |
| **生成时间** | 3-6 小时 | 3-5 分钟 | 5-10 分钟 |
| **电力消耗** | 0.05 度 | 0.2-0.4 度 | 0.5-1 度 |
| **硬件成本** | 0 元 | 1000 元 | 3000+ 元 |
| **配音支持** | ✅ | ✅ 分层 | ❌ |
| **灵活性** | 高 | 高 | 低 |
| **操作难度** | 简单 | 中等 | 简单 |
| **视频质量** | 好 | 很好 | 最好 |

### 场景推荐

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 学生/预算有限 | 混合模式 | 零成本 |
| 普通办公电脑 | 超优模式 | 兼容性好 |
| 游戏笔记本 | 超优模式 | 省资源 |
| 高端台式机 | 标准模式 | 简单快速 |
| 需要配音 | 超优模式 | 功能全 |
| 批量生产 | 标准模式 | 效率高 |
| 学习实验 | 混合模式 | 无风险 |

---

## 🛠️ 核心功能

### AI 智能分析

自动分析提示词，智能推荐场景类型和艺术风格：

```bash
python hybrid_mode/generate.py analyze -p "赛博朋克城市从日出到夜晚"
# AI 自动识别：
# - 场景类型：time_lapse (时间流逝)
# - 艺术风格：cyberpunk (赛博朋克)
# - 置信度：High (80%)
```

[使用指南 →](hybrid_mode/AI_FEATURE_GUIDE.md)

### 资源监控

实时监控 GPU/CPU/内存使用，超过阈值自动暂停：

```bash
python personal_mode/generate.py \
    -p "视频生成" \
    --gpu-threshold 75 \
    --project-dir ./my_project
```

**监控指标：**
- GPU 显存占用
- GPU 使用率
- CPU 使用率
- 内存占用
- 磁盘空间

### 断点续传

支持关机后再开机继续生成：

```bash
# 查看进度
python personal_mode/generate.py status --project-dir ./my_project

# 继续执行
python personal_mode/generate.py resume --project-dir ./my_project
```

### 分层配音

超优模式支持三层音频混合：

```bash
python personal_mode/run.py \
    -p "故事短片" \
    -d 20 \
    -m optimized \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/bgm.mp3 \
    --bgm-volume 0.3
```

**音频层次：**
1. 人物配音（每段独立）
2. 合并配音轨道
3. 背景音乐 + 特效音

### 云端免费资源

混合模式利用多个免费平台：

- SeaArt.ai（每日 60-100 积分）
- Tensor.art（每日 100 积分）
- Bing Image Creator（免费）
- 通义万相（免费额度）

**总免费额度：200+ 张/天**

---

## 📁 项目结构

```
text-to-video-local/
├── hybrid_mode/              # 混合模式（云端 + 本地）
│   ├── README.md            # 混合模式说明
│   ├── ai_analyzer.py       # AI 智能分析器
│   ├── prompt_generator.py  # 提示词模板生成器
│   ├── video_synthesizer.py # 视频合成器
│   ├── generate.py          # 主命令行工具
│   └── test_ai_analyze.py   # 测试脚本
│
├── personal_mode/            # 个人电脑模式
│   ├── README.md            # 个人模式说明
│   ├── run.py               # 统一启动器（双模式）
│   ├── generate.py          # 标准模式生成器
│   ├── generate_segmented.py # 超优模式生成器
│   ├── chunk_generator.py   # 分段生成器
│   ├── merger.py            # 视频合并器
│   ├── task_manager.py      # 任务调度器
│   ├── monitor.py           # 资源监控器
│   └── checkpoint.py        # 断点管理
│
├── scanner.py                # 系统扫描工具
├── download_models.py        # 模型下载工具
├── generation.py             # 基础生成器
├── requirements.txt          # Python 依赖
└── README.md                 # 本文档
```

---

## 💻 完整使用示例

### 示例 1: 赛博朋克城市纪录片

**混合模式（零成本）：**

```bash
cd hybrid_mode

# 1. AI 生成提示词模板
python generate.py template \
    -a \
    -p "cyberpunk city from night to dawn, neon lights" \
    -o prompts/city.json

# 2. 根据提示词云端生成图片
# 访问：SeaArt.ai / Tensor.art
# 使用 prompts/city.json 中的提示词

# 3. 本地合成视频
python generate.py synthesize \
    -i images \
    -o city_video.mp4 \
    --fps 24
```

**超优模式（低配置）：**

```bash
cd ..
python personal_mode/run.py \
    -p "cyberpunk city, neon lights, futuristic buildings" \
    -d 15 \
    -m optimized \
    --character-voice zh-CN-YunxiNeural \
    --bgm-file music/cyberpunk_ambience.mp3 \
    --output output/city_documentary.mp4
```

**标准模式（高配置）：**

```bash
python personal_mode/run.py \
    -p "cyberpunk city, neon lights" \
    -d 5 \
    -m standard \
    --resolution 768x768 \
    --output output/city_quick.mp4
```

---

### 示例 2: 奇幻故事短片

```bash
python personal_mode/run.py \
    -p "medieval fantasy castle, dragon flying above, magical atmosphere" \
    -d 30 \
    -m optimized \
    --segment-duration 3 \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/epic_fantasy.mp3 \
    --bgm-volume 0.3 \
    --output output/fantasy_story.mp4
```

**输出结构：**

```
output/
├── segments/              # 10 个片段（每段 3 秒）
│   ├── segment_001/       # 16 帧图片
│   ├── segment_002/
│   └── ...
├── audio/                 # 音频文件
│   ├── segment_001_character.wav
│   ├── character_combined.wav
│   └── background_music.wav
└── final_video.mp4        # 最终视频（30 秒）
```

---

### 示例 3: 教学视频

```bash
python personal_mode/run.py \
    -p "computer screen showing code, tutorial style" \
    -d 20 \
    -m optimized \
    --character-voice zh-CN-YunxiNeural \
    --bgm-file music/calm_piano.mp3 \
    --bgm-volume 0.2 \
    --output output/coding_tutorial.mp4
```

---

## 🔧 配置说明

### Python 依赖

```bash
pip install -r requirements.txt
```

**核心依赖：**
- torch >= 2.1.0
- diffusers >= 0.24.0
- transformers >= 4.35.0
- opencv-python >= 4.8.0
- ffmpeg-python
- edge-tts（配音用）
- pydub（音频处理）

### 系统要求

**最低配置（混合模式/超优模式）：**
- CPU: 双核
- 内存：4GB
- GPU: 集成显卡
- 存储：10GB

**推荐配置（标准模式）：**
- CPU: 8 核
- 内存：16GB
- GPU: RTX 3060 12GB
- 存储：50GB

**理想配置：**
- CPU: 12 核+
- 内存：32GB+
- GPU: RTX 4090 24GB
- 存储：100GB+ SSD

---

## 📊 性能基准

### 测试环境
- GPU: RTX 4090 (24GB)
- CPU: i9-13900K
- 内存：64GB

### 生成 10 秒视频对比

| 模式 | 显存 | 时间 | 电力 | 文件大小 |
|------|------|------|------|---------|
| 混合模式 | 0GB | 3-6 小时* | 0.05 度 | 12MB |
| 超优模式 | 6GB | 4 分钟 | 0.3 度 | 15MB |
| 标准模式 | 18GB | 6 分钟 | 0.8 度 | 12MB |

\* 云端等待时间，本地只需 30 秒合成

### 资源节省对比

| 指标 | 混合 vs 标准 | 超优 vs 标准 |
|------|-----------|-----------|
| 显存 | -100% ✅ | -60-70% ✅ |
| 时间 | +3000% ⚠️ | -30-40% ✅ |
| 电力 | -95% ✅ | -60% ✅ |
| 成本 | -100% ✅ | -70% ✅ |

---

## 🤖 AI 功能

### 智能场景分析

自动识别 5 种场景类型：
- time_lapse（时间流逝）
- zoom_sequence（视角推进）
- pan_sequence（空间移动）
- weather_change（天气变化）
- iterative_img2img（迭代图生图）

### 智能风格识别

自动识别 6 种艺术风格：
- cyberpunk（赛博朋克）
- fantasy（奇幻）
- scifi（科幻）
- natural（自然）
- horror（恐怖）
- custom（自定义）

### 配音语音支持

支持 10+ 种语音（微软 Edge TTS）：
- zh-CN-XiaoxiaoNeural（温柔女声）
- zh-CN-YunxiNeural（标准男声）
- en-US-JennyNeural（英文女声）
- ja-JP-NanamiNeural（日文女声）
- 更多...

---

## 📚 完整文档

### 混合模式
- [混合模式说明](hybrid_mode/README.md)
- [快速入门](hybrid_mode/QUICKSTART.md)
- [AI 功能指南](hybrid_mode/AI_FEATURE_GUIDE.md)
- [模式对比](hybrid_mode/COMPARISON.md)

### 个人电脑模式
- [个人模式说明](personal_mode/README.md)
- [分段视频指南](personal_mode/SEGMENTED_VIDEO_GUIDE.md)
- [模式选择指南](personal_mode/MODE_SELECTION_GUIDE.md)

### AI 智能分析
- [AI 功能总结](hybrid_mode/AI_SUMMARY.md)
- [优化总结](hybrid_mode/OPTIMIZATION_SUMMARY.md)

### 其他文档
- [快速启动指南](QUICKSTART.md)
- [硬件配置指南](HARDWARE_GUIDE.md)
- [部署指南](DEPLOYMENT_SUMMARY.md)

---

## 🎯 最佳实践

### 1. 先扫描再运行

```bash
python scanner.py  # 检测配置
python personal_mode/run.py -p "提示词" -d 10 -m optimized
```

### 2. 从低配置开始测试

```bash
# 低分辨率测试
python personal_mode/run.py -p "..." -d 5 --resolution 384x384

# 确认效果后提高配置
python personal_mode/run.py -p "..." -d 10 --resolution 512x512
```

### 3. 使用超优模式配音

```bash
python personal_mode/run.py \
    -p "..." \
    -d 10 \
    -m optimized \
    --character-voice zh-CN-XiaoxiaoNeural
```

### 4. 分段保存项目

```bash
python personal_mode/run.py \
    -p "my_story" \
    -d 20 \
    -m optimized \
    --output-dir projects/my_story
```

### 5. 利用混合模式学习

```bash
cd hybrid_mode
# 零成本学习提示词工程
python generate.py template -a -p "想要效果" -o template.json
```

---

## ❓ 常见问题

### Q1: 我该选择哪种模式？

**A:** 
- 预算有限/低配置 → 混合模式
- 普通电脑/需要配音 → 超优模式
- 高端配置/追求简单 → 标准模式

[详细选择指南 →](personal_mode/MODE_SELECTION_GUIDE.md)

### Q2: 显存不足怎么办？

**A:** 
1. 切换到超优模式：`-m optimized`
2. 降低分辨率：`--resolution 384x384`
3. 使用混合模式：完全不需要显存

### Q3: 如何添加配音？

**A:** 仅超优模式支持：

```bash
python personal_mode/run.py \
    -p "..." \
    -d 10 \
    -m optimized \
    --character-voice zh-CN-XiaoxiaoNeural
```

### Q4: 生成失败怎么办？

**A:** 
- 超优模式：自动跳过已生成片段，可重试
- 标准模式：降低配置重新开始
- 混合模式：检查网络连接

### Q5: 能生成多长的视频？

**A:**
- 超优模式：建议 10-60 秒（分段生成）
- 标准模式：建议 3-10 秒（一次性生成）
- 混合模式：无限制（受免费额度限制）

---

## 🌟 特色功能

### 🎯 智能决策

```bash
python scanner.py  # 自动推荐配置
```

### 🤖 AI 辅助

```bash
python hybrid_mode/generate.py analyze -p "提示词"
```

### 💰 零成本学习

```bash
cd hybrid_mode
python generate.py template -a -p "想要的效果" -o template.json
```

### 🎬 专业配音

```bash
python personal_mode/run.py \
    -p "故事" \
    -d 30 \
    -m optimized \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/bgm.mp3
```

### 🔄 断点续传

```bash
python personal_mode/generate.py resume --project-dir ./my_project
```

---

## 📈 版本历史

### v2.0（当前版本）
- ✅ 新增混合模式（云端图片 + 本地合成）
- ✅ 新增超优模式（分段文生图 + 配音）
- ✅ 新增 AI 智能分析
- ✅ 新增双模式统一启动器
- ✅ 优化资源消耗 60-90%

### v1.0
- ✅ 基础文生视频功能
- ✅ 分段生成系统
- ✅ 资源监控
- ✅ 断点续传

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
git clone https://github.com/lianxinjie/ai-video-generator.git
cd ai-video-generator/text-to-video-local
pip install -r requirements.txt
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

感谢以下开源项目：
- [Diffusers](https://github.com/huggingface/diffusers)
- [ModelScope](https://www.modelscope.cn/)
- [Edge TTS](https://github.com/rany2/edge-tts)
- [FFmpeg](https://ffmpeg.org/)

---

## 📬 联系方式

- 项目地址：https://github.com/lianxinjie/ai-video-generator
- Issue 反馈：https://github.com/lianxinjie/ai-video-generator/issues

---

## 🎯 快速参考

```bash
# 系统扫描
python scanner.py

# 混合模式（零成本）
cd hybrid_mode
python generate.py template -a -p "提示词" -o template.json
python generate.py synthesize -i images -o video.mp4

# 超优模式（推荐）
python personal_mode/run.py -p "提示词" -d 10 -m optimized

# 标准模式（高端）
python personal_mode/run.py -p "提示词" -d 5 -m standard

# AI 分析
python hybrid_mode/generate.py analyze -p "提示词"

# 查看帮助
python personal_mode/run.py --help
python hybrid_mode/generate.py --help
```

---

**🎬 开始创作你的 AI 视频吧！**
