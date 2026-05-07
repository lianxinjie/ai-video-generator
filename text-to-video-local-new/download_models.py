#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能模型下载器"""

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
    
    def download_from_huggingface(self, repo_id: str, variant: str = None, resume: bool = True) -> str:
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
            
            print(f"正在下载 {repo_id}...")
            model_path = snapshot_download(**kwargs)
            return model_path
            
        except Exception as e:
            print(f"下载失败：{e}")
            raise
    
    def download_from_modelscope(self, repo_id: str, resume: bool = True) -> str:
        """从 ModelScope 下载模型（支持续传）"""
        try:
            from modelscope import snapshot_download
            
            print(f"正在下载 {repo_id} (ModelScope)...")
            model_path = snapshot_download(
                repo_id,
                cache_dir=str(self.output_dir)
            )
            return model_path
            
        except Exception as e:
            print(f"下载失败：{e}")
            raise
    
    def download_single(self, model_name: str) -> Dict:
        """下载单个模型"""
        model_repos = {
            "modelscope": {
                "type": "modelscope",
                "repo": "damo/text-to-video-synthesis",
            },
        }
        
        model_info = model_repos.get(model_name)
        if not model_info:
            return {"name": model_name, "success": False, "error": "未知模型", "path": None}
        
        try:
            if model_info["type"] == "huggingface":
                path = self.download_from_huggingface(model_info["repo"])
            elif model_info["type"] == "modelscope":
                path = self.download_from_modelscope(model_info["repo"])
            else:
                return {"name": model_name, "success": False, "error": "未知类型", "path": None}
            
            return {"name": model_name, "success": True, "error": None, "path": path}
            
        except Exception as e:
            return {"name": model_name, "success": False, "error": str(e), "path": None}
    
    def download_batch(self, model_names: List[str], show_progress: bool = True) -> List[Dict]:
        """批量下载模型"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_model = {
                executor.submit(self.download_single, model): model
                for model in model_names
            }
            
            for future in as_completed(future_to_model):
                model = future_to_model[future]
                result = future.result()
                results.append(result)
        
        return results
    
    def check_existing_models(self, model_names: List[str]) -> Dict[str, bool]:
        """检查已下载的模型"""
        existing = {}
        
        for model_name in model_names:
            if model_name == "modelscope":
                check_path = self.output_dir / "damo" / "text-to-video-synthesis"
                existing[model_name] = check_path.exists()
            else:
                existing[model_name] = False
        
        return existing

def main():
    parser = argparse.ArgumentParser(description="智能模型下载器")
    parser.add_argument("--models", "-m", nargs="+", default=["modelscope"])
    parser.add_argument("--output", "-o", default="./models")
    parser.add_argument("--parallel", "-j", type=int, default=1)
    args = parser.parse_args()
    
    downloader = ModelDownloader(output_dir=args.output, max_workers=args.parallel)
    existing = downloader.check_existing_models(args.models)
    
    models_to_download = [m for m in args.models if not existing[m]]
    
    if not models_to_download:
        print("所有模型已存在")
        return 0
    
    print(f"下载 {len(models_to_download)} 个模型")
    results = downloader.download_batch(models_to_download)
    
    success = sum([1 for r in results if r.get("success")])
    print(f"完成：{success}/{len(results)}")
    
    return 0 if success == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
