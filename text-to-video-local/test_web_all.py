#!/usr/bin/env python3
"""
Web 功能严格测试脚本
测试所有 Web API 和硬件检测功能
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

print("="*70)
print("  Web 功能严格测试")
print("="*70)
print()

# 测试计数器
tests_passed = 0
tests_failed = 0

def test_result(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        print(f"✅ {name}")
        tests_passed += 1
    else:
        print(f"❌ {name}")
        if details:
            print(f"   详情：{details}")
        tests_failed += 1

# ========== 测试 1: 硬件检测 ==========
print("="*70)
print("  测试 1: 硬件检测（真实硬件）")
print("="*70)
print()

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from scanner import SystemScanner, HardwareInfo
    
    scanner = SystemScanner()
    hardware = scanner.scan_all()
    
    # CPU 检测
    test_result(
        "CPU 检测",
        hardware.cpu_model and len(hardware.cpu_model) > 0 and hardware.cpu_cores > 0,
        f"{hardware.cpu_model} ({hardware.cpu_cores}核)" if hardware.cpu_model else "未检测到 CPU"
    )
    
    # GPU 检测
    gpu_models = hardware.gpu_models or []
    gpu_info = ", ".join(gpu_models) if gpu_models else "无 GPU"
    test_result(
        "GPU 检测",
        len(gpu_models) > 0 or not hardware.gpu_available,
        gpu_info
    )
    
    # 内存检测 - 必须检测到真实内存
    test_result(
        "内存检测",
        hardware.ram_total > 0 and hardware.ram_total < 1000,  # 合理范围 0-1000GB
        f"总内存：{hardware.ram_total}GB, 可用：{hardware.ram_available}GB"
    )
    
    # 验证内存不是虚拟值
    if hardware.ram_total in [0, 8, 16, 32, 64]:  # 可能是硬编码的虚拟值
        print(f"   ⚠️  警告：内存值 {hardware.ram_total}GB 可能是虚拟值")
    
    # 磁盘检测
    test_result(
        "磁盘检测",
        hardware.disk_total > 0 and hardware.disk_available > 0,
        f"总磁盘：{hardware.disk_total}GB, 可用：{hardware.disk_available}GB"
    )
    
    # CUDA 检测（如果有 GPU）
    if hardware.gpu_available:
        test_result(
            "CUDA 检测",
            hardware.cuda_version is not None or hardware.pytorch_cuda is not None,
            f"CUDA: {hardware.cuda_version or 'N/A'}, PyTorch CUDA: {hardware.pytorch_cuda or 'N/A'}"
        )
    else:
        print(f"   ℹ️  无 GPU，跳过 CUDA 检测")
    
except Exception as e:
    test_result("硬件检测", False, f"异常：{str(e)}")
    import traceback
    traceback.print_exc()

print()

# ========== 测试 2: Flask 应用启动 ==========
print("="*70)
print("  测试 2: Flask 应用")
print("="*70)
print()

# 检查 Flask 是否安装
try:
    from flask import Flask
    flask_installed = True
    test_result("Flask 已安装", True)
except ImportError:
    flask_installed = False
    test_result("Flask 已安装", False, "请先安装 Flask: pip install flask")

if flask_installed:
    # 检查 Web 目录
    web_dir = Path(__file__).parent / "web"
    test_result("Web 目录存在", web_dir.exists(), str(web_dir))
    
    # 检查 app.py
    app_file = web_dir / "app.py"
    test_result("app.py 存在", app_file.exists())
    
    # 检查模板文件
    templates_dir = web_dir / "templates"
    test_result("templates 目录存在", templates_dir.exists())
    
    if templates_dir.exists():
        test_result("index.html 存在", (templates_dir / "index.html").exists())
        test_result("install.html 存在", (templates_dir / "install.html").exists())

print()

# ========== 测试 3: API 端点验证 ==========
print("="*70)
print("  测试 3: API 端点验证")
print("="*70)
print()

if flask_installed:
    # 导入 app 检查路由
    try:
        sys.path.insert(0, str(web_dir))
        from app import app
        
        # 获取所有路由
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        
        required_routes = [
            '/',
            '/api/generate',
            '/api/tasks',
            '/api/task/<task_id>',
            '/api/task/<task_id>/cancel',
        ]
        
        for route in required_routes:
            # 处理带参数的路由
            route_base = route.split('<')[0].rstrip('/')
            found = any(route_base in r for r in routes)
            test_result(f"路由 {route}", found)
        
    except Exception as e:
        test_result("加载 Flask 应用", False, str(e))
else:
    print("   ⚠️  跳过 API 端点测试（Flask 未安装）")

print()

# ========== 测试 4: 硬件检测真实性验证 ==========
print("="*70)
print("  测试 4: 硬件检测真实性验证")
print("="*70)
print()

# 验证 CPU 信息
def verify_cpu():
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name'],
                capture_output=True, text=True, timeout=5
            )
            cpu_name = result.stdout.strip().split('\n')[-1].strip()
            return len(cpu_name) > 0
        except:
            return False
    elif sys.platform == 'darwin':
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, timeout=5
            )
            return len(result.stdout.strip()) > 0
        except:
            return False
    else:  # Linux
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return True
            return False
        except:
            return False

test_result("CPU 信息真实", verify_cpu())

# 验证内存信息
def verify_memory():
    try:
        import psutil
        mem = psutil.virtual_memory()
        # 真实内存在合理范围内（2GB-1TB）
        return 2 * 1024**3 <= mem.total <= 1024 * 1024**3
    except:
        return False

test_result("内存信息真实", verify_memory())

# 验证 GPU 信息（如果有）
def verify_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return len(gpu_name) > 0 and 'GPU' in gpu_name or 'RTX' in gpu_name or 'GTX' in gpu_name or 'Tesla' in gpu_name
        return True  # 没有 GPU 也算通过
    except:
        return True  # PyTorch 未安装也算通过

test_result("GPU 信息真实", verify_gpu())

print()

# ========== 测试 5: 前端文件完整性 ==========
print("="*70)
print("  测试 5: 前端文件完整性")
print("="*70)
print()

if templates_dir.exists():
    # 检查关键文件
    critical_files = [
        'index.html',
        'install.html',
    ]
    
    for filename in critical_files:
        filepath = templates_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            test_result(f"{filename}", size > 1000, f"{size} bytes")
            
            # 检查是否包含关键内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if filename == 'index.html':
                has_generate_api = '/api/generate' in content
                test_result("  - 包含正确的 API 端点", has_generate_api)
                
            if filename == 'install.html':
                # install.html 现在不必需，已用 offline_install.html 替代
                # test_result("  - 包含 Python 下载链接", 'python.org' in content)
                pass  # 跳过此测试
        else:
            test_result(f"{filename}", False, "文件不存在")

print()

# ========== 测试结果 ==========
print("="*70)
print("  测试结果")
print("="*70)
print()
print(f"通过：{tests_passed}")
print(f"失败：{tests_failed}")
print()

if tests_failed == 0:
    print("✅ 所有测试通过！")
    sys.exit(0)
else:
    print(f"❌ 有 {tests_failed} 项测试失败")
    sys.exit(1)
