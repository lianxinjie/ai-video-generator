# -*- coding: utf-8 -*-
"""
AI 场景分析器 - 通过大语言模型智能判断场景拆分

核心功能：
1. 基于 LLM 的场景语义理解
2. 智能场景边界识别
3. 场景重要性评估
4. 拆分建议生成
5. 支持本地/云端 AI 模型

相比关键词匹配的优势：
- 理解语义而非简单匹配
- 识别隐含的场景转换
- 提供拆分理由和置信度
- 支持多轮交互优化
"""

import json
import re
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime


class AISceneAnalyzer:
    """AI 场景分析器"""
    
    # 系统提示词模板
    SYSTEM_PROMPT = """你是一位专业的视频场景分析专家。你的任务是分析用户提供的视频提示词，判断包含多少个独立场景，并给出拆分建议。

场景判定标准：
1. **时间变化**：日出→日落、白天→夜晚等
2. **空间变化**：室内→室外、城市→森林等
3. **镜头运动**：全景→特写、俯视→平视等
4. **主体变化**：人物 A→人物 B、龙→凤凰等
5. **动作变化**：静止→运动、飞行→战斗等
6. **情绪/氛围变化**：平静→紧张、欢乐→悲伤等

输出格式（JSON）：
{
    "total_scenes": 场景数量（整数）,
    "scenes": [
        {
            "index": 场景索引（从 1 开始）,
            "text": "该场景的原始文本",
            "start_position": 在原文本中的起始位置，
            "end_position": 在原文本中的结束位置，
            "importance": 重要度（0-1，越高越应该独立成段）,
            "scene_type": ["time_change", "location_change", "camera_change", "subject_change", "action_change", "mood_change"],
            "reason": "拆分理由（中文描述）",
            "confidence": 置信度（0-1）,
            "suggested_duration": 建议时长（秒）,
            "transition_to_next": "到下一场景的转场建议"
        }
    ],
    "overall_analysis": "整体分析总结",
    "optimization_suggestions": ["优化建议 1", "优化建议 2"]
}

注意事项：
- 场景数量不要过度拆分，保持语义完整性
- 每个场景应该有明确的主题和视觉焦点
- 重要场景（高 importance）应该独立成段
- 简单描述性内容可以合并"""

    # 简化版提示词（用于快速判断）
    SIMPLE_PROMPT = """分析以下视频提示词包含几个场景，判断每个部分是否应该独立成段。

提示词："{prompt}"

请回答：
1. 场景数量
2. 每个场景的文本和重要度（0-1）
3. 是否建议拆分（是/否）

用 JSON 格式输出。"""

    # AI 通道健康状态
    channel_status: Dict[str, Dict] = {}
    
    def __init__(self,
                 model_type: str = 'local',
                 model_name: str = None,
                 api_key: str = None,
                 api_base: str = None,
                 timeout: int = 10,
                 max_retries: int = 2,
                 enable_health_check: bool = True,
                 fallback_channels: List[str] = None,
                 verbose: bool = True):
        """
        初始化 AI 场景分析器（支持超时和故障转移）
        
        Args:
            model_type: 模型类型 ('local', 'openai', 'claude', 'qwen')
            model_name: 模型名称（本地模型如 'qwen2.5:7b'，云端模型如 'gpt-4'）
            api_key: API Key（云端模式需要）
            api_base: API Base URL（本地模型或自定义 API）
            timeout: 请求超时时间（秒，默认 10 秒）
            max_retries: 最大重试次数（默认 2 次）
            enable_health_check: 启用健康检查（默认 True）
            fallback_channels: 备用通道列表（故障时自动切换）
            verbose: 是否输出详细信息
        """
        self.verbose = verbose
        self.model_type = model_type
        self.model_name = model_name or self._get_default_model(model_type)
        self.api_key = api_key
        self.api_base = api_base or self._get_default_api_base(model_type)
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_health_check = enable_health_check
        self.fallback_channels = fallback_channels or self._get_default_fallback_channels()
        
        # 分析历史
        self.analysis_history: List[Dict] = []
        
        # 当前活跃通道
        self.active_channel = None
        
        # 检查依赖
        self._check_dependencies()
        
        # 初始化通道健康状态
        if enable_health_check:
            self._initialize_channel_status()
        
    def _get_default_model(self, model_type: str) -> str:
        """获取默认模型名称"""
        defaults = {
            'local': 'qwen2.5:7b',  # Ollama 默认
            'openai': 'gpt-3.5-turbo',
            'claude': 'claude-3-haiku-20240307',
            'qwen': 'qwen-turbo'
        }
        return defaults.get(model_type, 'qwen2.5:7b')
    
    def _get_default_api_base(self, model_type: str) -> str:
        """获取默认 API Base URL"""
        defaults = {
            'local': 'http://localhost:11434/v1',  # Ollama
            'openai': 'https://api.openai.com/v1',
            'claude': 'https://api.anthropic.com/v1',
            'qwen': 'https://dashscope.aliyuncs.com/api/v1'
        }
        return defaults.get(model_type, 'http://localhost:11434/v1')
    
    def _check_dependencies(self):
        """检查依赖"""
        try:
            import requests
            self.requests_available = True
        except ImportError:
            self.requests_available = False
            if self.verbose:
                print("[WARNING] 未安装 requests 库，AI 分析功能受限")
    
    def _log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def _get_default_fallback_channels(self) -> List[Dict]:
        """获取默认备用通道列表"""
        return [
            {'model_type': 'qwen', 'model_name': 'qwen-turbo'},  # 通义千问（快速备份）
            {'model_type': 'local', 'model_name': 'qwen2.5:7b'},  # 本地 Ollama
        ]
    
    def _initialize_channel_status(self):
        """初始化通道健康状态"""
        channel_key = f"{self.model_type}/{self.model_name}"
        self.channel_status[channel_key] = {
            'healthy': True,
            'last_check': datetime.now().isoformat(),
            'fail_count': 0,
            'success_count': 0,
            'avg_response_time': 0,
            'last_error': None
        }
        
        for channel in self.fallback_channels:
            key = f"{channel['model_type']}/{channel.get('model_name', 'default')}"
            if key not in self.channel_status:
                self.channel_status[key] = {
                    'healthy': True,
                    'last_check': datetime.now().isoformat(),
                    'fail_count': 0,
                    'success_count': 0
                }
    
    def check_channel_health(self, channel: Optional[Dict] = None) -> bool:
        """检查通道健康状态"""
        import requests
        
        if channel is None:
            channel = {
                'model_type': self.model_type,
                'model_name': self.model_name,
                'api_base': self.api_base,
                'api_key': self.api_key
            }
        
        channel_key = f"{channel['model_type']}/{channel.get('model_name', 'default')}"
        
        if channel_key in self.channel_status:
            status = self.channel_status[channel_key]
            if status['fail_count'] > 3:
                status['healthy'] = False
                return False
        
        try:
            import requests
            test_payload = {
                "model": channel.get('model_name', 'qwen2.5:7b'),
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5
            }
            
            headers = {"Content-Type": "application/json"}
            if channel.get('api_key'):
                headers["Authorization"] = f"Bearer {channel['api_key']}"
            
            response = requests.post(
                f"{channel.get('api_base', self.api_base)}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=5
            )
            
            if response.status_code == 200:
                if channel_key in self.channel_status:
                    self.channel_status[channel_key]['healthy'] = True
                return True
            else:
                if channel_key in self.channel_status:
                    self.channel_status[channel_key]['healthy'] = False
                return False
                
        except Exception as e:
            self._log(f"通道 {channel_key} 健康检查异常：{e}", "ERROR")
            if channel_key in self.channel_status:
                self.channel_status[channel_key]['healthy'] = False
            return False
    
    def get_available_channel(self) -> Optional[Dict]:
        """获取可用通道（自动故障转移）"""
        if self.check_channel_health():
            self.active_channel = {
                'model_type': self.model_type,
                'model_name': self.model_name,
                'api_base': self.api_base,
                'api_key': self.api_key,
                'is_fallback': False
            }
            return self.active_channel
        
        self._log("主通道不可用，尝试备用通道...", "WARNING")
        
        for fallback in self.fallback_channels:
            temp = AISceneAnalyzer(
                model_type=fallback['model_type'],
                model_name=fallback.get('model_name'),
                verbose=False
            )
            
            if temp.check_channel_health():
                self.active_channel = {
                    'model_type': fallback['model_type'],
                    'model_name': fallback.get('model_name') or self._get_default_model(fallback['model_type']),
                    'api_base': fallback.get('api_base') or self._get_default_api_base(fallback['model_type']),
                    'api_key': fallback.get('api_key'),
                    'is_fallback': True
                }
                return self.active_channel
        
        return None
    
    def _update_channel_status(self, success: bool, response_time: float = 0):
        """更新通道状态"""
        if self.active_channel:
            channel_key = f"{self.active_channel['model_type']}/{self.active_channel['model_name']}"
            
            if channel_key not in self.channel_status:
                self.channel_status[channel_key] = {
                    'healthy': True,
                    'fail_count': 0,
                    'success_count': 0
                }
            
            status = self.channel_status[channel_key]
            status['last_check'] = datetime.now().isoformat()
            
            if success:
                status['success_count'] += 1
                total = status['success_count']
                status['avg_response_time'] = (
                    (status['avg_response_time'] * (total - 1) + response_time) / total
                )
            else:
                status['fail_count'] += 1 
                mode: str = 'detailed') -> Dict:
        """
        AI 分析场景
        
        Args:
            prompt: 用户提示词
            mode: 分析模式 ('detailed' 详细 / 'simple' 快速)
            
        Returns:
            分析结果
        """
        if not self.requests_available:
            self._log("requests 库不可用，使用规则_based 分析", "WARNING")
            return self._fallback_analysis(prompt)
        
        try:
            if mode == 'detailed':
                return self._detailed_analysis(prompt)
            else:
                return self._simple_analysis(prompt)
        except Exception as e:
            self._log(f"AI 分析失败：{e}", "ERROR")
            return self._fallback_analysis(prompt)
    
    def _detailed_analysis(self, prompt: str) -> Dict:
        """详细分析模式"""
        self._log(f"开始 AI 详细分析：{prompt[:60]}...", "INFO")
        
        # 构建请求
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析这个视频提示词的场景：{prompt}"}
        ]
        
        # 调用 AI 模型
        response = self._call_llm(messages)
        
        # 解析响应
        result = self._parse_llm_response(response, prompt)
        
        # 记录历史
        self.analysis_history.append({
            'prompt': prompt,
            'mode': 'detailed',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        self._log(f"AI 分析完成：检测到 {result.get('total_scenes', 0)} 个场景", "INFO")
        
        return result
    
    def _simple_analysis(self, prompt: str) -> Dict:
        """快速分析模式"""
        self._log(f"开始 AI 快速分析...", "INFO")
        
        messages = [
            {"role": "system", "content": "你是一位视频场景分析助手。用简洁的 JSON 回答场景数量和建议。"},
            {"role": "user", "content": self.SIMPLE_PROMPT.format(prompt=prompt)}
        ]
        
        response = self._call_llm(messages, temperature=0.3)
        result = self._parse_llm_response(response, prompt, simple_mode=True)
        
        self.analysis_history.append({
            'prompt': prompt,
            'mode': 'simple',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def _call_llm(self, messages: List[Dict], 
                  temperature: float = 0.7) -> str:
        """
        调用 LLM 模型（支持超时、重试和故障转移）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            
        Returns:
            LLM 响应文本
        """
        import requests
        
        # 获取可用通道
        available_channel = self.get_available_channel()
        
        if not available_channel:
            self._log("无可用 AI 通道，使用回退方案", "WARNING")
            raise Exception("AI 通道不可用")
        
        # 自动重试逻辑
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = datetime.now()
                
                # 构建请求体
                payload = {
                    "model": available_channel['model_name'],
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000,
                    "stream": False
                }
                
                # 请求头
                headers = {
                    "Content-Type": "application/json"
                }
                
                if available_channel.get('api_key'):
                    headers["Authorization"] = f"Bearer {available_channel['api_key']}"
                
                # 根据不同模型调整格式
                if available_channel['model_type'] == 'claude':
                    payload = self._adapt_for_claude_with_channel(messages, temperature, available_channel)
                    headers["x-api-key"] = available_channel['api_key']
                    headers["anthropic-version"] = "2023-06-01"
                
                self._log(
                    f"调用 AI 模型：{available_channel['model_name']} @ "
                    f"{available_channel['api_base']} (尝试 {attempt + 1}/{self.max_retries + 1})", 
                    "DEBUG"
                )
                
                # 发送请求（带超时）
                response = requests.post(
                    f"{available_channel['api_base']}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout  # 使用配置的超时时间
                )
                
                # 计算响应时间
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code != 200:
                    raise Exception(f"API 返回错误：{response.status_code} - {response.text[:200]}")
                
                result = response.json()
                
                if not result.get('choices') or len(result['choices']) == 0:
                    raise Exception("API 返回空结果")
                
                content = result['choices'][0]['message']['content']
                
                # 更新通道状态（成功）
                self._update_channel_status(success=True, response_time=response_time)
                
                self._log(f"AI 响应成功，耗时：{response_time:.2f}s", "INFO")
                
                return content
                
            except requests.exceptions.Timeout:
                last_error = f"请求超时（{self.timeout}秒）"
                self._log(f"请求超时：{last_error}", "WARNING")
                self._update_channel_status(success=False)
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接失败：{str(e)}"
                self._log(f"连接错误：{last_error}", "WARNING")
                self._update_channel_status(success=False)
                
            except Exception as e:
                last_error = str(e)
                self._log(f"AI 调用失败：{last_error}", "ERROR")
                self._update_channel_status(success=False)
            
            # 重试前等待
            if attempt < self.max_retries:
                wait_time = min(2 ** attempt, 5)  # 指数退避，最多 5 秒
                self._log(f"{wait_time}秒后重试...", "INFO")
                time.sleep(wait_time)
                
                # 重试前重新检查通道
                available_channel = self.get_available_channel()
                if not available_channel:
                    break
        
        # 所有重试失败
        error_msg = f"AI 调用失败（{self.max_retries + 1}次尝试）：{last_error}"
        self._log(error_msg, "ERROR")
        raise Exception(error_msg)
    
    def _adapt_for_claude_with_channel(self, messages: List[Dict], 
                                        temperature: float,
                                        channel: Dict) -> Dict:
        """适配 Claude API 格式（带通道信息）"""
        system_message = next(
            (m for m in messages if m['role'] == 'system'), 
            None
        )
        user_messages = [m for m in messages if m['role'] != 'system']
        
        return {
            "model": channel['model_name'],
            "max_tokens": 2000,
            "temperature": temperature,
            "system": system_message['content'] if system_message else "",
            "messages": user_messages
        }
    
    def _adapt_for_claude(self, messages: List[Dict], 
                          temperature: float) -> Dict:
        """适配 Claude API 格式"""
        system_message = next(
            (m for m in messages if m['role'] == 'system'), 
            None
        )
        user_messages = [m for m in messages if m['role'] != 'system']
        
        return {
            "model": self.model_name,
            "max_tokens": 2000,
            "temperature": temperature,
            "system": system_message['content'] if system_message else "",
            "messages": user_messages
        }
    
    def _parse_llm_response(self, response_text: str, 
                            original_prompt: str,
                            simple_mode: bool = False) -> Dict:
        """
        解析 LLM 响应
        
        Args:
            response_text: LLM 原始响应
            original_prompt: 原始提示词
            simple_mode: 是否为简化模式
            
        Returns:
            解析后的结果
        """
        # 提取 JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if not json_match:
            self._log("无法从响应中提取 JSON，使用回退方案", "WARNING")
            return self._fallback_analysis(original_prompt)
        
        try:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            # 验证必要字段
            if simple_mode:
                # 简化模式只需场景数量和建议
                if 'total_scenes' not in result:
                    result['total_scenes'] = result.get('scene_count', 1)
                if 'scenes' not in result:
                    result['scenes'] = []
            else:
                # 详细模式验证完整字段
                result = self._validate_detailed_result(result, original_prompt)
            
            return result
            
        except json.JSONDecodeError as e:
            self._log(f"JSON 解析失败：{e}", "ERROR")
            return self._fallback_analysis(original_prompt)
    
    def _validate_detailed_result(self, result: Dict, 
                                   original_prompt: str) -> Dict:
        """验证详细模式结果"""
        # 确保有场景列表
        if 'scenes' not in result:
            result['scenes'] = []
        
        # 确保场景数量匹配
        if 'total_scenes' not in result:
            result['total_scenes'] = len(result.get('scenes', []))
        
        # 补充缺失字段
        for i, scene in enumerate(result.get('scenes', [])):
            if 'index' not in scene:
                scene['index'] = i + 1
            if 'importance' not in scene:
                scene['importance'] = 0.5
            if 'confidence' not in scene:
                scene['confidence'] = 0.8
            if 'scene_type' not in scene:
                scene['scene_type'] = ['custom']
            if 'reason' not in scene:
                scene['reason'] = 'AI 分析判定'
        
        # 添加整体分析
        if 'overall_analysis' not in result:
            result['overall_analysis'] = f"AI 分析检测到 {result['total_scenes']} 个独立场景"
        
        return result
    
    def _fallback_analysis(self, prompt: str) -> Dict:
        """回退分析（基于规则）"""
        self._log("使用规则_based 回退分析", "INFO")
        
        # 简单的逗号分隔
        segments = [s.strip() for s in re.split(r'[,.,!]', prompt) if s.strip()]
        
        scenes = []
        for i, segment in enumerate(segments):
            scenes.append({
                'index': i + 1,
                'text': segment,
                'importance': 0.5,
                'scene_type': ['custom'],
                'reason': '规则分析（AI 不可用）'
            })
        
        return {
            'total_scenes': len(scenes),
            'scenes': scenes,
            'overall_analysis': f'规则分析检测到 {len(scenes)} 个片段',
            'source': 'fallback'
        }
    
    def interactive_refine(self, prompt: str, 
                           initial_result: Dict = None) -> Dict:
        """
        交互式场景优化（多轮对话）
        
        Args:
            prompt: 原始提示词
            initial_result: 初始分析结果（可选）
            
        Returns:
            优化后的分析结果
        """
        self._log("开始交互式场景优化...", "INFO")
        
        # 第一轮：分析
        if not initial_result:
            result = self.analyze(prompt, mode='detailed')
        else:
            result = initial_result
        
        # 第二轮：优化建议
        refinement_prompt = f"""基于以下分析结果，请给出优化建议：

原始提示词：{prompt}

当前分析：
- 场景数量：{result.get('total_scenes', 0)}
- 场景列表：{json.dumps(result.get('scenes', []), ensure_ascii=False)}

请回答：
1. 场景拆分是否合理？
2. 是否有需要合并的场景？
3. 是否有需要拆分的场景？
4. 每个场景的重要度评估是否准确？
5. 其他优化建议

用 JSON 格式输出。"""

        messages = [
            {"role": "system", "content": "你是一位专业的视频场景优化顾问。请给出具体、可执行的优化建议。"},
            {"role": "user", "content": refinement_prompt}
        ]
        
        try:
            response = self._call_llm(messages, temperature=0.5)
            
            # 提取建议
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group(0))
                result['refinement_suggestions'] = suggestions
                self._log(f"获得 {len(suggestions)} 条优化建议", "INFO")
        except Exception as e:
            self._log(f"优化建议获取失败：{e}", "WARNING")
            result['refinement_suggestions'] = {}
        
        return result
    
    def batch_analyze(self, prompts: List[str], 
                      mode: str = 'simple') -> List[Dict]:
        """
        批量分析多个提示词
        
        Args:
            prompts: 提示词列表
            mode: 分析模式
            
        Returns:
            分析结果列表
        """
        results = []
        
        self._log(f"开始批量分析 {len(prompts)} 个提示词...", "INFO")
        
        for i, prompt in enumerate(prompts, 1):
            self._log(f"分析进度：{i}/{len(prompts)}", "INFO")
            result = self.analyze(prompt, mode)
            results.append(result)
        
        self._log(f"批量分析完成", "INFO")
        
        return results
    
    def export_analysis_report(self, output_path: str):
        """导出分析报告"""
        report = {
            'total_analyses': len(self.analysis_history),
            'analyses': self.analysis_history,
            'statistics': self._calculate_statistics(),
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self._log(f"导出分析报告：{output_path}", "INFO")
    
    def _calculate_statistics(self) -> Dict:
        """计算统计信息"""
        if not self.analysis_history:
            return {}
        
        total_scenes = sum(
            r.get('result', {}).get('total_scenes', 0) 
            for r in self.analysis_history
        )
        
        return {
            'total_analyses': len(self.analysis_history),
            'average_scenes_per_prompt': total_scenes / len(self.analysis_history),
            'model_used': self.model_name,
            'model_type': self.model_type
        }


# 便捷函数
def quick_analyze(prompt: str, model_type: str = 'local') -> Dict:
    """快速分析场景（便捷函数）"""
    analyzer = AISceneAnalyzer(model_type=model_type, verbose=False)
    return analyzer.analyze(prompt, mode='simple')


def detailed_analyze(prompt: str, model_type: str = 'local') -> Dict:
    """详细分析场景（便捷函数）"""
    analyzer = AISceneAnalyzer(model_type=model_type, verbose=True)
    return analyzer.analyze(prompt, mode='detailed')
