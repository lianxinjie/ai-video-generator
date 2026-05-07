#!/usr/bin/env python3
"""代码生成质量检查脚本"""

import ast
import re
from pathlib import Path

def check_python_file(filepath: Path) -> dict:
    """检查 Python 文件的潜在问题"""
    result = {
        'file': str(filepath),
        'errors': [],
        'warnings': []
    }
    
    content = filepath.read_text()
    
    # 1. 语法检查
    try:
        ast.parse(content)
    except SyntaxError as e:
        result['errors'].append(f"语法错误：行{e.lineno}, {e.msg}")
        return result
    
    # 2. 检查未导入的常用模块
    used_modules = set()
    imports = set()
    
    # 提取所有导入
    for node in ast.walk(ast.parse(content)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    
    # 检查代码中使用的模块
    common_modules = {
        'time': r'\btime\.\w+\(',
        'stat': r'\bstat\.\w+',
        'platform': r'\bplatform\.\w+\(',
        'shutil': r'\bshutil\.\w+\(',
        'subprocess': r'\bsubprocess\.\w+\(',
        'zipfile': r'\bzipfile\.\w+\(',
        'tarfile': r'\btarfile\.\w+\(',
        'requests': r'\brequests\.\w+\(',
        'json': r'\bjson\.\w+\(',
        'os': r'\bos\.\w+\(',
    }
    
    for module, pattern in common_modules.items():
        if re.search(pattern, content) and module not in imports:
            # 检查是否在函数内导入
            func_pattern = f'import {module}'
            if func_pattern not in content:
                result['warnings'].append(f"使用 {module} 但未导入")
    
    # 3. 检查函数定义语法
    func_defs = re.findall(r'def \w+\([^)]*\)\s*(?:->.*?:)?', content)
    for func in func_defs:
        if func.rstrip().endswith(':'):
            continue
        if not func.rstrip().endswith(')'):
            result['errors'].append(f"函数定义语法可能错误：{func}")
    
    # 4. 检查缩进不一致
    lines = content.split('\n')
    tabs = sum(1 for line in lines if line.startswith('\t'))
    spaces = sum(1 for line in lines if line.startswith(' '))
    if tabs > 0 and spaces > 0:
        result['warnings'].append(f"混用 tab 和空格缩进 (tab:{tabs}, space:{spaces})")
    
    return result

def check_file(filepath: Path) -> bool:
    """检查单个文件"""
    if filepath.suffix != '.py':
        return True
    
    result = check_python_file(filepath)
    
    if result['errors']:
        print(f"❌ {filepath}")
        for err in result['errors']:
            print(f"   错误：{err}")
        return False
    
    if result['warnings']:
        print(f"⚠️  {filepath}")
        for warn in result['warnings']:
            print(f"   警告：{warn}")
        return len(result['errors']) == 0
    
    print(f"✅ {filepath}")
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # 检查指定文件
        files = [Path(f) for f in sys.argv[1:]]
    else:
        # 检查所有 Python 文件
        root = Path('.')
        files = sorted(root.rglob('*.py'))
    
    failed = 0
    for f in files:
        if not check_file(f):
            failed += 1
    
    if failed > 0:
        print(f"\n❌ {failed} 个文件有问题")
        sys.exit(1)
    else:
        print(f"\n✅ 所有文件检查通过")
        sys.exit(0)
