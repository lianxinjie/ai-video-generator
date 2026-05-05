# 代码质量保证指南

## 问题教训

2024-05-05 出现的问题：
- ❌ `api_check_ffmpeg()` 缺少 `import platform` 和 `from pathlib import Path`
- ❌ `api_download_ffmpeg()` 缺少 `import time` 和 `import stat`

这些低本应该在代码审查时就被发现，但却被提交并导致用户遇到 500 错误。

## 防错机制

### 1. 自动检查工具

```bash
# 提交前运行
./pre_commit_check.sh

# 或手动运行
python check_code_quality.py
python -m py_compile web/app.py
```

### 2. 检查清单

生成或修改 Python 代码后，**必须**检查：

- [ ] 所有使用的模块都已导入
- [ ] `ast.parse()` 语法检查通过
- [ ] 没有在函数外部使用未导入的模块
- [ ] 所有网络请求有超时设置
- [ ] 所有外部调用有异常处理

### 3. 常见易错点

| 模块 | 常见使用 | 容易忘记导入的场景 |
|------|----------|------------------|
| `time` | `time.time()`, `time.sleep()` | 计算耗时、超时判断 |
| `stat` | `stat.S_IEXEC`, `stat.S_IXUSR` | 设置文件权限 |
| `platform` | `platform.system()`, `platform.machine()` | 系统检测 |
| `pathlib.Path` | `Path('./dir')` | 路径操作 |

### 4. 代码生成功作流

```
1. 生成代码
    ↓
2. 立即运行 python -m py_compile 检查语法
    ↓
3. 运行 python check_code_quality.py 检查导入
    ↓
4. 手动审查关键函数的导入语句
    ↓
5. 测试关键功能（如果可能）
    ↓
6. 提交
```

### 5. 审查重点

审查代码时特别关注：

1. **函数级导入**：每个函数的导入语句是否完整
2. **模块使用**：检查所有 `xxx.yyy()` 调用，确认 `xxx` 已导入
3. **跨平台代码**：`platform.system()` 判断分支是否都测试过
4. **异常处理**：是否所有可能的异常都被捕获

## 工具使用

### check_code_quality.py

```bash
# 检查所有 Python 文件
python check_code_quality.py

# 检查特定文件
python check_code_quality.py web/app.py download_models.py

# 在 CI/CD 中使用
if ! python check_code_quality.py; then
    echo "代码质量检查失败"
    exit 1
fi
```

### pre_commit_check.sh

```bash
# 提交前运行
./pre_commit_check.sh

# 或集成到 git hook
ln -s ../../pre_commit_check.sh .git/hooks/pre-commit
```

## 责任

- **生成代码时**：模型必须确保导入语句完整
- **提交前**：运行自动检查工具
- **发现问题**：立即修复并更新检查清单

---

**记住**：缺少导入这种低级错误不应该发生，更不应该连续发生！
