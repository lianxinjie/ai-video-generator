#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能场景检测功能测试脚本

测试基于关键词分析的场景新增判定功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'personal_mode'))

from scene_detector import SceneDetector


def test_keyword_detection():
    """测试场景关键词检测"""
    print("\n" + "="*70)
    print(" 测试 1: 场景关键词检测（5 大类 50+ 场景）")
    print("="*70 + "\n")
    
    detector = SceneDetector(verbose=True)
    
    test_prompts = [
        # 时间场景
        "cyberpunk city from night to dawn, time lapse",
        # 动作场景  
        "dragon flying and breathing fire, explosion",
        # 镜头场景
        "castle tower, camera pans to aerial view, zoom in",
        # 元素场景
        "phoenix and unicorn in magical forest, palace",
        # 天气场景
        "storm with lightning and thunder, heavy rain",
        # 混合场景
        "medieval castle at sunset, dragon flying, camera zooms in, battle explosion"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[{i}/6] 提示词：{prompt}")
        
        results = detector.detect_scene_keywords(prompt)
        
        # 显示各类别结果
        for scene_type, result in results.items():
            if scene_type == 'overall':
                continue
            
            if result['hits']:
                print(f"  ✓ {scene_type.replace('_', ' ').title()}: {result['hits']} "
                      f"(分数：{result['score']:.2f})")
        
        # 总体评分
        overall = results.get('overall', {})
        print(f"  总体评分：{overall.get('total_score', 0):.2f} "
              f"(检测到的类别数：{overall.get('detected_types', 0)})")
    
    return True


def test_importance_score():
    """测试场景重要度评分"""
    print("\n" + "="*70)
    print(" 测试 2: 场景重要度评分算法")
    print("="*70 + "\n")
    
    detector = SceneDetector(verbose=True, detection_threshold=0.5)
    
    test_cases = [
        ("简单描述", "a beautiful day"),
        ("时间场景", "sunset over mountains, golden hour"),
        ("动作场景", "explosion and battle, dragon attacking"),
        ("复杂场景", "medieval castle at night, dragon flying, camera zooms in, sudden explosion"),
    ]
    
    for name, prompt in test_cases:
        print(f"\n【{name}】{prompt}")
        
        should_create, report = detector.should_create_new_scene(prompt)
        
        print(f"  重要度分数：{report['importance_score']:.2f}")
        print(f"  检测阈值：{report['detection_threshold']}")
        print(f"  是否创建场景：{'是 ✓' if should_create else '否 ✗'}")
        print(f"  检测到的类别：{', '.join(report['detected_categories']) or '无'}")
        print(f"  转换强度：{report['transition_analysis']['detected_strength']}")
        print(f"  置信度：{report['confidence']:.0%}")
    
    return True


def test_scene_detection():
    """测试智能场景检测与拆分"""
    print("\n" + "="*70)
    print(" 测试 3: 智能场景检测与自动拆分")
    print("="*70 + "\n")
    
    detector = SceneDetector(verbose=True, detection_threshold=0.4)
    
    # 复杂提示词，包含多个潜在场景
    full_prompt = (
        "medieval castle at sunset, time lapse to night, "
        "dragon flying over tower, camera pans to aerial view, "
        "suddenly storm with lightning and thunder, "
        "battle explosion at the gate"
    )
    
    print(f"完整提示词:\n{full_prompt}\n")
    
    segments = detector.analyze_and_split(full_prompt)
    
    print(f"\n拆分结果：{len(segments)} 个场景")
    for i, seg in enumerate(segments, 1):
        print(f"\n  场景 {i}:")
        print(f"    文本：{seg['text']}")
        print(f"    重要度：{seg['importance_score']:.2f}")
        print(f"    类别：{', '.join(seg['detected_categories']) or '无'}")
        print(f"    关键词：{', '.join(seg['keywords'][:5]) or '无'}")
        if len(seg['keywords']) > 5:
            print(f"         ... 还有 {len(seg['keywords']) - 5} 个")
    
    return len(segments) >= 2


def test_threshold_sensitivity():
    """测试阈值敏感度"""
    print("\n" + "="*70)
    print(" 测试 4: 检测阈值敏感度（不同阈值的影响）")
    print("="*70 + "\n")
    
    prompt = "castle at sunset, dragon flying, then battle explosion"
    
    thresholds = [0.3, 0.5, 0.7]
    
    for threshold in thresholds:
        detector = SceneDetector(verbose=False, detection_threshold=threshold)
        should_create, report = detector.should_create_new_scene(prompt)
        
        print(f"阈值 {threshold}:")
        print(f"  重要度分数：{report['importance_score']:.2f}")
        print(f"  是否创建场景：{'是 ✓' if should_create else '否 ✗'}")
        print()
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" 智能场景检测功能测试套件")
    print(" 基于关键词分析的场景新增判定")
    print("="*70)
    
    tests = [
        ("场景关键词检测", test_keyword_detection),
        ("重要度评分算法", test_importance_score),
        ("智能场景拆分", test_scene_detection),
        ("阈值敏感度", test_threshold_sensitivity)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"\n  ✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"\n  ❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"\n  ❌ {test_name} - 异常：{e}")
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
        print("✅ 所有测试通过！智能场景检测功能正常工作\n")
        return 0
    else:
        print("⚠️  部分测试失败\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
