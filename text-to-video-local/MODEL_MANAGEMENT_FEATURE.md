# 模型管理功能更新说明

## 🎯 新增功能

### 1. 模型占用分析仪

**位置**: 设置向导 → 步骤 4：模型管理

**功能**:
- 📊 查看每个已安装模型的详细信息
- 📈 显示下载大小 vs 实际占用
- 📂 分析目录结构和文件分布
- ⚠️ 智能识别异常占用

**示例输出**:
```
总体统计
├─ 已安装模型：2 个
├─ 下载总大小：6.5 GB
├─ 实际占用：15.2 GB
└─ 膨胀比例：2.3x

模型详情
├─ MODELSCOPE
│  ├─ 下载大小：2.5 GB
│  ├─ 实际占用：6.8 GB ⚠️ 占用过大
│  ├─ 膨胀比例：2.7x
│  ├─ 文件数量：156
│  └─ 目录结构:
│     • damo: 5.2 GB (120 文件)
│     • .cache: 1.6 GB (36 文件)
└─ ANIMATEDIFF
   ├─ 下载大小：4.0 GB
   ├─ 实际占用：8.4 GB ✓ 正常
   ├─ 膨胀比例：2.1x
   └─ 文件数量：234
```

---

### 2. 一键清理功能

**三种清理模式**:

#### 🗑️ 清理缓存
- 清理 `.cache/` 目录
- 释放 ModelScope/HuggingFace 缓存
- 安全，不影响模型使用

#### 🗑️ 清理临时文件
- 删除 `*.tmp` 临时文件
- 删除 `*.pyc` Python 缓存
- 删除 `__pycache__/` 目录
- 删除 `*.egg-info` 包信息

#### 🧽 全面清理
- 执行以上所有清理
- 推荐定期使用

**清理结果**:
```
✅ 清理完成：释放 2.35 GB 空间
• 清理缓存：models/modelscope/.cache (1650.2 MB)
• 清理临时文件：models/__pycache__ (125.4 MB)
• 清理临时文件：models/modelscope/.cache/pip (601.8 MB)
```

---

### 3. 模型删除功能

**使用场景**:
- 不再使用某个模型
- 需要释放大量空间
- 损坏需要重新下载

**操作**:
1. 点击模型卡片上的"🗑️ 删除"按钮
2. 确认删除操作
3. 查看释放空间
4. 需要时可重新下载

**安全措施**:
- 删除前二次确认
- 显示将释放的空间
- 删除后自动更新分析

---

## 🔍 详细统计信息

### 总体统计面板

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| 已安装模型 | 当前安装的模型数量 | 1-5 个 |
| 下载总大小 | 所有模型标称下载大小 | - |
| 实际占用 | 磁盘实际使用空间 | 下载大小×1.5-2.5 |
| 膨胀比例 | 实际占用÷下载大小 | 1.5-2.5x |

### 膨胀比例说明

| 比例 | 状态 | 说明 | 建议 |
|------|------|------|------|
| < 2.0x | ✓ 正常 | 健康的缓存状态 | 无需操作 |
| 2.0-3.0x | ⚠️ 偏高 | 有可清理空间 | 建议清理缓存 |
| > 3.0x | ⚠️ 占用过大 | 大量临时文件 | 立即清理 |

### 目录结构分析

显示每个子目录的详细信息:
```
目录结构:
  • damo: 5.2 GB (120 文件) ← 主模型文件
  • .cache: 1.6 GB (36 文件) ← 可清理缓存
  • __pycache__: 0.3 GB (24 文件) ← 可清理
  • downloads: 0.5 GB (12 文件) ← 临时下载
```

---

## 💡 智能建议

系统会根据分析结果提供建议:

### 膨胀比例偏高 (> 2.5x)

```
💡 建议：
您的模型占用空间偏大（3.2x）。建议执行"全面清理"来释放空间。
```

**推荐操作**:
1. 点击"🧽 全面清理"
2. 查看释放空间结果
3. 重新分析确认

### 缓存过多

```
💡 发现 1.6 GB 缓存文件
建议执行"清理缓存"释放空间
```

### 临时文件堆积

```
💡 发现 0.8 GB 临时文件
建议执行"清理临时文件"
```

---

## 📋 使用流程

### 场景 1：新用户首次设置

1. 步骤 1-2：环境检测和依赖安装
2. 步骤 3：下载推荐的 ModelScope 模型 (2.5GB)
3. **步骤 4：模型管理**
   - 查看模型占用 (可能显示 6GB+)
   - 执行"全面清理"
   - 释放 1-2GB 空间
4. 步骤 5：完成

### 场景 2：定期维护清理

1. 打开设置向导
2. 进入步骤 4：模型管理
3. 点击"📊 分析模型占用空间"
4. 查看膨胀比例
5. 如果 > 2.5x，执行"🧽 全面清理"
6. 确认释放空间

### 场景 3：删除不需要的模型

1. 进入步骤 4：模型管理
2. 找到要删除的模型卡片
3. 点击"🗑️ 删除"按钮
4. 确认删除
5. 查看释放空间 (如 6.8 GB)
6. 分析结果自动更新

---

## 🔧 技术实现

### 后端 API

#### 1. `/api/models/analyze` (GET)
分析模型目录占用

**返回**:
```json
{
  "success": true,
  "models": [
    {
      "id": "modelscope",
      "installed": true,
      "download_size_gb": 2.5,
      "actual_size_gb": 6.8,
      "ratio": 2.72,
      "file_count": 156,
      "breakdown": {
        "damo": {"size_gb": 5.2, "files": 120},
        ".cache": {"size_gb": 1.6, "files": 36}
      },
      "status": "warning"
    }
  ],
  "summary": {
    "total_models": 1,
    "total_download_gb": 2.5,
    "total_actual_gb": 6.8,
    "ratio": 2.72
  }
}
```

#### 2. `/api/models/cleanup` (POST)
清理缓存和临时文件

**参数**:
```json
{"target": "all"}
```

**target 选项**:
- `all` - 全面清理
- `cache` - 仅清理缓存
- `temp` - 仅清理临时文件

**返回**:
```json
{
  "success": true,
  "stats": {
    "cleaned": 3,
    "freed_gb": 2.35,
    "details": [
      "清理缓存：models/modelscope/.cache (1650.2 MB)",
      "清理临时文件： (125.4 MB)",
      "清理临时文件： (601.8 MB)"
    ]
  },
  "message": "清理完成：释放 2.35 GB 空间"
}
```

#### 3. `/api/models/delete` (POST)
删除指定模型

**参数**:
```json
{"model": "modelscope"}
```

**返回**:
```json
{
  "success": true,
  "model": "modelscope",
  "freed_gb": 6.8,
  "message": "模型 modelscope 已删除，释放 6.80 GB"
}
```

---

### 前端组件

#### 模型卡片
```html
<div class="model-card">
  <div class="model-header">
    <strong>MODELSCOPE</strong>
    <span class="status-warning">⚠️ 占用过大</span>
    <button onclick="deleteModel('modelscope')">🗑️ 删除</button>
  </div>
  <div class="model-stats">
    <div>下载大小：<strong>2.5 GB</strong></div>
    <div>实际占用：<strong style="color: #ed8936;">6.8 GB</strong></div>
    <div>膨胀比例：<strong style="color: #f56565;">2.7x</strong></div>
    <div>文件数量：<strong>156</strong></div>
  </div>
  <div class="model-breakdown">
    <strong>目录结构:</strong>
    • damo: 5.2 GB (120 文件)<br>
    • .cache: 1.6 GB (36 文件)
  </div>
</div>
```

#### 清理按钮组
```html
<div class="cleanup-buttons">
  <button onclick="cleanupModels('cache')">🗑️ 清理缓存</button>
  <button onclick="cleanupModels('temp')">🗑️ 清理临时文件</button>
  <button onclick="cleanupModels('all')">🧽 全面清理</button>
</div>
```

---

## ⚠️ 注意事项

### 安全清理

✅ **安全**:
- `.cache/` 目录 - 会自动重建
- `__pycache__/` - Python 字节码缓存
- `*.tmp` - 临时文件
- `*.pyc` - 编译后的 Python 文件

❌ **不要手动删除**:
- 主模型文件（如 `damo/` 目录）
- 配置文件（`config.json` 等）
- 模型权重文件（`*.pt`, `*.bin`, `*.safetensors`）

### 清理后的影响

1. **首次启动稍慢**: 缓存会重建
2. **不影响功能**: 模型仍可正常使用
3. **可重复执行**: 定期清理有益无害

### 建议清理频率

- **轻度使用**: 每月一次
- **频繁使用**: 每周一次
- **开发环境**: 每次大版本更新后

---

## 📊 效果对比

### 清理前
```
已安装模型：2 个
下载总大小：6.5 GB
实际占用：18.3 GB
膨胀比例：2.8x
```

### 执行全面清理后
```
✅ 清理完成：释放 3.2 GB 空间

已安装模型：2 个
下载总大小：6.5 GB
实际占用：15.1 GB
膨胀比例：2.3x ✓ 改善
```

### 删除一个模型后
```
模型 MODELSCOPE 已删除，释放 6.8 GB

已安装模型：1 个
下载总大小：4.0 GB
实际占用：8.4 GB
膨胀比例：2.1x ✓ 优秀
```

---

## 🎯 未来改进

- [ ] 自动定期清理计划
- [ ] 清理历史记录
- [ ] 模型压缩建议
- [ ] 符号链接管理大模型
- [ ] 多模型批量删除
- [ ] 清理预览（先查看再确认）

---

## 📖 相关文档

- [模型大小编解](./MODEL_SIZE_EXPLANATION.md) - 为什么下载大小和实际占用不同
- [清理指南](./MODEL_SIZE_EXPLANATION.md#如何清理) - 手动清理方法
- [设置向导](./web/templates/setup_wizard.html) - 完整设置流程

---

**版本**: v1.2  
**更新日期**: 2026-05-05  
**功能状态**: ✅ 已上线
