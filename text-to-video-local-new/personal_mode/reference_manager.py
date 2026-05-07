#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参考图片管理器 - 支持人物卡和背景图

功能：
1. 加载单张参考图（人物卡/背景图）
2. 加载多张参考图（多视角人物卡/背景图集合）
3. 生成参考图特征（用于 image-to-image）
4. 提供参考图路径给生成流程
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from PIL import Image
import numpy as np


class ReferenceImageManager:
    """参考图片管理器"""
    
    def __init__(self, verbose: bool = True):
        """
        初始化参考图片管理器
        
        Args:
            verbose: 是否显示详细信息
        """
        self.verbose = verbose
        self.reference_images: List[str] = []
        self.reference_type: str = 'character'
        self.reference_strength: float = 0.6
        self.image_features: Dict = {}
    
    def load_reference(self, ref_path: Union[str, Path], 
                       ref_type: str = 'character',
                       ref_strength: float = 0.6) -> bool:
        """
        加载参考图片
        
        Args:
            ref_path: 参考图片路径（单张图片或目录）
            ref_type: 参考图类型 (character/background/mixed)
            ref_strength: 参考图强度 (0.0-1.0)
        
        Returns:
            是否加载成功
        """
        ref_path = Path(ref_path)
        
        if not ref_path.exists():
            if self.verbose:
                print(f"  ✗ 参考图片路径不存在：{ref_path}")
            return False
        
        self.reference_type = ref_type
        self.reference_strength = max(0.0, min(1.0, ref_strength))
        
        # 单张图片
        if ref_path.is_file():
            if ref_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                self.reference_images.append(str(ref_path))
                if self.verbose:
                    print(f"  ✓ 加载参考图片：{ref_path}")
            else:
                if self.verbose:
                    print(f"  ✗ 不支持的图片格式：{ref_path}")
                return False
        
        # 目录：加载所有图片
        elif ref_path.is_dir():
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(ref_path.glob(f'*{ext}'))
                image_files.extend(ref_path.glob(f'*{ext.upper()}'))
            
            if image_files:
                self.reference_images = [str(f) for f in sorted(image_files)]
                if self.verbose:
                    print(f"  ✓ 从目录加载 {len(self.reference_images)} 张参考图片：{ref_path}")
                    for i, img_path in enumerate(self.reference_images[:5], 1):
                        print(f"    [{i}] {Path(img_path).name}")
                    if len(self.reference_images) > 5:
                        print(f"    ... 还有 {len(self.reference_images) - 5} 张")
            else:
                if self.verbose:
                    print(f"  ✗ 目录中没有找到图片：{ref_path}")
                return False
        
        # 提取特征
        self._extract_features()
        
        return len(self.reference_images) > 0
    
    def _extract_features(self):
        """提取参考图特征"""
        if not self.reference_images:
            return
        
        self.image_features = {
            'count': len(self.reference_images),
            'type': self.reference_type,
            'strength': self.reference_strength,
            'sizes': [],
            'aspect_ratios': []
        }
        
        # 读取第一张图片获取尺寸信息
        try:
            with Image.open(self.reference_images[0]) as img:
                width, height = img.size
                self.image_features['primary_size'] = f"{width}x{height}"
                self.image_features['primary_aspect'] = width / height if height > 0 else 1.0
        except Exception as e:
            if self.verbose:
                print(f"  ⚠ 读取图片尺寸失败：{e}")
        
        if self.verbose:
            print(f"\n【参考图特征】")
            print(f"  类型：{self.reference_type}")
            print(f"  数量：{len(self.reference_images)} 张")
            print(f"  强度：{self.reference_strength:.1f}")
            if 'primary_size' in self.image_features:
                print(f"  尺寸：{self.image_features['primary_size']}")
    
    def get_reference_images(self) -> List[str]:
        """获取参考图片列表"""
        return self.reference_images
    
    def get_config(self) -> Dict:
        """获取参考图配置"""
        return {
            'enabled': len(self.reference_images) > 0,
            'paths': self.reference_images,
            'type': self.reference_type,
            'strength': self.reference_strength,
            'features': self.image_features
        }
    
    def generate_prompt_with_reference(self, base_prompt: str) -> str:
        """
        基于参考图生成增强提示词
        
        Args:
            base_prompt: 基础提示词
        
        Returns:
            增强后的提示词
        """
        if not self.reference_images:
            return base_prompt
        
        # 根据参考图类型添加描述
        type_prompts = {
            'character': "consistent character design, high quality reference sheet",
            'background': "detailed background, consistent environment design",
            'mixed': "consistent character and background design, high quality"
        }
        
        suffix = type_prompts.get(self.reference_type, '')
        
        if suffix:
            return f"{base_prompt}, {suffix}"
        
        return base_prompt
    
    def get_generation_params(self) -> Dict:
        """
        获取生成参数（用于 image-to-image）
        
        Returns:
            生成参数字典
        """
        return {
            'reference_images': self.reference_images,
            'reference_type': self.reference_type,
            'reference_strength': self.reference_strength,
            'image_guidance_scale': 1.5 + (self.reference_strength * 2),  # 0.6 -> 2.7
        }


def test_reference_manager():
    """测试参考图片管理器"""
    print("=" * 70)
    print("参考图片管理器测试")
    print("=" * 70)
    
    manager = ReferenceImageManager(verbose=True)
    
    # 测试 1：加载单张图片
    print("\n【测试 1】加载单张参考图")
    test_image = Path("test_character.png")
    if test_image.exists():
        manager.load_reference(test_image, ref_type='character', ref_strength=0.7)
    else:
        print(f"  ⚠ 测试图片不存在：{test_image}")
    
    # 测试 2：加载目录
    print("\n【测试 2】加载目录中的参考图")
    test_dir = Path("./reference_images")
    if test_dir.exists():
        manager.load_reference(test_dir, ref_type='background', ref_strength=0.5)
    else:
        print(f"  ⚠ 测试目录不存在：{test_dir}")
    
    # 测试 3：获取配置
    print("\n【测试 3】获取参考图配置")
    config = manager.get_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    # 测试 4：增强提示词
    print("\n【测试 4】增强提示词")
    base_prompt = "一个勇敢的骑士在城堡中战斗"
    enhanced = manager.generate_prompt_with_reference(base_prompt)
    print(f"  原提示词：{base_prompt}")
    print(f"  增强后：{enhanced}")
    
    # 测试 5：生成参数
    print("\n【测试 5】生成参数")
    params = manager.get_generation_params()
    print(f"  参考图数量：{len(params.get('reference_images', []))}")
    print(f"  参考图强度：{params.get('reference_strength')}")
    print(f"  图像引导比例：{params.get('image_guidance_scale')}")


if __name__ == "__main__":
    test_reference_manager()
