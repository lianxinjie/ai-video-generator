#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器 - 管理和调度所有视频生成任务
"""

import time
import logging
from pathlib import Path
from typing import Optional, Callable, Dict

from .monitor import ResourceMonitor
from .checkpoint import CheckpointManager
from .chunk_generator import ChunkGenerator
from .merger import VideoMerger
from .ai_offload import AIOffloadEngine

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(
        self,
        project_dir: Path,
        pipeline,
        device: str = "cuda",
        gpu_memory_threshold: float = 75.0,
        chunk_duration: float = 0.5,
        resolution: tuple = (512, 512),
        fps: int = 8,
        ai_offload_config: Optional[Dict] = None
    ):
        """
        初始化任务调度器
        
        Args:
            project_dir: 项目目录
            pipeline: 视频生成模型 pipeline
            device: 计算设备
            gpu_memory_threshold: GPU 显存阈值 (%)
            chunk_duration: 每段时长 (秒)
            resolution: 分辨率
            fps: 帧率
            ai_offload_config: AI 卸载配置
        """
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化资源监控
        self.monitor = ResourceMonitor(
            gpu_memory_threshold=gpu_memory_threshold
        )
        
        # 初始化检查点管理
        self.checkpoint_mgr = CheckpointManager(self.project_dir)
        
        # 初始化片段生成器
        self.generator = ChunkGenerator(
            pipeline=pipeline,
            monitor=self.monitor,
            checkpoint_mgr=self.checkpoint_mgr,
            device=device,
            resolution=resolution,
            fps=fps,
            chunk_duration=chunk_duration
        )
        
        # 初始化合并器
        self.merger = VideoMerger(self.project_dir)
        
        # 初始化 AI 卸载
        if ai_offload_config:
            self.ai_engine = AIOffloadEngine(**ai_offload_config)
        else:
            self.ai_engine = AIOffloadEngine(enabled=False)
        
        # 元数据
        self.metadata = {
            'created_at': time.time(),
            'total_chunks': 0,
            'chunk_duration': chunk_duration,
            'resolution': resolution,
            'fps': fps
        }
        
        logger.info(f"任务调度器初始化完成")
        logger.info(f"  - 项目目录：{self.project_dir}")
        logger.info(f"  - 分段时长：{chunk_duration}秒")
        logger.info(f"  - 分辨率：{resolution}")
    
    def create_tasks(
        self,
        total_duration: float,
        base_prompt: str,
        chunk_duration: Optional[float] = None,
        use_ai_enhance: bool = False
    ) -> int:
        """
        创建分段任务
        
        Args:
            total_duration: 总时长 (秒)
            base_prompt: 基础提示词
            chunk_duration: 每段时长 (秒)
            use_ai_enhance: 是否使用 AI 优化提示词
            
        Returns:
            创建的任务数量
        """
        if chunk_duration is None:
            chunk_duration = self.generator.chunk_duration
        
        # 计算总段数
        total_chunks = int(total_duration / chunk_duration)
        if total_chunks == 0:
            total_chunks = 1
        
        logger.info(f"将生成 {total_chunks} 个片段 (总时长 {total_duration}秒)")
        
        # 创建任务
        tasks = []
        for i in range(total_chunks):
            task_id = f"chunk_{i+1:03d}"
            
            # AI 优化提示词
            prompt = base_prompt
            if use_ai_enhance and self.ai_engine.is_enabled():
                prompt = self.ai_engine.enhance_prompt(base_prompt, i + 1)
                logger.info(f"片段 {i+1} 提示词已优化")
            
            seed = 1000 + i
            tasks.append({
                'task_id': task_id,
                'chunk_index': i + 1,
                'total_chunks': total_chunks,
                'prompt': prompt,
                'seed': seed
            })
        
        # 保存到检查点
        for task_data in tasks:
            self.checkpoint_mgr.create_tasks(
                total_chunks=1,
                base_prompt=task_data['prompt']
            )
        
        self.metadata['total_chunks'] = total_chunks
        self.metadata['base_prompt'] = base_prompt
        self.checkpoint_mgr.save_metadata(self.metadata)
        
        return len(tasks)
    
    def run_all_tasks(self) -> bool:
        """
        执行所有任务
        
        Returns:
            是否全部成功
        """
        pending_tasks = self.checkpoint_mgr.get_pending_tasks()
        
        if not pending_tasks:
            logger.warning("没有待执行的任务")
            return False
        
        total = len(self.checkpoint_mgr.get_all_tasks())
        completed = len(self.checkpoint_mgr.get_completed_tasks())
        
        logger.info(f"开始执行 {len(pending_tasks)} 个待处理任务")
        logger.info(f"总任务数：{total}, 已完成：{completed}")
        
        success_count = 0
        fail_count = 0
        
        for task_data in pending_tasks:
            # 打印进度
            progress = self.checkpoint_mgr.get_progress()
            print(f"\n{'='*60}")
            print(f" 进度：{progress['percentage']:.1f}% "
                  f"({progress['completed']}/{progress['total']})")
            print(f"{'='*60}\n")
            
            # 生成任务
            success = self.generator.generate_chunk(
                task_id=task_data['task_id'],
                chunk_index=task_data['chunk_index'],
                total_chunks=task_data['total_chunks'],
                prompt=task_data['prompt'],
                seed=task_data.get('seed')
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                logger.warning(f"任务 {task_data['task_id']} 失败")
            
            # 任务间延迟，让硬件休息
            time.sleep(2)
            self.monitor.clear_gpu_cache()
        
        # 生成报告
        self._generate_report(success_count, fail_count)
        
        all_success = fail_count == 0
        
        if all_success:
            logger.info("✓ 所有任务执行完成")
        else:
            logger.warning(f"✗ {fail_count} 个任务失败")
        
        return all_success
    
    def merge_results(
        self,
        output_name: str = "final_video.mp4",
        add_transition: bool = False,
        cleanup: bool = False
    ) -> Optional[str]:
        """
        合并所有结果
        
        Args:
            output_name: 输出文件名
            add_transition: 是否添加过渡效果
            cleanup: 是否清理片段文件
            
        Returns:
            输出文件路径
        """
        logger.info("开始合并视频片段...")
        
        output_path = self.merger.merge_videos(
            chunk_pattern="chunk_*.mp4",
            output_name=output_name,
            add_transition=add_transition,
            cleanup_chunks=cleanup
        )
        
        if output_path:
            logger.info(f"✓ 合并完成：{output_path}")
            return str(output_path)
        else:
            logger.error("合并失败")
            return None
    
    def _generate_report(self, success_count: int, fail_count: int):
        """生成统计报告"""
        stats = self.monitor.get_statistics()
        progress = self.checkpoint_mgr.get_progress()
        
        report = f"""
{'='*60}
 视频生成任务报告
{'='*60}

项目目录：{self.project_dir}
生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}

任务统计:
  - 总片段数：{progress['total']}
  - 成功：{success_count}
  - 失败：{fail_count}
  - 完成率：{progress['percentage']:.1f}%

资源统计:
  - 平均 GPU 显存占用：{stats.get('gpu_memory_avg', 'N/A')}%
  - 平均 CPU 使用率：{stats.get('cpu_avg', 'N/A')}%
  - 平均内存占用：{stats.get('memory_avg', 'N/A')}%
  - 暂停次数：{stats.get('pause_count', 0)}
  - 累计暂停时间：{stats.get('total_pause_time', 0)}秒

元数据:
  - 分段时长：{self.metadata.get('chunk_duration', 'N/A')}秒
  - 分辨率：{self.metadata.get('resolution', 'N/A')}
  - 帧率：{self.metadata.get('fps', 'N/A')}fps
{'='*60}
"""
        
        report_path = self.project_dir / "generation_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"报告已保存：{report_path}")
        
        # 打印到终端
        print(report)
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'project_dir': str(self.project_dir),
            'progress': self.checkpoint_mgr.get_progress(),
            'resources': self.monitor.check_status().__dict__,
            'metadata': self.metadata
        }
