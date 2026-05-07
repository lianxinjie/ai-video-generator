# -*- coding: utf-8 -*-
"""
智能场景检测器 - 基于关键词分析自动判定是否新增场景

核心功能：
1. 常用场景关键词库（5 大类 50+ 场景）
2. 场景重要度评分算法
3. 智能场景边界创建
4. 场景优先级排序
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class SceneDetector:
    """智能场景检测器"""
    
    # 常用场景关键词库（5 大类 50+ 场景）
    COMMON_SCENE_KEYWORDS = {
        # 1. 时间场景（10 个）
        'time_scene': {
            'keywords': [
                '日出', '黎明', '清晨', '早晨', '早上',
                '日落', '黄昏', '傍晚', '夜晚', '深夜', '午夜',
                '白天', '正午', '中午',
                'sunrise', 'dawn', 'morning', 'dusk', 'sunset', 
                'evening', 'night', 'midnight', 'noon', 'day',
                'from day to night', 'from night to dawn', 'time lapse'
            ],
            'weight': 1.2,  # 时间场景权重
            'min_score': 0.6  # 最低触发分数
        },
        
        # 2. 动作场景（12 个）
        'action_scene': {
            'keywords': [
                '爆炸', '战斗', '飞行', '奔跑', '跳跃',
                '舞蹈', '游泳', '攀爬', '打斗', '射击',
                '追逐', '降落',
                'explosion', 'battle', 'flying', 'running', 'jumping',
                'dancing', 'swimming', 'climbing', 'fighting', 'shooting',
                'chasing', 'landing', 'attack', 'strike'
            ],
            'weight': 1.5,  # 动作场景权重最高
            'min_score': 0.5
        },
        
        # 3. 镜头场景（8 个）
        'camera_scene': {
            'keywords': [
                '特写', '全景', '俯视图', '鸟瞰', '远景',
                '近景', '中景', '微距',
                'close-up', 'panorama', 'aerial view', 'bird view', 'wide shot',
                'zoom in', 'zoom out', 'pan left', 'pan right', 'tilt up', 'tilt down',
                'camera pans', 'camera zooms'
            ],
            'weight': 1.3,
            'min_score': 0.5
        },
        
        # 4. 元素场景（15 个）
        'element_scene': {
            'keywords': [
                # 生物
                '龙', '凤凰', '麒麟', '独角兽', '巨人',
                'dragon', 'phoenix', 'unicorn', 'giant', 'dinosaur',
                # 建筑
                '城堡', '寺庙', '宫殿', '塔楼', '桥梁',
                'castle', 'temple', 'palace', 'tower', 'bridge',
                # 载具
                '飞船', '飞艇', '战船', '马车',
                'spaceship', 'airship', ' UFO'
            ],
            'weight': 1.4,
            'min_score': 0.6
        },
        
        # 5. 天气场景（8 个）
        'weather_scene': {
            'keywords': [
                '下雨', '下雪', '雷暴', '暴雨', '大风',
                '雾霾', '彩虹', '闪电',
                'rain', 'snow', 'thunder', 'storm', 'fog',
                'windy', 'tornado', 'lightning', 'rainbow'
            ],
            'weight': 1.1,
            'min_score': 0.5
        }
    }
    
    # 场景转换强度标志（决定是否需要新场景）
    TRANSITION_STRENGTH = {
        'strong': {
            'keywords': ['切换到', '转到', '突然', '瞬间', '然后', 
                        'switch to', 'move to', 'suddenly', 'then', 'cut to'],
            'threshold': 0.3  # 超过 0.3 就需要新场景
        },
        'medium': {
            'keywords': ['接着', '随后', '之后', '继续',
                        'next', 'after', 'continue', 'followed by'],
            'threshold': 0.2  # 超过 0.2 就需要新场景
        },
        'weak': {
            'keywords': ['同时', '并且', '还有', '以及',
                        'while', 'also', 'and', 'plus'],
            'threshold': 0.15  # 弱转换通常不创建新场景
        }
    }
    
    def __init__(self, 
                 verbose: bool = True,
                 detection_threshold: float = 0.5,
                 weight_multiplier: float = 1.0):
        """
        初始化场景检测器
        
        Args:
            verbose: 是否输出详细信息
            detection_threshold: 检测阈值（0-1，默认 0.5）
                               低于此值不创建新场景
            weight_multiplier: 权重倍率（用于调整敏感度）
        """
        self.verbose = verbose
        self.detection_threshold = detection_threshold
        self.weight_multiplier = weight_multiplier
        self.detection_history: List[Dict] = []
        
    def _log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def detect_scene_keywords(self, text: str) -> Dict:
        """
        检测文本中的场景关键词
        
        Args:
            text: 输入文本
            
        Returns:
            检测结果，包含命中的关键词和分数
        """
        text_lower = text.lower()
        results = {
            'time_scene': {'hits': [], 'score': 0.0},
            'action_scene': {'hits': [], 'score': 0.0},
            'camera_scene': {'hits': [], 'score': 0.0},
            'element_scene': {'hits': [], 'score': 0.0},
            'weather_scene': {'hits': [], 'score': 0.0}
        }
        
        # 检测每类场景关键词
        for scene_type, config in self.COMMON_SCENE_KEYWORDS.items():
            keywords = config['keywords']
            weight = config['weight'] * self.weight_multiplier
            min_score = config['min_score']
            
            hits = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    hits.append(keyword)
            
            if hits:
                # 计算分数：命中词数 / 总词数 * 权重
                raw_score = len(hits) / len(keywords) * weight
                normalized_score = min(1.0, raw_score * 2)  # 归一化到 0-1
                
                results[scene_type] = {
                    'hits': hits,
                    'score': normalized_score,
                    'raw_score': raw_score,
                    'min_threshold': min_score
                }
        
        # 计算总分
        total_score = sum(r['score'] for r in results.values())
        max_possible = len(self.COMMON_SCENE_KEYWORDS)
        
        results['overall'] = {
            'total_score': total_score / max_possible,
            'max_score': max_possible,
            'detected_types': sum(1 for r in results.values() if r['hits'])
        }
        
        return results
    
    def detect_transition_strength(self, text: str) -> Dict:
        """
        检测场景转换强度
        
        Args:
            text: 输入文本
            
        Returns:
            转换强度评估
        """
        text_lower = text.lower()
        
        results = {
            'strong': [],
            'medium': [],
            'weak': [],
            'detected_strength': 'none',
            'threshold': 1.0
        }
        
        # 检测转换强度标志
        for strength, config in self.TRANSITION_STRENGTH.items():
            for keyword in config['keywords']:
                if keyword.lower() in text_lower:
                    results[strength].append(keyword)
        
        # 确定最强转换类型
        if results['strong']:
            results['detected_strength'] = 'strong'
            results['threshold'] = self.TRANSITION_STRENGTH['strong']['threshold']
        elif results['medium']:
            results['detected_strength'] = 'medium'
            results['threshold'] = self.TRANSITION_STRENGTH['medium']['threshold']
        elif results['weak']:
            results['detected_strength'] = 'weak'
            results['threshold'] = self.TRANSITION_STRENGTH['weak']['threshold']
        
        return results
    
    def should_create_new_scene(self, text: str, 
                                context: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        判断是否应该创建新场景
        
        Args:
            text: 输入文本
            context: 上下文信息（可选，包含之前场景的信息）
            
        Returns:
            (是否创建新场景，检测报告)
        """
        # 1. 检测场景关键词
        keyword_results = self.detect_scene_keywords(text)
        
        # 2. 检测转换强度
        transition_results = self.detect_transition_strength(text)
        
        # 3. 计算场景重要度分数
        importance_score = self._calculate_importance_score(
            keyword_results, 
            transition_results,
            context
        )
        
        # 4. 判定是否创建新场景
        should_create = importance_score >= self.detection_threshold
        
        # 5. 生成报告
        report = {
            'text': text,
            'importance_score': importance_score,
            'detection_threshold': self.detection_threshold,
            'should_create_scene': should_create,
            'keyword_analysis': keyword_results,
            'transition_analysis': transition_results,
            'detected_categories': self._get_detected_categories(keyword_results),
            'confidence': self._calculate_confidence(keyword_results, transition_results)
        }
        
        # 6. 记录历史
        self.detection_history.append(report)
        
        return should_create, report
    
    def _calculate_importance_score(self, 
                                     keyword_results: Dict,
                                     transition_results: Dict,
                                     context: Optional[Dict] = None) -> float:
        """
        计算场景重要度分数
        
        Args:
            keyword_results: 关键词检测结果
            transition_results: 转换强度检测结果
            context: 上下文信息
            
        Returns:
            重要度分数（0-1）
        """
        # 1. 基础分数（来自场景关键词）
        overall_score = keyword_results.get('overall', {}).get('total_score', 0.0)
        
        # 2. 检查是否有超过阈值的场景类型，大幅加分
        type_bonus = 0.0
        detected_count = 0
        for scene_type, result in keyword_results.items():
            if scene_type == 'overall':
                continue
            
            if result['hits']:
                detected_count += 1
                min_threshold = result.get('min_threshold', 0.5)
                score = result['score']
                
                # 超过最低阈值的类型给予额外加分
                if score >= min_threshold:
                    type_bonus += (score - min_threshold) * 1.5
                else:
                    # 即使未达到阈值，也给与基础加分
                    type_bonus += score * 0.5
        
        # 3. 检测到的类别数量加分（每多一个类别加 0.15）
        category_bonus = min(0.5, detected_count * 0.15)
        
        # 4. 转换强度加分
        transition_bonus = 0.0
        strength = transition_results['detected_strength']
        if strength == 'strong':
            transition_bonus = 0.4
        elif strength == 'medium':
            transition_bonus = 0.25
        elif strength == 'weak':
            transition_bonus = 0.1
        
        # 5. 上下文惩罚（如果与前一场景太相似）
        similarity_penalty = 0.0
        if context and 'previous_scene_keywords' in context:
            prev_keywords = set(context['previous_scene_keywords'])
            curr_keywords = set()
            
            for scene_type, result in keyword_results.items():
                if scene_type == 'overall':
                    continue
                curr_keywords.update(result.get('hits', []))
            
            if prev_keywords and curr_keywords:
                overlap = len(prev_keywords & curr_keywords) / max(len(curr_keywords), 1)
                if overlap > 0.5:  # 超过 50% 重复，给予惩罚
                    similarity_penalty = overlap * 0.3
        
        # 6. 综合计算（提高基础分数的权重）
        importance_score = (overall_score * 2.0) + type_bonus + category_bonus + transition_bonus - similarity_penalty
        
        # 归一化到 0-1
        return max(0.0, min(1.0, importance_score))
    
    def _get_detected_categories(self, keyword_results: Dict) -> List[str]:
        """获取检测到的场景类别列表"""
        categories = []
        for scene_type, result in keyword_results.items():
            if scene_type == 'overall':
                continue
            if result['hits']:
                categories.append(scene_type.replace('_', ' ').title())
        return categories
    
    def _calculate_confidence(self, 
                              keyword_results: Dict,
                              transition_results: Dict) -> float:
        """计算检测置信度"""
        # 基于检测到的类别数量和转换强度计算置信度
        detected_count = keyword_results.get('overall', {}).get('detected_types', 0)
        
        base_confidence = min(0.5, detected_count * 0.15)
        
        if transition_results['detected_strength'] == 'strong':
            base_confidence += 0.3
        elif transition_results['detected_strength'] == 'medium':
            base_confidence += 0.15
        
        return min(1.0, base_confidence)
    
    def analyze_and_split(self, full_prompt: str) -> List[Dict]:
        """
        分析完整提示词并智能拆分成场景
        
        Args:
            full_prompt: 完整提示词
            
        Returns:
            场景列表（包含拆分信息）
        """
        self._log(f"开始智能场景检测：{full_prompt[:60]}...", "INFO")
        
        # 1. 检测场景关键词
        keyword_results = self.detect_scene_keywords(full_prompt)
        
        # 2. 检测场景边界（逗号、句号、连接词等）
        boundaries = self._detect_sentence_boundaries(full_prompt)
        
        # 3. 对每个分段进行场景判定
        segments = []
        current_position = 0
        
        for i, boundary in enumerate(boundaries):
            segment_text = full_prompt[current_position:boundary['end']]
            
            # 判断是否创建新场景
            context = {
                'previous_scene_keywords': segments[-1].get('keywords', []) if segments else []
            }
            
            should_create, report = self.should_create_new_scene(
                segment_text,
                context
            )
            
            if should_create or i == 0:
                # 创建新场景
                segments.append({
                    'segment_index': len(segments),
                    'text': segment_text.strip(),
                    'start_position': current_position,
                    'end_position': boundary['end'],
                    'importance_score': report['importance_score'],
                    'detected_categories': report['detected_categories'],
                    'keywords': self._extract_all_keywords(keyword_results),
                    'transition_type': report['transition_analysis']['detected_strength']
                })
                
                self._log(
                    f"✓ 创建场景 {len(segments)}: {segment_text[:40]}... "
                    f"(重要度：{report['importance_score']:.2f})", 
                    "INFO"
                )
            
            current_position = boundary['end']
        
        self._log(f"场景检测完成：拆分为 {len(segments)} 个场景", "INFO")
        
        return segments
    
    def _detect_sentence_boundaries(self, text: str) -> List[Dict]:
        """检测句子边界（逗号、句号等）"""
        boundaries = []
        
        # 检测标点符号
        for i, char in enumerate(text):
            if char in ',.!.,':
                boundaries.append({
                    'position': i,
                    'end': i + 1,
                    'type': 'punctuation',
                    'char': char
                })
        
        # 检测连接词
        connectors = ['and', 'then', 'but', 'while', 'after', 'before']
        text_lower = text.lower()
        for connector in connectors:
            pos = 0
            while True:
                pos = text_lower.find(connector, pos)
                if pos == -1:
                    break
                boundaries.append({
                    'position': pos,
                    'end': pos + len(connector),
                    'type': 'connector',
                    'char': connector
                })
                pos += len(connector)
        
        # 按位置排序
        boundaries.sort(key=lambda x: x['position'])
        
        return boundaries
    
    def _extract_all_keywords(self, keyword_results: Dict) -> List[str]:
        """提取所有命中的关键词"""
        keywords = []
        for scene_type, result in keyword_results.items():
            if scene_type == 'overall':
                continue
            keywords.extend(result.get('hits', []))
        return keywords
    
    def export_analysis_report(self) -> Dict:
        """导出分析报告"""
        return {
            'total_detections': len(self.detection_history),
            'detections': self.detection_history,
            'statistics': self._calculate_statistics(),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_statistics(self) -> Dict:
        """计算统计信息"""
        if not self.detection_history:
            return {}
        
        created_scenes = sum(1 for d in self.detection_history if d['should_create_scene'])
        avg_confidence = sum(d['confidence'] for d in self.detection_history) / len(self.detection_history)
        
        return {
            'total_analyzed': len(self.detection_history),
            'scenes_created': created_scenes,
            'scenes_skipped': len(self.detection_history) - created_scenes,
            'creation_rate': created_scenes / len(self.detection_history),
            'average_confidence': avg_confidence,
            'threshold_used': self.detection_threshold
        }
