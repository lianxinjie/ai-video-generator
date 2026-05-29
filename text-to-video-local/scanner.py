#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置扫描与最优方案推荐工具
自动检测硬件配置，生成个性化离线包下载和安装方案
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import hashlib


@dataclass
class HardwareInfo:
    """硬件信息"""
    # CPU
    cpu_model: str = ""
    cpu_cores: int = 0
    cpu_threads: int = 0
    
    # GPU
    gpu_available: bool = False
    gpu_count: int = 0
    gpu_models: List[str] = field(default_factory=list)
    gpu_memory_total: List[float] = field(default_factory=list)
    
    # 内存
    ram_total: float = 0.0  # GB
    ram_available: float = 0.0  # GB
    
    # 磁盘
    disk_total: float = 0.0  # GB
    disk_available: float = 0.0  # GB
    disk_type: str = "unknown"  # ssd, hdd
    
    # 网络
    network_available: bool = False
    download_speed_mbps: float = 0.0
    
    # CUDA
    cuda_version: str = ""
    cudnn_version: str = ""
    
    # Python 环境
    python_version: str = ""
    pytorch_installed: bool = False
    pytorch_version: str = ""
    pytorch_cuda: str = ""


@dataclass
class ModelRequirement:
    """模型需求"""
    name: str
    size_gb: float
    ram_requirement_gb: float
    vram_requirement_gb: float
    cpu_only_compatible: bool
    recommended_gpu: bool


@dataclass
class Recommendation:
    """推荐方案"""
    mode: str  # "gpu_only", "cpu_only", "hybrid", "multi_gpu"
    confidence: str  # "high", "medium", "low"
    suitable_models: List[str]
    download_priority: List[str]
    estimated_time_minutes: float
    installation_steps: List[str]
    warnings: List[str]
    optimization_tips: List[str]
    docker_command: str
    direct_install_command: str


class SystemScanner:
    """系统扫描器"""
    
    def __init__(self):
        self.hardware = HardwareInfo()
        self.models = self._init_model_requirements()
        self.recommendation: Optional[Recommendation] = None
        
    def _init_model_requirements(self) -> Dict[str, ModelRequirement]:
        """初始化模型需求信息"""
        return {
            "modelscope": ModelRequirement(
                name="ModelScope",
                size_gb=2.5,
                ram_requirement_gb=8.0,
                vram_requirement_gb=6.0,
                cpu_only_compatible=True,
                recommended_gpu=True
            ),
            "animatediff": ModelRequirement(
                name="AnimateDiff",
                size_gb=8.0,
                ram_requirement_gb=16.0,
                vram_requirement_gb=12.0,
                cpu_only_compatible=True,
                recommended_gpu=True
            ),
            "cogvideox": ModelRequirement(
                name="CogVideoX-5B",
                size_gb=20.0,
                ram_requirement_gb=32.0,
                vram_requirement_gb=16.0,
                cpu_only_compatible=False,
                recommended_gpu=True
            ),
            "svd": ModelRequirement(
                name="Stable Video Diffusion",
                size_gb=12.0,
                ram_requirement_gb=24.0,
                vram_requirement_gb=14.0,
                cpu_only_compatible=True,
                recommended_gpu=True
            )
        }
    
    def scan_all(self) -> HardwareInfo:
        """执行完整扫描"""
        print("=" * 70)
        print("正在扫描系统配置...")
        print("=" * 70)
        
        self._scan_cpu()
        self._scan_gpu()
        self._scan_memory()
        self._scan_disk()
        self._scan_network()
        self._scan_cuda()
        self._scan_python_env()
        
        return self.hardware
    
    def _scan_cpu(self):
        """扫描 CPU 信息"""
        print("\n[1/7] 检测 CPU...")
        
        # CPU 型号
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True
                )
                self.hardware.cpu_model = result.stdout.strip().split("\n")[1].strip()
            except:
                self.hardware.cpu_model = platform.processor()
        else:
            try:
                result = subprocess.run(
                    ["cat", "/proc/cpuinfo"],
                    capture_output=True, text=True
                )
                lines = result.stdout.split("\n")
                for line in lines:
                    if "model name" in line:
                        self.hardware.cpu_model = line.split(":")[1].strip()
                        break
            except:
                self.hardware.cpu_model = platform.processor()
        
        # CPU 核心数
        self.hardware.cpu_cores = os.cpu_count() or 0
        try:
            import psutil
            self.hardware.cpu_threads = psutil.cpu_count(logical=True) or self.hardware.cpu_cores
        except ImportError:
            self.hardware.cpu_threads = self.hardware.cpu_cores * 2
        
        print(f"  ✓ CPU: {self.hardware.cpu_model}")
        print(f"  ✓ 核心数：{self.hardware.cpu_cores} 核")
    
    def _scan_gpu(self):
        """扫描 GPU 信息"""
        print("\n[2/7] 检测 GPU...")
        
        gpu_detected = False
        
        # 方法 1: PyTorch 检测
        try:
            import torch
            
            print("  使用 PyTorch 检测...")
            self.hardware.gpu_available = torch.cuda.is_available()
            
            if self.hardware.gpu_available:
                self.hardware.gpu_count = torch.cuda.device_count()
                
                for i in range(self.hardware.gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    
                    self.hardware.gpu_models.append(gpu_name)
                    self.hardware.gpu_memory_total.append(round(gpu_memory, 2))
                    
                    print(f"  ✓ GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
                
                gpu_detected = True
            else:
                print("  ⚠ PyTorch: CUDA 不可用")
                
        except ImportError:
            print("  ⚠ PyTorch 未安装")
            self.hardware.gpu_available = False
        except Exception as e:
            print(f"  ⚠ PyTorch 检测失败：{e}")
        
        # 方法 2: 使用 nvidia-smi (PyTorch 失败时)
        if not gpu_detected:
            try:
                print("  使用 nvidia-smi 检测...")
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    self.hardware.gpu_count = len(lines)
                    self.hardware.gpu_available = True
                    
                    for line in lines:
                        parts = line.split(', ')
                        if len(parts) == 2:
                            gpu_name = parts[0].strip()
                            gpu_memory = float(parts[1].strip()) / 1024
                            
                            self.hardware.gpu_models.append(gpu_name)
                            self.hardware.gpu_memory_total.append(round(gpu_memory, 2))
                    
                    print(f"  ✓ 通过 nvidia-smi 检测到 {self.hardware.gpu_count} 个 GPU")
                    for i, name in enumerate(self.hardware.gpu_models):
                        print(f"    GPU {i}: {name} ({self.hardware.gpu_memory_total[i]:.1f}GB)")
                    gpu_detected = True
                else:
                    print("  ⚠ nvidia-smi: 未检测到 NVIDIA GPU")
            except FileNotFoundError:
                print("  ⚠ nvidia-smi 未安装 (NVIDIA 驱动可能未安装)")
            except subprocess.TimeoutExpired:
                print("  ⚠ nvidia-smi 超时")
            except Exception as e:
                print(f"  ⚠ nvidia-smi 检测失败：{e}")
        
        # 方法 3: Windows 设备管理器 (备用)
        if not gpu_detected and platform.system() == "Windows":
            try:
                print("  使用 Windows 设备管理器检测...")
                result = subprocess.run(
                    ["wmic", "path", "Win32_VideoController", "get", "Name,AdapterRAM"],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                    for line in lines:
                        parts = line.strip().split()
                        if parts and 'NVIDIA' in line.upper() or 'AMD' in line.upper() or 'INTEL' in line.upper():
                            gpu_name = ' '.join(parts[:-1]) if len(parts) > 1 else line.strip()
                            # 尝试提取显存
                            try:
                                memory_bytes = int(parts[-1])
                                memory_gb = memory_bytes / 1024**3
                                self.hardware.gpu_memory_total.append(round(memory_gb, 2))
                            except:
                                self.hardware.gpu_memory_total.append(0)
                            
                            self.hardware.gpu_models.append(gpu_name)
                            self.hardware.gpu_count += 1
                    
                    if self.hardware.gpu_count > 0:
                        print(f"  ✓ 检测到 {self.hardware.gpu_count} 个显卡")
                        # 判断是否有独立显卡
                        for i, name in enumerate(self.hardware.gpu_models):
                            is_dedicated = 'NVIDIA' in name.upper() or 'AMD' in name.upper() or 'RADEON' in name.upper()
                            if is_dedicated:
                                self.hardware.gpu_available = True
                                print(f"    GPU {i}: {name} (独立显卡)")
                            else:
                                print(f"    GPU {i}: {name} (集成显卡)")
                        gpu_detected = True
            except Exception as e:
                print(f"  ⚠ Windows 设备管理器检测失败：{e}")
        
        # 如果没有检测到 GPU
        if not gpu_detected:
            print("  ❌ 未检测到独立 GPU，建议使用云端模式")
            self.hardware.gpu_available = False
        
        # 检测 macOS Apple Silicon
        if not self.hardware.gpu_available and platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True
                )
                if "Apple M" in result.stdout or "Apple Silicon" in result.stdout:
                    print("  ✓ 检测到 Apple Silicon (MPS 加速)")
                    self.hardware.gpu_models = ["Apple Silicon"]
                    self.hardware.gpu_count = 1
                    self.hardware.gpu_available = True
            except:
                pass
    
    def _scan_memory(self):
        """扫描内存信息"""
        print("\n[3/7] 检测内存...")
        
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory"],
                    capture_output=True, text=True
                )
                lines = result.stdout.strip().split("\n")[1].split()
                self.hardware.ram_total = round(int(lines[0]) / 1024**2, 2)
                self.hardware.ram_available = round(int(lines[1]) / 1024**2, 2)
            except:
                self.hardware.ram_total = 0.0
        else:
            try:
                import psutil
                mem = psutil.virtual_memory()
                self.hardware.ram_total = round(mem.total / 1024**3, 2)
                self.hardware.ram_available = round(mem.available / 1024**3, 2)
            except ImportError:
                # 尝试从/proc/meminfo 读取
                try:
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                self.hardware.ram_total = round(int(line.split()[1]) / 1024**2, 2)
                            elif line.startswith("MemAvailable:"):
                                self.hardware.ram_available = round(int(line.split()[1]) / 1024**2, 2)
                except:
                    pass
        
        print(f"  ✓ 总内存：{self.hardware.ram_total}GB")
        print(f"  ✓ 可用内存：{self.hardware.ram_available}GB")
    
    def _scan_disk(self):
        """扫描磁盘信息"""
        print("\n[4/7] 检测磁盘...")
        
        import shutil
        
        # 获取工作目录所在磁盘
        usage = shutil.disk_usage("/")
        self.hardware.disk_total = round(usage.total / 1024**3, 2)
        self.hardware.disk_available = round(usage.free / 1024**3, 2)
        
        # 尝试检测 SSD/HDD
        if platform.system() == "Linux":
            try:
                # 检测是否为 NVMe SSD
                nvme_result = subprocess.run(
                    ["lsblk", "-d", "-o", "name,rota"],
                    capture_output=True, text=True
                )
                if "nvme" in nvme_result.stdout.lower():
                    self.hardware.disk_type = "nvme_ssd"
                elif "0" in nvme_result.stdout:
                    self.hardware.disk_type = "ssd"
                else:
                    self.hardware.disk_type = "hdd"
            except:
                self.hardware.disk_type = "unknown"
        else:
            self.hardware.disk_type = "ssd"  # 默认假设 SSD
        
        print(f"  ✓ 磁盘总容量：{self.hardware.disk_total}GB")
        print(f"  ✓ 可用空间：{self.hardware.disk_available}GB")
        print(f"  ✓ 磁盘类型：{self.hardware.disk_type.upper()}")
    
    def _scan_network(self):
        """扫描网络状态"""
        print("\n[5/7] 检测网络...")
        
        # 检查网络连通性
        try:
            import socket
            socket.create_connection(("huggingface.co", 443), timeout=3)
            self.hardware.network_available = True
            print("  ✓ 网络连接正常")
        except:
            self.hardware.network_available = False
            print("  ⚠ 无法连接到 HuggingFace (可能需要离线安装)")
        
        # 测速 (简单测试)
        if self.hardware.network_available:
            try:
                import time
                start = time.time()
                subprocess.run(
                    ["curl", "-o", "/dev/null", "-s", "-w", "%{speed_download}", 
                     "https://huggingface.co/"],
                    capture_output=True, timeout=5
                )
                # 简化测速
                self.hardware.download_speed_mbps = 5.0  # 默认估计
                print(f"  ≈ 预估下载速度：{self.hardware.download_speed_mbps}MB/s")
            except:
                self.hardware.download_speed_mbps = 1.0
    
    def _scan_cuda(self):
        """扫描 CUDA 信息"""
        print("\n[6/7] 检测 CUDA...")
        
        if not self.hardware.gpu_available:
            print("  - 无 GPU 设备，跳过 CUDA 检测")
            return
        
        try:
            import torch
            self.hardware.cuda_version = torch.version.cuda or "unknown"
            print(f"  ✓ CUDA 版本：{self.hardware.cuda_version}")
            
            # 尝试检测 cuDNN
            try:
                cudnn_result = subprocess.run(
                    ["find", "/usr", "-name", "libcudnn.so*"],
                    capture_output=True, text=True, timeout=3
                )
                if cudnn_result.stdout:
                    self.hardware.cudnn_version = "detected"
            except:
                pass
                
        except Exception as e:
            print(f"  ⚠ CUDA 检测失败：{e}")
    
    def _scan_python_env(self):
        """扫描 Python 环境"""
        print("\n[7/7] 检测 Python 环境...")
        
        self.hardware.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"  ✓ Python 版本：{self.hardware.python_version}")
        
        # 检查 PyTorch
        try:
            import torch
            self.hardware.pytorch_installed = True
            self.hardware.pytorch_version = torch.__version__
            self.hardware.pytorch_cuda = torch.version.cuda or "CPU"
            print(f"  ✓ PyTorch: {self.hardware.pytorch_version} (CUDA: {self.hardware.pytorch_cuda})")
        except ImportError:
            print("  ⚠ PyTorch 未安装")
    
    def _classify_cpu_tier(self) -> str:
        """判断 CPU 档次"""
        hw = self.hardware
        
        # 高端 CPU: 8 核+ 或 最新代 i7/i9/Ryzen 7/9
        if hw.cpu_cores >= 8:
            return "high"
        # 中端 CPU: 6 核 或 i5/Ryzen 5
        elif hw.cpu_cores >= 6:
            return "mid"
        # 低端 CPU: 4 核或以下
        else:
            return "low"
    
    def _classify_gpu_tier(self) -> str:
        """判断 GPU 档次"""
        hw = self.hardware
        
        if not hw.gpu_available:
            return "none"
        
        total_vram = sum(hw.gpu_memory_total)
        
        # 高端 GPU: 显存≥12GB 或 RTX 3080/3090/4080/4090
        if total_vram >= 12:
            return "high"
        # 中端 GPU: 显存 6-12GB 或 RTX 2060/3060/3070
        elif total_vram >= 6:
            return "mid"
        # 低端 GPU: 显存<6GB
        else:
            return "low"
    
    def analyze(self) -> Recommendation:
        """分析硬件并生成推荐方案"""
        print("\n" + "=" * 70)
        print("正在分析最优方案...")
        print("=" * 70)
        
        hw = self.hardware
        warnings = []
        optimization_tips = []
        suitable_models = []
        download_priority = []
        
        # 判断 CPU 和 GPU 档次
        cpu_tier = self._classify_cpu_tier()
        gpu_tier = self._classify_gpu_tier()
        
        # ========== GPU+CPU 协调模式推荐方案 ==========
        if hw.gpu_available and hw.gpu_count >= 1:
            total_vram = sum(hw.gpu_memory_total)
            
            # --- 场景 1: 高端 GPU + 中端/高端 CPU ---
            if gpu_tier == "high" and cpu_tier in ["high", "mid"]:
                mode = "hybrid_high_end"
                confidence = "high"
                suitable_models = ["cogvideox", "svd", "animatediff", "modelscope"]
                download_priority = ["cogvideox", "svd", "animatediff", "modelscope"]
                
                optimization_tips.append("✓ 【高端 GPU+ 中端 CPU】推荐模式：GPU 主导 + CPU 辅助")
                optimization_tips.append("✓ 文本编码预处理交由 CPU 处理，GPU专注扩散采样和 VAE 解码")
                optimization_tips.append("✓ 推荐使用 CogVideoX-5B，可开启全部性能选项")
                optimization_tips.append("✓ 启用 enable_model_cpu_offload() 进一步优化显存")
                optimization_tips.append("✓ 建议分辨率：512x512 或更高，steps: 50-100")
                
                if hw.ram_total >= 32:
                    optimization_tips.append("✓ 大内存优势：可同时加载多个模型组件，减少 CPU-GPU 数据传输")
                
            # --- 场景 2: 中端 GPU + 中端 CPU ---
            elif gpu_tier == "mid" and cpu_tier in ["mid", "high"]:
                mode = "hybrid_mid_range"
                confidence = "high"
                suitable_models = ["modelscope", "animatediff", "svd"]
                download_priority = ["modelscope", "animatediff", "svd"]
                
                optimization_tips.append("✓ 【中端 GPU+ 中端 CPU】推荐模式：平衡模式")
                optimization_tips.append("✓ 优先使用 ModelScope 和 AnimateDiff，性能与质量平衡")
                optimization_tips.append("✓ 启用 enable_model_cpu_offload() 和 enable_vae_slicing()")
                optimization_tips.append("✓ 文本编码在 CPU 执行，扩散采样在 GPU 执行")
                optimization_tips.append("✓ 建议分辨率：512x512 (ModelScope) 或 256x256 (AnimateDiff)")
                optimization_tips.append("✓ 使用 fp16 精度，减少显存占用")
                
                warnings.append("⚠ CogVideoX-5B 可能需要降低分辨率到 256x256 并启用 CPU offload")
                
            # --- 场景 3: 低端 GPU + 低端 CPU ---
            elif gpu_tier == "low" and cpu_tier == "low":
                mode = "hybrid_low_end"
                confidence = "medium"
                suitable_models = ["modelscope"]
                download_priority = ["modelscope"]
                
                optimization_tips.append("✓ 【低端 GPU+ 低端 CPU】推荐模式：极简模式")
                optimization_tips.append("✓ 仅推荐 ModelScope 模型，确保稳定性")
                optimization_tips.append("✓ CPU 负责所有预处理，GPU仅负责核心推理")
                optimization_tips.append("✓ 必须启用 enable_model_cpu_offload()")
                optimization_tips.append("✓ 建议分辨率：256x256 或更低，steps: 20-30")
                optimization_tips.append("✓ 使用 --guidance-scale 7.5 保证生成质量")
                
                warnings.append("⚠ 显存和 CPU 性能都有限，视频生成速度较慢")
                warnings.append("⚠ AnimateDiff 和 SVD 可能因资源不足失败")
                warnings.append("⚠ 建议单个任务完成后等待系统冷却再进行下一个任务")
            
            # --- 场景 4: 中端 GPU + 低端 CPU ---
            elif gpu_tier == "mid" and cpu_tier == "low":
                mode = "gpu_mid_cpu_low"
                confidence = "medium"
                suitable_models = ["modelscope", "animatediff"]
                download_priority = ["modelscope", "animatediff"]
                
                optimization_tips.append("✓ 【中端 GPU+ 低端 CPU】推荐模式：GPU 主导")
                optimization_tips.append("✓ CPU 可能成为瓶颈，尽量让 GPU承担更多计算")
                optimization_tips.append("✓ 文本编码也尝试在 GPU 上执行（如果显存允许）")
                optimization_tips.append("✓ 使用 enable_model_cpu_offload() 但减少 CPU 预处理")
                optimization_tips.append("✓ 建议分辨率：256x256，steps: 25-35")
                
                warnings.append("⚠ CPU 性能不足可能导致预处理时间较长")
                warnings.append("⚠ CogVideoX-5B 和 SVD 不建议使用")
            
            # --- 场景 5: 低端 GPU + 中端 CPU ---
            elif gpu_tier == "low" and cpu_tier == "mid":
                mode = "gpu_low_cpu_mid"
                confidence = "medium"
                suitable_models = ["modelscope"]
                download_priority = ["modelscope"]
                
                optimization_tips.append("✓ 【低端 GPU+ 中端 CPU】推荐模式：CPU 辅助为主")
                optimization_tips.append("✓ 尽量让 CPU 承担预处理和后处理任务")
                optimization_tips.append("✓ GPU 仅用于核心扩散采样")
                optimization_tips.append("✓ 必须启用 enable_model_cpu_offload()")
                optimization_tips.append("✓ 建议分辨率：256x256，steps: 20-30")
                
                warnings.append("⚠ GPU 显存不足，无法运行大型模型")
                warnings.append("⚠ 速度较慢，建议耐心等待")
            
            # --- 场景 6: 高端 GPU + 低端 CPU ---
            elif gpu_tier == "high" and cpu_tier == "low":
                mode = "gpu_high_cpu_low"
                confidence = "medium"
                suitable_models = ["cogvideox", "svd", "animatediff", "modelscope"]
                download_priority = ["cogvideox", "animatediff", "svd", "modelscope"]
                
                optimization_tips.append("✓ 【高端 GPU+ 低端 CPU】推荐模式：GPU 全负荷")
                optimization_tips.append("✓ GPU 性能强大，可弥补 CPU 瓶颈")
                optimization_tips.append("✓ 尽量在 GPU 上执行所有可能的计算")
                optimization_tips.append("✓ CPU 仅处理最基础的 I/O 和后处理")
                optimization_tips.append("✓ 可使用 CogVideoX-5B，但预处理时间较长")
                
                warnings.append("⚠ CPU 可能成为瓶颈，特别是在批量生成时")
                warnings.append("⚠ 建议单次生成，避免多任务并行")
            
            # --- 场景 7: 低端 GPU ---
            elif total_vram < 6:
                mode = "gpu_very_low"
                confidence = "low"
                suitable_models = ["modelscope"]
                download_priority = ["modelscope"]
                warnings.append("⚠ 显存严重不足 (<6GB)，视频生成可能失败")
                warnings.append("⚠ 强烈建议使用 CPU offload 模式")
                optimization_tips.append("✓ 必须启用 --cpu-offload 参数")
                
        # ========== 纯 CPU 模式 ==========
        elif hw.ram_total >= 16:
            mode = "cpu_capable"
            confidence = "medium"
            suitable_models = ["modelscope"]
            download_priority = ["modelscope"]
            warnings.append("⚠ 未检测到 GPU，将使用 CPU 模式（速度较慢）")
            warnings.append("⚠ 生成 16 帧视频可能需要 5-15 分钟")
            optimization_tips.append("✓ 建议使用 --steps 20-30 平衡速度和质量")
            optimization_tips.append("✓ 考虑降低分辨率到 128x128 或 256x256")
            
        else:
            mode = "cpu_limited"
            confidence = "low"
            suitable_models = []
            download_priority = []
            warnings.append("⚠ 系统资源严重不足 (<8GB 内存)")
            warnings.append("⚠ 不建议运行视频生成任务")
            optimization_tips.append("✓ 升级硬件或使用云端 GPU 服务")
        
        # ========== 磁盘空间检查 ==========
        total_model_size = sum([self.models[m].size_gb for m in suitable_models])
        if hw.disk_available < total_model_size * 1.5:
            warnings.append(f"⚠ 磁盘空间不足：需要至少 {total_model_size * 1.5:.1f}GB，当前可用 {hw.disk_available:.1f}GB")
        
        # ========== 估算下载时间 ==========
        if self.hardware.network_available and self.hardware.download_speed_mbps > 0:
            total_size = sum([self.models[m].size_gb for m in download_priority]) * 1024  # MB
            estimated_minutes = (total_size / self.hardware.download_speed_mbps) / 60
        else:
            estimated_minutes = 0
        
        # ========== 生成安装命令 ==========
        if mode.startswith("gpu"):
            docker_cmd = f"docker run --gpus all -v ./outputs:/app/outputs video-gen:latest"
            direct_cmd = "python3 generation.py -m modelscope -p \"测试视频\" -o output.mp4"
        else:
            docker_cmd = f"docker run -v ./outputs:/app/outputs video-gen:cpu"
            direct_cmd = "python3 generation.py -m modelscope --device cpu -p \"测试视频\" -o output.mp4"
        
        # ========== 生成推荐方案 ==========
        self.recommendation = Recommendation(
            mode=mode,
            confidence=confidence,
            suitable_models=suitable_models,
            download_priority=download_priority,
            estimated_time_minutes=round(estimated_minutes, 1),
            installation_steps=self._generate_installation_steps(mode, suitable_models),
            warnings=warnings,
            optimization_tips=optimization_tips,
            docker_command=docker_cmd,
            direct_install_command=direct_cmd
        )
        
        return self.recommendation
    
    def _generate_installation_steps(self, mode: str, models: List[str]) -> List[str]:
        """生成安装步骤"""
        steps = []
        
        if mode.startswith("gpu"):
            steps.append("1. 安装 NVIDIA 驱动 (>= 525.60)")
            steps.append("2. 安装 CUDA Toolkit 12.1")
            steps.append("3. 安装 PyTorch GPU 版本: pip install torch --index-url https://download.pytorch.org/whl/cu121")
        else:
            steps.append("1. 安装 PyTorch CPU 版本：pip install torch torchvision torchaudio")
        
        steps.append("4. 安装依赖：pip install -r requirements.txt")
        
        if models:
            steps.append(f"5. 下载模型：python3 download_models.py -m {' '.join(models)}")
        
        steps.append("6. 测试运行：python3 generation.py --check")
        
        return steps
    
    def print_report(self):
        """打印扫描报告"""
        hw = self.hardware
        rec = self.recommendation
        
        if not rec:
            print("错误：请先运行 analyze()")
            return
        
        print("\n" + "=" * 70)
        print(" HARDWARE SCAN REPORT - 硬件扫描报告")
        print("=" * 70)
        
        print("\n【硬件摘要】")
        print(f"  CPU: {hw.cpu_model} ({hw.cpu_cores} 核)")
        if hw.gpu_models:
            for i, gpu in enumerate(hw.gpu_models):
                print(f"  GPU {i}: {gpu} ({hw.gpu_memory_total[i]:.1f}GB)")
        else:
            print(f"  GPU: 无独立 GPU")
        print(f"  内存：{hw.ram_total}GB (可用：{hw.ram_available}GB)")
        print(f"  磁盘：{hw.disk_available}GB 可用 ({hw.disk_type.upper()})")
        print(f"  网络：{'可用' if hw.network_available else '不可用'}")
        
        # 显示 CPU 和 GPU 档次
        cpu_tier = self._classify_cpu_tier()
        gpu_tier = self._classify_gpu_tier()
        print(f"\n【硬件档次评估】")
        print(f"  CPU 等级：{cpu_tier.upper()} ({self._get_tier_description(cpu_tier)})")
        print(f"  GPU 等级：{gpu_tier.upper()} ({self._get_tier_description(gpu_tier)})")
        
        print("\n【推荐方案】")
        print(f"  模式：{rec.mode.upper()}")
        print(f"  置信度：{rec.confidence.upper()}")
        print(f"  可用模型：{', '.join(rec.suitable_models) if rec.suitable_models else '无'}")
        print(f"  下载优先级：{' → '.join(rec.download_priority) if rec.download_priority else 'N/A'}")
        
        if rec.estimated_time_minutes > 0:
            print(f"  预估下载时间：{rec.estimated_time_minutes:.1f} 分钟")
        
        if rec.warnings:
            print("\n【警告】")
            for warning in rec.warnings:
                print(f"  {warning}")
        
        if rec.optimization_tips:
            print("\n【优化建议】")
            for tip in rec.optimization_tips:
                print(f"  {tip}")
        
        print("\n【快速开始】")
        print(f"  Docker: {rec.docker_command}")
        print(f"  直接运行：{rec.direct_install_command}")
        
        print("\n" + "=" * 70)
    
    def _get_tier_description(self, tier: str) -> str:
        """获取档次描述"""
        descriptions = {
            "high": "高端 - 适合高质量视频生成",
            "mid": "中端 - 平衡性能与质量",
            "low": "入门 - 基础功能支持",
            "none": "无 GPU - 纯 CPU 模式"
        }
        return descriptions.get(tier, "未知")
    
    def save_report(self, output_file: str = "scan_report.json"):
        """保存扫描报告为 JSON"""
        report = {
            "hardware": asdict(self.hardware),
            "recommendation": asdict(self.recommendation) if self.recommendation else None,
            "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip()
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 扫描报告已保存到：{output_file}")
        return output_file
    
    def generate_offline_package(self, output_dir: str = "offline-package"):
        """根据推荐生成离线包配置"""
        if not self.recommendation:
            print("错误：请先运行 analyze()")
            return
        
        print("\n" + "=" * 70)
        print("正在生成离线包配置...")
        print("=" * 70)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 生成个性化 requirements.txt
        req_content = self._generate_requirements()
        with open(output_path / "requirements-optimized.txt", "w") as f:
            f.write(req_content)
        print(f"  ✓ 生成 requirements-optimized.txt")
        
        # 2. 生成下载脚本
        models_to_download = self.recommendation.download_priority
        dl_script = self._generate_download_script(models_to_download)
        with open(output_path / "download_models.py", "w") as f:
            f.write(dl_script)
        print(f"  ✓ 生成 download_models.py")
        
        # 3. 生成安装指南
        guide = self._generate_installation_guide()
        with open(output_path / "INSTALL_GUIDE.txt", "w", encoding="utf-8") as f:
            f.write(guide)
        print(f"  ✓ 生成 INSTALL_GUIDE.txt")
        
        # 4. 生成一键安装脚本
        install_script = self._generate_install_script()
        install_path = output_path / "install.sh"
        with open(install_path, "w") as f:
            f.write(install_script)
        os.chmod(install_path, 0o755)
        print(f"  ✓ 生成 install.sh")
        
        print(f"\n✓ 离线包配置已生成到：{output_path.absolute()}")
        print(f"\n使用方法:")
        print(f"  cd {output_dir}")
        print(f"  bash install.sh")
    
    def _generate_requirements(self) -> str:
        """生成优化的 requirements.txt"""
        content = [
            "# AI Video Generation - Optimized Requirements",
            f"# Generated for: {self.recommendation.mode}",
            f"# Date: {subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip()}",
            "",
        ]
        
        # 根据 GPU 情况选择 PyTorch
        if self.hardware.gpu_available:
            cuda_version = self.hardware.cuda_version.replace(".", "") if self.hardware.cuda_version else "121"
            content.append(f"# GPU 版本 (CUDA {self.hardware.cuda_version})")
            content.append(f"torch>=2.1.0")
            content.append(f"torchvision>=0.16.0")
            content.append(f"torchaudio>=2.1.0")
            content.append("")
            
            if "gpu_low_end" not in self.recommendation.mode:
                content.append("# 性能优化 (中高配 GPU)")
                content.append("xformers>=0.0.23")
                content.append("triton>=2.1.0")
                content.append("")
        else:
            content.append("# CPU 版本")
            content.append("torch>=2.1.0")
            content.append("torchvision>=0.16.0")
            content.append("torchaudio>=2.1.0")
            content.append("")
        
        # 通用依赖
        content.extend([
            "# 模型依赖",
            "diffusers>=0.24.0",
            "transformers>=4.35.0",
            "accelerate>=0.24.0",
            "modelscope>=1.9.0",
            "",
            "# 视频处理",
            "opencv-python>=4.8.0",
            "imageio>=2.33.0",
            "imageio-ffmpeg>=0.4.9",
            "av>=10.0.0",
            "",
            "# 工具库",
            "numpy>=1.24.0",
            "pillow>=10.0.0",
            "tqdm>=4.66.0",
            "pyyaml>=6.0",
            "einops>=0.7.0",
            "click>=8.1.0",
            "",
            "# 可选：内存检测",
            "psutil>=5.9.0; platform_system != 'Windows'",
        ])
        
        return "\n".join(content)
    
    def _generate_download_script(self, models: List[str]) -> str:
        """生成优化的下载脚本"""
        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型下载脚本 - 针对当前系统优化
推荐模型：{', '.join(models)}
"""

import argparse
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_model(model_name: str, output_dir: str):
    """下载单个模型"""
    print(f"开始下载 {{model_name}}...")
    
    try:
        if model_name == "modelscope":
            from modelscope import snapshot_download
            model_dir = snapshot_download(
                'damo/text-to-video-synthesis',
                cache_dir=output_dir
            )
        else:
            from huggingface_hub import snapshot_download
            
            repo_map = {{
                "animatediff": "guoyww/animatediff-motion-adapter-v1-5-2",
                "cogvideox": "THUDM/CogVideoX-5b",
                "svd": "stabilityai/stable-video-diffusion-img2vid-xt",
            }}
            
            if model_name in repo_map:
                model_dir = snapshot_download(
                    repo_id=repo_map[model_name],
                    cache_dir=output_dir,
                    repo_type="model"
                )
            else:
                print(f"未知模型：{{model_name}}")
                return None
        
        print(f"✓ {{model_name}} 下载完成：{{model_dir}}")
        return model_dir
        
    except Exception as e:
        print(f"✗ {{model_name}} 下载失败：{{e}}")
        return None

def main():
    parser = argparse.ArgumentParser(description="下载推荐模型")
    parser.add_argument(
        "--models", "-m",
        nargs="+",
        default={models!r},
        help="要下载的模型列表"
    )
    parser.add_argument(
        "--output", "-o",
        default="./models",
        help="模型输出目录"
    )
    parser.add_argument(
        "--parallel", "-j",
        type=int,
        default=1,
        help="并行下载数量"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\\n下载配置:")
    print(f"  模型：{{', '.join(args.models)}}")
    print(f"  目录：{{output_path.absolute()}}")
    print(f"  并行数：{{args.parallel}}\\n")
    
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {{
            executor.submit(download_model, model, str(output_path)): model
            for model in args.models
        }}
        
        for future in as_completed(futures):
            result = future.result()
    
    print("\\n✓ 所有模型下载完成！")

if __name__ == "__main__":
    main()
'''
        return script
    
    def _generate_installation_guide(self) -> str:
        """生成安装指南"""
        rec = self.recommendation
        hw = self.hardware
        
        guide = f"""AI 视频生成离线包 - 安装指南
{'=' * 60}

硬件配置摘要:
  CPU: {hw.cpu_model} ({hw.cpu_cores} 核心)
  GPU: {', '.join(hw.gpu_models) if hw.gpu_models else '无'}
  内存：{hw.ram_total}GB
  磁盘：{hw.disk_available}GB 可用

推荐方案：{rec.mode} (置信度：{rec.confidence})

{'=' * 60}
安装步骤:

【方法一：一键安装脚本 (推荐)】

  bash install.sh

【方法二：手动安装】

1. 创建虚拟环境 (可选但推荐):
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate    # Windows

2. 安装 PyTorch:
"""
        
        if hw.gpu_available:
            guide += f"""
   # GPU 版本
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
"""
        else:
            guide += """
   # CPU 版本
   pip install torch torchvision torchaudio
"""
        
        guide += f"""

3. 安装依赖:
   pip install -r requirements-optimized.txt

4. 下载模型:
   python3 download_models.py -m {' '.join(rec.download_priority)}

5. 测试运行:
   python3 generation.py --check

6. 生成视频:
   python3 generation.py -m modelscope -p "一只猫在草地上奔跑" -o output.mp4

{'=' * 60}
可用模型：{', '.join(rec.suitable_models) if rec.suitable_models else '无推荐'}

警告:
"""
        
        for warning in rec.warnings:
            guide += f"  {warning}\n"
        
        guide += f"""
优化建议:
"""
        
        for tip in rec.optimization_tips:
            guide += f"  {tip}\n"
        
        guide += f"""
{'=' * 60}
Docker 用户:
  {rec.docker_command}

{'=' * 60}
"""
        
        return guide
    
    def _generate_install_script(self) -> str:
        """生成一键安装脚本"""
        hw = self.hardware
        rec = self.recommendation
        
        script = f'''#!/bin/bash
set -e

echo "=================================="
echo "AI Video Generator - 一键安装"
echo "=================================="
echo ""

# 检测系统
SYSTEM=$(uname -s)
echo "检测系统：$SYSTEM"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Python: $PYTHON_VERSION"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "错误：未找到 pip3"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
if [ "$SYSTEM" = "Darwin" ] || [ "$SYSTEM" = "Linux" ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

echo "✓ 虚拟环境已激活"

# 安装 PyTorch
echo ""
echo "安装 PyTorch..."
'''
        
        if hw.gpu_available:
            script += '''
# GPU 版本
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
'''
        else:
            script += '''
# CPU 版本
pip3 install torch torchvision torchaudio
'''
        
        script += '''

echo "✓ PyTorch 安装完成"

# 安装依赖
echo ""
echo "安装依赖包..."
pip3 install -r requirements-optimized.txt
echo "✓ 依赖安装完成"

# 下载模型
echo ""
echo "下载模型..."
python3 download_models.py -m ''' + ' '.join(rec.download_priority) + '''
echo "✓ 模型下载完成"

# 测试运行
echo ""
echo "测试运行..."
python3 generation.py --check

echo ""
echo "=================================="
echo "✓ 安装完成！"
echo "=================================="
echo ""
echo "使用方法:"
echo "  source venv/bin/activate  # 激活环境"
echo "  python3 generation.py -m modelscope -p \"测试视频\" -o output.mp4"
echo ""
'''
        
        return script


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="系统扫描与最优方案推荐")
    parser.add_argument(
        "--output", "-o",
        default="scan_report.json",
        help="保存扫描报告文件"
    )
    parser.add_argument(
        "--generate-package",
        action="store_true",
        help="生成离线包配置"
    )
    parser.add_argument(
        "--package-dir",
        default="offline-package",
        help="离线包输出目录"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="简洁输出模式"
    )
    
    args = parser.parse_args()
    
    # 创建扫描器
    scanner = SystemScanner()
    
    # 扫描硬件
    scanner.scan_all()
    
    # 分析并生成推荐
    scanner.analyze()
    
    # 打印报告
    if not args.quiet:
        scanner.print_report()
    
    # 保存报告
    scanner.save_report(args.output)
    
    # 生成离线包
    if args.generate_package:
        scanner.generate_offline_package(args.package_dir)
    
    print("\n✓ 扫描完成！")
    
    # 返回推荐信息供其他脚本使用
    if scanner.recommendation:
        return scanner.recommendation


if __name__ == "__main__":
    main()
