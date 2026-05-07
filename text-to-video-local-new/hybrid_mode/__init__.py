#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模式 - 云端 AI 图片 + 本地轻量合成

提供零 GPU 成本的 AI 视频生成方案
"""

from .prompt_generator import PromptTemplateGenerator
from .video_synthesizer import VideoSynthesizer

__version__ = "1.0.0"
__all__ = [
    "PromptTemplateGenerator",
    "VideoSynthesizer"
]
