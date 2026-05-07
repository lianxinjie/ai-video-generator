# Windows 环境 FFmpeg 下载问题排查

## 问题症状
- POST /api/download-ffmpeg 返回 503
- POST /api/install-dependencies 返回 404

## 已修复的问题

### 1. 导入缺失 (已修复)
- ✅ 添加 `import platform`
- ✅ 添加 `from pathlib import Path`
- ✅ 添加 `import time`
- ✅ 添加 `import stat`

### 2. 下载镜像优化 (已完成)
Windows 镜像优先级：
1. GitHub GyanD (0.67MB/s, 83MB, 2 分钟)
2. GitHub BtbN (0.77MB/s, 209MB, 4.5 分钟)
3. gyan.dev (0.21MB/s, 104MB, 8.5 分钟)

### 3. 调试日志 (已添加)
后端会输出：
```
[FFmpeg 下载] ===== 开始下载流程 =====
[FFmpeg 下载] 系统：Windows
[FFmpeg 下载] 可用镜像数量：3
[FFmpeg 下载] 主镜像：https://...
[FFmpeg 下载] 发送 HEAD 请求...
[FFmpeg 下载] HEAD 响应：HTTP XXX
```

## 排查步骤

### 步骤 1：重启 Flask 服务
```powershell
# 停止现有服务 (Ctrl+C)

# 重新启动
cd text-to-video-local
python web/app.py
```

### 步骤 2：查看控制台日志
点击"下载 FFmpeg"后，查看 Python 控制台输出

### 步骤 3：检查日志内容
- 如果看到 `[FFmpeg 下载]` 日志：说明服务正常，查看具体错误
- 如果没有日志：服务未重启或代码未更新

### 步骤 4：检查 Git 状态
```powershell
git log --oneline -3
```
应该看到最近的提交

### 步骤 5：更新代码
```powershell
git pull origin 260501-feat-add-hybrid-mode
```

## 常见错误

### 503 错误
原因：URL 预检查失败
解决：查看日志中的 HEAD 响应状态码

### 404 错误
原因：路由未注册或服务未重启
解决：重启 Flask 服务

### 语法错误
原因：代码修改导致语法错误
解决：运行 `python -m py_compile web/app.py` 检查

## 手动下载备选

如果自动下载一直失败：

1. 手动下载：https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-essentials_build.zip
2. 解压后复制 `bin/` 目录到：`text-to-video-local/ffmpeg/bin/`
3. 重启 Web 服务
