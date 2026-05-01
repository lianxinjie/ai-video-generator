# 混合模式快速入门指南

## 5 分钟开始使用

### 前置要求

- ✅ 任意电脑（集成显卡即可）
- ✅ Python 3.10+
- ✅ FFmpeg（用于视频合成）

### 安装 FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. 访问 https://ffmpeg.org/download.html
2. 下载并解压
3. 将 `ffmpeg.exe` 所在目录添加到系统 PATH

### 步骤 1：生成提示词模板

```bash
cd text-to-video-local

# 生成迭代图生图模板（推荐）
python hybrid_mode/generate.py template \
    --type iterative \
    --base-prompt "cyberpunk city street, night, rain, neon reflections" \
    --style cyberpunk \
    --output prompts/iterative.json
```

**输出:**
```
✓ 模板已生成：prompts/iterative.json
  类型：iterative_img2img
  帧数：5
  风格：cyberpunk
```

### 步骤 2：云端生成图片

```bash
# 查看需要生成的提示词
python hybrid_mode/generate.py download \
    --template prompts/iterative.json \
    --output images
```

**手动生成步骤:**

1. 访问免费 AI 图片平台（推荐 SeaArt.ai）
2. 使用模板中的提示词依次生成
3. **关键：保持一致性**
   - 第 1 张用"文生图"
   - 第 2-5 张用"图生图"，上传前一张作为参考
   - 重绘幅度：0.3-0.5
4. 下载并重命名图片：
   - `image_001.jpg`, `image_002.jpg`, ..., `image_005.jpg`

**免费平台推荐:**
- SeaArt.ai (每日 60-100 积分)
- Tensor.art (每日 100 积分)
- Bing Image Creator

### 步骤 3：本地合成视频

```bash
python hybrid_mode/generate.py synthesize \
    --input images \
    --output video.mp4 \
    --fps 24
```

**添加背景音乐:**
```bash
python hybrid_mode/generate.py synthesize \
    --input images \
    --output video_with_audio.mp4 \
    --fps 24 \
    --audio bgm.mp3
```

### 步骤 4：查看成果

```bash
# Linux
mpv video.mp4

# macOS
open video.mp4

# Windows
start video.mp4
```

---

## 完整示例：制作 5 秒赛博朋克视频

### 1. 生成模板

```bash
python hybrid_mode/generate.py template \
    -t iterative \
    -p "cyberpunk street, neon lights, rain, detailed" \
    -o prompts/cyberpunk.json
```

**生成的提示词序列:**
```
[001] cyberpunk street, neon lights, rain, detailed, wide angle, empty scene
[002] cyberpunk street, neon lights, rain, detailed, distant figure
[003] cyberpunk street, neon lights, rain, detailed, figure approaching
[004] cyberpunk street, neon lights, rain, detailed, medium shot
[005] cyberpunk street, neon lights, rain, detailed, close up
```

### 2. 云端生成（在 SeaArt.ai）

**第 1 张（文生图）:**
```
cyberpunk street, neon lights, rain, detailed, wide angle, empty scene
生成 → 下载 → image_001.jpg
```

**第 2 张（图生图）:**
```
上传 image_001.jpg → 输入提示词 → 重绘幅度 0.4
生成 → 下载 → image_002.jpg
```

**重复到第 5 张...**

### 3. 本地合成

```bash
python hybrid_mode/generate.py synthesize \
    -i images \
    -o cyberpunk_video.mp4 \
    --fps 24
```

**输出:**
```
============================================================
 AI 视频合成 - 混合模式
============================================================

配置信息:
  输入目录：images
  输出文件：cyberpunk_video.mp4
  帧率：24fps
  图片时长：auto 秒
  转场效果：无
  音频文件：无
  放大倍数：1.0x
============================================================

找到 5 张图片
执行 FFmpeg 命令...
✓ 视频合成完成：cyberpunk_video.mp4

============================================================
 最终视频信息
============================================================
  文件：cyberpunk_video.mp4
  时长：0.2 秒
  大小：0.5MB
============================================================

✓ 完成！

资源消耗统计:
  - GPU 显存：0GB（集成显卡即可）
  - 内存：<2GB
  - 电力：约 50-100W
  - 对比本地 GPU 模式节省：90-95% 资源
```

---

## 常见问题

### Q: 图片一致性差怎么办？

**A:** 使用迭代图生图方法：
1. 每张都用前一张作为参考
2. 重绘幅度 0.3-0.5（太低变化小，太高不一致）
3. 基础提示词保持不变
4. 使用相同的随机种子（如果平台支持）

### Q: 免费额度不够怎么办？

**A:** 
- 多平台轮换（SeaArt + Tensor + Bing）
- 每日起额刷新后再用
- 总共约 200+ 张免费图片/天

### Q: 如何制作更长的视频？

**A:** 
- 增加图片数量（如 120 张 = 5 秒@24fps）
- 降低 fps（如 12fps，120 张=10 秒）
- 延长每张图片的持续时间

### Q: 视频质量不高？

**A:** 
1. 云端生成时使用高分辨率
2. 本地合成时使用高质量参数：
   ```bash
   python hybrid_mode/generate.py synthesize \
       -i images \
       -o video_hq.mp4 \
       --fps 24 \
       --upscale 2.0
   ```

### Q: 可以添加转场效果吗？

**A:** 
```bash
python hybrid_mode/generate.py synthesize \
    -i images \
    -o video_transition.mp4 \
    --fps 24 \
    --transition crossfade
```

---

## 进阶技巧

### 1. 使用 AI 优化提示词

用免费 AI 对话帮你写更好的提示词：

```
你：想做一个赛博朋克城市探索的 5 分钟视频

AI 助手：帮你生成 300 张连贯的图片提示词，包括：
- 开场：城市全景（20 张）
- 进入街道（50 张）
- 发现废弃建筑（40 张）
- 建筑内部探索（60 张）
- 顶层俯瞰城市（40 张）
- 日落离开（40 张）
- 片尾字幕（50 张）
```

### 2. 批量处理多个项目

```bash
# 项目 1
python hybrid_mode/generate.py synthesize \
    -i images_cyberpunk \
    -o videos/cyberpunk.mp4

# 项目 2
python hybrid_mode/generate.py synthesize \
    -i images_fantasy \
    -o videos/fantasy.mp4

# 项目 3
python hybrid_mode/generate.py synthesize \
    -i images_scifi \
    -o videos/scifi.mp4
```

### 3. 添加专业配音

**使用免费 TTS 服务:**
1. Edge TTS（微软免费接口）
2. 剪映/必剪的文本转语音
3.  ElevenLabs 免费额度

**添加配音:**
```bash
python hybrid_mode/generate.py synthesize \
    -i images \
    -o video_with_narration.mp4 \
    --audio narration.mp3
```

---

## 总结

混合模式让你：
- ✅ **零硬件成本**制作 AI 视频
- ✅ 用时间换金钱（90-95% 资源节省）
- ✅ 从简单开始，逐步进阶
- ✅ 验证需求后再决定是否投资硬件

**适合人群:**
- 学生
- 业余爱好者
- 预算有限的创作者
- 低配置电脑用户

**下一步:**
1. 尝试生成第一个视频
2. 熟练掌握后，可以尝试更多风格
3. 如果需求量大，再考虑升级到个人电脑模式

**帮助:**
```bash
python hybrid_mode/generate.py --help
python hybrid_mode/generate.py show-resources
python hybrid_mode/generate.py show-templates
```
