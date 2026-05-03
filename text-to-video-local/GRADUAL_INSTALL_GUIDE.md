# 渐进式安装指南

## 🌟 新功能：零依赖启动，Web 界面引导安装

不需要预先安装任何依赖，只需 Python 3.10+ 即可启动！

---

## 🚀 快速开始

### 1. 零依赖启动

```bash
# 无需任何安装，直接运行
python3 quick_start.py
```

### 2. 访问 Web 界面

- **如果检测到 Flask 已安装**：
  - 自动启动完整功能 Web 服务
  - 访问：http://localhost:5000

- **如果 Flask 未安装**：
  - 启动快速预览模式
  - 访问：http://localhost:8080
  - 自动打开浏览器

### 3. Web 界面引导安装

1. **自动检测依赖状态**
   - ✅ 已安装依赖
   - ❌ 未安装依赖
   - 📊 显示安装进度

2. **选择要安装的包**
   - ✅ **Flask** (必需) - Web 服务框架
   - ✅ **Pillow** (推荐) - 图片处理
   - ✅ **psutil** (推荐) - 系统监控
   - ⚪ **PyTorch** (可选) - AI 模型（体积大）

3. **一键安装**
   - 点击"开始安装"
   - 实时查看安装日志
   - 安装完成后刷新页面

---

## 💡 优势

### 传统安装方式
```bash
# 步骤繁琐
pip install flask pillow psutil torch
python web/app.py
```

**问题**：
- ❌ 需要知道安装哪些依赖
- ❌ 不知道该安装 CPU 还是 GPU 版 PyTorch
- ❌ 安装失败不知道原因
- ❌ 一次性安装所有，时间长

### 渐进式安装 ✅
```bash
# 一步完成
python3 quick_start.py
```

**优势**：
- ✅ 自动检测已安装依赖
- ✅ 智能推荐安装方案
- ✅ 实时显示安装进度
- ✅ 按需安装，节省时间
- ✅ 安装失败有明确提示

---

## 📋 完整流程

```
1. 运行 quick_start.py
   ↓
2. 自动检测 Flask 是否安装
   ↓
3a. 已安装 → 启动完整功能 (端口 5000)
3b. 未安装 → 启动预览模式 (端口 8080)
   ↓
4. 浏览器访问 Web 界面
   ↓
5. 查看依赖状态
   ↓
6. 选择要安装的包
   ↓
7. 点击"开始安装"
   ↓
8. 实时查看安装日志
   ↓
9. 安装完成，刷新页面
   ↓
10. 开始使用！
```

---

## 🎯 使用场景

### 场景 1：首次使用（无依赖）

```bash
# 1. 直接运行
python3 quick_start.py

# 2. 访问 http://localhost:8080
# 3. 在 Web 界面点击"开始安装"
# 4. 等待安装完成
# 5. 刷新页面，开始使用
```

**优点**：
- 不需要知道要安装什么
- Web 界面图形化引导
- 安装进度可视化

### 场景 2：已有部分依赖

```bash
# 1. 运行 quick_start.py
# 2. 自动检测已安装依赖
# 3. Web 界面显示缺失的包
# 4. 只安装缺失的包
```

**优点**：
- 避免重复安装
- 只显示需要的包
- 节省时间

### 场景 3：完全安装

```bash
# 仍然可以用 Web 界面
python3 quick_start.py

# 或者手动安装
pip install -r requirements.txt
python3 web/app.py
```

**优点**：
- 灵活选择安装方式
- 两种方法都支持

---

## 🖥️ 跨平台支持

### Windows

```cmd
:: 命令行
python quick_start.py

:: 或使用批处理
quick_start.bat  (待创建)
```

### Linux/macOS

```bash
# 终端
python3 quick_start.py

# 或使用脚本
./quick_start.sh  (待创建)
```

---

## 🔧 技术细节

### 工作原理

1. **依赖检测**
   ```python
   try:
       import flask
       deps['flask'] = {'installed': True}
   except ImportError:
       deps['flask'] = {'installed': False}
   ```

2. **智能安装**
   ```python
   # 检测 GPU 自动选择 PyTorch 版本
   if has_gpu:
       pip install torch --index-url cu121
   else:
       pip install torch --index-url cpu
   ```

3. **进度显示**
   ```javascript
   fetch('/api/check-dependencies')
     .then(r => r.json())
     .then(data => updateUI(data))
   ```

### API 接口

| API | 方法 | 用途 |
|-----|------|------|
| `/api/check-dependencies` | GET | 检查依赖状态 |
| `/api/install-dependencies` | POST | 安装依赖 |
| `/api/status` | GET | 获取系统状态 |

---

## 📊 对比表

| 特性 | 传统方式 | 渐进式安装 |
|------|---------|-----------|
| 启动命令 | `pip install ...` + `python app.py` | `python quick_start.py` |
| 预安装依赖 | 需要 | 不需要 |
| 安装指导 | 无 | Web 界面图形化 |
| 进度显示 | 命令行文本 | 可视化进度条 |
| 智能推荐 | 无 | 自动检测缺少包 |
| 按需选择 | 困难 | 自由选择 |
| 错误提示 | 命令行 | 友好提示 |

---

## ❓ 常见问题

### Q1: 需要预先安装 pip 吗？
**A**: 不需要，`quick_start.py` 使用 Python 内置模块，启动后通过 Web 界面安装 pip 包。

### Q2: 安装失败怎么办？
**A**: Web 界面会显示详细错误信息，并提供解决建议。

### Q3: 可以只安装部分依赖吗？
**A**: 可以！Flask 是必需的，其他包可自由选择。

### Q4: PyTorch 必须安装吗？
**A**: 不必须。不使用 AI 功能可以不装。

### Q5: 安装后需要重启服务吗？
**A**: 不需要，安装完成后刷新页面即可。

---

## 🎯 最佳实践

### 推荐流程

1. **首次使用**
   ```bash
   python3 quick_start.py
   # Web 界面引导安装
   ```

2. **日常使用**
   ```bash
   python3 quick_start.py
   # 自动启动完整功能
   ```

3. **开发调试**
   ```bash
   python3 web/app.py
   # 直接使用 Flask
   ```

### 安装建议

| 用途 | 推荐安装 |
|------|---------|
| 基础功能 | Flask + Pillow |
| 完整功能 | Flask + Pillow + psutil |
| AI 功能 | 全选（包括 PyTorch） |

---

## 📁 相关文件

- `quick_start.py` - 渐进式安装启动脚本
- `web/templates/install.html` - 安装向导页面

---

**最后更新**: 2026-05-03  
**状态**: ✅ 可用  
**测试**: 通过
