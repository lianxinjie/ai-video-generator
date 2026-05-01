#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 计算卸载模块 - 通过豆包等 AI API 分担计算任务
"""

import requests
import time
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AIOffloadEngine:
    """AI 计算卸载引擎"""
    
    def __init__(
        self,
        api_provider: str = "doubao",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        enabled: bool = False
    ):
        """
        初始化 AI 卸载引擎
        
        Args:
            api_provider: API 提供商 (doubao, openai 等)
            api_key: API 密钥
            api_base: API 基础 URL
            timeout: 请求超时 (秒)
            max_retries: 最大重试次数
            enabled: 是否启用
        """
        self.api_provider = api_provider
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled
        
        # API 端点
        if api_base:
            self.api_endpoint = api_base
        elif api_provider == "doubao":
            self.api_endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        else:
            self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
        
        if enabled:
            logger.info(f"AI 卸载已启用：{api_provider}")
        else:
            logger.info("AI 卸载已禁用")
    
    def enhance_prompt(self, base_prompt: str, chunk_index: int) -> str:
        """
        通过 AI 优化提示词
        
        Args:
            base_prompt: 基础提示词
            chunk_index: 片段索引
            
        Returns:
            优化后的提示词
        """
        if not self.enabled:
            return base_prompt
        
        system_prompt = """你是一位专业的视频生成提示词优化专家。
请将用户的基础提示词优化为更适合 AI 视频生成的详细描述。
要求：
1. 增加视觉细节描述
2. 指定镜头运动和视角
3. 描述光影和色彩
4. 保持与原始意图一致
5. 适配分段生成，确保连贯性"""

        user_prompt = f"""基础提示词：{base_prompt}
当前片段序号：{chunk_index}
请优化这个提示词，使其适合生成 1 秒的视频片段。"""

        try:
            response = self._call_api(system_prompt, user_prompt)
            if response and 'choices' in response:
                enhanced = response['choices'][0]['message']['content']
                logger.info(f"提示词优化完成")
                return enhanced
        except Exception as e:
            logger.error(f"提示词优化失败：{e}")
        
        return base_prompt
    
    def generate_transition_prompt(
        self,
        current_chunk: int,
        total_chunks: int,
        base_prompt: str
    ) -> str:
        """
        生成过渡提示词，确保片段连贯性
        
        Args:
            current_chunk: 当前片段序号
            total_chunks: 总片段数
            base_prompt: 基础提示词
            
        Returns:
            带过渡信息的提示词
        """
        if not self.enabled:
            return base_prompt
        
        transition_info = f"这是第{current_chunk}/{total_chunks}个片段"
        if current_chunk == 1:
            transition_info += "，这是开头片段，需要建立场景"
        elif current_chunk == total_chunks:
            transition_info += "，这是结尾片段，需要完成叙事"
        else:
            transition_info += "，需要与前一个片段保持视觉连贯性"
        
        return f"{base_prompt}. {transition_info}"
    
    def suggest_parameters(self, gpu_memory_mb: int) -> Dict:
        """
        根据 GPU 显存建议生成参数
        
        Args:
            gpu_memory_mb: GPU 显存 (MB)
            
        Returns:
            建议的参数配置
        """
        if gpu_memory_mb < 2048:
            return {
                'resolution': (256, 256),
                'num_frames': 8,
                'num_inference_steps': 15,
                'recommendation': '显存非常有限，建议使用最低配置'
            }
        elif gpu_memory_mb < 4096:
            return {
                'resolution': (384, 384),
                'num_frames': 12,
                'num_inference_steps': 20,
                'recommendation': '显存紧张，建议使用中等配置'
            }
        else:
            return {
                'resolution': (512, 512),
                'num_frames': 16,
                'num_inference_steps': 25,
                'recommendation': '显存充足，可以使用较高配置'
            }
    
    def _call_api(
        self,
        system: str,
        user: str,
        retries: int = 0
    ) -> Optional[Dict]:
        """调用 AI API"""
        if retries >= self.max_retries:
            logger.error("AI API 调用达到最大重试次数")
            return None
        
        payload = {
            'model': 'doubao-pro-4k',
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user}
            ],
            'temperature': 0.7,
            'max_tokens': 500
        }
        
        try:
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"AI API 调用失败，重试 {retries + 1}/{self.max_retries}: {e}"
            )
            time.sleep(2 ** retries)  # 指数退避
            return self._call_api(system, user, retries + 1)
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled
    
    def get_cost_estimate(self, task_type: str) -> Dict:
        """
        估算 API 调用成本
        
        Args:
            task_type: 任务类型
            
        Returns:
            预估的 token 数和成本
        """
        # 豆包定价 (参考)
        pricing = {
            'prompt_enhancement': {'input_tokens': 100, 'output_tokens': 200, 'cost': 0.001},
            'transition_suggestion': {'input_tokens': 80, 'output_tokens': 150, 'cost': 0.0008},
            'parameter_suggestion': {'input_tokens': 50, 'output_tokens': 100, 'cost': 0.0005}
        }
        return pricing.get(task_type, {'input_tokens': 0, 'output_tokens': 0, 'cost': 0})
