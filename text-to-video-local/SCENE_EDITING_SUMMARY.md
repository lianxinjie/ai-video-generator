# 场景查看与编辑功能总结

## 📋 更新概览

本次更新为 AI 视频生成器添加了**场景查看和编辑功能**，用户可以在智能切分后查看场景列表，并进行修改调整。

---

## ✨ 新增功能

### 1. 场景查看器（SceneViewer）

**功能**：
- ✅ 显示场景列表（总数量、总时长）
- ✅ 详细模式：显示提示词、时长、参考图、配音、类型等
- ✅ 简洁模式：只显示基本信息
- ✅ 导出到 JSON 配置文件
- ✅ 从 JSON 文件导入

**使用示例**：
```python
from personal_mode.scene_viewer import SceneViewer

viewer = SceneViewer(verbose=True)
viewer.load_scenes(scenes)
viewer.display_scenes(show_details=True)
viewer.export_to_json('scenes.json')
```

### 2. 场景编辑器（SceneEditor）

**功能**：
- ✅ 编辑场景提示词
- ✅ 调整场景时长
- ✅ 添加新场景（指定位置）
- ✅ 删除指定场景
- ✅ 批量修改

**使用示例**：
```python
from personal_mode.scene_viewer import SceneEditor

editor = SceneEditor(scenes)
editor.edit_scene(2, prompt="新提示词", duration=6.0)
editor.add_scene(3, {'prompt': '新场景', 'duration': 5.0})
editor.delete_scene(1)
```

### 3. 交互式菜单

**命令行交互模式**：
```
可用命令:
  view         - 查看所有场景
  edit <编号>  - 编辑指定场景
  add <位置>   - 添加新场景
  delete <编号>- 删除场景
  export <文件> - 导出到 JSON
  import <文件> - 从 JSON 导入
  done         - 完成编辑
  quit         - 退出（不保存）
```

### 4. Web 场景确认页面

**访问地址**：http://localhost:5000/scenes/confirm?task_id=<id>

**功能**：
- ✅ 可视化场景卡片列表
- ✅ 点击卡片进入编辑模式
- ✅ 实时修改提示词和时长
- ✅ 添加/删除场景
- ✅ 实时统计总时长
- ✅ 保存并继续生成

---

## 🔌 API 接口

### 1. 分析场景

```http
POST /api/analyze
Content-Type: multipart/form-data

参数:
- prompt: 文本提示词
- duration: 总时长
- mode: 分析模式 (auto/keyword/ai)

返回:
{
  "success": true,
  "total_scenes": 5,
  "total_duration": 25.5,
  "scenes": [...]
}
```

### 2. 保存场景

```http
POST /api/scenes
Content-Type: application/json

参数:
- scenes: 场景列表
- task_id: 任务 ID（可选）

返回:
{
  "success": true,
  "task_id": "xxx-xxx-xxx",
  "message": "场景已保存"
}
```

### 3. 获取场景

```http
GET /api/scenes/<task_id>

返回:
{
  "success": true,
  "scenes": [...]
}
```

### 4. 场景确认页面

```
GET /scenes/confirm?task_id=<task_id>
```

---

## 🎯 使用场景

### 场景 1：AI 切分后手动调整

1. 输入提示词，选择协同模式
2. AI 自动分析并切分场景
3. 查看场景列表
4. 编辑不满意的场景（修改提示词或时长）
5. 确认后继续生成

### 场景 2：复用场景配置

1. 导出已有的成功场景为 JSON
2. 修改 JSON 文件（更换提示词等）
3. 导入修改后的配置
4. 使用新配置生成视频

### 场景 3：批量生成系列视频

1. 创建基础场景模板（JSON）
2. 批量修改部分字段（提示词、配音等）
3. 依次生成多个视频
4. 保持风格和结构一致

---

## 📊 三种使用方式对比

| 方式 | 适用场景 | 优点 | 示例 |
|------|---------|------|------|
| **Web 界面** | 可视化操作 | 直观、实时预览 | 点击卡片编辑 |
| **命令行交互** | 远程终端 | 快速、无需 GUI | `edit 2` |
| **API 调用** | 集成/批量 | 可编程、灵活 | `POST /api/scenes` |

---

## 🔧 场景数据结构

### 完整字段

```json
{
  "id": 1,
  "prompt": "场景提示词",
  "duration": 5.0,
  "scene_type": "character|background|action|default",
  "generation_location": "local|cloud",
  "reference_images": ["image1.png"],
  "voiceover": {
    "text": "配音文本",
    "voice": "语音名称",
    "emotion": "情绪",
    "speed": "语速"
  }
}
```

### JSON 配置文件格式

```json
{
  "version": "1.0",
  "created_at": "2026-05-02T10:30:00",
  "total_scenes": 3,
  "total_duration": 15.5,
  "scenes": [
    {
      "prompt": "...",
      "duration": 5.0,
      "scene_type": "character"
    }
  ]
}
```

---

## 💡 最佳实践

### 场景切分建议

| 场景类型 | 推荐时长 | 适用内容 |
|---------|---------|---------|
| 快速切换 | 3-5 秒 | 动作、转场 |
| 中等叙述 | 5-8 秒 | 对话、说明 |
| 详细展示 | 8-12 秒 | 全景、细节 |

### 编辑技巧

1. **先自动后手动**
   - 让 AI 先自动切分
   - 再手动微调不满意的地方

2. **保持连贯性**
   - 场景之间逻辑连贯
   - 时长变化自然

3. **合理分工**
   - 简单场景用 local（省资源）
   - 复杂场景用 cloud（质量好）

4. **使用模板**
   - 成功的场景配置保存为模板
   - 系列视频复用模板

---

## 📚 使用示例

### 示例 1：Web 界面编辑

```
1. 访问 http://localhost:5000
2. 输入提示词："勇敢的骑士与巨龙战斗"
3. 选择模式：collaborative
4. 点击"分析场景"
5. 查看场景列表（显示 5 个场景）
6. 点击第 3 个场景卡片
7. 修改提示词和时长
8. 点击"保存"
9. 确认所有场景后点击"确认并开始生成"
```

### 示例 2：命令行交互

```bash
# 启动交互式编辑
python -c "
from personal_mode.scene_viewer import interactive_edit_menu
scenes = [...]  # 场景列表
modified = interactive_edit_menu(scenes)
"

# 使用命令
请输入命令 > view          # 查看所有场景
请输入命令 > edit 3        # 编辑第 3 个场景
请输入命令 > add 2         # 在位置 2 添加场景
请输入命令 > delete 1      # 删除第 1 个场景
请输入命令 > export config.json  # 导出配置
请输入命令 > done          # 完成编辑
```

### 示例 3：JSON 配置

```python
import json

# 读取配置
with open('scenes_template.json', 'r') as f:
    config = json.load(f)

# 批量修改时长（增加 20%）
for scene in config['scenes']:
    scene['duration'] *= 1.2

# 添加新场景
config['scenes'].append({
    'prompt': '新的场景',
    'duration': 5.0,
    'scene_type': 'action'
})

# 保存配置
with open('scenes_modified.json', 'w') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
```

---

## 🎨 界面预览

### 场景列表视图

```
┌─────────────────────────────────────────────┐
│  🎬 场景确认与编辑                           │
│     查看 AI 智能生成的场景分镜，可以编辑修改   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 【场景 01】时长：5.0 秒                        │
│  提示词：一个勇敢的骑士站在古老城堡前...     │
│  类型：character  生成位置：local            │
│  参考图：1 张                               │
└─────────────────────────────────────────────┘

[+ 添加场景]     共 5 个场景，总时长 25.5 秒    [✓ 确认并开始生成]
```

### 编辑模式

```
┌─────────────────────────────────────────────┐
│ 【场景 01】时长：5.0 秒                        │
│ ─────────────────────────────────────────  │
│ 提示词:                                    │
│ ┌───────────────────────────────────────┐  │
│ │ 一个勇敢的骑士站在古老城堡前...        │  │
│ └───────────────────────────────────────┘  │
│                                            │
│ 时长（秒）: [5.0 ▼]                        │
│                                            │
│ [保存] [取消] [删除]                       │
└─────────────────────────────────────────────┘
```

---

## 🐛 已知问题

1. **Web 界面集成**：需要在主页面添加"分析场景"按钮
2. **命令行集成**：需要在 run.py 中添加 interaction 参数
3. **配置参数**：`--interactive-scenes` 参数待添加

---

## 🚀 后续改进

- [ ] 在主页面集成"分析场景"按钮
- [ ] 在 run.py 中添加 `--interactive-scenes` 参数
- [ ] 增加场景预览缩略图功能
- [ ] 支持场景拖拽排序
- [ ] 支持批量操作（批量修改时长、位置等）
- [ ] 增加场景模板库
- [ ] 支持场景版本对比

---

## 📖 相关文档

- [场景查看器代码](personal_mode/scene_viewer.py)
- [场景确认页面](web/templates/scenes_confirm.html)
- [场景确认功能完整指南](SCENE_CONFIRMATION_FEATURE.md)
- [Web 界面使用指南](web/README.md)

---

*更新时间：2026-05-02*  
*版本：v2.1.0*
