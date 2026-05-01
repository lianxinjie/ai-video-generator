#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控模块 - 实时监控 GPU、CPU、内存、磁盘使用情况
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("未安装 psutil，系统监控功能受限")

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("未安装 PyTorch，GPU 监控不可用")


@dataclass
class ResourceStatus:
    """资源状态数据类"""
    timestamp: float
    gpu_memory_used: float  # MB
    gpu_memory_total: float  # MB
    gpu_memory_percent: float  # %
    gpu_temperature: Optional[float]  # °C
    cpu_percent: float  # %
    memory_used: float  # MB
    memory_total: float  # MB
    memory_percent: float  # %
    disk_used: float  # GB
    disk_total: float  # GB
    disk_percent: float  # %
    is_safe: bool  # 是否可以继续运行


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(
        self,
        gpu_memory_threshold: float = 75.0,
        gpu_temp_threshold: float = 80.0,
        cpu_threshold: float = 85.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 90.0,
        pause_duration: int = 60
    ):
        """
        初始化资源监控器
        
        Args:
            gpu_memory_threshold: GPU 显存阈值 (%)
            gpu_temp_threshold: GPU 温度阈值 (°C)
            cpu_threshold: CPU 使用率阈值 (%)
            memory_threshold: 系统内存阈值 (%)
            disk_threshold: 磁盘使用率阈值 (%)
            pause_duration: 暂停后等待时间 (秒)
        """
        self.gpu_memory_threshold = gpu_memory_threshold
        self.gpu_temp_threshold = gpu_temp_threshold
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.pause_duration = pause_duration
        
        self.status_history = []
        self.pause_count = 0
        self.total_pause_time = 0
        
        # 检测 GPU
        self.has_gpu = HAS_TORCH and torch.cuda.is_available()
        if self.has_gpu:
            logger.info(f"检测到 GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"  - 显存：{torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")
    
    def get_gpu_info(self) -> Dict:
        """获取 GPU 信息"""
        if not self.has_gpu:
            return {
                'gpu_memory_used': 0,
                'gpu_memory_total': 0,
                'gpu_memory_percent': 0,
                'gpu_temperature': None
            }
        
        # 显存信息
        memory_allocated = torch.cuda.memory_allocated() / 1024 / 1024
        memory_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        memory_percent = (memory_allocated / memory_total) * 100
        
        # 温度 (需要 pynvml)
        temperature = None
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, 0)
            pynvml.nvmlShutdown()
        except Exception:
            pass
        
        return {
            'gpu_memory_used': round(memory_allocated, 2),
            'gpu_memory_total': round(memory_total, 2),
            'gpu_memory_percent': round(memory_percent, 2),
            'gpu_temperature': temperature
        }
    
    def get_cpu_info(self) -> Dict:
        """获取 CPU 信息"""
        if not HAS_PSUTIL:
            return {'cpu_percent': 0}
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.5)
        }
    
    def get_memory_info(self) -> Dict:
        """获取系统内存信息"""
        if not HAS_PSUTIL:
            return {'memory_used': 0, 'memory_total': 0, 'memory_percent': 0}
        
        mem = psutil.virtual_memory()
        return {
            'memory_used': round(mem.used / 1024 / 1024, 2),
            'memory_total': round(mem.total / 1024 / 1024, 2),
            'memory_percent': round(mem.percent, 2)
        }
    
    def get_disk_info(self, path: str = "/") -> Dict:
        """获取磁盘信息"""
        if not HAS_PSUTIL:
            return {'disk_used': 0, 'disk_total': 0, 'disk_percent': 0}
        
        disk = psutil.disk_usage(path)
        return {
            'disk_used': round(disk.used / 1024 / 1024 / 1024, 2),
            'disk_total': round(disk.total / 1024 / 1024 / 1024, 2),
            'disk_percent': round(disk.percent, 2)
        }
    
    def check_status(self) -> ResourceStatus:
        """检查当前资源状态"""
        gpu_info = self.get_gpu_info()
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()
        
        # 判断是否安全
        is_safe = True
        
        if gpu_info['gpu_memory_percent'] >= self.gpu_memory_threshold:
            is_safe = False
            logger.warning(f"GPU 显存占用过高：{gpu_info['gpu_memory_percent']:.1f}%")
        
        if (gpu_info['gpu_temperature'] is not None and 
            gpu_info['gpu_temperature'] >= self.gpu_temp_threshold):
            is_safe = False
            logger.warning(f"GPU 温度过高：{gpu_info['gpu_temperature']:.1f}°C")
        
        if cpu_info['cpu_percent'] >= self.cpu_threshold:
            is_safe = False
            logger.warning(f"CPU 使用率过高：{cpu_info['cpu_percent']:.1f}%")
        
        if memory_info['memory_percent'] >= self.memory_threshold:
            is_safe = False
            logger.warning(f"系统内存占用过高：{memory_info['memory_percent']:.1f}%")
        
        if disk_info['disk_percent'] >= self.disk_threshold:
            is_safe = False
            logger.warning(f"磁盘使用率过高：{disk_info['disk_percent']:.1f}%")
        
        status = ResourceStatus(
            timestamp=time.time(),
            gpu_memory_used=gpu_info['gpu_memory_used'],
            gpu_memory_total=gpu_info['gpu_memory_total'],
            gpu_memory_percent=gpu_info['gpu_memory_percent'],
            gpu_temperature=gpu_info['gpu_temperature'],
            cpu_percent=cpu_info['cpu_percent'],
            memory_used=memory_info['memory_used'],
            memory_total=memory_info['memory_total'],
            memory_percent=memory_info['memory_percent'],
            disk_used=disk_info['disk_used'],
            disk_total=disk_info['disk_total'],
            disk_percent=disk_info['disk_percent'],
            is_safe=is_safe
        )
        
        self.status_history.append(status)
        return status
    
    def should_pause(self) -> bool:
        """判断是否应该暂停"""
        status = self.check_status()
        return not status.is_safe
    
    def clear_gpu_cache(self):
        """清理 GPU 缓存"""
        if self.has_gpu:
            torch.cuda.empty_cache()
            logger.debug("已清理 GPU 缓存")
    
    def wait_for_resources(self, max_wait: int = 600) -> bool:
        """等待资源恢复
        
        Args:
            max_wait: 最大等待时间 (秒)
            
        Returns:
            资源是否恢复
        """
        logger.info(f"等待资源恢复，最多等待 {max_wait} 秒...")
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(10)
            wait_time += 10
            self.clear_gpu_cache()
            
            if self.check_status().is_safe:
                logger.info(f"资源已恢复，等待了 {wait_time} 秒")
                return True
            
            if wait_time % 60 == 0:
                logger.info(f"已等待 {wait_time} 秒...")
        
        logger.error("等待资源超时")
        return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.status_history:
            return {}
        
        gpu_percent_avg = sum(s.gpu_memory_percent for s in self.status_history) / len(self.status_history)
        cpu_percent_avg = sum(s.cpu_percent for s in self.status_history) / len(self.status_history)
        memory_percent_avg = sum(s.memory_percent for s in self.status_history) / len(self.status_history)
        
        return {
            'total_checks': len(self.status_history),
            'pause_count': self.pause_count,
            'total_pause_time': self.total_pause_time,
            'gpu_memory_avg': round(gpu_percent_avg, 2),
            'cpu_avg': round(cpu_percent_avg, 2),
            'memory_avg': round(memory_percent_avg, 2)
        }
    
    def print_status(self):
        """打印当前状态"""
        status = self.check_status()
        
        print("\n" + "=" * 50)
        print(" 资源监控状态")
        print("=" * 50)
        print(f" GPU 显存：{status.gpu_memory_used:.0f}/{status.gpu_memory_total:.0f} MB ({status.gpu_memory_percent:.1f}%)")
        if status.gpu_temperature:
            print(f" GPU 温度：{status.gpu_temperature:.1f}°C")
        print(f" CPU 使用：{status.cpu_percent:.1f}%")
        print(f" 内存使用：{status.memory_used:.0f}/{status.memory_total:.0f} MB ({status.memory_percent:.1f}%)")
        print(f" 磁盘使用：{status.disk_used:.0f}/{status.disk_total:.0f} GB ({status.disk_percent:.1f}%)")
        print(f" 状态：{'✓ 安全' if status.is_safe else '✗ 需要暂停'}")
        print("=" * 50 + "\n")
