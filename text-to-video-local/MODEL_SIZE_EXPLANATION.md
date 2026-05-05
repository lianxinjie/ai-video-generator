# 模型大小说明

## 为什么显示的"下载大小"和"实际占用"不一样？

### 示例

- **下载大小**: 2.5 GB
- **实际占用**: 13 GB (或更多)

这不是错误，而是正常现象。

---

## 原因解析

### 1. 压缩包 vs 解压后

```
下载：  compressed_model.safetensors (2.5GB 压缩)
                ↓ 解压
占用：  model_weights/
        ├── config.json
        ├── model.safetensors (已展开，4.2GB)
        ├── tokenizer.json (0.3GB)
        ├── scheduler/
        ├── feature_extractor/
        └── ...
```

**压缩比**: 通常是 1:2 到 1:5

---

### 2. 缓存结构占用空间

#### HuggingFace 缓存

```
models/
└── models--guoyww--animatediff-motion-adapter-v1-5-2/
    ├── blobs/           # 实际文件 (多个版本)
    │   ├── abc123... (2.5GB)
    │   └── def456... (2.5GB)  # 不同版本的同一模型
    ├── refs/            # 引用
    └── snapshots/       # 快照链接
```

**问题**:
- 多次下载会保留历史版本
- `blobs/` 目录可能包含多个版本
- 不会自动清理旧版本

---

#### ModelScope 缓存

```
models/
└── text-to-video-synthesis/
    ├── damo/
    │   └── text-to-video-synthesis/
    │       ├── config.json
    │       ├── model.pt (2.8GB)
    │       ├── pipeline.py
    │       └── ...
    └── .cache/          # 临时缓存 (可能很大)
```

**问题**:
- `.cache/` 目录可能包含临时文件
- 下载过程中的临时文件未清理
- 日志和元数据

---

### 3. 多个模型文件

"基础模型" 2.5GB 可能包含：

```
text-to-video-synthesis/
├── main_model.pt        (2.5GB) ← 主要模型
├── reference_model.pt   (1.2GB) ← 参考模型
├── vae_model.pt        (0.8GB) ← VAE 解码器
└── additional/
    └── extra.pt        (0.5GB) ← 额外组件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总计：5.0GB+
```

---

### 4. Git LFS 存储

如果模型使用 Git LFS：

```
.git/lfs/
├── objects/
│   ├── 12/34/1234567... (2.5GB)
│   └── 56/78/5678901... (2.5GB)  # 历史版本
└── tmp/
    └── temp_file       (1.0GB)  # 未清理的临时文件
```

---

### 5. Python 依赖和缓存

```
models/
├── modelscope/
│   └── ...
├── __pycache__/         # Python 字节码缓存
├── .cache/
│   └── pip/            # pip 缓存
└── downloads/
    └── temp_*.tmp      # 未完成的下载
```

---

## 实际案例

### 用户报告：13GB vs 2.5GB

**可能的原因组合**:

| 项目 | 大小 |
|------|------|
| 主模型文件（解压后） | 4.2 GB |
| 辅助模型（VAE 等） | 2.5 GB |
| HuggingFace 缓存（2 个版本） | 1.8 GB |
| ModelScope `.cache/` | 1.2 GB |
| 临时文件未清理 | 1.0 GB |
| Python 缓存和其他 | 0.5 GB |
| Git LFS 历史版本 | 1.8 GB |
| **总计** | **13.0 GB** |

---

## 如何清理

### 1. 清理临时文件

```bash
# 进入模型目录
cd models/modelscope

# 清理缓存
rm -rf .cache/
rm -rf __pycache__/

# 清理临时文件
find . -name "*.tmp" -delete
find . -name "*.pyc" -delete
```

### 2. 清理 HuggingFace 缓存

```bash
# 进入缓存目录
cd models/models--*

# 查看快照
ls -lh snapshots/

# 只保留最新的快照
# (先备份！)
```

**或使用官方工具**:

```bash
# 安装 huggingface_hub
pip install huggingface_hub

# 扫描缓存
huggingface-cli scan-cache

# 删除缓存
huggingface-cli delete-cache --all
```

### 3. 清理 Git LFS

```bash
# 查看 LFS 文件
git lfs ls-files --all

# 清理未使用的 LFS 对象
git lfs prune --verbose
```

### 4. 完全重新下载

```bash
# 删除所有模型
rm -rf models/*

# 重新下载
python download_models.py -m modelscope
```

---

## 预防建议

### 1. 使用符号链接（推荐）

```bash
# 下载到单独目录
mkdir -p /data/models
python download_models.py -o /data/models -m modelscope

# 创建符号链接
ln -s /data/models/modelscope ./models/modelscope
```

### 2. 定期清理

```bash
# 添加 cron 任务
0 3 * * * cd /workspace && python clean_models.py
```

### 3. 监控磁盘空间

```bash
# 检查模型目录大小
du -sh models/*/

# 找出最大的文件
find models/ -type f -exec du -h {} + | sort -rh | head -10
```

---

## 验证模型完整性

清理后验证模型是否可用：

```bash
# 仅检查不下载
python download_models.py --check-only

# 或
python -c "
from download_models import ModelDownloader
d = ModelDownloader('./models')
print(d.check_existing_models(['modelscope']))
"
```

---

## 总结

✅ **正常现象**: 实际占用 > 下载大小  
✅ **合理范围**: 2.5GB 下载 → 5-8GB 占用  
⚠️ **需要清理**: 2.5GB 下载 → 13GB+ 占用

**建议**:
- 定期清理缓存和临时文件
- 不要多次重复下载同一模型
- 使用符号链接管理大型模型
- 监控磁盘空间使用
