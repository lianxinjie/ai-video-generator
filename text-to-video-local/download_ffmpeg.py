#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动下载 FFmpeg 脚本

支持:
- Windows (x64)
- Linux (x64, arm64)
- macOS (intel, arm64)
"""

import sys
import platform
import subprocess
from pathlib import Path
from urllib import request
import zipfile
import tarfile
import shutil

print("=" * 60)
print("🎬 FFmpeg 自动下载工具")
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
        'x86_64': 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz',
        'aarch64': 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-arm64-static.tar.xz',
        'arm64': 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-arm64-static.tar.xz',
    },
    'darwin': {
        'x86_64': 'https://evermeet.cx/ffmpeg/getrelease/zip',
        'arm64': 'https://evermeet.cx/ffmpeg/getrelease/zip',
    }
}

print(f"\n正在准备下载...")

# 创建临时目录
temp_dir = Path('./temp_ffmpeg')
temp_dir.mkdir(exist_ok=True)

output_dir = Path('./ffmpeg')
output_dir.mkdir(exist_ok=True)

try:
    # 获取下载 URL
    if system not in ffmpeg_urls:
        print(f"❌ 不支持的操作系统：{system}")
        print(f"\n请手动安装 FFmpeg:")
        print(f"  - Windows: https://www.gyan.dev/ffmpeg/builds/")
        print(f"  - Linux: sudo apt install ffmpeg")
        print(f"  - macOS: brew install ffmpeg")
        sys.exit(1)
    
    if arch not in ffmpeg_urls[system]:
        print(f"❌ 不支持的架构：{arch}")
        sys.exit(1)
    
    url = ffmpeg_urls[system][arch]
    print(f"  下载地址：{url}")
    
    # 下载文件名
    filename = url.split('/')[-1]
    download_path = temp_dir / filename
    
    # 下载
    print(f"  开始下载：{filename}")
    print(f"  这可能需要 1-5 分钟，请耐心等待...")
    
    def download_with_progress(url, path):
        import urllib.request
        import urllib.error
        
        try:
            urllib.request.urlretrieve(url, path, reporthook=lambda b, bs, t: print(f"  进度：{b*bs/t*100:.0f}%", end='\r'))
            print()  # 换行
            return True
        except Exception as e:
            print(f"\n  下载失败：{e}")
            return False
    
    if not download_with_progress(url, download_path):
        print(f"\n下载失败，请检查网络连接")
        sys.exit(1)
    
    # 解压
    print(f"\n正在解压...")
    
    if filename.endswith('.zip'):
        with zipfile.ZipFile(download_path, 'r') as z:
            # 找到 ffmpeg.exe 所在的目录
            names = z.namelist()
            ffmpeg_dir = None
            for name in names:
                if 'ffmpeg.exe' in name or 'ffprobe.exe' in name:
                    ffmpeg_dir = name.split('/')[0]
                    break
            
            if ffmpeg_dir:
                z.extractall(temp_dir)
                # 复制到输出目录
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
            # 查找 ffmpeg 二进制文件
            for member in t.getmembers():
                if member.name.endswith('ffmpeg') or member.name.endswith('ffprobe'):
                    t.extract(member, temp_dir)
                    src = temp_dir / member.name
                    # 使用 bin 子目录保持一致性
                    dst = output_dir / 'bin' / src.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
    
    # 验证
    ffmpeg_path = output_dir / 'bin' / ('ffmpeg.exe' if system == 'windows' else 'ffmpeg')
    if not ffmpeg_path.exists():
        # 尝试直接查找
        for f in output_dir.glob('**/ffmpeg*'):
            if f.is_file():
                ffmpeg_path = f
                break
    
    if ffmpeg_path.exists():
        print(f"\n✅ FFmpeg 下载成功!")
        print(f"  路径：{ffmpeg_path.absolute()}")
        
        # 验证版本
        subprocess.run([str(ffmpeg_path), '-version'], check=True)
        
        # 添加到 PATH (Windows)
        if system == 'windows':
            print(f"\n💡 提示: FFmpeg 已下载，但需要添加到系统 PATH 才能全局使用")
            print(f"  方法 1: 手动添加环境变量:")
            print(f"    右键此电脑 → 属性 → 高级系统设置 → 环境变量")
            print(f"    在 Path 中添加：{output_dir.absolute()}\\bin")
            print(f"  方法 2: 使用命令行临时添加:")
            print(f"    $env:Path += \";{output_dir.absolute()}\\bin\"")
            print(f"  方法 3: 重启服务，程序会自动使用本地 FFmpeg")
        
        print(f"\n✓ 完成!")
    else:
        print(f"\n⚠️ FFmpeg 文件未找到，请检查输出目录：{output_dir.absolute()}")
    
except KeyboardInterrupt:
    print(f"\n\n下载被中断")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 发生错误：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # 清理临时文件
    if temp_dir.exists():
        print(f"\n正在清理临时文件...")
        shutil.rmtree(temp_dir, ignore_errors=True)
