# Web 端一键安装功能使用指南

> **版本**: v3.0 | **更新日期**: 2026-05-03

---

## 一、功能概述

Web 端现已集成完整的硬件扫描与一键安装功能：

1. 🔍 **硬件检测** - 自动识别 CPU/GPU/内存/磁盘配置
2. 🎯 **智能推荐** - 根据硬件推荐最优配置方案
3. 📦 **生成安装包** - 生成个性化的安装脚本和依赖
4. ⬇️ **下载离线包** - 打包下载所有安装文件
5. 🔧 **一键安装** - 在 Web 界面直接执行安装

---

## 二、API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/scanner/report` | GET | 获取硬件摘要和推荐 |
| `/api/scanner/generate-package` | POST | 生成个性化安装包 |
| `/api/scanner/download-package` | GET | 下载离线包 (ZIP) |
| `/api/scanner/install` | POST | 执行一键安装 |
| `/api/scanner/install-status/<id>` | GET | 查询安装进度 |

---

## 三、使用流程

### 3.1 硬件检测

```
访问 Web → 点击"开始硬件检测" → 查看结果
```

### 3.2 生成安装包

```
点击"生成一键安装包" → 等待生成完成 → 查看文件列表
```

### 3.3 下载安装包

```
点击"下载离线包" → 保存 ZIP 文件 → 解压使用
```

### 3.4 执行安装

```
点击"执行安装" → 查看实时日志 → 等待完成提示
```

---

## 四、安装包内容

```
offline-package-{task_id}/
├── requirements-optimized.txt   # 个性化依赖
├── download_models.py           # 模型下载脚本
├── install.sh                   # 一键安装脚本
└── INSTALL_GUIDE.txt            # 安装指南
```

---

## 五、推荐模式

| 模式 | 适用配置 |
|------|---------|
| `hybrid_high_end` | 高端 GPU + 中端/高端 CPU |
| `hybrid_mid_range` | 中端 GPU + 中端 CPU |
| `hybrid_low_end` | 低端 GPU + 低端 CPU |
| `gpu_mid_cpu_low` | 中端 GPU + 低端 CPU |
| `gpu_low_cpu_mid` | 低端 GPU + 中端 CPU |
| `gpu_high_cpu_low` | 高端 GPU + 低端 CPU |
| `cpu_capable` | 无 GPU，16GB+内存 |

---

**状态**: ✅ 已完成并部署
