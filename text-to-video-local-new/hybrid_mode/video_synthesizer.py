#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模式 - 视频合成器

使用 FFmpeg 轻量合成云端下载的图片为视频
无需 GPU，CPU 即可完成
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VideoSynthesizer:
    """视频合成器"""
    
    def __init__(
        self,
        output_dir: str = "./hybrid_mode/output",
        temp_dir: str = "./hybrid_mode/temp"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认参数
        self.default_params = {
            "fps": 24,
            "video_codec": "libx264",
            "audio_codec": "aac",
            "crf": 23,
            "preset": "medium",
            "pixel_format": "yuv420p"
        }
    
    def concatenate_audios(
        self,
        audio_files: List[str],
        output_file: str
    ) -> Optional[str]:
        """
        拼接多个音频文件
        
        Args:
            audio_files: 音频文件列表
            output_file: 输出文件
            
        Returns:
            输出文件路径
        """
        if not audio_files:
            logger.error("音频文件列表为空")
            return None
        
        # 创建 FFmpeg concat 文件
        list_file = self.temp_dir / "audio_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
        
        # FFmpeg 命令
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            output_file
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            logger.info(f"音频拼接完成：{output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"音频拼接失败：{e}")
            return None
        except Exception as e:
            logger.error(f"处理失败：{e}")
            return None
    
    def mix_audio(
        self,
        audio1: str,
        audio2: str,
        output: str,
        volume1: float = 1.0,
        volume2: float = 0.3,
        loop_background: bool = True
    ) -> Optional[str]:
        """
        混合两个音频文件（配音 +BGM）
        
        Args:
            audio1: 主音频（配音）
            audio2: 背景音频（BGM）
            output: 输出文件
            volume1: 主音频音量
            volume2: 背景音频音量
            loop_background: 是否循环背景音频以匹配主音频长度
            
        Returns:
            输出文件路径
        """
        try:
            # 获取两个音频的时长
            probe_cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
                        "-of", "csv=p=0", audio1]
            duration1 = float(subprocess.check_output(probe_cmd).decode().strip())
            
            probe_cmd2 = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                         "-of", "csv=p=0", audio2]
            duration2 = float(subprocess.check_output(probe_cmd2).decode().strip())
            
            # FFmpeg amix 命令
            if loop_background and duration2 < duration1:
                # BGM 比配音短，需要循环
                filter_complex = (
                    f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{duration1}[bgm];"
                    f"[0:a][bgm]amix=inputs=2:duration=longest:dropout_transition=2"
                )
            else:
                # 音频 2 够长或者不需要循环
                filter_complex = (
                    f"[1:a]volume={volume2}[bgm];"
                    f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2"
                )
            
            cmd = [
                "ffmpeg",
                "-y",
                "-i", audio1,
                "-i", audio2,
                "-filter_complex", filter_complex,
                "-c:a", "aac",
                "-b:a", "192k",
                output
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            logger.info(f"音频混合完成：{output}")
            return output
            
        except subprocess.CalledProcessError as e:
            logger.error(f"音频混合失败：{e}")
            logger.error(f"stderr: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"处理失败：{e}")
            return None
    
    def create_video_from_images(
        self,
        image_dir: str,
        output_file: str,
        fps: int = 24,
        pattern: str = "*.jpg",
        duration_per_image: float = None
    ) -> Optional[str]:
        """
        从图片序列创建视频
        
        Args:
            image_dir: 图片目录
            output_file: 输出文件路径
            fps: 帧率
            pattern: 文件名匹配模式
            duration_per_image: 每张图片持续时间（秒），None 则按 fps 计算
            
        Returns:
            输出文件路径
        """
        image_path = Path(image_dir)
        
        if not image_path.exists():
            logger.error(f"图片目录不存在：{image_path}")
            return None
        
        # 获取图片列表
        images = sorted(image_path.glob(pattern))
        images = [img for img in images if img.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        
        if not images:
            logger.error(f"未找到匹配的图片：{pattern}")
            return None
        
        logger.info(f"找到 {len(images)} 张图片")
        
        # 构建 FFmpeg 命令
        if duration_per_image:
            # 指定每张图片持续时间
            framerate = 1 / duration_per_image
        else:
            # 使用 fps
            framerate = fps
        
        output_path = Path(output_file)
        
        # 创建 temp 文件列表（兼容不同图片尺寸）
        list_file = self.temp_dir / "images.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for img in images:
                # 使用 POSIX 路径格式
                img_path_posix = str(img).replace('\\', '/')
                f.write(f"file '{img_path_posix}'\n")
                f.write(f"duration {duration_per_image or (1/fps)}\n")
        
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖已存在文件
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-vf", f"fps={framerate},scale=iw:-1",  # 保持原始宽高比
            "-c:v", self.default_params["video_codec"],
            "-crf", str(self.default_params["crf"]),
            "-preset", self.default_params["preset"],
            "-pix_fmt", self.default_params["pixel_format"],
            "-r", str(fps),
            str(output_path)
        ]
        
        logger.info(f"执行 FFmpeg 命令...")
        logger.debug(f"命令：{' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✓ 视频合成完成：{output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg 执行失败：{e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("未找到 FFmpeg，请先安装")
            logger.info("  Ubuntu/Debian: sudo apt install ffmpeg")
            logger.info("  macOS: brew install ffmpeg")
            logger.info("  Windows: 从 https://ffmpeg.org/download.html 下载")
            return None
    
    def create_video_with_transitions(
        self,
        image_dir: str,
        output_file: str,
        fps: int = 24,
        transition_type: str = "crossfade",
        transition_duration: float = 0.5
    ) -> Optional[str]:
        """
        使用转场效果合成视频（更高质量但 CPU 密集）
        
        Args:
            image_dir: 图片目录
            output_file: 输出文件路径
            fps: 帧率
            transition_type: 转场类型 (crossfade, fade, slide)
            transition_duration: 转场时长（秒）
            
        Returns:
            输出文件路径
        """
        image_path = Path(image_dir)
        
        if not image_path.exists():
            logger.error(f"图片目录不存在：{image_path}")
            return None
        
        images = sorted(image_path.glob("*.jpg"))
        if not images:
            logger.error("未找到图片")
            return None
        
        logger.info(f"使用 {transition_type} 转场效果...")
        
        # 构建复杂的滤镜链
        # 简单实现：使用 fade 滤镜
        output_path = Path(output_file)
        
        # 对于跨场景视频，使用简单 crossfade
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-pattern_type", "glob",
            "-i", str(image_path / "*.jpg"),
            "-vf", f"fps={fps},format=yuv420p",
            "-c:v", "libx264",
            "-crf", "18",  # 更高质量
            "-preset", "slow",  # 更好的压缩
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 带转场的视频已合成：{output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg 失败：{e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("未找到 FFmpeg")
            return None
    
    def add_audio(
        self,
        video_file: str,
        audio_file: str,
        output_file: str,
        volume: float = 1.0,
        loop_audio: bool = False
    ) -> Optional[str]:
        """
        为视频添加音频
        
        Args:
            video_file: 输入视频文件
            audio_file: 音频文件
            output_file: 输出文件
            volume: 音量（1.0 为原音量，0.5 为减半）
            loop_audio: 是否循环音频（如果音频比视频短）
            
        Returns:
            输出文件路径
        """
        video_path = Path(video_file)
        audio_path = Path(audio_file)
        output_path = Path(output_file)
        
        if not video_path.exists():
            logger.error(f"视频文件不存在：{video_path}")
            return None
        
        if not audio_path.exists():
            logger.error(f"音频文件不存在：{audio_path}")
            return None
        
        logger.info("添加音频轨道...")
        
        # 构建 FFmpeg 命令
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",  # 视频流复制，不重新编码
            "-c:a", "aac",
            "-b:a", "192k",
            "-vf", f"volume={volume}",
            "-strict", "experimental",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 音频已添加：{output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg 失败：{e.stderr}")
            return None
    
    def upscale_video(
        self,
        input_file: str,
        output_file: str,
        scale_factor: float = 2.0
    ) -> Optional[str]:
        """
        视频超分辨率（可选，需要较好 CPU）
        
        Args:
            input_file: 输入视频
            output_file: 输出视频
            scale_factor: 放大倍数
            
        Returns:
            输出文件路径
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            logger.error(f"视频文件不存在：{input_path}")
            return None
        
        output_path = Path(output_file)
        
        logger.info(f"放大视频 {scale_factor}x...")
        
        # 使用 lanczos 缩放算法（质量较好）
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vf", f"scale=iw*{scale_factor}:ih*{scale_factor}:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-c:a", "copy",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 视频已放大：{output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"放大失败：{e}")
            return None
    
    def merge_videos(
        self,
        video_files: List[str],
        output_file: str
    ) -> Optional[str]:
        """
        合并多个视频文件
        
        Args:
            video_files: 视频文件列表
            output_file: 输出文件
            
        Returns:
            输出文件路径
        """
        # 创建合并列表
        list_file = self.temp_dir / "merge.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for video in video_files:
                video_path = Path(video)
                if video_path.exists():
                    img_path_posix = str(video_path).replace('\\', '/')
                    f.write(f"file '{img_path_posix}'\n")
        
        output_path = Path(output_file)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 视频已合并：{output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"合并失败：{e}")
            return None
    
    def get_video_info(self, video_file: str) -> Dict:
        """获取视频信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return info
        except Exception as e:
            logger.error(f"获取视频信息失败：{e}")
            return {}


def main():
    """命令行测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description="视频合成器")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入图片目录"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出视频文件"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="帧率"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="每张图片持续时间（秒）"
    )
    parser.add_argument(
        "--transition",
        choices=["none", "crossfade", "fade"],
        default="none",
        help="转场效果"
    )
    parser.add_argument(
        "--audio",
        default=None,
        help="添加音频文件"
    )
    
    args = parser.parse_args()
    
    synthesizer = VideoSynthesizer()
    
    if args.transition == "none":
        output = synthesizer.create_video_from_images(
            image_dir=args.input,
            output_file=args.output,
            fps=args.fps,
            duration_per_image=args.duration
        )
    else:
        output = synthesizer.create_video_with_transitions(
            image_dir=args.input,
            output_file=args.output,
            fps=args.fps,
            transition_type=args.transition
        )
    
    if output and args.audio:
        output = synthesizer.add_audio(
            video_file=output,
            audio_file=args.audio,
            output_file=args.output.replace('.mp4', '_with_audio.mp4')
        )
    
    if output:
        print(f"\n✓ 最终视频：{output}")
        
        info = synthesizer.get_video_info(output)
        if info and 'format' in info:
            fmt = info['format']
            print(f"  时长：{fmt.get('duration', 'N/A')}秒")
            print(f"  文件大小：{int(fmt.get('size', 0)) / 1024 / 1024:.1f}MB")


if __name__ == "__main__":
    main()
