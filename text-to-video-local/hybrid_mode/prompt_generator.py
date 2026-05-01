#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模式 - 提示词生成器

通过 AI 对话生成连贯的视频提示词模板，支持多种场景转换类型
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptTemplateGenerator:
    """提示词模板生成器"""
    
    def __init__(self, output_dir: str = "./hybrid_mode/prompts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 预设模板类型
        self.template_types = {
            "time_lapse": "时间流逝（同一场景不同时间）",
            "zoom_sequence": "视角推进（远→中→近）",
            "pan_sequence": "空间移动（场景 A→场景 B）",
            "scene_transition": "多场景转换",
            "weather_change": "天气变化",
            "emotion_progression": "情绪递进",
            "iterative_img2img": "迭代图生图"
        }
        
        # 基础风格库
        self.style_presets = {
            "cyberpunk": {
                "keywords": "cyberpunk, neon lights, futuristic city, high tech, dark atmosphere",
                "colors": "blue, purple, magenta, cyan",
                "lighting": "neon glow, volumetric lighting"
            },
            "fantasy": {
                "keywords": "fantasy world, magical, medieval, epic, mystical",
                "colors": "gold, emerald, sapphire, warm earth tones",
                "lighting": "ethereal glow, sunset/sunrise"
            },
            "scifi": {
                "keywords": "science fiction, spaceship, alien world, advanced technology",
                "colors": "metallic, white, orange, cool blue",
                "lighting": "clean, clinical, dramatic shadows"
            },
            "natural": {
                "keywords": "nature, landscape, peaceful, serene, organic",
                "colors": "green, brown, blue, natural tones",
                "lighting": "golden hour, soft natural light"
            },
            "horror": {
                "keywords": "horror, dark, creepy, unsettling, gothic",
                "colors": "desaturated, black, dark red, muted tones",
                "lighting": "low key, harsh shadows"
            }
        }
    
    def generate_time_lapse_template(
        self,
        location: str,
        style: str = "natural",
        time_points: List[str] = None
    ) -> Dict:
        """
        生成时间流逝序列模板
        
        Args:
            location: 场景位置描述
            style: 风格预设
            time_points: 时间点列表
            
        Returns:
            提示词模板
        """
        if time_points is None:
            time_points = [
                "pre-dawn dark blue",
                "sunrise golden hour",
                "morning bright",
                "noon",
                "afternoon",
                "sunset",
                "twilight",
                "night"
            ]
        
        style_preset = self.style_presets.get(style, self.style_presets["natural"])
        
        prompts = []
        for i, time_point in enumerate(time_points):
            prompt = {
                "index": i + 1,
                "transition": "fade" if i > 0 else "fade_in",
                "prompt": (
                    f"{location}, {time_point} time of day, "
                    f"{style_preset['keywords']}, "
                    f"color palette: {style_preset['colors']}, "
                    f"{style_preset['lighting']}, "
                    "maintain same composition and framing as previous image, "
                    "only change lighting and time of day"
                )
            }
            prompts.append(prompt)
        
        template = {
            "type": "time_lapse",
            "style": style,
            "location": location,
            "total_frames": len(prompts),
            "consistency_elements": ["composition", "framing", "location"],
            "prompts": prompts
        }
        
        # 保存模板
        output_file = self.output_dir / f"time_lapse_{location.replace(' ', '_')[:30]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"时间流逝模板已保存：{output_file}")
        
        return template
    
    def generate_zoom_sequence_template(
        self,
        subject: str,
        style: str = "scifi",
        num_shots: int = 5
    ) -> Dict:
        """
        生成视角推进序列模板
        
        Args:
            subject: 拍摄主体
            style: 风格预设
            num_shots: 镜头数量
            
        Returns:
            提示词模板
        """
        style_preset = self.style_presets.get(style, self.style_presets["scifi"])
        
        # 镜头序列
        shot_types = [
            ("extreme wide shot", "entire scene visible"),
            ("wide shot", "subject and environment"),
            ("medium shot", "subject from waist up"),
            ("close up", "subject's face/details"),
            ("extreme close up", "specific detail or feature")
        ][:num_shots]
        
        prompts = []
        for i, (shot_type, description) in enumerate(shot_types):
            prompt = {
                "index": i + 1,
                "transition": "cut" if i > 0 else "fade_in",
                "shot_type": shot_type,
                "prompt": (
                    f"{shot_type} of {subject}, {description}, "
                    f"{style_preset['keywords']}, "
                    f"color palette: {style_preset['colors']}, "
                    f"{style_preset['lighting']}, "
                    "maintain consistent art style and character design"
                )
            }
            prompts.append(prompt)
        
        template = {
            "type": "zoom_sequence",
            "style": style,
            "subject": subject,
            "total_frames": len(prompts),
            "consistency_elements": ["subject design", "art style", "color grading"],
            "prompts": prompts
        }
        
        # 保存模板
        output_file = self.output_dir / f"zoom_{subject.replace(' ', '_')[:30]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"视角推进模板已保存：{output_file}")
        
        return template
    
    def generate_pan_sequence_template(
        self,
        locations: List[Dict],
        style: str = "cyberpunk"
    ) -> Dict:
        """
        生成空间移动序列模板
        
        Args:
            locations: 位置列表，每项包含{"name": "位置名", "description": "描述"}
            style: 风格预设
            
        Returns:
            提示词模板
        """
        style_preset = self.style_presets.get(style, self.style_presets["cyberpunk"])
        
        prompts = []
        for i, loc in enumerate(locations):
            prompt = {
                "index": i + 1,
                "transition": "crossfade" if i > 0 else "fade_in",
                "location": loc["name"],
                "prompt": (
                    f"{loc['name']}, {loc.get('description', '')}, "
                    f"{style_preset['keywords']}, "
                    f"color palette: {style_preset['colors']}, "
                    f"{style_preset['lighting']}, "
                    "smooth transition from previous location, "
                    "maintain consistent visual style"
                )
            }
            prompts.append(prompt)
        
        template = {
            "type": "pan_sequence",
            "style": style,
            "locations": [loc["name"] for loc in locations],
            "total_frames": len(prompts),
            "consistency_elements": ["visual style", "color grading", "lighting approach"],
            "prompts": prompts
        }
        
        # 保存模板
        output_file = self.output_dir / f"pan_sequence_{len(locations)}_locations.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"空间移动模板已保存：{output_file}")
        
        return template
    
    def generate_iterative_img2img_template(
        self,
        base_prompt: str,
        iteration_prompts: List[str],
        style: str = "cyberpunk",
        denoising_strength: float = 0.4
    ) -> Dict:
        """
        生成迭代图生图模板
        
        Args:
            base_prompt: 基础提示词（保持不变的部分）
            iteration_prompts: 每张图的变化部分
            style: 风格预设
            denoising_strength: 重绘幅度（0.3-0.5 推荐）
            
        Returns:
            提示词模板
        """
        style_preset = self.style_presets.get(style, self.style_presets["cyberpunk"])
        
        prompts = []
        for i, variation in enumerate(iteration_prompts):
            prompt = {
                "index": i + 1,
                "use_previous_as_init": True,  # 关键：使用上一张作为参考
                "denoising_strength": denoising_strength,
                "consistency_weight": 0.9 if i > 0 else 0.0,  # 除第一张外都要保持一致性
                "prompt": (
                    f"{base_prompt}, {variation}, "
                    f"{style_preset['keywords']}, "
                    f"color palette: {style_preset['colors']}, "
                    f"{style_preset['lighting']}"
                )
            }
            prompts.append(prompt)
        
        # 第一张不需要参考前一张
        if prompts:
            prompts[0]["use_previous_as_init"] = False
        
        template = {
            "type": "iterative_img2img",
            "style": style,
            "base_prompt": base_prompt,
            "denoising_strength": denoising_strength,
            "total_frames": len(prompts),
            "consistency_elements": ["base composition", "art style", "color grading"],
            "prompts": prompts
        }
        
        # 保存模板
        output_file = self.output_dir / f"iterative_{base_prompt[:30]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"迭代图生图模板已保存：{output_file}")
        
        return template
    
    def generate_custom_template(
        self,
        title: str,
        theme: str,
        scene_list: List[Dict],
        style: str = "custom"
    ) -> Dict:
        """
        生成自定义模板
        
        Args:
            title: 模板标题
            theme: 主题描述
            scene_list: 场景列表，每项包含场景详情
            style: 风格
            
        Returns:
            提示词模板
        """
        prompts = []
        for i, scene in enumerate(scene_list):
            prompt = {
                "index": i + 1,
                "scene_type": scene.get("type", "general"),
                "transition": scene.get("transition", "crossfade"),
                "prompt": scene.get("prompt", f"scene {i+1}")
            }
            prompts.append(prompt)
        
        template = {
            "type": "custom",
            "title": title,
            "theme": theme,
            "style": style,
            "total_frames": len(prompts),
            "prompts": prompts
        }
        
        # 保存模板
        output_file = self.output_dir / f"custom_{title.replace(' ', '_')[:30]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"自定义模板已保存：{output_file}")
        
        return template
    
    def load_template(self, template_file: str) -> Optional[Dict]:
        """加载已有的模板"""
        template_path = Path(template_file)
        
        if not template_path.exists():
            logger.error(f"模板文件不存在：{template_path}")
            return None
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        logger.info(f"模板已加载：{template_path}")
        
        return template
    
    def list_templates(self) -> List[Dict]:
        """列出所有可用模板"""
        templates = []
        
        for template_file in self.output_dir.glob("*.json"):
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
                templates.append({
                    "file": str(template_file),
                    "type": template.get("type", "unknown"),
                    "title": template.get("title", template_file.stem),
                    "total_frames": template.get("total_frames", 0)
                })
        
        return templates


def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="提示词模板生成器")
    parser.add_argument(
        "--type", "-t",
        choices=["time_lapse", "zoom", "pan", "iterative", "custom"],
        default="time_lapse",
        help="模板类型"
    )
    parser.add_argument(
        "--output", "-o",
        default="./hybrid_mode/prompts",
        help="输出目录"
    )
    parser.add_argument(
        "--show-templates",
        action="store_true",
        help="显示所有可用模板"
    )
    
    args = parser.parse_args()
    
    generator = PromptTemplateGenerator(output_dir=args.output)
    
    if args.show_templates:
        templates = generator.list_templates()
        print(f"\n可用模板 ({len(templates)} 个):")
        for t in templates:
            print(f"  - {t['file']}")
            print(f"    类型：{t['type']}, 帧数：{t['total_frames']}")
        return
    
    # 根据类型生成示例模板
    if args.type == "time_lapse":
        template = generator.generate_time_lapse_template(
            location="ancient temple courtyard",
            style="natural"
        )
    elif args.type == "zoom":
        template = generator.generate_zoom_sequence_template(
            subject="cyberpunk robot warrior",
            style="cyberpunk"
        )
    elif args.type == "pan":
        template = generator.generate_pan_sequence_template(
            locations=[
                {"name": "rooftop overlooking city", "description": "neon lights"},
                {"name": "busy street below", "description": "flying cars"},
                {"name": "narrow alley", "description": "street vendors"}
            ],
            style="cyberpunk"
        )
    elif args.type == "iterative":
        template = generator.generate_iterative_img2img_template(
            base_prompt="cyberpunk city street, night, rain, neon reflections",
            iteration_prompts=[
                "empty street, wide angle",
                "distant figure walking",
                "figure approaches camera",
                "close up of figure's face",
                "figure walks away, fade out"
            ],
            style="cyberpunk",
            denoising_strength=0.4
        )
    
    print(f"\n✓ 模板已生成并保存")
    print(f"  类型：{template['type']}")
    print(f"  帧数：{template['total_frames']}")
    print(f"  一致性元素：{', '.join(template['consistency_elements'])}")


if __name__ == "__main__":
    main()
