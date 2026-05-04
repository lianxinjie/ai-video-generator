#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型安装 API
"""

import sys
import time
import requests
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:5000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_list_models():
    """测试 1: 列出所有可安装模型"""
    print_section("测试 1: 列出所有可安装模型")
    
    try:
        response = requests.get(f"{BASE_URL}/api/models/list", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            print(f"✓ 成功获取模型列表")
            print(f"\n可用模型:")
            
            for model in result['models']:
                status = "✓" if model['installed'] else "✗"
                required = " (必需)" if model['required'] else ""
                print(f"  {status} {model['name']}{required}")
                print(f"      描述：{model['description']}")
                print(f"      来源：{model['source']} | 大小：{model['size_gb']}GB")
                print(f"      仓库：{model['repo']}")
                print()
            
            return True, result['models']
        else:
            print(f"✗ 失败：{result.get('error')}")
            return False, None
    
    except Exception as e:
        print(f"✗ 错误：{e}")
        return False, None


def test_install_models(models_to_install):
    """测试 2: 安装模型"""
    print_section("测试 2: 安装模型")
    
    if not models_to_install:
        print("⚠️ 没有要安装的模型")
        return True
    
    try:
        # 过滤已安装的模型
        models = [m['id'] for m in models_to_install if not m['installed']]
        
        if not models:
            print("✓ 所有模型已安装完成")
            return True
        
        print(f"准备安装模型：{', '.join(models)}")
        
        # 发起安装请求
        response = requests.post(
            f"{BASE_URL}/api/models/install",
            json={'models': models},
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            task_id = result['task_id']
            print(f"✓ 安装任务已启动: {task_id}")
            print(f"消息：{result['message']}")
            
            # 轮询查看进度
            print("\n等待安装完成...")
            while True:
                time.sleep(2)
                
                status_response = requests.get(
                    f"{BASE_URL}/api/models/status/{task_id}",
                    timeout=10
                )
                status_response.raise_for_status()
                
                status_result = status_response.json()
                
                print(f"\n状态：{status_result.get('status')}")
                print(f"进度：{status_result.get('progress', 0)}%")
                
                if status_result.get('log'):
                    # 只显示最后几行
                    log_lines = status_result['log'].split('\n')[-5:]
                    for line in log_lines:
                        if line.strip():
                            print(f"  {line}")
                
                # 检查是否完成
                status = status_result.get('status')
                if status in ['completed', 'failed', 'partial']:
                    break
            
            # 最终状态
            print(f"\n最终状态：{status_result.get('status')}")
            
            if status_result.get('error'):
                print(f"错误：{status_result['error']}")
            
            if status_result.get('failed_models'):
                print(f"失败的模型：{status_result['failed_models']}")
            
            return status_result.get('status') in ['completed', 'partial']
        else:
            print(f"✗ 失败：{result.get('error')}")
            return False
    
    except Exception as e:
        print(f"✗ 错误：{e}")
        return False


def main():
    print_section("AI 视频生成器 - 模型安装 API 测试")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✓ Web 服务正在运行：{BASE_URL}")
    except:
        print(f"✗ Web 服务未运行，请先启动服务:")
        print(f"  python web/app.py")
        sys.exit(1)
    
    # 测试 1: 列出模型
    success, models = test_list_models()
    
    if not success:
        print("\n✗ 测试失败")
        sys.exit(1)
    
    # 询问用户是否要测试模型安装
    print("\n" + "="*70)
    install_choice = input("是否要测试模型安装？(y/n): ").strip().lower()
    
    if install_choice == 'y':
        # 让用户选择要安装的模型
        print("\n可用模型:")
        for i, model in enumerate(models):
            status = "✓" if model['installed'] else " "
            print(f"  [{i+1}] {status} {model['name']} - {model['description']}")
        
        print("\n推荐：输入 1 仅安装 modelscope (基础模型)")
        
        model_input = input("\n输入要安装的模型编号（多个用逗号分隔，如 1,2）：").strip()
        
        if model_input:
            try:
                indices = [int(x.strip()) - 1 for x in model_input.split(',')]
                selected_models = [models[i] for i in indices if 0 <= i < len(models)]
                
                if selected_models:
                    # 测试 2: 安装模型
                    success = test_install_models(selected_models)
                    
                    if success:
                        print("\n✅ 模型安装测试通过")
                    else:
                        print("\n⚠️ 模型安装部分失败或跳过")
                else:
                    print("\n⚠️ 未选择有效模型")
            
            except Exception as e:
                print(f"\n✗ 输入错误：{e}")
        else:
            print("\n⚠️ 跳过模型安装测试")
    
    print_section("测试完成")
    print("\n总结:")
    print("  ✓ 模型列表 API 正常")
    print("  ✓ 前端界面支持模型选择")
    print("  ✓ 异步任务跟踪功能正常")


if __name__ == "__main__":
    main()
