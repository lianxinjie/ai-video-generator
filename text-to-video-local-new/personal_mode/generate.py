#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人电脑模式 - 视频分段生成命令行工具
"""

import sys
import click
import logging
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from personal_mode.task_manager import TaskScheduler
from generation import VideoGenerator


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """个人电脑模式 - 视频分段生成工具

    支持低显存 GPU(1-8GB) 的视频生成，通过分段生成 + 合并的方式，
    用时间换性能，支持断点续传和自动资源监控。
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    '--prompt', '-p',
    required=True,
    help='基础提示词'
)
@click.option(
    '--duration', '-d',
    type=float,
    default=5.0,
    help='总时长 (秒)'
)
@click.option(
    '--chunk-duration', '-c',
    type=float,
    default=0.5,
    help='每段时长 (秒)'
)
@click.option(
    '--output', '-o',
    default='final_video.mp4',
    help='输出文件名'
)
@click.option(
    '--project-dir',
    default='./projects/default',
    help='项目目录'
)
@click.option(
    '--gpu-threshold',
    type=float,
    default=75.0,
    help='GPU 显存阈值 (%)'
)
@click.option(
    '--resolution',
    type=str,
    default='512x512',
    help='分辨率 (如 512x512)'
)
@click.option(
    '--fps',
    type=int,
    default=8,
    help='帧率'
)
@click.option(
    '--model', '-m',
    type=click.Choice(['modelscope', 'animatediff', 'cogvideox']),
    default='modelscope',
    help='选择使用的模型'
)
@click.option(
    '--merge/--no-merge',
    default=True,
    help='是否合并视频'
)
@click.option(
    '--transition/--no-transition',
    default=False,
    help='合并时是否添加过渡效果'
)
@click.option(
    '--cleanup/--no-cleanup',
    default=False,
    help='合并后是否删除片段文件'
)
@click.option(
    '--ai-enhance/--no-ai-enhance',
    default=False,
    help='是否使用 AI 优化提示词'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='显示详细日志'
)
def generate(
    prompt: str,
    duration: float,
    chunk_duration: float,
    output: str,
    project_dir: str,
    gpu_threshold: float,
    resolution: str,
    fps: int,
    model: str,
    merge: bool,
    transition: bool,
    cleanup: bool,
    ai_enhance: bool,
    verbose: bool
):
    """生成视频（分段模式）

    示例:

    \b
    # 生成 5 秒视频，每段 0.5 秒
    python personal_mode/generate.py -p "蝴蝶在花丛中飞舞" -d 5 -c 0.5

    \b
    # 自定义分辨率和 GPU 阈值
    python personal_mode/generate.py -p "小猫奔跑" -d 3 --resolution 384x384 --gpu-threshold 70

    \b
    # 添加过渡效果并清理片段
    python personal_mode/generate.py -p "风景" -m animatediff --transition --cleanup
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 解析分辨率
    try:
        width, height = map(int, resolution.split('x'))
    except:
        logger.error(f"无效的分辨率格式：{resolution}")
        return
    
    # 创建项目目录
    project_path = Path(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print(" AI 视频生成 - 个人电脑模式")
    print("=" * 60)
    print(f"\n配置信息:")
    print(f"  提示词：{prompt}")
    print(f"  总时长：{duration} 秒")
    print(f"  分段时长：{chunk_duration} 秒")
    print(f"  分段数：{int(duration / chunk_duration)}")
    print(f"  分辨率：{width}x{height}")
    print(f"  帧率：{fps}fps")
    print(f"  模型：{model}")
    print(f"  GPU 阈值：{gpu_threshold}%")
    print(f"  项目目录：{project_path}")
    print(f"  AI 增强：{'是' if ai_enhance else '否'}")
    print(f"\n{'='*60}\n")
    
    # 初始化视频生成器
    print("正在加载模型...")
    generator = VideoGenerator(
        model_name=model,
        device='cuda'
    )
    
    try:
        generator.load_model()
    except Exception as e:
        logger.error(f"模型加载失败：{e}")
        return
    
    # 创建任务调度器
    scheduler = TaskScheduler(
        project_dir=project_path,
        pipeline=generator.pipeline,
        gpu_memory_threshold=gpu_threshold,
        chunk_duration=chunk_duration,
        resolution=(width, height),
        fps=fps
    )
    
    # 创建任务
    print("\n创建分段任务...")
    scheduler.create_tasks(
        total_duration=duration,
        base_prompt=prompt,
        use_ai_enhance=ai_enhance
    )
    
    # 执行任务
    print("\n开始生成视频片段...")
    print("(程序会自动监控资源，超过阈值时会暂停等待)\n")
    
    success = scheduler.run_all_tasks()
    
    if not success:
        logger.warning("部分任务失败，但继续合并...")
    
    # 合并视频
    if merge and success:
        print("\n合并视频片段...")
        output_path = scheduler.merge_results(
            output_name=output,
            add_transition=transition,
            cleanup=cleanup
        )
        
        if output_path:
            print(f"\n✓ 最终视频：{output_path}")
    else:
        logger.info("跳过合并步骤")
    
    # 打印最终状态
    status = scheduler.get_status()
    print("\n" + "=" * 60)
    print(" 最终状态")
    print("=" * 60)
    print(f" 完成率：{status['progress']['percentage']:.1f}%")
    print(f" 已完成：{status['progress']['completed']}/{status['progress']['total']}")
    print("=" * 60 + "\n")


@cli.command()
@click.option(
    '--project-dir',
    default='./projects/default',
    help='项目目录'
)
def resume(project_dir: str):
    """从断点继续执行"""
    project_path = Path(project_dir)
    
    if not project_path.exists():
        logger.error(f"项目目录不存在：{project_path}")
        return
    
    # 检查任务文件
    task_file = project_path / "tasks.json"
    if not task_file.exists():
        logger.error("未找到任务文件，无法恢复")
        return
    
    logger.info(f"从项目目录恢复：{project_path}")
    logger.info("请运行生成命令继续执行")


@cli.command()
@click.option(
    '--project-dir',
    default='./projects/default',
    help='项目目录'
)
def status(project_dir: str):
    """查看项目状态"""
    project_path = Path(project_dir)
    
    if not project_path.exists():
        print(f"项目目录不存在：{project_path}")
        return
    
    from personal_mode.checkpoint import CheckpointManager
    
    checkpoint_mgr = CheckpointManager(project_path)
    progress = checkpoint_mgr.get_progress()
    
    print("\n" + "=" * 50)
    print(" 项目状态")
    print("=" * 50)
    print(f" 总任务数：{progress['total']}")
    print(f" 已完成：{progress['completed']}")
    print(f" 待处理：{progress['pending']}")
    print(f" 失败：{progress['failed']}")
    print(f" 完成率：{progress['percentage']:.1f}%")
    print("=" * 50 + "\n")


@cli.command()
def check():
    """检查系统环境和 GPU 状态"""
    import torch
    
    print("\n" + "=" * 60)
    print(" 系统环境检查")
    print("=" * 60)
    print(f"\nPython 版本：{sys.version}")
    
    try:
        import torch
        print(f"PyTorch 版本：{torch.__version__}")
    except ImportError:
        print("PyTorch: 未安装")
    
    try:
        import psutil
        print(f"psutil: 已安装")
    except ImportError:
        print("psutil: 未安装 (建议安装)")
    
    print(f"\nCUDA 可用：{torch.cuda.is_available() if 'torch' in dir() else False}")
    
    if torch.cuda.is_available():
        print(f"CUDA 版本：{torch.version.cuda}")
        print(f"GPU 数量：{torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"\n  GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"    - 显存：{props.total_memory / 1024**2:.0f} MB")
            print(f"    - 计算能力：{props.major}.{props.minor}")
    else:
        print("\n警告：未检测到 CUDA 设备")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    cli()
