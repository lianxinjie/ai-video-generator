"""
云端 AI 平台接口层

支持平台：
- SeaArt.ai
- Tensor.art
- Bing Image Creator
- 通义万相 (Aliyun)
- LiblibAI
- Raphael AI
- MGTV AIGC (芒果TV - 图片生成/视频生成)

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
import hmac as _hmac
import uuid as _uuid
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


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


def _load_ai_config(usage: str = None) -> Optional[Dict]:
    """从 config.json 加载指定用途的 AI 配置。"""
    config_path = Path(__file__).parent.parent / 'config.json'
    if not config_path.exists():
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception:
        return None
    ai_configs = config.get('ai_configs', [])
    if not usage:
        return ai_configs[0] if ai_configs else None
    for cfg in ai_configs:
        if cfg.get('usage') == usage and cfg.get('enabled', True):
            return cfg
    for cfg in ai_configs:
        if cfg.get('usage') == usage:
            return cfg
    return None


def _mgtv_signature(method: str, path: str, timestamp: str, nonce: str,
                    params: dict, secret: str) -> str:
    """生成芒果TV AIGC HMAC-SHA256 签名。"""
    sorted_keys = sorted(params.keys())
    query_parts = [f"{k}={params[k]}" for k in sorted_keys]
    sorted_query = "&".join(query_parts)
    string_to_sign = f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{sorted_query}"
    return _hmac.new(
        key=secret.encode("utf-8"),
        msg=string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()


def _mgtv_build_headers(method: str, url: str, access_key: str, secret_key: str,
                         query_params: dict = None) -> Dict[str, str]:
    """生成芒果TV AIGC 请求头。"""
    parsed = urlparse(url)
    timestamp = str(int(time.time()))
    nonce = _uuid.uuid4().hex[:16]
    signature = _mgtv_signature(method, parsed.path, timestamp, nonce,
                                query_params or {}, secret_key)
    return {
        "Content-Type": "application/json",
        "X-Access-Key": access_key,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
    }


def _poll_async_task(task_id: str, query_url: str, access_key: str, secret_key: str,
                     status_key: str = "status",
                     success_values: Tuple = ("SUCCESS", "success", "FINISHED", 2, "2"),
                     result_key: str = "result",
                     timeout_seconds: int = 300,
                     poll_interval: float = 5.0,
                     log_fn=None,
                     use_path_param: bool = False) -> Optional[Dict]:
    """轮询异步任务，返回成功后的 result 字段。

    use_path_param=True 时将 taskId 拼接到 URL 路径中（MGTV /detail/{id} 模式），
    否则作为 query 参数发送。
    """
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            if use_path_param:
                final_url = f"{query_url.rstrip('/')}/{task_id}"
                headers = _mgtv_build_headers("GET", final_url, access_key, secret_key)
                params = None
            else:
                final_url = query_url
                params = {"taskId": task_id}
                headers = _mgtv_build_headers("GET", final_url, access_key, secret_key, params)
            resp = requests.get(final_url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                if log_fn:
                    log_fn(f"轮询失败：HTTP {resp.status_code}", "WARNING")
                time.sleep(poll_interval)
                continue
            body = resp.json()
            if body.get("code") not in (200, None):
                if log_fn:
                    log_fn(f"轮询接口返回业务错误：code={body.get('code')}, msg={body.get('msg')}", "WARNING")
                # 某些任务刚提交时 detail 接口可能尚未就绪，继续等待
                time.sleep(poll_interval)
                continue
            data = body.get("data", body)
            status_val = data.get(status_key)
            if log_fn:
                log_fn(f"任务状态：{status_val}", "DEBUG")
            if status_val in success_values:
                return data.get(result_key, data)
            if str(status_val).upper() in ("FAILED", "ERROR", "TIMEOUT"):
                if log_fn:
                    log_fn(f"任务失败：{json.dumps(data, ensure_ascii=False)[:300]}", "ERROR")
                return None
        except Exception as e:
            if log_fn:
                log_fn(f"轮询异常：{e}", "WARNING")
        time.sleep(poll_interval)
    if log_fn:
        log_fn("轮询超时", "ERROR")
    return None


class MGTVImagePlatform(CloudPlatformBase):
    """
    芒果TV AIGC 图片生成平台

    文档：https://aigc.mgtv.com/develop/docs#quick-start
    图片生成接口：POST /api/v1/storyboard/generateByPromptv2
    图片详情接口：GET  /api/v1/storyboard/detail/{imgId}
    认证：HMAC-SHA256（X-Access-Key / X-Timestamp / X-Nonce / X-Signature）
    """

    CONFIG_USAGE = 'image_generation'

    def __init__(self, access_key: str = None, secret_key: str = None,
                 api_base: str = None, model_name: str = None,
                 verbose: bool = True, **kwargs):
        super().__init__(api_key=access_key, verbose=verbose)
        self.daily_limit = 500
        self.access_key = access_key or ""
        self.secret_key = secret_key or ""
        self.api_base = (api_base or "https://aigc.mgtv.com").rstrip("/")
        self.image_endpoint = f"{self.api_base}/api/v1/storyboard/generateByPromptv2"
        self.video_endpoint = f"{self.api_base}/api/v1/aivideo/generateByPromptv2"
        self.poll_endpoint = f"{self.api_base}/api/v1/storyboard/detail"
        self.video_poll_endpoint = f"{self.api_base}/api/v1/aivideo/detail"
        self.image_styles_endpoint = f"{self.api_base}/api/v1/aitools/image/styles"
        self.video_models_endpoint = f"{self.api_base}/api/v1/aitools/videoModelList"
        self.image_detail_by_ids_endpoint = f"{self.api_base}/api/v1/storyboard/detailByIds"
        self.model_name = model_name or "mgtv-image"
        self.poll_interval = kwargs.get("poll_interval", 5.0)
        self.poll_timeout = kwargs.get("poll_timeout", 300)

        cfg = _load_ai_config(self.CONFIG_USAGE)
        if cfg:
            self.access_key = self.access_key or cfg.get("access_key", "")
            self.secret_key = self.secret_key or cfg.get("secret_key", "")
            base = cfg.get("api_base", "")
            if base:
                self.api_base = base.rstrip("/")
                self.image_endpoint = f"{self.api_base}/api/v1/storyboard/generateByPromptv2"
                self.video_endpoint = f"{self.api_base}/api/v1/aivideo/generateByPromptv2"
                self.poll_endpoint = f"{self.api_base}/api/v1/storyboard/detail"
                self.video_poll_endpoint = f"{self.api_base}/api/v1/aivideo/detail"
                self.image_styles_endpoint = f"{self.api_base}/api/v1/aitools/image/styles"
                self.video_models_endpoint = f"{self.api_base}/api/v1/aitools/videoModelList"
                self.image_detail_by_ids_endpoint = f"{self.api_base}/api/v1/storyboard/detailByIds"

    @property
    def platform_name(self) -> str:
        return "MGTV"

    def is_available(self) -> bool:
        self._check_daily_reset()
        return self.remaining_quota > 0 and bool(self.access_key and self.secret_key)

    def _sign_headers(self, method: str, url: str, query_params: dict = None) -> Dict[str, str]:
        return _mgtv_build_headers(method, url, self.access_key, self.secret_key, query_params)

    def _submit_image_task(self, prompt: str, **kwargs) -> Optional[str]:
        body = {
            "imgUrls": kwargs.get("img_urls", []),
            "styleId": kwargs.get("style_id", 35),
            "resolution": kwargs.get("resolution", "2K"),
            "ratio": kwargs.get("ratio", "3:4"),
            "nums": kwargs.get("nums", 1),
            "prompt": {
                "args": kwargs.get("prompt_args", []),
                "prompt": prompt,
            },
        }
        headers = self._sign_headers("POST", self.image_endpoint)
        resp = requests.post(self.image_endpoint, json=body, headers=headers, timeout=60)
        if resp.status_code != 200:
            self._log(f"提交图片任务失败：HTTP {resp.status_code} - {resp.text[:200]}", "ERROR")
            return None
        data = resp.json()
        if data.get("code") not in (200, None):
            self._log(f"提交图片任务被拒绝：code={data.get('code')}, msg={data.get('msg')}", "ERROR")
            return None
        inner = data.get("data") or {}
        raw_status = inner.get("status")
        status = raw_status if isinstance(raw_status, dict) else {}
        task_id = (
            inner.get("taskId")
            or inner.get("imgId")
            or status.get("taskId")
            or inner.get("aseetRecordId")
            or inner.get("aigcSessionId")
            or data.get("taskId")
        )
        if not task_id or task_id == 0:
            self._log(f"响应中无有效 taskId：{json.dumps(data, ensure_ascii=False)[:400]}", "ERROR")
            return None
        fail_reason = status.get("failReason", "") if isinstance(raw_status, dict) else ""
        status_str = status.get("status") if isinstance(raw_status, dict) else raw_status
        self._log(
            f"提交图片任务成功，taskId={task_id}，status={status_str}，fail={fail_reason}",
            "INFO",
        )
        return str(task_id)

    def _poll_image_result(self, task_id: str) -> Optional[List[str]]:
        result = _poll_async_task(
            task_id=task_id,
            query_url=self.poll_endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            success_values=("FINISHED", "SUCCESS", "success", 2, "2"),
            result_key="imgUrls",
            timeout_seconds=self.poll_timeout,
            poll_interval=self.poll_interval,
            log_fn=self._log,
            use_path_param=True,
        )
        if result is None:
            return None
        if isinstance(result, list):
            return [u for u in result if u] if result else None
        url = result.get("imgUrl") or result.get("url")
        return [url] if url else None

    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        生成图片。

        kwargs: style_id, resolution, ratio, nums, img_urls, prompt_args,
                poll_interval, poll_timeout, return_list
        """
        if not self.is_available():
            self._log("平台不可用（缺 AK/SK 或额度耗尽）", "ERROR")
            return None

        self._log(f"生成图片：{prompt[:60]}...", "INFO")
        task_id = self._submit_image_task(prompt, **kwargs)
        if not task_id:
            return None

        urls = self._poll_image_result(task_id)
        if not urls:
            self._log("未获取到图片 URL", "ERROR")
            return None

        self.used_today += int(kwargs.get("nums", 1))
        self._log(f"图片生成成功，共 {len(urls)} 张", "INFO")
        if kwargs.get("return_list"):
            return urls
        return urls[0] if len(urls) == 1 else urls

    def parse_response(self, response: dict) -> Optional[str]:
        try:
            data = response.get("data", response)
            urls = data.get("imgUrls") or []
            return urls[0] if urls else None
        except Exception as e:
            self._log(f"解析响应失败：{e}", "ERROR")
            return None

    def generate_video(self, prompt: str, **kwargs) -> Optional[str]:
        """
        调用芒果TV 视频生成接口。

        文档：https://aigc.mgtv.com/develop/docs#quick-start
        接口：POST /api/v1/aivideo/generateByPromptv2
        详情：GET  /api/v1/aivideo/detail/{taskId}
        kwargs: model_id(默认28), ratio(默认16:9), resolution(默认720p),
                duration(默认5), nums(默认1), auto_bgm(默认False),
                img_urls(可选，图生视频输入), prompt_args
        """
        if not self.is_available():
            self._log("平台不可用", "ERROR")
            return None

        body = {
            "modelId": kwargs.get("model_id", 28),
            "type": kwargs.get("type", ""),
            "aspectRatio": kwargs.get("ratio", "16:9"),
            "resolution": kwargs.get("resolution", "720p"),
            "duration": kwargs.get("duration", 5),
            "nums": kwargs.get("nums", 1),
            "autoBgm": kwargs.get("auto_bgm", False),
            "prompt": {
                "prompt": prompt,
                "args": kwargs.get("prompt_args", []),
            },
        }
        if kwargs.get("img_urls"):
            body["imgUrls"] = kwargs["img_urls"]

        headers = self._sign_headers("POST", self.video_endpoint)
        self._log(f"生成视频：{prompt[:60]}...", "INFO")
        try:
            resp = requests.post(self.video_endpoint, json=body, headers=headers, timeout=60)
        except requests.RequestException as e:
            self._log(f"提交视频任务失败：{e}", "ERROR")
            return None

        if resp.status_code != 200:
            self._log(f"提交视频任务失败：HTTP {resp.status_code} - {resp.text[:200]}", "ERROR")
            return None

        data = resp.json()
        if data.get("code") not in (200, None):
            self._log(f"提交视频任务被拒绝：code={data.get('code')}, msg={data.get('msg')}", "ERROR")
            return None
        inner = data.get("data") or {}
        raw_status = inner.get("status")
        status = raw_status if isinstance(raw_status, dict) else {}
        task_id = (
            inner.get("taskId")
            or status.get("taskId")
            or inner.get("imgId")
            or inner.get("aseetRecordId")
            or inner.get("aigcSessionId")
            or data.get("taskId")
        )
        if not task_id or task_id == 0:
            self._log(f"响应中无 taskId：{json.dumps(data, ensure_ascii=False)[:400]}", "ERROR")
            return None

        self._log(f"视频任务已提交，taskId={task_id}，开始轮询...", "INFO")
        result = _poll_async_task(
            task_id=task_id,
            query_url=self.video_poll_endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            success_values=("FINISHED", "SUCCESS", "success", 2, "2"),
            result_key="videoUrl",
            timeout_seconds=kwargs.get("poll_timeout", 600),
            poll_interval=kwargs.get("poll_interval", 10.0),
            log_fn=self._log,
            use_path_param=True,
        )
        if not result:
            return None
        if isinstance(result, str):
            return result
        url = result.get("videoUrl") or result.get("url")
        return url


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

        mgtv_cfg = _load_ai_config('image_generation')
        if mgtv_cfg and mgtv_cfg.get('access_key') and mgtv_cfg.get('secret_key'):
            try:
                self.platforms['mgtv'] = MGTVImagePlatform(
                    access_key=mgtv_cfg.get('access_key', ''),
                    secret_key=mgtv_cfg.get('secret_key', ''),
                    api_base=mgtv_cfg.get('api_base', 'https://aigc.mgtv.com'),
                    verbose=self.verbose,
                )
                self.platform_stats['mgtv'] = {
                    'success_count': 0,
                    'fail_count': 0,
                    'avg_speed': 0.0,
                }
                self._log("初始化平台：mgtv", "INFO")
            except Exception as e:
                self._log(f"初始化平台 mgtv 失败：{e}", "ERROR")
    
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
