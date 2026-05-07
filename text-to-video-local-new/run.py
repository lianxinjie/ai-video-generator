#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能启动脚本
根据系统扫描结果自动选择最优运行模式
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional
import argparse


class SmartLauncher:
    """智能启动器"""
    
    def __init__(self):
        self.scan_report = None
        self.hardware_info = None
        self.recommendation = None
        
    def load_scan_report(self, report_path: str = "scan_report.json") -> bool:
        """加载扫描报告"""
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                self.scan_report = json.load(f)
            
            self.hardware_info = self.scan_report.get("hardware", {})
            self.recommendation = self.scan_report.get("recommendation", {})
            
            print(f"✓ 已加载扫描报告：{report_path}")
            return True
            
        except FileNotFoundError:
            print(f"⚠ 未找到扫描报告：{report_path}")
            print("  将使用默认配置启动")
            return False
        except Exception as e:
            print(f"⚠ 加载扫描报告失败：{e}")
            return False
    
    def get_optimal_device(self) -> str:
        """获取最优设备"""
        if not self.recommendation:
            return "cuda" if self._check_gpu_available() else "cpu"
        
        mode = self.recommendation.get("mode", "")
        
        if "gpu" in mode:
            return "cuda"
        else:
            return "cpu"
    
    def _check_gpu_available(self) -> bool:
        """检查 GPU 是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def get_optimal_model(self) -> str:
        """获取推荐模型"""
        if not self.recommendation:
            return "modelscope"
        
        priority = self.recommendation.get("download_priority", [])
        
        if priority:
            return priority[0]
        else:
            return "modelscope"
    
    def get_optimization_args(self) -> list:
        """获取优化参数"""
        args = []
        
        if not self.recommendation:
            return args
        
        mode = self.recommendation.get("mode", "")
        warnings = self.recommendation.get("warnings", [])
        
        # 低端 GPU 优化
        if "low_end" in mode or "very_low" in mode:
            args.extend(["--height", "256", "--width", "256"])
            args.extend(["--steps", "25"])
        
        # CPU 模式优化
        if "cpu" in mode:
            args.extend(["--steps", "20"])
            args.append("--device")
            args.append("cpu")
        
        return args
    
    def run(
        self,
        model: Optional[str] = None,
        prompt: str = "一只猫在草地上奔跑",
        output: str = "output.mp4",
        interactive: bool = False
    ):
        """运行生成"""
        
        # 自动选择模型
        if not model:
            model = self.get_optimal_model()
        
        # 构建命令
        cmd = [
            sys.executable,
            "generation.py",
            "-m", model,
            "-p", prompt,
            "-o", output
        ]
        
        # 添加优化参数
        opt_args = self.get_optimization_args()
        if opt_args:
            cmd.extend(opt_args)
        
        # 打印配置信息
        print("\n" + "="*60)
        print(" AI 视频生成 - 智能启动")
        print("="*60)
        print(f"\n配置信息:")
        print(f"  模型：{model}")
        print(f"  设备：{self.get_optimal_device()}")
        print(f"  提示词：{prompt}")
        print(f"  输出：{output}")
        
        if opt_args:
            print(f"  优化参数：{' '.join(opt_args)}")
        
        if self.recommendation:
            mode = self.recommendation.get("mode", "unknown")
            print(f"  运行模式：{mode}")
        
        print(f"\n执行命令:")
        print(f"  {' '.join(cmd)}")
        print(f"\n{'='*60}\n")
        
        # 执行
        try:
            result = subprocess.run(cmd, check=True)
            
            if result.returncode == 0:
                print(f"\n✓ 视频生成完成：{output}")
            else:
                print(f"\n⚠ 视频生成完成但有警告")
                
        except subprocess.CalledProcessError as e:
            print(f"\n✗ 视频生成失败：{e}")
            return False
        except Exception as e:
            print(f"\n✗ 执行失败：{e}")
            return False
        
        return True
    
    def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print(" AI 视频生成 - 交互模式")
        print("="*60)
        
        # 显示推荐
        if self.recommendation:
            print("\n推荐配置:")
            print(f"  模式：{self.recommendation.get('mode', 'N/A')}")
            print(f"  可用模型：{', '.join(self.recommendation.get('suitable_models', []))}")
            print(f"  优化建议:")
            for tip in self.recommendation.get('optimization_tips', []):
                print(f"    {tip}")
        
        # 获取用户输入
        print("\n请输入提示词（直接回车使用默认值）:")
        default_prompt = "一只猫在草地上奔跑"
        prompt = input(f"[{default_prompt}] ").strip()
        
        if not prompt:
            prompt = default_prompt
        
        print("\n请选择模型:")
        if self.recommendation:
            models = self.recommendation.get('suitable_models', ['modelscope'])
        else:
            models = ['modelscope']
        
        for i, model in enumerate(models):
            print(f"  {i+1}. {model}")
        
        try:
            choice = input(f"[1] ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    model = models[idx]
            else:
                model = models[0] if models else 'modelscope'
        except:
            model = 'modelscope'
        
        print("\n请输入输出文件名（直接回车使用默认值）:")
        default_output = "output.mp4"
        output = input(f"[{default_output}] ").strip()
        
        if not output:
            output = default_output
        
        # 确认
        print(f"\n确认配置:")
        print(f"  模型：{model}")
        print(f"  提示词：{prompt}")
        print(f"  输出：{output}")
        
        confirm = input("\n开始生成？[Y/n] ").strip().lower()
        
        if confirm in ['', 'y', 'yes']:
            self.run(model=model, prompt=prompt, output=output)
        else:
            print("已取消")


def main():
    parser = argparse.ArgumentParser(description="智能启动脚本")
    
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="指定模型名称"
    )
    
    parser.add_argument(
        "--prompt", "-p",
        default="一只猫在草地上奔跑",
        help="文本提示词"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output.mp4",
        help="输出文件路径"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互模式"
    )
    
    parser.add_argument(
        "--scan",
        action="store_true",
        help="先执行系统扫描"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="显示配置信息后退出"
    )
    
    args = parser.parse_args()
    
    # 创建启动器
    launcher = SmartLauncher()
    
    # 先扫描
    if args.scan:
        print("执行系统扫描...")
        subprocess.run([sys.executable, "scanner.py"])
        
        # 重新加载扫描报告
        launcher.load_scan_report()
    else:
        # 加载现有扫描报告
        launcher.load_scan_report()
    
    # 显示配置
    if args.show_config:
        print("\n当前配置:")
        print(f"  推荐模型：{launcher.get_optimal_model()}")
        print(f"  推荐设备：{launcher.get_optimal_device()}")
        print(f"  优化参数：{' '.join(launcher.get_optimization_args())}")
        return
    
    # 交互模式
    if args.interactive:
        launcher.interactive_mode()
    else:
        # 直接运行
        launcher.run(
            model=args.model,
            prompt=args.prompt,
            output=args.output
        )


if __name__ == "__main__":
    main()
