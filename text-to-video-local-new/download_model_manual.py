#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动下载 ModelScope 模型脚本

用于解决网络问题导致的模型下载失败

使用方法:
    python download_model_manual.py

如果仍然失败，请手动下载:
1. 访问 https://www.modelscope.cn/models/damo/text-to-video-synthesis/summary
2. 下载所有文件到 ./models/modelscope 目录
"""

import os
import sys
from pathlib import Path

# 创建模型目录
models_dir = Path('./models/modelscope')
models_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("ModelScope 模型手动下载工具")
print("=" * 60)

print("\n模型信息:")
print("  模型名称：damo/text-to-video-synthesis")
print("  模型大小：约 3-5GB")
print("  下载目录:", models_dir.absolute())

print("\n方法 1: 使用 ModelScope SDK (推荐)")
print("-" * 60)
print("1. 安装 ModelScope:")
print("   pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple")
print()
print("2. 运行下载命令:")
print("   python -c \"from modelscope import snapshot_download; snapshot_download('damo/text-to-video-synthesis', cache_dir='./models/modelscope')\"")
print()

print("方法 2: 使用 HuggingFace 镜像")
print("-" * 60)
print("设置镜像环境变量:")
print("  Windows PowerShell:")
print("    $env:HF_ENDPOINT='https://hf-mirror.com'")
print()
print("  Linux/Mac:")
print("    export HF_ENDPOINT='https://hf-mirror.com'")
print()
print("然后使用 diffusers 下载:")
print("  from diffusers import DiffusionPipeline")
print("  DiffusionPipeline.from_pretrained('damo/text-to-video-synthesis', cache_dir='./models/modelscope')")
print()

print("方法 3: 网页手动下载")
print("-" * 60)
print("1. 访问：https://www.modelscope.cn/models/damo/text-to-video-synthesis/summary")
print("2. 点击 '文件' 标签页")
print("3. 下载所有文件到:", models_dir.absolute())
print()
print("需要的文件:")
print("  - config.json")
print("  - *.bin 或 *.safetensors (模型权重)")
print("  - scheduler/scheduler_config.json")
print("  - tokenizer/*")
print("  - 等等...")
print()

print("方法 4: 使用云端模式 (无需下载)")
print("-" * 60)
print("如果本地模型下载太慢，可以使用云端生成模式:")
print("  python personal_mode/run.py -p '你的提示词' -m collaborative")
print()
print("或者在 Web 界面选择:")
print("  - 协同模式：本地 + 云端 AI 协同")
print("  - 混合模式：纯云端生成 (0 显存)")
print()

print("=" * 60)
print("提示：国内用户建议使用清华/中科大镜像源加速 pip 和模型下载")
print("=" * 60)
