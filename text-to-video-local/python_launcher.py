#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 安装启动器
用于执行 install_python.bat 或 install_python.sh
"""

import os
import sys
import subprocess
import webbrowser

def check_python_installed():
    """检查 Python 是否已安装"""
    try:
        import sys
        version = sys.version
        if version.startswith('3.'):
            return True, version.split()[0]
        return False, None
    except:
        return False, None

def run_windows_installer():
    """运行 Windows 安装脚本"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'install_python.bat')
    
    if not os.path.exists(script_path):
        print(f"❌ 找不到安装脚本：{script_path}")
        return False
    
    print(f"正在执行：{script_path}")
    try:
        # 直接运行脚本
        subprocess.Popen([script_path], shell=True, cwd=os.path.dirname(script_path))
        print("✅ 安装程序已启动")
        return True
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        return False

def run_unix_installer():
    """运行 macOS/Linux 安装脚本"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'install_python.sh')
    
    if not os.path.exists(script_path):
        print(f"❌ 找不到安装脚本：{script_path}")
        return False
    
    print(f"正在执行：{script_path}")
    try:
        # 给脚本执行权限
        os.chmod(script_path, 0o755)
        # 运行脚本
        subprocess.Popen(['bash', script_path], cwd=os.path.dirname(script_path))
        print("✅ 安装程序已启动")
        return True
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        return False

def main():
    print("="*60)
    print("  AI 视频生成器 - Python 安装启动器")
    print("="*60)
    print()
    
    # 检查是否已安装
    installed, version = check_python_installed()
    
    if installed:
        print(f"✅ Python 已安装：{version}")
        print("\n要重新安装或升级 Python 吗？")
        response = input("输入 y 继续，或直接回车退出：").strip().lower()
        if response != 'y':
            print("\n按回车键退出...")
            input()
            return
    
    # 检测操作系统
    system = sys.platform
    print(f"检测到操作系统：{system}")
    
    if system.startswith('win'):
        print("正在运行 Windows 安装脚本...")
        if run_windows_installer():
            print("\n✅ 安装程序已启动，請在打开的窗口中查看进度")
        else:
            print("\n❌ 启动失败，请手动运行 install_python.bat")
    else:
        print("正在运行 Unix 安装脚本...")
        if run_unix_installer():
            print("\n✅ 安装程序已启动，請在打开的窗口中查看进度")
        else:
            print("\n❌ 启动失败，请手动运行 install_python.sh")
    
    print()
    print("安装完成后，请重新运行启动器或直接运行：python quick_start.py")
    print("\n按回车键退出...")
    input()

if __name__ == '__main__':
    main()
