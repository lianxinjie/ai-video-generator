#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版 AI 配音分析引擎 - 三层智能配音系统

功能：
1. 双层分段架构
   - 小分段（0.5-1 秒）：人物台词/旁白
   - 中分段（2-3 秒）：特效音 + 场景背景音

2. 三层配音架构
   - Layer 1: 人物配音（Dialogue）
   - Layer 2: 音效（Foley/SFX）
   - Layer 3: 背景音乐（BGM）
"""

import json
from typing import Dict, List
from datetime import datetime


class EnhancedAIVoiceAnalyzer:
    """增强版 AI 配音分析引擎"""
    
    # 音效分类库
    SFX_CATEGORIES = {
        'nature': {
            'name': '自然环境',
            'sounds': ['rain', 'wind', 'thunder', 'birds', 'ocean', 'river'],
            'keywords': ['雨', '雪', '风', '雷', '鸟', '海浪', '河流', '自然']
        },
        'urban': {
            'name': '城市环境',
            'sounds': ['traffic', 'horn', 'siren', 'crowd', 'footsteps'],
            'keywords': ['车', '城市', '街道', '人群', '都市']
        },
        'action': {
            'name': '动作音效',
            'sounds': ['explosion', 'punch', 'gunshot', 'crash'],
            'keywords': ['战斗', '爆炸', '动作', '撞击']
        },
        'fantasy': {
            'name': '奇幻音效',
            'sounds': ['magic', 'dragon', 'castle', 'sword'],
            'keywords': ['魔法', '龙', '奇幻', '城堡', '剑']
        },
        'scifi': {
            'name': '科幻音效',
            'sounds': ['laser', 'robot', 'alarm', 'scanner'],
            'keywords': ['科幻', '激光', '机器人', '太空', '未来']
        }
    }
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def analyze_for_layers(self, prompt: str, duration: float) -> Dict:
        """分析提示词，生成三层配音方案"""
        
        # 1. 分析情绪
        from personal_mode.ai_voice_analyzer import AIVoiceAnalyzer
        base = AIVoiceAnalyzer(verbose=False)
        emotion = base.analyze_emotion(prompt)
        
        # 2. 分析场景
        scene = self._analyze_scene(prompt)
        
        # 3. 生成人物配音层（小分段）
        character_layers = self._gen_character(prompt, duration, emotion)
        
        # 4. 生成音效层（中分段）
        sfx_layers = self._gen_sfx(prompt, duration, emotion, scene)
        
        # 5. 推荐 BGM
        bgm = self._recommend_bgm(emotion, scene)
        
        return {
            'total_duration': duration,
            'emotion': emotion,
            'scene': scene,
            'layers': {
                'character': character_layers,
                'sfx': sfx_layers,
                'bgm': bgm
            },
            'mixing_guide': self._gen_mixing_guide(character_layers, sfx_layers, bgm)
        }
    
    def _analyze_scene(self, prompt: str) -> Dict:
        """分析场景类型"""
        prompt_lower = prompt.lower()
        
        scenes = []
        for scene_type, data in self.SFX_CATEGORIES.items():
            if any(kw in prompt_lower for kw in data['keywords']):
                scenes.append(scene_type)
        
        return {
            'primary': scenes[0] if scenes else 'neutral',
            'secondary': scenes[1:],
            'all': scenes
        }
    
    def _gen_character(self, prompt: str, duration: float, emotion: Dict) -> List[Dict]:
        """生成人物配音层（小分段 0.5-1 秒）"""
        from personal_mode.ai_voice_analyzer import AIVoiceAnalyzer
        base = AIVoiceAnalyzer(verbose=False)
        
        # 拆分为小分段
        segments = base.split_script_by_duration(prompt, duration, 0.75)
        
        layers = []
        for i, seg in enumerate(segments):
            # 智能分工：简单本地，复杂 AI
            text = seg['voiceover']['text']
            use_local = len(text) < 30 and '!' not in text
            
            layers.append({
                'index': i,
                'start': i * 0.75,
                'duration': 0.75,
                'text': text,
                'emotion': seg['voiceover']['emotion'],
                'voice': seg['voiceover']['voice'],
                'method': 'local' if use_local else 'ai',
                'file': f'audio/char_{i:03d}.wav'
            })
        
        return layers
    
    def _gen_sfx(self, prompt: str, duration: float, emotion: Dict, scene: Dict) -> List[Dict]:
        """生成音效层（中分段 2-3 秒）"""
        
        # 每 2.5 秒一个音效分段
        segment_dur = 2.5
        total_segments = int(duration / segment_dur)
        
        layers = []
        for i in range(total_segments):
            start = i * segment_dur
            
            # 分析该段需要的音效
            sfx_list = self._analyze_sfx(prompt, i, emotion, scene)
            
            for sfx in sfx_list:
                # 智能分工：常见音效本地，特殊音效 AI
                use_local = sfx['type'] in ['rain', 'wind', 'birds', 'traffic']
                
                layers.append({
                    'index': len(layers),
                    'segment': i,
                    'start': start + sfx.get('offset', 0),
                    'duration': sfx.get('duration', 1.5),
                    'type': sfx['type'],
                    'category': sfx['category'],
                    'volume': sfx.get('volume', 0.4),
                    'method': 'local' if use_local else 'ai',
                    'file': f"audio/sfx_{sfx['type']}_{i:03d}.wav",
                    'fade_in': 0.1,
                    'fade_out': 0.1
                })
        
        return layers
    
    def _analyze_sfx(self, prompt: str, seg_idx: int, emotion: Dict, scene: Dict) -> List[Dict]:
        """分析某段需要的音效"""
        results = []
        
        # 根据主场景推荐
        primary = scene.get('primary', 'neutral')
        if primary in self.SFX_CATEGORIES:
            sounds = self.SFX_CATEGORIES[primary]['sounds']
            results.append({
                'type': sounds[seg_idx % len(sounds)],
                'category': primary,
                'volume': 0.3,
                'description': f'{primary}环境音'
            })
        
        # 根据情绪添加
        emo = emotion.get('dominant_emotion', 'neutral')
        if emo == 'tense':
            results.append({
                'type': 'heartbeat',
                'category': 'emotion',
                'volume': 0.2,
                'offset': 0.5
            })
        elif emo == 'epic':
            results.append({
                'type': 'orchestra_hit',
                'category': 'music',
                'volume': 0.4,
                'offset': 0.0
            })
        
        return results
    
    def _recommend_bgm(self, emotion: Dict, scene: Dict) -> Dict:
        """推荐背景音乐"""
        
        emo = emotion.get('dominant_emotion', 'neutral')
        
        bgm_map = {
            'excited': {'type': 'upbeat', 'tempo': 'fast', 'genre': 'electronic'},
            'calm': {'type': 'peaceful', 'tempo': 'slow', 'genre': 'ambient'},
            'tense': {'type': 'suspense', 'tempo': 'medium', 'genre': 'orchestral'},
            'sad': {'type': 'melancholy', 'tempo': 'slow', 'genre': 'piano'},
            'epic': {'type': 'epic', 'tempo': 'medium', 'genre': 'orchestral'},
            'mysterious': {'type': 'mystery', 'tempo': 'slow', 'genre': 'ambient'}
        }
        
        rec = bgm_map.get(emo, bgm_map['calm'])
        
        return {
            'type': rec['type'],
            'tempo': rec['tempo'],
            'genre': rec['genre'],
            'volume': 0.25,
            'method': 'user_provided',
            'suggested_files': [
                f"music/{rec['type']}_{rec['genre']}.mp3"
            ]
        }
    
    def _gen_mixing_guide(self, char_layers, sfx_layers, bgm) -> Dict:
        """生成混音指南"""
        
        return {
            'character_volume': 1.0,
            'sfx_volume': 0.4,
            'bgm_volume': 0.25,
            'ducking': {
                'enable': True,
                'trigger': 'character',
                'reduction': -6
            },
            'master_limit': -0.1
        }


if __name__ == '__main__':
    analyzer = EnhancedAIVoiceAnalyzer()
    
    result = analyzer.analyze_for_layers(
        "赛博朋克城市，霓虹灯闪烁，雨夜，紧张的气氛",
        10.0
    )
    
    print("\n=== 三层配音分析 ===")
    print(f"情绪：{result['emotion']['dominant_emotion']}")
    print(f"场景：{result['scene']['primary']}")
    
    print(f"\n人物配音层：{len(result['layers']['character'])}段")
    for layer in result['layers']['character'][:3]:
        print(f"  [{layer['index']}] {layer['text'][:30]}... ({layer['method']})")
    
    print(f"\n音效层：{len(result['layers']['sfx'])}个音效")
    for layer in result['layers']['sfx'][:3]:
        print(f"  [{layer['index']}] {layer['type']} - {layer['category']} ({layer['method']})")
    
    print(f"\nBGM 推荐：{result['layers']['bgm']['type']} {result['layers']['bgm']['genre']}")
