# FFmpeg 安装指南

## 问题说明

运行程序时出现警告：
```
RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
```

这是因为系统未安装 FFmpeg，pydub 无法正常处理音频。

---

## 🚀 快速解决方案

### 方案 1: 使用 Web 界面自动下载（推荐）

1. 启动 Web 服务
   ```bash
   python quick_start.py
   ```

2. 访问 Web 界面
   ```
   http://localhost:5000
   ```

3. 点击导航栏的 **🎬 FFmpeg** 按钮

4. 点击 **⬇️ 自动下载 FFmpeg**

5. 等待下载完成，重启服务

---

### 方案 2: Windows 手动安装

#### 方法 A: 使用包管理器（推荐）

如果使用 **Chocolatey**:
```powershell
choco install ffmpeg
```

如果使用 **winget** (Windows 10+):
```powershell
winget install Gyan.FFmpeg
```

如果使用 **Scoop**:
```powershell
scoop install ffmpeg
```

#### 方法 B: 手动下载安装

1. **下载 FFmpeg**
   
   访问：https://www.gyan.dev/ffmpeg/builds/
   
   下载：`ffmpeg-release-essentials.zip`

2. **解压到本地**
   ```
   C:\ffmpeg\
   ```

3. **添加环境变量**
   
   - 右键"此电脑" → "属性" → "高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到 `Path`
   - 点击"编辑" → "新建"
   - 添加：`C:\ffmpeg\bin`
   - 确定保存

4. **验证安装**
   ```cmd
   ffmpeg -version
   ```

---

### 方案 3: Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

---

### 方案 4: macOS

使用 **Homebrew**:
```bash
brew install ffmpeg
ffmpeg -version
```

使用 **MacPorts**:
```bash
sudo port install ffmpeg
```

---

## 📦 项目内自动下载脚本

如果 Web 界面不可用，可以运行下载脚本：

```bash
# Windows
python download_ffmpeg.py

# Linux/Mac
python3 download_ffmpeg.py
```

脚本会自动：
1. 检测系统架构
2. 下载对应版本的 FFmpeg
3. 解压到 `./ffmpeg/` 目录
4. 配置环境变量（某些系统）

---

## ✅ 验证安装

安装完成后，验证：

### 1. 命令行验证
```bash
ffmpeg -version
```

应该显示类似：
```
ffmpeg version 6.0-full_build-www.gyan.dev
built with gcc 12.2.0 (Rev10, Built by MSYS2 project)
```

### 2. Python 验证
```python
import subprocess
result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
print(result.stdout[:200])
```

### 3. pydub 验证
```python
from pydub import AudioSegment
from pydub.utils import which

# 检查 ffmpeg 是否可用
if which("ffmpeg"):
    print("✓ FFmpeg 已安装")
else:
    print("❌ FFmpeg 未安装")
```

---

## 🛠️ 常见问题

### Q1: 提示 "command not found" 或 "不是内部或外部命令"

**原因：** FFmpeg 未添加到系统 PATH

**解决方案：**

**Windows:**
```powershell
# 临时添加（当前窗口有效）
$env:Path += ";C:\ffmpeg\bin"

# 永久添加：按照上面的方法添加到环境变量
```

**Linux/Mac:**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export PATH="$PATH:/path/to/ffmpeg/bin"' >> ~/.bashrc
source ~/.bashrc
```

### Q2: 下载速度慢

**原因：** GitHub 或官方源在国内访问慢

**解决方案：** 使用镜像源

```bash
# 使用清华镜像 (如果下载脚本支持)
python download_ffmpeg.py --mirror tsinghua

# 手动下载镜像
下载：https://mirrors.tuna.tsinghua.edu.cn/github-release/gyanD/FFmpeg/
```

### Q3: 安装后仍然报错

**可能原因：**
1. 需要重启终端或 IDE
2. 需要重启 Web 服务
3. PATH 未生效

**解决方案：**
```bash
# 关闭并重新打开终端
# 重启 Web 服务
python quick_start.py
```

### Q4: Windows 权限问题

**错误：** "拒绝访问" 或 "无法创建文件"

**解决方案：**
1. 以管理员身份运行命令行
2. 安装到用户目录（不需要管理员）
   ```powershell
   winget install --user Gyan.FFmpeg
   ```

---

## 📊 FFmpeg 用途

本项目使用 FFmpeg 进行：

1. **视频合并** - 将图片序列合并为视频
2. **音频处理** - 配音、背景音乐混合
3. **格式转换** - MP4/WebM 等格式转换
4. **视频编码** - H.264/H.265 编码
5. **滤镜效果** - 转场、缩放等

**没有 FFmpeg，视频生成将无法工作！**

---

## 🎯 推荐安装方式

| 操作系统 | 推荐方式 | 难度 |
|----------|----------|------|
| Windows  | winget 或 Web 界面自动下载 | ⭐ |
| Ubuntu   | apt install ffmpeg | ⭐ |
| macOS    | brew install ffmpeg | ⭐⭐ |
| 其他 Linux | 包管理器或源码编译 | ⭐⭐⭐ |

---

## 📞 获取帮助

如果以上方法都无法解决，请提供：

1. **操作系统版本** - Windows 10/11, Ubuntu 22.04, macOS 13
2. **错误信息** - 完整的错误输出
3. **尝试过的方法** - 已试过哪些安装方式
4. **FFmpeg 版本** - `ffmpeg -version` 的输出

---

**最后更新:** 2026-05-05
