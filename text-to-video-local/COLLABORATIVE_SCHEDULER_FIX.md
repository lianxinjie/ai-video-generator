# collaborative_scheduler.py 编码问题修复指南

## 问题概述

文件 `personal_mode/collaborative_scheduler.py` 包含 175 个中文全角字符，导致 Python 无法编译。

## 错误信息

```
SyntaxError: invalid character '（' (U+FF08) (collaborative_scheduler.py, line 92)
```

## 问题字符统计

- `（` U+FF08 全角左括号：44 处
- `）` U+FF09 全角右括号：44 处
- `,` U+FF0C 全角逗号：46 处
- `：` U+FF1A 全角冒号：36 处
- `,` U+3001 中文顿号：5 处

**总计：175 处全角字符**

## 手动修复步骤

### 方法 1：使用 VSCode/IDE 替换

1. 打开文件 `personal_mode/collaborative_scheduler.py`
2. 使用查找替换功能（Ctrl+H）
3. 依次替换：
   - 查找 `（` 替换为 `(`
   - 查找 `）` 替换为 `)`
   - 查找 `,` 替换为 `,`
   - 查找 `：` 替换为 `:`
   - 查找 `,` 替换为 `,`
4. 保存文件
5. 测试编译：`python3 -m py_compile personal_mode/collaborative_scheduler.py`

### 方法 2：使用 sed 命令

```bash
cd text-to-video-local
sed -i 's/(/(/g; s/)/)/g; s/,/,/g; s/:/:/g; s/,/,/g' personal_mode/collaborative_scheduler.py
python3 -m py_compile personal_mode/collaborative_scheduler.py
```

### 方法 3：使用 Python 脚本

```python
with open('personal_mode/collaborative_scheduler.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('(', '(').replace(')', ')')\
                 .replace('，', ',').replace('：', ':')\
                 .replace('、', ',')

with open('personal_mode/collaborative_scheduler.py', 'w', encoding='utf-8') as f:
    f.write(content)
```

## 验证修复

```bash
python3 -m py_compile personal_mode/collaborative_scheduler.py
# 应输出：无错误

curl -X POST http://localhost:5000/api/analyze \
  -F "prompt=测试场景" \
  -F "duration=10"
# 应返回成功响应的 JSON
```

## 当前功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| Web 场景编辑器 | ✅ 完成 | 可正常交互 |
| 场景查看器模块 | ✅ 完成 | 可加载/显示 |
| 场景确认页面 | ✅ 完成 | 可访问 |
| 导出/导入 JSON | ✅ 完成 | 功能正常 |
| API 场景分析 | ⏳ 待修复 | 依赖此文件 |

## 注意事项

- ❗ 不要直接替换所有全角字符，因为 docstring 中的中文应该保留
- ✅ 只替换代码部分（变量名、参数等位置）的全角字符
- ✅ docstring 中的说明文字保持中文即可，标点符号建议统一为半角

## 修复后测试

修复后运行完整测试：

```bash
python3 /tmp/test_scenes_api.py
```

预期输出：所有测试通过

---

*更新时间：2026-05-02*  
*问题发现者：系统测试*
