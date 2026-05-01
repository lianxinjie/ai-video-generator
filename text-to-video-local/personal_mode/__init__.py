#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人电脑模式 - 视频分段生成 + 合并方案
支持低显存 GPU(1-8GB) 的视频生成，通过时间换性能
"""

__version__ = "1.0.0"
__author__ = "MonkeyCode-AI"

from .monitor import ResourceMonitor, ResourceStatus
from .checkpoint import CheckpointManager, CheckpointData
from .task_manager import TaskScheduler
from .chunk_generator import ChunkGenerator
from .ai_offload import AIOffloadEngine
from .merger import VideoMerger

__all__ = [
    "ResourceMonitor",
    "ResourceStatus",
    "CheckpointManager",
    "CheckpointData",
    "TaskScheduler",
    "ChunkGenerator",
    "AIOffloadEngine",
    "VideoMerger",
]
