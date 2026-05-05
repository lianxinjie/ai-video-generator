# FFmpeg 自动安装指南

## 📥 一键安装

通过 Web 界面，点击导航栏的 🎬 **FFmpeg**，然后点击 **"⬇️ 自动下载 FFmpeg"** 按钮。

系统会自动完成以下步骤：

### 安装流程

1. **资源检查** - 检查磁盘空间和系统资源
2. **下载** - 根据系统下载对应版本
   - Windows: `.zip` 压缩包 (~73 MB)
   - Linux: `.tar.xz` 压缩包 (~76 MB)
   - macOS: `.zip` 压缩包
3. **解压** - 自动解压到 `ffmpeg/bin/` 目录
4. **配置** - 设置执行权限（Linux/macOS）
5. **清理** - 删除临时下载文件

### 解压逻辑

#### Windows
```
下载：ffmpeg/temp_download/ffmpeg.zip
       ↓ 解压
临时：ffmpeg/temp_download/ffmpeg-<version>/
         ├── bin/
         │   ├── ffmpeg.exe  ✓ 复制到 ffmpeg/bin/
         │   └── ffprobe.exe ✓ 复制到 ffmpeg/bin/
         └── 其他文件...
       ↓ 复制 bin/ 目录
输出：ffmpeg/bin/
         ├── ffmpeg.exe
         └── ffprobe.exe
```

#### Linux/macOS
```
下载：ffmpeg/temp_download/ffmpeg.tar.xz
       ↓ 解压
临时：ffmpeg/temp_download/ffmpeg-<version>-static/
         ├── ffmpeg  ✓ 复制到 ffmpeg/bin/
         └── ffprobe ✓ 复制到 ffmpeg/bin/
       ↓ 复制文件
输出：ffmpeg/bin/
       ├── ffmpeg  (可执行权限)
       └── ffprobe (可执行权限)
```

---

## ✅ 验证安装

### 方法 1: Web 界面查看

刷新页面后，点击 🎬 FFmpeg，应该显示 "✓ 已安装"。

### 方法 2: 命令行验证

#### Windows
```bash
cd ffmpeg/bin
ffmpeg.exe -version
```

#### Linux/macOS
```bash
cd ffmpeg/bin
./ffmpeg -version
```

**成功输出示例**:
```
ffmpeg version N-xxxxxx Copyright (c) ...
configuration: --enable-gpl --enable-libx264 ...
libavutil      xx.x.xxx
libavcodec     xx.x.xxx
...
```

---

## ⚠️ 常见问题

### 1. 下载后显示的是压缩包文件

**问题**: 下载目录中仍显示 `.zip` 或 `.tar.xz` 文件

**原因**: 
- 解压可能失败
- 临时文件未清理

**解决**:
```bash
# 手动清理
cd ffmpeg
rm -rf temp_download/

# 重新下载
# 在 Web 界面点击"自动下载"
```

### 2. bin 目录为空

**问题**: `ffmpeg/bin/` 目录存在但没有文件

**原因**:
- 压缩包格式变化
- 解压路径不匹配

**解决**: 手动下载

#### Windows 手动安装
```bash
# 1. 下载
curl -L -o ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

# 2. 解压（手动或用 7-Zip）
# 3. 复制 bin/ffmpeg.exe 和 bin/ffprobe.exe 到 ffmpeg/bin/
# 4. 删除 ffmpeg.zip
```

#### Linux 手动安装
```bash
# 1. 下载
wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz

# 2. 解压
tar -xf ffmpeg-release-amd64-static.tar.xz

# 3. 复制
cd ffmpeg-*/
cp ffmpeg ffprobe ../ffmpeg/bin/
chmod +x ../ffmpeg/bin/*

# 4. 清理
cd ..
rm -rf ffmpeg-*/
rm ffmpeg-release-*.tar.xz
```

### 3. 权限问题 (Linux/macOS)

**问题**: `Permission denied` 或无法执行

**解决**:
```bash
cd ffmpeg/bin
chmod +x ffmpeg ffprobe
./ffmpeg -version
```

---

## 🔧 手动安装选项

如果自动下载失败，可以选择手动安装。

### Windows

1. **下载** 
   - 官方：https://www.gyan.dev/ffmpeg/builds/
   - 选择：`ffmpeg-release-essentials.zip`

2. **解压**
   - 使用 7-Zip 或 Windows 解压
   - 解压到临时目录

3. **复制**
   ```
   解压目录/ffmpeg-<version>/bin/
     ├── ffmpeg.exe → 复制到项目的 ffmpeg/bin/
     └── ffprobe.exe → 复制到项目的 ffmpeg/bin/
   ```

4. **清理**
   - 删除下载的 `.zip` 文件
   - 删除解压的临时目录

### Linux

1. **下载**
   ```bash
   # AMD64/Intel
   wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz
   
   # ARM64 (Raspberry Pi 等)
   wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-arm64-static.tar.xz
   ```

2. **解压**
   ```bash
   tar -xf ffmpeg-release-*-static.tar.xz
   ```

3. **复制**
   ```bash
   cd ffmpeg-*/
   cp ffmpeg ffprobe ../ffmpeg/bin/
   chmod +x ../ffmpeg/bin/*
   ```

4. **清理**
   ```bash
   cd ..
   rm -rf ffmpeg-*/
   rm ffmpeg-release-*.tar.xz
   ```

### macOS

1. **下载**
   ```bash
   curl -L -o ffmpeg.zip https://evermeet.cx/ffmpeg/getrelease/zip
   ```

2. **解压**
   ```bash
   unzip ffmpeg.zip
   ```

3. **复制**
   ```bash
   cp ffmpeg ffprobe ffmpeg/bin/
   chmod +x ffmpeg/bin/*
   ```

4. **清理**
   ```bash
   rm ffmpeg.zip
   ```

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

### 检查下载进度

```bash
# 查看下载日志（Web 界面）
# 点击 🎬 FFmpeg 后查看进度条和提示信息
```

### 验证文件完整性

```bash
# Windows
ffmpeg/bin/ffmpeg.exe -version

# Linux/macOS
./ffmpeg/bin/ffmpeg -version
```

### 清理重装

```bash
# 删除 FFmpeg 目录
rm -rf ffmpeg/

# 重新下载
# 在 Web 界面点击"自动下载"
```

---

## 💡 最佳实践

1. **不要提交 FFmpeg 到 Git**
   - `.gitignore` 已配置忽略 `ffmpeg/bin/`
   - 避免仓库体积过大

2. **定期更新 FFmpeg**
   - Web 界面重新下载即可
   - 旧版本会自动覆盖

3. **使用静态编译版本**
   - 无需系统依赖
   - 跨平台兼容

4. **保持 ffmpeg/bin/ 结构**
   - 所有工具必须在 `ffmpeg/bin/` 目录
   - 方便统一管理和清理

---

**相关文档**:
- [FFmpeg 下载脚本](./download_ffmpeg.py) - 独立下载工具
- [模型管理功能](./MODEL_MANAGEMENT_FEATURE.md) - 清理优化空间
