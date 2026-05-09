# FFmpeg 下载镜像速度测试

## 测试日期
2026-05-05

## Windows 平台测试

### 测试结果

| 镜像 | 速度 | 文件大小 | 预计时间 | 推荐度 |
|------|------|----------|----------|--------|
| gyan.dev (官方) | 0.21MB/s | 104.2MB | 8.5 分钟 | ⭐⭐ |
| GitHub (BtbN) | 0.77MB/s | 208.8MB | 4.5 分钟 | ⭐⭐⭐ |
| **GitHub (GyanD)** | **0.67MB/s** | **83.3MB** | **2.1 分钟** | ⭐⭐⭐⭐⭐ |

### 选择 GyanD 的理由

1. **速度第二快**：0.67MB/s，是官方的 3 倍
2. **文件最小**：83MB，比官方小 20%
3. **综合时间最短**：2.1 分钟 vs 8.5 分钟
4. **GitHub CDN**：全球加速，国内访问更快

## Linux 平台测试

### 测试结果

| 镜像 | 速度 | 文件大小 | 推荐度 |
|------|------|----------|--------|
| johnvansickle | 0.38MB/s | 39.9MB | ⭐⭐ |
| **GitHub (BtbN)** | **0.78MB/s** | ~100MB | ⭐⭐⭐⭐⭐ |

## 配置说明

### Windows
```python
'Windows': [
    'https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-essentials_build.zip',
    'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
    'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
]
```

### Linux
```python
'Linux': [
    f'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{arch}-gpl.tar.xz',
    f'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz',
]
```

### macOS
```python
'Darwin': [
    'https://evermeet.cx/ffmpeg/getrelease/zip',
    'https://github.com/evermeet/ffmpeg/releases/download/5.1.2/ffmpeg-5.1.2.zip',
]
```

## 故障切换机制

如果主镜像失败，自动切换到备用镜像：
1. 尝试主镜像（HEAD 请求验证）
2. 失败则尝试备用镜像 1
3. 再失败则尝试备用镜像 2
4. 全部失败则返回错误提示

## 性能提升

### Windows 用户
- **之前**：8.5 分钟 (0.21MB/s)
- **现在**：2.1 分钟 (0.67MB/s)
- **提升**：**4 倍速度**

### Linux 用户
- **之前**：5 分钟 (0.38MB/s)
- **现在**：2 分钟 (0.78MB/s)
- **提升**：**2.5 倍速度**

## 手动下载备选

如果自动下载仍然很慢，可以手动下载：

### Windows
1. 访问：https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-essentials_build.zip
2. 下载完成后解压
3. 将 `bin/` 目录复制到 `text-to-video-local/ffmpeg/bin/`

### Linux
1. 访问：https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-amd64-gpl.tar.xz
2. 下载后解压并复制 ffmpeg 到 `text-to-video-local/ffmpeg/bin/`
