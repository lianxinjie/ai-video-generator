# -*- coding: utf-8 -*-
"""
智能场景整理器 - AI 交互与用户交互结合，智能更新整理场景

核心功能：
1. AI 场景分析增强（场景边界检测、连贯性评估）
2. 用户交互确认（可修改场景分析结果）
3. 场景智能优化（合并相似场景、优化转场）
4. 场景转换建议（推荐最佳转场效果）
5. 智能场景检测（基于关键词判定是否新增场景）
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# 导入智能场景检测器
try:
    from scene_detector import SceneDetector
    SCENE_DETECTOR_AVAILABLE = True
except ImportError:
    SCENE_DETECTOR_AVAILABLE = False


class SceneRefiner:
    """智能场景整理器"""
    
    # 场景连贯性关键词
    CONTINUITY_KEYWORDS = {
        'same_location': ['继续', '仍然', '还在', '同样', '依旧', 'continue', 'still', 'same'],
        'time_change': ['然后', '接着', '随后', '之后', 'then', 'next', 'after'],
        'location_change': ['切换到', '转到', '来到', '场景变为', 'switch', 'move to'],
        'action_change': ['开始', '变成', '转为', 'begin', 'turn', 'become'],
        'contrast': ['但是', '然而', '却', '相反', 'but', 'however', 'instead']
    }
    
    # 场景边界标志词
    SCENE_BOUNDARY_MARKERS = [
        # 时间转换
        '从...到...', '从白天到黄昏', '从夜晚到黎明',
        'day to night', 'night to dawn', 'morning to evening',
        # 空间转换
        '镜头转向', '视角切换', '切换到', '转到',
        'camera pans', 'switch to', 'move to',
        # 场景结束
        '最后', '最终', '结束时', 'fade out', 'end with'
    ]
    
    # 推荐转场效果
    TRANSITION_SUGGESTIONS = {
        'time_lapse': '渐变溶解 (Dissolve)',
        'zoom_sequence': '推进转场 (Zoom In)',
        'pan_sequence': '平移转场 (Pan)',
        'weather_change': '交叉溶解 (Cross Dissolve)',
        'iterative_img2img': '直接切换 (Cut)',
        'custom': '渐变溶解 (Dissolve)'
    }
    
    def __init__(self, verbose: bool = True, enable_scene_detection: bool = True):
        """
        初始化场景整理器
        
        Args:
            verbose: 是否输出详细信息
            enable_scene_detection: 启用智能场景检测（基于关键词判定新增场景）
        """
        self.verbose = verbose
        self.analysis_cache: Dict = {}
        self.enable_scene_detection = enable_scene_detection
        
        # 初始化场景检测器
        self.scene_detector = None
        if enable_scene_detection and SCENE_DETECTOR_AVAILABLE:
            try:
                self.scene_detector = SceneDetector(verbose=verbose)
                self._log("已启用智能场景检测器（关键词分析 + 场景判定）", "INFO")
            except Exception as e:
                self._log(f"初始化场景检优化完成", "INFO")
            return optimized_segments, scene_report
        else:
            self._log("用户取消优化，保持原始场景", "INFO")
            return segments, scene_report
    
    def _display_scene_report(self, report: Dict):
        """显示场景分析报告"""
        print(f"【场景统计】")
        print(f"  总分段数：{report['total_segments']}")
        
        print(f"\n【场景类型分布】")
        for scene_type, count in report['scene_type_distribution'].items():
            percentage = count / report['total_segments'] * 100
            print(f"  {scene_type}: {count} 段 ({percentage:.0f}%)")
        
        print(f"\n【艺术风格分布】")
        for style, count in report['style_distribution'].items():
            percentage = count / report['total_segments'] * 100
            print(f"  {style}: {count} 段 ({percentage:.0f}%)")
        
        if report['transition_suggestions']:
            print(f"\n【转场建议】")
            for trans in report['transition_suggestions'][:5]:
                print(f"  段 {trans['from_segment']+1} → 段 {trans['to_segment']+1}: {trans['suggested_transition']}")
