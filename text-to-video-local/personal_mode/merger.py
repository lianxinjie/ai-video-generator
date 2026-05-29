#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合并模块 - 将多个视频片段合并为完整视频
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class VideoMerger:
    """视频合并器"""
    
    def __init__(self, project_dir: Path):
        """
        初始化视频合并器
        
        Args:
            project_dir: 项目目录
        """
        self.project_dir = Path(project_dir)
        self.ffmpeg_path = self._find_ffmpeg()
        
        logger.info(f"视频合并器初始化完成")
        if self.ffmpeg_path:
            logger.info(f"FFmpeg 路径：{self.ffmpeg_path}")
        else:
            logger.warning("未找到 FFmpeg，合并功能受限")
    
    def _find_ffmpeg(self) -> Optional[Path]:
        """查找 FFmpeg 可执行文件"""
        # 尝试在系统 PATH 中查找
        try:
            result = subprocess.run(
                ['which', 'ffmpeg'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass
        
        # 常见安装位置
        common_paths = [
            Path('/usr/bin/ffmpeg'),
            Path('/usr/local/bin/ffmpeg'),
            Path('C:\\Windows\\System32\\ffmpeg.exe'),
            Path('C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe'),
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        return None
    
    def merge_videos(
        self,
        chunk_pattern: str = "chunk_*.mp4",
        output_name: Optional[str] = None,
        add_transition: bool = False,
        cleanup_chunks: bool = False
    ) -> Optional[Path]:
        """
        合并所有视频片段
        
        Args:
            chunk_pattern: 片段文件匹配模式
            output_name: 输出文件名
            add_transition: 是否添加过渡效果
            cleanup_chunks: 合并后是否删除片段
            
        Returns:
            输出文件路径，失败返回 None
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg 不可用，无法合并视频")
            return None
        
        # 获取所有片段文件
        chunk_files = sorted(self.project_dir.glob(chunk_pattern))
        
        if not chunk_files:
            logger.error(f"未找到视频片段文件：{chunk_pattern}")
            return None
        
        logger.info(f"找到 {len(chunk_files)} 个视频片段")
        
        # 创建文件列表
        list_file = self.project_dir / "merge_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for chunk in chunk_files:
                f.write(f"file '{chunk.absolute()}'\n")
        
        # 输出文件名
        if output_name is None:
            output_file = self.project_dir / "output_merged.mp4"
        else:
            output_file = self.project_dir / output_name
        
        # 构建 FFmpeg 命令
        if add_transition:
            # 添加淡入淡出过渡
            cmd = self._build_transition_cmd(list_file, output_file, len(chunk_files))
        else:
            # 直接合并
            cmd = [
                str(self.ffmpeg_path),
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-c:v', 'copy',
                '-c:a', 'copy',
                str(output_file)
            ]
        
        logger.info(f"执行合并命令...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✓ 视频合并完成：{output_file}")
            
            # 清理临时文件
            list_file.unlink()
            
            if cleanup_chunks:
                self._cleanup_chunks(chunk_files)
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"合并失败：{e.stderr}")
            list_file.unlink()
            return None
    
    def _build_transition_cmd(
        self,
        list_file: Path,
        output_file: Path,
        num_chunks: int
    ) -> list:
        """构建带过渡效果的命令"""
        # 构建滤镜字符串
        filters = []
        for i in range(num_chunks):
            if i == 0:
                filters.append(f"[{i}:v]fade=t=in:st=0:d=0.3[v{i}]")
            elif i == num_chunks - 1:
                filters.append(f"[{i}:v]fade=t=out:st=0:d=0.3[v{i}]")
            else:
                filters.append(
                    f"[{i}:v]fade=t=in:st=0:d=0.15,fade=t=out:st=0.85:d=0.15[v{i}]"
                )
        
        concat_inputs = ' '.join([f"[v{i}]" for i in range(num_chunks)])
        filters.append(f"{concat_inputs}concat=n={num_chunks}:v=1:a=0[outv]")
        
        filter_complex = ';'.join(filters)
        
        return [
            str(self.ffmpeg_path),
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-c:v', 'libx264',
            '-crf', '23',
            str(output_file)
        ]
    
    def _cleanup_chunks(self, chunk_files: List[Path]):
        """清理片段文件"""
        for chunk in chunk_files:
            try:
                chunk.unlink()
                logger.debug(f"删除片段：{chunk}")
            except Exception as e:
                logger.warning(f"删除失败：{chunk} - {e}")
        
        logger.info(f"已清理 {len(chunk_files)} 个片段文件")
    
    def create_slideshow(
        self,
        images: List[Path],
        output_file: Path,
        duration_per_image: float = 1.0,
        fps: int = 30
    ) -> Optional[Path]:
        """
        从图片创建幻灯片视频
        
        Args:
            images: 图片文件路径列表
            output_file: 输出文件路径
            duration_per_image: 每张图片展示时长 (秒)
            fps: 帧率
            
        Returns:
            输出文件路径
        """
        if not self.ffmpeg_path:
            return None
        
        # 创建临时文件列表
        list_file = self.project_dir / "slideshow_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for img in images:
                # 每张图片重复指定帧数
                num_frames = int(duration_per_image * fps)
                for _ in range(num_frames):
                    f.write(f"file '{img.absolute()}'\n")
        
        try:
            cmd = [
                str(self.ffmpeg_path),
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-r', str(fps),
                '-c:v', 'libx264',
                '-crf', '23',
                str(output_file)
            ]
            
            subprocess.run(cmd, check=True)
            list_file.unlink()
            
            logger.info(f"幻灯片视频创建完成：{output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"创建失败：{e}")
            if list_file.exists():
                list_file.unlink()
            return None
    
    def add_background_music(
        self,
        video_file: Path,
        music_file: Path,
        output_file: Path,
        music_volume: float = 0.3
    ) -> Optional[Path]:
        """
        为视频添加背景音乐
        
        Args:
            video_file: 视频文件路径
            music_file: 音乐文件路径
            output_file: 输出文件路径
            music_volume: 音乐音量 (0.0-1.0)
            
        Returns:
            输出文件路径
        """
        if not self.ffmpeg_path:
            return None
        
        try:
            cmd = [
                str(self.ffmpeg_path),
                '-y',
                '-i', str(video_file),
                '-i', str(music_file),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-filter_complex',
                f'[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first',
                str(output_file)
            ]
            
            subprocess.run(cmd, check=True)
            
            logger.info(f"已添加背景音乐：{output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"添加背景音乐失败：{e}")
            return None
    
    def get_video_info(self, video_file: Path) -> Optional[Dict]:
        """
        获取视频信息
        
        Args:
            video_file: 视频文件路径
            
        Returns:
            视频信息字典
        """
        if not self.ffmpeg_path:
            return None
        
        try:
            cmd = [
                str(self.ffmpeg_path),
                '-i', str(video_file),
                '-hide_banner'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # 解析输出（简化的实现）
            info = {
                'file': str(video_file),
                'exists': video_file.exists()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取视频信息失败：{e}")
            return None
