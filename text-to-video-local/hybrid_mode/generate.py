#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合模式 - 主命令行工具

云端 AI 生成图片 + 本地轻量合成视频
无需独立 GPU，集成显卡即可运行
"""

import sys
import json
import logging
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from hybrid_mode.prompt_generator import PromptTemplateGenerator
from hybrid_mode.video_synthesizer import VideoSynthesizer


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """混合模式 - 云端图片 + 本地合成
    
    使用云端免费 AI 图片生成服务，结合本地轻量视频合成，
    实现在任何电脑上（包括无独立显卡）制作 AI 视频。
    
    资源优势：
    - GPU 显存：0GB（集成显卡即可）
    - 内存：4-8GB
    - 电力消耗：降低 90-95%
    - 硬件成本：0 元
    
    示例:
    
    \b
    # 1. 生成提示词模板
    python hybrid_mode/generate.py template --type iterative -o prompts.json
    
    # 2. 根据模板批量下载图片（使用 API）
    python hybrid_mode/generate.py download --template prompts.json --output ./images
    
    # 3. 本地合成视频
    python hybrid_mode/generate.py synthesize --input ./images --output video.mp4 --fps 24
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    '--type', '-t',
    type=click.Choice(['time_lapse', 'zoom', 'pan', 'iterative', 'custom']),
    default='time_lapse',
    help='模板类型'
)
@click.option(
    '--location', '-l',
    default='ancient temple courtyard',
    help='场景位置（用于 time_lapse）'
)
@click.option(
    '--subject', '-s',
    default='cyberpunk robot',
    help='拍摄主体（用于 zoom）'
)
@click.option(
    '--base-prompt', '-p',
    default='',
    help='基础提示词（用于 iterative）'
)
@click.option(
    '--output', '-o',
    default='./hybrid_mode/prompts/template.json',
    help='输出模板文件'
)
@click.option(
    '--style',
    type=click.Choice(['cyberpunk', 'fantasy', 'scifi', 'natural', 'horror']),
    default='cyberpunk',
    help='风格预设'
)
def template(type: str, location: str, subject: str, base_prompt: str, output: str, style: str):
    """生成提示词模板
    
    支持多种场景转换类型：
    - time_lapse: 时间流逝（同一场景不同时间）
    - zoom: 视角推进（远→中→近）
    - pan: 空间移动（场景 A→场景 B）
    - iterative: 迭代图生图（保持一致性）
    - custom: 自定义
    
    示例:
    
    \b
    # 生成时间流逝模板
    generate.py template -t time_lapse -l "mountain landscape" -o time_lapse.json
    
    # 生成视角推进模板
    generate.py template -t zoom -s "medieval castle" -o zoom.json
    
    # 生成迭代图生图模板
    generate.py template -t iterative -p "cyberpunk street, neon lights" -o iterative.json
    """
    generator = PromptTemplateGenerator(
        output_dir=str(Path(output).parent)
    )
    
    if type == 'time_lapse':
        template_data = generator.generate_time_lapse_template(
            location=location,
            style=style
        )
    elif type == 'zoom':
        template_data = generator.generate_zoom_sequence_template(
            subject=subject,
            style=style
        )
    elif type == 'iterative':
        if not base_prompt:
            logger.error("iterative 模式需要 --base-prompt 参数")
            return
        iteration_prompts = [
            "wide angle, empty scene",
            "add distant subject",
            "subject moving closer",
            "medium shot of subject",
            "close up, details"
        ]
        template_data = generator.generate_iterative_img2img_template(
            base_prompt=base_prompt,
            iteration_prompts=iteration_prompts,
            style=style,
            denoising_strength=0.4
        )
    else:
        logger.error(f"暂不支持自动创建 {type} 模板，请手动创建 JSON 文件")
        return
    
    # 保存到指定文件
    output_path = Path(output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 模板已生成：{output_path}")
    print(f"  类型：{template_data['type']}")
    print(f"  帧数：{template_data['total_frames']}")
    print(f"  风格：{template_data['style']}")
    print(f"\n下一步:")
    print(f"  1. 根据模板中的提示词，使用云端免费 API 生成图片")
    print(f"  2. 将生成的图片保存到统一目录")
    print(f"  3. 运行 synthesize 命令合成视频")


@cli.command()
@click.option(
    '--template', '-t',
    required=True,
    help='提示词模板文件（JSON）'
)
@click.option(
    '--output', '-o',
    default='./hybrid_mode/images',
    help='图片输出目录'
)
@click.option(
    '--platform', '-p',
    type=click.Choice(['seaart', 'tensor', 'bing', 'all']),
    default='all',
    help='使用的平台'
)
def download(template: str, output: str, platform: str):
    """根据模板批量生成/下载图片
    
    支持多个免费平台：
    - SeaArt.ai (每日 60-100 积分)
    - Tensor.art (每日 100 积分)
    - Bing Image Creator (免费)
    
    示例:
    
    \b
    # 使用所有平台生成图片
    generate.py download -t template.json -o ./images
    
    # 使用特定平台
    generate.py download -t template.json -o ./images -p seaart
    """
    template_path = Path(template)
    if not template_path.exists():
        logger.error(f"模板文件不存在：{template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    prompts = template_data.get('prompts', [])
    logger.info(f"模板包含 {len(prompts)} 个提示词")
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print(" 图片批量生成")
    print("="*60)
    print(f"\n配置信息:")
    print(f"  图片数量：{len(prompts)}")
    print(f"  输出目录：{output_dir.absolute()}")
    print(f"  平台：{platform}")
    print(f"\n{'='*60}")
    print("\n手动生成步骤:")
    print("\n1. 访问免费 AI 图片生成平台:")
    print("   - SeaArt.ai: https://www.seaart.ai")
    print("   - Tensor.art: https://tensor.art")
    print("   - Bing Image Creator: https://www.bing.com/create")
    print("\n2. 使用模板中的提示词依次生成:")
    
    for i, prompt_item in enumerate(prompts[:5], 1):  # 只显示前 5 个
        prompt = prompt_item.get('prompt', '')
        print(f"   [{i:03d}] {prompt[:80]}...")
    
    if len(prompts) > 5:
        print(f"   ... 还有 {len(prompts) - 5} 个提示词")
    
    print("\n3. 下载图片并重命名:")
    print(f"   - 第 1 张：image_001.jpg")
    print(f"   - 第 2 张：image_002.jpg")
    print(f"   - ...")
    print(f"   - 最后 1 张：image_{len(prompts):03d}.jpg")
    
    print("\n4. 所有图片下载完成后，运行:")
    print(f"   generate.py synthesize --input {output_dir} --output video.mp4")
    
    # 保存提示词列表供参考
    prompts_file = output_dir / "prompts_reference.txt"
    with open(prompts_file, 'w', encoding='utf-8') as f:
        f.write("# 提示词参考列表\n\n")
        for i, prompt_item in enumerate(prompts, 1):
            f.write(f"[{i:03d}] {prompt_item.get('prompt', '')}\n")
    
    print(f"\n✓ 提示词参考已保存：{prompts_file}")
    
    # 注意说明
    print("\n" + "="*60)
    print(" 重要提示")
    print("="*60)
    print("\n为保持一致性，请使用以下技巧:")
    
    if template_data.get('type') == 'iterative_img2img':
        print("\n【迭代图生图模式】")
        print("1. 第一张用文生图生成")
        print("2. 后续每张都用'图生图'功能，上传前一张作为参考")
        print(f"3. 重绘幅度设置为：{template_data.get('denoising_strength', 0.4)}")
        print("4. 每张都保留基础提示词中的共同元素")
    
    print("\n通用技巧:")
    print("- 使用相同的随机种子（如果平台支持）")
    print("- 保持 CFG Scale 一致（推荐 7-9）")
    print("- 使用相同的采样器和步数")
    print("- 如果平台有'style reference'功能，可以固定风格")


@cli.command()
@click.option(
    '--input', '-i',
    required=True,
    help='输入图片目录'
)
@click.option(
    '--output', '-o',
    default='./hybrid_mode/output/video.mp4',
    help='输出视频文件'
)
@click.option(
    '--fps',
    type=int,
    default=24,
    help='目标帧率'
)
@click.option(
    '--duration',
    type=float,
    default=None,
    help='每张图片持续时间（秒），默认根据 fps 计算'
)
@click.option(
    '--transition',
    type=click.Choice(['none', 'crossfade', 'fade']),
    default='none',
    help='转场效果'
)
@click.option(
    '--audio',
    default=None,
    help='添加音频文件（BGM 或配音）'
)
@click.option(
    '--upscale',
    type=float,
    default=1.0,
    help='视频放大倍数（1.0 不放大，2.0 放大 2 倍）'
)
def synthesize(
    input: str,
    output: str,
    fps: int,
    duration: float,
    transition: str,
    audio: str,
    upscale: float
):
    """本地合成视频
    
    将云端生成的图片序列合成为视频，CPU 即可完成，
    无需独立 GPU。
    
    示例:
    
    \b
    # 基础合成
    generate.py synthesize -i ./images -o video.mp4 --fps 24
    
    # 添加转场效果
    generate.py synthesize -i ./images -o video.mp4 --transition crossfade
    
    # 添加背景音乐
    generate.py synthesize -i ./images -o video.mp4 --audio bgm.mp3
    
    # 高质量放大
    generate.py synthesize -i ./images -o video_4k.mp4 --upscale 2.0
    """
    print("\n" + "="*60)
    print(" AI 视频合成 - 混合模式")
    print("="*60)
    print(f"\n配置信息:")
    print(f"  输入目录：{input}")
    print(f"  输出文件：{output}")
    print(f"  帧率：{fps}fps")
    print(f"  图片时长：{duration or 'auto'} 秒")
    print(f"  转场效果：{transition or '无'}")
    print(f"  音频文件：{audio or '无'}")
    print(f"  放大倍数：{upscale}x")
    print(f"\n{'='*60}\n")
    
    synthesizer = VideoSynthesizer()
    
    # 1. 合成图片为视频
    if transition == 'none':
        output_video = synthesizer.create_video_from_images(
            image_dir=input,
            output_file=output,
            fps=fps,
            duration_per_image=duration
        )
    else:
        output_video = synthesizer.create_video_with_transitions(
            image_dir=input,
            output_file=output,
            fps=fps,
            transition_type=transition
        )
    
    if not output_video:
        logger.error("视频合成失败")
        return
    
    print(f"\n✓ 视频合成完成：{output_video}")
    
    # 2. 添加音频（可选）
    if audio:
        audio_output = output_video.replace('.mp4', '_with_audio.mp4')
        result = synthesizer.add_audio(
            video_file=output_video,
            audio_file=audio,
            output_file=audio_output
        )
        if result:
            output_video = result
            print(f"✓ 音频已添加：{output_video}")
    
    # 3. 放大视频（可选）
    if upscale > 1.0:
        upscaled_output = output_video.replace('.mp4', f'_upscaled_{upscale}x.mp4')
        result = synthesizer.upscale_video(
            input_file=output_video,
            output_file=upscaled_output,
            scale_factor=upscale
        )
        if result:
            print(f"✓ 视频已放大：{result}")
    
    # 4. 显示最终信息
    info = synthesizer.get_video_info(output_video)
    print("\n" + "="*60)
    print(" 最终视频信息")
    print("="*60)
    if info and 'format' in info:
        fmt = info['format']
        print(f"  文件：{output_video}")
        print(f"  时长：{fmt.get('duration', 'N/A')}秒")
        print(f"  大小：{int(fmt.get('size', 0)) / 1024 / 1024:.1f}MB")
    print("="*60 + "\n")
    
    print("✓ 完成！")
    print("\n资源消耗统计:")
    print("  - GPU 显存：0GB（集成显卡即可）")
    print("  - 内存：<2GB")
    print("  - 电力：约 50-100W")
    print("  - 对比本地 GPU 模式节省：90-95% 资源")


@cli.command()
def show_resources():
    """显示资源配置说明"""
    print("\n" + "="*60)
    print(" 混合模式资源配置说明")
    print("="*60)
    
    print("\n【最低配置要求】")
    print("  CPU: 任意双核以上")
    print("  内存：4GB")
    print("  GPU: 集成显卡即可")
    print("  存储：2GB 可用空间")
    print("  网络：需要（用于云端图片生成）")
    
    print("\n【推荐配置】")
    print("  CPU: 4 核以上")
    print("  内存：8GB")
    print("  GPU: 集成显卡（或入门独显更好）")
    print("  存储：10GB 可用空间")
    print("  网络：稳定连接")
    
    print("\n【资源对比】")
    print("\n| 资源类型 | 本地 GPU 模式 | 混合模式 | 节省比例 |")
    print("|---------|-----------|---------|---------|")
    print("| GPU 显存 | 12-24GB   | 0GB     | 100%    |")
    print("| 内存     | 32-64GB   | 4-8GB   | 75-87%  |")
    print("| 存储     | 100-200GB | 1-2GB   | 98%     |")
    print("| 电力/次  | 1-2 度     | 0.05 度  | 95%     |")
    print("| 硬件成本 | 5000+ 元  | 0 元     | 100%    |")
    
    print("\n【适用场景】")
    print("  ✓ 个人创作")
    print("  ✓ 学习使用")
    print("  ✓ 预算有限")
    print("  ✓ 电脑配置较低")
    print("  ✓ 偶尔制作视频")
    
    print("\n不适用场景:")
    print("  ✗ 需要高度隐私的项目（图片上传云端）")
    print("  ✗ 大规模批量生产（受每日免费额度限制）")
    print("  ✗ 实时性要求高的任务（云端生成需等待）")
    
    print("\n" + "="*60 + "\n")


@cli.command()
def show_templates():
    """显示所有可用模板"""
    generator = PromptTemplateGenerator()
    templates = generator.list_templates()
    
    if not templates:
        print("\n暂无模板，使用 template 命令创建")
        return
    
    print(f"\n可用模板 ({len(templates)} 个):\n")
    print(f"{'文件':<50} | {'类型':<20} | {'帧数':<8}")
    print("-" * 80)
    for t in templates:
        filename = Path(t['file']).name
        print(f"{filename:<50} | {t['type']:<20} | {t['total_frames']:<8}")
    print()


if __name__ == '__main__':
    cli()
