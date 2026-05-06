# Windows 环境依赖修复指南

## 问题诊断结果

根据最新检测日志，发现以下问题：

### ❌ 问题 1: torch/diffusers/modelscope 导入失败
**错误信息：**
```
[WinError 126] 找不到指定的模块
```

**根本原因：**
缺少 **Microsoft Visual C++ Redistributable** 运行库

**解决方案：**
1. 下载 VC++ 运行库：
   ```
   https://aka.ms/vs/17/release/vc_redist.x64.exe
   ```

2. 安装下载的文件（双击运行）

3. **重启电脑**（重要！）

4. 重新启动 Web 服务
   ```powershell
   python quick_start.py
   ```

5. 再次检测依赖
   ```
   http://localhost:5000/setup
   ```

---

### ❌ 问题 2: pydub 导入失败
**错误信息：**
```
No module named 'pyaudioop'
```

**根本原因：**
Python 3.13 移除了 `audioop` 模块，`pydub` 依赖它

**解决方案：**

**方案 A: 安装 audioop-lts _compat 包
```powershell
pip install audioop-lts --break-system-packages
```

**方案 B: 暂时不安装 pydub（如果不使用配音功能）**
- pydub 是**可选依赖**
- 只在需要音频处理时才需要

**方案 C: 降级到 Python 3.12
```powershell
# 如果经常使用 pydub，建议降级到 Python 3.12
```

---

## 完整修复流程

### 步骤 1: 安装 VC++ 运行库
1. 下载：https://aka.ms/vs/17/release/vc_redist.x64.exe
2. 双击安装
3. **重启电脑**

### 步骤 2: 修复 pydub（可选）
如果需要使用 pydub：
```powershell
pip install audioop-lts --break-system-packages
```

### 步骤 3: 重新检测依赖
```powershell
# 启动服务
python quick_start.py

# 访问 Setup 页面
http://localhost:5000/setup

# 点击"重新检测"
```

### 步骤 4: 验证结果

**应该看到：**
```
[依赖检测] ✓ torch: 2.11.0+cpu
[依赖检测] ✓ diffusers: 0.38.0
[依赖检测] ✓ modelscope: 1.36.3
[依赖检测] ✓ pydub: 0.25.1
[依赖检测] 汇总：10/10 已安装
```

---

## 常见问题

### Q: VC++ 运行库安装失败
**A:** 确保：
- 以**管理员身份**运行安装程序
- 关闭所有正在运行的程序
- 检查 Windows 版本兼容性

### Q: 安装后还是检测失败
**A:** 
1. 确认已**重启电脑**
2. 重启后**重新启动 Flask 服务**
3. 在 Setup 页面点击"**重新检测**"

### Q: audioop-lts 安装失败
**A:** 
```powershell
# 使用 --break-system-packages 参数
pip install audioop-lts --break-system-packages

# 或者使用虚拟环境
python -m venv venv
venv\Scripts\activate
pip install audioop-lts
```

---

## 检测日志说明

### ✓ 成功标志
```
[依赖检测] ✓ pkg: version
[依赖检测] 汇总：10/10 已安装
```

### ⚠️ 需要修复
```
[依赖检测] ⚠ pkg: 缺少 VC++ 运行库
[依赖检测] ⚠ pkg: Python 3.13 兼容性问题
```

### ✗ 其他错误
```
[依赖检测] ✗ pkg: 错误信息
```

---

**修复完成后，请重新运行依赖检测！**
