# 项目路径使用说明

## 📂 目录结构

```
workspace/                    # 工作空间根目录
└── text-to-video-local/     # 项目主目录（所有操作在此目录内）
    ├── web/                 # Web 应用
    │   ├── app.py          # Flask 后端
    │   └── templates/      # HTML 模板
    ├── models/             # AI 模型目录（按需下载）
    ├── ffmpeg/             # FFmpeg 目录（按需下载）
    ├── download_models.py  # 模型下载脚本
    ├── download_ffmpeg.py  # FFmpeg 下载脚本
    └── *.md               # 文档文件
```

## ✅ 路径配置说明

### 1. 工作目录

**当前工作目录**: `text-to-video-local/`

所有相对路径都基于此目录：

```bash
# 正确的命令
cd text-to-video-local
python web/app.py
python download_models.py
python download_ffmpeg.py
```

### 2. 相对路径使用

代码中使用的相对路径：

```python
# 模型目录
models_dir = Path('./models')

# FFmpeg 目录
ffmpeg_dir = Path('./ffmpeg/bin')

# Web 模板
templates_dir = Path('./web/templates')
```

### 3. 路径基准点

| 路径 | 实际位置 | 说明 |
|------|---------|------|
| `./models` | `text-to-video-local/models/` | AI 模型 |
| `./ffmpeg` | `text-to-video-local/ffmpeg/` | FFmpeg 工具 |
| `./web` | `text-to-video-local/web/` | Web 应用 |
| `./web/templates` | `text-to-video-local/web/templates/` | HTML 模板 |

## 🚀 快速开始

### 方式 1: 在项目目录内

```bash
cd text-to-video-local
python web/app.py
```

### 方式 2: 从 workspace 根目录

```bash
cd /workspace/text-to-video-local
python web/app.py
```

### 方式 3: 使用绝对路径

```bash
python /workspace/text-to-video-local/web/app.py
```

## ⚠️ 常见错误

### 错误 1: 路径错误

```bash
# ❌ 错误 - 在 workspace 根目录执行
cd /workspace
python web/app.py  # FileNotFoundError

# ✅ 正确 - 进入项目目录
cd /workspace/text-to-video-local
python web/app.py
```

### 错误 2: 模型路径错误

```bash
# ❌ 错误 - 路径不存在
cd /workspace
mkdir models  # 创建在错误的位置

# ✅ 正确 - 在项目目录内
cd /workspace/text-to-video-local
mkdir models  # 创建在正确位置
```

## 📋 所有文件位置

### 核心文件（不可移动）

| 文件 | 路径 | 说明 |
|------|------|------|
| web/app.py | text-to-video-local/web/app.py | Flask 后端 |
| web/templates/index.html | text-to-video-local/web/templates/index.html | 主页面 |
| web/templates/setup_wizard.html | text-to-video-local/web/templates/setup_wizard.html | 设置向导 |
| download_models.py | text-to-video-local/download_models.py | 模型下载 |
| download_ffmpeg.py | text-to-video-local/download_ffmpeg.py | FFmpeg 下载 |

### 数据目录（按需创建）

| 目录 | 路径 | 创建时机 |
|------|------|---------|
| models/ | text-to-video-local/models/ | 下载模型时 |
| ffmpeg/ | text-to-video-local/ffmpeg/ | 下载 FFmpeg 时 |

### 文档文件（只读）

| 文件 | 路径 |
|------|------|
| README.md | text-to-video-local/README.md |
| FFMPEG_INSTALL_GUIDE.md | text-to-video-local/FFMPEG_INSTALL_GUIDE.md |
| MODEL_MANAGEMENT_FEATURE.md | text-to-video-local/MODEL_MANAGEMENT_FEATURE.md |
| MODEL_SIZE_EXPLANATION.md | text-to-video-local/MODEL_SIZE_EXPLANATION.md |
| FFMPEG_STRICT_VERIFICATION.md | text-to-video-local/FFMPEG_STRICT_VERIFICATION.md |

## 🔧 配置文件

### .gitignore

位于 `text-to-video-local/.gitignore`

```
# Python
__pycache__/
*.py[cod]

# 模型文件（体积大）
models/

# FFmpeg（按需下载）
ffmpeg/

# 其他
*.log
.env
```

## 💡 最佳实践

1. **始终在项目目录内操作**
   ```bash
   cd text-to-video-local
   # 然后执行所有命令
   ```

2. **使用相对路径**
   ```python
   # ✅ 好的做法
   Path('./models')
   
   # ❌ 避免硬编码
   Path('/workspace/text-to-video-local/models')
   ```

3. **检查当前目录**
   ```bash
   pwd  # 应该显示：.../text-to-video-local
   ```

---

**所有文件都位于 `text-to-video-local/` 目录内，无需在外部创建任何文件！**
