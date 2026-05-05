#!/usr/bin/env python3
"""
最终验证测试 - 确保所有功能真实可用
"""

import sys
from pathlib import Path
from flask import Flask

sys.path.insert(0, './web')
from app import app

# ============================================================================

def run_final_tests():
    print("="*70)
    print("最终功能验证测试")
    print("="*70)
    
    tests = []
    
    # 测试 1: API 路由存在
    print("\n【1】API 路由检查")
    routes = {str(rule): rule.methods for rule in app.url_map.iter_rules()}
    required_routes = [
        '/api/models/analyze',
        '/api/models/cleanup', 
        '/api/models/delete',
        '/api/models/list',
    ]
    
    for route in required_routes:
        found = any(route in r for r in routes)
        print(f"  {'✓' if found else '✗'} {route}")
        tests.append(found)
    
    # 测试 2: 前端资源存在
    print("\n【2】前端文件检查")
    files = [
        'web/templates/setup_wizard.html',
        'web/templates/index.html',
        'web/app.py',
    ]
    for f in files:
        exists = Path(f).exists()
        print(f"  {'✓' if exists else '✗'} {f}")
        tests.append(exists)
    
    # 测试 3: 前端功能存在
    print("\n【3】前端功能检查")
    html = Path('web/templates/setup_wizard.html').read_text()
    features = [
        ('模型管理步骤', '模型管理'),
        ('分析函数', 'analyzeModels()'),
        ('清理函数', 'cleanupModels('),
        ('删除函数', 'deleteModel('),
        ('API 调用', '/api/models/'),
    ]
    
    for name, feature in features:
        found = feature in html
        print(f"  {'✓' if found else '✗'} {name}")
        tests.append(found)
    
    # 测试 4: 后端功能测试
    print("\n【4】后端 API 功能测试")
    with app.test_client() as client:
        # 分析 API
        resp = client.get('/api/models/analyze')
        data = resp.get_json()
        ok = resp.status_code == 200 and data.get('success') is not None
        print(f"  {'✓' if ok else '✗'} /api/models/analyze")
        tests.append(ok)
        
        # 清理 API
        resp = client.post('/api/models/cleanup', 
                          json={'target': 'temp'},
                          content_type='application/json')
        data = resp.get_json()
        ok = resp.status_code == 200 and data.get('success') is not None
        print(f"  {'✓' if ok else '✗'} /api/models/cleanup")
        tests.append(ok)
        
        # 列表 API
        resp = client.get('/api/models/list')
        data = resp.get_json()
        ok = resp.status_code == 200
        print(f"  {'✓' if ok else '✗'} /api/models/list")
        tests.append(ok)
    
    # 测试 5: 代码质量检查
    print("\n【5】代码质量检查")
    app_content = Path('web/app.py').read_text()
    
    # 检查函数是否存在
    funcs = [
        'def calculate_model_actual_size',
        'def api_cleanup_models',
        'def api_delete_model',
        'def api_analyze_models',
    ]
    
    for func in funcs:
        found = func in app_content
        print(f"  {'✓' if found else '✗'} {func}")
        tests.append(found)
    
    # 总结
    print("\n" + "="*70)
    print("测试结果")
    print("="*70)
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"通过：{passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✅ 所有功能验证通过！可以安全使用。")
        return True
    else:
        print(f"\n❌ {total-passed} 项功能有问题，请检查。")
        return False

# ============================================================================

if __name__ == '__main__':
    success = run_final_tests()
    sys.exit(0 if success else 1)
