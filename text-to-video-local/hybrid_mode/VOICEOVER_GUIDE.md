# 混合模式 - AI 智能配音功能指南

## 🎯 功能概述

混合模式现已集成**三层智能配音系统**，支持：

1. **人物配音**（小分段 0.75 秒）
   - AI 自动生成台词脚本
   - 情绪识别和语音匹配
   - 本地 Edge TTS 生成

2. **场景音效**（中分段 2.5 秒）
   - 环境音（雨声、风声、车流等）
   - 动作音效（爆炸、撞击等）
   - 情绪音效（心跳、笑声等）

3. **背景音乐**（整段循环）
   - 用户提供 BGM
   - 智能音量平衡
   - 自动淡入淡出

---

## 🚀 快速开始

### 方式 1: 一键完整流程（推荐新手）

```bash
python hybrid_mode/generate.py full \
    -p "赛博朋克城市，霓虹灯闪烁，雨夜追逐" \
    -d 10 \
    -o output \
    --voiceover \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/cyberpunk.mp3
```

**自动完成：**
- ✅ AI 分析提示词
- ✅ 生成配音脚本
- ✅ 提示下载图片
- ✅ 合成视频 + 配音

---

### 方式 2: 分步执行（推荐高级用户）

#### 步骤 1: 生成模板 + 配音脚本

```bash
python hybrid_mode/generate.py template \
    -a \
    -p "赛博朋克城市从夜晚到黎明" \
    -o template.json
```

**输出示例：**
```
============================================================
 AI 智能配音分析
============================================================
  分析完成：共 20 段配音

  前 3 段示例:
    段 1: 赛博朋克城市，夜晚
           情绪：mysterious, 语速：140 字/分钟
    段 2: 霓虹灯闪烁
           情绪：excited, 语速：250 字/分钟
    段 3: 高楼林立
           情绪：epic, 语速：180 字/分钟

  配音建议:
    - 主导情绪：mysterious (12/20 段)
    - 推荐语音：zh-CN-XiaomengNeural
    - 平均语速：165 字/分钟
```

#### 步骤 2: 下载图片

按照模板中的提示词，前往云端平台生成图片：
- SeaArt.ai
- Tensor.art
- Bing Image Creator

#### 步骤 3: 合成视频 + 配音

```bash
python hybrid_mode/generate.py synthesize \
    -i ./images \
    -o video.mp4 \
    --voiceover \
    --template template.json \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/bgm.mp3 \
    --bgm-volume 0.3
```

---

## 📋 参数详解

### `template` 命令新增选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 自动触发 | 生成模板时自动分析配音 | - |

**无需额外参数**，生成模板时自动分析并保存配音脚本到 JSON 中。

### `synthesize` 命令新增选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--voiceover` | 启用 AI 配音 | ❌ 不启用 |
| `--template` | 模板文件（含配音脚本） | 无 |
| `--character-voice` | 配音语音 | zh-CN-XiaoxiaoNeural |
| `--bgm-file` | 背景音乐文件 | 无 |
| `--bgm-volume` | BGM 音量 (0.0-1.0) | 0.3 |

### `full` 命令完整参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p`, `--prompt` | 基础提示词 | **必填** |
| `-o`, `--output-dir` | 输出目录 | ./hybrid_mode/full_output |
| `-d`, `--duration` | 总时长（秒） | 5.0 |
| `--voiceover` | 启用 AI 配音 | ❌ |
| `--character-voice` | 配音语音 | zh-CN-XiaoxiaoNeural |
| `--bgm-file` | BGM 文件 | 无 |
| `--transition` | 转场效果 | crossfade |

---

## 🎬 使用示例

### 示例 1: 赛博朋克城市纪录片

```bash
# 生成模板
python hybrid_mode/generate.py template \
    -a \
    -p "cyberpunk city from night to dawn, neon lights" \
    -o cyberpunk.json

# 下载图片后合成
python hybrid_mode/generate.py synthesize \
    -i ./cyberpunk_images \
    -o cyberpunk_video.mp4 \
    --voiceover \
    --template cyberpunk.json \
    --character-voice zh-CN-YunxiNeural \
    --bgm-file music/cyberpunk_ambience.mp3
```

### 示例 2: 童话故事短片

```bash
# 一键完整流程
python hybrid_mode/generate.py full \
    -p "魔法城堡，公主和巨龙，奇幻冒险" \
    -d 15 \
    -o ./fairy_tale \
    --voiceover \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/fairy_tale.mp3 \
    --bgm-volume 0.25 \
    --transition crossfade
```

### 示例 3: 动作场景

```bash
python hybrid_mode/generate.py full \
    -p "激烈的战斗场景，爆炸和火焰，英雄与巨龙搏斗" \
    -d 10 \
    -o ./action_scene \
    --voiceover \
    --character-voice zh-CN-YunyangNeural \
    --bgm-file music/epic_battle.mp3 \
    --bgm-volume 0.3
```

---

## 🎛️ 配音语音选择

### 中文语音

| 语音名称 | 特点 | 适用场景 |
|---------|------|---------|
| `zh-CN-XiaoxiaoNeural` | 温柔女声 | 童话、故事、温和场景 |
| `zh-CN-YunxiNeural` | 标准男声 | 纪录片、解说、史诗 |
| `zh-CN-YunyangNeural` | 专业男声 | 新闻、紧张场景 |
| `zh-CN-XiaohanNeural` | 深情女声 | 悲伤、情感场景 |
| `zh-CN-XiaomengNeural` | 轻柔女声 | 神秘、悬疑场景 |

### 英文语音

| 语音名称 | 特点 |
|---------|------|
| `en-US-JennyNeural` | 标准女声 |
| `en-US-GuyNeural` | 标准男声 |
| `en-GB-SoniaNeural` | 英式女声 |

---

## 🎵 BGM 推荐

### 按情绪选择

| 情绪 | BGM 类型 | 示例文件名 |
|------|---------|-----------|
| **excited** (兴奋) | Upbeat/Electronic | `upbeat_electronic.mp3` |
| **calm** (平静) | Ambient/Piano | `calm_piano.mp3` |
| **tense** (紧张) | Suspense/Orchestral | `tension_build.mp3` |
| **sad** (悲伤) | Melancholy/Strings | `sad_strings.mp3` |
| **epic** (史诗) | Epic/Orchestral | `epic_heroic.mp3` |
| **mysterious** (神秘) | Mystery/Ambient | `mystery_ambient.mp3` |

### 音量建议

| 音频层 | 推荐音量 | 说明 |
|-------|---------|------|
| 人物配音 | 1.0 | 基准音量 |
| BGM | 0.2-0.3 | 不盖过人声 |
| 音效 | 0.3-0.5 | 根据场景调整 |

---

## 🔍 配音脚本结构

生成的模板 JSON 中包含配音脚本：

```json
{
  "type": "time_lapse",
  "total_frames": 20,
  "prompts": [...],
  "voiceover_script": [
    {
      "segment_index": 0,
      "start_time": 0.0,
      "end_time": 0.5,
      "voiceover": {
        "text": "赛博朋克城市，夜晚",
        "emotion": "mysterious",
        "voice": "zh-CN-XiaomengNeural",
        "speed": 140,
        "estimated_duration": 0.5
      }
    },
    ...
  ]
}
```

---

## ⚠️ 常见问题

### Q1: 配音功能需要额外安装依赖吗？

**A:** 需要安装以下依赖：

```bash
pip install edge-tts pydub
```

### Q2: 生成的配音声音太小/太大怎么办？

**A:** 调整 `--bgm-volume` 参数：

```bash
# BGM 太大
--bgm-volume 0.2

# BGM 太小
--bgm-volume 0.4
```

### Q3: 可以使用自己的配音而非 AI 生成吗？

**A:** 可以，使用 `--audio` 参数：

```bash
python hybrid_mode/generate.py synthesize \
    -i ./images \
    -o video.mp4 \
    --audio my_voiceover.mp3
```

### Q4: 配音和画面不同步怎么办？

**A:** 
1. 确保模板中的 `voiceover_script` 时长与视频匹配
2. 调整每段台词的语速
3. 使用 `--duration` 参数调整视频总时长

### Q5: 支持多角色配音吗？

**A:** 目前支持单一配音语音。多角色配音需要后期处理。

---

## 📊 性能影响

| 配置 | 无配音 | 有配音 |
|------|-------|-------|
| **配音生成时间** | - | +1-2 分钟 |
| **音频混合时间** | - | +30 秒 |
| **文件大小增加** | - | +5-10MB |
| **CPU 使用** | 低 | 中等 |
| **内存使用** | 4-8GB | 4-8GB |

---

## 🎯 最佳实践

### 1. 提示词优化

```bash
# ✅ 好的提示词（具体，有情绪）
"赛博朋克城市夜景，霓虹灯闪烁，小雨，紧张气氛"

# ❌ 差的提示词（模糊，无情绪）
"城市，晚上"
```

### 2. 配音选择

```bash
# 纪录片风格
--character-voice zh-CN-YunxiNeural

# 童话故事
--character-voice zh-CN-XiaoxiaoNeural

# 紧张场景
--character-voice zh-CN-YunyangNeural
```

### 3. BGM 选择

```bash
# 平静场景
--bgm-file music/calm_ambient.mp3
--bgm-volume 0.2

# 动作场景
--bgm-file music/action_epic.mp3
--bgm-volume 0.3
```

---

## 🔧 高级配置

### 自定义配音参数

编辑模板 JSON 中的 `voiceover_script`：

```json
{
  "voiceover_script": [
    {
      "voiceover": {
        "emotion": "excited",
        "speed": 250,
        "voice": "zh-CN-XiaoxiaoNeural"
      }
    }
  ]
}
```

### 手动调整混音

```bash
# 导出各层音频后手动混音
ffmpeg -i character.wav -i sfx.wav -i bgm.mp3 \
    -filter_complex \
    "[0:a][1:a][2:a]amix=inputs=3:duration=longest" \
    final_audio.wav
```

---

## 📈 未来计划

- [ ] 支持多角色配音
- [ ] AI 自动生成音效层
- [ ] 自动 ducking（人声触发 BGM 降低）
- [ ] 更多语音和语言支持
- [ ] 配音实时预览

---

## 📝 更新日志

### v2.1 (当前版本)
- ✅ 新增 AI 智能配音分析
- ✅ 三层配音架构
- ✅ 一键完整流程支持配音
- ✅ 音效分类库（6 大类 30+ 种）
- ✅ 智能音量平衡

### v2.0
- ✅ 基础视频合成功能
- ✅ 支持外部音频文件

---

**🎬 开始创作带专业配音的 AI 视频吧！**
