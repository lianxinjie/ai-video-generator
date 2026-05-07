# 项目清理规则

## 📋 清理目标

确保项目始终保持干净整洁，无任何无用代码和文件。

---

## 🧹 清理范围

### 1. Python 缓存 ✅

**清理内容**:
- `__pycache__/` 目录
- `*.pyc` 文件 (Python 字节码)
- `*.pyo` 文件 (优化字节码)
- `*.pyd` 文件 (Windows DLL)

**原因**: 自动生成的缓存，可重新编译

**命令**:
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

---

### 2. 临时文件 ✅

**清理内容**:
- `*.tmp` 临时文件
- `*.temp` 临时文件
- `*.log` 日志文件

**原因**: 运行中产生的临时数据

**命令**:
```bash
find . -name "*.tmp" -delete
find . -name "*.log" -delete
```

---

### 3. 备份文件 ✅

**清理内容**:
- `*.bak` 备份文件
- `*.backup` 备份文件
- `*~` 编辑器临时文件

**原因**: 手动备份或编辑器自动生成

**命令**:
```bash
find . -name "*.bak" -delete
find . -name "*~" -delete
```

---

### 4. IDE 配置 ✅

**清理内容**:
- `.idea/` (JetBrains IDE)
- `.vscode/` (VS Code)
- `*.swp` (Vim 交换文件)
- `*.swo` (Vim 交换文件)

**原因**: 个人 IDE 配置，不应提交

**命令**:
```bash
rm -rf .idea/
rm -rf .vscode/
```

---

### 5. 测试文件 ✅

**清理内容**:
- `test_*.py` (顶层临时测试)
- `pytest_cache/` (Pytest 缓存)
- `.pytest_cache/` (Pytest 缓存)
- `.coverage` (测试覆盖)
- `htmlcov/` (覆盖报告)

**保留**:
- ✅ 正式测试文件 (在 tests/ 目录内)

**命令**:
```bash
find . -maxdepth 1 -name "test_*.py" -delete
rm -rf pytest_cache/
```

---

### 6. 构建产物 ✅

**清理内容**:
- `dist/` (分发包)
- `build/` (构建目录)
- `*.egg-info/` (包信息)

**原因**: 构建时自动生成

**命令**:
```bash
rm -rf dist/
rm -rf build/
```

---

### 7. 文档缓存 ✅

**清理内容**:
- `COMMIT_MSG.txt` (临时提交消息)
- `*.md.bak` (文档备份)
- `.DS_Store` (macOS 元数据)
- `Thumbs.db` (Windows 缩略图)

**命令**:
```bash
rm -f COMMIT_MSG.txt
rm -f .DS_Store
```

---

### 8. 空目录 ✅

**清理内容**:
- 所有空目录（除了 `.git/`）

**命令**:
```bash
find . -type d -empty -not -path "./.git*" -delete
```

---

## 🚀 使用方法

### 方式 1: 运行清理脚本

```bash
cd text-to-video-local
./clean.sh
```

### 方式 2: 手动清理

```bash
# Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +

# 临时文件
find . -name "*.tmp" -delete

# 备份文件
find . -name "*.bak" -delete

# 空目录
find . -type d -empty -delete
```

### 方式 3: 提交前清理

```bash
# 提交前自动清理
git add .
./clean.sh
git status
```

---

## 📅 清理频率

| 场景 | 频率 | 说明 |
|------|------|------|
| 开发中 | 随时 | 发现无用文件立即删除 |
| 提交前 | 必须 | 每次 git commit 前清理 |
| 每天 | 建议 | 下班前运行 `./clean.sh` |
| 每周 | 强制 | 周末全面清理 |

---

## ✅ 验证清理结果

### 检查命令

```bash
# 检查是否有残留
find . -name "__pycache__" -o -name "*.pyc" -o -name "*.tmp" -o -name "*.bak"

# 应返回空结果
```

### 清理彻底标准

- ✅ 无 `__pycache__/` 目录
- ✅ 无 `*.pyc` 文件
- ✅ 无 `*.tmp` 文件
- ✅ 无 `*.bak` 文件
- ✅ 无空目录
- ✅ 无 IDE 配置
- ✅ 无测试缓存

---

## 📊 清理效果

### 清理前

```bash
$ find . -type f | wc -l
356  # 包含大量缓存和临时文件
```

### 清理后

```bash
$ find . -type f | wc -l
79  # 只剩核心文件
```

**清理率**: ~78%

---

## 🎯 保留文件

以下文件**应该保留**：

### 核心代码
- ✅ `web/app.py`
- ✅ `download_models.py`
- ✅ `download_ffmpeg.py`
- ✅ `scanner.py`
- ✅ `generation.py`

### 文档
- ✅ `README.md`
- ✅ `USAGE_GUIDE.md`
- ✅ `CLEANING_RULES.md`
- ✅ `FFMPEG_INSTALL_GUIDE.md`
- ✅ `MODEL_MANAGEMENT_FEATURE.md`
- ✅ `MODEL_SIZE_EXPLANATION.md`
- ✅ `FFMPEG_STRICT_VERIFICATION.md`

### 配置
- ✅ `.gitignore`
- ✅ `requirements.txt`

### 模板
- ✅ `web/templates/*.html`

---

## ⚠️ 注意事项

### 1. 不要删除的文件

- ❌ `*.py` - Python 源代码
- ❌ `*.md` - 项目文档
- ❌ `*.html` - Web 模板
- ❌ `*.txt` - 重要文本文件

### 2. 特殊情况

某些 `.py` 文件可能是临时的：
- `test_temp.py`
- `debug_script.py`
- `backup_code.py`

**处理**: 用完立即删除或移动到合适位置

### 3. 模型和 FFmpeg

`models/` 和 `ffmpeg/` 目录：
- ✅ 按 `.gitignore` 忽略
- ✅ 本地保留（用户数据）
- ✅ 不提交到 git

---

## 📋 清理清单

**每次提交前检查**:

- [ ] 已运行 `./clean.sh`
- [ ] 无 `__pycache__/` 目录
- [ ] 无 `*.pyc` 文件
- [ ] 无 `*.tmp` 文件
- [ ] 无 `*.bak` 文件
- [ ] 无空目录
- [ ] 无 IDE 配置
- [ ] `git status` 干净

---

## 🎉 最佳实践

1. **即时清理** - 用完立即删除临时文件
2. **提交前清理** - 每次 commit 前运行 `./clean.sh`
3. **定期清理** - 每天/每周例行清理
4. **自动化** - 使用清理脚本而非手动删除
5. **验证** - 清理后检查确认

---

**保持项目干净整洁是每个人的责任！**

**清理脚本**: `./clean.sh`  
**清理频率**: 提交前必须，建议每天  
**清理标准**: 无缓存、无临时文件、无备份、无空目录
