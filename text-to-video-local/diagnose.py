#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成问题诊断工具
帮助检查环境、依赖、模型等状态
"""

import sys
import importlib.util
from pathlib import Path
import subprocess

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_python():
    """检查 Python 版本"""
    print_section("1. Python 环境")
    print(f"Python 版本：{sys.version}")
    print(f"Python 路径：{sys.executable}")

def check_dependencies():
    """检查依赖"""
    print_section("2. Python 依赖")
    
    deps = {
        'flask': ('Flask', True),
        'PIL': ('Pillow', True),
        'psutil': ('psutil', False),
        'torch': ('PyTorch', True),
        'transformers': ('Transformers', True),
        'diffusers': ('Diffusers', True),
        'huggingface_hub': ('Huggingface Hub', True),
        'modelscope': ('ModelScope', True),
    }
    
    missing = []
    for package, (name, required) in deps.items():
        spec = importlib.util.find_spec(package)
        if spec:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"  ✓ {name}: v{version}")
            except:
                print(f"  ⚠️  {name}: 已安装但导入失败")
                missing.append(name)
        else:
            status = "(必需)" if required else "(可选)"
            print(f"  ✗ {name}: 未安装 {status}")
            if required:
                missing.append(name)
    
    if missing:
        print(f"\n  建议安装：pip install {' '.join([m.lower() for m in missing])}")
    else:
        print("\n  ✅ 所有必需依赖已安装")

def check_models():
    """检查模型"""
    print_section("3. 模型文件")
    
    models_dir = Path('./models')
    if not models_dir.exists():
        print(f"  ❌ 模型目录不存在：{models_dir.absolute()}")
        print(f"\n  解决方案:")
        print(f"  1. 启动 Web 服务：python web/app.py")
        print(f"  2. 浏览器访问：http://localhost:5000/install")
        print(f"  3. 选择并下载模型（推荐 modelscope）")
        return
    
    models = list(models_dir.glob('*'))
    if not models:
        print(f"  ❌ 模型目录为空：{models_dir.absolute()}")
        print(f"\n  解决方案：同上，需要在 Web 界面下载模型")
        return
    
    print(f"  ✅ 已下载 {len(models)} 个模型:")
    for model in models[:10]:
        if model.is_dir():
            print(f"    📁 {model.name}/")
        else:
            print(f"    📄 {model.name} ({model.stat().st_size / 1024 / 1024:.1f}MB)")

def check_scripts():
    """检查脚本"""
    print_section("4. 生成脚本")
    
    scripts = [
        'personal_mode/run.py',
        'generation.py',
        'web/app.py'
    ]
    
    for script in scripts:
        path = Path(script)
        if path.exists():
            print(f"  ✓ {script}: 存在 ({path.stat().st_size} bytes)")
            
            # 检查是否可执行
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    print(f"    可执行：{first_line}")
        else:
            print(f"  ✗ {script}: 不存在")

def check_web_service():
    """检查 Web 服务"""
    print_section("5. Web 服务状态")
    
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5000))
    
    if result == 0:
        print("  ✓ Web 服务正在运行 (端口 5000)")
        print("\n  访问地址:")
        print(f"    主界面：http://localhost:5000")
        print(f"    安装向导：http://localhost:5000/install")
    else:
        print("  ⚠️  Web 服务未运行")
        print("\n  启动命令：python web/app.py")
    
    sock.close()

def test_generate_api():
    """测试生成 API"""
    print_section("6. 生成 API 测试")
    
    try:
        import requests
        from flask import Flask
        
        # 尝试导入 Flask 应用
        sys.path.insert(0, 'web')
        from app import app, tasks
        
        print("  ✓ Flask 应用导入成功")
        
        # 检查路由
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        api_routes = [r for r in routes if '/api/' in r]
        
        print(f"  ✓ 注册了 {len(api_routes)} 个 API 端点")
        
        # 检查关键 API
        critical_apis = ['/api/generate', '/api/task/<task_id>']
        for api in critical_apis:
            found = any(api.split('<')[0] in r for r in routes)
            if found:
                print(f"  ✓ {api}: 已注册")
            else:
                print(f"  ✗ {api}: 未注册")
        
    except ImportError as e:
        print(f"  ⚠️  无法测试 API: {e}")
        print("  这可能是正常的，如果某些依赖未安装")
    except Exception as e:
        print(f"  ✗ 测试失败：{e}")

def show_summary():
    """显示总结"""
    print_section("诊断总结")
    
    print("可能的问题:")
    print("  1. 模型文件未下载 → 访问 Web 安装向导下载")
    print("  2. 缺少 torch/transformers → pip install torch transformers")
    print("  3. Web 服务未启动 → python web/app.py")
    print("\n建议操作:")
    print("  步骤 1: pip install torch transformers huggingface_hub diffusers")
    print("  步骤 2: python web/app.py")
    print("  步骤 3: 浏览器访问 http://localhost:5000/install")
    print("  步骤 4: 选择 modelscope 模型并下载")
    print("  步骤 5: 返回主界面生成视频")
    print("\n调试技巧:")
    print("  - 查看 Web 服务日志（终端输出）")
    print("  - 浏览器 F12 查看 Console 和 Network")
    print("  - 检查 /api/generate API 返回的错误信息")

def main():
    print("\n" + "="*70)
    print("  AI 视频生成器 - 问题诊断工具")
    print("="*70)
    
    check_python()
    check_dependencies()
    check_models()
    check_scripts()
    check_web_service()
    test_generate_api()
    show_summary()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
