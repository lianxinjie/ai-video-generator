#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查点管理模块 - 保存和恢复任务状态，支持断点续传
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CheckpointData:
    """检查点数据"""
    task_id: str
    chunk_index: int
    total_chunks: int
    status: str  # pending, running, paused, completed, failed
    progress: float  # 0-100
    created_at: float
    updated_at: float
    error_message: Optional[str]
    retry_count: int
    prompt: str
    seed: Optional[int]
    output_path: Optional[str]


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, project_dir: Path):
        """
        初始化检查点管理器
        
        Args:
            project_dir: 项目目录
        """
        self.project_dir = Path(project_dir)
        self.checkpoint_dir = self.project_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.task_file = self.project_dir / "tasks.json"
        self.metadata_file = self.project_dir / "metadata.json"
        
        logger.info(f"检查点目录：{self.checkpoint_dir}")
    
    def save_checkpoint(self, checkpoint: CheckpointData):
        """保存检查点"""
        checkpoint.updated_at = time.time()
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint.task_id}.json"
        
        data = asdict(checkpoint)
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # 更新任务列表
        self._update_task_list(checkpoint)
        logger.debug(f"保存检查点：{checkpoint.task_id} (进度：{checkpoint.progress}%)")
    
    def load_checkpoint(self, task_id: str) -> Optional[CheckpointData]:
        """加载检查点"""
        checkpoint_path = self.checkpoint_dir / f"{task_id}.json"
        
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return CheckpointData(**data)
        except Exception as e:
            logger.error(f"加载检查点失败：{e}")
            return None
    
    def delete_checkpoint(self, task_id: str):
        """删除检查点"""
        checkpoint_path = self.checkpoint_dir / f"{task_id}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.debug(f"删除检查点：{task_id}")
    
    def _update_task_list(self, checkpoint: CheckpointData):
        """更新任务列表"""
        tasks = self.get_all_tasks()
        
        # 查找并更新
        found = False
        for i, task in enumerate(tasks):
            if task.get('task_id') == checkpoint.task_id:
                tasks[i] = asdict(checkpoint)
                found = True
                break
        
        if not found:
            tasks.append(asdict(checkpoint))
        
        with open(self.task_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False, default=str)
    
    def get_all_tasks(self) -> list:
        """获取所有任务"""
        if not self.task_file.exists():
            return []
        
        try:
            with open(self.task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取任务列表失败：{e}")
            return []
    
    def get_pending_tasks(self) -> list:
        """获取未完成的任务"""
        tasks = self.get_all_tasks()
        return [t for t in tasks if t.get('status') in ['pending', 'paused', 'failed']]
    
    def get_completed_tasks(self) -> list:
        """获取已完成的任务"""
        tasks = self.get_all_tasks()
        return [t for t in tasks if t.get('status') == 'completed']
    
    def create_tasks(
        self,
        total_chunks: int,
        base_prompt: str,
        chunk_duration: float = 0.5,
        fps: int = 8
    ) -> list:
        """创建一批任务"""
        tasks = []
        
        for i in range(total_chunks):
            task_id = f"chunk_{i+1:03d}"
            checkpoint = CheckpointData(
                task_id=task_id,
                chunk_index=i + 1,
                total_chunks=total_chunks,
                status='pending',
                progress=0,
                created_at=time.time(),
                updated_at=time.time(),
                error_message=None,
                retry_count=0,
                prompt=f"{base_prompt} (part {i+1}/{total_chunks})",
                seed=1000 + i,
                output_path=None
            )
            tasks.append(checkpoint)
            self.save_checkpoint(checkpoint)
        
        logger.info(f"创建 {total_chunks} 个分段任务")
        return tasks
    
    def save_metadata(self, metadata: Dict):
        """保存元数据"""
        metadata['updated_at'] = time.time()
        
        # 合并现有元数据
        existing = self.load_metadata()
        existing.update(metadata)
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False, default=str)
    
    def load_metadata(self) -> Dict:
        """加载元数据"""
        if not self.metadata_file.exists():
            return {}
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_progress(self) -> Dict:
        """获取进度信息"""
        tasks = self.get_all_tasks()
        
        if not tasks:
            return {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'failed': 0,
                'percentage': 0.0
            }
        
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        failed = sum(1 for t in tasks if t.get('status') == 'failed')
        pending = len(tasks) - completed - failed
        
        return {
            'total': len(tasks),
            'completed': completed,
            'pending': pending,
            'failed': failed,
            'percentage': round(completed / len(tasks) * 100, 2) if tasks else 0.0
        }
    
    def get_chunk_files(self, output_pattern: str = "chunk_*.mp4") -> list:
        """获取所有生成的视频片段文件"""
        chunk_files = sorted(self.project_dir.glob(output_pattern))
        return chunk_files
    
    def cleanup_checkpoints(self, keep_completed: bool = True):
        """清理检查点文件
        
        Args:
            keep_completed: 是否保留已完成的检查点
        """
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            task_id = checkpoint_file.stem
            
            checkpoint = self.load_checkpoint(task_id)
            if checkpoint:
                if keep_completed and checkpoint.status == 'completed':
                    continue
                checkpoint_file.unlink()
        
        logger.info("已清理检查点文件")
