"""
智能协同调度器 - 本地生成与云端 AI 协同配合

核心功能：
1. 实时分析场景复杂度，智能分配本地/AI 任务
2. 监控双方生成速度，动态调整分工比例
3. 支持多云端平台，自动选择最优
4. 断点续传和失败重试
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class CollaborativeScheduler:
    """智能协同调度器"""
    
    def __init__(
        self,
        project_dir: str,
        total_duration: float = 10.0,
        segment_duration: float = 1.0,
        local_ratio: float = 0.5,
        enable_auto_adjust: bool = True,
        cloud_platforms: List[str] = None,
        verbose: bool = True
    ):
        """
        初始化协同调度器
        
        Args:
            project_dir: 项目目录
            total_duration: 总时长（秒）
            segment_duration: 每段时长（秒）
            local_ratio: 本地生成比例（0.0-1.0，0.5=50% 本地）
            enable_auto_adjust: 启用自动调整
            cloud_platforms: 支持的云端平台列表
            verbose: 是否输出详细信息
        """
        self.project_dir = Path(project_dir)
        self.total_duration = total_duration
        self.segment_duration = segment_duration
        self.local_ratio = local_ratio
        self.enable_auto_adjust = enable_auto_adjust
        self.cloud_platforms = cloud_platforms or [
            'seaart', 'tensor', 'bing', 'aliyun', 'liblib', 'raphael'
        ]
        self.verbose = verbose
        
        # 计算总段数
        self.total_segments = int(total_duration / segment_duration)
        
        # 任务状态跟踪
        self.segments: Dict[int, Dict] = {}
        self.local_speed: List[float] = []  # 本地生成耗时列表（秒/段）
        self.cloud_speed: List[float] = []  # 云端生成耗时列表（秒/段）
        self.local_failures: int = 0
        self.cloud_failures: int = 0
        
        # 云平台优先级（根据速度动态调整）
        self.platform_priority: Dict[str, float] = {
            platform: 1.0 for platform in self.cloud_platforms
        }
        
        # 初始化项目目录
        self._init_project_dir()
    
    def _init_project_dir(self):
        """初始化项目目录结构"""
        dirs = [
            self.project_dir,
            self.project_dir / 'segments',
            self.project_dir / 'audio',
            self.project_dir / 'working',
            self.project_dir / 'checkpoint'
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # 加载断点信息
        self._load_checkpoint()
    
    def _log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def _load_checkpoint(self):
        """加载断点信息"""
        checkpoint_file = self.project_dir / 'checkpoint' / 'scheduler.json'
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.segments = {int(k): v for k, v in data.get('segments', {}).items()}
                    self.local_speed = data.get('local_speed', [])
                    self.cloud_speed = data.get('cloud_speed', [])
                    self.local_ratio = data.get('local_ratio', 0.5)
                    self._log("已加载断点信息，从中断处继续", "INFO")
            except Exception as e:
                self._log(f"加载断点失败：{e}", "WARNING")
    
    def _save_checkpoint(self):
        """保存断点信息"""
        checkpoint_file = self.project_dir / 'checkpoint' / 'scheduler.json'
        data = {
            'segments': self.segments,
            'local_speed': self.local_speed,
            'cloud_speed': self.cloud_speed,
            'local_ratio': self.local_ratio,
            'timestamp': datetime.now().isoformat()
        }
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存断点失败：{e}", "WARNING")
    
    def analyze_scene_complexity(self, prompt: str, segment_index: int) -> Dict:
        """
        分析场景复杂度，决定使用本地还是云端生成
        
        复杂度评分维度：
        1. 提示词长度和细节程度
        2. 动态元素数量（人物、动物、车辆等）
        3. 场景变化（天气、光线、时间）
        4. 艺术风格复杂度
        
        Args:
            prompt: 提示词
            segment_index: 段索引
            
        Returns:
            复杂度分析报告
        """
        # 复杂度关键词
        complex_keywords = [
            # 动态元素
            'running', 'jumping', 'flying', 'dancing', 'fighting',
            '奔跑', '跳跃', '飞舞', '舞蹈', '战斗',
            # 复杂场景
            'crowd', 'battle', 'explosion', 'storm', 'waterfall',
            '人群', '战斗', '爆炸', '风暴', '瀑布',
            # 精细细节
            'detailed', 'intricate', 'complex', 'elaborate',
            '精细', '复杂', ' intricate', '华丽'
        ]
        
        simple_keywords = [
            # 静态场景
            'standing', 'sitting', 'landscape', 'building', 'sky',
            '站立', '坐着', '风景', '建筑', '天空',
            # 简单描述
            'simple', 'plain', 'minimal', 'clean',
            '简单', '纯净', '极简', '干净'
        ]
        
        # 计算复杂度分数
        complexity_score = 0.5  # 基础分数
        
        # 提示词长度评分
        prompt_length = len(prompt)
        if prompt_length > 200:
            complexity_score += 0.2
        elif prompt_length > 100:
            complexity_score += 0.1
        elif prompt_length < 50:
            complexity_score -= 0.1
        
        # 关键词评分
        prompt_lower = prompt.lower()
        complex_count = sum(1 for kw in complex_keywords if kw.lower() in prompt_lower)
        simple_count = sum(1 for kw in simple_keywords if kw.lower() in prompt_lower)
        
        complexity_score += (complex_count - simple_count) * 0.05
        
        # 段位置评分（中间段通常更复杂）
        middle_segment = self.total_segments // 2
        distance_from_middle = abs(segment_index - middle_segment)
        position_bonus = (middle_segment - distance_from_middle) * 0.02
        complexity_score += position_bonus
        
        # 限制分数范围
        complexity_score = max(0.0, min(1.0, complexity_score))
        
        # 决定生成方式
        if complexity_score > 0.7:
            method = 'cloud'
            reason = '复杂场景，需要 AI 精细生成'
        elif complexity_score < 0.3:
            method = 'local'
            reason = '简单场景，本地快速生成'
        else:
            # 中等复杂度，根据当前负载决定
            if len(self.local_speed) > 0 and len(self.cloud_speed) > 0:
                local_avg = sum(self.local_speed[-5:]) / len(self.local_speed[-5:])
                cloud_avg = sum(self.cloud_speed[-5:]) / len(self.cloud_speed[-5:])
                method = 'local' if local_avg < cloud_avg else 'cloud'
                reason = f'根据速度动态分配（本地：{local_avg:.1f}s, 云端：{cloud_avg:.1f}s）'
            else:
                method = 'local' if random.random() < self.local_ratio else 'cloud'
                reason = '初始分配（无历史数据）'
        
        return {
            'segment_index': segment_index,
            'prompt': prompt,
            'complexity_score': complexity_score,
            'recommended_method': method,
            'reason': reason,
            'local_keywords': simple_count,
            'complex_keywords': complex_count
        }
    
    def assign_task(self, segment_index: int, prompt: str) -> Dict:
        """
        为指定段分配生成任务
        
        Args:
            segment_index: 段索引（从 0 开始）
            prompt: 该段提示词
            
        Returns:
            任务分配信息
        """
        # 检查是否已完成
        if segment_index in self.segments:
            status = self.segments[segment_index].get('status')
            if status == 'completed':
                self._log(f"段 {segment_index + 1} 已完成，跳过", "INFO")
                return self.segments[segment_index]
        
        # 分析场景复杂度
        analysis = self.analyze_scene_complexity(prompt, segment_index)
        
        # 创建任务记录
        task = {
            'segment_index': segment_index,
            'prompt': prompt,
            'status': 'pending',
            'method': analysis['recommended_method'],
            'complexity_score': analysis['complexity_score'],
            'assigned_time': datetime.now().isoformat(),
            'start_time': None,
            'end_time': None,
            'duration': None,
            'retry_count': 0,
            'error': None
        }
        
        self.segments[segment_index] = task
        self._save_checkpoint()
        
        self._log(
            f"段 {segment_index + 1}/{self.total_segments} -> "
            f"{analysis['recommended_method'].upper()} ({analysis['reason']})",
            "INFO"
        )
        
        return task
    
    def record_completion(self, segment_index: int, method: str, duration: float, success: bool = True):
        """
        记录任务完成
        
        Args:
            segment_index: 段索引
            method: 生成方法 ('local' 或 'cloud')
            duration: 耗时（秒）
            success: 是否成功
        """
        if segment_index not in self.segments:
            self._log(f"段 {segment_index} 未找到任务记录", "ERROR")
            return
        
        task = self.segments[segment_index]
        task['status'] = 'completed' if success else 'failed'
        task['end_time'] = datetime.now().isoformat()
        task['duration'] = duration
        task['method'] = method
        
        if success:
            # 记录速度
            if method == 'local':
                self.local_speed.append(duration)
                # 保留最近 10 次记录
                if len(self.local_speed) > 10:
                    self.local_speed = self.local_speed[-10:]
            else:
                self.cloud_speed.append(duration)
                if len(self.cloud_speed) > 10:
                    self.cloud_speed = self.cloud_speed[-10:]
        else:
            # 记录失败
            if method == 'local':
                self.local_failures += 1
            else:
                self.cloud_failures += 1
        
        self._save_checkpoint()
        
        # 自动调整比例
        if self.enable_auto_adjust and success:
            self._auto_adjust_ratio()
    
    def _auto_adjust_ratio(self):
        """自动调整本地/云端比例"""
        if len(self.local_speed) < 2 or len(self.cloud_speed) < 2:
            return  # 数据不足，不调整
        
        # 计算平均速度
        local_avg = sum(self.local_speed[-5:]) / min(5, len(self.local_speed))
        cloud_avg = sum(self.cloud_speed[-5:]) / min(5, len(self.cloud_speed))
        
        # 计算速度比
        if cloud_avg > 0:
            speed_ratio = local_avg / cloud_avg
        else:
            speed_ratio = 1.0
        
        # 调整策略
        old_ratio = self.local_ratio
        
        if speed_ratio < 0.7:
            # 本地更快，增加本地比例
            self.local_ratio = min(0.9, self.local_ratio + 0.1)
            reason = f"本地速度快 {speed_ratio:.2f}x，增加本地任务"
        elif speed_ratio > 1.3:
            # 云端更快，增加云端比例
            self.local_ratio = max(0.1, self.local_ratio - 0.1)
            reason = f"云端速度快 {1/speed_ratio:.2f}x，增加云端任务"
        else:
            # 速度接近，保持当前比例
            reason = "速度相当，保持当前比例"
        
        if abs(old_ratio - self.local_ratio) > 0.05:
            self._log(
                f"动态调整：本地比例 {old_ratio:.0%} -> {self.local_ratio:.0%} ({reason})",
                "INFO"
            )
            self._save_checkpoint()
    
    def get_next_task(self) -> Optional[Dict]:
        """
        获取下一个待处理任务
        
        Returns:
            任务信息，如果没有待处理任务则返回 None
        """
        for i in range(self.total_segments):
            if i not in self.segments:
                # 未分配的任务
                return {'segment_index': i, 'status': 'unassigned'}
            
            task = self.segments[i]
            if task['status'] == 'pending':
                return task
            elif task['status'] == 'failed' and task['retry_count'] < 3:
                # 失败但未超过重试次数
                task['retry_count'] += 1
                task['status'] = 'pending'
                task['error'] = None
                self._log(f"段 {i + 1} 重试 ({task['retry_count']}/3)", "INFO")
                return task
        
        return None
    
    def get_progress(self) -> Dict:
        """
        获取当前进度
        
        Returns:
            进度信息字典
        """
        total = self.total_segments
        completed = sum(1 for t in self.segments.values() if t['status'] == 'completed')
        failed = sum(1 for t in self.segments.values() if t['status'] == 'failed')
        pending = total - completed - failed
        
        # 计算平均速度
        local_avg = sum(self.local_speed[-5:]) / min(5, len(self.local_speed)) if self.local_speed else 0
        cloud_avg = sum(self.cloud_speed[-5:]) / min(5, len(self.cloud_speed)) if self.cloud_speed else 0
        
        # 预估剩余时间
        if local_avg > 0 or cloud_avg > 0:
            avg_speed = (local_avg * self.local_ratio + cloud_avg * (1 - self.local_ratio))
            remaining_time = pending * avg_speed
        else:
            remaining_time = 0
        
        return {
            'total_segments': total,
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'progress_percent': completed / total * 100 if total > 0 else 0,
            'local_ratio': self.local_ratio,
            'local_avg_speed': local_avg,
            'cloud_avg_speed': cloud_avg,
            'estimated_remaining_time': remaining_time,
            'local_failures': self.local_failures,
            'cloud_failures': self.cloud_failures
        }
    
    def print_progress(self):
        """打印进度信息"""
        progress = self.get_progress()
        
        print("\n" + "=" * 60)
        print(f"📊 协同生成进度：{progress['progress_percent']:.1f}%")
        print("=" * 60)
        print(f"总段数：{progress['total_segments']}")
        print(f"已完成：{progress['completed']} ✅")
        print(f"失败：{progress['failed']} ❌")
        print(f"待处理：{progress['pending']} ⏳")
        print(f"本地比例：{progress['local_ratio']:.0%}")
        print(f"本地速度：{progress['local_avg_speed']:.1f}秒/段")
        print(f"云端速度：{progress['cloud_avg_speed']:.1f}秒/段")
        print(f"预计剩余：{progress['estimated_remaining_time']:.0f}秒")
        print("=" * 60 + "\n")
    
    def export_report(self) -> str:
        """
        导出协同生成报告
        
        Returns:
            报告文件路径
        """
        report_file = self.project_dir / 'collaborative_report.json'
        
        report = {
            'project_dir': str(self.project_dir),
            'total_duration': self.total_duration,
            'segment_duration': self.segment_duration,
            'total_segments': self.total_segments,
            'generation_config': {
                'initial_local_ratio': 0.5,
                'final_local_ratio': self.local_ratio,
                'auto_adjust_enabled': self.enable_auto_adjust,
                'cloud_platforms': self.cloud_platforms
            },
            'performance': {
                'total_completed': sum(1 for t in self.segments.values() if t['status'] == 'completed'),
                'local_segments': len([t for t in self.segments.values() if t.get('method') == 'local']),
                'cloud_segments': len([t for t in self.segments.values() if t.get('method') == 'cloud']),
                'local_avg_speed': sum(self.local_speed) / len(self.local_speed) if self.local_speed else 0,
                'cloud_avg_speed': sum(self.cloud_speed) / len(self.cloud_speed) if self.cloud_speed else 0,
                'local_failures': self.local_failures,
                'cloud_failures': self.cloud_failures
            },
            'segments': self.segments,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self._log(f"生成报告：{report_file}", "INFO")
        return str(report_file)


if __name__ == '__main__':
    # 测试示例
    scheduler = CollaborativeScheduler(
        project_dir='./test_collaborative',
        total_duration=10.0,
        segment_duration=1.0,
        local_ratio=0.5,
        enable_auto_adjust=True
    )
    
    # 模拟任务分配
    test_prompts = [
        "简单的蓝天背景",
        "一只猫在草地上奔跑，细节丰富",
        "赛博朋克城市，霓虹灯闪烁，复杂场景",
        "宁静的湖面，倒映着远山",
        "激烈的战斗场景，爆炸和火焰",
    ]
    
    for i, prompt in enumerate(test_prompts):
        task = scheduler.assign_task(i, prompt)
        print(f"\n段 {i + 1}: {task['method']} - {task['complexity_score']:.2f}")
        print(f"原因：{scheduler.segments[i]['reason']}")
    
    # 查看进度
    scheduler.print_progress()
