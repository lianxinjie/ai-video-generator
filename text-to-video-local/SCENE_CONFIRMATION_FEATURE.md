# 场景查看与编辑功能

## 🎯 功能概述

在智能切分场景后，用户可以查看切分结果并进行修改，包括：
- 查看所有场景的详细信息
- 修改场景提示词
- 调整场景时长
- 添加/删除场景
- 导出/导入场景配置

---

## 🖥️ 使用方式

### 方式 1：Web 界面（推荐）

#### 步骤：

1. **访问主页面**
   ```
   http://localhost:5000
   ```

2. **输入提示词并选择模式**
   - 提示词：描述视频内容
   - 模式：选择 `collaborative`（协同模式）或 `optimized`（超优模式）
   - 启用场景分析：勾选相关选项

3. **点击"分析场景"按钮**（新增）
   - 系统会自动分析提示词并切分场景
   - 显示场景列表和详细信息

4. **查看和编辑场景**
   - 点击任意场景卡片进入编辑模式
   - 修改提示词、时长等参数
   - 可以添加或删除场景

5. **保存并继续**
   - 确认场景无误后点击"保存并开始生成"
   - 系统会使用确认后的场景生成视频

#### 场景确认页面功能：

- **场景卡片**：显示场景编号、提示词、时长、类型
- **编辑模式**：点击卡片进入编辑
  - 修改提示词
  - 调整时长（秒）
  - 保存/取消修改
- **添加场景**：在列表末尾添加新场景
- **删除场景**：删除不需要的场景
- **导出 JSON**：将场景配置保存到文件
- **导入 JSON**：从文件加载场景配置

---

### 方式 2：命令行交互模式

```bash
# 启用交互式场景确认
python personal_mode/run.py \
  -p "勇敢的骑士在古老城堡中与巨龙战斗" \
  -m collaborative \
  -d 10 \
  --enable-scene-detection \
  --enable-scene-refine \
  --interactive-scenes
```

**交互式菜单**：

```
======================================================================
  场景编辑器 - 交互式菜单
======================================================================

可用命令:
  view         - 查看所有场景
  edit <编号>  - 编辑指定场景
  add <位置>   - 添加新场景
  delete <编号>- 删除场景
  export <文件> - 导出到 JSON
  import <文件> - 从 JSON 导入
  done         - 完成编辑
  quit         - 退出（不保存）
======================================================================

请输入命令 >
```

**使用示例**：

```bash
# 查看所有场景
请输入命令 > view

# 编辑第 2 个场景
请输入命令 > edit 2
  提示词 [城堡内部...]: 修改后的提示词
  时长 [5.0]: 6.5

# 添加新场景
请输入命令 > add 3
  提示词：巨龙喷火
  时长（秒）: 4.0

# 删除场景
请输入命令 > delete 1
  确认删除场景 1? (y/n): y

# 完成编辑
请输入命令 > done
  保存修改？(y/n): y
```

---

### 方式 3：配置文件编辑

#### 步骤 1：导出场景配置

**命令行**：
```bash
# 使用 Python 脚本导出
python -c "
from personal_mode.scene_viewer import SceneViewer
viewer = SceneViewer()
# 假设已有 scenes 列表
viewer.load_scenes(scenes)
viewer.export_to_json('scenes_config.json')
"
```

**API**：
```bash
curl http://localhost:5000/api/scenes/<task_id> -o scenes_config.json
```

#### 步骤 2：编辑 JSON 文件

```json
{
  "version": "1.0",
  "created_at": "2026-05-02T10:30:00",
  "total_scenes": 3,
  "total_duration": 15.5,
  "scenes": [
    {
      "id": 1,
      "prompt": "勇敢的骑士站在古老城堡前",
      "duration": 5.0,
      "scene_type": "character",
      "generation_location": "local"
    },
    {
      "id": 2,
      "prompt": "城堡内部的王座大厅",
      "duration": 4.5,
      "scene_type": "background",
      "generation_location": "cloud"
    },
    {
      "id": 3,
      "prompt": "激烈的战斗场面",
      "duration": 6.0,
      "scene_type": "action",
      "generation_location": "local",
      "voiceover": {
        "text": "骑士挥舞宝剑",
        "voice": "zh-CN-XiaoxiaoNeural",
        "emotion": "excited"
      }
    }
  ]
}
```

#### 步骤 3：导入修改后的配置

**命令行**：
```bash
python personal_mode/run.py \
  -p "提示词" \
  -m collaborative \
  --scenes-file scenes_config.json
```

**API**：
```bash
curl -X POST http://localhost:5000/api/scenes \
  -H "Content-Type: application/json" \
  -d @scenes_config.json
```

---

## 📊 API 接口

### 1. 分析场景

```http
POST /api/analyze
Content-Type: multipart/form-data
```

**参数**：
- `prompt` (string): 文本提示词
- `duration` (float): 总时长
- `mode` (string): 分析模式 (`auto`/`keyword`/`ai`)

**响应**：
```json
{
  "success": true,
  "total_scenes": 5,
  "total_duration": 25.5,
  "scenes": [
    {
      "prompt": "...",
      "duration": 5.0,
      "scene_type": "character",
      ...
    }
  ]
}
```

### 2. 保存场景

```http
POST /api/scenes
Content-Type: application/json
```

**参数**：
- `scenes` (array): 场景列表
- `task_id` (string): 任务 ID（可选）

**响应**：
```json
{
  "success": true,
  "task_id": "xxx-xxx-xxx",
  "message": "场景已保存"
}
```

### 3. 获取场景

```http
GET /api/scenes/<task_id>
```

**响应**：
```json
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

## 🔧 Python 代码示例

### 使用 SceneViewer

```python
from personal_mode.scene_viewer import SceneViewer, SceneEditor

# 创建查看器
viewer = SceneViewer(verbose=True)

# 加载场景
scenes = [...]  # 场景列表
viewer.load_scenes(scenes)

# 显示场景
viewer.display_scenes(show_details=True)

# 导出到 JSON
viewer.export_to_json('my_scenes.json')

# 从 JSON 导入
viewer.import_from_json('my_scenes.json')
```

### 使用 SceneEditor

```python
# 创建编辑器
editor = SceneEditor(scenes, verbose=True)

# 编辑场景
editor.edit_scene(
    scene_index=2,
    prompt="新的提示词",
    duration=6.5
)

# 添加场景
editor.add_scene(
    position=3,
    scene_data={
        'prompt': '新场景',
        'duration': 5.0,
        'scene_type': 'action'
    }
)

# 删除场景
editor.delete_scene(scene_index=1)

# 获取修改后的场景
modified_scenes = editor.get_scenes()
```

### 交互式编辑

```python
from personal_mode.scene_viewer import interactive_edit_menu

# 打开交互式编辑菜单
modified_scenes = interactive_edit_menu(scenes)
```

---

## ⚙️ 配置选项

### 场景字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `prompt` | string | 场景提示词 | ✅ |
| `duration` | float | 场景时长（秒） | ✅ |
| `scene_type` | string | 场景类型 | ❌ |
| `generation_location` | string | 生成位置（local/cloud） | ❌ |
| `reference_images` | array | 参考图片列表 | ❌ |
| `voiceover` | object | 配音配置 | ❌ |

### 配音配置字段

```json
{
  "voiceover": {
    "text": "配音文本",
    "voice": "语音名称",
    "emotion": "情绪",
    "speed": "语速"
  }
}
```

---

## 💡 最佳实践

### 1. 场景切分建议

- **短场景**：3-5 秒，适合快速切换
- **中等场景**：5-8 秒，适合叙述性内容
- **长场景**：8-12 秒，适合展示细节

### 2. 编辑技巧

- **先自动分析**：让 AI 先切分，再手动调整
- **保持连贯**：场景之间逻辑要连贯
- **合理分工**：简单场景用 local，复杂场景用 cloud

### 3. 批量修改

使用 JSON 配置文件批量修改多个场景：

```python
# 读取配置
with open('scenes.json', 'r') as f:
    data = json.load(f)

# 批量调整时长
for scene in data['scenes']:
    scene['duration'] *= 1.2  # 增加 20%

# 保存
with open('scenes_modified.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 🐛 常见问题

### Q1: 场景切分不合理怎么办？
**A**: 使用编辑功能手动调整：
- Web 界面：点击场景卡片编辑
- 命令行：使用 `edit` 命令
- 或直接修改 JSON 文件

### Q2: 如何保存编辑后的场景？
**A**: 
- Web 界面：点击"确认并开始生成"自动保存
- 命令行：使用 `export` 命令导出
- 或直接修改 JSON 文件

### Q3: 可以复用之前的场景配置吗？
**A**: 可以，使用 `import` 命令或 `/api/scenes` 接口导入 JSON 配置

---

## 📚 相关文档

- [场景查看器代码](personal_mode/scene_viewer.py)
- [Web 界面使用](web/README.md)
- [协同模式指南](personal_mode/COLLABORATIVE_MODE_GUIDE.md)

---

*更新时间：2026-05-02*
