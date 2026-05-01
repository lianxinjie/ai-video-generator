# 更新日志

## v1.2.0 (2026-05-01) - 个人电脑模式：分段生成 + 断点续传

### 🎯 新增功能

#### 1. 个人电脑模式 (Personal Mode)

**新增目录**: `personal_mode/`

**核心特性**:
- ✅ **分段生成**: 将长视频分成多个短片段依次生成，降低显存占用
- ✅ **资源监控**: 实时监控 GPU/CPU/内存/磁盘，超过阈值自动暂停
- ✅ **断点续传**: 任务状态持久化，支持关机续跑
- ✅ **智能等待**: 资源紧张时自动暂停，恢复后继续执行
- ✅ **视频合并**: 自动合并所有片段，支持过渡效果
- ✅ **AI 卸载**: 可选豆包 API 优化提示词，分担本地计算

**适用场景**:
- 低显存 GPU(1-8GB): GTX 1050/1060/1650/RTX 3050 等
- 系统内存紧张 (8-16GB)
- 需要生成长视频但显存不足
- 希望后台运行，可随时中断和恢复

#### 2. 核心模块

**新增文件**:
- `personal_mode/__init__.py` - 模块初始化
- `personal_mode/monitor.py` - 资源监控模块
- `personal_mode/checkpoint.py` - 检查点管理模块
- `personal_mode/chunk_generator.py` - 视频片段生成器
- `personal_mode/task_manager.py` - 任务调度器
- `personal_mode/ai_offload.py` - AI 计算卸载模块
- `personal_mode/merger.py` - 视频合并模块
- `personal_mode/generate.py` - 命令行工具
- `personal_mode/README.md` - 详细使用文档
- `personal_mode/requirements.txt` - 依赖列表

#### 3. 命令行工具

**命令示例**:

```bash
# 基础使用
python3 personal_mode/generate.py -p "蝴蝶飞舞" -d 5

# 自定义配置
python3 personal_mode/generate.py \
  -p "风景" \
  -d 10 \
  -c 0.5 \
  --resolution 384x384 \
  --gpu-threshold 70 \
  --model modelscope

# 查看状态
python3 personal_mode/generate.py status --project-dir ./projects/butterfly

# 添加过渡效果
python3 personal_mode/generate.py -p "城市夜景" -d 5 --transition
```

### 📈 性能参考

**GTX 1050 2GB 配置**:

| 总时长 | 分段数 | 每段时长 | 预估时间 |
|--------|--------|----------|----------|
| 3 秒 | 6 | 0.5 秒 | 15-20 分钟 |
| 5 秒 | 10 | 0.5 秒 | 25-35 分钟 |
| 10 秒 | 20 | 0.5 秒 | 50-70 分钟 |

### 🔧 技术实现

**资源监控**:
- GPU 显存：torch.cuda + pynvml
- GPU 温度：pynvml
- CPU 使用率：psutil
- 内存使用：psutil
- 磁盘空间：psutil

**断点续传**:
- 任务状态 JSON 持久化
- 检查点自动保存
- 支持任意时刻中断和恢复

**视频合并**:
- FFmpeg 自动检测和调用
- 支持直接合并和过渡效果
- 可选清理片段文件

### 📝 更新内容

- 更新 `README.md` - 添加个人电脑模式说明
- 更新 `.gitignore` - 添加个人模式相关文件

### 🙏 致谢

- 豆包 AI API - 提示词优化支持

---

## v1.1.0 (2026-04-30) - GPU+CPU 协调模式增强

### 🎯 新增功能

#### 1. GPU+CPU 协调模式智能推荐

**新增文件**: `HYBRID_MODE_GUIDE.md`

**功能描述**:
- 根据 CPU 和 GPU 的档次自动选择最优协调模式
- 提供 7 种详细的协调模式配置方案
- 针对每种模式提供具体的优化建议和性能预期

**协调模式列表**:

| 模式 | 适用硬件 | 推荐模型 |
|------|----------|----------|
| `hybrid_high_end` | 高端 GPU + 中/高端 CPU | CogVideoX-5B |
| `hybrid_mid_range` | 中端 GPU + 中/高端 CPU | ModelScope |
| `hybrid_low_end` | 低端 GPU + 低端 CPU | ModelScope |
| `gpu_mid_cpu_low` | 中端 GPU + 低端 CPU | ModelScope |
| `gpu_low_cpu_mid` | 低端 GPU + 中端 CPU | ModelScope |
| `gpu_high_cpu_low` | 高端 GPU + 低端 CPU | CogVideoX-5B |
| `gpu_very_low` | 显存<6GB | ModelScope |

#### 2. 硬件档次自动分类

**文件更新**: `scanner.py`

**新增功能**:
- `_classify_cpu_tier()` - 自动判断 CPU 档次（高端/中端/低端）
- `_classify_gpu_tier()` - 自动判断 GPU 档次（高端/中端/低端）
- `_get_tier_description()` - 提供档次描述信息

**分类标准**:

**CPU 档次**:
- **高端**: 8 核 + (i7/i9/Ryzen 7/9)
- **中端**: 6 核 (i5/Ryzen 5)
- **低端**: 4 核及以下 (i3/赛扬)

**GPU 档次**:
- **高端**: 显存≥12GB (RTX 3080/3090/4080/4090)
- **中端**: 显存 6-12GB (RTX 2060/3060/3070)
- **低端**: 显存<6GB (GTX 1060/1650/RTX 3050)

### 📝 更新内容

#### scanner.py 更新

**新增方法**:
```python
def _classify_cpu_tier(self) -> str:
    """判断 CPU 档次"""
    
def _classify_gpu_tier(self) -> str:
    """判断 GPU 档次"""
    
def _get_tier_description(self, tier: str) -> str:
    """获取档次描述"""
```

**优化逻辑**:
- 重写 `analyze()` 方法，新增 7 种协调模式
- 针对每种模式提供详细的优化建议
- 根据 CPU+GPU组合智能选择运行策略

**输出增强**:
```
【硬件档次评估】
  CPU 等级：MID (中端 - 平衡性能与质量)
  GPU 等级：HIGH (高端 - 适合高质量视频生成)
```

#### README_FEATURES.md 更新

**新增章节**: `GPU+CPU 协调模式 (新增!)`

- 协调模式速查表
- 硬件档次标准
- 使用示例

---

## v1.0.0 (2026-04-30) - 初始版本

### 核心功能

- ✅ 系统扫描器 (`scanner.py`)
- ✅ 智能模型下载器 (`download_models.py`)
- ✅ 智能启动器 (`run.py`)
- ✅ 一键安装脚本 (`install.sh`)
- ✅ 模型量化工具 (`model_quantize.py`)
- ✅ 视频生成主程序 (`generation.py`)

### 文档系统

- ✅ README.md - 项目主文档
- ✅ QUICKSTART.md - 快速开始指南
- ✅ README_INSTALL.md - 安装指南
- ✅ README_FEATURES.md - 功能总览
- ✅ PROJECT_OVERVIEW.md - 项目总览
- ✅ CHEATSHEET.md - 命令速查表
- ✅ DEPLOYMENT_SUMMARY.md - 部署总结
- ✅ HYBRID_MODE_GUIDE.md - 协调模式指南

### Docker 支持

- ✅ Dockerfile (GPU/CPU双模式)
- ✅ docker-compose.yml

---

## 版本特性对比

| 版本 | 发布日期 | 主要特性 |
|------|----------|----------|
| v1.0.0 | 2026-04-30 | 初始版本，基础功能 |
| v1.1.0 | 2026-04-30 | GPU+CPU 协调模式增强 |

---

## 升级指南

### 从 v1.0.0 升级到 v1.1.0

```bash
# 1. 更新 scanner.py
git pull origin main  # 或手动替换文件

# 2. 查看新功能
python3 scanner.py

# 3. 阅读新文档
cat HYBRID_MODE_GUIDE.md
```

**变更说明**:
- 修改了扫描推荐的输出格式
- 新增了硬件档次显示
- 优化了推荐算法

**向后兼容**: 完全兼容 v1.0.0 的所有功能

---

## 贡献者

- AI Coding Assistant

---

## 许可证

MIT License
