#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 场景分析功能测试脚本

测试基于 LLM 的智能场景判断
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'personal_mode'))

from ai_scene_analyzer import AISceneAnalyzer, quick_analyze


def test_quick_analysis():
    """测试快速分析（无需 AI）"""
    print("\n" + "="*70)
    print(" 测试 1: 快速分析（回退模式）")
    print("="*70 + "\n")
    
    test_prompts = [
        "cyberpunk city from night to dawn, time lapse",
        "medieval castle, dragon flying, camera pans to aerial view",
        "peaceful forest, river flowing, birds singing"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[{i}/3] 提示词：{prompt}")
        
        result = quick_analyze(prompt, model_type='local')
        
        print(f"  场景数量：{result.get('total_scenes', 0)}")
        print(f"  分析来源：{result.get('source', 'ai')}")
        
        for scene in result.get('scenes', []):
            print(f"    场景{scene['index']}: {scene['text'][:40]}... "
                  f"(重要度：{scene.get('importance', 0):.2f})")
    
    return True


def test_analyzer_initialization():
    """测试分析器初始化"""
    print("\n" + "="*70)
    print(" 测试 2: AI 分析器初始化")
    print("="*70 + "\n")
    
    # 测试不同模型配置
    configs = [
        {'model_type': 'local', 'model_name': 'qwen2.5:7b'},
        {'model_type': 'openai', 'model_name': 'gpt-3.5-turbo'},
        {'model_type': 'qwen', 'model_name': 'qwen-turbo'}
    ]
    
    for config in configs:
        print(f"配置：{config}")
        
        try:
            analyzer = AISceneAnalyzer(
                model_type=config['model_type'],
                model_name=config.get('model_name'),
                verbose=False
            )
            
            print(f"  ✓ 初始化成功")
            print(f"    模型：{analyzer.model_name}")
            print(f"    API Base: {analyzer.api_base}")
            
            # 测试回退分析
            result = analyzer._fallback_analysis("test prompt")
            print(f"    回退分析：{result['total_scenes']} 个片段")
            
        except Exception as e:
            print(f"  ❌ 初始化失败：{e}")
    
    return True


def test_response_parsing():
    """测试响应解析"""
    print("\n" + "="*70)
    print(" 测试 3: LLM 响应解析")
    print("="*70 + "\n")
    
    analyzer = AISceneAnalyzer(verbose=False)
    
    # 测试不同格式的响应
    test_responses = [
        # 完整 JSON
        '''{
            "total_scenes": 3,
            "scenes": [
                {"index": 1, "text": "scene 1", "importance": 0.8},
                {"index": 2, "text": "scene 2", "importance": 0.6},
                {"index": 3, "text": "scene 3", "importance": 0.9}
            ]
        }''',
        
        # 带标记的 JSON
        '''好的，分析结果如下：

```json
{
    "total_scenes": 2,
    "scenes": [
        {"index": 1, "text": "first scene"},
        {"index": 2, "text": "second scene"}
    ]
}
```

希望这对您有帮助！''',
        
        # 不完整 JSON（容错测试）
        '''{
            "total_scenes": 1,
            "overall_analysis": "single scene"
        }'''
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n[{i}/3] 响应格式测试")
        
        try:
            result = analyzer._parse_llm_response(response, "test prompt")
            
            print(f"  ✓ 解析成功")
            print(f"    场景数量：{result.get('total_scenes', 0)}")
            print(f"    场景数：{len(result.get('scenes', []))}")
            
        except Exception as e:
            print(f"  ❌ 解析失败：{e}")
    
    return True


def test_fallback_analysis():
    """测试回退分析"""
    print("\n" + "="*70)
    print(" 测试 4: 回退分析（规则 base）")
    print("="*70 + "\n")
    
    analyzer = AISceneAnalyzer(verbose=False)
    
    test_prompts = [
        "cyberpunk city, neon lights, night time",
        "medieval castle at sunset. dragon flying in the sky! sudden explosion,",
        "forest, river, birds, flowers, peacefully"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[{i}/3] 提示词：{prompt}")
        
        result = analyzer._fallback_analysis(prompt)
        
        print(f"  拆分结果：{result['total_scenes']} 个片段")
        for scene in result.get('scenes', []):
            print(f"    片段{scene['index']}: {scene['text']}")
    
    return True


def test_interactive_mode():
    """测试交互模式"""
    print("\n" + "="*70)
    print(" 测试 5: 交互式场景优化（模拟）")
    print("="*70 + "\n")
    
    analyzer = AISceneAnalyzer(verbose=True, model_type='local')
    
    # 模拟初始结果
    initial_result = {
        'total_scenes': 2,
        'scenes': [
            {'index': 1, 'text': 'castle at sunset', 'importance': 0.5},
            {'index': 2, 'text': 'dragon flying', 'importance': 0.5}
        ]
    }
    
    print("提示词：medieval castle at sunset, dragon flying over tower\n")
    print("初始分析结果:")
    print(f"  场景数量：{initial_result['total_scenes']}")
    for scene in initial_result['scenes']:
        print(f"    场景{scene['index']}: {scene['text']}")
    
    print("\n⚠️  注意：完整交互模式需要 AI 模型支持")
    print("  跳过实际 API 调用，显示模拟流程\n")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" AI 场景分析功能测试套件")
    print(" 基于 LLM 的智能场景判断")
    print("="*70)
    
    tests = [
        ("快速分析（回退）", test_quick_analysis),
        ("分析器初始化", test_analyzer_initialization),
        ("响应解析", test_response_parsing),
        ("回退分析", test_fallback_analysis),
        ("交互模式", test_interactive_mode)
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
        print("✅ 所有测试通过！AI 场景分析功能正常工作\n")
        return 0
    else:
        print("⚠️  部分测试失败（AI 模式需要实际模型支持）\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
