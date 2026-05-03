# 🌍 跨平台快速参考

## 一鍵安裝

| 系统 | 命令 |
|------|------|
| **Linux** | `bash install.sh` |
| **macOS** | `bash install.sh` |
| **Windows** | `install.bat` (CMD/PowerShell) |
| **Windows (Git Bash)** | `bash install.sh` |
| **WSL** | `bash install.sh` |

## 启动服务

| 系统 | Web 模式 | 混合模式 | 检查安装 |
|------|---------|---------|---------|
| **Linux/macOS** | `bash start.sh web` | `bash start.sh hybrid` | `bash start.sh check` |
| **Windows** | `start.bat web` | `start.bat hybrid` | `start.bat check` |
| **WSL/Git Bash** | `bash start.sh web` | `bash start.sh hybrid` | `bash start.sh check` |

## 手动运行

```bash
# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows (CMD/PowerShell):
venv\Scripts\activate

# Windows (Git Bash):
source venv/Scripts/activate

# 运行模式
python personal_mode/run.py -m personal   # 个人模式
python personal_mode/run.py -m hybrid     # 混合模式
python personal_mode/run.py -m collaborative  # 协同模式
python web/app.py                         # Web 模式
```

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **Python** | 3.10+ | 3.11+ |
| **内存** | 8GB | 16GB+ |
| **磁盘** | 30GB | 50GB+ |
| **GPU** | 可选 | NVIDIA 8GB+ / Apple M1+ |

## 平台支持等级

- ⭐⭐⭐⭐⭐ **Linux** - 完全支持，推荐部署
- ⭐⭐⭐⭐ **Windows** - 良好支持，需 Git Bash 或 WSL
- ⭐⭐⭐⭐ **macOS** - 良好支持，Apple Silicon 优化
- ⭐⭐ **iOS** - 仅 Web 访问 (浏览器)

## 快速故障排查

### Python 未找到
```bash
# Linux/macOS
sudo apt install python3 python3-pip  # Ubuntu/Debian
brew install python3                  # macOS

# Windows
# 下载 https://www.python.org/downloads/
```

### FFmpeg 未找到
```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
# 或下载 https://ffmpeg.org/download.html
```

### 权限错误 (Linux/macOS)
```bash
chmod +x install.sh start.sh
bash install.sh
```

### Windows 路径错误
```powershell
# 使用 Git Bash 而不是 CMD
# 或安装 WSL2
```

## Web 模式访问

启动后访问:
- 本地：http://localhost:5000
- 局域网：http://你的IP:5000
- iOS: Safari 访问上述地址

## 详细文档

查看完整跨平台指南：
[CROSS_PLATFORM_COMPATIBILITY.md](./CROSS_PLATFORM_COMPATIBILITY.md)
