# 智能场景优化功能使用指南

## 功能概述

智能场景优化功能通过 **AI 分析 + 用户交互** 的方式，自动识别场景边界、评估连贯性、推荐转场效果，并提供场景合并建议，让视频生成更加智能和专业。

## 核心功能

### 1. AI 场景边界检测

自动识别提示词中的场景转换点：

**支持的场景边界类型：**

| 类型 | 识别模式 | 示例 |
|------|---------|------|
| **时间转换** | `from...to...`, `night to dawn` | "从夜晚到黎明", "day to night" |
| **空间转换** | `切换到`, `转到`, `camera pans` | "镜头转向街道", "switch to castle" |
| **镜头运动** | `zoom in`, `pan to`, `move to` | "推进到", "移至" |
| **场景结束** | `fade out`, `end with`, `最后` | "淡出", "最终" |

### 2. 场景连贯性评估

分析相邻场景之间的关系，提供 5 种连贯类型识别：

| 连贯类型 | 关键词示例 | 推荐转场 |
|---------|-----------|---------|
| `same_location` | 继续、仍然、still、same | 直接切换 (Cut) |
| `time_change` | 然后、接着、then、next | 渐变溶解 (Dissolve) |
| `location_change` | 切换到、转到、switch to | 平移转场 (Pan) |
| `action_change` | 开始、变成、begin、turn | 交叉溶解 (Cross Dissolve) |
| `contrast` | 但是、然而、but、however | 交叉溶解 (Cross Dissolve) |

### 3. 智能场景合并

基于相似度算法自动合并相似场景：

**相似度计算维度：**
- 词汇相似度（Jaccard 相似系数）50%
- 场景类型相似度 30%
- 艺术风格相似度 20%

**合并建议置信度：**
- **高**：相似度 ≥ 80%
- **中**：相似度 ≥ 60%
- **低**：相似度 < 60%（不合并）

### 4. 转场效果推荐

根据场景类型和连贯性智能推荐转场：

| 场景类型 | 推荐转场 |
|---------|---------|
| `time_lapse` | 渐变溶解 (Dissolve) |
| `zoom_sequence` | 推进转场 (Zoom In) |
| `pan_sequence` | 平移转场 (Pan) |
| `weather_change` | 交叉溶解 (Cross Dissolve) |
| `iterative_img2img` | 直接切换 (Cut) |
| `custom` | 渐变溶解 (Dissolve) |

### 5. 交互式优化流程

**工作流程：**

```
1. AI 分析提示词
   ↓
2. 检测场景边界
   ↓
3. 评估连贯性
   ↓
4. 生成优化建议
   ↓
5. 显示场景报告
   ↓
6. 用户确认/修改
   ↓
7. 应用优化
```

## 使用方法

### 命令行参数

```bash
# 启用智能场景分析 + 优化（默认启用）
python3 personal_mode/run.py -p "提示词" -d 10 -m collaborative \
  --enable-scene-analysis \
  --enable-scene-refine

# 自动确认所有优化建议（无需用户交互）
python3 personal_mode/run.py -p "提示词" -d 10 -m collaborative \
  --enable-scene-analysis \
  --enable-scene-refine \
  --auto-approve-changes

# 仅启用场景分析，不启用优化
python3 personal_mode/run.py -p "提示词" -d 10 -m collaborative \
  --enable-scene-analysis
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--enable-scene-analysis` | 启用智能场景分析（5 种场景类型 +6 种风格） | `False` |
| `--enable-scene-refine` | 启用智能场景优化（边界检测 + 连贯性评估） | `True` |
| `--auto-approve-changes` | 自动确认优化建议，无需用户确认 | `False` |

## 输出示例

### 场景边界检测

```
[07:18:18] [INFO] 检测到 2 个场景边界
[07:18:18] [INFO]   边界 1: night to dawn @ 位置 20
[07:18:18] [INFO]   边界 2: camera pans @ 位置 60
```

### 场景分析报告

```
======================================================================
 智能场景分析与优化
======================================================================

【场景统计】
  总分段数：3

【场景类型分布】
  time_lapse: 1 段 (33%)
  custom: 2 段 (67%)

【艺术风格分布】
  cyberpunk: 1 段 (33%)
  fantasy: 1 段 (33%)
  scifi: 1 段 (33%)

【转场建议】
  段 1 → 段 2: 渐变溶解 (Dissolve)
  段 2 → 段 3: 渐变溶解 (Dissolve)

【合并建议】
  段1, 段2 - 相似度 75% (置信度：高)

是否应用场景优化建议？[Y/n]:
```

### 优化后结果

```
[07:18:18] [INFO] 场景优化完成：3 段 → 2 段

✓ 场景优化完成：3 段 → 2 段
```

## 测试功能

运行独立测试脚本验证所有功能：

```bash
cd /workspace/text-to-video-local
python3 personal_mode/test_scene_refiner.py
```

**测试项目：**
1. ✅ 场景边界检测（4 种场景）
2. ✅ 连贯性评估（5 种类型）
3. ✅ 智能场景合并（相似度算法）
4. ✅ 完整报告生成（统计 + 转场建议）

## 实际案例

### 案例 1：时间流逝场景

**输入提示词：**
```
cyberpunk city from night to dawn, time lapse, neon lights
```

**检测结果：**
- 场景边界：`night to dawn @ 位置 20`
- 场景类型：`time_lapse`
- 艺术风格：`cyberpunk`
- 推荐转场：`渐变溶解 (Dissolve)`

### 案例 2：多镜头场景

**输入提示词：**
```
medieval castle, camera pans to dragon flying, then zoom in to knight
```

**检测结果：**
- 场景边界 1: `camera pans @ 位置 16`
- 场景边界 2: `zoom in @ 位置 41`
- 连贯类型：`action_change`
- 推荐转场：`平移转场 (Pan)` → `推进转场 (Zoom In)`

### 案例 3：相似场景合并

**输入分段：**
1. "cyberpunk city street, neon lights, night"
2. "cyberpunk city street with rain, neon lights reflecting"
3. "cyberpunk city alley, dark, same style"
4. "suddenly switch to peaceful forest, mountains"

**优化结果：**
- 段 1+2 合并（相似度 64%）
- 段 3 保持独立
- 段 4 保持独立
- **最终：3 段（优化前 4 段）**

## 与其他功能集成

### AI 配音分析

智能场景优化可与 AI 配音分析协同工作：

1. 先进行配音脚本分析
2. 再优化场景分配
3. 根据场景类型推荐配音情绪

### 协同模式

在协同模式中，场景优化影响任务分配：

- 优化后减少分段数 → 降低总生成时间
- 相似场景合并 → 一致性更好
- 转场建议 → 指导后期合成

## 注意事项

1. **场景边界检测依赖关键词**：如果提示词中没有明显的场景转换词，可能检测不到边界
2. **相似度阈值可调**：默认 0.7（70%），可在 `merge_similar_scenes` 中调整
3. **用户确认是可选的**：使用 `--auto-approve-changes` 可跳过确认
4. **与混合模式兼容**：场景类型和风格识别复用了混合模式的 `AIStyleAnalyzer`

## 技术实现

### 模块结构

```
personal_mode/
├── scene_refiner.py          # 智能场景整理器
│   ├── SceneRefiner          # 主类
│   │   ├── analyze_scene_boundaries()    # 边界检测
│   │   ├── evaluate_continuity()         # 连贯性评估
│   │   ├── merge_similar_scenes()        # 场景合并
│   │   ├── generate_scene_report()       # 报告生成
│   │   └── interactive_refine()          # 交互优化
│   │
├── collaborative_scheduler.py # 协同调度器
│   └── optimize_scenes()     # 场景优化入口
│
└── run.py                    # 统一启动器
    └── --enable-scene-refine # 新增参数
```

### 关键算法

**相似度计算：**
```python
similarity = (
    lexical_similarity * 0.5 +      # 词汇相似度
    type_similarity * 0.3 +         # 场景类型相似度
    style_similarity * 0.2          # 艺术风格相似度
)
```

**连贯性判断：**
- 检查连贯性关键词
- 计算共同词汇数量
- 基于规则匹配类型

## 未来扩展

- [ ] 支持更多场景边界模式
- [ ] 增加自定义转场效果
- [ ] 支持用户手动编辑场景边界
- [ ] 基于机器学习的连贯性评估
- [ ] 场景优化历史记录和回滚

## 相关链接

- [混合模式 AI 分析器](../hybrid_mode/ai_analyzer.py) - 场景类型和风格识别
- [协同调度器](collaborative_scheduler.py) - 智能任务分配
- [AI 配音分析](ai_voice_analyzer.py) - 配音脚本分析
