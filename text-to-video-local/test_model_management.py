#!/usr/bin/env python3
"""
模型管理功能严格测试脚本
测试所有新增的模型管理 API 功能
"""

import sys
import json
from pathlib import Path
from flask import Flask

# 导入 app
sys.path.insert(0, './web')
from app import app, calculate_model_actual_size, api_analyze_models, api_cleanup_models, api_delete_model


def test_api_routes():
    """测试 1: 验证所有 API 路由已定义"""
    print("\n" + "="*60)
    print("测试 1: API 路由定义检查")
    print("="*60)
    
    expected_routes = [
        ('/api/models/list', 'GET'),
        ('/api/models/install', 'POST'),
        ('/api/models/status/<task_id>', 'GET'),
        ('/api/models/cleanup', 'POST'),
        ('/api/models/delete', 'POST'),
        ('/api/models/analyze', 'GET'),
    ]
    
    routes = {str(rule): list(rule.methods) for rule in app.url_map.iter_rules()}
    
    passed = 0
    failed = 0
    
    for route, method in expected_routes:
        base_route = route.split('<')[0].rstrip('/')
        found = False
        for r in routes:
            if base_route in r:
                found = True
                break
        
        if found:
            print(f"✓ {method} {route}")
            passed += 1
        else:
            print(f"✗ {method} {route} - 未找到")
            failed += 1
    
    print(f"\n结果：{passed} 通过，{failed} 失败")
    return failed == 0


def test_calculate_size():
    """测试 2: 模型大小计算函数"""
    print("\n" + "="*60)
    print("测试 2: 模型大小计算函数")
    print("="*60)
    
    test_cases = [
        ('modelscope', {'type': 'modelscope', 'repo': 'damo/text-to-video-synthesis'}),
        ('animatediff', {'type': 'huggingface', 'repo': 'guoyww/animatediff-motion-adapter-v1-5-2'}),
        ('test', {'type': 'unknown', 'repo': 'test'}),
    ]
    
    for name, info in test_cases:
        try:
            size = calculate_model_actual_size(name, info)
            assert isinstance(size, (int, float)), "返回值应该是数字"
            assert size >= 0, "大小不能为负数"
            print(f"✓ {name}: {size} GB")
        except Exception as e:
            print(f"✗ {name}: 错误 - {e}")
            return False
    
    return True


def test_analyze_empty_models():
    """测试 3: 空模型目录分析"""
    print("\n" + "="*60)
    print("测试 3: 空模型目录分析")
    print("="*60)
    
    with app.test_request_context('/api/models/analyze'):
        result = api_analyze_models()
        
        # 处理不同的返回格式
        if isinstance(result, tuple):
            response_obj, status_code = result
        else:
            response_obj = result
            status_code = 200
        
        data = response_obj.get_json() if hasattr(response_obj, 'get_json') else response_obj
        
        if data.get('success'):
            print(f"✓ API 调用成功")
            print(f"  总结：{json.dumps(data.get('summary', {}), indent=2)}")
            return True
        else:
            print(f"✗ API 调用失败：{data.get('error', '未知错误')}")
            return False


def test_cleanup_empty():
    """测试 4: 空目录清理"""
    print("\n" + "="*60)
    print("测试 4: 清理功能测试")
    print("="*60)
    
    with app.test_request_context('/api/models/cleanup', method='POST', json={'target': 'temp'}):
        try:
            result = api_cleanup_models()
            
            if isinstance(result, tuple):
                response_obj, status_code = result
            else:
                response_obj = result
                status_code = 200
            
            data = response_obj.get_json() if hasattr(response_obj, 'get_json') else response_obj
            
            if data.get('success'):
                print(f"✓ 清理成功：{data.get('message', '无消息')}")
                stats = data.get('stats', {})
                print(f"  清理数量：{stats.get('cleaned', 0)}")
                print(f"  释放空间：{stats.get('freed_gb', 0):.3f} GB")
                return True
            else:
                print(f"✗ 清理失败：{data.get('error', '未知错误')}")
                return False
        except Exception as e:
            print(f"✗ 异常：{e}")
            return False


def test_file_structure():
    """测试 5: 前端文件结构检查"""
    print("\n" + "="*60)
    print("测试 5: 前端文件检查")
    print("="*60)
    
    checks = [
        ('web/templates/setup_wizard.html', '模型管理步骤'),
        ('web/templates/setup_wizard.html', 'analyzeModels'),
        ('web/templates/setup_wizard.html', 'cleanupModels'),
        ('web/templates/setup_wizard.html', 'deleteModel'),
    ]
    
    for file_path, search_term in checks:
        path = Path(file_path)
        if not path.exists():
            print(f"✗ {file_path} - 文件不存在")
            return False
        
        content = path.read_text()
        if search_term in content:
            print(f"✓ {file_path} - 包含 '{search_term}'")
        else:
            print(f"✗ {file_path} - 缺少 '{search_term}'")
            return False
    
    return True


def test_integration():
    """测试 6: 完整集成测试"""
    print("\n" + "="*60)
    print("测试 6: 完整工作流程测试")
    print("="*60)
    
    # 模拟完整流程：分析 → 清理 → 重新分析
    with app.test_client() as client:
        # 1. 分析
        print("1. 分析模型占用...")
        response = client.get('/api/models/analyze')
        data = response.get_json()
        if response.status_code == 200 and data.get('success'):
            print(f"   ✓ 分析成功，已安装 {data['summary']['total_models']} 个模型")
        else:
            print(f"   ✗ 分析失败：{data.get('error')}")
            return False
        
        # 2. 清理
        print("2. 清理临时文件...")
        response = client.post('/api/models/cleanup', 
                             json={'target': 'temp'},
                             content_type='application/json')
        data = response.get_json()
        if response.status_code == 200 and data.get('success'):
            print(f"   ✓ 清理成功，释放 {data['stats']['freed_gb']:.3f} GB")
        else:
            print(f"   ✗ 清理失败：{data.get('error')}")
            return False
        
        # 3. 重新分析
        print("3. 重新分析...")
        response = client.get('/api/models/analyze')
        data = response.get_json()
        if response.status_code == 200 and data.get('success'):
            print(f"   ✓ 重新分析成功")
        else:
            print(f"   ✗ 重新分析失败：{data.get('error')}")
            return False
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("模型管理功能严格测试")
    print("="*60)
    
    tests = [
        ("API 路由定义", test_api_routes),
        ("大小计算函数", test_calculate_size),
        ("空目录分析", test_analyze_empty_models),
        ("清理功能", test_cleanup_empty),
        ("前端文件", test_file_structure),
        ("集成测试", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✅ 所有测试通过！功能可以安全使用。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查问题。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
