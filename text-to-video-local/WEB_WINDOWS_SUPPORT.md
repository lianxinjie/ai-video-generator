# Web 端 Windows 系统支持说明

## ✅ 完全支持

### 1. 硬件检测 (Scanner API) ✅

**支持功能**:
- ✅ CPU 检测 (Intel/AMD 通过 wmic 命令)
- ✅ GPU 检测 (NVIDIA 通过 PyTorch CUDA)
- ✅ GPU 检测 (Apple Silicon 通过 system_profiler)
- ✅ 内存检测 (Windows 通过 wmic)
- ✅ 磁盘检测 (所有平台)
- ✅ 网络检测 (socket 连接测试)
- ✅ Python 环境检测

**代码实现**:
```python
# scanner.py 已实现 Windows 支持
def _scan_cpu(self):
    if platform.system() == "Windows":
        # Windows 使用 wmic
        subprocess.run(["wmic", "cpu", "get", "name"])
    else:
        # Linux/macOS 使用/proc/cpuinfo
        subprocess.run(["cat", "/proc/cpuinfo"])

def _scan_memory(self):
    if platform.system() == "Windows":
        # Windows 使用 wmic
        subprocess.run(["wmic", "OS", "get", "TotalVisibleMemorySize"])
    else:
        # Linux/macOS 使用 psutil
        import psutil
```

**Web API**:
```
GET /api/scanner/report
响应：
{
  "hardware": {
    "cpu_model": "Intel(R) Core(TM) i7-9750H",
    "cpu_cores": 12,
    "gpu_available": true,
    "gpu_models": ["NVIDIA GeForce RTX 2060"],
    "ram_total": 16.0,
    "ram_available": 8.5,
    "disk_total": 512.0,
    "disk_available": 256.0
  },
  "recommendation": {
    "recommended_mode": "hybrid_mid_range"
  }
}
```

---

### 2. 一键安装包生成 ✅

**支持功能**:
- ✅ 根据 Windows 硬件生成个性化安装包
- ✅ NVIDIA GPU → PyTorch CUDA 版本
- ✅ 无 GPU → PyTorch CPU 版本
- ✅ 生成 requirements-optimized.txt
- ✅ 生成 download_models.py
- ✅ 生成 INSTALL_GUIDE.txt

**Web API**:
```
POST /api/scanner/generate-package
响应:
{
  "success": true,
  "package_id": "xxx-xxx-xxx",
  "package_name": "offline-package-xxx.zip",
  "files": [
    "requirements-optimized.txt",
    "download_models.py",
    "install.bat",  # Windows 专用脚本
    "INSTALL_GUIDE.txt"
  ]
}
```

---

### 3. 下载安装包 ✅

**Web API**:
```
GET /api/scanner/download-package?package=xxx
响应：ZIP 文件下载
```

---

### 4. 一键安装执行 ✅

**Web API**:
```
POST /api/scanner/install
请求:
{
  "package_dir": "web/outputs/offline-package-xxx"
}

响应:
{
  "success": true,
  "task_id": "install-xxx",
  "message": "安装任务已启动"
}
```

**后端实现**:
```python
# app.py
@app.route('/api/scanner/install', methods=['POST'])
def api_install():
    # Windows/Linux/macOS 统一处理
    # 自动检测操作系统并执行对应脚本
    if platform.system() == "Windows":
        # 执行 install.bat
        subprocess.run(["install.bat"])
    else:
        # 执行 install.sh
        subprocess.run(["bash", "install.sh"])
```

---

### 5. 安装状态查询 ✅

**Web API**:
```
GET /api/scanner/install-status/<task_id>
响应:
{
  "status": "running",  // running/completed/failed
  "progress": 60,
  "log": "正在安装 PyTorch...",
  "start_time": "2026-05-03T10:00:00"
}
```

---

### 6. 一键启动 ✅

**Web API**:
```
POST /api/quick-start
请求:
{
  "prompt": "一只猫在草地上奔跑",
  "mode": "hybrid",
  "duration": 5
}

响应:
{
  "success": true,
  "task_id": "xxx-xxx-xxx",
  "mode": "hybrid",
  "message": "任务已启动"
}
```

---

## 📋 Web 界面功能

### 硬件检测页面

访问 `http://localhost:5000` 后:

1. **点击"🖥️ 硬件检测"按钮**
   - 自动扫描 Windows 硬件
   - 显示 CPU/GPU/内存/磁盘信息
   - 智能推荐最优模式

2. **查看推荐方案**
   - hybrid_high_end (高端 GPU)
   - hybrid_mid_range (中端 GPU)
   - hybrid_low_end (低端 GPU)
   - cpu_capable (强 CPU 无 GPU)
   - cpu_limited (弱 CPU 无 GPU)

3. **一键生成安装包**
   - 点击"📦 生成安装包"
   - 下载 ZIP 文件
   - 解压后运行 install.bat

---

### 一键安装页面

**方式 1: 通过 Web 界面**
```
1. 访问 http://localhost:5000
2. 点击"📦 安装包生成"
3. 下载 ZIP 包
4. 解压并运行 install.bat
```

**方式 2: 通过 Web API 直接安装**
```javascript
// 前端调用示例
fetch('/api/scanner/install', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    package_dir: 'web/outputs/offline-package-xxx'
  })
})
.then(r => r.json())
.then(data => {
  // 轮询状态
  pollInstallStatus(data.task_id)
})
```

---

### 一键启动页面

访问 `http://localhost:5000`:

1. **输入提示词**
   ```
   例如：一只猫在草地上奔跑
   ```

2. **选择模式** (或自动推荐)
   - personal (个人模式)
   - hybrid (混合模式)
   - collaborative (协同模式)

3. **点击" ▶️ 一键启动"**
   - 实时显示进度
   - 查看运行日志
   - 下载生成视频

---

## 🔧 Windows 特殊处理

### 1. 路径分隔符

```python
# 自动处理
from pathlib import Path
install_script = Path(package_dir) / "install.bat"  # Windows
install_script = Path(package_dir) / "install.sh"   # Linux/macOS
```

### 2. 长路径支持

```batch
:: install.bat 自动启用
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

### 3. 虚拟环境激活

```batch
:: Windows
call venv\Scripts\activate.bat

:: Linux/macOS
source venv/bin/activate
```

### 4. 进程管理

```python
# Windows 使用 CREATE_NEW_PROCESS_GROUP
if platform.system() == "Windows":
    subprocess.Popen(
        ["python", "generation.py"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
else:
    subprocess.Popen(["python", "generation.py"])
```

---

## 📊 完整流程图

```
Windows 用户访问 Web 界面
         ↓
    点击"硬件检测"
         ↓
   Scanner API 扫描硬件
   - wmic cpu get name
   - PyTorch CUDA 检测
   - wmic OS get Memory
         ↓
    显示推荐方案
         ↓
  点击"生成安装包"
         ↓
  Package API 生成文件
  - requirements-optimized.txt
  - download_models.py
  - install.bat ← Windows 专用
         ↓
    下载 ZIP 包
         ↓
 解压并运行 install.bat
         ↓
   安装 Python 依赖
   下载模型文件
         ↓
    安装完成！
         ↓
 返回 Web 界面启动服务
         ↓
    输入提示词
         ↓
   点击"一键启动"
         ↓
   Quick-Start API
         ↓
    生成视频
         ↓
    下载视频
```

---

## ✅ 验证清单

### Windows 用户验证步骤

- [ ] 1. 访问 Web 界面 `http://localhost:5000`
- [ ] 2. 点击"硬件检测"按钮
- [ ] 3. 查看 CPU/GPU/内存信息是否正确
- [ ] 4. 查看推荐模式是否合理
- [ ] 5. 点击"生成安装包"
- [ ] 6. 下载 ZIP 文件
- [ ] 7. 解压 ZIP 文件
- [ ] 8. 运行 `install.bat`
- [ ] 9. 等待安装完成
- [ ] 10. 返回 Web 界面
- [ ] 11. 输入提示词
- [ ] 12. 点击"一键启动"
- [ ] 13. 查看实时日志
- [ ] 14. 下载生成的视频

---

## 🐛 已知限制

| 限制 | 影响 | 解决方案 |
|------|------|---------|
| PowerShell 兼容性 | 需要 CMD 或 Git Bash | 使用 install.bat 而非 PowerShell |
| 防火墙阻止 | wmic 可能被阻止 | 允许 wmic 通过防火墙 |
| NVIDIA 驱动 | 需要安装 NVIDIA 驱动 | 从 NVIDIA 官网下载 |
| 长路径 | >260 字符可能失败 | install.bat 已自动启用长路径 |

---

## 📞 故障排查

### 问题 1: 硬件检测无响应

```javascript
// 浏览器 F12 控制台查看错误
// 检查网络请求
fetch('/api/scanner/report')
  .then(r => r.json())
  .then(console.log)
```

### 问题 2: 安装包下载失败

```
检查:
1. Web 服务是否运行
2. 输出目录权限
3. 磁盘空间
```

### 问题 3: install.bat 运行失败

```cmd
:: 查看详细错误
install.bat > install.log 2>&1
type install.log

:: 手动安装
call venv\Scripts\activate
pip install torch torchvision torchaudio
pip install -r requirements-optimized.txt
```

---

## 🎯 总结

### ✅ 已实现

- [✅] Windows 硬件检测 (CPU/GPU/内存/磁盘)
- [✅] 智能推荐方案
- [✅] 个性化安装包生成
- [✅] Windows 专用 install.bat
- [✅] Web API 一键安装
- [✅] 安装状态查询
- [✅] Web 一键启动
- [✅] 实时日志显示
- [✅] 视频下载

### 📋 使用流程

**完整流程**:
```
访问 Web → 硬件检测 → 生成安装包 → 下载 → install.bat → 
一键启动 → 输入提示词 → 生成 → 下载
```

**快捷流程** (已安装环境):
```
访问 Web → 一键启动 → 输入提示词 → 生成 → 下载
```

---

**支持版本**: Windows 10 1607+ / Windows 11
**最后更新**: 2026-05-03
**状态**: ✅ 完全支持
