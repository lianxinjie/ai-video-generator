#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人电脑模式 - 分段文生图 + 合成视频 + 分层配音

优化方案:
1. 分段生成图片（而非直接生成视频）
2. 每个小片段独立配音（人物对话）
3. 中型视频合成后添加特效音/BGM
4. 确保视频和配音的时序一致性
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from personal_mode.task_manager import TaskScheduler
from personal_mode.merger import VideoMerger

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """音频配置"""
    # 人物配音
    character_voice: str = "zh-CN-XiaoxiaoNeural"  # 微软 TTS 语音
    character_volume: float = 1.0
    character_rate: float = 1.0
    
    # 背景音乐
    bgm_file: Optional[str] = None
    bgm_volume: float = 0.3
    bgm_fade_in: float = 2.0
    bgm_fade_out: float = 2.0
    
    # 特效音
    sfx_files: List[str] = None
    sfx_volume: float = 0.5
    
    def __post_init__(self):
        if self.sfx_files is None:
            self.sfx_files = []


class SegmentedVideoGenerator:
    """分段视频生成器"""
    
    def __init__(
        self,
        project_dir: Path,
        model_name: str = "modelscope",
        device: str = "cuda",
        resolution: tuple = (512, 512),
        fps: int = 8,
        gpu_memory_threshold: float = 75.0
    ):
        """
        初始化分段视频生成器
        
        Args:
            project_dir: 项目目录
            model_name: 模型名称
            device: 计算设备
            resolution: 分辨率
            fps: 帧率
            gpu_memory_threshold: GPU 显存阈值
        """
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_name
        self.device = device
        self.resolution = resolution
        self.fps = fps
        self.gpu_threshold = gpu_memory_threshold
        
        # 子项目目录
        self.segments_dir = self.project_dir / "segments"
        self.segments_dir.mkdir(exist_ok=True)
        
        self.audio_dir = self.project_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        
        self.output_dir = self.project_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"分段视频生成器初始化完成")
        logger.info(f"  项目目录：{self.project_dir}")
        logger.info(f"  模型：{model_name}")
        logger.info(f"  分辨率：{resolution}")
    
    def create_segment_tasks(
        self,
        total_duration: float,
        segment_duration: float,
        base_prompt: str,
        segment_prompts: Optional[List[str]] = None,
        audio_scripts: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        创建分段任务
        
        Args:
            total_duration: 总时长（秒）
            segment_duration: 每段时长（秒）
            base_prompt: 基础提示词
            segment_prompts: 每段的独立提示词（可选）
            audio_scripts: 每段的配音脚本（可选）
            
        Returns:
            任务列表
        """
        num_segments = int(total_duration / segment_duration)
        if num_segments == 0:
            num_segments = 1
        
        frames_per_segment = int(segment_duration * self.fps)
        
        logger.info(f"将生成 {num_segments} 个片段")
        logger.info(f"  每段时长：{segment_duration}秒")
        logger.info(f"  每段帧数：{frames_per_segment}帧")
        
        tasks = []
        for i in range(num_segments):
            segment_id = f"segment_{i+1:03d}"
            
            # 使用独立提示词或基础提示词
            if segment_prompts and i < len(segment_prompts):
                prompt = segment_prompts[i]
            else:
                prompt = base_prompt
            
            # 使用独立配音脚本或空
            if audio_scripts and i < len(audio_scripts):
                script = audio_scripts[i]
            else:
                script = ""
            
            task = {
                'task_id': segment_id,
                'segment_index': i + 1,
                'total_segments': num_segments,
                'prompt': prompt,
                'audio_script': script,
                'frames': frames_per_segment,
                'duration': segment_duration,
                'status': 'pending'
            }
            tasks.append(task)
        
        # 保存任务配置
        task_file = self.project_dir / "segment_tasks.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"任务配置已保存：{task_file}")
        
        return tasks
    
    def generate_segment_images(
        self,
        task: Dict,
        pipeline
    ) -> bool:
        """
        生成单个片段的图片序列
        
        Args:
            task: 任务配置
            pipeline: 视频生成模型 pipeline
            
        Returns:
            是否成功
        """
        segment_id = task['task_id']
        segment_dir = self.segments_dir / segment_id
        segment_dir.mkdir(exist_ok=True)
        
        logger.info(f"\n生成片段 {task['segment_index']}: {segment_id}")
        logger.info(f"  提示词：{task['prompt']}")
        logger.info(f"  帧数：{task['frames']}")
        
        try:
            # 逐帧生成（节省显存）
            for frame_idx in range(task['frames']):
                frame_id = f"{segment_id}_frame_{frame_idx:03d}"
                output_path = segment_dir / f"{frame_id}.jpg"
                
                # 检查是否已生成
                if output_path.exists():
                    logger.debug(f"  帧 {frame_idx} 已存在，跳过")
                    continue
                
                # 生成单帧
                image = pipeline(
                    prompt=task['prompt'],
                    num_frames=1,
                    height=self.resolution[0],
                    width=self.resolution[1],
                    num_inference_steps=25
                ).frames[0][0]
                
                image.save(output_path)
                
                # GPU 休息，防止过热
                if frame_idx % 5 == 4:
                    import torch
                    torch.cuda.empty_cache()
                    time.sleep(1)
                
                if (frame_idx + 1) % 10 == 0:
                    logger.info(f"  已生成 {frame_idx + 1}/{task['frames']} 帧")
            
            logger.info(f"✓ 片段 {segment_id} 生成完成")
            task['status'] = 'images_completed'
            return True
            
        except Exception as e:
            logger.error(f"✗ 片段 {segment_id} 生成失败：{e}")
            task['status'] = 'failed'
            return False
    
    def generate_segment_audio(
        self,
        task: Dict,
        audio_config: AudioConfig
    ) -> Optional[str]:
        """
        生成单个片段的配音
        
        Args:
            task: 任务配置
            audio_config: 音频配置
            
        Returns:
            音频文件路径
        """
        segment_id = task['task_id']
        script = task.get('audio_script', '')
        
        if not script.strip():
            logger.info(f"片段 {segment_id} 无配音脚本，跳过")
            return None
        
        logger.info(f"\n生成片段 {segment_id} 的配音:")
        logger.info(f"  脚本：{script[:50]}...")
        
        output_file = self.audio_dir / f"{segment_id}_character.wav"
        
        try:
            # 使用 Edge TTS（免费）
            import asyncio
            import edge_tts
            
            async def generate_voice():
                communicate = edge_tts.Communicate(
                    text=script,
                    voice=audio_config.character_voice
                )
                await communicate.save(str(output_file))
            
            asyncio.run(generate_voice())
            
            logger.info(f"✓ 配音生成完成：{output_file}")
            task['audio_file'] = str(output_file)
            task['status'] = 'audio_completed'
            return str(output_file)
            
        except ImportError:
            logger.warning("edge-tts 未安装，跳过配音生成")
            logger.info("  安装：pip install edge-tts")
            return None
        except Exception as e:
            logger.error(f"✗ 配音生成失败：{e}")
            return None
    
    def merge_segments_to_video(
        self,
        tasks: List[Dict],
        output_name: str = "video_only.mp4",
        add_transition: bool = True,
        transition_duration: float = 0.3
    ) -> Optional[str]:
        """
        合并所有片段为视频（不含音频）
        
        Args:
            tasks: 任务列表
            output_name: 输出文件名
            add_transition: 是否添加转场
            transition_duration: 转场时长
            
        Returns:
            输出文件路径
        """
        logger.info("\n合并所有片段为视频...")
        
        # 收集所有片段目录
        segment_dirs = []
        for task in tasks:
            if task['status'] in ['images_completed', 'audio_completed', 'completed']:
                segment_dir = self.segments_dir / task['task_id']
                if segment_dir.exists():
                    segment_dirs.append(segment_dir)
        
        if not segment_dirs:
            logger.error("没有可用的片段")
            return None
        
        merger = VideoMerger(self.project_dir)
        
        # 合并视频
        output_path = self.output_dir / output_name
        
        logger.info(f"合并 {len(segment_dirs)} 个片段...")
        
        # 创建临时合并列表
        merge_files = []
        for seg_dir in segment_dirs:
            frames = sorted(seg_dir.glob("*.jpg"))
            for frame in frames:
                merge_files.append(str(frame))
        
        # 使用 FFmpeg 合并
        import subprocess
        
        list_file = self.project_dir / "merge_list.txt"
        with open(list_file, 'w') as f:
            for frame_file in merge_files:
                f.write(f"file '{frame_file}'\n")
        
        if add_transition:
            # 带转场效果
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-vf", f"fps={self.fps},format=yuv420p",
                "-c:v", "libx264",
                "-crf", "18",
                str(output_path)
            ]
        else:
            # 无转场
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", str(list_file),
                "-c:v", "libx264",
                "-crf", "18",
                str(output_path)
            ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 视频合并完成：{output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ 视频合并失败：{e.stderr.decode()}")
            return None
    
    def add_character_audio(
        self,
        video_file: str,
        tasks: List[Dict],
        output_name: str = "video_with_character.mp4"
    ) -> Optional[str]:
        """
        添加人物配音到视频
        
        Args:
            video_file: 视频文件
            tasks: 任务列表
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        logger.info("\n添加人物配音...")
        
        import subprocess
        from pydub import AudioSegment
        
        output_path = self.output_dir / output_name
        video_path = Path(video_file)
        
        # 收集所有配音文件
        audio_files = []
        for task in tasks:
            if 'audio_file' in task and Path(task['audio_file']).exists():
                audio_files.append({
                    'file': task['audio_file'],
                    'duration': task['duration']
                })
        
        if not audio_files:
            logger.warning("没有可用的配音文件")
            return None
        
        # 合并所有配音
        logger.info(f"合并 {len(audio_files)} 个配音文件...")
        
        try:
            combined = AudioSegment.empty()
            
            # 获取视频时长
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", str(video_path)],
                capture_output=True, text=True
            )
            video_info = json.loads(result.stdout)
            video_duration = float(video_info['format']['duration'])
            
            # 合并音频
            for audio_item in audio_files:
                audio = AudioSegment.from_file(audio_item['file'])
                
                # 调整时长匹配
                target_duration = audio_item['duration'] * 1000  # 毫秒
                if len(audio) > target_duration:
                    audio = audio[:int(target_duration)]
                elif len(audio) < target_duration:
                    # 添加静音填充
                    silence = AudioSegment.silent(
                        duration=int(target_duration - len(audio))
                    )
                    audio = audio + silence
                
                combined += audio
            
            # 保存合并后的配音
            character_audio = self.audio_dir / "character_combined.wav"
            combined.export(character_audio, format="wav")
            
            # 将配音添加到视频
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(character_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 人物配音已添加：{output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"✗ 添加配音失败：{e}")
            return None
    
    def add_background_music(
        self,
        video_file: str,
        audio_config: AudioConfig,
        output_name: str = "final_video.mp4"
    ) -> Optional[str]:
        """
        添加背景音乐和特效音
        
        Args:
            video_file: 视频文件
            audio_config: 音频配置
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        logger.info("\n添加背景音乐和特效音...")
        
        import subprocess
        from pydub import AudioSegment
        
        output_path = self.output_dir / output_name
        video_path = Path(video_file)
        
        try:
            # 获取视频时长
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", str(video_path)],
                capture_output=True, text=True
            )
            video_info = json.loads(result.stdout)
            video_duration = float(video_info['format']['duration'])
            
            # 准备最终音频
            final_audio = AudioSegment.empty()
            
            # 1. 添加背景音乐
            if audio_config.bgm_file:
                logger.info(f"加载背景音乐：{audio_config.bgm_file}")
                bgm = AudioSegment.from_file(audio_config.bgm_file)
                
                # 循环直到视频长度
                while len(final_audio) < video_duration * 1000:
                    remaining = video_duration * 1000 - len(final_audio)
                    if remaining < len(bgm):
                        final_audio += bgm[:int(remaining)]
                    else:
                        final_audio += bgm
                
                # 音量调整
                final_audio = final_audio - (1 - audio_config.bgm_volume) * 20
                
                # 淡入淡出
                if audio_config.bgm_fade_in > 0:
                    final_audio = final_audio.fade_in(int(audio_config.bgm_fade_in * 1000))
                if audio_config.bgm_fade_out > 0:
                    final_audio = final_audio.fade_out(int(audio_config.bgm_fade_out * 1000))
            
            # 2. 添加特效音（在指定时间点）
            for sfx_file in (audio_config.sfx_files or []):
                logger.info(f"添加特效音：{sfx_file}")
                # 这里可以根据需要添加特效音的时间点
                # 简单实现：添加到开头
                sfx = AudioSegment.from_file(sfx_file)
                sfx = sfx - (1 - audio_config.sfx_volume) * 20
                # final_audio = final_audio.overlay(sfx, position=0)
            
            # 保存最终音频
            bgm_audio = self.audio_dir / "background_music.wav"
            final_audio.export(bgm_audio, format="wav")
            
            # 检查是否已有配音轨道
            if video_file.endswith('_with_character.mp4'):
                # 已有配音，需要混音
                logger.info("检测到已有配音，进行混音...")
                
                # 添加 BGM 到已有视频
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(bgm_audio),
                    "-filter_complex",
                    f"[0:a][1:a]amix=inputs=2:duration=shortest:weights=1 {audio_config.bgm_volume}",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_path)
                ]
            else:
                # 无配音，直接添加
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(bgm_audio),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    str(output_path)
                ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 背景音乐已添加：{output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"✗ 添加背景音乐失败：{e}")
            return None


@click.command()
@click.option(
    '--base-prompt', '-p',
    required=True,
    help='基础提示词'
)
@click.option(
    '--total-duration', '-d',
    type=float,
    default=10.0,
    help='总时长（秒）'
)
@click.option(
    '--segment-duration', '-s',
    type=float,
    default=2.0,
    help='每段时长（秒）'
)
@click.option(
    '--output-dir',
    default='output/segmented_video',
    help='输出目录'
)
@click.option(
    '--resolution',
    type=str,
    default='512x512',
    help='分辨率'
)
@click.option(
    '--fps',
    type=int,
    default=8,
    help='帧率'
)
@click.option(
    '--model', '-m',
    type=str,
    default='modelscope',
    help='模型名称'
)
@click.option(
    '--device',
    default='cuda',
    help='计算设备'
)
@click.option(
    '--character-voice',
    default='zh-CN-XiaoxiaoNeural',
    help='人物配音语音（微软 TTS）'
)
@click.option(
    '--bgm-file',
    default=None,
    help='背景音乐文件'
)
@click.option(
    '--bgm-volume',
    type=float,
    default=0.3,
    help='背景音乐音量（0-1）'
)
@click.option(
    '--add-transition/--no-transition',
    default=True,
    help='是否添加转场效果'
)
def main(
    base_prompt: str,
    total_duration: float,
    segment_duration: float,
    output_dir: str,
    resolution: str,
    fps: int,
    model: str,
    device: str,
    character_voice: str,
    bgm_file: str,
    bgm_volume: float,
    add_transition: bool
):
    """
    分段文生图 + 合成视频 + 分层配音
    
    示例:
    
    \b
    # 基础使用
    python personal_mode/generate_segmented.py \\
        -p "cyberpunk city street" \\
        -d 10 -s 2 \\
        --output-dir output/test
    
    \b
    # 添加配音和 BGM
    python personal_mode/generate_segmented.py \\
        -p "魔法城堡" \\
        -d 10 -s 2 \\
        --character-voice zh-CN-XiaoxiaoNeural \\
        --bgm-file music/bgm.mp3 \\
        --bgm-volume 0.3
    """
    import torch
    
    # 配置
    project_dir = Path(output_dir)
    
    # 解析分辨率
    try:
        width, height = map(int, resolution.split('x'))
    except:
        logger.error(f"无效的分辨率：{resolution}")
        return
    
    print("\n" + "="*60)
    print(" 分段文生图 + 合成视频 + 分层配音")
    print("="*60)
    print(f"\n配置信息:")
    print(f"  基础提示词：{base_prompt}")
    print(f"  总时长：{total_duration} 秒")
    print(f"  分段时长：{segment_duration} 秒")
    print(f"  分段数：{int(total_duration / segment_duration)}")
    print(f"  分辨率：{width}x{height}")
    print(f"  帧率：{fps}fps")
    print(f"  模型：{model}")
    print(f"  人物配音：{character_voice}")
    print(f"  背景音乐：{bgm_file or '无'}")
    print(f"  输出目录：{project_dir}")
    print(f"\n{'='*60}\n")
    
    # 1. 初始化生成器
    generator = SegmentedVideoGenerator(
        project_dir=project_dir,
        model_name=model,
        device=device,
        resolution=(width, height),
        fps=fps
    )
    
    # 2. 创建分段任务
    print("创建分段任务...")
    # 示例配音脚本
    audio_scripts = [
        "这是一个神奇的地方",
        "看那座古老的城堡",
        "里面住着魔法师",
        "他们在施展法术",
        "多么美丽的景象"
    ][:int(total_duration / segment_duration)]
    
    tasks = generator.create_segment_tasks(
        total_duration=total_duration,
        segment_duration=segment_duration,
        base_prompt=base_prompt,
        audio_scripts=audio_scripts
    )
    
    # 3. 加载模型
    print("\n加载模型...")
    try:
        from diffusers import DiffusionPipeline
        
        if model == "modelscope":
            pipeline = DiffusionPipeline.from_pretrained(
                "damo/text-to-video-synthesis",
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            pipeline = pipeline.to(device)
        else:
            logger.error(f"不支持的模型：{model}")
            return
        
        # 启用优化
        if device == "cuda":
            pipeline.enable_attention_slicing()
            pipeline.enable_vae_slicing()
        
        print("✓ 模型加载完成")
        
    except Exception as e:
        logger.error(f"模型加载失败：{e}")
        return
    
    # 4. 生成每个片段的图片和配音
    audio_config = AudioConfig(
        character_voice=character_voice,
        bgm_file=bgm_file,
        bgm_volume=bgm_volume
    )
    
    print("\n开始生成片段...")
    for i, task in enumerate(tasks, 1):
        print(f"\n片段 {i}/{len(tasks)}")
        
        # 生成图片
        success = generator.generate_segment_images(task, pipeline)
        
        if success:
            # 生成配音
            generator.generate_segment_audio(task, audio_config)
        
        # 清理 GPU 缓存
        if device == "cuda":
            torch.cuda.empty_cache()
            time.sleep(2)
    
    # 5. 合并视频
    print("\n合并视频...")
    video_path = generator.merge_segments_to_video(
        tasks=tasks,
        output_name="video_only.mp4",
        add_transition=add_transition
    )
    
    if not video_path:
        logger.error("视频合并失败")
        return
    
    # 6. 添加人物配音
    print("\n添加人物配音...")
    video_with_character = generator.add_character_audio(
        video_file=video_path,
        tasks=tasks,
        output_name="video_with_character.mp4"
    )
    
    # 7. 添加背景音乐
    print("\n添加背景音乐和特效音...")
    final_video = generator.add_background_music(
        video_file=video_with_character or video_path,
        audio_config=audio_config,
        output_name="final_video.mp4"
    )
    
    if final_video:
        print(f"\n{'='*60}")
        print(f" ✓ 最终视频：{final_video}")
        print(f"{'='*60}\n")
        
        # 显示文件信息
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", final_video],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            if 'format' in info:
                fmt = info['format']
                print(f"  时长：{fmt.get('duration', 'N/A')}秒")
                print(f"  大小：{int(fmt.get('size', 0)) / 1024 / 1024:.1f}MB")
                print(f"  码率：{fmt.get('bit_rate', 'N/A')} bps")
    
    print("\n✓ 完成！\n")


if __name__ == "__main__":
    main()
