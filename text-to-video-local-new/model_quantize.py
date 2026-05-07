#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型量化工具
减小显存占用，提升推理速度
"""

import os
import sys
import argparse
from pathlib import Path
import torch


class ModelQuantizer:
    """模型量化器"""
    
    def __init__(self, model_name: str, output_dir: str = "./quantized_models"):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def quantize_to_int8(self) -> str:
        """量化到 INT8（减少 50% 显存）"""
        print(f"开始 INT8 量化：{self.model_name}")
        
        try:
            from optimum.onnxruntime import ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig
            
            # 加载模型
            print("加载模型...")
            model_path = self._download_model()
            
            # 配置量化
            quant_config = AutoQuantizationConfig.int8(
                is_static=False,
                per_channel=True
            )
            
            # 执行量化
            print("执行量化...")
            quantizer = ORTQuantizer.from_pretrained(model_path)
            quantized_path = self.output_dir / f"{self.model_name}_int8"
            
            quantizer.quantize(
                save_dir=quantized_path,
                quantization_config=quant_config
            )
            
            print(f"✓ INT8 量化完成：{quantized_path}")
            return str(quantized_path)
            
        except ImportError:
            print("错误：需要安装 optimum 和 onnxruntime")
            print("运行：pip install optimum onnxruntime-gpu")
            raise
    
    def quantize_to_fp16(self) -> str:
        """量化到 FP16（减少 50% 显存，保持精度）"""
        print(f"开始 FP16 量化：{self.model_name}")
        
        # 对于 PyTorch 模型，直接使用 float16 dtype 加载
        print("FP16 模式下加载模型...")
        
        # 这通常在模型加载时指定 dtype=torch.float16
        # 这里只是创建配置文件
        
        config_path = self.output_dir / f"{self.model_name}_fp16_config.json"
        with open(config_path, "w") as f:
            f.write('{"dtype": "float16", "device": "cuda"}')
        
        print(f"✓ FP16 配置已保存：{config_path}")
        return str(config_path)
    
    def _download_model(self) -> str:
        """下载模型"""
        model_map = {
            "modelscope": "damo/text-to-video-synthesis",
            "cogvideox": "THUDM/CogVideoX-5b",
            "animatediff": "guoyww/animatediff-motion-adapter-v1-5-2",
        }
        
        if self.model_name not in model_map:
            raise ValueError(f"不支持的模型：{self.model_name}")
        
        try:
            from huggingface_hub import snapshot_download
            
            cache_dir = Path("./models")
            cache_dir.mkdir(exist_ok=True)
            
            model_path = snapshot_download(
                repo_id=model_map[self.model_name],
                cache_dir=str(cache_dir)
            )
            
            return model_path
            
        except Exception as e:
            print(f"下载失败：{e}")
            raise
    
    def convert_to_onnx(self) -> str:
        """转换为 ONNX 格式（加速推理）"""
        print(f"开始 ONNX 转换：{self.model_name}")
        
        try:
            from optimum.exporters.onnx import main_export
            
            model_path = self._download_model()
            output_path = self.output_dir / f"{self.model_name}_onnx"
            
            print("转换中...")
            
            main_export(
                model_name_or_path=model_path,
                output=output_path,
                opset=15
            )
            
            print(f"✓ ONNX 转换完成：{output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"ONNX 转换失败：{e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="模型量化工具")
    
    parser.add_argument(
        "--model", "-m",
        required=True,
        choices=["modelscope", "cogvideox", "animatediff", "svd"],
        help="要量化的模型"
    )
    
    parser.add_argument(
        "--bits", "-b",
        type=int,
        choices=[8, 16],
        default=8,
        help="量化位数（8=INT8, 16=FP16）"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./quantized_models",
        help="输出目录"
    )
    
    parser.add_argument(
        "--onnx",
        action="store_true",
        help="转换为 ONNX 格式"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="量化后进行性能测试"
    )
    
    args = parser.parse_args()
    
    # 创建量化器
    quantizer = ModelQuantizer(args.model, args.output)
    
    # 执行量化
    if args.bits == 8:
        result_path = quantizer.quantize_to_int8()
    elif args.bits == 16:
        result_path = quantizer.quantize_to_fp16()
    
    # ONNX 转换
    if args.onnx:
        onnx_path = quantizer.convert_to_onnx()
        print(f"ONNX 模型：{onnx_path}")
    
    # 性能测试
    if args.benchmark:
        print("\n运行性能测试...")
        # TODO: 实现性能测试逻辑
    
    print("\n✓ 量化完成！")


if __name__ == "__main__":
    main()
