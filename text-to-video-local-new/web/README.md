# Web 界面和 API 使用指南

## 🌐 快速启动

### 方式 1：启动脚本（推荐）

```bash
./start_web.sh
```

启动脚本会自动安装所需依赖。

### 方式 2：手动启动

```bash
# 安装依赖
pip install flask pillow

# 启动服务
python3 web/app.py
```

### 访问地址

启动后访问：**http://localhost:5000**

---

## 🎯 两种调用方式

### 1. Web 界面（浏览器）

打开浏览器访问 http://localhost:5000，通过图形界面操作：

**操作步骤：**

1. **输入提示词**：描述你想要生成的视频内容
2. **选择生成模式**：
   - ⚡ 超优模式（推荐）- 4GB 显存即可，3-5 分钟
   - 🚀 标准模式 - 需要 12GB+ 显存，5-10 分钟
   - 🤖 协同模式 - 本地 + 云端协同，2-4 分钟
   - 🔀 混合模式 - 0 显存，云端图片 + 本地合成，3-6 小时
3. **设置视频时长**：1-60 秒
4. **上传参考图片**（可选）：
   - 人物卡：保持角色一致性
   - 背景图：保持场景一致性
   - 混合：角色 + 背景
   - 参考强度：0.0-1.0（值越大越像参考图）
   - **注意**：混合模式不支持参考图片功能
5. **启用 AI 配音**（可选）：
   - 选择配音语音（4 种音色）
   - 上传背景音乐（可选）
   - **注意**：混合模式支持配音功能
6. **点击"开始生成视频"**
7. **等待完成**：显示进度条和实时状态
8. **下载视频**：生成完成后在线播放和下载

**界面特点：**
- 📊 实时进度显示
- 🎬 在线视频播放
- ⬇️ 一键下载
- 📱 响应式设计

---

### 2. API 接口（编程调用）

#### API 端点

**生成视频**
```http
POST /api/generate
Content-Type: multipart/form-data
```

**参数说明：**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| prompt | string | ✅ | 文本提示词 |
| mode | string | ❌ | 生成模式：`standard`/`optimized`/`collaborative`，默认 `optimized` |
| duration | float | ❌ | 视频时长（秒），默认 10 |
| ref_images | file[] | ❌ | 参考图片文件（支持多张） |
| ref_type | string | ❌ | 参考图类型：`character`/`background`/`mixed`，默认 `character` |
| ref_strength | float | ❌ | 参考图强度 0.0-1.0，默认 0.6 |
| voiceover | boolean | ❌ | 是否启用配音，默认 `false` |
| character_voice | string | ❌ | 配音语音，默认 `zh-CN-XiaoxiaoNeural` |
| bgm_file | file | ❌ | 背景音乐文件 |

**查询任务状态**
```http
GET /api/task/<task_id>
```

**获取输出文件**
```http
GET /api/output/<task_id>/<filename>
```

---

#### 使用示例

##### Python 示例

```python
import requests

# 1. 提交生成任务
files = {
    'ref_images': open('character_sheet.png', 'rb'),
    'bgm_file': open('bgm.mp3', 'rb')
}

data = {
    'prompt': '一个勇敢的骑士在古老城堡中与巨龙战斗',
    'mode': 'optimized',
    'duration': 10,
    'ref_type': 'character',
    'ref_strength': 0.6,
    'voiceover': 'true',
    'character_voice': 'zh-CN-XiaoxiaoNeural'
}

response = requests.post('http://localhost:5000/api/generate', 
                        files=files, data=data)

task_data = response.json()
task_id = task_data['task_id']

print(f"任务已提交：{task_id}")

# 2. 轮询任务状态
import time

while True:
    status_response = requests.get(f'http://localhost:5000/api/task/{task_id}')
    status = status_response.json()
    
    print(f"状态：{status['status']}, 进度：{status['progress']}%")
    
    if status['status'] == 'completed':
        video_url = status['video_url']
        print(f"生成完成！下载链接：{video_url}")
        
        # 下载视频
        video_response = requests.get(f'http://localhost:5000{video_url}')
        with open('output.mp4', 'wb') as f:
            f.write(video_response.content)
        
        break
    elif status['status'] == 'failed':
        print(f"生成失败：{status.get('error')}")
        break
    
    time.sleep(2)
```

##### cURL 示例

```bash
# 提交任务
curl -X POST http://localhost:5000/api/generate \
  -F "prompt=一个勇敢的骑士在古老城堡中与巨龙战斗" \
  -F "mode=optimized" \
  -F "duration=10" \
  -F "ref_images=@character_sheet.png" \
  -F "ref_type=character" \
  -F "ref_strength=0.6" \
  -F "voiceover=true" \
  -F "character_voice=zh-CN-XiaoxiaoNeural"

# 查询状态
curl http://localhost:5000/api/task/<task_id>

# 下载视频
curl http://localhost:5000/api/output/<task_id>/output.mp4 -o output.mp4
```

##### JavaScript (Fetch) 示例

```javascript
// 提交生成任务
const formData = new FormData();
formData.append('prompt', '一个勇敢的骑士在古老城堡中与巨龙战斗');
formData.append('mode', 'optimized');
formData.append('duration', '10');
formData.append('ref_images', fileInput.files[0]);
formData.append('ref_type', 'character');
formData.append('ref_strength', '0.6');
formData.append('voiceover', 'true');

const response = await fetch('/api/generate', {
    method: 'POST',
    body: formData
});

const data = await response.json();
const taskId = data.task_id;

// 轮询状态
async function pollStatus(taskId) {
    const interval = setInterval(async () => {
        const statusResponse = await fetch(`/api/task/${taskId}`);
        const status = await statusResponse.json();
        
        console.log(`状态：${status.status}, 进度：${status.progress}%`);
        
        if (status.status === 'completed') {
            clearInterval(interval);
            console.log(`生成完成！视频 URL: ${status.video_url}`);
            
            // 下载视频
            const videoBlob = await fetch(status.video_url).then(r => r.blob());
            // 处理视频...
        }
    }, 2000);
}

pollStatus(taskId);
```

---

## 📊 任务状态说明

| 状态 | 说明 |
|------|------|
| `running` | 任务正在运行中 |
| `completed` | 任务已完成，视频已生成 |
| `failed` | 任务失败，查看 error 字段 |

**进度说明：**
- 0-20%：准备阶段（加载模型、创建目录）
- 20-60%：生成图片（分段生成）
- 60-80%：合成视频
- 80-100%：添加配音和后期处理

---

## 🔧 高级配置

### 修改端口

编辑 `web/app.py`，修改：

```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

改为：

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### 生产环境部署

使用 Gunicorn 部署：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

### 文件存储位置

- **上传文件**：`web/uploads/<task_id>/`
- **输出文件**：`web/outputs/<task_id>/`

可以修改 `app.config` 中的路径配置。

---

## 🎨 参考图片功能

### 人物卡（character）

上传角色设计图，保持视频中角色的一致性。

**建议：**
- 清晰的角色正面/侧面/背面图
- 白底或透明背景
- 高分辨率（512x512 以上）

### 背景图（background）

上传场景背景图，保持环境一致性。

**建议：**
- 完整的场景图
- 符合视频氛围
- 无明显角色

### 混合（mixed）

同时使用人物卡和背景图。

---

## 🎵 三层配音架构

启用配音后，系统自动生成：

1. **人物配音**：基于情绪分析的智能配音
   - 6 种情绪识别
   - 10+ 语音选择
   - 0.5 秒分段

2. **音效**：场景音效（待实现）
   - 动作音效
   - 环境音效

3. **背景音乐**：循环播放的 BGM
   - 支持上传自定义 BGM
   - 自动音量调节（不盖过配音）

---

## ⚠️ 注意事项

1. **性能考虑**：
   - 每个任务独立运行，建议限制并发数量
   - 大文件上传限制 50MB（可配置）

2. **安全考虑**：
   - 生产环境请使用 WSGI 服务器（如 Gunicorn）
   - 添加用户认证和权限控制
   - 限制 API 调用频率

3. **存储管理**：
   - 定期清理 `web/uploads` 和 `web/outputs` 目录
   - 建议设置自动清理策略（如 24 小时后删除）

---

## 📚 更多文档

- [个人电脑模式使用指南](../personal_mode/README.md)
- [混合模式使用指南](../hybrid_mode/README.md)
- [三层配音架构说明](../VOICEOVER_TEST_REPORT.md)

---

*最后更新：2026-05-02*
