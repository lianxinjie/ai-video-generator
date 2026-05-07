#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频片段生成器 - 支持低显存的的分段视频生成
"""

import time
import logging
import torch
from pathlib import Path
from typing import Optional

from .monitor import ResourceMonitor
from .checkpoint import CheckpointManager, CheckpointData

logger = logging.getLogger(__name__)


class ChunkGenerator:
    """视频片段生成器"""
    
    def __init__(
        self,
        pipeline,
        monitor: ResourceMonitor,
        checkpoint_mgr: CheckpointManager,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        resolution: tuple = (512, 512),
        fps: int = 8,
        chunk_duration: float = 0.5,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5
    ):
        """
        初始化片段生成器
        
        Args:
            pipeline: 视频生成模型 pipeline
            monitor: 资源监控器
            checkpoint_mgr: 检查点管理器
            device: 计算设备
            dtype: 计算精度
            resolution: 分辨率 (宽，高)
            fps: 帧率
            chunk_duration: 每段时长 (秒)
            num_inference_steps: 推理步数
            guidance_scale: 引导系数
        """
        self.pipeline = pipeline
        self.monitor = monitor
        self.checkpoint_mgr = checkpoint_mgr
        self.device = device
        self.dtype = dtype
        self.resolution = resolution
        self.fps = fps
        self.chunk_duration = chunk_duration
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale
        
        # 计算每段帧数
        self.num_frames = int(chunk_duration * fps)
        
        logger.info(f"片段生成器初始化完成")
        logger.info(f"  - 设备：{device}")
        logger.info(f"  - 精度：{dtype}")
        logger.info(f"  - 分辨率：{resolution}")
        logger.info(f"  - 每段帧数：{num_frames}")
    
    def generate_chunk(
        self,
        task_id: str,
        chunk_index: int,
        total_chunks: int,
        prompt: str,
        seed: Optional[int] = None,
        max_retries: int = 3
    ) -> bool:
        """
        生成单个视频片段
        
        Args:
            task_id: 任务 ID
            chunk_index: 片段索引 (从 1 开始)
            total_chunks: 总片段数
            prompt: 提示词
            seed: 随机种子
            max_retries: 最大重试次数
            
        Returns:
            是否成功
        """
        # 检查是否已完成
        checkpoint = self.checkpoint_mgr.load_checkpoint(task_id)
        
        if checkpoint and checkpoint.status == 'completed':
            logger.info(f"任务 {task_id} 已完成，跳过")
            return True
        
        # 创建或恢复检查点
        if checkpoint is None:
            checkpoint = CheckpointData(
                task_id=task_id,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                status='pending',
                progress=0,
                created_at=time.time(),
                updated_at=time.time(),
                error_message=None,
                retry_count=0,
                prompt=prompt,
                seed=seed,
                output_path=None
            )
            self.checkpoint_mgr.save_checkpoint(checkpoint)
        
        # 重试循环
        while checkpoint.retry_count < max_retries:
            # 检查资源
            if self.monitor.should_pause():
                logger.info("⚠ 资源占用过高，暂停任务...")
                checkpoint.status = 'paused'
                self.checkpoint_mgr.save_checkpoint(checkpoint)
                
                # 等待资源恢复
                if not self.monitor.wait_for_resources():
                    logger.error("等待资源超时，任务失败")
                    checkpoint.status = 'failed'
                    checkpoint.error_message = "等待资源超时"
                    self.checkpoint_mgr.save_checkpoint(checkpoint)
                    return False
                
                checkpoint.status = 'running'
                checkpoint.progress = 10
                self.checkpoint_mgr.save_checkpoint(checkpoint)
            
            try:
                checkpoint.status = 'running'
                checkpoint.progress = 20
                self.checkpoint_mgr.save_checkpoint(checkpoint)
                
                # 清理 GPU 缓存
                self.monitor.clear_gpu_cache()
                
                # 生成视频
                logger.info(f"生成片段 {chunk_index}/{total_chunks}: {prompt[:50]}...")
                
                output_path = self._run_inference(
                    prompt=prompt,
                    seed=seed,
                    chunk_index=chunk_index
                )
                
                checkpoint.progress = 100
                checkpoint.status = 'completed'
                checkpoint.output_path = str(output_path)
                self.checkpoint_mgr.save_checkpoint(checkpoint)
                
                logger.info(f"✓ 片段 {chunk_index} 生成完成：{output_path}")
                return True
            
            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"✗ 显存不足：{e}")
                checkpoint.retry_count += 1
                checkpoint.error_message = f"显存不足：{str(e)}"
                checkpoint.status = 'failed'
                self.checkpoint_mgr.save_checkpoint(checkpoint)
                
                torch.cuda.empty_cache()
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"✗ 生成失败：{e}")
                checkpoint.retry_count += 1
                checkpoint.error_message = str(e)
                checkpoint.status = 'failed'
                self.checkpoint_mgr.save_checkpoint(checkpoint)
                
                time.sleep(5)
        
        logger.error(f"任务 {task_id} 达到最大重试次数，失败")
        return False
    
    def _run_inference(
        self,
        prompt: str,
        seed: Optional[int],
        chunk_index: int
    ) -> Path:
        """运行模型推理"""
        # 设置随机种子
        if seed is not None:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        
        # 设置负向提示词
        negative_prompt = "bad quality, worst quality, blurry, distorted, deformed, ugly"
        
        # 根据模型类型调用不同的生成方法
        if hasattr(self.pipeline, 'model_name'):
            model_name = self.pipeline.model_name
        else:
            model_name = "unknown"
        
        # 使用半精度推理
        with torch.inference_mode():
            if model_name == "modelscope":
                output = self._generate_modelscope(prompt, negative_prompt)
            elif model_name == "animatediff":
                output = self._generate_animatediff(prompt, negative_prompt)
            else:
                # 通用方法
                output = self._generate_generic(prompt, negative_prompt)
        
        # 保存视频
        output_path = self.checkpoint_mgr.project_dir / f"chunk_{chunk_index:03d}.mp4"
        self._save_video(output, output_path)
        
        return output_path
    
    def _generate_modelscope(self, prompt: str, negative_prompt: str):
        """ModelScope 模型生成"""
        output = self.pipeline(
            text=prompt,
            num_frames=self.num_frames,
            height=self.resolution[1],
            width=self.resolution[0],
        )
        return output["video"]
    
    def _generate_animatediff(self, prompt: str, negative_prompt: str):
        """AnimateDiff 模型生成"""
        output = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=self.num_frames,
            height=self.resolution[1],
            width=self.resolution[0],
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
        )
        return output.frames[0]
    
    def _generate_generic(self, prompt: str, negative_prompt: str):
        """通用生成方法"""
        output = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=self.num_frames,
            height=self.resolution[1],
            width=self.resolution[0],
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
        )
        if hasattr(output, 'frames'):
            return output.frames[0]
        return output
    
    def _save_video(self, frames, output_path: Path):
        """保存视频"""
        try:
            import imageio
            imageio.mimwrite(
                str(output_path),
                frames,
                fps=self.fps,
                codec='libx264',
                quality=8
            )
        except Exception as e:
            logger.error(f"保存视频失败：{e}")
            # 备用方法：保存为 GIF
            output_path = output_path.with_suffix('.gif')
            import imageio
            imageio.mimwrite(str(output_path), frames, fps=self.fps, loop=0)
