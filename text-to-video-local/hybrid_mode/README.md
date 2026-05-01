# Hybrid Mode - 混合模式

## 方案对比

### 原有个人电脑模式（本地 GPU 生成）

```
本地 GPU → 生成分段视频 → 合并 → 输出
```

**资源消耗:**
- GPU 显存：6-24GB
- 内存：16-64GB
- 电力：300-800W
- 时间：2-4 小时/5 分钟视频

### 新增混合模式（云端图片 + 本地合成）

```
AI 对话 (免费) → 生成提示词模板 → 云端免费图片 API → 本地 FFmpeg 合成视频
```

**资源消耗:**
- GPU 显存：0GB（集成显卡即可）
- 内存：4-8GB
- 电力：50-150W
- 电力节省：**90-95%**
- 硬件成本：**0 元**（无需独立显卡）
- 时间：3-6 小时（受免费额度限制，可后台运行）

---

## 核心优化点

### 1. 提示词生成优化

```python
# 由 AI 对话免费生成连贯的提示词序列
# 支持：
# - 场景转换规划
# - 时间流逝序列
# - 视角推进序列
# - 空间移动序列
# - 迭代图生图提示词
```

### 2. 云端图片批量生成

```python
# 调用多个免费平台 API
# - SeaArt.ai (每日 60-100 积分)
# - Tensor.art (每日 100 积分)
# - Bing Image Creator
# - 通义万相
# 支持图生图迭代，保持风格一致性
```

### 3. 本地轻量合成

```python
# 使用 FFmpeg/MoviePy 合成
# CPU 消耗：30-60W
# GPU 消耗：0W（集成显卡即可）
# 内存消耗：<2GB
```

---

## 使用方式

```bash
# 1. 生成提示词模板（AI 对话完成）

# 2. 批量下载图片

# 3. 本地合成视频
python hybrid_mode/generate.py \
    --prompt-template prompts.json \
    --input-dir ./images \
    --output video.mp4 \
    --fps 24 \
    --transition crossfade
```

---

## 文件结构

```
hybrid_mode/
├── prompt_generator.py      # 提示词生成器（AI 辅助）
├── image_downloader.py      # 云端图片下载器
├── video_synthesizer.py     # 本地视频合成器
├── consistency_engine.py    # 一致性保持引擎
├── generate.py             # 主命令行工具
└── templates/              # 提示词模板
    ├── time_lapse.json
    ├── zoom_sequence.json
    ├── pan_sequence.json
    └── scene_transition.json
```

---

## 资源对比表

| 资源类型 | 本地 GPU 模式 | 混合模式 | 节省比例 |
|---------|------------|---------|---------|
| GPU 显存 | 12-24GB | 0GB | 100% |
| 内存 | 32-64GB | 4-8GB | 75-87% |
| 存储 | 100-200GB | 1-2GB | 98% |
| 电力 | 1-2 度/次 | 0.05-0.1 度/次 | 90-95% |
| 硬件成本 | 5000-20000 元 | 0 元 | 100% |
| 部署时间 | 2-4 小时 | 10-30 分钟 | 90% |

---

## 适用场景

| 场景 | 推荐模式 |
|------|---------|
| 有高端 GPU，频繁使用 | 本地 GPU 模式 |
| 无独立显卡，偶尔制作 | 混合模式 ✅ |
| 预算有限 | 混合模式 ✅ |
| 隐私敏感项目 | 本地 GPU 模式 |
| 大规模批量生产 | 本地 GPU 模式 |
| 学习/个人创作 | 混合模式 ✅ |

---

## 一致性保持方案

### 迭代图生图工作流

```
图片 1 → 作为参考 → 图片 2 → 作为参考 → 图片 3
        + 提示词模板         + 提示词模板
```

**关键参数:**
- Denoising Strength: 0.3-0.5
- CFG Scale: 7-9
- 基础风格提示词：每张都重复

### AI 辅助提示词模板

```json
{
  "base_style": "cyberpunk city, neon lights, detailed architecture",
  "scene_sequence": [
    {"location": "rooftop", "shot": "wide", "time": "night"},
    {"location": "street", "shot": "medium", "time": "night"},
    {"location": "alley", "shot": "close", "time": "night"}
  ],
  "consistency_elements": ["neon colors", "architectural style", "lighting"]
}
```

---

## 下一步

1. 运行 `python hybrid_mode/generate.py --help` 查看完整选项
2. 查看 `templates/` 目录获取预设模板
3. 使用 AI 对话生成自定义提示词模板
