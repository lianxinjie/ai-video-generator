#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动下载 FFmpeg 脚本 - 完整版

支持:
- Windows (x64), Linux (x64, arm64), macOS (intel, arm64)
- 断点续传：自动恢复中断的下载
- 多线程下载：显著提高大文件下载速度（4 线程）
"""

import sys
import platform
import subprocess
import requests
from pathlib import Path
import zipfile
import tarfile
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from tqdm import tqdm

# 全局配置
THREAD_COUNT = 4  # 多线程下载线程数
RESUME_ENABLED = True  # 启用断网续传
CHUNK_SIZE = 1024 * 1024  # 每个线程下载块大小（1MB）

print("=" * 60)
print("🎬 FFmpeg 自动下载工具 v2.0（多线程版）")
print("=" * 60)

# 检测系统
system = platform.system().lower()
arch = platform.machine().lower()

print(f"\n系统信息:")
print(f"  操作系统：{system}")
print(f"  架构：{arch}")

# FFmpeg 下载配置
ffmpeg_urls = {
    'windows': {
        'x86_64': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        'amd64': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
    },
    'linux': {
        'x86_64': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
        'amd64': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
        'arm64': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz',
    },
    'darwin': {
        'x86_64': 'https://evermeet.cx/ffmpeg/getrelease/zip',
        'arm64': 'https://evermeet.cx/ffmpeg/getrelease/zip',
    }
}

# 备用镜像（主镜像失败时使用）
mirror_urls = {
    'main': ffmpeg_urls,
    'mirror1': {
        'windows': {
            'x86_64': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
        },
        'linux': {
            'x86_64': 'https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v5.1/ffmpeg-5.1-linux-64.zip',
        }
    }
}

# 输出目录
output_dir = Path("./ffmpeg")
temp_dir = Path("./temp_ffmpeg")

def get_file_size(url, timeout=10):
    """获取远程文件大小"""
    try:
        head = requests.head(url, timeout=timeout, allow_redirects=True)
        return int(head.headers.get('content-length', 0))
    except Exception:
        return 0

def check_resume_support(url, timeout=10):
    """检查服务器是否支持断点续传"""
    try:
        head = requests.head(url, timeout=timeout, allow_redirects=True)
        accept_ranges = head.headers.get('accept-ranges', '').lower() == 'bytes'
        return accept_ranges
    except Exception:
        return False

def download_chunk(url, start, end, chunk_id, results):
    """
    下载文件块（线程函数）
    
    Args:
        url: 下载 URL
        start: 开始字节
        end: 结束字节
        chunk_id: 块 ID
        results: 结果字典 {chunk_id: bytes}
    """
    try:
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 206:
            results[chunk_id] = response.content
            return True
        else:
            return False
    except Exception as e:
        print(f"  线程 {chunk_id} 下载失败：{e}")
        return False

def download_file_multithread(url, path, thread_count=4, resume=True):
    """
    多线程下载文件，支持断点续传
    
    Args:
        url: 下载 URL
        path: 保存路径
        thread_count: 线程数
        resume: 是否启用断点续传
    
    Returns:
        bool: 下载是否成功
    """
    try:
        # 获取文件大小
        print(f"  📊 获取文件信息...")
        total_size = get_file_size(url)
        
        if total_size == 0:
            print(f"  ⚠️  无法获取文件大小，使用单线程下载")
            return download_file_single(url, path, resume)
        
        # 检查是否支持断点续传
        supports_resume = check_resume_support(url)
        if not supports_resume and resume:
            print(f"  ⚠️  服务器不支持断点续传，使用单线程下载")
            return download_file_single(url, path, False)
        
        # 检查已下载部分
        downloaded_size = 0
        if path.exists() and resume:
            downloaded_size = path.stat().st_size
            if downloaded_size >= total_size:
                print(f"  ✅ 文件已完整下载")
                return True
            print(f"  📥 发现未完成文件：{downloaded_size/1024/1024:.2f}MB / {total_size/1024/1024:.2f}MB")
        
        remaining_size = total_size - downloaded_size
        
        # 如果剩余数据太小，使用单线程
        if remaining_size < 5 * 1024 * 1024 or thread_count <= 1:
            return download_file_single(url, path, resume)
        
        # 创建进度条
        pbar = tqdm(
            total=remaining_size,
            unit='B',
            unit_scale=True,
            desc=f"  下载 ({thread_count}线程)",
            ncols=80,
            initial=downloaded_size if resume else 0
        )
        
        # 计算每个线程的下载范围
        chunk_size = remaining_size // thread_count
        ranges = []
        for i in range(thread_count):
            start = downloaded_size + i * chunk_size
            end = total_size if i == thread_count - 1 else start + chunk_size - 1
            ranges.append((start, end, i))
        
        # 使用线程池下载
        results = {}
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = {}
            for start, end, chunk_id in ranges:
                future = executor.submit(
                    download_chunk,
                    url, start, end, chunk_id, results
                )
                futures[future] = chunk_id
            
            # 等待所有线程完成
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
        
        pbar.close()
        
        # 检查结果
        if success_count == thread_count:
            # 按顺序合并数据
            sorted_results = [results[i] for i in range(thread_count)]
            
            # 写入文件
            mode = 'ab' if (path.exists() and resume) else 'wb'
            with open(path, mode) as f:
                for chunk in sorted_results:
                    f.write(chunk)
            
            print(f"  ✅ 下载完成：{path.name}")
            return True
        else:
            print(f"  ❌ 部分线程下载失败 ({success_count}/{thread_count})")
            # 回退到单线程重试
            print(f"  🔄 尝试单线程下载...")
            return download_file_single(url, path, False)
    
    except Exception as e:
        print(f"  ❌ 多线程下载失败：{e}")
        print(f"  🔄 回退到单线程下载...")
        return download_file_single(url, path, False)

def download_file_single(url, path, resume=True):
    """
    单线程下载文件（备用方案）
    
    Args:
        url: 下载 URL
        path: 保存路径
        resume: 是否启用断点续传
    
    Returns:
        bool: 下载是否成功
    """
    try:
        # 检查已下载部分
        downloaded_size = 0
        if path.exists() and resume:
            downloaded_size = path.stat().st_size
        
        # 创建进度条
        total_size = get_file_size(url)
        pbar = tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=f"  下载 (单线程)",
            ncols=80,
            initial=downloaded_size
        )
        
        # 设置 Range 头
        headers = {}
        if resume and downloaded_size > 0:
            headers['Range'] = f'bytes={downloaded_size}-'
        
        # 下载文件
        with requests.get(url, headers=headers, stream=True, timeout=30) as response:
            response.raise_for_status()
            
            mode = 'ab' if (path.exists() and resume) else 'wb'
            with open(path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        pbar.close()
        print(f"  ✅ 下载完成：{path.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ 单线程下载失败：{e}")
        return False

def download_with_progress(url, path):
    """
    下载函数（统一入口）
    自动选择多线程或单线程下载
    
    Args:
        url: 下载 URL
        path: 保存路径
    
    Returns:
        bool: 下载是否成功
    """
    print(f"  📥 开始下载...")
    print(f"  📊 文件信息:")
    
    # 获取文件大小
    total_size = get_file_size(url)
    if total_size > 0:
        size_mb = total_size / 1024 / 1024
        print(f"     大小：{size_mb:.2f} MB")
        print(f"     线程数：{THREAD_COUNT}")
    
    # 使用多线程下载
    success = download_file_multithread(
        url,
        path,
        thread_count=THREAD_COUNT,
        resume=RESUME_ENABLED
    )
    
    return success

# 主程序开始
print(f"\n下载配置:")
print(f"  输出目录：{output_dir.absolute()}")
print(f"  线程数：{THREAD_COUNT}")
print(f"  断点续传：{'✅ 启用' if RESUME_ENABLED else '❌ 禁用'}")

try:
    # 获取下载 URL
    if system not in ffmpeg_urls:
        print(f"\n❌ 不支持的操作系统：{system}")
        print(f"\n请手动安装 FFmpeg:")
        print(f"  - Windows: https://www.gyan.dev/ffmpeg/builds/")
        print(f"  - Linux: sudo apt install ffmpeg")
        print(f"  - macOS: brew install ffmpeg")
        sys.exit(1)
    
    if arch not in ffmpeg_urls[system]:
        print(f"\n❌ 不支持的架构：{arch}")
        sys.exit(1)
    
    url = ffmpeg_urls[system][arch]
    print(f"\n🌐 下载地址：{url}")
    
    # 下载文件名
    filename = url.split('/')[-1]
    download_path = temp_dir / filename
    
    # 创建临时目录
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载
    print(f"\n📥 开始下载：{filename}")
    
    if not download_with_progress(url, download_path):
        print(f"\n❌ 下载失败，请检查网络连接")
        sys.exit(1)
    
    # 解压
    print(f"\n📦 正在解压...")
    
    if filename.endswith('.zip'):
        with zipfile.ZipFile(download_path, 'r') as z:
            names = z.namelist()
            ffmpeg_dir = None
            for name in names:
                if 'ffmpeg.exe' in name or 'ffprobe.exe' in name:
                    ffmpeg_dir = name.split('/')[0]
                    break
            
            if ffmpeg_dir:
                z.extractall(temp_dir)
                src_bin = temp_dir / ffmpeg_dir / 'bin'
                if src_bin.exists():
                    shutil.copytree(src_bin, output_dir / 'bin', dirs_exist_ok=True)
                else:
                    for name in names:
                        if name.endswith('ffmpeg.exe') or name.endswith('ffprobe.exe'):
                            z.extract(name, temp_dir)
                            shutil.move(temp_dir / name, output_dir / Path(name).name)
            else:
                z.extractall(output_dir)
    elif filename.endswith('.tar.xz') or filename.endswith('.tar.gz'):
        with tarfile.open(download_path, 'r:*') as t:
            t.extractall(temp_dir)
            for member in t.getmembers():
                name = member.name
                if name.endswith('ffmpeg') or name.endswith('ffprobe'):
                    t.extract(member, temp_dir)
                    src = temp_dir / name
                    dst = output_dir / 'bin' / Path(name).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
    elif filename.endswith('.tar.bz2'):
        with tarfile.open(download_path, 'r:bz2') as t:
            t.extractall(temp_dir)
            for member in t.getmembers():
                name = member.name
                if 'ffmpeg' in name or 'ffprobe' in name:
                    t.extract(member, temp_dir)
                    src = temp_dir / Path(name)
                    dst = output_dir / 'bin' / src.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
    
    # 验证
    ffmpeg_path = output_dir / 'bin' / ('ffmpeg.exe' if system == 'windows' else 'ffmpeg')
    if not ffmpeg_path.exists():
        for f in output_dir.glob('**/ffmpeg*'):
            if f.is_file():
                ffmpeg_path = f
                break
    
    if ffmpeg_path.exists():
        print(f"\n✅ FFmpeg 下载成功!")
        print(f"  路径：{ffmpeg_path.absolute()}")
        
        # 验证版本
        result = subprocess.run(
            [str(ffmpeg_path), '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"  版本：{result.stdout.splitlines()[0]}")
        
        # 添加到 PATH 提示
        if system == 'windows':
            print(f"\n💡 提示：FFmpeg 已下载，需要添加到系统 PATH 才能全局使用")
            print(f"  方法 1: 手动添加环境变量:")
            print(f"     右键此电脑 → 属性 → 高级系统设置 → 环境变量")
            print(f"     在 Path 中添加：{output_dir.absolute()}\\bin")
            print(f"  方法 2: 使用命令行临时添加:")
            print(f"     $env:Path += \";{output_dir.absolute()}\\bin\"")
            print(f"  方法 3: 重启服务，程序会自动使用本地 FFmpeg")
        
        print(f"\n✅ 完成!")
    else:
        print(f"\n⚠️ FFmpeg 文件未找到，请检查输出目录：{output_dir.absolute()}")

except KeyboardInterrupt:
    print(f"\n\n🛑 下载被用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 发生错误：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # 清理临时文件
    if temp_dir.exists():
        print(f"\n🧹 正在清理临时文件...")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"  ✅ 临时文件已清理")
        except Exception:
            pass
