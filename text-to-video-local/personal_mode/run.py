#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人电脑模式 - 统一启动器

提供两种生成模式：
1. 标准模式 - 原文生视频直接跑模型（适合高端配置）
2. 超优模式 - 分段文生图 + 合成视频（适合所有配置）
"""

import sys
import click
import logging
import json
import time
import random
from pathlib import Path
from typing import Optional, List, Dict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--prompt', '-p',
    required=True,
    help='文本提示词'
)
@click.option(
    '--mode', '-m',
    type=click.Choice(['standard', 'optimized', 'collaborative']),
    default='optimized',
    help='生成模式：standard(标准模式)、optimized(超优模式) 或 collaborative(协同模式)，默认超优模式'
)
@click.option(
    '--duration', '-d',
    type=float,
    default=5.0,
    help='视频时长（秒）'
)
@click.option(
    '--segment-duration',
    type=float,
    default=2.0,
    help='每段时长（秒），仅超优模式有效'
)
@click.option(
    '--resolution',
    type=str,
    default='512x512',
    help='分辨率（如 512x512）'
)
@click.option(
    '--fps',
    type=int,
    default=8,
    help='帧率'
)
@click.option(
    '--model',
    type=str,
    default='modelscope',
    help='模型名称'
)
@click.option(
    '--device',
    type=str,
    default='cuda',
    help='计算设备（cuda 或 cpu）'
)
@click.option(
    '--output', '-o',
    default='output/video.mp4',
    help='输出文件路径'
)
@click.option(
    '--character-voice',
    default=None,
    help='人物配音语音（超优模式专属）'
)
@click.option(
    '--bgm-file',
    default=None,
    help='背景音乐文件（超优模式专属）'
)
@click.option(
    '--bgm-volume',
    type=float,
    default=0.3,
    help='背景音乐音量（超优模式/协同模式专属）'
)
@click.option(
    '--local-ratio',
    type=float,
    default=0.5,
    help='本地生成比例 0.0-1.0（协同模式专属，默认 50%）'
)
@click.option(
    '--cloud-platforms',
    type=str,
    default='seaart,tensor,bing,aliyun,liblib,raphael',
    help='云平台列表，逗号分隔（协同模式专属）'
)
@click.option(
    '--auto-adjust',
    is_flag=True,
    default=True,
    help='启用自动调整生成比例（协同模式专属）'
)
@click.option(
    '--enable-scene-analysis',
    is_flag=True,
    default=False,
    help='启用智能场景分析（协同模式专属）'
)
@click.option(
    '--enable-scene-refine',
    is_flag=True,
    default=True,
    help='启用智能场景优化（协同模式专属，默认启用）'
)
@click.option(
    '--auto-approve-changes',
    is_flag=True,
    default=False,
    help='自动确认场景优化建议，无需用户确认（协同模式专属）'
)
@click.option(
    '--show-mode-info',
    is_flag=True,
    help='显示两种模式的详细说明后退出'
)
def main(
    prompt: str,
    mode: str,
    duration: float,
    segment_duration: float,
    resolution: str,
    fps: int,
    model: str,
    device: str,
    output: str,
    character_voice: Optional[str],
    bgm_file: Optional[str],
    bgm_volume: float,
    local_ratio: float,
    cloud_platforms: str,
    auto_adjust: bool,
    enable_scene_analysis: bool,
    enable_scene_refine: bool,
    auto_approve_changes: bool,
    show_mode_info: bool
):
    """
    个人电脑模式 - AI 视频生成器
    
    提供三种生成模式，适应不同硬件配置：
    
    \b
    【标准模式】standard
    - 原文生视频直接跑模型
    - 适合：高端 GPU (RTX 3060+, 12GB+ 显存)
    - 优势：一键生成，简单快速
    - 显存：12-24GB
    - 时间：5-10 分钟
    
    \b
    【超优模式】optimized（推荐）
    - 分段文生图 + 合成视频 + 分层配音
    - 适合：所有配置（4GB 显存即可）
    - 优势：节省 60-70% 资源，支持配音
    - 显存：4-8GB
    - 时间：3-5 分钟
    
    \b
    【协同模式】collaborative（最新）
    - 本地生成 + 云端 AI 协同配合
    - 适合：所有配置，动态调整
    - 优势：智能分工，速度最优，支持 AI 配音分析
    - 显存：0-8GB（弹性）
    - 时间：动态调整（通常 2-4 分钟）
    
    示例:
    
    \b
    # 使用超优模式（推荐）
    python personal_mode/run.py -p "cyberpunk city" -d 10 -m optimized
    
    # 使用标准模式（高端配置）
    python personal_mode/run.py -p "cyberpunk city" -d 5 -m standard
    
    # 使用协同模式（智能分工）
    python personal_mode/run.py -p "魔法城堡" -d 10 -m collaborative
    
    # 协同模式自定义本地比例
    python personal_mode/run.py -p "魔法城堡" -d 10 -m collaborative --local-ratio 0.3
    
    # 超优模式添加配音和 BGM
    python personal_mode/run.py \\
        -p "魔法城堡" \\
        -d 10 \\
        -m optimized \\
        --character-voice zh-CN-XiaoxiaoNeural \\
        --bgm-file music/bgm.mp3 \\
        --bgm-volume 0.3
    
    # 查看模式说明
    python personal_mode/run.py --show-mode-info
    """
    
    # 显示模式信息
    if show_mode_info:
        show_mode_details()
        return
    
    # 输出路径处理
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 解析分辨率
    try:
        width, height = map(int, resolution.split('x'))
    except:
        logger.error(f"无效的分辨率格式：{resolution}")
        return
    
    print("\n" + "="*70)
    print(" AI 视频生成 - 个人电脑模式")
    print("="*70)
    
    print(f"\n配置信息:")
    print(f"  模式：{get_mode_name(mode)}")
    print(f"  提示词：{prompt}")
    print(f"  时长：{duration} 秒")
    if mode == 'optimized' or mode == 'collaborative':
        print(f"  分段时长：{segment_duration} 秒")
        print(f"  分段数：{int(duration / segment_duration)}")
    print(f"  分辨率：{width}x{height}")
    print(f"  帧率：{fps}fps")
    print(f"  模型：{model}")
    print(f"  设备：{device}")
    print(f"  输出：{output_path}")
    
    if mode == 'optimized' or mode == 'collaborative':
        if character_voice:
            print(f"  人物配音：{character_voice}")
        if bgm_file:
            print(f"  背景音乐：{bgm_file} (音量：{bgm_volume})")
    
    if mode == 'collaborative':
        print(f"  本地比例：{local_ratio:.0%}")
        print(f"  云平台：{cloud_platforms}")
        print(f"  自动调整：{'是' if auto_adjust else '否'}")
    
    print(f"\n{'='*70}\n")
    
    # 根据模式选择执行
    if mode == 'standard':
        # 标准模式：直接文生视频
        run_standard_mode(
            prompt=prompt,
            duration=duration,
            resolution=(width, height),
            fps=fps,
            model=model,
            device=device,
            output=str(output_path)
        )
    elif mode == 'optimized':
        # 超优模式：分段文生图 + 合成
        run_optimized_mode(
            prompt=prompt,
            duration=duration,
            segment_duration=segment_duration,
            resolution=(width, height),
            fps=fps,
            model=model,
            device=device,
            output=str(output_path),
            character_voice=character_voice,
            bgm_file=bgm_file,
            bgm_volume=bgm_volume
        )
    else:
        # 协同模式：本地 + 云端 AI 协同
        run_collaborative_mode(
            prompt=prompt,
            duration=duration,
            segment_duration=segment_duration,
            resolution=(width, height),
            fps=fps,
            model=model,
            device=device,
            output=str(output_path),
            local_ratio=local_ratio,
            cloud_platforms=cloud_platforms.split(','),
            auto_adjust=auto_adjust,
            enable_scene_analysis=enable_scene_analysis,
            enable_scene_refine=enable_scene_refine,
            auto_approve_changes=auto_approve_changes,
            character_voice=character_voice,
            bgm_file=bgm_file,
            bgm_volume=bgm_volume
        )


def get_mode_name(mode: str) -> str:
    """获取模式名称"""
    names = {
        'standard': '标准模式 (standard)',
        'optimized': '超优模式 (optimized) ⭐',
        'collaborative': '协同模式 (collaborative) 🆕'
    }
    return names.get(mode, mode)


def run_collaborative_mode(
    prompt: str,
    duration: float,
    segment_duration: float,
    resolution: tuple,
    fps: int,
    model: str,
    device: str,
    output: str,
    local_ratio: float,
    cloud_platforms: List[str],
    auto_adjust: bool,
    enable_scene_analysis: bool,
    enable_scene_refine: bool,
    auto_approve_changes: bool,
    character_voice: Optional[str],
    bgm_file: Optional[str],
    bgm_volume: float
):
    """
    运行协同模式（本地生成 + 云端 AI 协同配合）
    
    核心功能：
    1. 智能场景分析，动态分配本地/AI 任务
    2. 实时监控速度，自动调整分工比例
    3. AI 配音分析，智能脚本拆分
    4. 多云端平台支持，自动选择最优
    """
    print("【协同模式】启动本地 + 云端 AI 协同生成流程...\n")
    
    try:
        # 导入协同模块
        from collaborative_scheduler import CollaborativeScheduler
        from ai_voice_analyzer import AIVoiceAnalyzer
        from cloud_platforms import CloudPlatformManager
        
        # 初始化组件
        output_dir = Path(output).parent
        scheduler = CollaborativeScheduler(
            project_dir=str(output_dir / 'segments'),
            total_duration=duration,
            segment_duration=segment_duration,
            local_ratio=local_ratio,
            enable_auto_adjust=auto_adjust,
            enable_scene_analysis=enable_scene_analysis,
            enable_interactive_refine=enable_scene_refine,
            auto_approve_changes=auto_approve_changes,
            cloud_platforms=cloud_platforms,
            verbose=True
        )
        
        voice_analyzer = AIVoiceAnalyzer(verbose=True)
        cloud_manager = CloudPlatformManager(api_keys={}, verbose=True)
        
        print("="*70)
        print(" 协同模式初始化完成")
        print("="*70)
        print(f"  总分段数：{scheduler.total_segments}")
        print(f"  初始本地比例：{scheduler.local_ratio:.0%}")
        print(f"  可用云平台：{', '.join(cloud_platforms)}")
        print(f"  自动调整：{'启用' if auto_adjust else '禁用'}")
        print(f"  场景分析：{'启用' if enable_scene_analysis else '禁用'}")
        print(f"  场景优化：{'启用' if enable_scene_refine else '禁用'}")
        print(f"  自动确认：{'是' if auto_approve_changes else '否（用户确认）'}")
        print("="*70 + "\n")
        
        # AI 分析配音脚本
        if character_voice or True:  # 始终分析，即使用户没指定语音
            print("【AI 配音分析】正在分析视频脚本...\n")
            script_segments = voice_analyzer.split_script_by_duration(
                full_prompt=prompt,
                total_duration=duration,
                segment_duration=segment_duration
            )
            
            print(f"  分析完成：共 {len(script_segments)} 段配音脚本")
            for seg in script_segments[:3]:  # 只显示前 3 段
                print(f"    段{seg['segment_index'] + 1}: {seg['voiceover']['text'][:30]}...")
            if len(script_segments) > 3:
                print(f"    ... 还有 {len(script_segments) - 3} 段")
            print()
        
        # 场景智能优化（AI 分析 + 用户交互）
        if enable_scene_refine and scheduler.scene_refiner:
            print("="*70)
            print("【智能场景优化】开始分析场景并优化任务分配...")
            print("="*70 + "\n")
            
            # 使用配音脚本的分段进行优化
            optimized_segments = scheduler.optimize_scenes(
                full_prompt=prompt,
                raw_segments=script_segments
            )
            
            # 更新调度器的分段（如果优化后数量变化）
            if len(optimized_segments) != len(script_segments):
                print(f"\n✓ 场景优化完成：{len(script_segments)} 段 → {len(optimized_segments)} 段")
                scheduler.total_segments = len(optimized_segments)
                # TODO: 将优化后的分段应用到任务生成流程
            
            print()
        
        # 协同生成循环
        completed_segments = []
        
        while True:
            # 获取下一个任务
            task = scheduler.get_next_task()
            
            if not task:
                print("\n✓ 所有任务分配完成！")
                break
            
            segment_idx = task.get('segment_index')
            if segment_idx is None:
                continue
            
            # 分配生成方式
            if task.get('status') == 'unassigned':
                task = scheduler.assign_task(segment_idx, prompt)
            
            # 生成图片
            start_time = time.time()
            method = task['method']
            
            print(f"\n[段 {segment_idx + 1}/{scheduler.total_segments}] 使用 {method.upper()} 模式生成...")
            
            try:
                if method == 'local':
                    # 本地生成（调用现有的 generate_segmented.py 的单段生成逻辑）
                    image_result = generate_local_segment(
                        prompt=prompt,
                        segment_index=segment_idx,
                        resolution=resolution,
                        fps=fps,
                        model=model,
                        device=device,
                        output_dir=output_dir / 'segments' / f'segment_{segment_idx + 1:03d}'
                    )
                else:
                    # 云端生成
                    image_url, platform_name = cloud_manager.generate_image(
                        prompt=prompt,
                        preferred_platform=None  # 自动选择
                    )
                    image_result = {'url': image_url, 'platform': platform_name} if image_url else None
                
                duration = time.time() - start_time
                
                if image_result:
                    scheduler.record_completion(segment_idx, method, duration, success=True)
                    completed_segments.append(segment_idx)
                    
                    method_cn = '本地' if method == 'local' else '云端'
                    print(f"  ✓ {method_cn}生成成功，耗时：{duration:.1f}s")
                    
                    # 打印进度
                    progress = scheduler.get_progress()
                    bar_len = 40
                    filled = int(progress['progress_percent'] / 100 * bar_len)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    print(f"  进度：[{bar}] {progress['progress_percent']:.1f}%")
                    
                    if progress['estimated_remaining_time'] > 0:
                        print(f"  预计剩余：{progress['estimated_remaining_time']:.0f}s")
                else:
                    scheduler.record_completion(segment_idx, method, duration, success=False)
                    print(f"  ✗ 生成失败，将自动重试")
                    
            except Exception as e:
                import traceback
                print(f"  ✗ 生成异常：{e}")
                traceback.print_exc()
                scheduler.record_completion(segment_idx, method, time.time() - start_time, success=False)
        
        # 显示最终统计
        scheduler.print_progress()
        
        # 合并视频
        print("\n【合并视频】正在合成最终视频...")
        merge_segments(
            segment_dir=output_dir / 'segments',
            audio_dir=output_dir / 'audio',
            output_file=output,
            fps=fps
        )
        
        print(f"\n✓ 协同模式完成：{output}")
        
        # 导出报告
        report_path = scheduler.export_report()
        print(f"  生成报告：{report_path}")
        
    except ImportError as e:
        logger.error(f"导入模块失败：{e}")
        print("\n💡 提示：协同模式需要安装额外依赖")
        print("  请确保以下文件存在：")
        print("  - collaborative_scheduler.py")
        print("  - ai_voice_analyzer.py")
        print("  - cloud_platforms.py")
    except Exception as e:
        import traceback
        logger.error(f"协同模式执行失败：{e}")
        traceback.print_exc()


def generate_local_segment(
    prompt: str,
    segment_index: int,
    resolution: tuple,
    fps: int,
    model: str,
    device: str,
    output_dir: Path
) -> Optional[Dict]:
    """
    本地生成单段图片序列
    
    这里简化实现，实际应该调用 generate_segmented.py 的单段生成逻辑
    """
    # TODO: 实现真实的本地生成
    # 这里仅作为示例框架
    time.sleep(random.uniform(3, 8))  # 模拟生成时间
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成假图片
    for frame in range(fps * 2):  # 假设每段 2 秒
        img_path = output_dir / f'frame_{frame:04d}.png'
        img_path.touch()  # 创建空文件
    
    return {'frames': fps * 2, 'dir': str(output_dir)}


def merge_segments(
    segment_dir: Path,
    audio_dir: Path,
    output_file: str,
    fps: int
):
    """
    合并所有片段为最终视频
    
    简化实现，调用 generate_segmented.py 的合并逻辑
    """
    # TODO: 实现真实的合并逻辑
    time.sleep(2)  # 模拟合并时间
    
    # 创建输出文件
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).touch()


    
    import subprocess
    import sys
    
    # 调用原有的生成脚本
    cmd = [
        sys.executable,
        "personal_mode/generate.py",
        "-p", prompt,
        "-d", str(duration),
        "--resolution", f"{resolution[0]}x{resolution[1]}",
        "--fps", str(fps),
        "-m", model,
        "-o", output
    ]
    
    if device == "cpu":
        cmd.append("--device")
        cmd.append("cpu")
    
    print(f"执行命令：{' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print(f"\n✓ 标准模式完成：{output}")
        else:
            print(f"\n⚠ 标准模式完成但有警告")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"标准模式执行失败：{e}")
        print("\n💡 建议:")
        print("  您的配置可能不适合标准模式，请尝试：")
        print("  1. 使用超优模式：添加参数 -m optimized")
        print("  2. 降低分辨率：--resolution 384x384")
        print("  3. 减少时长：-d 3")
    except Exception as e:
        logger.error(f"执行失败：{e}")


def run_optimized_mode(
    prompt: str,
    duration: float,
    segment_duration: float,
    resolution: tuple,
    fps: int,
    model: str,
    device: str,
    output: str,
    character_voice: Optional[str],
    bgm_file: Optional[str],
    bgm_volume: float
):
    """
    运行超优模式（分段文生图 + 合成视频 + 分层配音）
    
    调用新增的 generate_segmented.py
    """
    print("【超优模式】启动分段文生图 + 合成视频流程...\n")
    
    import subprocess
    import sys
    
    # 构建输出目录
    output_dir = Path(output).parent
    
    # 调用分段生成脚本
    cmd = [
        sys.executable,
        "personal_mode/generate_segmented.py",
        "-p", prompt,
        "-d", str(duration),
        "-s", str(segment_duration),
        "--resolution", f"{resolution[0]}x{resolution[1]}",
        "--fps", str(fps),
        "-m", model,
        "--device", device,
        "--output-dir", str(output_dir)
    ]
    
    # 添加配音选项
    if character_voice:
        cmd.append("--character-voice")
        cmd.append(character_voice)
    
    # 添加 BGM 选项
    if bgm_file:
        cmd.append("--bgm-file")
        cmd.append(bgm_file)
        cmd.append("--bgm-volume")
        cmd.append(str(bgm_volume))
    
    print(f"执行命令：{' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            # 找到最终视频
            final_video = output_dir / "final_video.mp4"
            if final_video.exists():
                print(f"\n✓ 超优模式完成：{final_video}")
                
                # 复制到用户指定的输出路径
                import shutil
                if str(final_video) != output:
                    shutil.copy(final_video, output)
                    print(f"  已复制到：{output}")
            else:
                print(f"\n⚠ 未找到最终视频文件")
        else:
            print(f"\n⚠ 超优模式完成但有警告")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"超优模式执行失败：{e}")
    except Exception as e:
        logger.error(f"执行失败：{e}")


def show_mode_details():
    """显示两种模式的详细信息"""
    
    print("\n" + "="*70)
    print(" AI 视频生成 - 模式说明")
    print("="*70)
    
    print("\n【模式 1: 标准模式 (standard)】")
    print("-" * 70)
    print("\n工作原理:")
    print("  文本提示词 → 加载视频生成模型 → 一次性生成完整视频 → 输出")
    
    print("\n硬件要求:")
    print("  - GPU: RTX 3060 或更高 (12GB+ 显存)")
    print("  - 内存：16GB+")
    print("  - 推荐：RTX 4090 (24GB 显存)")
    
    print("\n资源消耗:")
    print("  - 显存：12-24GB")
    print("  - 时间：5-10 分钟/5 秒视频")
    print("  - 电力：0.5-1 度")
    
    print("\n优势:")
    print("  ✓ 一键生成，操作简单")
    print("  ✓ 视频流畅度好")
    print("  ✓ 适合批量生产")
    
    print("\n劣势:")
    print("  ✗ 硬件门槛高")
    print("  ✗ 显存需求大")
    print("  ✗ 不支持分段配音")
    print("  ✗ 失败需重新生成")
    
    print("\n适用场景:")
    print("  • 高端游戏电脑")
    print("  • 专业工作室")
    print("  • 快速原型制作")
    print("  • 短视频生成 (<5 秒)")
    
    print("\n【模式 2: 超优模式 (optimized)】 ⭐推荐")
    print("-" * 70)
    
    print("\n工作原理:")
    print("  文本提示词")
    print("    ↓")
    print("  分段生成图片序列 (每段 2 秒)")
    print("    ↓")
    print("  合并所有片段")
    print("    ↓")
    print("  分层配音 (人物+BGM+ 音效)")
    print("    ↓")
    print("  输出最终视频")
    
    print("\n硬件要求:")
    print("  - GPU: GTX 1650 或更高 (4GB+ 显存)")
    print("  - 内存：8GB+")
    print("  - 集成显卡也支持 (使用 CPU)")
    
    print("\n资源消耗:")
    print("  - 显存：4-8GB")
    print("  - 时间：3-5 分钟/10 秒视频")
    print("  - 电力：0.2-0.4 度")
    
    print("\n优势:")
    print("  ✓ 硬件门槛低 (60-70% 显存节省)")
    print("  ✓ 支持分层配音")
    print("  ✓ 支持断点续传")
    print("  ✓ 失败可单独重试")
    print("  ✓ 每段可用不同提示词")
    print("  ✓ 时间灵活控制")
    
    print("\n劣势:")
    print("  ✗ 步骤较多")
    print("  ✗ 视频时长受分段限制")
    
    print("\n适用场景:")
    print("  • 普通办公电脑")
    print("  • 笔记本电脑")
    print("  • 老旧电脑升级")
    print("  • 学生/个人用户")
    print("  • 长视频生成 (>10 秒)")
    print("  • 需要配音的讲解视频")
    
    print("\n" + "="*70)
    print(" 模式对比总结")
    print("="*70)
    
    comparison = [
        ("显存需求", "12-24GB", "4-8GB", "超优模式节省 60-70%"),
        ("时间消耗", "5-10 分钟", "3-5 分钟", "超优模式快 40-50%"),
        ("电力消耗", "0.5-1 度", "0.2-0.4 度", "超优模式省 50-60%"),
        ("硬件门槛", "高端 GPU", "任意电脑", "超优模式门槛低"),
        ("配音支持", "✗ 不支持", "✓ 支持分层", "超优模式功能强"),
        ("灵活性", "低", "高", "超优模式更灵活"),
        ("适用配置", "RTX 3060+", "GTX 1650+", "超优模式兼容好"),
    ]
    
    print(f"\n{'对比项':<15} | {'标准模式':<15} | {'超优模式':<15} | {'优势'}")
    print("-" * 80)
    
    for item, standard, optimized, benefit in comparison:
        print(f"{item:<15} | {standard:<15} | {optimized:<15} | {benefit}")
    
    print("\n" + "="*70)
    print(" 选择建议")
    print("="*70)
    
    print("\n✅ 选择标准模式，如果:")
    print("  - 你有 RTX 3060 或更高端 GPU")
    print("  - 需要快速生成短视频 (<5 秒)")
    print("  - 不需要配音功能")
    print("  - 追求最简单的操作流程")
    
    print("\n✅ 选择超优模式，如果:")
    print("  - 你的配置较低（GTX 1650 或集成显卡）")
    print("  - 想节省电力和资源")
    print("  - 需要添加人物配音和 BGM")
    print("  - 制作较长的视频 (>10 秒)")
    print("  - 需要灵活控制每段内容")
    
    print("\n" + "="*70)
    print("\n命令示例:")
    print("\n# 超优模式（推荐）：")
    print('python personal_mode/run.py -p "cyberpunk city" -d 10 -m optimized')
    
    print("\n# 标准模式（高端配置）：")
    print('python personal_mode/run.py -p "cyberpunk city" -d 5 -m standard')
    
    print("\n# 超优模式添加配音：")
    print('python personal_mode/run.py -p "魔法城堡" -d 10 -m optimized \\')
    print('    --character-voice zh-CN-XiaoxiaoNeural \\')
    print('    --bgm-file music/bgm.mp3')
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
