# FFmpeg 自动安装指南

## 📥 一键安装

通过 Web 界面，点击导航栏的 🎬 **FFmpeg**，然后点击 **"⬇️ 自动下载 FFmpeg"** 按钮。

### ⚠️ 重要说明

- **FFmpeg 文件夹不会预先存在**
- 只有在点击"自动下载"时才会创建 `ffmpeg/bin/` 目录
- 未安装前，项目中不会有 `ffmpeg/` 文件夹

---

## 🔍 安装流程

### 步骤 1: 检查 FFmpeg 状态

点击 🎬 FFmpeg 后，系统会检测：
- ✅ **已安装**: 显示 FFmpeg 信息和版本
- ❌ **未安装**: 显示下载按钮

### 步骤 2: 自动下载和安装

点击"自动下载"后：

```
1. 检查系统资源
     ↓
2. 检测操作系统
   ├─ Windows → 下载 ffmpeg-release-essentials.zip
   ├─ Linux   → 下载 ffmpeg-release-amd64-static.tar.xz
   └─ macOS   → 下载 ffmpeg-getrelease.zip
     ↓
3. 创建目录结构
   - ffmpeg/bin/        (存放最终文件)
   - ffmpeg/temp_download/ (临时目录)
     ↓
4. 下载压缩包
   - Windows: ~73 MB
   - Linux: ~76 MB
   - macOS: ~45 MB
     ↓
5. 解压到临时目录
     ↓
6. 提取 FFmpeg 文件
   - Windows: bin/ffmpeg.exe, bin/ffprobe.exe
   - Linux: ffmpeg, ffprobe
   - macOS: ffmpeg, ffprobe
     ↓
7. 复制到 ffmpeg/bin/
     ↓
8. 设置执行权限 (Linux/macOS)
     ↓
9. 验证文件完整性
     ↓
10. 清理临时文件
    - 删除压缩包
    - 删除临时目录
      ↓
11. 返回成功信息
```

### 步骤 3: 验证安装

**Web 界面**:
- 刷新页面
- 点击 🎬 FFmpeg
- 状态应为 "✓ 已安装"

**命令行**:
```bash
# Linux/macOS
cd ffmpeg/bin
./ffmpeg -version

# Windows
cd ffmpeg\bin
ffmpeg.exe -version
```

---

## 📂 目录结构

### 安装前
```
项目根目录/
├── web/
├── models/
└── ... (没有 ffmpeg/ 文件夹)
```

### 安装后
```
项目根目录/
├── web/
├── models/
├── ffmpeg/              ← 新创建
│   └── bin/
│       ├── ffmpeg       ← Linux/macOS
│       └── ffprobe
└── ...
```

---

## ⚠️ 常见问题

### Q1: 为什么看不到 ffmpeg 文件夹？

**A**: 这是正常的！FFmpeg 文件夹只有在点击"自动下载"时才会创建。

**解决**: 
1. 点击 🎬 FFmpeg
2. 点击"⬇️ 自动下载 FFmpeg"
3. 等待下载完成

### Q2: 下载后显示的是压缩包？

**A**: 可能解压失败或未完全解压。

**解决**:
1. 刷新页面重新检测
2. 如果仍显示未安装，重新点击下载
3. 查看错误提示

### Q3: bin 目录为空？

**A**: 解压路径可能不匹配。

**解决**: 手动安装（见下文）

### Q4: 权限问题 (Linux/macOS)?

**A**: 文件没有执行权限。

**解决**:
```bash
cd ffmpeg/bin
chmod +x ffmpeg ffprobe
./ffmpeg -version
```

---

## 🔧 手动安装（可选）

如果自动下载失败，可以手动安装。

### Windows

```bash
# 1. 下载
curl -L -o ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

# 2. 解压（手动或用 7-Zip）

# 3. 复制文件
# 从 解压目录/ffmpeg-<version>/bin/
# 复制到 项目的 ffmpeg/bin/
#   - ffmpeg.exe
#   - ffprobe.exe

# 4. 清理
# 删除下载的 .zip 文件
# 删除解压的临时目录
```

### Linux

```bash
# 1. 下载
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz

# 2. 解压
tar -xf ffmpeg-release-amd64-static.tar.xz

# 3. 创建目录
mkdir -p ffmpeg/bin

# 4. 复制
cd ffmpeg-*/
cp ffmpeg ffprobe ../ffmpeg/bin/
chmod +x ../ffmpeg/bin/*

# 5. 清理
cd ..
rm -rf ffmpeg-*/
rm ffmpeg-release-*.tar.xz
```

### macOS

```bash
# 1. 下载
curl -L -o ffmpeg.zip https://evermeet.cx/ffmpeg/getrelease/zip

# 2. 解压
unzip ffmpeg.zip

# 3. 创建目录
mkdir -p ffmpeg/bin

# 4. 复制
cp ffmpeg ffprobe ffmpeg/bin/
chmod +x ffmpeg/bin/*

# 5. 清理
rm ffmpeg.zip
```

---

## 🗑️ 卸载 FFmpeg

需要删除 FFmpeg 时：

```bash
# 删除整个 ffmpeg 目录
rm -rf ffmpeg/

# 或在 Windows
rmdir /s /q ffmpeg
```

重新安装时，再次点击"自动下载"即可。

---

## 📊 文件大小说明

| 文件 | Windows | Linux | macOS |
|------|---------|-------|-------|
| 压缩包 | ~73 MB | ~76 MB | ~45 MB |
| ffmpeg | ~34 MB | ~38 MB | ~23 MB |
| ffprobe | ~34 MB | ~38 MB | ~23 MB |

**总计占用**: ~70-80 MB（解压后）

---

## ⚙️ 环境变量（可选）

如果需要全局使用 FFmpeg：

### Windows
```bat
setx PATH "%PATH%;C:\path\to\project\ffmpeg\bin"
```

### Linux/macOS
```bash
echo 'export PATH="$PATH:/path/to/project/ffmpeg/bin"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🔍 故障排查

### 查看下载日志

在 Web 界面：
1. 点击 🎬 FFmpeg
2. 点击下载按钮
3. 查看进度条下方消息

### 检查文件完整性

```bash
# Windows
ffmpeg/bin/ffmpeg.exe -version

# Linux/macOS
./ffmpeg/bin/ffmpeg -version
```

### 完全重装

```bash
# 1. 删除
rm -rf ffmpeg/

# 2. 刷新 Web 页面

# 3. 重新下载
# 点击"自动下载"按钮
```

---

## 💡 最佳实践

1. **按需安装**
   - 不需要预先创建 ffmpeg 文件夹
   - 需要使用时再点击下载

2. **不要提交到 Git**
   - `.gitignore` 已配置忽略 `ffmpeg/bin/`
   - 避免仓库体积过大

3. **定期更新**
   - Web 界面重新下载即可
   - 旧版本会自动覆盖

4. **保持结构**
   - FFmpeg 必须在 `ffmpeg/bin/` 目录
   - 方便统一管理和清理

---

## 📖 相关文档

- [模型管理功能](./MODEL_MANAGEMENT_FEATURE.md) - 清理优化空间
- [大小说明](./MODEL_SIZE_EXPLANATION.md) - 为什么下载大小和实际占用不同

---

**版本**: v2.0  
**更新日期**: 2026-05-05  
**状态**: ✅ 已优化（按需创建）
