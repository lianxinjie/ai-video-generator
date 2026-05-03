# -*- coding: utf-8 -*-
"""
智能场景整理器 - AI 交互与用户交互结合，智能更新整理场景

核心功能：
1. AI 场景分析增强（场景边界检测、连贯性评估）
2. 用户交互确认（可修改场景分析结果）
3. 场景智能优化（合并相似场景、优化转场）
4. 场景转换建议（推荐最佳转场效果）
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
                self._log(f"初始化场景检测器失败：{e}", "WARNING")
        
    def _log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def analyze_scene_boundaries(self, full_prompt: str) -> List[Dict]:
        """
        分析提示词中的场景边界
        
        Args:
            full_prompt: 完整提示词
            
        Returns:
            场景边界列表，包含位置和类型
        """
        boundaries = []
        prompt_lower = full_prompt.lower()
        
        # 检测场景边界标志词
        for marker in self.SCENE_BOUNDARY_MARKERS:
            marker_lower = marker.lower()
            if '...' in marker_lower:
                # 处理模式匹配（如"从...到..."）
                pattern = marker_lower.replace('...', '(.*?)')
                matches = re.finditer(pattern, prompt_lower)
                for match in matches:
                    boundaries.append({
                        'position': match.start(),
                        'type': 'pattern_match',
                        'marker': marker,
                        'content': match.group(0)
                    })
            else:
                # 直接匹配
                pos = prompt_lower.find(marker_lower)
                if pos != -1:
                    boundaries.append({
                        'position': pos,
                        'type': 'keyword_match',
                        'marker': marker,
                        'content': full_prompt[pos:pos+len(marker)]
                    })
        
        # 按位置排序
        boundaries.sort(key=lambda x: x['position'])
        
        # 移除重复（位置接近的）
        unique_boundaries = []
        last_pos = -50
        for boundary in boundaries:
            if boundary['position'] - last_pos >= 20:  # 至少相隔 20 个字符
                unique_boundaries.append(boundary)
                last_pos = boundary['position']
        
        self._log(f"检测到 {len(unique_boundaries)} 个场景边界", "INFO")
        
        return unique_boundaries
    
    def evaluate_continuity(self, segments: List[Dict]) -> List[Dict]:
        """
        评估场景之间的连贯性
        
        Args:
            segments: 分段列表
            
        Returns:
            连贯性评估报告
        """
        continuity_reports = []
        
        for i in range(len(segments) - 1):
            curr_segment = segments[i]
            next_segment = segments[i + 1]
            
            curr_prompt = curr_segment.get('prompt', '').lower()
            next_prompt = next_segment.get('prompt', '').lower()
            
            # 检查连贯性类型
            continuity_type = 'neutral'
            confidence = 0.5
            keywords_found = []
            
            for cont_type, keywords in self.CONTINUITY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in next_prompt:
                        continuity_type = cont_type
                        confidence = 0.8
                        keywords_found.append(keyword)
                        break
            
            # 检查场景元素重复（表示连续性）
            curr_words = set(curr_prompt.split())
            next_words = set(next_prompt.split())
            common_words = curr_words & next_words
            
            if len(common_words) >= 3:
                continuity_type = 'same_location'
                confidence = 0.9
                keywords_found.extend(list(common_words)[:3])
            
            continuity_reports.append({
                'from_segment': i,
                'to_segment': i + 1,
                'continuity_type': continuity_type,
                'confidence': confidence,
                'keywords_found': keywords_found,
                'transition_suggestion': self._suggest_transition(
                    curr_segment.get('scene_type', 'custom'),
                    continuity_type
                )
            })
        
        self._log(f"完成 {len(continuity_reports)} 个场景连贯性评估", "INFO")
        
        return continuity_reports
    
    def _suggest_transition(self, scene_type: str, continuity_type: str) -> str:
        """
        根据场景类型和连贯性推荐转场效果
        
        Args:
            scene_type: 场景类型
            continuity_type: 连贯性类型
            
        Returns:
            推荐的转场效果
        """
        # 基础转场基于场景类型
        base_transition = self.TRANSITION_SUGGESTIONS.get(scene_type, '渐变溶解 (Dissolve)')
        
        # 根据连贯性调整
        if continuity_type == 'same_location':
            return '直接切换 (Cut)'  # 同一场景，直接切换
        elif continuity_type == 'time_change':
            return '渐变溶解 (Dissolve)'  # 时间变化，渐变
        elif continuity_type == 'location_change':
            return '平移转场 (Pan)'  # 位置变化，平移
        elif continuity_type == 'contrast':
            return '交叉溶解 (Cross Dissolve)'  # 对比，交叉溶解
        
        return base_transition
    
    def merge_similar_scenes(self, segments: List[Dict], 
                             similarity_threshold: float = 0.7) -> List[Dict]:
        """
        合并相似场景
        
        Args:
            segments: 分段列表
            similarity_threshold: 相似度阈值（0-1，越高越严格）
            
        Returns:
            合并后的分段列表
        """
        if len(segments) <= 1:
            return segments
        
        merged = []
        current_group = [segments[0]]
        
        for i in range(1, len(segments)):
            prev_segment = current_group[-1]
            curr_segment = segments[i]
            
            # 计算相似度
            similarity = self._calculate_scene_similarity(prev_segment, curr_segment)
            
            if similarity >= similarity_threshold:
                # 相似度高，合并到当前组
                current_group.append(curr_segment)
                self._log(f"段 {i-1} 和段 {i} 相似度高 ({similarity:.2f})，建议合并", "INFO")
            else:
                # 相似度低，保存当前组，开始新组
                merged.append(self._merge_segment_group(current_group))
                current_group = [curr_segment]
        
        # 添加最后一组
        if current_group:
            merged.append(self._merge_segment_group(current_group))
        
        if len(merged) < len(segments):
            self._log(f"场景合并：{len(segments)} 段 -> {len(merged)} 段", "INFO")
        
        return merged
    
    def _calculate_scene_similarity(self, seg1: Dict, seg2: Dict) -> float:
        """
        计算两个场景的相似度
        
        Args:
            seg1: 分段 1
            seg2: 分段 2
            
        Returns:
            相似度分数（0-1）
        """
        prompt1 = seg1.get('prompt', '').lower()
        prompt2 = seg2.get('prompt', '').lower()
        
        # 1. 词汇相似度（Jaccard 相似系数）
        words1 = set(prompt1.split())
        words2 = set(prompt2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        lexical_similarity = len(intersection) / len(union)
        
        # 2. 场景类型相似度
        type1 = seg1.get('scene_type', 'custom')
        type2 = seg2.get('scene_type', 'custom')
        type_similarity = 1.0 if type1 == type2 else 0.3
        
        # 3. 风格相似度
        style1 = seg1.get('style', 'unknown')
        style2 = seg2.get('style', 'unknown')
        style_similarity = 1.0 if style1 == style2 else 0.5
        
        # 加权平均
        total_similarity = (
            lexical_similarity * 0.5 +
            type_similarity * 0.3 +
            style_similarity * 0.2
        )
        
        return total_similarity
    
    def _merge_segment_group(self, group: List[Dict]) -> Dict:
        """
        合并一组相似场景
        
        Args:
            group: 场景组
            
        Returns:
            合并后的分段
        """
        if len(group) == 1:
            return group[0].copy()
        
        # 合并提示词
        prompts = [seg.get('prompt', '') for seg in group]
        merged_prompt = ', '.join(prompts)
        
        # 取第一个场景的类型和风格
        base_segment = group[0].copy()
        base_segment['prompt'] = merged_prompt
        base_segment['merged_from'] = list(range(
            group[0].get('segment_index', 0),
            group[0].get('segment_index', 0) + len(group)
        ))
        base_segment['merge_reason'] = '相似场景自动合并'
        
        return base_segment
    
    def generate_scene_report(self, segments: List[Dict], 
                              continuity_reports: List[Dict]) -> Dict:
        """
        生成场景分析报告
        
        Args:
            segments: 分段列表
            continuity_reports: 连贯性报告
            
        Returns:
            完整的场景分析报告
        """
        # 统计场景类型
        scene_types = {}
        for seg in segments:
            scene_type = seg.get('scene_type', 'custom')
            scene_types[scene_type] = scene_types.get(scene_type, 0) + 1
        
        # 统计艺术风格
        styles = {}
        for seg in segments:
            style = seg.get('style', 'unknown')
            styles[style] = styles.get(style, 0) + 1
        
        # 生成转场建议
        transitions = []
        for cont_report in continuity_reports:
            transitions.append({
                'from_segment': cont_report['from_segment'],
                'to_segment': cont_report['to_segment'],
                'suggested_transition': cont_report['transition_suggestion']
            })
        
        report = {
            'total_segments': len(segments),
            'scene_type_distribution': scene_types,
            'style_distribution': styles,
            'continuity_analysis': continuity_reports,
            'transition_suggestions': transitions,
            'merge_suggestions': self._generate_merge_suggestions(segments),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_merge_suggestions(self, segments: List[Dict]) -> List[Dict]:
        """
        生成合并建议
        
        Args:
            segments: 分段列表
            
        Returns:
            合并建议列表
        """
        suggestions = []
        
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]
            
            similarity = self._calculate_scene_similarity(seg1, seg2)
            
            if similarity >= 0.6:  # 相似度较高，建议手动确认
                suggestions.append({
                    'segments': [i, i + 1],
                    'similarity': similarity,
                    'confidence': 'high' if similarity >= 0.8 else 'medium',
                    'reason': f'场景相似度高 ({similarity:.0%})'
                })
        
        return suggestions
    
    def interactive_refine(self, segments: List[Dict], 
                          auto_approve: bool = False) -> Tuple[List[Dict], Dict]:
        """
        交互式场景优化
        
        Args:
            segments: 原始分段列表
            auto_approve: 是否自动确认所有建议
            
        Returns:
            (优化后的分段列表，优化报告)
        """
        print("\n" + "="*70)
        print(" 智能场景分析与优化")
        print("="*70 + "\n")
        
        # 1. 评估连贯性
        continuity_reports = self.evaluate_continuity(segments)
        
        # 2. 生成合并建议
        merge_suggestions = self._generate_merge_suggestions(segments)
        
        # 3. 生成场景报告
        scene_report = self.generate_scene_report(segments, continuity_reports)
        
        # 4. 显示报告
        self._display_scene_report(scene_report)
        
        # 5. 询问用户是否应用建议
        if not auto_approve and (merge_suggestions or continuity_reports):
            user_input = input("\n是否应用场景优化建议？[Y/n]: ").strip().lower()
            apply_changes = user_input != 'n'
        else:
            apply_changes = True
        
        if apply_changes:
            # 应用合并建议
            if merge_suggestions and len(merge_suggestions) > 0:
                optimized_segments = self.merge_similar_scenes(segments, similarity_threshold=0.7)
            else:
                optimized_segments = segments
            
            self._log("场景优化完成", "INFO")
            
            return optimized_segments, scene_report
        else:
            self._log("用户取消优化，保持原始场景", "INFO")
            return segments, scene_report
    
    def _display_scene_report(self, report: Dict):
        """
        显示场景分析报告
        
        Args:
            report: 场景分析报告
        """
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
            for trans in report['transition_suggestions'][:5]:  # 只显示前 5 个
                print(f"  段 {trans['from_segment']+1} → 段 {trans['to_segment']+1}: "
                      f"{trans['suggested_transition']}")
            if len(report['transition_suggestions']) > 5:
                print(f"  ... 还有 {len(report['transition_suggestions']) - 5} 个建议")
        
        if report['merge_suggestions']:
            print(f"\n【合并建议】")
            for merge in report['merge_suggestions'][:3]:  # 只显示前 3 个
                segs = ', '.join([f"段{s+1}" for s in merge['segments']])
                confidence = "高" if merge['confidence'] == 'high' else "中"
                print(f"  {segs} - 相似度 {merge['similarity']:.0%} (置信度：{confidence})")
            if len(report['merge_suggestions']) > 3:
                print(f"  ... 还有 {len(report['merge_suggestions']) - 3} 个建议")
