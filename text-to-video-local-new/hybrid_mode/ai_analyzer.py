#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 智能分析模块 - 自动判断场景类型和风格

通过 AI 对话分析用户提示词，自动选择最优的场景转换类型和风格预设
"""

import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AIStyleAnalyzer:
    """AI 风格分析器"""
    
    def __init__(self):
        # 场景类型关键词库
        self.scene_type_keywords = {
            "time_lapse": {
                "keywords": [
                    "time", "day", "night", "morning", "evening", "sunrise", "sunset",
                    "dawn", "dusk", "season", "spring", "summer", "autumn", "winter",
                    "changing", "transition", "evolution", "passing", "flow",
                    "时间", "天", "夜", "早晨", "傍晚", "日出", "日落",
                    "季节", "春", "夏", "秋", "冬", "变化", "流逝"
                ],
                "description": "同一场景在不同时间/季节的变化"
            },
            "zoom_sequence": {
                "keywords": [
                    "zoom", "approach", "close", "detail", "wide", "far", "near",
                    "focus", "macro", "extreme", "panoramic", "close-up",
                    "推进", "拉近", "特写", "远景", "细节", "放大", "缩小", "聚焦"
                ],
                "description": "视角从远到近或从近到远的推进"
            },
            "pan_sequence": {
                "keywords": [
                    "move", "walk", "travel", "journey", "explore", "enter", "leave",
                    "through", "across", "from", "to", "path", "route",
                    "移动", "行走", "旅行", "探索", "进入", "离开", "穿过", "从", "到"
                ],
                "description": "从一个场景移动到另一个场景"
            },
            "weather_change": {
                "keywords": [
                    "weather", "rain", "snow", "storm", "cloud", "fog", "mist",
                    "clear", "wind", "thunder", "lightning",
                    "天气", "雨", "雪", "风暴", "云", "雾", "晴", "风", "雷", "电"
                ],
                "description": "同一场景在不同天气下的变化"
            },
            "iterative_img2img": {
                "keywords": [
                    "story", "narrative", "sequence", "action", "character", "person",
                    "figure", "happen", "event", "plot", "character", "protagonist",
                    "故事", "情节", "序列", "动作", "角色", "人物", "事件", "发生"
                ],
                "description": "有连续情节或动作的叙事性场景"
            }
        }
        
        # 风格关键词库
        self.style_keywords = {
            "cyberpunk": {
                "keywords": [
                    "cyberpunk", "neon", "futuristic", "cyber", "sci-fi", "high-tech",
                    "dystopian", "hologram", "android", "robot", "synthetic",
                    "赛博朋克", "霓虹", "未来", "赛博", "高科技", " dystopia", "全息", "机器人"
                ],
                "colors": ["blue", "purple", "magenta", "cyan", "pink"],
                "description": "未来高科技、霓虹灯光、赛博朋克风格"
            },
            "fantasy": {
                "keywords": [
                    "fantasy", "magic", "medieval", "dragon", "wizard", "castle",
                    "elf", "dwarf", "mythical", "enchanted", "mystical", "legendary",
                    "奇幻", "魔法", "中世纪", "龙", "巫师", "城堡", "精灵", "神秘"
                ],
                "colors": ["gold", "emerald", "sapphire", "purple", "warm"],
                "description": "魔法、中世纪、神话元素的奇幻风格"
            },
            "scifi": {
                "keywords": [
                    "sci-fi", "science fiction", "spaceship", "alien", "space",
                    "technology", "futuristic", "laser", "starship", "cosmic",
                    "科幻", "太空", "飞船", "外星人", "科技", "激光", "星际"
                ],
                "colors": ["white", "silver", "orange", "blue", "metallic"],
                "description": "太空、科技、外星文明的科幻风格"
            },
            "natural": {
                "keywords": [
                    "nature", "landscape", "mountain", "river", "forest", "ocean",
                    "peaceful", "serene", "organic", "natural", "scenic", "beautiful",
                    "自然", "风景", "山", "河", "森林", "海洋", "宁静", "美丽"
                ],
                "colors": ["green", "brown", "blue", "earth tone", "natural"],
                "description": "自然风光、宁静优美的自然风格"
            },
            "horror": {
                "keywords": [
                    "horror", "dark", "creepy", "scary", "haunted", "ghost",
                    "nightmare", "evil", "sinister", "gothic", "macabre", "terrifying",
                    "恐怖", "黑暗", "诡异", "可怕", "鬼魂", "噩梦", "邪恶"
                ],
                "colors": ["black", "dark red", "grey", "desaturated", "muted"],
                "description": "黑暗、诡异、令人不安的恐怖风格"
            },
            "custom": {
                "keywords": [],
                "colors": [],
                "description": "用户自定义或混合风格"
            }
        }
    
    def analyze_prompt(self, prompt: str) -> Dict:
        """
        分析用户提示词，自动判断场景类型和风格
        
        Args:
            prompt: 用户输入的提示词
            
        Returns:
            分析结果，包括推荐的场景类型、风格等
        """
        prompt_lower = prompt.lower()
        
        # 1. 分析场景转换类型
        scene_type = self._detect_scene_type(prompt_lower)
        
        # 2. 分析艺术风格
        style = self._detect_style(prompt_lower)
        
        # 3. 提取关键元素
        elements = self._extract_key_elements(prompt_lower)
        
        # 4. 生成建议
        suggestions = self._generate_suggestions(prompt, scene_type, style, elements)
        
        result = {
            "scene_type": scene_type,
            "style": style,
            "elements": elements,
            "suggestions": suggestions,
            "confidence": self._calculate_confidence(scene_type, style)
        }
        
        logger.info(f"AI 分析完成：{scene_type['type']} + {style['style']}")
        
        return result
    
    def _detect_scene_type(self, prompt: str) -> Dict:
        """检测场景转换类型"""
        scores = {}
        
        for scene_type, config in self.scene_type_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in prompt:
                    score += 1
                    matched_keywords.append(keyword)
            
            scores[scene_type] = {
                "score": score,
                "matched": matched_keywords,
                "description": config["description"]
            }
        
        # 找出得分最高的类型
        best_match = max(scores.items(), key=lambda x: x[1]["score"])
        
        if best_match[1]["score"] == 0:
            # 没有匹配，返回默认
            return {
                "type": "custom",
                "confidence": 0,
                "description": "无法确定场景类型，使用自定义模式",
                "matched_keywords": []
            }
        else:
            return {
                "type": best_match[0],
                "confidence": min(best_match[1]["score"] / 5, 1.0),  # 归一化到 0-1
                "description": best_match[1]["description"],
                "matched_keywords": best_match[1]["matched"]
            }
    
    def _detect_style(self, prompt: str) -> Dict:
        """检测艺术风格"""
        scores = {}
        
        for style_name, config in self.style_keywords.items():
            if style_name == "custom":
                continue
            
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in prompt:
                    score += 1
                    matched_keywords.append(keyword)
            
            scores[style_name] = {
                "score": score,
                "matched": matched_keywords,
                "colors": config["colors"],
                "description": config["description"]
            }
        
        # 找出得分最高的风格
        if not scores or scores[max(scores.keys(), key=lambda k: scores[k]["score"])]["score"] == 0:
            # 没有匹配，返回自定义
            return {
                "style": "custom",
                "confidence": 0,
                "description": "无法确定风格，使用自定义",
                "colors": [],
                "matched_keywords": []
            }
        
        best_match = max(scores.items(), key=lambda x: x[1]["score"])
        
        return {
            "style": best_match[0],
            "confidence": min(best_match[1]["score"] / 5, 1.0),
            "description": best_match[1]["description"],
            "colors": best_match[1]["colors"],
            "matched_keywords": best_match[1]["matched"]
        }
    
    def _extract_key_elements(self, prompt: str) -> List[str]:
        """提取关键元素"""
        # 简单的元素提取：名词短语
        # 可以后续用 AI 优化
        elements = []
        
        # 常见元素关键词
        element_keywords = [
            "city", "street", "building", "tower", "car", "person", "animal",
            "tree", "mountain", "river", "ocean", "sky", "cloud", "star",
            "城市", "街道", "建筑", "塔", "车", "人", "动物",
            "树", "山", "河", "海", "天空", "云", "星"
        ]
        
        for keyword in element_keywords:
            if keyword in prompt:
                elements.append(keyword)
        
        return elements
    
    def _generate_suggestions(
        self,
        prompt: str,
        scene_type: Dict,
        style: Dict,
        elements: List[str]
    ) -> Dict:
        """生成优化建议"""
        suggestions = {
            "prompt_enhancement": [],
            "transition_tips": [],
            "consistency_tips": []
        }
        
        # 提示词增强建议
        if len(prompt.split()) < 10:
            suggestions["prompt_enhancement"].append(
                "提示词较短，建议添加更多细节描述（光线、色彩、氛围）"
            )
        
        if scene_type["type"] != "custom":
            suggestions["prompt_enhancement"].append(
                f"已识别为「{scene_type['type']}」场景，建议在每张图中保持"
            )
        
        # 转场建议
        if scene_type["type"] == "time_lapse":
            suggestions["transition_tips"].append(
                "建议使用 crossfade 转场效果，时长 0.5-1 秒"
            )
        elif scene_type["type"] == "zoom_sequence":
            suggestions["transition_tips"].append(
                "建议使用 cut 或快速转场，突出镜头切换感"
            )
        
        # 一致性建议
        if style["style"] == "cyberpunk":
            suggestions["consistency_tips"].append(
                "保持霓虹色调一致：蓝、紫、粉、青"
            )
        elif style["style"] == "natural":
            suggestions["consistency_tips"].append(
                "保持自然光色温和，避免过度饱和"
            )
        
        # 如果是自定义类型，建议用户补充信息
        if scene_type["type"] == "custom" and style["style"] == "custom":
            suggestions["prompt_enhancement"].append(
                "提示词特征不明显，AI 无法自动判断场景类型和风格\n"
                "建议：\n"
                "  - 添加场景转换描述（如'从远到近'、'白天到夜晚'）\n"
                "  - 添加风格关键词（如'赛博朋克'、'奇幻'）\n"
                "  - 或手动指定 --scene-type 和 --style 参数"
            )
        
        return suggestions
    
    def _calculate_confidence(
        self,
        scene_type: Dict,
        style: Dict
    ) -> Dict:
        """计算置信度"""
        scene_conf = scene_type.get("confidence", 0)
        style_conf = style.get("confidence", 0)
        
        overall = (scene_conf + style_conf) / 2
        
        return {
            "scene_type": scene_conf,
            "style": style_conf,
            "overall": overall,
            "level": "high" if overall > 0.6 else "medium" if overall > 0.3 else "low"
        }


def main():
    """测试用命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 风格分析器")
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="要分析的提示词"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出 JSON 文件路径"
    )
    
    args = parser.parse_args()
    
    analyzer = AIStyleAnalyzer()
    result = analyzer.analyze_prompt(args.prompt)
    
    # 打印结果
    print("\n" + "="*60)
    print(" AI 智能分析结果")
    print("="*60)
    
    print(f"\n场景类型：{result['scene_type']['type']}")
    print(f"  置信度：{result['scene_type']['confidence']*100:.0f}%")
    print(f"  描述：{result['scene_type']['description']}")
    if result['scene_type']['matched_keywords']:
        print(f"  匹配关键词：{', '.join(result['scene_type']['matched_keywords'])}")
    
    print(f"\n艺术风格：{result['style']['style']}")
    print(f"  置信度：{result['style']['confidence']*100:.0f}%")
    print(f"  描述：{result['style']['description']}")
    if result['style'].get('colors'):
        print(f"  推荐色彩：{', '.join(result['style']['colors'])}")
    if result['style']['matched_keywords']:
        print(f"  匹配关键词：{', '.join(result['style']['matched_keywords'])}")
    
    if result['elements']:
        print(f"\n关键元素：{', '.join(result['elements'])}")
    
    print(f"\n总置信度：{result['confidence']['level'].upper()} ({result['confidence']['overall']*100:.0f}%)")
    
    if result['suggestions']:
        print(f"\n建议:")
        suggestions = result['suggestions']
        
        if suggestions.get('prompt_enhancement'):
            print("\n  【提示词增强】")
            for s in suggestions['prompt_enhancement']:
                print(f"    • {s}")
        
        if suggestions.get('transition_tips'):
            print("\n  【转场建议】")
            for s in suggestions['transition_tips']:
                print(f"    • {s}")
        
        if suggestions.get('consistency_tips'):
            print("\n  【一致性建议】")
            for s in suggestions['consistency_tips']:
                print(f"    • {s}")
    
    # 保存为 JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到：{args.output}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
