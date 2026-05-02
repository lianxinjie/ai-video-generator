# Hybrid Mode - 混合模式

## 🆕 新增功能 (v2.1)

**AI 智能配音** - 三层智能配音系统现已集成！

- ✅ **人物配音**（小分段 0.75 秒）：自动台词生成
- ✅ **场景音效**（中分段 2.5 秒）：环境音/动作音/情绪音
- ✅ **背景音乐**（整段循环）：BGM 智能混音
- ✅ **一键流程**：`generate.py full --voiceover`

详细文档：[VOICEOVER_GUIDE.md](VOICEOVER_GUIDE.md)

---

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
├── ai_analyzer.py          # AI 智能分析器（新增）
├── prompt_generator.py      # 提示词生成器（AI 辅助）
├── image_downloader.py      # 云端图片下载器
├── video_synthesizer.py     # 本地视频合成器
├── consistency_engine.py    # 一致性保持引擎
├── generate.py             # 主命令行工具
├── test_ai_analyze.py      # AI 分析测试脚本
└── templates/              # 提示词模板
    ├── time_lapse.json
    ├── zoom_sequence.json
    ├── pan_sequence.json
    └── scene_transition.json
```

---

## 新增 AI 智能分析功能

### 自动判断场景类型和风格

AI 可以分析用户提示词，自动选择最优配置：

```bash
# AI 全自动分析并生成模板
python hybrid_mode/generate.py template \
    -a \
    -p "cyberpunk city, neon lights, from night to dawn" \
    -o template.json
```

**AI 分析内容:**
- 🎯 场景转换类型（5 种）
  - time_lapse（时间流逝）
  - zoom_sequence（视角推进）
  - pan_sequence（空间移动）
  - weather_change（天气变化）
  - iterative_img2img（迭代图生图）

- 🎨 艺术风格（6 种）
  - cyberpunk（赛博朋克）
  - fantasy（奇幻）
  - scifi（科幻）
  - natural（自然）
  - horror（恐怖）
  - custom（自定义）

### 使用示例

```bash
# 仅分析，不生成模板
python hybrid_mode/generate.py analyze \
    -p "赛博朋克城市从日出到夜晚，霓虹灯光"

# 分析并保存结果为 JSON
python hybrid_mode/generate.py analyze \
    -p "..." \
    -o analysis.json

# AI 自动推荐生成模板
python hybrid_mode/generate.py template \
    -a \
    -p "中世纪城堡，魔法师施法，火焰闪电" \
    -o fantasy_castle.json

# AI 置信度低时手动指定
python hybrid_mode/generate.py template \
    -t iterative \
    -p "自定义场景" \
    --style cyberpunk
```

### AI 工作原理

1. **关键词匹配** - 内置场景类型和风格关键词库
2. **置信度计算** - 根据匹配程度打分（0-1）
3. **智能推荐** - 置信度>0.6 高，0.3-0.6 中，<0.3 低
4. **优化建议** - 提供提示词优化、转场、一致性建议

### 置信度处理

```python
if confidence > 0.6:
    # 高置信度，直接使用
    use_ai_recommendation()
elif confidence > 0.3:
    # 中等置信度，建议使用但可调整
    suggest_with_confirmation()
else:
    # 低置信度，建议手动指定
    suggest_manual_config()
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

## 配音功能

混合模式支持**三层智能配音**系统：

### 快速使用

```bash
# 1. 生成模板（自动分析配音脚本）
python hybrid_mode/generate.py template \
    -a -p "赛博朋克城市" -o template.json

# 2. 合成视频（添加 AI 配音）
python hybrid_mode/generate.py synthesize \
    -i ./images \
    -o video.mp4 \
    --voiceover \
    --template template.json \
    --character-voice zh-CN-XiaoxiaoNeural

# 3. 一键完整流程（推荐）
python hybrid_mode/generate.py full \
    -p "魔法城堡，奇幻冒险" \
    -d 10 \
    -o output \
    --voiceover \
    --character-voice zh-CN-YunxiNeural \
    --bgm-file music/fantasy.mp3
```

### 配音功能

- ✅ **人物配音**：AI 自动生成台词（小分段 0.75 秒）
- ✅ **场景音效**：环境音/动作音/情绪音（中分段 2.5 秒）
- ✅ **背景音乐**：智能混音和音量平衡
- ✅ **情绪识别**：自动匹配语音和语速
- ✅ **智能分工**：简单本地生成，复杂 AI 生成

📖 **详细文档**: [配音功能使用指南 (VOICEOVER_GUIDE.md)](VOICEOVER_GUIDE.md)

---

## 下一步

1. 运行 `python hybrid_mode/generate.py --help` 查看完整选项
2. 查看 `templates/` 目录获取预设模板
3. 使用 AI 对话生成自定义提示词模板
4. 尝试添加 AI 配音：`--voiceover` 参数
