#!/usr/bin/env python3
"""一键修复 pip 安装命令"""
from pathlib import Path

content = Path('web/app.py').read_text()

# 1. 找到并替换包分组逻辑（在 thread 创建之前）
old_thread_start = """# 后台执行安装任务
        def install_task():"""

new_thread_start = """# 包分组：torch 需要单独使用 PyTorch 源
        torch_packages = []
        other_packages = []
        
        for pkg in packages:
            if pkg in package_info:
                info = package_info[pkg]
                if info.get('extra'):
                    torch_packages.append(info['pip_name'])
                else:
                    other_packages.append(info['pip_name'])
        
        # 分别安装
        commands = []
        if torch_packages:
            cmd_torch = [sys.executable, '-m', 'pip', 'install'] + torch_packages + ['--index-url', 'https://download.pytorch.org/whl/cpu', '--break-system-packages']
            commands.append(('torch (CPU 版)', cmd_torch))
        
        if other_packages:
            cmd_other = [sys.executable, '-m', 'pip', 'install'] + other_packages + ['--break-system-packages']
            commands.append(('其他依赖', cmd_other))
        
        # 后台执行安装任务
        def install_task():"""

if old_thread_start in content:
    content = content.replace(old_thread_start, new_thread_start)
    print("✅ 已添加包分组逻辑")
else:
    print("❌ 未找到 thread 开始位置")

# 2. 替换 install_task 函数内容
old_task = """log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装依赖：{', '.join(packages)}\\n")
                log.write(f"命令：{' '.join(cmd)}\\n\\n")
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    
                    if result.returncode == 0:
                        log.write("✓ 依赖安装成功\\n")
                        # 更新任务状态为完成
                        if task_id in tasks:
                            tasks[task_id]['status'] = 'completed'
                            tasks[task_id]['progress'] = 100
                    else:
                        log.write(f"❌ 依赖安装失败：{result.stderr}\\n")
                        # 更新任务状态为失败
                        if task_id in tasks:
                            tasks[task_id]['status'] = 'failed'
                            tasks[task_id]['error'] = result.stderr
                
                except subprocess.TimeoutExpired:
                    log.write("❌ 安装超时\\n")
                except Exception as e:
                    log.write(f"❌ 安装异常：{str(e)}\\n")"""

new_task = """log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            all_success = True
            failed = []
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装 {len(packages)} 个依赖...\\n\\n")
                
                # 依次安装
                for name, cmd in commands:
                    log.write(f"【安装 {name}】\\n")
                    log.write(f"命令：{' '.join(cmd)}\\n\\n")
                    print(f"[pip] 正在安装 {name}...")
                    
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=600
                        )
                        
                        if result.returncode == 0:
                            log.write(f"✓ {name} 安装成功\\n\\n")
                            print(f"[pip] ✓ {name} 安装成功")
                        else:
                            log.write(f"❌ {name} 安装失败：{result.stderr}\\n\\n")
                            print(f"[pip] ❌ {name} 安装失败")
                            all_success = False
                            failed.append(name)
                    except subprocess.TimeoutExpired:
                        log.write(f"❌ {name} 安装超时\\n\\n")
                        all_success = False
                        failed.append(name)
                    except Exception as e:
                        log.write(f"❌ {name} 安装异常：{str(e)}\\n\\n")
                        all_success = False
                        failed.append(e)
                
                # 更新任务状态
                if task_id in tasks:
                    if all_success:
                        log.write("\\n✅ 所有依赖安装成功！\\n")
                        tasks[task_id]['status'] = 'completed'
                        tasks[task_id]['progress'] = 100
                        print("[pip] ✅ 所有依赖安装成功！")
                    else:
                        log.write(f"\\n❌ 安装失败：{', '.join(failed)}\\n")
                        tasks[task_id]['status'] = 'failed'
                        tasks[task_id]['error'] = f"安装失败：{', '.join(failed)}"
                        print(f"[pip] ❌ 安装失败：{', '.join(failed)}\")"""

if old_task in content:
    content = content.replace(old_task, new_task)
    print("✅ 已更新 install_task 函数")
else:
    print("❌ 未找到 install_task")

Path('web/app.py').write_text(content)

# 验证语法
import ast
try:
    ast.parse(content)
    print("✅ 语法检查通过")
    print("\n修复完成！请重启 Flask 服务测试。")
except SyntaxError as e:
    print(f"❌ 语法错误：{e}")
    print(f"   行：{e.lineno}")
