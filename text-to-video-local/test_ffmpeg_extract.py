#!/usr/bin/env python3
"""测试 FFmpeg 解压逻辑"""

from pathlib import Path
import zipfile
import tarfile
import shutil
import subprocess as sp
import tempfile

def test_extract():
    """测试解压逻辑"""
    
    print("="*60)
    print("测试 FFmpeg 解压逻辑")
    print("="*60)
    
    # 创建临时目录
    temp_dir = Path('./ffmpeg/test_extract')
    temp_dir.mkdir(exist_ok=True)
    
    output_dir = Path('./ffmpeg/test_bin')
    output_dir.mkdir(exist_ok=True)
    
    # 创建测试 ZIP
    test_zip = temp_dir / 'test.zip'
    
    print("\n1. 创建测试 ZIP 文件...")
    with zipfile.ZipFile(test_zip, 'w') as zf:
        # 模拟真实结构
        zf.writestr('ffmpeg-6.1-full_build-bin64/ffmpeg.exe', 'fake ffmpeg content')
        zf.writestr('ffmpeg-6.1-full_build-bin64/ffprobe.exe', 'fake ffprobe content')
        zf.writestr('ffmpeg-6.1-full_build-bin64/bin/ffmpeg.exe', 'fake ffmpeg in bin')
        zf.writestr('ffmpeg-6.1-full_build-bin64/bin/ffprobe.exe', 'fake ffprobe in bin')
    
    print(f"✓ 创建测试 ZIP: {test_zip}")
    
    # 测试解压
    print("\n2. 测试解压逻辑 (Windows 模式)...")
    with zipfile.ZipFile(test_zip, 'r') as zip_ref:
        names = zip_ref.namelist()
        print(f"  ZIP 包含 {len(names)} 个文件:")
        for name in names[:5]:
            print(f"    - {name}")
        
        # 找到顶层目录
        ffmpeg_dir = None
        for name in names:
            if 'ffmpeg' in name.lower() and name.endswith('/'):
                ffmpeg_dir = name.rstrip('/')
                break
        
        if not ffmpeg_dir:
            # 尝试从文件名推断
            for name in names:
                if '/' in name:
                    ffmpeg_dir = name.split('/')[0]
                    break
        
        print(f"  找到顶层目录：{ffmpeg_dir}")
        
        # 解压
        zip_ref.extractall(temp_dir)
        print(f"  ✓ 解压到：{temp_dir}")
        
        # 查找 bin 目录
        extracted_base = temp_dir / ffmpeg_dir
        src_bin = extracted_base / 'bin'
        
        print(f"  检查 bin 目录：{src_bin.exists()}")
        
        if src_bin.exists():
            # 复制到输出目录
            shutil.copytree(src_bin, output_dir, dirs_exist_ok=True)
            print(f"  ✓ 复制 bin/ 到输出目录")
            
            # 验证
            for f in output_dir.iterdir():
                print(f"    - {f.name}")
        else:
            print(f"  ✗ bin 目录不存在，尝试直接复制...")
            # 直接找 exe 文件
            for name in names:
                if name.endswith('ffmpeg.exe') or name.endswith('ffprobe.exe'):
                    zip_ref.extract(name, temp_dir)
                    src = temp_dir / name
                    dst = output_dir / src.name
                    shutil.copy2(src, dst)
                    print(f"  ✓ 复制：{src.name}")
    
    # 清理
    print("\n3. 清理测试文件...")
    shutil.rmtree(temp_dir)
    shutil.rmtree(output_dir)
    print("  ✓ 清理完成")
    
    print("\n✅ 测试完成")

if __name__ == '__main__':
    test_extract()
