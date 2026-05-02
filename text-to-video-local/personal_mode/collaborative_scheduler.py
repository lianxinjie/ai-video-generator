"""
智能协同调度器 - 本地生成与云端 AI 协同配合

核心功能：
1. 实时分析场景复杂度，智能分配本地/AI 任务
2. 智能场景类型识别（集成混合模式功能）
3. 艺术风格识别和匹配
4. 监控双方生成速度，动态调整分工比例
5. 支持多云端平台，自动选择最优
6. 断点续传和失败重试
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# 集成混合模式的智能场景转换功能
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hybrid_mode.ai_analyzer import AIStyleAnalyzer
    SCENE_ANALYZER_AVAILABLE = True
except ImportError:
    SCENE_ANALYZER_AVAILABLE = False

# 集成智能场景整理器
try:
    from scene_refiner import SceneRefiner
    SCENE_REFINER_AVAILABLE = True
except ImportError:
    SCENE_REFINER_AVAILABLE = False

# 集成 AI 场景分析器
try:
    from ai_scene_analyzer import AISceneAnalyzer
    AI_SCENE_ANALYZER_AVAILABLE = True
except ImportError:
    AI_SCENE_ANALYZER_AVAILABLE = False


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
        enable_scene_analysis: bool = True,
        enable_interactive_refine: bool = True,
        enable_scene_detection: bool = True,
        enable_ai_assist: bool = True,  # 新增：启用 AI 辅助判断
        ai_model_type: str = 'local',  # AI 模型类型：'local', 'openai', 'qwen', 'claude'
        ai_model_name: str = None,
        ai_api_key: str = None,
        ai_api_base: str = None,
        auto_approve_changes: bool = False,
        verbose: bool = True
    ):
        """
        初始化协同调度器（支持 AI 辅助场景判断）
        
        Args:
            project_dir: 项目目录
            total_duration: 总时长（秒）
            segment_duration: 每段时长（秒）
            local_ratio: 本地生成比例（0.0-1.0，0.5=50% 本地）
            enable_auto_adjust: 启用自动调整
            cloud_platforms: 支持的云端平台列表
            enable_scene_analysis: 启用智能场景分析
            enable_interactive_refine: 启用交互式场景优化
            enable_scene_detection: 启用智能场景检测（基于关键词）
            enable_ai_assist: 启用 AI 辅助判断（基于 LLM）
            ai_model_type: AI 模型类型（'local', 'openai', 'qwen', 'claude'）
            ai_model_name: AI 模型名称
            ai_api_key: AI API Key
            ai_api_base: AI API Base URL
            auto_approve_changes: 自动确认优化建议
            verbose: 是否输出详细信息
        """
        初始化协同调度器
        
        Args:
            project_dir: 项目目录
            total_duration: 总时长（秒）
            segment_duration: 每段时长（秒）
            local_ratio: 本地生成比例（0.0-1.0，0.5=50% 本地）
            enable_auto_adjust: 启用自动调整
            cloud_platforms: 支持的云端平台列表
            enable_scene_analysis: 启用智能场景分析
            enable_interactive_refine: 启用交互式场景优化
            auto_approve_changes: 自动确认优化建议（无需用户确认）
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
        self.enable_scene_analysis = enable_scene_analysis
        self.enable_interactive_refine = enable_interactive_refine
        self.auto_approve_changes = auto_approve_changes
        
        # 初始化 AI 场景分析器（集成混合模式功能）
        self.scene_analyzer = None
        if enable_scene_analysis and SCENE_ANALYZER_AVAILABLE:
            try:
                self.scene_analyzer = AIStyleAnalyzer()
                self._log("已启用智能场景转换功能（混合模式 AI 分析器）", "INFO")
            except Exception as e:
                self._log(f"初始化场景分析器失败：{e}", "WARNING")
        elif enable_scene_analysis and not SCENE_ANALYZER_AVAILABLE:
            self._log("未找到混合模式 AI 分析器，使用简化场景分析", "WARNING")
        
        # 初始化场景整理器（智能优化）
        self.scene_refiner = None
        if enable_interactive_refine and SCENE_REFINER_AVAILABLE:
            try:
                self.scene_refiner = SceneRefiner(
                    verbose=verbose,
                    enable_scene_detection=enable_scene_detection
                )
                self._log("已启用智能场景整理器（AI+ 用户交互优化）", "INFO")
            except Exception as e:
                self._log(f"初始化场景整理器失败：{e}", "WARNING")
        elif enable_interactive_refine and not SCENE_REFINER_AVAILABLE:
            self._log("未找到场景整理器，使用基础场景分析", "WARNING")
        
        # 初始化 AI 场景分析器（智能辅助判断）
        self.ai_analyzer = None
        if enable_ai_assist and AI_SCENE_ANALYZER_AVAILABLE:
            try:
                self.ai_analyzer = AISceneAnalyzer(
                    model_type=ai_model_type,
                    model_name=ai_model_name,
                    api_key=ai_api_key,
                    api_base=ai_api_base,
                    timeout=ai_timeout,
                    max_retries=ai_max_retries,
                    enable_health_check=ai_health_check,
                    verbose=verbose
                )
                self._log(
                    f"已启用 AI 辅助场景判断（{ai_model_type}/{ai_model_name or 'default'}）", 
                    "INFO"
                )
                self._log(f"AI 超时：{ai_timeout}秒，重试：{ai_max_retries}次", "DEBUG")
            except Exception as e:
                self._log(f"初始化 AI 分析器失败：{e}", "WARNING")
        elif enable_ai_assist and not AI_SCENE_ANALYZER_AVAILABLE:
            self._log("未找到 AI 分析器，使用关键词方案", "WARNING")
        
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
        
        # 场景分析报告（优化后）
        self.scene_report: Optional[Dict] = None
    
    def ai_assisted_scene_analysis(self, full_prompt: str) -> List[Dict]:
        """
        AI 辅助场景分析（智能路由：关键词 vs AI）
        
        Args:
            full_prompt: 完整提示词
            
        Returns:
            场景分段列表
        """
        self._log("\n【智能场景分析】开始 AI 辅助分析...", "INFO")
        
        # 方案 1: AI 分析（如果可用）
        if self.ai_analyzer and self.scene_refiner and self.scene_refiner.scene_detector:
            self._log("使用混合方案：关键词预筛选 + AI 精确定界", "INFO")
            
            # Step 1: 关键词快速分析
            keyword_result = self.scene_refiner.scene_detector.detect_scene_keywords(full_prompt)
            overall_score = keyword_result.get('overall', {}).get('total_score', 0)
            detected_types = keyword_result.get('overall', {}).get('detected_types', 0)
            
            self._log(
                f"关键词分析：总体分数 {overall_score:.2f}, "
                f"检测到 {detected_types} 个场景类别", 
                "INFO"
            )
            
            # Step 2: 智能决策
            use_ai = False
            reason = ""
            
            if overall_score >= 0.7 and detected_types >= 2:
                # 高置信度，不需要 AI
                use_ai = False
                reason = "关键词分析置信度高"
            elif overall_score < 0.3:
                # 太低，AI 可能也帮不上
                use_ai = False
                reason = "场景特征不明显，使用基础拆分"
            elif self.ai_analyzer.requests_available:
                # 中等置信度，AI 辅助判断
                use_ai = True
                reason = "中等置信度，AI 辅助提升准确率"
            
            self._log(f"决策：{'使用 AI' if use_ai else '不使用 AI'} - {reason}", "INFO")
            
            if use_ai:
                # 调用 AI 分析
                try:
                    ai_result = self.ai_analyzer.analyze(full_prompt, mode='detailed')
                    
                    self._log(
                        f"AI 分析完成：{ai_result.get('total_scenes', 0)} 个场景", 
                        "INFO"
                    )
                    
                    # 转换为标准格式
                    segments = self._convert_ai_result_to_segments(ai_result, full_prompt)
                    
                    return segments
                    
                except Exception as e:
                    self._log(f"AI 分析失败：{e}，回退到关键词方案", "WARNING")
            
            # 回退到关键词方案
            return self.keyword_based_scene_detection(full_prompt)
        
        # 方案 2: 仅有场景整理器
        elif self.scene_refiner and self.scene_refiner.scene_detector:
            self._log("使用方案 2: 关键词智能检测", "INFO")
            return self.keyword_based_scene_detection(full_prompt)
        
        # 方案 3: 基础拆分
        else:
            self._log("使用方案 3: 基础规则拆分", "WARNING")
            return self._fallback_scene_split(full_prompt)
    
    def keyword_based_scene_detection(self, full_prompt: str) -> List[Dict]:
        """基于关键词的场景检测"""
        if not self.scene_refiner or not self.scene_refiner.scene_detector:
            return self._fallback_scene_split(full_prompt)
        
        return self.scene_refiner.scene_detector.analyze_and_split(full_prompt)
    
    def _convert_ai_result_to_segments(self, ai_result: Dict, 
                                        full_prompt: str) -> List[Dict]:
        """转换 AI 分析结果为标准分段格式"""
        segments = []
        
        scenes = ai_result.get('scenes', [])
        
        for scene in scenes:
            segments.append({
                'segment_index': len(segments),
                'text': scene.get('text', ''),
                'start_position': scene.get('start_position', 0),
                'end_position': scene.get('end_position', 0),
                'importance_score': scene.get('importance', 0.5),
                'detected_categories': scene.get('scene_type', ['custom']),
                'keywords': [],  # AI 模式下暂不提取关键词
                'transition_type': scene.get('transition_to_next', 'custom'),
                'reason': scene.get('reason', 'AI 分析判定'),
                'confidence': scene.get('confidence', 0.8),
                'suggested_duration': scene.get('suggested_duration'),
                'source': 'ai_analyzer'
            })
        
        return segments
    
    def _fallback_scene_split(self, full_prompt: str) -> List[Dict]:
        """回退方案：简单按标点拆分"""
        import re
        
        # 按标点符号拆分
        raw_segments = [s.strip() for s in re.split(r'[,.,]! ', full_prompt) if s.strip()]
        
        segments = []
        for i, text in enumerate(raw_segments):
            segments.append({
                'segment_index': i,
                'text': text,
                'importance_score': 0.5,
                'detected_categories': [],
                'source': 'fallback'
            })
        
        return segments
    
    def optimize_scenes(self, full_prompt: str, raw_segments: List[Dict]) -> List[Dict]:
        """
        优化场景分割和分配（包含智能场景检测）
        
        Args:
            full_prompt: 完整提示词
            raw_segments: 原始分段列表
            
        Returns:
            优化后的分段列表
        """
        if not self.scene_refiner:
            self._log("场景整理器未启用，跳过优化", "INFO")
            return raw_segments
        
        self._log("\n开始智能场景优化...", "INFO")
        
        # 1. 分析场景边界（传统方法）
        boundaries = self.scene_refiner.analyze_scene_boundaries(full_prompt)
        
        if boundaries:
            self._log(f"检测到 {len(boundaries)} 个场景边界", "INFO")
            for i, boundary in enumerate(boundaries[:5], 1):
                self._log(f"  边界{i}: {boundary['marker']} @ 位置{boundary['position']}", "INFO")
            if len(boundaries) > 5:
                self._log(f"  ... 还有 {len(boundaries) - 5} 个边界", "INFO")
        
        # 2. 智能场景检测（基于关键词分析，新增功能）
        if self.scene_refiner.enable_scene_detection and self.scene_refiner.scene_detector:
            self._log("\n【智能场景检测】开始分析关键词并判定新增场景...", "INFO")
            raw_segments = self.scene_refiner.detect_and_add_scenes(full_prompt, raw_segments)
        
        # 3. 交互式优化（AI 分析 + 用户确认）
        optimized_segments, scene_report = self.scene_refiner.interactive_refine(
            segments=raw_segments,
            auto_approve=self.auto_approve_changes
        )
        
        # 保存优化报告
        self.scene_report = scene_report
        
        # 显示优化结果
        if len(optimized_segments) != len(raw_segments):
            self._log(
                f"场景优化完成：{len(raw_segments)} 段 → {len(optimized_segments)} 段", 
                "INFO"
            )
        
        return optimized_segments
    
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
    
    def analyze_scene_complexity(self, prompt: str, segment_index: int, base_prompt: str = None) -> Dict:
        """
        分析场景复杂度，决定使用本地还是云端生成
        
        新增智能场景转换功能（集成混合模式 AI 分析器）：
        1. 5 种场景类型识别（time_lapse/zoom/pan/weather/iterative）
        2. 6 种艺术风格识别（cyberpunk/fantasy/scifi/natural/horror/custom）
        3. 镜头序列规划建议
        4. 转场效果推荐
        
        复杂度评分维度：
        1. 提示词长度和细节程度
        2. 动态元素数量（人物、动物、车辆等）
        3. 场景变化（天气、光线、时间）
        4. 艺术风格复杂度
        
        Args:
            prompt: 提示词
            segment_index: 段索引
            base_prompt: 基础提示词（用于整体场景分析）
            
        Returns:
            复杂度分析报告（包含场景类型、风格等）
        """
        
        # 使用智能场景分析器（如果可用）
        scene_analysis = None
        style_analysis = None
        
        if self.scene_analyzer and base_prompt:
            try:
                # 调用混合模式的 AI 分析器
                full_analysis = self.scene_analyzer.analyze_prompt(base_prompt)
                scene_analysis = full_analysis.get('scene_type', {})
                style_analysis = full_analysis.get('style', {})
                self._log(
                    f"智能场景分析：{scene_analysis.get('type', 'unknown')} + "
                    f"{style_analysis.get('style', 'unknown')}", 
                    "INFO"
                )
            except Exception as e:
                self._log(f"场景分析失败：{e}", "WARNING")
        
        # 原有的复杂度分析方法（向后兼容）
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
        
        # 如果有智能场景分析结果，调整复杂度评分
        if scene_analysis:
            scene_type = scene_analysis.get('type', 'custom')
            # 某些场景类型天生更复杂
            complex_scene_types = ['weather_change', 'iterative_img2img']
            if scene_type in complex_scene_types:
                complexity_score = min(1.0, complexity_score + 0.1)
        
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
        
        # 构建返回结果
        result = {
            'segment_index': segment_index,
            'prompt': prompt,
            'complexity_score': complexity_score,
            'recommended_method': method,
            'reason': reason,
            'local_keywords': simple_count,
            'complex_keywords': complex_count
        }
        
        # 如果有智能场景分析结果，添加到返回中
        if scene_analysis:
            result['scene_type'] = scene_analysis
            result['style'] = style_analysis
            result['analysis_source'] = 'ai_analyzer'  # 标记使用了 AI 分析器
            
            # 根据场景类型提供额外建议
            scene_type = scene_analysis.get('type', 'custom')
            if scene_type == 'time_lapse':
                result['suggestion'] = '时间流逝场景，建议保持建筑和构图一致，仅变化时间和光线'
            elif scene_type == 'zoom_sequence':
                result['suggestion'] = '视角推进场景，建议保持主体一致，逐步拉近镜头'
            elif scene_type == 'pan_sequence':
                result['suggestion'] = '空间移动场景，建议保持风格一致，变化场景位置'
            elif scene_type == 'iterative_img2img':
                result['suggestion'] = '迭代图生图场景，建议使用相同 seed 和重绘幅度 0.3-0.5'
        else:
            result['analysis_source'] = 'keyword_matching'  # 标记使用关键词匹配
        
        return result
    
    def assign_task(self, segment_index: int, prompt: str, base_prompt: str = None) -> Dict:
        """
        为指定段分配任务
        
        Args:
            segment_index: 段索引（从 0 开始）
            prompt: 该段提示词
            base_prompt: 基础提示词（用于智能场景分析，可选）
            
        Returns:
            任务分配信息
        """
        # 检查是否已完成
        if segment_index in self.segments:
            status = self.segments[segment_index].get('status')
            if status == 'completed':
                self._log(f"段 {segment_index + 1} 已完成，跳过", "INFO")
                return self.segments[segment_index]
        
        # 分析场景复杂度（使用智能场景分析）
        analysis = self.analyze_scene_complexity(prompt, segment_index, base_prompt)
        
        # 创建任务记录
        task = {
            'segment_index': segment_index,
            'prompt': prompt,
            'status': 'pending',
            'method': analysis['recommended_method'],
            'complexity_score': analysis['complexity_score'],
            'scene_type': analysis.get('scene_type', {}).get('type', 'unknown'),
            'style': analysis.get('style', {}).get('style', 'unknown'),
            'suggestion': analysis.get('suggestion', ''),
            'assigned_time': datetime.now().isoformat(),
            'start_time': None,
            'end_time': None,
            'duration': None,
            'retry_count': 0,
            'error': None
        }
        
        self.segments[segment_index] = task
        self._save_checkpoint()
        
        # 显示详细信息
        scene_info = f"{task['scene_type']} + {task['style']}" if task['scene_type'] != 'unknown' else ''
        self._log(
            f"段 {segment_index + 1}/{self.total_segments} -> "
            f"{analysis['recommended_method'].upper()} "
            f"({analysis['reason']})"
            + (f" [{scene_info}]" if scene_info else ""),
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
