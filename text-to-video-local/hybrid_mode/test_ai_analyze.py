#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 智能分析测试示例

演示如何使用 AI 自动分析提示词并生成模板
"""

import subprocess
import json
from pathlib import Path


def test_analyze():
    """测试 AI 分析功能"""
    print("\n" + "="*70)
    print(" 测试 1: AI 智能分析提示词")
    print("="*70 + "\n")
    
    prompts = [
        "赛博朋克城市从日出到夜晚的变化，霓虹灯光",
        "cyberpunk city, neon lights, time lapse from day to night",
        "魔法师在古老城堡中施法，火焰和闪电",
        "natural landscape, mountain river, serene and peaceful",
        "恐怖鬼屋内部，黑暗诡异，幽灵出没"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n【测试 {i}/{len(prompts)}】")
        print(f"提示词：{prompt}\n")
        
        # 运行分析
        result = subprocess.run(
            [
                "python", "hybrid_mode/generate.py", "analyze",
                "-p", prompt
            ],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"错误：{result.stderr}")


def test_auto_template():
    """测试 AI 自动生成模板"""
    print("\n" + "="*70)
    print(" 测试 2: AI 自动生成模板")
    print("="*70 + "\n")
    
    test_cases = [
        {
            "prompt": "赛博朋克城市从日出到夜晚的变化，霓虹灯光，高楼大厦",
            "expected_type": "time_lapse",
            "expected_style": "cyberpunk"
        },
        {
            "prompt": "中世纪城堡，魔法师施法，火焰闪电，奇幻风格",
            "expected_type": "iterative",
            "expected_style": "fantasy"
        },
        {
            "prompt": "natural forest landscape, peaceful river, morning to night",
            "expected_type": "time_lapse",
            "expected_style": "natural"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}/{len(test_cases)}】")
        print(f"提示词：{case['prompt']}")
        print(f"预期类型：{case['expected_type']}")
        print(f"预期风格：{case['expected_style']}")
        
        output_file = Path(f"./hybrid_mode/prompts/test_auto_{i}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成模板
        result = subprocess.run(
            [
                "python", "hybrid_mode/generate.py", "template",
                "-a",  # AI 自动模式
                "-p", case['prompt'],
                "-o", str(output_file)
            ],
            capture_output=True,
            text=True
        )
        
        print("\n输出:")
        print(result.stdout)
        
        # 检查生成的模板
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            print(f"\n✓ 模板生成成功:")
            print(f"  实际类型：{template['type']}")
            print(f"  实际风格：{template['style']}")
            print(f"  帧数：{template['total_frames']}")
            
            # 验证是否符合预期
            if (template['type'] == case['expected_type'] and 
                template['style'] == case['expected_style']):
                print(f"  ✓ 匹配预期！")
            else:
                print(f"  ⚠ 与预期不符（AI 自主判断）")
        

def demo_realistic_usage():
    """演示真实使用场景"""
    print("\n" + "="*70)
    print(" 演示：真实使用场景")
    print("="*70 + "\n")
    
    print("场景：用户想制作一个赛博朋克城市的延时摄影视频\n")
    
    # 步骤 1: AI 分析
    print("【步骤 1】AI 分析提示词")
    result1 = subprocess.run(
        [
            "python", "hybrid_mode/generate.py", "analyze",
            "-p", "cyberpunk city street, night to dawn, neon lights reflecting on wet pavement, futuristic buildings"
        ],
        capture_output=True,
        text=True
    )
    print(result1.stdout)
    
    # 步骤 2: AI 生成模板
    print("\n【步骤 2】AI 自动生成模板")
    result2 = subprocess.run(
        [
            "python", "hybrid_mode/generate.py", "template",
            "-a",
            "-p", "cyberpunk city street, night to dawn, neon lights reflecting on wet pavement, futuristic buildings",
            "-o", "./hybrid_mode/prompts/demo_cyberpunk_timelapse.json"
        ],
        capture_output=True,
        text=True
    )
    print(result2.stdout)
    
    print("\n✓ 演示完成！用户现在可以:")
    print("  1. 查看生成的模板文件")
    print("  2. 根据提示词去云端生成图片")
    print("  3. 用 synthesize 命令合成视频")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" AI 智能分析功能测试")
    print("="*70)
    
    # 运行测试
    test_analyze()
    test_auto_template()
    demo_realistic_usage()
    
    print("\n" + "="*70)
    print(" 所有测试完成！")
    print("="*70 + "\n")
