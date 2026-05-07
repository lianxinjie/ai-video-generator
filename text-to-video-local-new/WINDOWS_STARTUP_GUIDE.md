# Windows 环境快速启动指南

## 问题诊断

### 症状
- `/setup` 页面点击"安装 Python 依赖"返回 404
- `/api/download-ffmpeg` 返回 503

### 原因
Flask 服务未重启，仍在运行旧代码

## 快速解决

### 方法 1：使用快速修复脚本
```powershell
cd text-to-video-local
./quick_fix_windows.sh
```

### 方法 2：手动重启
```powershell
# 1. 停止当前服务 (Ctrl+C)

# 2. 确认 Python 可用
python --version

# 3. (可选) 安装/更新依赖
pip install flask pillow psutil requests --break-system-packages

# 4. 运行诊断 (可选)
python diagnose_routes.py

# 5. 启动服务
python web/app.py
```

## 验证启动成功

启动成功后，控制台会显示：
```
======================================================================
 AI 视频生成器 - Windows 环境
======================================================================
 Flask 应用：<Flask 'web.app'>
 注册路由数：52

 关键 API 路由:
   ✅ /api/check-dependencies
   ✅ /api/install-dependencies
   ✅ /api/task/<id>

======================================================================
 * Running on http://127.0.0.1:5000
```

## 测试步骤

### 1. 访问设置页面
```
http://127.0.0.1:5000/setup
```

### 2. 点击"开始安装依赖"
查看按钮是否可用

### 3. 浏览器控制台（F12）
- Network 标签查看请求 URL
- Console 标签查看错误信息

### 4. Python 控制台
查看 `[pip 安装]` 开头的日志

## 仍然 404？

### 检查请求 URL
浏览器 F12 → Network → 点击请求 → 查看 Request URL

应该是：
```
http://127.0.0.1:5000/api/check-dependencies (GET)
http://127.0.0.1:5000/api/install-dependencies (POST)
```

### 检查端口
确认访问的是正确的端口（默认 5000）

### 清除缓存
- Ctrl + F5 强制刷新
- 或清除浏览器缓存

## 手动安装依赖

如果自动安装仍然失败：

```powershell
cd text-to-video-local
pip install flask pillow psutil torch torchvision --index-url https://download.pytorch.org/whl/cpu transformers diffusers huggingface-hub modelscope edge-tts pydub --break-system-packages
```

## 联系支持

提供以下信息：
1. Python 版本：`python --version`
2. Flask 启动日志
3. 浏览器控制台错误截图
4. Network 标签的请求详情
