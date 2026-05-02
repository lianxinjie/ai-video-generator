# 分段文生图 + 合成视频 + 分层配音

## 核心优化

### 原文生视频流程

```
文本 → 视频生成 (16-64 帧，高显存) → 输出
- 显存：12-24GB
- 时间：5-10 分钟
- 模型：AnimateDiff/SVD (8-20GB)
```

### 优化后流程

```
文本 → 分段生图 (1 帧/次，低显存) → 合并 → 分层配音 → 输出
- 显存：4-8GB
- 时间：3-5 分钟
- 模型：SD 1.5/XL (2-7GB)
```

---

## 资源消耗对比

| 资源类型 | 原文生视频 | 分段优化 | 节省比例 |
|---------|----------|---------|---------|
| **显存需求** | 12-24GB | 4-8GB | **60-70%** ✅ |
| **生成时间** | 5-10 分钟 | 3-5 分钟 | **40-50%** ✅ |
| **电力消耗** | 0.5-1 度 | 0.2-0.4 度 | **50-60%** ✅ |
| **模型大小** | 8-20GB | 2-7GB | **60-75%** ✅ |
| **最低配置** | RTX 3060 | GTX 1650 | **门槛降低** ✅ |

---

## 核心优势

### 1. 分层配音策略

```
层级 1: 人物配音（每个小视频独立）
  ↓
层级 2: 合并为中型视频
  ↓
层级 3: 添加背景音乐/特效音
```

**优势：**
- ✅ 人物对话与时序精准同步
- ✅ 每个片段独立配音，易于修改
- ✅ BGM 和音效独立控制音量
- ✅ 后期调整更灵活

---

### 2. 分段生成策略

```
总时长 10 秒
  ↓
分为 5 段，每段 2 秒（16 帧）
  ↓
逐段生成图片 → 合并
```

**优势：**
- ✅ 显存占用稳定（不累积）
- ✅ 失败可单独重试某段
- ✅ 每段可使用不同提示词
- ✅ 支持断点续传

---

### 3. 时序一致性保证

```python
# 每段视频时长 = 配音时长 = 脚本时长
segment_duration = 2.0 秒
audio_duration = 2.0 秒（自动匹配）
video_duration = segment_duration × num_segments

# 确保音画同步
for each segment:
    generate_frames(duration=segment_duration)
    generate_audio(script, duration=segment_duration)
    # 自动对齐
```

---

## 使用方式

### 基础使用

```bash
python personal_mode/generate_segmented.py \
    -p "cyberpunk city street, neon lights, rain" \
    -d 10 \
    -s 2 \
    --output-dir output/cyberpunk_city
```

**参数说明：**
- `-p`: 基础提示词
- `-d`: 总时长（秒）
- `-s`: 每段时长（秒）
- `--output-dir`: 输出目录

**输出结构：**
```
output/cyberpunk_city/
├── segments/          # 各片段图片
│   ├── segment_001/   # 第 1 段
│   ├── segment_002/   # 第 2 段
│   └── ...
├── audio/             # 配音和 BGM
│   ├── segment_001_character.wav
│   ├── segment_002_character.wav
│   ├── character_combined.wav
│   └── background_music.wav
├── output/            # 最终视频
│   ├── video_only.mp4
│   ├── video_with_character.mp4
│   └── final_video.mp4
└── segment_tasks.json # 任务配置
```

---

### 添加人物配音

```bash
python personal_mode/generate_segmented.py \
    -p "魔法城堡，中世纪风格，塔楼高耸" \
    -d 10 \
    -s 2 \
    --character-voice zh-CN-XiaoxiaoNeural \
    --output-dir output/magic_castle
```

**支持的语音（微软 Edge TTS）：**

| 语音 ID | 语言 | 风格 |
|--------|------|------|
| zh-CN-XiaoxiaoNeural | 中文 | 温柔女声 ⭐推荐 |
| zh-CN-YunxiNeural | 中文 | 标准男声 |
| zh-CN-XiaoyiNeural | 中文 | 活泼女声 |
| en-US-JennyNeural | 英文 | 标准女声 |
| en-US-GuyNeural | 英文 | 标准男声 |
| ja-JP-NanamiNeural | 日文 | 标准女声 |

**自定义配音脚本：**

修改 `generate_segmented.py` 中的 `audio_scripts`：

```python
audio_scripts = [
    "这是一个神奇的地方",      # 第 1 段配音
    "看那座古老的城堡",        # 第 2 段
    "里面住着强大的魔法师",    # 第 3 段
    "他们在施展神秘的法术",    # 第 4 段
    "多么美丽的景象"          # 第 5 段
]
```

---

### 添加背景音乐和特效音

```bash
python personal_mode/generate_segmented.py \
    -p "森林小径，阳光透过树叶" \
    -d 10 \
    -s 2 \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/forest_ambience.mp3 \
    --bgm-volume 0.3 \
    --add-transition \
    --output-dir output/forest_path
```

**背景音乐控制：**
- `--bgm-file`: BGM 文件路径
- `--bgm-volume`: BGM 音量（0-1，默认 0.3）
- `--add-transition`: 添加转场效果

**添加特效音：**

编辑代码中的音频配置：

```python
audio_config = AudioConfig(
    character_voice='zh-CN-XiaoxiaoNeural',
    bgm_file='music/forest.mp3',
    bgm_volume=0.3,
    sfx_files=[
        'sfx/birds.mp3',      # 鸟叫声
        'sfx/wind.mp3',       # 风声
        'sfx/leaves.mp3'      # 树叶沙沙声
    ],
    sfx_volume=0.5
)
```

---

## 完整工作流示例

### 示例 1: 赛博朋克城市纪录片

```bash
# 创建项目目录
mkdir -p projects/cyberpunk_doc

# 生成视频
python personal_mode/generate_segmented.py \
    -p "cyberpunk city, neon lights, futuristic buildings, flying cars" \
    -d 15 \
    -s 3 \
    --character-voice zh-CN-YunxiNeural \
    --bgm-file music/cyberpunk_ambience.mp3 \
    --bgm-volume 0.25 \
    --output-dir projects/cyberpunk_doc
```

**配音脚本（5 段，每段 3 秒）：**
```python
audio_scripts = [
    "这是 2077 年的新东京市",
    "霓虹灯照亮了整个夜空",
    "飞行汽车在空中穿梭",
    "高科技与低生活的对比",
    "这就是赛博朋克的世界"
]
```

---

### 示例 2: 奇幻故事短片

```bash
python personal_mode/generate_segmented.py \
    -p "medieval fantasy castle, dragon flying above, magical atmosphere" \
    -d 20 \
    -s 4 \
    --character-voice zh-CN-XiaoxiaoNeural \
    --bgm-file music/epic_fantasy.mp3 \
    --bgm-volume 0.3 \
    --output-dir projects/fantasy_dragon
```

**配音脚本（5 段，每段 4 秒）：**
```python
audio_scripts = [
    "在遥远的王国边境，矗立着一座古老城堡",
    "传说中，城堡里住着一位强大的魔法师",
    "有一天，一条巨龙出现在了天空",
    "魔法师决定与巨龙进行沟通",
    "从此，王国迎来了和平的时代"
]
```

---

### 示例 3: 自然景观延时摄影

```bash
python personal_mode/generate_segmented.py \
    -p "beautiful mountain landscape, sunrise to sunset, time lapse" \
    -d 12 \
    -s 2 \
    --character-voice en-US-JennyNeural \
    --bgm-file music/nature_ambience.mp3 \
    --bgm-volume 0.4 \
    --output-dir projects/mountain_timelapse
```

**配音脚本（6 段，每段 2 秒）：**
```python
audio_scripts = [
    "The sun rises over the mountains",
    "Golden light spreads across the valley",
    "Clouds drift slowly in the sky",
    "The temperature rises, nature awakens",
    "Afternoon shadows grow longer",
    "The sun sets, painting the sky orange"
]
```

---

## 自定义配音脚本

### 方式 1: 修改代码（推荐）

编辑 `generate_segmented.py` 文件：

```python
# 找到这行（约 420 行）
audio_scripts = [
    "这是一个神奇的地方",
    "看那座古老的城堡",
    "里面住着魔法师",
    "他们在施展法术",
    "多么美丽的景象"
][:int(total_duration / segment_duration)]
```

修改为你自己的脚本：

```python
audio_scripts = [
    "第 1 段：介绍场景",
    "第 2 段：描述主体",
    "第 3 段：动作发生",
    "第 4 段：高潮部分",
    "第 5 段：结尾总结"
]
```

---

### 方式 2: 使用外部文件

创建 `audio_scripts.txt`：

```bash
# projects/my_video/audio_scripts.txt
这是一个美丽的地方
这里充满了生机
阳光洒在大地上
万物都在生长
多么美好的世界
```

修改代码读取文件：

```python
# 在 generate_segmented.py 中添加
script_file = project_dir.parent / "audio_scripts.txt"

if script_file.exists():
    with open(script_file, 'r', encoding='utf-8') as f:
        audio_scripts = [line.strip() for line in f.readlines() if line.strip()]
else:
    audio_scripts = [
        "默认脚本 1",
        "默认脚本 2",
        # ...
    ]
```

---

## 音频同步机制

### 自动时长匹配

```python
# 每段视频时长
segment_duration = 2.0 秒

# 自动生成对应时长的配音
for each segment:
    # 1. 生成配音
    audio = TTS(script, target_duration=segment_duration)
    
    # 2. 检查时长
    if len(audio) < segment_duration:
        # 添加静音填充
        audio = audio + silence(segment_duration - len(audio))
    elif len(audio) > segment_duration:
        # 裁剪超长部分
        audio = audio[:segment_duration]
    
    # 3. 确保音画同步
    video_duration = segment_duration
    audio_duration = segment_duration
    # 完美同步！
```

---

### 音量平衡

```python
# 音量配置
character_volume = 1.0    # 人物配音（100%）
bgm_volume = 0.3          # 背景音乐（30%）
sfx_volume = 0.5          # 特效音（50%）

# 自动混音
final_audio = character_audio.overlay(
    bgm_audio,
    gain_during_overlay=-10  # BGM 降低 10dB
)
```

---

## 性能优化技巧

### 1. 减少显存占用

```bash
# 使用更低的分辨率
python personal_mode/generate_segmented.py \
    -p "..." \
    --resolution 384x384 \
    --output-dir output/low_mem

# 使用 CPU offload
# 在代码中添加
pipeline.enable_model_cpu_offload()
```

---

### 2. 加速生成

```bash
# 减少每段时长（减少帧数）
python personal_mode/generate_segmented.py \
    -p "..." \
    -d 10 \
    -s 1.5 \      # 每段 1.5 秒（vs 默认 2 秒）
    --output-dir output/fast

# 减少推理步数
# 在代码中修改
num_inference_steps=20  # 默认 25
```

---

### 3. 提高质量

```bash
# 提高分辨率
python personal_mode/generate_segmented.py \
    -p "..." \
    --resolution 768x768 \
    --output-dir output/hq

# 增加推理步数
# 在代码中修改
num_inference_steps=30
```

---

## 常见问题

### Q1: 为什么配音和视频不同步？

**A:** 检查以下几点：
1. 确保每段时长配置正确（`-s` 参数）
2. 检查配音脚本时长（太长会被裁剪）
3. 查看日志中的时长信息

**调试方法：**
```python
# 在代码中添加调试输出
print(f"视频时长：{video_duration}")
print(f"配音时长：{audio_duration}")
print(f"差值：{abs(video_duration - audio_duration)}秒")
```

---

### Q2: 背景音乐太大声/太小声？

**A:** 调整 `--bgm-volume` 参数：
- 默认值：0.3（30%）
- 太大声：调低到 0.2 或 0.15
- 太小声：调高到 0.4 或 0.5

---

### Q3: 某段生成失败了怎么办？

**A:** 分段生成的优势就是可以单独重试：
```bash
# 只需重新运行，已生成的片段会自动跳过
python personal_mode/generate_segmented.py \
    -p "..." \
    -d 10 -s 2 \
    --output-dir output/my_video

# 程序会检查已生成的片段，只生成失败的
```

---

### Q4: 如何更换配音演员？

**A:** 修改 `--character-voice` 参数：
```bash
# 温柔女声
--character-voice zh-CN-XiaoxiaoNeural

# 标准男声
--character-voice zh-CN-YunxiNeural

# 英文女声
--character-voice en-US-JennyNeural
```

---

### Q5: 可以不加配音只加 BGM 吗？

**A:** 可以！不指定配音脚本即可：
```bash
# 配音脚本留空
audio_scripts = ["", "", "", "", ""]

# 或者不提供音频文件
# 程序会自动跳过配音步骤
```

---

## 总结

### 核心优势

✅ **节省资源：** 显存降低 60-70%  
✅ **灵活控制：** 每段独立，易于修改  
✅ **分层配音：** 人物+BGM+ 音效独立控制  
✅ **时序同步：** 自动匹配，确保音画同步  
✅ **断点续传：** 失败可单独重试某段  

### 适用场景

| 场景 | 推荐配置 |
|------|---------|
| 纪录片/解说 | 人物配音 + 轻柔 BGM |
| 故事短片 | 多角色配音 + 剧情 BGM + 音效 |
| 景观延时 | 可选配音 + 环境 BGM |
| 教程视频 | 清晰配音 + 无 BGM |

### 最佳实践

1. **先测试 1-2 段**，确认效果后再完整生成
2. **BGM 音量控制在 0.2-0.4**，不要盖过配音
3. **每段时长 2-3 秒**，平衡质量和速度
4. **配音脚本简短**，每段 1-2 句话为宜
5. **分段数 5-10 段**，总时长 10-30 秒最合适

🎬 **开始创作你的视频吧！**
