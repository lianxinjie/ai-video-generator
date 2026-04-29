# 使用示例

## 快速开始

### 1. 环境检查

```bash
# 检查 GPU 和 CUDA
python generation.py check
```

示例输出:
```
============================================================
系统环境检查
============================================================

Python 版本：3.11.5 (main, Sep 20 2023, 15:24:53) [Clang 14.0.0]
PyTorch 版本：2.1.0
CUDA 可用：True
CUDA 版本：12.1
GPU 数量：1

GPU 信息:
  GPU 0: NVIDIA GeForce RTX 4090
    - 显存：24.0GB
    - 计算能力：8.9

============================================================
```

### 2. 使用 ModelScope 生成视频（推荐入门）

```bash
# 简单示例
python generation.py generate \
  --model modelscope \
  --prompt "一只可爱的小猫在草地上玩耍" \
  --output examples/cute_cat.mp4 \
  --duration 3

# 高质量示例
python generation.py generate \
  --model modelscope \
  --prompt "春暖花开，樱花盛开，微风吹过，花瓣飘落" \
  --negative-prompt "模糊，变形，低质量" \
  --output examples/sakura.mp4 \
  --duration 5 \
  --fps 10 \
  --height 512 \
  --width 512 \
  --steps 60
```

### 3. 使用 AnimateDiff 生成视频

```bash
# 卡通风格
python generation.py generate \
  --model animatediff \
  --prompt "anime girl walking in the rain, cherry blossoms falling" \
  --negative-prompt "bad quality, worst quality, blurry, distorted" \
  --output examples/anime_girl.mp4 \
  --duration 2 \
  --fps 8 \
  --height 256 \
  --width 256 \
  --seed 42

# 风景动画
python generation.py generate \
  --model animatediff \
  --prompt "beautiful sunset over mountains, clouds moving, cinematic lighting" \
  --output examples/sunset.mp4 \
  --duration 4 \
  --fps 10 \
  --steps 50
```

### 4. 使用 CogVideoX-5B 生成高质量视频

```bash
# 需要较大显存（建议 20GB+）
python generation.py generate \
  --model cogvideox \
  --prompt "A panda eating bamboo in a forest, peaceful atmosphere" \
  --output examples/panda.mp4 \
  --duration 4 \
  --fps 8 \
  --height 480 \
  --width 480 \
  --steps 50 \
  --guidance-scale 7.5
```

## 提示词编写指南

### 中文提示词（ModelScope）

```bash
# 人物类
"一位穿着汉服的女子在花园中赏莲，古典风格，优雅"
"功夫大师在竹林中练武，动作流畅，中国风"

# 风景类
"桂林山水，漓江风光，云雾缭绕，水墨画风格"
"雪山日出，金光洒在雪峰上，壮观景色"

# 动物类
"大熊猫在竹林中悠闲地吃竹子，可爱温馨"
"锦鲤在池塘中游动，水波荡漾，吉祥寓意"

# 科幻类
"未来城市，飞行器穿梭在高楼大厦之间，赛博朋克风格"
"太空站俯瞰地球，星空璀璨，科幻感"
```

### 英文提示词（AnimateDiff / CogVideoX）

```bash
# 人物类
"A beautiful princess dancing in a ballroom, elegant dress, sparkling lights"
"A warrior in armor walking through a misty forest, epic atmosphere"

# 风景类
"Majestic waterfall in a tropical rainforest, mist rising, sunlight through trees"
"Ancient castle on a hilltop at sunset, dramatic sky, cinematic lighting"

# 动物类
"A majestic eagle soaring through the clouds, wings spread wide, slow motion"
"Colorful jellyfish floating in the deep ocean, bioluminescent glowing"

# 科幻类
"A futuristic robot city at night, neon lights, flying cars, cyberpunk style"
"An alien landscape with purple sky and floating rocks, otherworldly"
```

### 负向提示词模板

```bash
# 通用负向提示词
"bad quality, worst quality, blurry, distorted, deformed, ugly, watermark, text"

# 人物负向提示词
"extra limbs, missing limbs, bad anatomy, disfigured, poorly drawn hands"

# 风景负向提示词
"oversaturated, artificial, fake, low resolution, noisy artifacts"
```

## 性能优化技巧

### 1. 显存优化

如果显存不足，可以：

```bash
# 降低分辨率
python generation.py generate \
  --model modelscope \
  --prompt "测试视频" \
  --height 256 \
  --width 256 \
  --output low_res.mp4

# 减少帧数
python generation.py generate \
  --prompt "测试视频" \
  --duration 2 \
  --fps 8 \
  --output short.mp4

# 使用 CPU offload（会降低速度）
python generation.py generate \
  --prompt "测试视频" \
  --device cpu \
  --output cpu_output.mp4
```

### 2. 速度优化

```bash
# 减少推理步数（牺牲部分质量）
python generation.py generate \
  --prompt "快速生成" \
  --steps 25 \
  --output fast.mp4

# 降低引导系数
python generation.py generate \
  --prompt "快速生成" \
  --guidance-scale 5.0 \
  --output fast_low_cfg.mp4
```

### 3. 质量优化

```bash
# 增加推理步数
python generation.py generate \
  --prompt "高质量视频" \
  --steps 100 \
  --output high_quality.mp4

# 提高分辨率（需要更多显存）
python generation.py generate \
  --prompt "高清视频" \
  --height 512 \
  --width 512 \
  --output hd.mp4

# 提高帧率使视频更流畅
python generation.py generate \
  --prompt "流畅视频" \
  --fps 16 \
  --duration 3 \
  --output smooth.mp4
```

## 批量生成

创建批处理脚本 `batch_generate.sh`:

```bash
#!/bin/bash

# 定义提示词数组
prompts=(
    "一只可爱的小猫在草地上玩耍"
    "小狗在公园里跑步"
    "小鸟在树枝上唱歌"
    "小兔子在胡萝卜地里跳跃"
)

# 批量生成
for prompt in "${prompts[@]}"
do
    echo "正在生成：$prompt"
    python generation.py generate \
        --model modelscope \
        --prompt "$prompt" \
        --output "outputs/$(echo $prompt | md5sum | cut -d' ' -f1).mp4" \
        --duration 3 \
        --fps 8
    
    echo "完成: $prompt"
    echo "---"
done

echo "批量生成完成!"
```

使用方法:

```bash
chmod +x batch_generate.sh
./batch_generate.sh
```

## 使用配置文件

创建 `my_config.yaml`:

```yaml
model: modelscope
device: cuda
generation:
  duration: 4
  fps: 10
  height: 512
  width: 512
  num_inference_steps: 60
  guidance_scale: 7.5
  negative_prompt: "bad quality, blurry, distorted"
output:
  directory: ./my_outputs
```

使用方法:

```bash
# 通过配置文件运行（需要自行实现配置加载逻辑）
python generation.py generate \
  --config my_config.yaml \
  --prompt "使用配置文件生成视频"
```

## 常见问题

### Q1: 显存不足怎么办？

**解决方案**:
1. 降低分辨率（256×256）
2. 减少帧数（8-16 帧）
3. 启用 CPU offload
4. 使用半精度（--dtype float16）

### Q2: 生成速度太慢？

**解决方案**:
1. 减少推理步数（25-30 步）
2. 降低分辨率
3. 使用更强大的 GPU
4. 启用 xformers 加速

### Q3: 视频质量不佳？

**解决方案**:
1. 增加推理步数（60-100 步）
2. 调整引导系数（7.0-9.0）
3. 优化提示词描述
4. 添加更详细的环境和动作描述

### Q4: 中文提示词效果不好？

**解决方案**:
1. 使用 ModelScope 模型（对中文支持最好）
2. 尝试将中文翻译成英文
3. 使用更简洁的描述
4. 参考官方示例的提示词风格

## 输出示例

运行以下命令生成示例视频:

```bash
# 示例 1: 可爱动物
python generation.py generate \
  --model modelscope \
  --prompt "一只可爱的熊猫宝宝在竹林中玩耍，阳光透过竹叶洒下" \
  --output examples/panda.mp4 \
  --duration 4 \
  --height 256 \
  --seed 12345

# 示例 2: 风景
python generation.py generate \
  --model modelscope \
  --prompt "壮观的瀑布，水花飞溅，彩虹出现，自然风光" \
  --output examples/waterfall.mp4 \
  --duration 5 \
  --seed 67890

# 示例 3: 动漫风格
python generation.py generate \
  --model animatediff \
  --prompt "anime style girl with long hair walking on the street, cherry blossoms" \
  --output examples/anime.mp4 \
  --duration 3 \
  --seed 11111
```

生成完成后，视频文件将保存在 `examples/` 目录下。
