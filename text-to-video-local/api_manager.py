#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI API 管理器 - 统一管理多个 AI 服务商的 API 调用

支持平台：
- OpenAI (GPT 系列)
- Anthropic (Claude 系列)
- DashScope (通义千问)
- 自定义兼容 API
- Cookie 模式 (豆包/文心/Kimi 等)

功能：
1. 统一接口封装
2. 多 API 配置管理（增删改查）
3. 自动验证和测试
4. 智能选择最优 API
5. Cookie 代理模式支持
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


class AIAPIConfig:
    """单个 AI API 配置的容器"""
    
    def __init__(
        self,
        name: str,
        api_type: str = 'openai_chat',
        provider: str = '',
        api_key: str = '',
        api_base: str = '',
        model_name: str = '',
        timeout: int = 60,
        max_retries: int = 3,
        enabled: bool = True,
        priority: int = 0,
        created_at: str = None,
        last_used: str = None,
        success_count: int = 0,
        fail_count: int = 0,
        usage_tags: List[str] = None
    ):
        self.name = name
        self.api_type = api_type
        self.provider = provider
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled
        self.priority = priority
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
        self.success_count = success_count
        self.fail_count = fail_count
        self.usage_tags = usage_tags or []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'api_type': self.api_type,
            'provider': self.provider,
            'api_key': self.api_key,
            'api_base': self.api_base,
            'model_name': self.model_name,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'enabled': self.enabled,
            'priority': self.priority,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'usage_tags': self.usage_tags
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'AIAPIConfig':
        """从字典创建"""
        # 确保 usage_tags 存在且为列表
        if 'usage_tags' not in data:
            data['usage_tags'] = []
        elif not isinstance(data['usage_tags'], list):
            data['usage_tags'] = []
        return AIAPIConfig(**data)


class AIAPIWrapper:
    """单个 AI API 的调用封装"""
    
    def __init__(self, config: AIAPIConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose
        self.session = requests.Session()
        self._setup_session()
    
    def _log(self, message: str, level: str = "INFO"):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [API:{self.config.name}] [{level}] {message}")
    
    def _setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AISystem/1.0'
        })
        
        if self.config.api_type != 'cookie' and self.config.api_key:
            self.session.headers['Authorization'] = f"Bearer {self.config.api_key}"
    
    def detect_api_type(self, base_url: str) -> str:
        """根据 URL 自动检测 API 类型"""
        parsed = urlparse(base_url)
        host = parsed.netloc.lower()
        
        if 'openai.com' in host:
            return 'openai_chat'
        elif 'anthropic.com' in host:
            return 'anthropic'
        elif 'aliyuncs.com' in host or 'dashscope' in host:
            return 'dashscope'
        elif 'baidu.com' in host:
            return 'ernie'
        elif 'byte' in host or 'doubao' in host:
            return 'doubao'
        elif 'moonshot' in host:
            return 'kimi'
        else:
            return 'custom'
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试 API 连接
        
        Returns:
            (是否成功，消息)
        """
        try:
            start_time = time.time()
            
            if self.config.api_type == 'openai_chat':
                # OpenAI 标准接口测试
                url = f"{self.config.api_base}/models"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    duration = time.time() - start_time
                    self._log(f"连接成功 ({duration:.1f}s)", "SUCCESS")
                    return True, f"连接成功，响应时间：{duration:.1f}s"
                else:
                    return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
            elif self.config.api_type == 'anthropic':
                # Anthropic 特殊测试
                url = f"{self.config.api_base}/models"
                headers = {'x-api-key': self.config.api_key}
                response = self.session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    duration = time.time() - start_time
                    return True, f"连接成功 ({duration:.1f}s)"
                else:
                    return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
            elif self.config.api_type == 'dashscope':
                # DashScope 通义千问测试
                url = f"{self.config.api_base}/models"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    duration = time.time() - start_time
                    return True, f"连接成功 ({duration:.1f}s)"
                else:
                    return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
            else:
                # 通用测试或 Cookie 模式
                if hasattr(self.config, 'cookie_value') and self.config.cookie_value:
                    # Cookie 验证需要特定逻辑
                    self._log("Cookie 模式暂不支持自动验证", "WARNING")
                    return True, "Cookie 模式需要手动验证"
                else:
                    self._log(f"未知 API 类型：{self.config.api_type}", "WARNING")
                    return True, "未执行验证"
        
        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器，请检查 URL 和网络"
        except Exception as e:
            return False, f"异常：{str(e)}"
    
    def chat_completion(
        self,
        messages: List[dict],
        **kwargs
    ) -> Optional[dict]:
        """
        执行聊天对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数
            
        Returns:
            响应数据，失败返回 None
        """
        if not self.config.enabled:
            self._log("该 API 已禁用", "WARNING")
            return None
        
        url = f"{self.config.api_base}/chat/completions"
        
        payload = {
            'model': self.config.model_name,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048)
        }
        
        headers = {}
        if self.config.api_type == 'anthropic':
            headers['x-api-key'] = self.config.api_key
        
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                
                if self.config.api_type == 'anthropic':
                    payload = {
                        'model': self.config.model_name,
                        'messages': messages,
                        'max_tokens': payload['max_tokens']
                    }
                    url = f"{self.config.api_base}/v1/messages"
                    
                response = self.session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    self.config.last_used = datetime.now().isoformat()
                    self.config.success_count += 1
                    self._log(f"请求成功 ({duration:.1f}s)", "SUCCESS")
                    return result
                else:
                    error_msg = response.text[:200]
                    self._log(f"HTTP {response.status_code}: {error_msg}", "ERROR")
                    
                    if response.status_code >= 500:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        self.config.fail_count += 1
                        return None
                        
            except Exception as e:
                self._log(f"请求异常 (尝试 {attempt + 1}/{self.config.max_retries}): {e}", "ERROR")
                self.config.fail_count += 1
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                
                return None
        
        return None


class MultiAPIManager:
    """多 API 管理器 - 支持增删改查和调度"""
    
    CONFIG_FILE = Path("./cloud_ai_configs.json")
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.configs: Dict[str, AIAPIConfig] = {}
        self.wrappers: Dict[str, AIAPIWrapper] = {}
        self._load_configs()
    
    def _log(self, message: str, level: str = "INFO"):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [APIManager] [{level}] {message}")
    
    def _load_configs(self):
        """加载配置文件"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, config_data in data.items():
                        config = AIAPIConfig.from_dict(config_data)
                        self.configs[key] = config
                        self.wrappers[key] = AIAPIWrapper(config, self.verbose)
                        self._log(f"加载配置：{config.name} ({key})", "INFO")
            except Exception as e:
                self._log(f"加载配置文件失败：{e}", "ERROR")
    
    def _save_configs(self):
        """保存配置文件"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                data = {key: config.to_dict() for key, config in self.configs.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log("配置已保存到云 ai_configs.json", "INFO")
        except Exception as e:
            self._log(f"保存配置文件失败：{e}", "ERROR")
    
    def add_api(
        self,
        name: str,
        api_type: str = 'openai_chat',
        provider: str = '',
        api_key: str = '',
        api_base: str = '',
        model_name: str = '',
        timeout: int = 60,
        max_retries: int = 3,
        priority: int = 0,
        usage_tags: List[str] = None
    ) -> Tuple[bool, str]:
        """
        添加新 API 配置
        
        Returns:
            (是否成功，消息)
        """
        if name in self.configs:
            return False, f"配置 '{name}' 已存在"
        
        config = AIAPIConfig(
            name=name,
            api_type=api_type,
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            priority=priority,
            usage_tags=usage_tags
        )
        
        self.configs[name] = config
        self.wrappers[name] = AIAPIWrapper(config, self.verbose)
        self._save_configs()
        
        self._log(f"添加 API 配置：{name}", "INFO")
        return True, f"API 配置 '{name}' 添加成功"
    
    def update_api(self, name: str, **kwargs) -> Tuple[bool, str]:
        """
        更新已有 API 配置
        
        Returns:
            (是否成功，消息)
        """
        if name not in self.configs:
            return False, f"配置 '{name}' 不存在"
        
        config = self.configs[name]
        
        allowed_fields = ['api_type', 'provider', 'api_key', 'api_base', 
                         'model_name', 'timeout', 'max_retries', 'enabled', 'priority', 'usage_tags']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                # 确保 usage_tags 是列表
                if key == 'usage_tags' and not isinstance(value, list):
                    value = []
                setattr(config, key, value)
        
        # 如果修改了关键信息，需要重新创建 wrapper
        if any(key in ['api_type', 'api_key', 'api_base', 'model_name'] for key in kwargs):
            self.wrappers[name] = AIAPIWrapper(config, self.verbose)
        
        self._save_configs()
        self._log(f"更新 API 配置：{name}", "INFO")
        return True, f"API 配置 '{name}' 更新成功"
    
    def delete_api(self, name: str) -> Tuple[bool, str]:
        """
        删除 API 配置
        
        Returns:
            (是否成功，消息)
        """
        if name not in self.configs:
            return False, f"配置 '{name}' 不存在"
        
        del self.configs[name]
        del self.wrappers[name]
        self._save_configs()
        
        self._log(f"删除 API 配置：{name}", "INFO")
        return True, f"API 配置 '{name}' 已删除"
    
    def get_api(self, name: str, show_key: bool = False) -> Optional[dict]:
        """获取指定 API 的配置"""
        if name in self.configs:
            config = self.configs[name]
            result = config.to_dict()
            # 根据参数决定是否显示完整密钥
            if result['api_key'] and not show_key:
                result['api_key'] = '*' * 8 + result['api_key'][-4:] if len(result['api_key']) > 8 else '****'
            return result
        return None
    
    def list_apis(self) -> List[dict]:
        """列出所有 API 配置"""
        apis = []
        for name, config in sorted(self.configs.items(), key=lambda x: -x[1].priority):
            data = config.to_dict()
            if data['api_key']:
                data['api_key'] = '*' * 8 + data['api_key'][-4:] if len(data['api_key']) > 8 else '****'
            apis.append(data)
        return apis
    
    def test_api(self, name: str) -> Tuple[bool, str]:
        """
        测试 API 连接
        
        Returns:
            (是否成功，消息)
        """
        if name not in self.wrappers:
            return False, f"配置 '{name}' 不存在"
        
        wrapper = self.wrappers[name]
        return wrapper.test_connection()
    
    def auto_detect_and_add(
        self,
        name: str,
        api_base: str,
        api_key: str = ''
    ) -> Tuple[bool, str, dict]:
        """
        自动检测 API 类型并添加配置
        
        Returns:
            (是否成功，消息，配置快照)
        """
        wrapper = AIAPIWrapper(AIAPIConfig(name="temp", api_base=api_base))
        detected_type = wrapper.detect_api_type(api_base)
        
        presets = {
            'openai_chat': {
                'provider': 'gpt-4o-mini',
                'model_name': 'gpt-4o-mini'
            },
            'anthropic': {
                'provider': 'claude-sonnet',
                'model_name': 'claude-3-5-sonnet-20240620'
            },
            'dashscope': {
                'provider': 'qwen',
                'model_name': 'qwen-max'
            }
        }
        
        preset = presets.get(detected_type, {})
        
        success, msg = self.add_api(
            name=name,
            api_type=detected_type,
            provider=preset.get('provider', ''),
            api_key=api_key,
            api_base=api_base,
            model_name=preset.get('model_name', '')
        )
        
        snapshot = self.get_api(name) if success else None
        return success, msg, snapshot
    
    def select_best_api(self) -> Optional[str]:
        """
        智能选择最优 API
        
        策略：
        1. 只选择启用的
        2. 优先选成功率高的
        3. 考虑优先级
        
        Returns:
            最优 API 名称
        """
        candidates = []
        
        for name, config in self.configs.items():
            if not config.enabled:
                continue
            
            total = config.success_count + config.fail_count
            success_rate = config.success_count / total if total > 0 else 0
            
            score = config.priority * 10 + success_rate * 100
            candidates.append((name, score))
        
        if not candidates:
            self._log("没有可用的 API", "WARNING")
            return None
        
        candidates.sort(key=lambda x: -x[1])
        best = candidates[0][0]
        self._log(f"选择最优 API: {best} (得分：{candidates[0][1]:.1f})", "INFO")
        
        return best
    
    def chat(
        self,
        messages: List[dict],
        api_name: str = None,
        **kwargs
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        发送聊天请求（自动选择 API）
        
        Returns:
            (响应数据，使用的 API 名称)
        """
        if api_name is None:
            api_name = self.select_best_api()
        
        if not api_name or api_name not in self.wrappers:
            self._log("没有可用的 API", "ERROR")
            return None, None
        
        wrapper = self.wrappers[api_name]
        result = wrapper.chat_completion(messages, **kwargs)
        
        return result, api_name
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            'total': len(self.configs),
            'enabled': sum(1 for c in self.configs.values() if c.enabled),
            'configs': {}
        }
        
        for name, config in self.configs.items():
            total_calls = config.success_count + config.fail_count
            success_rate = config.success_count / total_calls if total_calls > 0 else 0
            
            stats['configs'][name] = {
                'enabled': config.enabled,
                'priority': config.priority,
                'success_rate': f"{success_rate * 100:.1f}%",
                'total_calls': total_calls,
                'last_used': config.last_used
            }
        
        return stats


if __name__ == '__main__':
    # 测试代码
    manager = MultiAPIManager(verbose=True)
    
    print("\n" + "="*60)
    print("AI API Manager - 功能演示")
    print("="*60)
    
    # 1. 列出已有配置
    print("\n📋 现有配置:")
    apis = manager.list_apis()
    if apis:
        for api in apis:
            print(f"  - {api['name']} ({api['api_type']}) - 启用：{api['enabled']}")
    else:
        print("  (暂无)")
    
    # 2. 自动检测并添加
    print("\n🔍 测试自动检测...")
    test_url = "https://api.openai.com/v1"
    success, msg, config = manager.auto_detect_and_add("test_openai", test_url)
    print(f"  {msg}")
    
    # 3. 查看统计
    print("\n📊 统计信息:")
    stats = manager.get_stats()
    print(f"  总配置数：{stats['total']}")
    print(f"  启用数量：{stats['enabled']}")
    
    # 4. 打印详细配置
    print("\n✅ 已完成")
