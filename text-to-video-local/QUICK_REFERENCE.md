# 快速参考卡片 🎬

## 🚀 三种调用方式

### 1️⃣ 命令行（本地开发）

```bash
# 基础用法
python personal_mode/run.py -p "提示词" -m optimized

# 使用参考图片
python personal_mode/run.py -p "提示词" \
  --ref-images ./character.png \
  --ref-type character \
  --ref-strength 0.7

# 启用配音
python personal_mode/run.py -p "提示词" \
  --voiceover \
  --character-voice zh-CN-XiaoxiaoNeural
```

### 2️⃣ Web 界面（浏览器）

```bash
# 启动服务
./start_web.sh

# 访问地址
http://localhost:5000
```

### 3️⃣ API（编程调用）

```python
import requests

# 提交任务
response = requests.post('http://localhost:5000/api/generate',
    data={'prompt': '提示词', 'mode': 'optimized'},
    files={'ref_images': open('character.png', 'rb')}
)
task_id = response.json()['task_id']

# 查询状态
status = requests.get(f'http://localhost:5000/api/task/{task_id}').json()

# 下载视频
video = requests.get(f"http://localhost:5000{status['video_url']}")
```

---

## 📊 参数速查

### 生成模式

| 模式 | 显存需求 | 时间 | 适用场景 |
|------|---------|------|---------|
| `standard` | 12GB+ | 5-10 分钟 | 高端 GPU |
| `optimized` ⭐ | 4GB+ | 3-5 分钟 | 所有配置 |
| `collaborative` | 0-8GB | 2-4 分钟 | 弹性需求 |

### 参考图片

| 参数 | 值 | 说明 |
|------|-----|------|
| `--ref-type` | `character` | 人物卡（角色一致性） |
| | `background` | 背景图（场景一致性） |
| | `mixed` | 混合 |
| `--ref-strength` | 0.0-1.0 | 参考强度（默认 0.6） |

### 配音选项

| 语音 | 音色 | 适合场景 |
|------|------|---------|
| `zh-CN-XiaoxiaoNeural` | 女声 | 通用 |
| `zh-CN-YunxiNeural` | 男声 | 解说 |
| `zh-CN-YunyangNeural` | 男声 | 新闻 |
| `zh-CN-XiaomengNeural` | 女声 | 故事 |

---

## 🔧 常用命令

```bash
# 启动 Web 服务
./start_web.sh

# 超优模式 + 参考图 + 配音
python personal_mode/run.py \
  -p "勇敢的骑士" \
  -m optimized \
  -d 10 \
  --ref-images ./character.png \
  --voiceover

# Web 模式测试
curl http://localhost:5000

# 查看 Git 提交
git log --oneline -10
```

---

## 📁 目录结构

```
text-to-video-local/
├── personal_mode/          # 个人电脑模式
│   ├── run.py             # 统一启动器
│   ├── reference_manager.py  # 参考图管理器
│   └── ...
├── hybrid_mode/           # 混合模式
│   └── generate.py
├── web/                   # Web 界面
│   ├── app.py
│   ├── templates/
│   └── README.md
├── start_web.sh          # 启动脚本
└── QUICK_REFERENCE.md    # 本文档
```

---

## ⚡ 快速故障排除

### Web 服务无法启动
```bash
# 检查端口占用
lsof -i:5000

# 更换端口
# 编辑 web/app.py，修改 port=8080
```

### 参考图片不生效
- 检查图片格式（PNG/JPG/WebP）
- 调整参考强度（建议 0.5-0.8）
- 确认参考图类型正确

### 配音生成失败
- 安装 edge-tts: `pip install edge-tts`
- 检查网络连接
- 确认语音名称正确

---

## 📚 完整文档

- [Web 界面使用指南](web/README.md)
- [完整功能总结](WEB_INTERFACE_SUMMARY.md)
- [个人电脑模式指南](personal_mode/README.md)
- [混合模式指南](hybrid_mode/README.md)

---

*快速参考卡片 - v1.0*
