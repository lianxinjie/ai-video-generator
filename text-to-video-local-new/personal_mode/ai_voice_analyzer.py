"""
AI 配音分析引擎

功能：
1. 智能脚本拆分 - 根据用户描述自动拆分为每秒的配音脚本
2. 情绪匹配 - 识别场景情绪匹配配音风格
3. 动态语速调节 - 根据视频内容调节语速和停顿
4. 分段台词生成 - 为每段视频生成对应的配音台词
5. 图片内容描述生成 - 为每段生成画面描述
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class AIVoiceAnalyzer:
    """AI 配音分析引擎"""
    
    # 情绪分类关键词
    EMOTION_KEYWORDS = {
        'excited': [
            '兴奋', '激动', '快乐', '欢呼', '跳跃', '庆祝', '胜利',
            'excited', 'happy', 'joy', 'celebrate', 'victory', 'cheer'
        ],
        'calm': [
            '平静', '宁静', '安详', '放松', '舒适', '温和', '优雅',
            'calm', 'peaceful', 'quiet', 'relaxed', 'gentle', 'elegant'
        ],
        'tense': [
            '紧张', '危险', '紧迫', '危机', '战斗', '逃跑', '追逐',
            'tense', 'danger', 'urgent', 'crisis', 'battle', 'chase'
        ],
        'sad': [
            '悲伤', '忧郁', '孤独', '失落', '哭泣', '哀伤', '怀念',
            'sad', 'melancholy', 'lonely', 'loss', 'cry', 'grief'
        ],
        'mysterious': [
            '神秘', '诡异', '未知', '探索', '发现', '奇迹', '魔法',
            'mysterious', 'magic', 'unknown', 'explore', 'discovery', 'wonder'
        ],
        'epic': [
            '史诗', '宏大', '壮观', '震撼', '伟大', '英雄', '传奇',
            'epic', 'grand', 'magnificent', 'awesome', 'heroic', 'legend'
        ]
    }
    
    # 语速建议（字/分钟）
    SPEECH_RATE = {
        'excited': {'min': 220, 'max': 280, 'default': 250},
        'calm': {'min': 140, 'max': 180, 'default': 160},
        'tense': {'min': 240, 'max': 320, 'default': 280},
        'sad': {'min': 100, 'max': 140, 'default': 120},
        'mysterious': {'min': 120, 'max': 160, 'default': 140},
        'epic': {'min': 160, 'max': 200, 'default': 180},
        'neutral': {'min': 180, 'max': 220, 'default': 200}
    }
    
    # 语音情感映射（Edge TTS 语音）
    VOICE_MAPPING = {
        'excited': 'zh-CN-XiaoxiaoNeural',  # 活泼女声
        'calm': 'zh-CN-YunxiNeural',        # 温和男声
        'tense': 'zh-CN-YunyangNeural',     # 专业男声（新闻播报）
        'sad': 'zh-CN-XiaohanNeural',       # 深情女声
        'mysterious': 'zh-CN-XiaomengNeural', # 轻柔女声
        'epic': 'zh-CN-YunxiNeural',        # 标准男声
        'neutral': 'zh-CN-XiaoxiaoNeural'   # 默认女声
    }
    
    def __init__(self, verbose: bool = True):
        """
        初始化 AI 配音分析引擎
        
        Args:
            verbose: 是否输出详细信息
        """
        self.verbose = verbose
        self.analysis_history: List[Dict] = []
    
    def _log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def analyze_emotion(self, text: str) -> Dict:
        """
        分析文本情绪
        
        Args:
            text: 要分析的文本
            
        Returns:
            情绪分析报告
        """
        text_lower = text.lower()
        
        # 计算每种情绪的匹配度
        emotion_scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            emotion_scores[emotion] = score
        
        # 找出主导情绪
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        dominant_score = emotion_scores[dominant_emotion]
        
        # 如果没有匹配到任何情绪，返回中性
        if dominant_score == 0:
            dominant_emotion = 'neutral'
        
        # 计算置信度
        total_matches = sum(emotion_scores.values())
        confidence = dominant_score / total_matches if total_matches > 0 else 0.5
        
        # 获取推荐语音和语速
        recommended_voice = self.VOICE_MAPPING.get(dominant_emotion, 'zh-CN-XiaoxiaoNeural')
        recommended_rate = self.SPEECH_RATE.get(dominant_emotion, self.SPEECH_RATE['neutral'])
        
        return {
            'dominant_emotion': dominant_emotion,
            'confidence': confidence,
            'emotion_scores': emotion_scores,
            'recommended_voice': recommended_voice,
            'recommended_speed': recommended_rate,
            'analysis': self._get_emotion_description(dominant_emotion)
        }
    
    def _get_emotion_description(self, emotion: str) -> str:
        """获取情绪描述"""
        descriptions = {
            'excited': '兴奋激动的情绪，适合使用明快的语调和较快的语速',
            'calm': '平静安详的情绪，适合使用温和的语调和中等语速',
            'tense': '紧张紧迫的情绪，适合使用紧凑的语调和快速的语速',
            'sad': '悲伤忧郁的情绪，适合使用低沉的语调和缓慢的语速',
            'mysterious': '神秘诡异的情绪，适合使用轻柔的语调和较慢的语速',
            'epic': '史诗宏大的情绪，适合使用浑厚的语调和稳重的语速',
            'neutral': '中性平静的情绪，使用标准语调和语速'
        }
        return descriptions.get(emotion, descriptions['neutral'])
    
    def split_script_by_duration(
        self,
        full_prompt: str,
        total_duration: float,
        segment_duration: float = 1.0
    ) -> List[Dict]:
        """
        根据视频时长智能拆分配音脚本
        
        Args:
            full_prompt: 完整的用户描述
            total_duration: 总时长（秒）
            segment_duration: 每段时长（秒）
            
        Returns:
            分段脚本列表
        """
        # 计算总段数
        total_segments = int(total_duration / segment_duration)
        
        # 分析整体情绪
        overall_emotion = self.analyze_emotion(full_prompt)
        
        # 分段策略
        # 1. 提取关键动作/场景变化点
        segments = self._extract_key_moments(full_prompt, total_segments)
        
        # 2. 如果没有明确的分段点，按时间均匀分配
        if len(segments) < total_segments:
            segments = self._distribute_evenly(full_prompt, total_segments)
        
        # 3. 为每段生成配音脚本和画面描述
        result = []
        for i, segment in enumerate(segments):
            # 分析该段情绪
            segment_emotion = self.analyze_emotion(segment.get('prompt', ''))
            
            # 生成配音台词
            voiceover = self._generate_voiceover_script(segment, i + 1)
            
            # 生成画面描述
            visual_description = self._generate_visual_description(segment, i + 1)
            
            # 计算建议播放时长
            suggested_duration = self._calculate_speech_duration(
                voiceover,
                segment_emotion['recommended_speed']['default']  # 取 default 值
            )
            
            result.append({
                'segment_index': i,
                'prompt': segment.get('prompt', ''),
                'start_time': i * segment_duration,
                'end_time': (i + 1) * segment_duration,
                'duration': segment_duration,
                'voiceover': {
                    'text': voiceover,
                    'emotion': segment_emotion['dominant_emotion'],
                    'voice': segment_emotion['recommended_voice'],
                    'speed': segment_emotion['recommended_speed']['default'],
                    'estimated_duration': suggested_duration
                },
                'visual_description': visual_description,
                'emotion_analysis': segment_emotion
            })
        
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'full_prompt': full_prompt,
            'total_duration': total_duration,
            'segments': result
        })
        
        return result
    
    def _extract_key_moments(self, text: str, max_segments: int) -> List[Dict]:
        """提取关键时刻/动作"""
        segments = []
        
        # 分割标点符号
        sentences = re.split(r'[,.!?;,.\uff0c.\uff1a]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 提取动作词
        action_patterns = [
            r'(开始 [\u4e00-\u9fa5]+)',
            r'(然后 [\u4e00-\u9fa5]+)',
            r'(接着 [\u4e00-\u9fa5]+)',
            r'(随后 [\u4e00-\u9fa5]+)',
            r'(最后 [\u4e00-\u9fa5]+)',
            r'(突然 [\u4e00-\u9fa5]+)',
            r'(渐渐 [\u4e00-\u9fa5]+)',
            r'(慢慢 [\u4e00-\u9fa5]+)'
        ]
        
        for sentence in sentences:
            if len(segments) >= max_segments:
                break
            
            # 查找动作标记
            has_action = any(re.search(pattern, sentence) for pattern in action_patterns)
            
            segments.append({
                'prompt': sentence,
                'has_action_marker': has_action,
                'importance': 2 if has_action else 1
            })
        
        return segments
    
    def _distribute_evenly(self, text: str, num_segments: int) -> List[Dict]:
        """均匀分配文本到各段"""
        # 简单策略：将整个提示词分配给每段（因为每段都会基于此生成）
        # 实际应用中可以根据场景变化智能拆分
        segments = []
        
        for i in range(num_segments):
            segments.append({
                'prompt': text,
                'segment_progress': f"{i + 1}/{num_segments}",
                'note': f'第{i + 1}段，建议微调提示词增加变化'
            })
        
        return segments
    
    def _generate_voiceover_script(self, segment: Dict, segment_index: int) -> str:
        """
        为该段生成配音台词
        
        Args:
            segment: 段信息
            segment_index: 段索引
            
        Returns:
            配音台语文本
        """
        prompt = segment.get('prompt', '')
        
        # 策略 1: 直接提取关键短语
        keywords = self._extract_keywords(prompt)
        
        if len(keywords) > 0:
            # 组合成自然的台词
            voiceover = self._compose_natural_speech(keywords, segment_index)
        else:
            # 使用原始提示词精简版
            voiceover = self._simplify_prompt(prompt, segment_index)
        
        return voiceover
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 移除常见停用词
        stopwords = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个']
        
        # 简单分词（中文）
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]
        
        # 提取英文单词
        en_words = re.findall(r'\b[a-zA-Z]+\b', text)
        keywords.extend(en_words)
        
        return keywords[:5]  # 最多 5 个关键词
    
    def _compose_natural_speech(self, keywords: List[str], segment_index: int) -> str:
        """将关键词组合成自然的台词"""
        if not keywords:
            return f"场景{segment_index}"
        
        # 使用连接词组合
        connectors = ['，', '，', '，', ' ']
        
        # 简单组合
        voiceover = connectors[0].join(keywords[:3])
        
        # 添加适当的标点
        if len(voiceover) > 10:
            voiceover = voiceover[:10] + '，' + voiceover[10:]
        
        return voiceover
    
    def _simplify_prompt(self, prompt: str, segment_index: int) -> str:
        """精简提示词作为台词"""
        # 截断到合适长度（20-30 字）
        if len(prompt) <= 30:
            return prompt
        
        # 找到最近的标点符号
        cutoff = 30
        for i, char in enumerate(prompt[:30]):
            if char in ',....!?!.,':
                cutoff = i + 1
                break
        
        return prompt[:cutoff]
    
    def _generate_visual_description(self, segment: Dict, segment_index: int) -> str:
        """
        生成画面描述
        
        Args:
            segment: 段信息
            segment_index: 段索引
            
        Returns:
            画面描述文本
        """
        prompt = segment.get('prompt', '')
        
        # 生成简洁的画面描述
        description = f"场景{segment_index}: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
        
        return description
    
    def _calculate_speech_duration(self, text: str, speech_rate: int) -> float:
        """
        计算语音时长
        
        Args:
            text: 台语文本
            speech_rate: 语速（字/分钟）
            
        Returns:
            预计时长（秒）
        """
        # 中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        # 英文单词数
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        # 总字符数（英文单词按 2 字计算）
        total_chars = chinese_chars + english_words * 2
        
        # 计算时长（秒）
        duration = (total_chars / speech_rate) * 60
        
        return max(0.5, min(duration, 5.0))  # 限制在 0.5-5 秒
    
    def export_analysis(self, output_path: str):
        """
        导出分析报告
        
        Args:
            output_path: 输出文件路径
        """
        report = {
            'analysis_history': self.analysis_history,
            'total_analyses': len(self.analysis_history),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self._log(f"导出分析报告：{output_path}", "INFO")
    
    def get_voice_config(self, emotion: str) -> Dict:
        """
        获取指定情绪的语音配置
        
        Args:
            emotion: 情绪类型
            
        Returns:
            语音配置
        """
        return {
            'voice': self.VOICE_MAPPING.get(emotion, 'zh-CN-XiaoxiaoNeural'),
            'rate': self.SPEECH_RATE.get(emotion, self.SPEECH_RATE['neutral']),
            'emotion_description': self._get_emotion_description(emotion)
        }


if __name__ == '__main__':
    # 测试示例
    analyzer = AIVoiceAnalyzer()
    
    # 测试情绪分析
    test_prompts = [
        "一只快乐的小狗在草地上奔跑",
        "宁静的夜晚，月光洒在湖面上",
        "激烈的战斗场面，英雄与巨龙搏斗",
        "神秘古老的城堡，隐藏在迷雾中",
        "史诗般的宏大场景，千军万马奔腾"
    ]
    
    print("=" * 60)
    print("AI 配音分析引擎 - 情绪分析测试")
    print("=" * 60)
    
    for prompt in test_prompts:
        print(f"\n提示词：{prompt}")
        result = analyzer.analyze_emotion(prompt)
        print(f"主导情绪：{result['dominant_emotion']} ({result['confidence']:.0%})")
        print(f"推荐语音：{result['recommended_voice']}")
        print(f"推荐语速：{result['recommended_speed']['default']} 字/分钟")
        print(f"分析：{result['analysis']}")
    
    print("\n" + "=" * 60)
    print("配音脚本拆分测试")
    print("=" * 60)
    
    # 测试脚本拆分
    full_prompt = "赛博朋克城市从夜晚到黎明，霓虹灯闪烁，高楼林立，" \
                  "街道上人来人往，飞行器穿梭其间，" \
                  "渐渐天空泛起鱼肚白，灯光渐暗，新的一天开始"
    
    segments = analyzer.split_script_by_duration(
        full_prompt=full_prompt,
        total_duration=5.0,
        segment_duration=1.0
    )
    
    for seg in segments:
        print(f"\n第{seg['segment_index'] + 1}秒:")
        print(f"  提示词：{seg['prompt'][:30]}...")
        print(f"  台词：{seg['voiceover']['text']}")
        print(f"  情绪：{seg['voiceover']['emotion']}")
        print(f"  语音：{seg['voiceover']['voice']}")
        print(f"  时长：{seg['voiceover']['estimated_duration']:.1f}秒")
