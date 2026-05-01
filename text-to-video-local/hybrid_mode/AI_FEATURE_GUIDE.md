# AI 智能分析功能使用指南

## 功能概述

新增 AI 智能分析功能，可以自动分析用户提示词，推荐最优的场景转换类型和艺术风格，无需用户手动选择。

## 使用方式

### 方式 1: 全自动模式（推荐）

```bash
# AI 自动分析并生成模板（最简单）
python hybrid_mode/generate.py template \
    -a \
    -p "cyberpunk city street, night to dawn, neon lights" \
    -o template.json
```

**AI 会自动判断：**
- 场景类型：time_lapse（因为有"night to dawn"时间变化）
- 艺术风格：cyberpunk（因为有"cyberpunk city, neon lights"）
- 自动生成合适的提示词序列

### 方式 2: 先分析，后生成

```bash
# 步骤 1: 查看 AI 分析结果
python hybrid_mode/generate.py analyze \
    -p "赛博朋克城市从日出到夜晚的变化，霓虹灯光"

# AI 会输出：
# 【场景类型分析】
#   推荐类型：time_lapse
#   置信度：80%
#   匹配关键词：时间、日出、夜晚、变化
#
# 【艺术风格分析】
#   推荐风格：cyberpunk
#   置信度：100%
#   匹配关键词：赛博朋克、霓虹

# 步骤 2: 如果满意，生成模板
python hybrid_mode/generate.py template \
    -a \
    -p "赛博朋克城市从日出到夜晚的变化，霓虹灯光" \
    -o template.json
```

### 方式 3: AI 推荐 + 手动微调

```bash
# AI 分析置信度中等，想手动指定场景类型
python hybrid_mode/generate.py template \
    -t iterative \
    -p "complex scene with multiple elements" \
    --style auto \
    -o template.json
```

## AI 识别能力

### 场景转换类型识别

| 识别类型 | 关键词示例 | 适用场景 |
|---------|-----------|---------|
| **time_lapse** | time, day, night, morning, evening, sunrise, sunset, changing, 时间, 日出，日落 | 同一场景在不同时间变化 |
| **zoom_sequence** | zoom, approach, close, detail, wide, far, near, focus, 推进，拉近，特写 | 镜头从远到近推进 |
| **pan_sequence** | move, walk, travel, explore, enter, leave, through, 移动，行走，旅行 | 从场景 A 移动到场景 B |
| **weather_change** | weather, rain, snow, storm, cloud, fog, 天气，雨，雪，风暴 | 同一场景在不同天气下 |
| **iterative_img2img** | story, sequence, action, character, person, 故事，情节，角色 | 有连续情节的叙事 |

### 艺术风格识别

| 识别风格 | 关键词示例 | 色彩推荐 |
|---------|-----------|---------|
| **cyberpunk** | cyberpunk, neon, futuristic, cyber, 赛博朋克，霓虹，未来 | 蓝、紫、粉、青 |
| **fantasy** | fantasy, magic, medieval, dragon, wizard, 奇幻，魔法，中世纪 | 金、绿、蓝、暖色 |
| **scifi** | sci-fi, spaceship, alien, space, technology, 科幻，太空，飞船 | 白、银、橙、金属色 |
| **natural** | nature, landscape, mountain, river, forest, 自然，风景，山，河 | 绿、棕、蓝、自然色 |
| **horror** | horror, dark, creepy, scary, ghost, 恐怖，黑暗，诡异 | 黑、暗红、灰、低饱和 |

## 置信度说明

AI 会给出置信度评估：

### 高置信度 (>60%)

```
✓ AI 分析置信度高，可直接生成模板:
  generate.py template -a -p "..." -o template.json
```

**处理方式：** 直接使用 AI 推荐，通常很准确！

### 中等置信度 (30%-60%)

```
⚠ AI 分析置信度中等，可：
  1. 直接使用：generate.py template -a -p "..." -o template.json
  2. 手动指定：generate.py template -t time_lapse -p "..." --style cyberpunk
```

**处理方式：** AI 有一定把握，用户可以自己决定是否信任

### 低置信度 (<30%)

```
⚠ AI 分析置信度低，建议手动指定参数:
  generate.py template -t iterative -p "..." --style custom
```

**处理方式：** 提示词特征不明显，建议手动指定类型和风格

## 实际应用示例

### 示例 1: 时间流逝视频

```bash
# 提示词包含"time"、"day to night"
python hybrid_mode/generate.py template \
    -a \
    -p "cyberpunk city, neon lights, time lapse from day to night" \
    -o cyberpunk_timelapse.json

# AI 识别:
# - 场景类型：time_lapse (80% 置信度)
# - 艺术风格：cyberpunk (100% 置信度)
```

### 示例 2: 视角推进视频

```bash
python hybrid_mode/generate.py template \
    -a \
    -p "medieval castle, zoom from far to close, fantasy style" \
    -o castle_zoom.json

# AI 识别:
# - 场景类型：zoom_sequence ("zoom"关键词)
# - 艺术风格：fantasy ("medieval", "fantasy"关键词)
```

### 示例 3: 叙事性视频

```bash
python hybrid_mode/generate.py template \
    -a \
    -p "a knight walking through a dark forest, encountering a dragon" \
    -o knight_story.json

# AI 识别:
# - 场景类型：iterative_img2img (有角色和情节)
# - 艺术风格：fantasy ("knight", "dragon"关键词)
```

### 示例 4: 中文提示词

```bash
python hybrid_mode/generate.py template \
    -a \
    -p "魔法师在古老城堡中施法，火焰和闪电，奇幻风格" \
    -o wizard_spell.json

# AI 识别:
# - 场景类型：iterative_img2img (有角色动作)
# - 艺术风格：fantasy (中世纪、魔法关键词)
```

## 自定义扩展

### 添加新的关键词

编辑 `ai_analyzer.py`：

```python
# 在 scene_type_keywords 中添加
self.scene_type_keywords["new_type"] = {
    "keywords": [
        "keyword1", "keyword2",
        "中文关键词"
    ],
    "description": "新类型描述"
}

# 在 style_keywords 中添加
self.style_keywords["new_style"] = {
    "keywords": ["style_keyword1", "风格关键词"],
    "colors": ["color1", "color2"],
    "description": "新风格描述"
}
```

## 优势总结

1. **零学习成本** - 用户无需了解 5 种场景类型的区别
2. **傻瓜式操作** - 一条命令完成所有配置
3. **智能推荐** - AI 根据内容自动判断
4. **置信度提示** - 明确告知用户 AI 的把握程度
5. **支持中英文** - 中文英文提示词都能识别
6. **可手动覆盖** - AI 推荐不准确时可手动指定

## 下一步

```bash
# 查看帮助
python hybrid_mode/generate.py --help
python hybrid_mode/generate.py template --help
python hybrid_mode/generate.py analyze --help

# 运行测试
python hybrid_mode/test_ai_analyze.py
```
