# 模型下载指南

## 问题说明

ModelScope 模型下载失败，错误：`[WinError 10060] 连接超时`

这是由于网络连接问题，无法访问 ModelScope 服务器。

---

## 🚀 快速解决方案

### 方案 1: 使用云端模式（推荐）

**不需要下载模型**，直接使用 AI 视频生成：

```bash
# 协同模式 - 本地 + 云端 AI 协同
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m collaborative

# 混合模式 - 纯云端生成 (0 显存)
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m hybrid
```

**Web 界面:**
- 选择 "协同模式" 或 "混合模式"
- 点击 "🔍 检测环境"
- 如果有云端 API 配置，可以直接使用

---

### 方案 2: 使用 HuggingFace 镜像

设置镜像环境变量后重新运行。

#### Windows

**PowerShell:**
```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m optimized
```

**CMD:**
```cmd
set HF_ENDPOINT=https://hf-mirror.com
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m optimized
```

#### Linux/Mac
```bash
export HF_ENDPOINT=https://hf-mirror.com
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m optimized
```

#### 永久设置 (推荐)

在用户目录创建 `.bashrc` 或 `.zshrc`:

```bash
# 添加到 ~/.bashrc
echo "export HF_ENDPOINT=https://hf-mirror.com" >> ~/.bashrc
source ~/.bashrc
```

---

### 方案 3: 使用脚本自动下载

运行提供的下载脚本：

```bash
python download_model_manual.py
```

脚本会提供：
1. ModelScope SDK 下载方法
2. HuggingFace 镜像下载方法
3. 网页手动下载指南

---

### 方案 4: 手动下载模型文件

#### 步骤 1: 访问 ModelScope 页面

打开浏览器访问：
https://www.modelscope.cn/models/damo/text-to-video-synthesis/summary

#### 步骤 2: 下载所有文件

点击"文件"标签页，下载所有文件到:

```
./models/modelscope/
```

需要的关键文件：
```
models/modelscope/
├── damo--text-to-video-synthesis/
│   ├── config.json
│   ├── scheduler/
│   │   └── scheduler_config.json
│   ├── tokenizer/
│   │   ├── special_tokens_map.json
│   │   └── tokenizer_config.json
│   ├── unet/
│   │   ├── config.json
│   │   └── diffusion_pytorch_model.safetensors
│   ├── vae/
│   │   ├── config.json
│   │   └── diffusion_pytorch_model.safetensors
│   └── text_encoder/
│       ├── config.json
│       └── model.safetensors
```

#### 步骤 3: 重新运行

文件下载完成后，重新运行超优模式：

```bash
python personal_mode/run.py -p "一只蝴蝶在树林中翩翩起舞" -m optimized
```

---

## 🛠️ 模型下载优化技巧

### 1. 使用 aria2 下载器

ModelScope 支持 aria2 多线程下载：

```bash
pip install aria2

from modelscope import snapshot_download
model_dir = snapshot_download(
    'damo/text-to-video-synthesis',
    cache_dir='./models/modelscope',
    user_agent={'pipeline': 'text-to-video'}
)
```

### 2. 断点续传

如果下载中断，重新运行会自动续传：

```python
from diffusers import DiffusionPipeline
DiffusionPipeline.from_pretrained(
    'damo/text-to-video-synthesis',
    cache_dir='./models/modelscope',
    resume_download=True  # 启用断点续传
)
```

### 3. 国内镜像源

使用清华/中科大镜像加速 Python 包安装：

```bash
# 清华镜像源
pip install modelscope diffusers transformers -i https://pypi.tuna.tsinghua.edu.cn/simple

# 中科大镜像源
pip install modelscope diffusers transformers -i https://pypi.mirrors.ustc.edu.cn/simple
```

---

## 📊 模型信息

| 项目 | 说明 |
|------|------|
| 模型名称 | damo/text-to-video-synthesis |
| 模型来源 | 达摩院 (阿里巴巴) |
| 模型大小 | 约 3-5GB |
| 下载时间 | 5-30 分钟 (取决于网速) |
| 显存需求 | 最低 4GB，推荐 8GB+ |
| 模型路径 | `./models/modelscope/damo--text-to-video-synthesis` |

---

## ❓ FAQ

### Q1: 下载速度只有几 KB/s

**原因:** ModelScope 服务器限速或网络拥堵

**解决方案:**
1. 使用 HuggingFace 镜像（方案 2）
2. 等待网络高峰期后重试（晚上 8-10 点除外）
3. 使用云端模式，不需要本地模型

### Q2: 下载失败提示 403/404

**原因:** 模型路径或权限问题

**解决方案:**
```bash
# 清理下载缓存
rm -rf ./models/modelscope/downloads

# 重新下载
python download_model_manual.py
```

### Q3: 模型下载成功但加载失败

**原因:** 文件损坏或版本不兼容

**解决方案:**
```bash
# 验证模型文件完整性
ls -lh ./models/modelscope/damo--text-to-video-synthesis

# 检查 diffusers 版本
pip show diffusers

# 升级到最新版
pip install -U diffusers transformers
```

### Q4: GPU 显存不足

**错误信息：** `RuntimeError: CUDA out of memory`

**解决方案:**
1. 降低分辨率：`--resolution 512x512` → `--resolution 256x256`
2. 使用云端模式：`-m collaborative`
3. 使用混合模式：`-m hybrid`

---

## 🎯 推荐方案

| 用户类型 | 推荐方案 | 说明 |
|----------|----------|------|
| 国内用户 | ☁️ 云端模式 | 不需要下载，速度快 |
| 有 GPU | 🌐 HuggingFace 镜像 | 下载快，本地生成 |
| 网络好 | 📦 ModelScope 直连 | 官方源，稳定 |
| 开发者 | 📥 手动下载 | 一次性投入，长期使用 |

---

## 📞 获取帮助

如果以上方案都无法解决，请提供以下信息：

1. **错误日志:** 完整的错误输出
2. **网络环境:** 国内/国外，带宽大小
3. **尝试过的方案:** 已试过哪些方法
4. **系统信息:** Windows/Linux/Mac，Python 版本

可以通过以下方式反馈：
- GitHub Issues
- 项目讨论区

---

**最后更新:** 2026-05-05
