"""
云端 AI 平台接口层

支持平台：
- SeaArt.ai
- Tensor.art
- Bing Image Creator
- 通义万相 (Aliyun)
- LiblibAI
- Raphael AI

功能：
1. 统一接口封装
2. 自动选择最优平台
3. 积分/额度管理
4. 失败重试和降级
"""

import os
import json
import time
import random
import hashlib
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path


class CloudPlatformBase:
    """云平台基类"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        self.api_key = api_key
        self.verbose = verbose
        self.daily_limit = 0
        self.used_today = 0
        self.last_reset = datetime.now().date()
    
    def _log(self, message: str, level: str = "INFO"):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{self.platform_name}] [{level}] {message}")
    
    def _check_daily_reset(self):
        """检查是否跨天，重置计数器"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.used_today = 0
            self.last_reset = today
            self._log("新的一天，积分计数器已重置", "INFO")
    
    @property
    def platform_name(self) -> str:
        return "Base"
    
    @property
    def remaining_quota(self) -> int:
        self._check_daily_reset()
        return max(0, self.daily_limit - self.used_today)
    
    def is_available(self) -> bool:
        """检查平台是否可用"""
        self._check_daily_reset()
        return self.remaining_quota > 0
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成图片
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            图片 URL 或本地路径，失败返回 None
        """
        raise NotImplementedError
    
    def parse_response(self, response: dict) -> Optional[str]:
        """解析响应，提取图片 URL"""
        raise NotImplementedError


class SeaArtPlatform(CloudPlatformBase):
    """SeaArt.ai 平台"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 100  # 每日约 60-100 积分
        self.base_url = "https://api.seaart.ai"
    
    @property
    def platform_name(self) -> str:
        return "SeaArt"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        使用 SeaArt 生成图片
        
        注意：实际使用需要注册账号并获取 API key
        这里提供接口框架，实际调用需要根据官方 API 文档实现
        """
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        # TODO: 实现真实的 API 调用
        # 示例代码结构：
        # headers = {"Authorization": f"Bearer {self.api_key}"}
        # payload = {
        #     "prompt": prompt,
        #     "width": kwargs.get('width', 512),
        #     "height": kwargs.get('height', 512),
        #     "steps": kwargs.get('steps', 20),
        # }
        # response = requests.post(f"{self.base_url}/generate", json=payload, headers=headers)
        # result = response.json()
        # image_url = self.parse_response(result)
        
        # 模拟返回（实际使用时删除）
        time.sleep(random.uniform(5, 10))  # 模拟 API 延迟
        self.used_today += 1
        self._log(f"积分剩余：{self.remaining_quota}/{self.daily_limit}", "INFO")
        
        # 返回示例 URL
        return f"https://example.com/seaart_{int(time.time())}.jpg"
    
    def parse_response(self, response: dict) -> Optional[str]:
        """解析 SeaArt 响应"""
        # TODO: 根据实际 API 响应结构调整
        try:
            return response.get('data', {}).get('image_url')
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class TensorPlatform(CloudPlatformBase):
    """Tensor.art 平台"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 100  # 每日 100 积分
        self.base_url = "https://api.tensor.art"
    
    @property
    def platform_name(self) -> str:
        return "Tensor"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        # TODO: 实现真实的 API 调用
        time.sleep(random.uniform(3, 8))
        self.used_today += 1
        self._log(f"积分剩余：{self.remaining_quota}/{self.daily_limit}", "INFO")
        
        return f"https://example.com/tensor_{int(time.time())}.jpg"
    
    def parse_response(self, response: dict) -> Optional[str]:
        try:
            return response.get('result', {}).get('url')
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class BingPlatform(CloudPlatformBase):
    """Bing Image Creator (免费)"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 100  # Bing 限制较宽松
        self.session = requests.Session()
    
    @property
    def platform_name(self) -> str:
        return "Bing"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        # Bing Image Creator 通常需要浏览器 cookie
        # 这里提供框架，实际使用需要实现 cookie 管理
        
        try:
            # TODO: 实现真实的 API 调用
            time.sleep(random.uniform(10, 20))  # Bing 通常较慢
            self.used_today += 1
            
            return f"https://example.com/bing_{int(time.time())}.jpg"
        except Exception as e:
            self._log(f"生成失败：{e}", "ERROR")
            return None
    
    def parse_response(self, response: dict) -> Optional[str]:
        try:
            if 'images' in response:
                return response['images'][0].get('url')
            return None
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class AliyunPlatform(CloudPlatformBase):
    """通义万相 (阿里云)"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 200  # 免费额度较高
        self.base_url = "https://dashscope.aliyuncs.com"
    
    @property
    def platform_name(self) -> str:
        return "Aliyun"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        # 通义万相 API
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "wanx-v1",
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "style": kwargs.get('style', '<auto>'),
                    "size": kwargs.get('size', '1024*1024'),
                    "n": 1
                }
            }
            
            # TODO: 实现真实调用
            # response = requests.post(f"{self.base_url}/api/v1/services/aigc/text-generation/generation",
            #                        json=payload, headers=headers)
            
            time.sleep(random.uniform(5, 15))
            self.used_today += 1
            self._log(f"额度剩余：{self.remaining_quota}/{self.daily_limit}", "INFO")
            
            return f"https://example.com/aliyun_{int(time.time())}.jpg"
        except Exception as e:
            self._log(f"生成失败：{e}", "ERROR")
            return None
    
    def parse_response(self, response: dict) -> Optional[str]:
        try:
            return response.get('output', {}).get('results', [{}])[0].get('url')
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class LiblibPlatform(CloudPlatformBase):
    """LiblibAI (国内平台，速度快)"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 150
        self.base_url = "https://api.liblib.ai"
    
    @property
    def platform_name(self) -> str:
        return "Liblib"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        try:
            # TODO: 实现真实 API 调用
            time.sleep(random.uniform(2, 6))  # 国内速度快
            self.used_today += 1
            
            return f"https://example.com/liblib_{int(time.time())}.jpg"
        except Exception as e:
            self._log(f"生成失败：{e}", "ERROR")
            return None
    
    def parse_response(self, response: dict) -> Optional[str]:
        try:
            return response.get('data', {}).get('imageUrl')
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class RaphaelPlatform(CloudPlatformBase):
    """Raphael AI"""
    
    def __init__(self, api_key: str = None, verbose: bool = True):
        super().__init__(api_key, verbose)
        self.daily_limit = 100
        self.base_url = "https://api.raphael.ai"
    
    @property
    def platform_name(self) -> str:
        return "Raphael"
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        self._log(f"生成图片：{prompt[:50]}...", "INFO")
        
        try:
            # TODO: 实现真实 API 调用
            time.sleep(random.uniform(3, 8))
            self.used_today += 1
            
            return f"https://example.com/raphael_{int(time.time())}.jpg"
        except Exception as e:
            self._log(f"生成失败：{e}", "ERROR")
            return None
    
    def parse_response(self, response: dict) -> Optional[str]:
        try:
            return response.get('result', {}).get('image_url')
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None


class CloudPlatformManager:
    """云平台管理器 - 智能选择和调度"""
    
    def __init__(self, api_keys: Dict[str, str] = None, verbose: bool = True):
        """
        初始化云平台管理器
        
        Args:
            api_keys: API密钥字典 {"seaart": "xxx", "tensor": "yyy", ...}
            verbose: 是否输出详细信息
        """
        self.verbose = verbose
        self.platforms: Dict[str, CloudPlatformBase] = {}
        self.platform_stats: Dict[str, Dict] = {}
        
        # 初始化各平台
        self._init_platforms(api_keys or {})
        
        # 速度统计（用于智能选择）
        self.speed_history: Dict[str, List[float]] = {
            platform: [] for platform in self.platforms.keys()
        }
    
    def _log(self, message: str, level: str = "INFO"):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [CloudManager] [{level}] {message}")
    
    def _init_platforms(self, api_keys: Dict[str, str]):
        """初始化所有平台"""
        platform_classes = {
            'seaart': SeaArtPlatform,
            'tensor': TensorPlatform,
            'bing': BingPlatform,
            'aliyun': AliyunPlatform,
            'liblib': LiblibPlatform,
            'raphael': RaphaelPlatform
        }
        
        for name, platform_class in platform_classes.items():
            api_key = api_keys.get(name)
            try:
                self.platforms[name] = platform_class(api_key, self.verbose)
                self.platform_stats[name] = {
                    'success_count': 0,
                    'fail_count': 0,
                    'avg_speed': 0.0
                }
                self._log(f"初始化平台：{name}", "INFO")
            except Exception as e:
                self._log(f"初始化平台 {name} 失败：{e}", "ERROR")
    
    def get_available_platforms(self) -> List[str]:
        """获取可用的平台列表"""
        available = []
        for name, platform in self.platforms.items():
            if platform.is_available():
                available.append(name)
        return available
    
    def select_best_platform(self) -> Optional[str]:
        """
        智能选择最优平台
        
        选择策略：
        1. 只考虑可用平台
        2. 优先选择历史速度快的
        3. 考虑成功率
        4. 负载均衡
        
        Returns:
            最优平台名称，无可用平台返回 None
        """
        available = self.get_available_platforms()
        
        if not available:
            self._log("所有平台都不可用", "ERROR")
            return None
        
        if len(available) == 1:
            return available[0]
        
        # 计算综合得分
        scores = {}
        for name in available:
            stats = self.platform_stats[name]
            
            # 速度得分（越快分越高，0-100）
            speed_score = 100 / (1 + stats['avg_speed']) if stats['avg_speed'] > 0 else 50
            
            # 成功率得分（0-100）
            total = stats['success_count'] + stats['fail_count']
            success_rate = stats['success_count'] / total if total > 0 else 0.5
            success_score = success_rate * 100
            
            # 综合得分
            scores[name] = speed_score * 0.6 + success_score * 0.4
        
        # 选择得分最高的
        best = max(scores, key=scores.get)
        self._log(f"选择平台：{best} (得分：{scores[best]:.1f})", "INFO")
        
        return best
    
    def generate_image(
        self,
        prompt: str,
        preferred_platform: str = None,
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        生成图片（自动选择平台）
        
        Args:
            prompt: 提示词
            preferred_platform: 首选平台（None=自动选择）
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            (图片 URL 或路径，使用的平台名称)
        """
        retry_count = 0
        
        while retry_count < max_retries:
            # 选择平台
            platform_name = preferred_platform or self.select_best_platform()
            
            if not platform_name:
                self._log("没有可用的云平台", "ERROR")
                return None, None
            
            platform = self.platforms.get(platform_name)
            if not platform:
                self._log(f"平台 {platform_name} 不存在", "ERROR")
                return None, None
            
            if not platform.is_available():
                self._log(f"平台 {platform_name} 额度用完，切换平台", "WARNING")
                retry_count += 1
                continue
            
            # 记录开始时间
            start_time = time.time()
            
            try:
                self._log(f"使用 {platform_name} 生成图片 (尝试 {retry_count + 1}/{max_retries})", "INFO")
                
                # 生成图片
                image_url = platform.generate_image(prompt, **kwargs)
                
                # 记录耗时
                duration = time.time() - start_time
                
                # 更新统计
                if image_url:
                    self.platform_stats[platform_name]['success_count'] += 1
                    # 更新平均速度
                    history = self.speed_history[platform_name]
                    history.append(duration)
                    if len(history) > 10:
                        history = history[-10:]
                    self.platform_stats[platform_name]['avg_speed'] = sum(history) / len(history)
                    
                    self._log(f"生成成功，耗时：{duration:.1f}s", "INFO")
                    return image_url, platform_name
                else:
                    self.platform_stats[platform_name]['fail_count'] += 1
                    self._log(f"生成失败，返回空结果", "ERROR")
                    
            except Exception as e:
                duration = time.time() - start_time
                self.platform_stats[platform_name]['fail_count'] += 1
                self._log(f"生成异常：{e}，耗时：{duration:.1f}s", "ERROR")
            
            retry_count += 1
        
        self._log(f"达到最大重试次数 ({max_retries})，生成失败", "ERROR")
        return None, None
    
    def get_stats(self) -> Dict:
        """获取平台统计信息"""
        stats = {}
        for name, platform in self.platforms.items():
            stats[name] = {
                'available': platform.is_available(),
                'remaining_quota': platform.remaining_quota,
                'daily_limit': platform.daily_limit,
                'success_count': self.platform_stats[name]['success_count'],
                'fail_count': self.platform_stats[name]['fail_count'],
                'avg_speed': self.platform_stats[name]['avg_speed']
            }
        return stats
    
    def print_stats(self):
        """打印平台统计信息"""
        print("\n" + "=" * 60)
        print("☁️  云平台状态")
        print("=" * 60)
        
        stats = self.get_stats()
        for name, info in stats.items():
            status = "✅" if info['available'] else "❌"
            print(f"\n{name.upper()}: {status}")
            print(f"  可用额度：{info['remaining_quota']}/{info['daily_limit']}")
            print(f"  成功/失败：{info['success_count']}/{info['fail_count']}")
            print(f"  平均速度：{info['avg_speed']:.1f}s")
        
        print("=" * 60 + "\n")


if __name__ == '__main__':
    # 测试示例
    manager = CloudPlatformManager(api_keys={})
    
    print("=" * 60)
    print("云平台管理器 - 可用平台测试")
    print("=" * 60)
    
    available = manager.get_available_platforms()
    print(f"\n可用平台：{', '.join(available) if available else '无'}")
    
    # 测试选择最优平台
    best = manager.select_best_platform()
    print(f"推荐平台：{best}")
    
    # 测试生成
    if best:
        print(f"\n使用 {best} 生成测试图片...")
        image_url, platform = manager.generate_image("测试图片，美丽的风景")
        print(f"结果：{image_url}")
        print(f"平台：{platform}")
    
    # 打印统计
    manager.print_stats()
