#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能模型下载器
根据系统扫描结果自动选择最优下载方案
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class ModelDownloader:
    """智能模型下载器"""
    
    def __init__(self, output_dir: str = "./models", max_workers: int = 1):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        
        # 模型仓库映射
        self.model_repos = {
            "modelscope": {
                "type": "modelscope",
                "repo": "damo/video-generation-damo",
                "size_gb": 2.5,
                "required": True
            },
            "animatediff": {
                "type": "huggingface",
                "repo": "guoyww/animatediff-motion-adapter-v1-5-2",
                "size_gb": 4.0,
                "required": False
            },
            "animatediff_sd": {
                "type": "huggingface",
                "repo": "frankjoshua/toonyou_beta6",
                "size_gb": 4.0,
                "required": False,
                "depends_on": "animatediff"
            },
            "cogvideox": {
                "type": "huggingface",
                "repo": "THUDM/CogVideoX-5b",
                "size_gb": 20.0,
                "required": False
            },
            "svd": {
                "type": "huggingface",
                "repo": "stabilityai/stable-video-diffusion-img2vid-xt",
                "size_gb": 12.0,
                "variant": "fp16",
                "required": False
            }
        }
    
    def download_from_huggingface(self, repo_id: str, variant: str = None) -> str:
        """从 HuggingFace 下载模型"""
        try:
            from huggingface_hub import snapshot_download
            
            kwargs = {
                "repo_id": repo_id,
                "cache_dir": str(self.output_dir),
                "repo_type": "model",
            }
            
            if variant:
                kwargs["variant"] = variant
            
            print(f"  正在下载 {repo_id}...")
            
            model_path = snapshot_download(**kwargs)
            
            return model_path
            
        except ImportError:
            print("  错误：需要安装 huggingface_hub")
            print("  运行：pip install huggingface_hub")
            raise
        except Exception as e:
            print(f"  错误：下载失败 - {e}")
            raise
    
    def download_from_modelscope(self, repo_id: str) -> str:
        """从 ModelScope 下载模型"""
        try:
            from modelscope import snapshot_download
            
            print(f"  正在下载 {repo_id} (ModelScope)...")
            
            model_path = snapshot_download(
                repo_id,
                cache_dir=str(self.output_dir)
            )
            
            return model_path
            
        except ImportError:
            print("  错误：需要安装 modelscope")
            print("  运行：pip install modelscope")
            raise
        except Exception as e:
            print(f"  错误：下载失败 - {e}")
            raise
    
    def download_single(self, model_name: str) -> Dict:
        """下载单个模型"""
        model_info = self.model_repos.get(model_name)
        
        if not model_info:
            return {
                "name": model_name,
                "success": False,
                "error": "未知模型",
                "path": None
            }
        
        # 检查依赖
        if "depends_on" in model_info:
            dep_path = self.output_dir / model_info["depends_on"]
            if not dep_path.exists():
                return {
                    "name": model_name,
                    "success": False,
                    "error": f"依赖模型不存在：{model_info['depends_on']}",
                    "path": None
                }
        
        try:
            if model_info["type"] == "huggingface":
                path = self.download_from_huggingface(
                    model_info["repo"],
                    model_info.get("variant")
                )
            elif model_info["type"] == "modelscope":
                path = self.download_from_modelscope(model_info["repo"])
            else:
                return {
                    "name": model_name,
                    "success": False,
                    "error": f"未知下载类型：{model_info['type']}",
                    "path": None
                }
            
            return {
                "name": model_name,
                "success": True,
                "error": None,
                "path": path
            }
            
        except Exception as e:
            return {
                "name": model_name,
                "success": False,
                "error": str(e),
                "path": None
            }
    
    def download_batch(self, model_names: List[str], show_progress: bool = True) -> List[Dict]:
        """批量下载模型"""
        results = []
        
        if show_progress:
            total_size = sum([
                self.model_repos.get(m, {}).get("size_gb", 0) 
                for m in model_names
            ])
            
            print(f"\n{'='*70}")
            print(f"下载计划:")
            print(f"  模型数量：{len(model_names)}")
            print(f"  总大小：约 {total_size:.1f}GB")
            print(f"  并行数：{self.max_workers}")
            print(f"  目录：{self.output_dir.absolute()}")
            print(f"{'='*70}\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_model = {
                executor.submit(self.download_single, model): model
                for model in model_names
            }
            
            for future in as_completed(future_to_model):
                model = future_to_model[future]
                result = future.result()
                results.append(result)
                
                if result["success"]:
                    print(f"✓ {model} 下载成功: {result['path']}")
                else:
                    print(f"✗ {model} 下载失败: {result['error']}")
        
        return results
    
    def check_existing_models(self, model_names: List[str]) -> Dict[str, bool]:
        """检查已下载的模型"""
        existing = {}
        
        for model_name in model_names:
            model_info = self.model_repos.get(model_name)
            if not model_info:
                existing[model_name] = False
                continue
            
            # 根据类型检查路径
            if model_info["type"] == "huggingface":
                # HuggingFace 缓存检查
                repo_parts = model_info["repo"].split("/")
                check_path = self.output_dir / f"models--{repo_parts[0]}--{repo_parts[1]}"
                existing[model_name] = check_path.exists()
            elif model_info["type"] == "modelscope":
                # ModelScope 缓存检查
                repo_parts = model_info["repo"].split("/")
                check_path = self.output_dir / repo_parts[-1]
                existing[model_name] = check_path.exists()
            else:
                existing[model_name] = False
        
        return existing


def main():
    parser = argparse.ArgumentParser(description="智能模型下载器")
    
    parser.add_argument(
        "--models", "-m",
        nargs="+",
        choices=["modelscope", "animatediff", "cogvideox", "svd", "all"],
        default=["modelscope"],
        help="要下载的模型"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./models",
        help="模型输出目录"
    )
    
    parser.add_argument(
        "--parallel", "-j",
        type=int,
        default=1,
        help="并行下载数量"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查已下载模型，不下载"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新下载已存在的模型"
    )
    
    parser.add_argument(
        "--from-scan",
        action="store_true",
        help="从扫描结果读取推荐模型"
    )
    
    args = parser.parse_args()
    
    # 从扫描结果读取
    if args.from_scan:
        scan_file = Path("scan_report.json")
        if scan_file.exists():
            import json
            with open(scan_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            if report.get("recommendation"):
                args.models = report["recommendation"]["download_priority"]
                print(f"从扫描报告读取推荐模型：{', '.join(args.models)}")
        else:
            print("警告：未找到 scan_report.json，使用默认模型")
    
    # 展开"all"
    if "all" in args.models:
        args.models = ["modelscope", "animatediff", "cogvideox", "svd"]
    
    # 创建下载器
    downloader = ModelDownloader(
        output_dir=args.output,
        max_workers=args.parallel
    )
    
    # 仅检查
    if args.check_only:
        print("检查已下载的模型...")
        existing = downloader.check_existing_models(args.models)
        
        print(f"\n{'='*70}")
        print("模型状态:")
        for model, exists in existing.items():
            status = "✓ 已存在" if exists else "✗ 未下载"
            print(f"  {model}: {status}")
        print(f"{'='*70}")
        
        return
    
    # 强制模式：删除已存在的模型
    if args.force:
        print("强制模式：清理已存在的模型...")
        existing = downloader.check_existing_models(args.models)
        for model, exists in existing.items():
            if exists:
                print(f"  标记重新下载：{model}")
    
    # 过滤已存在的模型
    if not args.force:
        existing = downloader.check_existing_models(args.models)
        models_to_download = [m for m in args.models if not existing[m]]
        
        if not models_to_download:
            print("✓ 所有模型已下载完成！")
            return
        
        print(f"需要下载 {len(models_to_download)} 个模型，跳过 {len(args.models) - len(models_to_download)} 个已存在模型")
        args.models = models_to_download
    
    # 开始下载
    start_time = time.time()
    
    results = downloader.download_batch(args.models)
    
    elapsed = time.time() - start_time
    
    # 统计结果
    success_count = sum([1 for r in results if r["success"]])
    fail_count = len(results) - success_count
    
    print(f"\n{'='*70}")
    print("下载完成统计:")
    print(f"  成功：{success_count}/{len(results)}")
    print(f"  失败：{fail_count}/{len(results)}")
    print(f"  耗时：{elapsed/60:.1f} 分钟")
    print(f"{'='*70}")
    
    if fail_count > 0:
        print("\n失败的模型:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['name']}: {result['error']}")
        
        print("\n提示：可以重新运行以下命令重试失败的模型:")
        failed_models = [r["name"] for r in results if not r["success"]]
        print(f"  python3 download_models.py -m {' '.join(failed_models)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
