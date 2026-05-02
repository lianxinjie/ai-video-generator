# Web 界面和参考图片功能 - 完整总结

## 📋 更新概览

本次更新为 AI 视频生成器添加了两种新的调用方式，并增强了个人电脑模式和混合模式的功能。

---

## ✨ 新增功能

### 1. Web 界面（浏览器访问）

**访问地址**：http://localhost:5000

**功能特点**：
- 📊 响应式图形界面
- 🎬 实时进度显示
- 📁 拖拽上传参考图片
- 🎵 配音选项配置
- ⬇️ 在线播放和下载

**支持功能**：
- 文本到视频生成
- 三种生成模式选择
- 参考图片上传（人物卡/背景图）
- AI 智能配音（三层架构）
- 背景音乐上传

---

### 2. REST API（编程调用）

**API 端点**：

```http
POST /api/generate           # 生成视频
GET  /api/task/<id>          # 查询任务状态
GET  /api/output/<id>/<file> # 获取输出文件
```

**支持语言**：
- ✅ Python (requests)
- ✅ JavaScript (Fetch)
- ✅ cURL
- ✅ 任何 HTTP 客户端

---

### 3. 参考图片功能

**支持类型**：
| 类型 | 说明 | 适用场景 |
|------|------|---------|
| `character` | 人物卡 | 保持角色一致性 |
| `background` | 背景图 | 保持场景一致性 |
| `mixed` | 混合 | 角色 + 背景 |

**参考强度**：0.0-1.0
- 0.0：完全忽略参考图
- 0.6：平衡（默认）
- 1.0：最大程度模仿参考图

**使用方式**：
- 命令行：`--ref-images <path>`
- Web 界面：上传文件
- API：`ref_images` 参数

---

## 🎯 三种调用方式对比

| 方式 | 适用场景 | 优点 | 示例 |
|------|---------|------|------|
| **命令行** | 本地开发、脚本调用 | 快速、直接 | `python personal_mode/run.py -p "提示词"` |
| **Web 界面** | 非技术人员、可视化操作 | 直观、易上手 | http://localhost:5000 |
| **API** | 集成到其他系统、自动化 | 可编程、灵活 | `POST /api/generate` |

---

## 📦 安装和启动

### 快速启动（推荐）

```bash
./start_web.sh
```

自动安装 Flask 和 Pillow 依赖。

### 手动启动

```bash
pip install flask pillow
python3 web/app.py
```

### 命令行使用（新增参考图功能）

```bash
# 使用人物卡参考图
python personal_mode/run.py \
  -p "勇敢的骑士" \
  -m optimized \
  --ref-images ./character_sheet.png \
  --ref-type character \
  --ref-strength 0.7

# 使用多张背景图
python personal_mode/run.py \
  -p "魔法森林" \
  -m collaborative \
  --ref-images ./backgrounds/ \
  --ref-type background \
  --ref-strength 0.5

# 配合配音功能
python personal_mode/run.py \
  -p "童话故事" \
  -m optimized \
  --ref-images ./character.png \
  --voiceover \
  --bgm-file ./bgm.mp3
```

---

## 🔧 技术架构

### Web 应用

```
web/
├── app.py              # Flask 主应用
├── templates/
│   └── index.html      # Web 界面
├── static/             # 静态资源
├── uploads/            # 上传文件目录
└── outputs/            # 输出文件目录
```

### 参考图片管理

```python
personal_mode/
├── reference_manager.py  # 参考图管理器
└── run.py                # 集成参考图支持
```

### 任务处理流程

```
用户提交 → 创建任务 → 后台运行 → 轮询状态 → 完成下载
   ↓          ↓          ↓          ↓          ↓
 /api/generate  UUID   线程运行  /api/task  /api/output
```

---

## 📊 使用示例

### Python API 调用

```python
import requests

# 提交任务
data = {
    'prompt': '勇敢的骑士与巨龙战斗',
    'mode': 'optimized',
    'duration': 10,
    'ref_type': 'character',
    'ref_strength': 0.6,
    'voiceover': 'true'
}

files = {
    'ref_images': open('character.png', 'rb')
}

response = requests.post('http://localhost:5000/api/generate', 
                        files=files, data=data)
task_id = response.json()['task_id']

# 轮询状态
while True:
    status = requests.get(f'http://localhost:5000/api/task/{task_id}').json()
    
    if status['status'] == 'completed':
        # 下载视频
        video = requests.get(f"http://localhost:5000{status['video_url']}")
        with open('output.mp4', 'wb') as f:
            f.write(video.content)
        break
    
    time.sleep(2)
```

### Web 界面操作流

1. 打开 http://localhost:5000
2. 输入提示词："一个勇敢的骑士在古老城堡中与巨龙战斗"
3. 选择模式：超优模式
4. 设置时长：10 秒
5. 上传参考图：character_sheet.png
6. 启用配音：✓
7. 选择语音：晓晓（女声）
8. 点击"开始生成视频"
9. 等待进度条完成
10. 在线播放和下载

---

## ⚙️ 配置文件说明

### 修改端口

编辑 `web/app.py`:

```python
app.run(host='0.0.0.0', port=8080)  # 改为 8080 端口
```

### 文件大小限制

编辑 `web/app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### 存储位置

编辑 `web/app.py`:

```python
app.config['UPLOAD_FOLDER'] = Path('/data/uploads')
app.config['OUTPUT_FOLDER'] = Path('/data/outputs')
```

---

## 🔐 安全建议

### 生产环境部署

1. **使用 WSGI 服务器**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
   ```

2. **添加认证**
   ```python
   from flask_httpauth import HTTPTokenAuth
   auth = HTTPTokenAuth()
   ```

3. **限制请求频率**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.remote_addr)
   ```

4. **定期清理文件**
   ```bash
   # crontab 配置
   0 * * * * find web/outputs -mmin +60 -delete
   ```

---

## 🎨 最佳实践

### 参考图片准备

**人物卡**：
- ✅ 正面、侧面、背面三视图
- ✅ 白底或透明背景
- ✅ 512x512 以上分辨率
- ❌ 避免复杂背景
- ❌ 避免多个人物

**背景图**：
- ✅ 完整场景图
- ✅ 符合视频氛围
- ✅ 无明显角色
- ❌ 避免人物出现
- ❌ 避免文字

### 参数调优

| 场景 | 参考强度 | 模式的选择 | 配音建议 |
|------|---------|-----------|---------|
| 角色一致性要求高 | 0.7-0.8 | optimized | 启用 |
| 快速测试 | 0.0 | standard | 禁用 |
| 复杂场景 | 0.5-0.6 | collaborative | 启用 + BGM |

---

## 📚 相关文档

- [个人电脑模式完整指南](personal_mode/COMPLETE_GUIDE.md)
- [混合模式使用指南](hybrid_mode/README.md)
- [三层配音测试报告](VOICEOVER_TEST_REPORT.md)
- [参考图片管理器代码](personal_mode/reference_manager.py)

---

## 🐛 已知问题

1. **Pillow 依赖**：需要手动安装 `pip install pillow`
2. **大文件上传**：默认限制 50MB，需手动调整
3. **并发限制**：建议限制同时运行的任务数量

---

## 🚀 未来计划

- [ ] WebSocket 实时进度推送
- [ ] 批量任务支持
- [ ] 视频预览缩略图
- [ ] 音效生成集成
- [ ] 用户账户系统
- [ ] 历史记录管理

---

*更新时间：2026-05-02*  
*版本：v2.0.0*
