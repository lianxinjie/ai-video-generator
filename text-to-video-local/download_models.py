#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能模型下载器（V2 增强版）
- 支持多线程分片下载单个大文件
- 支持断点续传（Range 请求）
- 详细进度日志
- 兼容官方 SDK + 直接 URL 两种模式
"""

import os
import sys
import argparse
import time
import shutil
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed


class MultiThreadDownloader:
    """多线程分片下载器（类似 Aria2）"""
    
    def __init__(self, num_threads: int = 4, min_file_mb: float = 10.0):
        """
        Args:
            num_threads: 最大线程数
            min_file_mb: 启用多线程的文件大小阈值（MB）
        """
        self.num_threads = num_threads
        self.min_file_mb = min_file_mb
    
    def calculate_optimal_threads(self, file_size_mb: float) -> int:
        """根据文件大小智能计算最优线程数"""
        if file_size_mb < 10:
            return 1
        elif file_size_mb < 100:
            return 2
        elif file_size_mb < 500:
            return 4
        else:
            return min(8, self.num_threads)
    
    def check_range_support(self, url: str) -> bool:
        """检查服务器是否支持 Range 请求"""
        try:
            head = requests.head(url, timeout=10)
            accept_ranges = head.headers.get('Accept-Ranges', '').lower() == 'bytes'
            print(f"[检测] Accept-Ranges: {head.headers.get('Accept-Ranges', 'none')}")
            return accept_ranges
        except Exception as e:
            print(f"[警告] 无法检测 Range 支持：{e}")
            return False
    
    def get_file_size(self, url: str) -> int:
        """获取文件大小（字节）"""
        try:
            head = requests.head(url, timeout=10)
            content_length = head.headers.get('Content-Length')
            if content_length:
                return int(content_length)
            
            # HEAD 可能返回 0，尝试 GET 第一个字节后取消
            response = requests.get(url, stream=True, timeout=10)
            total = int(response.headers.get('Content-Length', 0))
            response.close()
            return total
        except:
            return 0
    
    def download_single_thread(self, url: str, output_path: Path, resume_offset: int = 0, show_progress: bool = True) -> bool:
        """单线程下载（小文件或不支持 Range 时使用）"""
        
        total_size = self.get_file_size(url)
        if total_size == 0:
            print("[错误] 无法获取文件大小")
            return False
        
        downloaded_size = resume_offset if output_path.exists() else 0
        remaining = total_size - downloaded_size
        
        print(f"[单线程] 总计 {total_size/1024/1024:.2f}MB | 已下载 {downloaded_size/1024/1024:.2f}MB | 剩余 {remaining/1024/1024:.2f}MB")
        
        try:
            headers = {}
            if resume_offset > 0 and self.check_range_support(url):
                headers['Range'] = f'bytes={resume_offset}-'
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            
            open_mode = 'ab' if resume_offset > 0 else 'wb'
            with open(output_path, open_mode) as f:
                chunk_size = 5 * 1024 * 1024  # 每块 5MB
                bytes_downloaded = 0
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        
                        if show_progress:
                            progress = (downloaded_size + bytes_downloaded) / total_size * 100
                            print(f"\r[进度] {progress:>6.1f}% [{downloaded_size+bytes_downloaded:>12.2f}/{total_size:>12.2f}MB]", end='', flush=True)
            
            if show_progress:
                print()
            
            final_size = output_path.stat().st_size
            print(f"✅ [完成] 实际下载 {final_size/1024/1024:.2f}MB")
            return (final_size >= total_size * 0.99)  # 99% 以上视为成功
            
        except Exception as e:
            print(f"\n❌ [失败] {e}")
            return False
    
    def download_chunk(
        self, 
        url: str, 
        start: int, 
        end: int, 
        chunk_id: int
    ) -> Tuple[int, bytes, Optional[str]]:
        """下载一个分片"""
        headers = {'Range': f'bytes={start}-{end}'}
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 206:
                data = response.content
                print(f"  [线程 {chunk_id}] ✓ ({(end-start+1)/1024/1024:.1f}MB)")
                return (chunk_id, data, None)
            else:
                return (chunk_id, b'', f"HTTP{response.status_code}")
        except Exception as e:
            return (chunk_id, b'', str(e)[:100])
    
    def download_multi_thread(self, url: str, output_path: Path, thread_count: int, show_progress: bool = True) -> bool:
        """多线程分片下载"""
        
        # Check range support first
        if not self.check_range_support(url):
            print("[警告] 服务器不支持 Range 请求，降级到单线程")
            return self.download_single_thread(url, output_path, 0, show_progress)
        
        total_size = self.get_file_size(url)
        if total_size == 0:
            print("[错误] 无法获取文件大小")
            return False
        
        resumed_bytes = output_path.stat().st_size if output_path.exists() else 0
        if resumed_bytes > 0:
            print(f"[续传] 已有 {resumed_bytes/1024/1024:.2f}MB")
        
        remaining = total_size - resumed_bytes
        if remaining <= 0:
            print("[跳过] 文件已完整")
            return True
        
        # Calculate chunks
        chunk_size = remaining // thread_count
        ranges = []
        for i in range(thread_count):
            start = resumed_bytes + i * chunk_size
            end = total_size - 1 if i == thread_count - 1 else start + chunk_size - 1
            ranges.append((start, end, i))
        
        # Start parallel downloads
        print(f"\n[开始] {thread_count} 线程并发下载...")
        results = [None] * thread_count
        started_time = time.time()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = {
                executor.submit(self.download_chunk, url, start, end, chunk_id): chunk_id
                for start, end, chunk_id in ranges
            }
            
            last_update = time.time()
            total_downloaded = resumed_bytes
            
            for future in as_completed(futures):
                chunk_id, data, error = future.result()
                results[chunk_id] = (data, error)
                
                if data:
                    total_downloaded += len(data)
                
                # Real-time progress update
                now = time.time()
                elapsed = now - started_time
                if now - last_update >= 0.5 or all(r is not None for r in results):
                    speed = total_downloaded / max(elapsed, 0.1) / 1024 / 1024
                    eta = (total_size - total_downloaded) / max(speed, 0.01) / 60
                    percent = total_downloaded / total_size * 100
                    
                    print(f"\r[进度] {percent:>6.1f}% | "
                          f"{total_downloaded/1024/1024:>8.2f}/{total_size/1024/1024:.2f}MB | "
                          f"{speed:>7.2f}MB/s | ETA: {eta:>6.1f}min ", 
                          end='', flush=True)
                    last_update = now
        
        print()
        
        # Validate all chunks succeeded
        failed = [(i, err) for i, (data, err) in enumerate(results) if err is not None]
        if failed:
            print(f"\n❌ [失败] {len(failed)}个分片下载异常:")
            for idx, err in failed[:3]:
                print(f"   Chunk {idx}: {err}")
            return False
        
        # Merge to final file
        temp_file = output_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'wb') as f:
                for chunk_data, _ in results:
                    f.write(chunk_data)
            
            shutil.move(temp_file, output_path)
            
            final_size = output_path.stat().st_size
            diff_percent = abs(final_size - total_size) / total_size * 100
            print(f"\n✅ [完成] {final_size/1024/1024:.2f}MB (差异 {diff_percent:.2f}%) - 耗时 {elapsed:.1f}s")
            return diff_percent < 1  # 允许 1% 误差
            
        except Exception as e:
            print(f"\n❌ [错误] 合并失败：{e}")
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def download_with_resume(
        self,
        url: str,
        filename: str,
        base_dir: str = "./downloads",
        show_progress: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        自动选择最佳下载方式（单线程/多线程）
        
        Returns:
            (是否成功，保存路径或错误原因)
        """
        output_dir = Path(base_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        # Get metadata
        total_size = self.get_file_size(url)
        if total_size == 0:
            return (False, "无法获取文件大小")
        
        size_mb = total_size / 1024 / 1024
        existing_size = output_path.stat().st_size if output_path.exists() else 0
        
        if existing_size >= total_size * 0.99:
            print(f"[跳过] {filename} 已存在且完整")
            return (True, str(output_path))
        
        # Decide strategy
        if size_mb < self.min_file_mb or existing_size == 0:
            print(f"[策略] {size_mb:.1f}MB < {self.min_file_mb:.0f}MB，使用单线程下载")
            success = self.download_single_thread(url, output_path, existing_size, show_progress)
        else:
            threads = self.calculate_optimal_threads(size_mb)
            print(f"[策略] {size_mb:.1f}MB ≥ {self.min_file_mb:.0f}MB，启用 {threads} 线程加速下载")
            success = self.download_multi_thread(url, output_path, threads, show_progress)
        
        return (success, str(output_path) if success else "下载失败")


class SmartDownloader:
    """智能模型下载管理器（支持官方 SDK + 直接 URL）"""
    
    MODELS_REGISTRY = {
        'modelscope': {
            'type': 'modelscope',
            'repo': 'damo/text-to-video-synthesis',
            'path_pattern': 'modelscope/hub/cache/damo_text-to-video-synthesis',
            'estimated_size_mb': 1500
        },
        'animatediff': {
            'type': 'huggingface',
            'repo': 'guoyww/animatediff-motion.module-v1',
            'path_pattern': 'models--guoyww--animatediff-motion.module-v1',
            'estimated_size_mb': 1200
        },
        'cogvideox': {
            'type': 'huggingface',
            'repo': 'THUDM/cogvideox-5b',
            'path_pattern': 'models--THUDM--cogvideox-5b',
            'estimated_size_mb': 5200
        }
    }
    
    def __init__(self, output_dir: str = "./models", use_multithread: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mt_downloader = MultiThreadDownloader(num_threads=4) if use_multithread else None
    
    def check_existing(self, model_name: str) -> Tuple[bool, Optional[Path]]:
        """检查模型是否已下载"""
        model_info = self.MODELS_REGISTRY.get(model_name)
        if not model_info:
            return (False, None)
        
        model_type = model_info.get('type', '')
        repo = model_info.get('repo', '')
        path_pattern = model_info.get('path_pattern', '')
        
        # 构建主要检查路径
        check_path = self.output_dir / path_pattern
        
        # 如果主路径存在且有文件，返回成功
        if check_path.exists() and any(check_path.rglob('*')):
            return (True, check_path)
        
        # 回退：检查其他可能的路径
        possible_paths = []
        
        if model_type == 'modelscope':
            repo_id_underscore = repo.replace('/', '_')
            possible_paths = [
                self.output_dir / "modelscope" / "hub" / "models" / repo,
                self.output_dir / repo,
                self.output_dir / repo_id_underscore,
            ]
        elif model_type == 'huggingface':
            repo_parts = repo.split('/')
            if len(repo_parts) == 2:
                possible_paths = [
                    self.output_dir / "huggingface" / f"models--{repo_parts[0]}--{repo_parts[1]}",
                    self.output_dir / "huggingface" / repo.replace('/', '--'),
                ]
        
        for alt_path in possible_paths:
            if alt_path.exists() and any(alt_path.rglob('*')):
                return (True, alt_path)
        
        return (False, None)
    
    def download_from_modelscope(self, repo_id: str, resume: bool = True) -> Optional[str]:
        """从 ModelScope 下载模型（支持续传）"""
        import logging
        import shutil
        try:
            from modelscope import snapshot_download
            from modelscope.utils.constant import DEFAULT_MODEL_REVISION
            
            # 目标路径：强制下载到项目目录
            repo_id_underscore = repo_id.replace('/', '_')
            target_dir = self.output_dir / "modelscope" / "hub" / "cache" / repo_id_underscore
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否已存在
            if resume and target_dir.exists():
                existing_files = sum(1 for f in target_dir.rglob("*") if f.is_file())
                existing_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                print(f"[ModelScope 下载] ✅ 发现已下载部分文件")
                print(f"  📁 路径：{target_dir}")
                print(f"  📦 已有文件：{existing_files} 个")
                print(f"  💾 已下载：{existing_size / 1024 / 1024:.2f}MB")
                print(f"  🔄 检查续传中...")
            
            print(f"[ModelScope 下载] 开始下载 {repo_id}...")
            
            # 配置日志级别
            logging.getLogger("modelscope").setLevel(logging.INFO)
            
            # 使用 local_dir 参数强制下载到指定目录
            model_path = snapshot_download(
                repo_id,
                local_dir=str(target_dir),
                revision=DEFAULT_MODEL_REVISION
            )
            
            # 验证下载结果
            # snapshot_download 可能返回的是 cache 路径，我们需要确认 target_dir 有文件
            if target_dir.exists() and any(target_dir.rglob('*')):
                total_files = sum(1 for f in target_dir.rglob("*") if f.is_file())
                total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                print(f"[ModelScope 下载] ✅ 下载完成")
                print(f"  📁 路径：{target_dir}")
                print(f"  📦 文件数：{total_files} 个")
                print(f"  💾 总大小：{total_size / 1024 / 1024:.2f}MB")
                return str(target_dir)
            elif os.path.exists(model_path):
                # 如果返回的路径不是 target_dir，尝试移动
                print(f"[ModelScope 下载] ⚠️  SDK 下载到 {model_path}，移动到 {target_dir}")
                if model_path != str(target_dir):
                    shutil.move(model_path, str(target_dir))
                total_files = sum(1 for f in target_dir.rglob("*") if f.is_file())
                total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                print(f"[ModelScope 下载] ✅ 下载完成")
                print(f"  📁 路径：{target_dir}")
                print(f"  📦 文件数：{total_files} 个")
                print(f"  💾 总大小：{total_size / 1024 / 1024:.2f}MB")
                return str(target_dir)
            else:
                print(f"[ModelScope 下载] ❌ 下载失败：路径不存在")
                return None
                
        except ImportError:
            return "缺少依赖：pip install modelscope"
        except Exception as e:
            print(f"❌ [ModelScope] 下载失败：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_from_huggingface(self, repo_id: str, variant: str = None, resume: bool = True) -> Optional[str]:
        """从 HuggingFace 下载模型"""
        import shutil
        try:
            from huggingface_hub import snapshot_download
            
            # 目标路径：强制下载到项目目录
            repo_parts = repo_id.split('/')
            if len(repo_parts) == 2:
                target_name = f"models--{repo_parts[0]}--{repo_parts[1]}"
            else:
                target_name = repo_id.replace('/', '--')
            
            target_dir = self.output_dir / target_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否已存在
            if resume and target_dir.exists() and any(target_dir.rglob('*')):
                existing_files = sum(1 for f in target_dir.rglob("*") if f.is_file())
                existing_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                print(f"[HuggingFace 下载] ✅ 发现已下载部分文件")
                print(f"  📁 路径：{target_dir}")
                print(f"  📦 已有文件：{existing_files} 个")
                print(f"  💾 已下载：{existing_size / 1024 / 1024:.2f}MB")
                print(f"  🔄 检查续传中...")
            
            print(f"[HuggingFace 下载] 开始下载 {repo_id}...")
            
            kwargs = {
                "repo_id": repo_id,
                "local_dir": str(target_dir),
                "repo_type": "model",
            }
            
            if variant:
                kwargs["variant"] = variant
            
            model_path = snapshot_download(**kwargs)
            
            # 验证下载结果
            if target_dir.exists() and any(target_dir.rglob('*')):
                total_files = sum(1 for _ in target_dir.rglob('*') if _.is_file())
                total_size = sum(_.stat().st_size for _ in target_dir.rglob('*') if _.is_file())
                print(f"✅ [HuggingFace] 下载完成 | {total_files}个文件 | {total_size/1024/1024:.2f}MB")
                print(f"  📁 路径：{target_dir}")
                return str(target_dir)
            elif os.path.isdir(model_path):
                # SDK 返回的路径不是 target_dir，尝试移动
                print(f"[HuggingFace 下载] ⚠️  SDK 下载到 {model_path}，移动到 {target_dir}")
                if model_path != str(target_dir):
                    shutil.move(model_path, str(target_dir))
                total_files = sum(1 for _ in target_dir.rglob('*') if _.is_file())
                total_size = sum(_.stat().st_size for _ in target_dir.rglob('*') if _.is_file())
                print(f"✅ [HuggingFace] 下载完成 | {total_files}个文件 | {total_size/1024/1024:.2f}MB")
                print(f"  📁 路径：{target_dir}")
                return str(target_dir)
            else:
                print(f"⚠️ [HuggingFace] 下载成功但路径校验失败")
                return None
                
        except ImportError:
            return "缺少依赖：pip install huggingface-hub"
        except Exception as e:
            print(f"❌ [HuggingFace] 下载失败：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_single(self, model_name: str) -> Dict:
        """下载单个模型"""
        model_info = self.MODELS_REGISTRY.get(model_name)
        
        if not model_info:
            return {'name': model_name, 'success': False, 'error': '未找到模型定义', 'path': None}
        
        # Check if already exists
        exists, path_hint = self.check_existing(model_name)
        if exists:
            return {'name': model_name, 'success': True, 'error': None, 'path': str(path_hint), 'skipped': True}
        
        try:
            if model_info['type'] == 'modelscope':
                result_path = self.download_from_modelscope(model_info['repo'])
            elif model_info['type'] == 'huggingface':
                result_path = self.download_from_huggingface(model_info['repo'])
            elif self.mt_downloader and model_info.get('url'):
                # Direct URL download with multi-thread
                filename = f"{model_name}_model.bin"
                success, path_or_err = self.mt_downloader.download_with_resume(
                    model_info['url'], filename, str(self.output_dir)
                )
                result_path = path_or_err if success else None
            
            if result_path is None or isinstance(result_path, str) and result_path.startswith(('缺少', '❌')):
                return {'name': model_name, 'success': False, 'error': result_path, 'path': None}
            
            return {'name': model_name, 'success': True, 'error': None, 'path': result_path}
            
        except Exception as e:
            return {'name': model_name, 'success': False, 'error': str(e), 'path': None}
    
    def download_batch(self, model_names: List[str], parallel: int = 2) -> List[Dict]:
        """批量并行下载多个模型"""
        if not model_names:
            return []
        
        if parallel <= 1:
            # Sequential download
            return [self.download_single(name) for name in model_names]
        
        # Parallel downloads
        results = []
        with ThreadPoolExecutor(max_workers=min(parallel, len(model_names))) as executor:
            futures = [executor.submit(self.download_single, model) for model in model_names]
            for future in as_completed(futures):
                results.append(future.result())
        
        return results


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="智能模型下载器 V2")
    parser.add_argument('--models', '-m', nargs='+', default=['modelscope'])
    parser.add_argument('--output', '-o', default='./models')
    parser.add_argument('--parallel', '-j', type=int, default=2, help='并发下载任务数')
    parser.add_argument('--disable-mt', action='store_true', help='禁用多线程下载单个大文件')
    args = parser.parse_args()
    
    downloader = SmartDownloader(output_dir=args.output, use_multithread=(not args.disable_mt))
    
    # Filter out existing ones
    to_download = []
    for name in args.models:
        exists, _ = downloader.check_existing(name)
        if not exists:
            to_download.append(name)
        else:
            print(f"✓ {name} 已存在，跳过")
    
    if not to_download:
        print("\n所有模型已安装完毕！")
        return 0
    
    print(f"\n需要下载 {len(to_download)} 个模型：{', '.join(to_download)}")
    print("="*70)
    
    # Execute batch download
    results = downloader.download_batch(to_download, parallel=args.parallel)
    
    # Summary
    print("\n" + "="*70)
    success_count = sum(1 for r in results if r.get('success'))
    skip_count = sum(1 for r in results if r.get('skipped'))
    fail_count = len(results) - success_count
    
    print(f"\n📊 汇总报告:")
    print(f"  成功：{success_count}")
    print(f"  跳过：{skip_count}")
    print(f"  失败：{fail_count}")
    
    if fail_count > 0:
        print(f"\n⚠️  失败的模型:")
        for r in results:
            if not r.get('success'):
                print(f"  - {r['name']}: {r.get('error', '未知错误')}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())


# =====================
# 向后兼容层 - ModelDownloader 别名
# =====================

class ModelDownloader(SmartDownloader):
    """向后兼容的 ModelDownloader 类（兼容旧版 API）"""

    def __init__(self, output_dir: str = "./models", max_workers: int = 2, **kwargs):
        super().__init__(output_dir=output_dir, use_multithread=True)
        self.max_workers = max_workers

    @property
    def model_repos(self):
        """兼容旧版的 model_repos 属性"""
        return self.MODELS_REGISTRY

    def check_existing_models(self, model_names: List[str]) -> Dict[str, bool]:
        """兼容旧版的 check_existing_models 方法"""
        result = {}
        for name in model_names:
            exists, _ = self.check_existing(name)
            result[name] = exists
        return result

    def create_model_zip(self, model_name: str, compress_level: int = 9, auto_extract: bool = True) -> Dict:
        """创建模型压缩包（简化版）"""
        model_info = self.MODELS_REGISTRY.get(model_name)
        if not model_info:
            return {'success': False, 'error': f'未知模型：{model_name}'}

        exists, model_path = self.check_existing(model_name)
        if not exists:
            return {'success': False, 'error': f'模型 {model_name} 未安装'}

        import zipfile
        zip_name = f"{model_name}_model.zip"
        zip_path = self.output_dir / zip_name

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in model_path.rglob('*'):
                    if f.is_file():
                        arcname = f.relative_to(model_path.parent)
                        zf.write(f, arcname)

            result = {'success': True, 'zip_path': str(zip_path)}
            if auto_extract:
                result['extract_result'] = '自动解压功能需要手动操作'
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
