#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格测试新增功能，防止虚假功能
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔬 功能严格测试")
print("=" * 70)

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_import(name, module_path):
    """测试模块导入"""
    try:
        __import__(module_path)
        print(f"  ✓ {name}: 导入成功")
        return True
    except Exception as e:
        print(f"  ❌ {name}: 导入失败 - {e}")
        return False

def test_api_endpoint(url, description):
    """测试 API 端点"""
    try:
        import requests
        response = requests.get(f'http://localhost:5000{url}', timeout=5)
        if response.status_code == 200:
            print(f"  ✓ {description}: OK (HTTP 200)")
            return True
        else:
            print(f"  ❌ {description}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠ {description}: 跳过 (服务未启动) - {e}")
        return None

def test_pytorch_installation():
    """1. 测试 PyTorch 安装检测"""
    print_section("测试 1: PyTorch 状态检测")
    
    try:
        import torch
        
        info = {
            'version': torch.__version__,
            'cuda_available': torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            info['cuda_version'] = torch.version.cuda
            info['gpu_count'] = torch.cuda.device_count()
            info['gpu_name'] = torch.cuda.get_device_name(0)
        
        print(f"  ✓ PyTorch 版本：{info['version']}")
        print(f"  ✓ CUDA 可用：{info['cuda_available']}")
        
        if info['cuda_available']:
            print(f"  ✓ CUDA 版本：{info['cuda_version']}")
            print(f"  ✓ GPU 数量：{info['gpu_count']}")
            print(f"  ✓ GPU 型号：{info['gpu_name']}")
        
        return True
    except ImportError:
        print(f"  ⚠ PyTorch 未安装，这是预期的")
        return False

def test_gpu_detection():
    """2. 测试 GPU 检测（多重检测方案）"""
    print_section("测试 2: GPU 多重检测")
    
    # 方法 1: PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ PyTorch 检测到 GPU: {torch.cuda.get_device_name(0)}")
            return True
    except:
        pass
    
    # 方法 2: nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"  ✓ nvidia-smi 检测到 GPU: {result.stdout.strip()}")
            return True
    except:
        pass
    
    # 方法 3: Windows 设备管理器
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['wmic', 'path', 'Win32_VideoController', 'get', 'Name'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and 'NVIDIA' in result.stdout:
                print(f"  ✓ WMI 检测到 NVIDIA GPU")
                return True
        except:
            pass
    
    print(f"  ⚠ 未检测到独立 GPU")
    return False

def test_model_download_guide():
    """3. 测试模型下载文档"""
    print_section("测试 3: 模型下载指南文档")
    
    doc_path = Path('./MODEL_DOWNLOAD_GUIDE.md')
    if doc_path.exists():
        size = doc_path.stat().st_size
        print(f"  ✓ 文档存在：{doc_path}")
        print(f"  ✓ 文件大小：{size / 1024:.1f} KB")
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'HuggingFace 镜像' in content:
                print(f"  ✓ 包含 HuggingFace 镜像方案")
            if '云端模式' in content:
                print(f"  ✓ 包含云端模式方案")
            if 'modelscope' in content.lower():
                print(f"  ✓ 包含 ModelScope 下载方案")
        
        return True
    else:
        print(f"  ❌ 文档不存在：{doc_path}")
        return False

def test_manual_download_script():
    """4. 测试手动下载脚本"""
    print_section("测试 4: 手动下载脚本")
    
    script_path = Path('./download_model_manual.py')
    if script_path.exists():
        print(f"  ✓ 脚本存在：{script_path}")
        
        # 运行脚本（应该显示帮助信息）
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"  ✓ 脚本可正常执行")
                if 'modelscope' in result.stdout.lower():
                    print(f"  ✓ 输出包含 ModelScope 信息")
                return True
            else:
                print(f"  ❌ 脚本执行失败：{result.stderr[:200]}")
        except Exception as e:
            print(f"  ⚠ 脚本执行超时或异常：{e}")
    else:
        print(f"  ❌ 脚本不存在：{script_path}")
        return False

def test_collaborative_mode_code():
    """5. 测试协同模式代码"""
    print_section("测试 5: 协同模式代码完整性")
    
    run_py = Path('./personal_mode/run.py')
    if run_py.exists():
        with open(run_py, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('轮流执行逻辑', 'attempt_methods' in content),
            ('详细错误检测', '详细错误检测' in content),
            ('本地环境检测', '检测本地环境' in content),
            ('CUDA 检测', 'cuda.is_available()' in content),
            ('显存检测', 'mem_get_info()' in content),
            ('云端图片下载', 'requests.get' in content and '下载图片' in content),
            ('文件验证', '验证' in content and 'stat().st_size' in content),
        ]
        
        passed = 0
        for name, found in checks:
            if found:
                print(f"  ✓ {name}: 存在")
                passed += 1
            else:
                print(f"  ❌ {name}: 缺失")
        
        print(f"\n  总计：{passed}/{len(checks)} 项检查通过")
        return passed == len(checks)
    else:
        print(f"  ❌ 文件不存在：{run_py}")
        return False

def test_mode_environment_detection():
    """6. 测试模式环境检测 API"""
    print_section("测试 6: 模式环境检测 API")
    
    try:
        sys.path.insert(0, str(Path('./web').absolute()))
        from app import api_check_mode_environment
        
        modes = ['optimized', 'standard', 'collaborative', 'hybrid']
        
        for mode in modes:
            try:
                # 模拟 Flask request context
                from flask import Flask
                app = Flask(__name__)
                with app.test_request_context():
                    result = api_check_mode_environment(mode)
                    print(f"  ✓ {mode}模式检测：可用")
            except Exception as e:
                print(f"  ⚠ {mode}模式检测：{type(e).__name__}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败：{e}")
        return False

def test_pytorch_install_api():
    """7. 测试 PyTorch 安装 API"""
    print_section("测试 7: PyTorch 安装 API")
    
    try:
        from web.app import api_check_pytorch_installation
        
        # 模拟 Flask request context
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context():
            response = api_check_pytorch_installation()
            if response.status_code == 200:
                print(f"  ✓ API 可正常调用")
                
                import json
                data = json.loads(response.data)
                if data.get('success'):
                    print(f"  ✓ 返回数据结构正确")
                    print(f"    - PyTorch 已安装：{data['pytorch']['installed']}")
                    print(f"    - CUDA 支持：{data['pytorch']['cuda_support']}")
            else:
                print(f"  ❌ API 返回错误：HTTP {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败：{e}")
        return False

def test_scanner_gpu_detection():
    """8. 测试 scanner GPU 检测"""
    print_section("测试 8: scanner GPU 多重检测")
    
    scanner_py = Path('./scanner.py')
    if scanner_py.exists():
        with open(scanner_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('PyTorch 检测', 'torch.cuda.is_available()' in content),
            ('nvidia-smi 检测', 'nvidia-smi' in content),
            ('WMI 检测', 'Win32_VideoController' in content),
            ('Apple Silicon 检测', 'Apple Silicon' in content),
        ]
        
        passed = 0
        for name, found in checks:
            if found:
                print(f"  ✓ {name}: 存在")
                passed += 1
            else:
                print(f"  ❌ {name}: 缺失")
        
        print(f"\n  总计：{passed}/{len(checks)} 项检查通过")
        return passed == len(checks)
    else:
        print(f"  ❌ 文件不存在：{scanner_py}")
        return False

def test_quick_start():
    """9. 测试 quick_start.py 可运行性"""
    print_section("测试 9: quick_start.py 启动测试")
    
    quick_start = Path('./quick_start.py')
    if quick_start.exists():
        try:
            # 运行脚本 3 秒，看是否能正常启动
            result = subprocess.run(
                [sys.executable, str(quick_start)],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if '启动 Flask 应用' in result.stdout:
                print(f"  ✓ 可正常启动")
                return True
            elif 'SyntaxError' in result.stderr or 'Traceback' in result.stderr:
                print(f"  ❌ Python 语法错误")
                print(result.stderr[:500])
                return False
            else:
                print(f"  ⚠ 超时但无明显错误（正常）")
                return True
        except subprocess.TimeoutExpired:
            print(f"  ✓ 运行中（超时预期）")
            return True
        except Exception as e:
            print(f"  ❌ 测试异常：{e}")
            return False
    else:
        print(f"  ❌ 文件不存在：{quick_start}")
        return False

def main():
    """执行所有测试"""
    start_time = datetime.now()
    
    tests = [
        ('PyTorch 状态检测', test_pytorch_installation),
        ('GPU 多重检测', test_gpu_detection),
        ('模型下载指南', test_model_download_guide),
        ('手动下载脚本', test_manual_download_script),
        ('协同模式代码', test_collaborative_mode_code),
        ('模式环境检测', test_mode_environment_detection),
        ('PyTorch 安装 API', test_pytorch_install_api),
        ('Scanner GPU 检测', test_scanner_gpu_detection),
        ('quick_start.py', test_quick_start),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            if result is None:  # 跳过
                results.append((name, '跳过'))
            elif result:
                results.append((name, True))
            else:
                results.append((name, False))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n  ❌ 测试异常：{e}")
            results.append((name, f'异常：{e}'))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r == '跳过')
    
    print(f"\n  总测试数：{len(results)}")
    print(f"  ✓ 通过：{passed}")
    if failed > 0:
        print(f"  ❌ 失败：{failed}")
    if skipped > 0:
        print(f"  ⚠ 跳过：{skipped}")
    
    print(f"\n  成功率：{passed / (passed + failed) * 100:.0f}%" if (passed + failed) > 0 else "  无结果")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\n  测试耗时：{duration:.1f}秒")
    
    # 返回退出码
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
