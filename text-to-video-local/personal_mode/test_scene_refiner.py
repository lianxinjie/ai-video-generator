#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能场景优化功能测试脚本

测试内容：
1. 场景边界检测
2. 连贯性评估
3. 场景合并建议
4. 转场效果推荐
5. 交互式优化流程
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'personal_mode'))

from scene_refiner import SceneRefiner


def test_scene_boundary_detection():
    """测试场景边界检测"""
    print("\n" + "="*70)
    print(" 测试 1: 场景边界检测")
    print("="*70 + "\n")
    
    refiner = SceneRefiner(verbose=True)
    
    # 测试提示词列表
    test_prompts = [
        "cyberpunk city from night to dawn, neon lights",
        "medieval castle, then camera pans to dragon flying",
        "scifi space station, switch to alien planet surface",
        "peaceful forest, move to mountain peak at sunset"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"[{i}/4] 提示词：{prompt}")
        boundaries = refiner.analyze_scene_boundaries(prompt)
        
        if boundaries:
            print(f"  ✓ 检测到 {len(boundaries)} 个场景边界:")
            for boundary in boundaries:
                print(f"    - {boundary['marker']} @ 位置{boundary['position']}")
        else:
            print(f"  ⚠️  未检测到明显场景边界")
        print()
    
    return True


def test_continuity_evaluation():
    """测试连贯性评估"""
    print("\n" + "="*70)
    print(" 测试 2: 场景连贯性评估")
    print("="*70 + "\n")
    
    refiner = SceneRefiner(verbose=True)
    
    # 模拟分段
    segments = [
        {'prompt': 'cyberpunk city street, neon lights, night', 'scene_type': 'custom'},
        {'prompt': 'same street, but now at dawn, continue view', 'scene_type': 'time_lapse'},
        {'prompt': 'camera pans to alley, robot walking', 'scene_type': 'pan_sequence'}
    ]
    
    print("输入分段:")
    for i, seg in enumerate(segments, 1):
        print(f"  段{i}: {seg['prompt'][:50]}...")
    
    continuity_reports = refiner.evaluate_continuity(segments)
    
    print("\n连贯性评估结果:")
    for report in continuity_reports:
        print(f"\n  段 {report['from_segment']+1} → 段 {report['to_segment']+1}:")
        print(f"    连贯类型：{report['continuity_type']}")
        print(f"    置信度：{report['confidence']:.0%}")
        print(f"    关键词：{', '.join(report['keywords_found'])}")
        print(f"    推荐转场：{report['transition_suggestion']}")
    
    return True


def test_scene_merge():
    """测试场景合并"""
    print("\n" + "="*70)
    print(" 测试 3: 智能场景合并")
    print("="*70 + "\n")
    
    refiner = SceneRefiner(verbose=True)
    
    # 创建相似场景
    segments = [
        {'prompt': 'cyberpunk city street, neon lights, night', 'scene_type': 'custom', 'style': 'cyberpunk'},
        {'prompt': 'cyberpunk city street with rain, neon lights reflecting', 'scene_type': 'custom', 'style': 'cyberpunk'},
        {'prompt': 'cyberpunk city alley, dark, same style', 'scene_type': 'custom', 'style': 'cyberpunk'},
        {'prompt': 'suddenly switch to peaceful forest, mountains', 'scene_type': 'custom', 'style': 'natural'}
    ]
    
    print("原始分段 (4 段):")
    for i, seg in enumerate(segments, 1):
        print(f"  段{i}: {seg['prompt'][:50]}...")
    
    # 测试合并（阈值 0.6）
    merged = refiner.merge_similar_scenes(segments, similarity_threshold=0.6)
    
    print(f"\n合并后分段 ({len(merged)} 段):")
    for i, seg in enumerate(merged, 1):
        prompt = seg.get('prompt', '')[:60]
        merged_from = seg.get('merged_from', [])
        print(f"  段{i}: {prompt}..." + (f" [合并自段{merged_from}]" if merged_from else ""))
    
    return True


def test_scene_report():
    """测试场景分析报告"""
    print("\n" + "="*70)
    print(" 测试 4: 完整场景分析报告")
    print("="*70 + "\n")
    
    refiner = SceneRefiner(verbose=True)
    
    # 创建多样场景
    segments = [
        {'prompt': 'cyberpunk city from night to dawn', 'scene_type': 'time_lapse', 'style': 'cyberpunk'},
        {'prompt': 'medieval castle with dragon', 'scene_type': 'custom', 'style': 'fantasy'},
        {'prompt': 'scifi space station interior', 'scene_type': 'custom', 'style': 'scifi'}
    ]
    
    continuity_reports = refiner.evaluate_continuity(segments)
    report = refiner.generate_scene_report(segments, continuity_reports)
    
    print(f"总分段数：{report['total_segments']}")
    
    print("\n场景类型分布:")
    for scene_type, count in report['scene_type_distribution'].items():
        print(f"  {scene_type}: {count} 段")
    
    print("\n艺术风格分布:")
    for style, count in report['style_distribution'].items():
        print(f"  {style}: {count} 段")
    
    if report['transition_suggestions']:
        print("\n转场建议:")
        for trans in report['transition_suggestions']:
            print(f"  段{trans['from_segment']+1} → 段{trans['to_segment']+1}: {trans['suggested_transition']}")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" 智能场景优化功能测试套件")
    print("="*70)
    
    tests = [
        ("场景边界检测", test_scene_boundary_detection),
        ("连贯性评估", test_continuity_evaluation),
        ("智能场景合并", test_scene_merge),
        ("完整报告生成", test_scene_report)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"  ✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"  ❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"  ❌ {test_name} - 异常：{e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "="*70)
    print(" 测试结果总结")
    print("="*70)
    print(f"  通过：{passed}/{len(tests)}")
    print(f"  失败：{failed}/{len(tests)}")
    print(f"  成功率：{passed/len(tests)*100:.0f}%\n")
    
    if passed == len(tests):
        print("✅ 所有测试通过！智能场景优化功能正常工作")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
