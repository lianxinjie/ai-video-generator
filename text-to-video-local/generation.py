#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-to-Video Local Deployment
支持多种开源文生视频模型的本地部署程序
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List
import click

import torch
from PIL import Image


class VideoGenerator:
    """文生视频生成器，支持多种模型"""

    def __init__(
        self,
        model_name: str = "modelscope",
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float16,
    ):
        """
        初始化视频生成器

        Args:
            model_name: 模型名称 ['modelscope', 'animatediff', 'cogvideox']
            device: 计算设备，默认自动检测
            dtype: 计算精度，默认 float16
        """
        self.model_name = model_name.lower()
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.dtype = dtype
        self.pipeline = None
        self.model_path = Path("./models")
        self.model_path.mkdir(exist_ok=True)
        
        print(f"初始化视频生成器:")
        print(f"  - 模型：{model_name}")
        print(f"  - 设备：{self.device}")
        print(f"  - 精度：{dtype}")
    
    def load_model(self):
        """加载指定的文生视频模型"""
        print(f"\n正在加载 {self.model_name} 模型...")
        
        if self.model_name == "modelscope":
            self._load_modelscope()
        elif self.model_name == "animatediff":
            self._load_animatediff()
        elif self.model_name == "cogvideox":
            self._load_cogvideox()
        elif self.model_name == "stable_video_diffusion":
            self._load_stable_video_diffusion()
        else:
            raise ValueError(
                f"不支持的模型：{self.model_name}\n"
                f"支持的模型：['modelscope', 'animatediff', 'cogvideox', 'stable_video_diffusion']"
            )
        
        print(f"模型加载完成 ✓")
    
    def _load_modelscope(self):
        """加载 ModelScope 文本到视频合成模型"""
        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks
            
            self.pipeline = pipeline(
                Tasks.text_to_video_synthesis,
                model='damo/cv_synthesis_video-generation-damo',
                device=self.device if self.device != "cpu" else "cpu"
            )
            print("  - ModelScope 模型加载成功")
            print("  - 支持中文文本输入")
            print("  - 推荐分辨率：256x256, 512x512")
            
        except ImportError as e:
            print(f"\n错误：需要安装 modelscope")
            print("运行：pip install modelscope")
            raise e
    
    def _load_animatediff(self):
        """加载 AnimateDiff 模型"""
        try:
            from diffusers import (
                DiffusionPipeline,
                DPMSolverMultistepScheduler,
                MotionAdapter,
            )
            
            adapter = MotionAdapter.from_pretrained(
                "guoyww/animatediff-motion-adapter-v1-5-2",
                torch_dtype=self.dtype
            )
            
            self.pipeline = DiffusionPipeline.from_pretrained(
                "frankjoshua/toonyou_beta6",
                motion_adapter=adapter,
                torch_dtype=self.dtype
            )
            
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipeline.scheduler.config,
                algorithm_type="dpmsolver++",
                final_sigmas_type="zero"
            )
            
            if self.device == "cuda":
                self.pipeline.enable_model_cpu_offload()
                self.pipeline.enable_vae_slicing()
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                except:
                    pass
            
            print("  - AnimateDiff 模型加载成功")
            print("  - 基于 Stable Diffusion 架构")
            print("  - 支持 ControlNet 扩展")
            
        except ImportError as e:
            print(f"\n错误：需要安装 diffusers 和相关依赖")
            print("运行：pip install diffusers transformers accelerate")
            raise e
    
    def _load_cogvideox(self):
        """加载 CogVideoX-5B 模型"""
        try:
            import torch
            from diffusers import CogVideoXPipeline
            
            self.pipeline = CogVideoXPipeline.from_pretrained(
                "THUDM/CogVideoX-5b",
                torch_dtype=self.dtype
            )
            
            if self.device == "cuda":
                self.pipeline.enable_model_cpu_offload()
                self.pipeline.enable_vae_slicing()
            
            print("  - CogVideoX-5B 模型加载成功")
            print("  - 纯 Transformer 架构")
            print("  - 支持高质量视频生成")
            
        except ImportError as e:
            print(f"\n错误：需要安装 diffusers >= 0.30.0")
            print("运行：pip install 'diffusers>=0.30.0' transformers")
            raise e
    
    def _load_stable_video_diffusion(self):
        """加载 Stable Video Diffusion 模型"""
        try:
            from diffusers import StableVideoDiffusionPipeline
            
            self.pipeline = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid-xt",
                torch_dtype=self.dtype,
                variant="fp16"
            )
            
            if self.device == "cuda":
                self.pipeline.enable_model_cpu_offload()
            
            print("  - Stable Video Diffusion 模型加载成功")
            print("  - 图生视频模式")
            print("  - 需要先生成或提供输入图像")
            
        except ImportError as e:
            print(f"\n错误：需要安装 diffusers")
            raise e
    
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = 16,
        fps: int = 8,
        duration: Optional[int] = None,
        height: int = 256,
        width: int = 256,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        output_path: str = "output.mp4",
    ) -> str:
        """
        生成视频

        Args:
            prompt: 文本提示词，描述视频内容
            negative_prompt: 负向提示词，描述不希望出现的内容
            num_frames: 视频帧数，默认 16 帧
            fps: 帧率，默认 8fps
            duration: 视频时长（秒），如果指定，会自动计算帧数
            height: 视频高度，默认 256
            width: 视频宽度，默认 256
            num_inference_steps: 推理步数，默认 50
            guidance_scale: 引导系数，默认 7.5
            seed: 随机种子，用于复现结果
            output_path: 输出文件路径

        Returns:
            输出视频文件路径
        """
        if self.pipeline is None:
            self.load_model()
        
        if duration is not None:
            num_frames = int(duration * fps)
            print(f"根据时长计算的帧数：{num_frames} 帧 ({duration}秒 @ {fps}fps)")
        
        print(f"\n开始生成视频:")
        print(f"  - 提示词：{prompt}")
        print(f"  - 分辨率：{width}x{height}")
        print(f"  - 帧数：{num_frames}")
        print(f"  - 帧率：{fps}fps")
        print(f"  - 推理步数：{num_inference_steps}")
        print(f"  - 引导系数：{guidance_scale}")
        
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None
        
        start_time = time.time()
        
        try:
            if self.model_name == "modelscope":
                output = self.pipeline(
                    text=prompt,
                    num_frames=num_frames,
                    height=height,
                    width=width,
                )
                video_frames = output["video"]
                
            elif self.model_name == "animatediff":
                output = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt or "bad quality, worst quality, blurry, distorted",
                    num_frames=num_frames,
                    height=height,
                    width=width,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
                video_frames = output.frames[0]
                
            elif self.model_name == "cogvideox":
                output = self.pipeline(
                    prompt=prompt,
                    num_frames=num_frames // 2,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
                video_frames = output.frames[0]
                
            elif self.model_name == "stable_video_diffusion":
                raise NotImplementedError(
                    "Stable Video Diffusion 需要输入图像，请使用图生视频模式"
                )
            
            else:
                raise ValueError(f"不支持的模型：{self.model_name}")
            
            elapsed_time = time.time() - start_time
            print(f"\n生成完成！耗时：{elapsed_time:.2f}秒")
            
            # 保存视频
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._save_video(video_frames, output_path, fps)
            
            print(f"视频已保存到：{output_path.absolute()}")
            
            return str(output_path.absolute())
            
        except Exception as e:
            print(f"\n生成过程中发生错误：{e}")
            raise
    
    def _save_video(self, frames, output_path: Path, fps: int = 8):
        """保存视频帧为视频文件"""
        import imageio
        
        output_path = Path(output_path)
        suffix = output_path.suffix.lower()
        
        if suffix == '.mp4':
            imageio.mimwrite(
                output_path,
                frames,
                fps=fps,
                codec='libx264',
                quality=8
            )
        elif suffix in ['.gif', '.webp']:
            imageio.mimwrite(
                output_path,
                frames,
                fps=fps,
                loop=0
            )
        else:
            # 默认保存为 mp4
            output_path = output_path.with_suffix('.mp4')
            imageio.mimwrite(
                output_path,
                frames,
                fps=fps,
                codec='libx264',
                quality=8
            )


@click.group()
def cli():
    """Text-to-Video Local Deployment CLI"""
    pass


@cli.command()
@click.option(
    "--model", "-m",
    type=click.Choice(["modelscope", "animatediff", "cogvideox", "stable_video_diffusion"]),
    default="modelscope",
    help="选择使用的模型"
)
@click.option(
    "--prompt", "-p",
    required=True,
    help="文本提示词，描述要生成的视频内容"
)
@click.option(
    "--negative-prompt", "-n",
    default="",
    help="负向提示词，描述不希望出现的内容"
)
@click.option(
    "--output", "-o",
    default="output.mp4",
    help="输出文件路径"
)
@click.option(
    "--duration", "-d",
    type=int,
    default=None,
    help="视频时长（秒）"
)
@click.option(
    "--fps",
    type=int,
    default=8,
    help="帧率"
)
@click.option(
    "--height", "-H",
    type=int,
    default=256,
    help="视频高度"
)
@click.option(
    "--width", "-W",
    type=int,
    default=256,
    help="视频宽度"
)
@click.option(
    "--steps",
    type=int,
    default=50,
    help="推理步数"
)
@click.option(
    "--guidance-scale",
    type=float,
    default=7.5,
    help="引导系数"
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="随机种子"
)
@click.option(
    "--device",
    default=None,
    help="计算设备 (cuda / cpu)"
)
def generate(
    model: str,
    prompt: str,
    negative_prompt: str,
    output: str,
    duration: Optional[int],
    fps: int,
    height: int,
    width: int,
    steps: int,
    guidance_scale: float,
    seed: Optional[int],
    device: Optional[str]
):
    """生成视频"""
    generator = VideoGenerator(
        model_name=model,
        device=device
    )
    
    generator.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        duration=duration,
        fps=fps,
        height=height,
        width=width,
        num_inference_steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
        output_path=output
    )


@cli.command()
def check():
    """检查系统环境和 GPU 状态"""
    print("=" * 60)
    print("系统环境检查")
    print("=" * 60)
    
    print(f"\nPython 版本：{sys.version}")
    print(f"PyTorch 版本：{torch.__version__}")
    print(f"CUDA 可用：{torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA 版本：{torch.version.cuda}")
        print(f"GPU 数量：{torch.cuda.device_count()}")
        print(f"\nGPU 信息:")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"    - 显存：{props.total_memory / 1024**3:.1f}GB")
            print(f"    - 计算能力：{props.major}.{props.minor}")
    else:
        print("警告：未检测到 CUDA 设备，将使用 CPU 运行（速度较慢）")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    cli()
