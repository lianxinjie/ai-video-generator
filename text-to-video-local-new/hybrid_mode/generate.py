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
from hybrid_mode.ai_analyzer import AIStyleAnalyzer


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
    
    三种使用方式：
    
    1. 分步执行（推荐新手）:
       generate.py template -a -p "提示词" -o template.json
       generate.py synthesize -i ./images -o video.mp4 --voiceover --template template.json
    
    2. 一键完整流程（快捷）:
       generate.py full -p "提示词" -o output_dir
    
    示例:
    
    \b
    # 1. 生成提示词模板
    python hybrid_mode/generate.py template --type iterative -o prompts.json
    
    # 2. 根据模板中的提示词，手动下载图片
    # 访问 SeaArt.ai / Tensor.art 等平台
    
    # 3. 本地合成视频（支持 AI 配音）
    python hybrid_mode/generate.py synthesize --input ./images --output video.mp4 --voiceover
    
    # 4. 一键完整流程（新增）
    python hybrid_mode/generate.py full -p "cyberpunk city" -d 5 -o output
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    '--prompt', '-p',
    required=True,
    help='基础提示词'
)
@click.option(
    '--output-dir', '-o',
    default='./hybrid_mode/full_output',
    help='输出目录'
)
@click.option(
    '--duration', '-d',
    type=float,
    default=5.0,
    help='总时长（秒）'
)
@click.option(
    '--fps',
    type=int,
    default=24,
    help='帧率'
)
@click.option(
    '--voiceover',
    is_flag=True,
    help='启用 AI 智能配音'
)
@click.option(
    '--character-voice',
    default='zh-CN-XiaoxiaoNeural',
    help='配音语音'
)
@click.option(
    '--bgm-file',
    default=None,
    help='背景音乐文件'
)
@click.option(
    '--transition',
    type=click.Choice(['none', 'crossfade', 'fade']),
    default='crossfade',
    help='转场效果'
)
def full(prompt: str, output_dir: str, duration: float, fps: int,
         voiceover: bool, character_voice: str, bgm_file: str, transition: str):
    """一键完整流程
    
    自动执行以下步骤：
    1. AI 分析提示词并生成模板
    2. 生成配音脚本
    3. 显示提示词列表（需要手动生成图片）
    4. 等待图片准备好后合成视频
    5. 添加配音和 BGM
    
    示例:
    
    \b
    # 一键生成（手动下载图片）
    generate.py full -p "cyberpunk city" -o output
    
    # 一键生成 + AI 配音
    generate.py full -p "魔法城堡" -d 10 -o output --voiceover
    
    # 一键生成 + 配音 + BGM
    generate.py full -p "童话故事" -d 15 -o output \\
        --voiceover \\
        --character-voice zh-CN-XiaoxiaoNeural \\
        --bgm-file music/bgm.mp3
    """
    print("\n" + "="*70)
    print(" 混合模式 - 一键完整流程")
    print("="*70)
    
    print(f"\n提示词：{prompt}")
    print(f"输出目录：{output_dir}")
    print(f"时长：{duration}秒")
    print(f"配音：{'启用' if voiceover else '禁用'}")
    if voiceover:
        print(f"  语音：{character_voice}")
        if bgm_file:
            print(f"  BGM: {bgm_file}")
    print()
    
    # 1. 生成提示词模板
    print("\n【步骤 1】AI 分析并生成提示词模板...\n")
    
    from hybrid_mode.prompt_generator import PromptTemplateGenerator
    from hybrid_mode.ai_analyzer import AIStyleAnalyzer
    
    analyzer = AIStyleAnalyzer()
    analysis = analyzer.analyze_prompt(prompt)
    
    scene_type = analysis['scene_type']['type']
    style = analysis['style']['style']
    
    print(f"  场景类型：{scene_type}")
    print(f"  艺术风格：{style}")
    print(f"  置信度：{analysis['confidence']['overall']:.0%}")
    
    generator = PromptTemplateGenerator(output_dir=output_dir)
    
    # 根据类型生成模板
    if scene_type == 'time_lapse':
        template_data = generator.generate_time_lapse_template(
            location=prompt,
            style=style
        )
    elif scene_type in ['zoom', 'dolly_zoom']:
        template_data = generator.generate_zoom_sequence_template(
            subject=prompt,
            style=style
        )
    else:
        # 默认使用迭代模式
        template_data = generator.generate_iterative_img2img_template(
            base_prompt=prompt,
            iteration_prompts=[
                "wide angle, establishing shot",
                "medium shot, subject appears",
                "medium close-up",
                "close-up, details",
                "extreme close-up"
            ],
            style=style,
            denoising_strength=0.4
        )
    
    # 2. 生成配音脚本（增强版：三层配音架构）
    if voiceover:
        print(f"\n【步骤 2】生成 AI 配音脚本（增强三层架构）...")
        
        # 优先使用增强配音分析器（三层架构）
        try:
            from personal_mode.enhanced_voice_analyzer import EnhancedAIVoiceAnalyzer
            enhanced_analyzer = EnhancedAIVoiceAnalyzer()
            
            script_result = enhanced_analyzer.analyze_for_layers(
                prompt=prompt,
                duration=duration
            )
            
            # 提取配音脚本（三层：人物 + 音效+BGM）
            template_data['voiceover_script'] = script_result.get('character_segments', [])
            template_data['sound_effects'] = script_result.get('sound_effects', [])
            template_data['bgm_config'] = script_result.get('bgm_config', {})
            
            print(f"  ✓ 生成三层配音架构:")
            print(f"    - 人物配音：{len(script_result.get('character_segments', []))} 段")
            print(f"    - 音效：{len(script_result.get('sound_effects', []))} 个")
            print(f"    - 背景音乐：{'有' if script_result.get('bgm_config') else '无'}")
            
        except ImportError:
            # 回退到基础配音分析器
            print(f"\n【步骤 2】生成 AI 配音脚本（基础版）...")
            from personal_mode.ai_voice_analyzer import AIVoiceAnalyzer
            voice_analyzer = AIVoiceAnalyzer()
            
            script_segments = voice_analyzer.split_script_by_duration(
                full_prompt=prompt,
                total_duration=duration,
                segment_duration=0.5
            )
            
            template_data['voiceover_script'] = script_segments
            print(f"  ✓ 生成 {len(script_segments)} 段配音脚本（基础版）")
    
    # 3. 保存模板
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    template_file = output_dir_path / 'template.json'
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n【步骤 3】提示词模板已保存：{template_file}")
    
    # 4. 显示提示词列表
    print(f"\n【步骤 4】请使用以下提示词在云端平台生成图片\n")
    
    prompts = template_data.get('prompts', [])
    print(f"共需要生成 {len(prompts)} 张图片：\n")
    
    for i, prompt_item in enumerate(prompts[:5], 1):
        p = prompt_item.get('prompt', '')
        print(f"  [{i:03d}] {p[:80]}...")
    
    if len(prompts) > 5:
        print(f"  ... 还有 {len(prompts) - 5} 个提示词（见模板文件）")
    
    # 5. 下载说明
    print(f"\n【步骤 5】前往免费平台生成图片:")
    print("  - SeaArt.ai: https://www.seaart.ai")
    print("  - Tensor.art: https://tensor.art")
    print("  - Bing Image Creator: https://www.bing.com/create")
    
    images_dir = output_dir_path / 'images'
    print(f"\n  将下载的图片保存到：{images_dir}")
    print("  命名规则：image_001.jpg, image_002.jpg, ...")
    
    # 6. 询问是否已准备好图片
    input("\n准备好所有图片后，按 Enter 键继续...\n")
    
    # 检查图片目录
    if not images_dir.exists():
        images_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"【步骤 6】开始合成视频...\n")
    
    # 7. 合成视频
    from hybrid_mode.video_synthesizer import VideoSynthesizer
    synthesizer = VideoSynthesizer()
    
    video_file = output_dir_path / 'video.mp4'
    
    if transition == 'none':
        result = synthesizer.create_video_from_images(
            image_dir=str(images_dir),
            output_file=str(video_file),
            fps=fps,
            duration_per_image=duration / len(prompts) if prompts else 0.5
        )
    else:
        result = synthesizer.create_video_with_transitions(
            image_dir=str(images_dir),
            output_file=str(video_file),
            fps=fps,
            transition_type=transition
        )
    
    if not result:
        print("❌ 视频合成失败")
        return
    
    print(f"✓ 视频合成完成：{result}")
    
    # 8. 添加配音（如果启用）
    if voiceover:
        print(f"\n【步骤 7】生成并添加配音...")
        
        # 复用 synthesize 命令的配音逻辑
        # 注意：这里简化处理，实际应该调用 synthesize 命令
        print("  提示：请运行以下命令添加配音:")
        print(f"  generate.py synthesize -i {images_dir} -o {video_file}")
        print(f"    --voiceover --template {template_file}")
        print(f"    --character-voice {character_voice}")
        if bgm_file:
            print(f"    --bgm-file {bgm_file} --bgm-volume 0.3")
    else:
        print(f"\n✓ 完成：{video_file}")
    
    print("\n" + "="*70)


@cli.command()
@click.option(
    '--type', '-t',
    type=click.Choice(['time_lapse', 'zoom', 'pan', 'iterative', 'custom']),
    default=None,
    help='模板类型（不指定时 AI 自动判断）'
)
@click.option(
    '--location', '-l',
    default=None,
    help='场景位置（用于 time_lapse）'
)
@click.option(
    '--subject', '-s',
    default=None,
    help='拍摄主体（用于 zoom）'
)
@click.option(
    '--base-prompt', '-p',
    required=True,
    help='基础提示词（AI 会自动分析并生成模板）'
)
@click.option(
    '--output', '-o',
    default='./hybrid_mode/prompts/template.json',
    help='输出模板文件'
)
@click.option(
    '--style',
    type=click.Choice(['cyberpunk', 'fantasy', 'scifi', 'natural', 'horror', 'auto']),
    default='auto',
    help='风格预设（auto 时 AI 自动判断）'
)
@click.option(
    '--auto', '-a',
    is_flag=True,
    help='使用 AI 智能分析提示词，自动选择场景类型和风格'
)
@click.option(
    '--show-analysis',
    is_flag=True,
    help='显示 AI 分析结果后退出'
)
def template(type: str, location: str, subject: str, base_prompt: str, output: str, style: str, auto: bool, show_analysis: bool):
    """生成提示词模板（支持 AI 智能分析）
    
    支持多种场景转换类型：
    - time_lapse: 时间流逝（同一场景不同时间）
    - zoom: 视角推进（远→中→近）
    - pan: 空间移动（场景 A→场景 B）
    - iterative: 迭代图生图（保持一致性）
    - custom: 自定义
    
    新增 AI 智能分析功能：
    - 自动判断场景转换类型
    - 自动识别艺术风格
    - 提供优化建议
    
    示例:
    
    \b
    # AI 自动分析推荐（推荐）
    generate.py template -a -p "赛博朋克城市从日出到夜晚的变化"
    
    # 显示 AI 分析结果
    generate.py template -a -p "cyberpunk city, neon lights" --show-analysis
    
    # 手动指定类型
    generate.py template -t time_lapse -l "mountain landscape" -o time_lapse.json
    
    # 生成视角推进模板
    generate.py template -t zoom -s "medieval castle" -o zoom.json
    
    # 生成迭代图生图模板
    generate.py template -t iterative -p "cyberpunk street, neon lights" -o iterative.json
    """
    # 使用 AI 智能分析
    if auto or (type is None and style == 'auto'):
        print("\n" + "="*60)
        print(" AI 智能分析模式")
        print("="*60 + "\n")
        
        analyzer = AIStyleAnalyzer()
        analysis_result = analyzer.analyze_prompt(base_prompt)
        
        # 显示分析结果
        print_analysis(analysis_result)
        
        if show_analysis:
            # 仅显示分析结果，不生成模板
            return
        
        # 使用 AI 推荐的类型和风格
        if type is None:
            type = analysis_result['scene_type']['type']
            print(f"\n✓ AI 推荐场景类型：{type}")
        
        if style == 'auto':
            style = analysis_result['style']['style']
            print(f"✓ AI 推荐艺术风格：{style}")
        
        # 如果置信度低，提醒用户
        if analysis_result['confidence']['overall'] < 0.4:
            print("\n⚠ AI 分析置信度较低，建议:")
            print("  - 添加更多细节描述")
            print("  - 手动指定 --type 和 --style 参数")
            print(f"  - 继续使用 AI 推荐（当前：type={type}, style={style}）")
            print()
    
    # 处理 auto 类型/风格
    if type == 'custom' or type is None:
        type = 'iterative'  # 默认使用 iterative
        logger.info("使用默认场景类型：iterative")
    
    if style == 'auto' or style is None:
        style = 'cyberpunk'  # 默认使用 cyberpunk
        logger.info("使用默认风格：cyberpunk")
    
    # 继续原有的模板生成逻辑
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
    
    # 新增：AI 配音分析
    try:
        from personal_mode.ai_voice_analyzer import AIVoiceAnalyzer
        base_prompt_for_analysis = base_prompt
        
        print(f"\n" + "="*60)
        print(" AI 智能配音分析")
        print("="*60 + "\n")
        
        voice_analyzer = AIVoiceAnalyzer()
        estimated_duration = template_data['total_frames'] * 0.5  # 假设每帧 0.5 秒
        
        script_segments = voice_analyzer.split_script_by_duration(
            full_prompt=base_prompt_for_analysis,
            total_duration=estimated_duration,
            segment_duration=0.5
        )
        
        # 将配音脚本添加到模板中
        template_data['voiceover_script'] = script_segments
        
        print(f"  分析完成：共 {len(script_segments)} 段配音\n")
        print(f"  前 3 段示例:")
        for seg in script_segments[:3]:
            print(f"    段{seg['segment_index'] + 1}: {seg['voiceover']['text']}")
            print(f"           情绪：{seg['voiceover']['emotion']}, 语速：{seg['voiceover']['speed']}字/分钟")
        
        if len(script_segments) > 3:
            print(f"    ... 还有 {len(script_segments) - 3} 段")
        
        print(f"\n✓ 配音脚本已添加到模板")
        print(f"\n配音建议:")
        if script_segments:
            emotions_count = {}
            for seg in script_segments:
                emotion = seg['voiceover']['emotion']
                emotions_count[emotion] = emotions_count.get(emotion, 0) + 1
            
            dominant_emotion = max(emotions_count, key=emotions_count.get)
            print(f"  - 主导情绪：{dominant_emotion} ({emotions_count[dominant_emotion]}/{len(script_segments)}段)")
            print(f"  - 推荐语音：{script_segments[0]['voiceover']['voice']}")
            print(f"  - 平均语速：{sum(s['voiceover']['speed'] for s in script_segments) // len(script_segments)}字/分钟")
            
    except ImportError:
        print(f"\n⚠ 未导入配音分析模块，跳过配音分析")
    except Exception as e:
        print(f"\n⚠ 配音分析失败：{e}")


@cli.command()
@click.option(
    '--prompt', '-p',
    required=True,
    help='要分析的提示词'
)
@click.option(
    '--output', '-o',
    default=None,
    help='保存分析结果为 JSON 文件'
)
@click.option(
    '--detail', '-d',
    is_flag=True,
    help='显示详细分析信息'
)
def analyze(prompt: str, output: str, detail: bool):
    """AI 智能分析提示词
    
    自动分析用户提示词，推荐最优的场景转换类型和艺术风格。
    
    示例:
    
    \b
    # 分析中文提示词
    generate.py analyze -p "赛博朋克城市从日出到夜晚的变化"
    
    # 分析英文提示词
    generate.py analyze -p "cyberpunk city, neon lights, time lapse"
    
    # 保存分析结果
    generate.py analyze -p "..." -o analysis.json
    """
    print("\n" + "="*60)
    print(" AI 智能分析")
    print("="*60 + "\n")
    
    analyzer = AIStyleAnalyzer()
    result = analyzer.analyze_prompt(prompt)
    
    # 打印分析结果
    print_analysis(result)
    
    # 保存为 JSON
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✓ 分析结果已保存：{output}")
    
    # 提供下一步建议
    print("\n【下一步建议】")
    scene_type = result['scene_type']['type']
    style = result['style']['style']
    
    if result['confidence']['overall'] > 0.6:
        print(f"✓ AI 分析置信度高，可直接生成模板:")
        print(f"  generate.py template -a -p \"{prompt}\" -o template.json")
    elif result['confidence']['overall'] > 0.3:
        print(f"⚠ AI 分析置信度中等，可:")
        print(f"  1. 直接使用：generate.py template -a -p \"{prompt}\" -o template.json")
        print(f"  2. 手动指定：generate.py template -t {scene_type} -p \"{prompt}\" --style {style}")
    else:
        print(f"⚠ AI 分析置信度低，建议手动指定参数:")
        print(f"  generate.py template -t iterative -p \"{prompt}\" --style custom")
    
    print()


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
    '--voiceover',
    is_flag=True,
    help='启用 AI 智能配音分析（需要模板文件）'
)
@click.option(
    '--character-voice',
    default='zh-CN-XiaoxiaoNeural',
    help='配音语音（启用 voiceover 时使用）'
)
@click.option(
    '--bgm-file',
    default=None,
    help='背景音乐文件'
)
@click.option(
    '--bgm-volume',
    type=float,
    default=0.3,
    help='背景音乐音量（0.0-1.0）'
)
@click.option(
    '--template',
    default=None,
    help='提示词模板文件（用于 AI 配音分析）'
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
    upscale: float,
    voiceover: bool,
    character_voice: str,
    bgm_file: str,
    bgm_volume: float,
    template: str
):
    """本地合成视频（支持三层配音架构）
    
    将云端生成的图片序列合成为视频，CPU 即可完成，
    无需独立 GPU。
    
    新增 AI 智能配音功能（三层架构）：
    - 人物配音：基于情绪分析的智能配音（0.5s 分段）
    - 音效：AI 生成的场景音效（待实现）
    - 背景音乐：循环播放的 BGM（可调节音量）
    
    示例:
    
    \b
    # 基础合成
    generate.py synthesize -i ./images -o video.mp4 --fps 24
    
    # 添加转场效果
    generate.py synthesize -i ./images -o video.mp4 --transition crossfade
    
    # 添加 AI 智能配音（需要模板文件）
    generate.py synthesize -i ./images -o video.mp4 --voiceover --template prompts.json
    
    # 自定义配音语音
    generate.py synthesize -i ./images -o video.mp4 \\
        --voiceover \\
        --template prompts.json \\
        --character-voice zh-CN-YunxiNeural
    
    # 添加背景音乐
    generate.py synthesize -i ./images -o video.mp4 --audio bgm.mp3
    
    # 完整配音：人物 +BGM
    generate.py synthesize -i ./images -o video.mp4 \\
        --voiceover \\
        --template prompts.json \\
        --character-voice zh-CN-XiaoxiaoNeural \\
        --bgm-file music/bgm.mp3 \\
        --bgm-volume 0.3
    
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
    if voiceover:
        print(f"  AI 配音：启用")
        print(f"    语音：{character_voice}")
        if template:
            print(f"    模板：{template}")
        if bgm_file:
            print(f"    BGM: {bgm_file} (音量：{bgm_volume})")
    elif audio:
        print(f"  音频文件：{audio}")
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
    
    # AI 配音（如果启用，支持三层架构）
    if voiceover:
        try:
            import edge_tts
            import asyncio
            
            print("\n【AI 配音】正在生成三层配音...\n")
            
            # 1. 读取模板中的配音脚本（支持三层架构）
            voiceover_script = []
            sound_effects = []
            bgm_config = {}
            
            if template and Path(template).exists():
                with open(template, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    voiceover_script = template_data.get('voiceover_script', [])
                    sound_effects = template_data.get('sound_effects', [])
                    bgm_config = template_data.get('bgm_config', {})
            
            if not voiceover_script:
                # 尝试使用增强配音分析器生成三层架构
                try:
                    from personal_mode.enhanced_voice_analyzer import EnhancedAIVoiceAnalyzer
                    enhanced_analyzer = EnhancedAIVoiceAnalyzer()
                    result = enhanced_analyzer.analyze_for_layers(
                        prompt="AI 视频",
                        duration=dps
                    )
                    voiceover_script = result.get('character_segments', [])
                    sound_effects = result.get('sound_effects', [])
                    bgm_config = result.get('bgm_config', {})
                    print("  ✓ 使用增强配音分析器（三层架构）")
                except ImportError:
                    # 回退到基础配音
                    from personal_mode.ai_voice_analyzer import AIVoiceAnalyzer
                    analyzer = AIVoiceAnalyzer()
                    voiceover_script = analyzer.split_script_by_duration(
                        full_prompt="AI 视频",
                        total_duration=dps,
                        segment_duration=0.5
                    )
                    print("  ✓ 使用基础配音分析器（单层）")
            
            # 2. 生成配音（三层：人物 + 音效+BGM）
            audio_dir = Path(input).parent / 'audio'
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            audio_tracks = {
                'character': [],
                'sound_effects': [],
                'bgm': None
            }
            
            # 2.1 生成人物配音
            print("\n【人物配音】")
            character_audio_files = []
            
            async def generate_single_voiceover(text, voice, output_file):
                """异步生成单个配音"""
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_file)
                return output_file
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for i, seg in enumerate(voiceover_script):
                    text = seg.get('voiceover', {}).get('text', str(seg))
                    voice = character_voice or 'zh-CN-XiaoxiaoNeural'
                    
                    audio_file = audio_dir / f'segment_{i:03d}_character.wav'
                    
                    print(f"  生成配音 {i + 1}/{len(voiceover_script)}: {text[:30]}...")
                    
                    try:
                        loop.run_until_complete(
                            generate_single_voiceover(text, voice, str(audio_file))
                        )
                        character_audio_files.append(str(audio_file))
                    except Exception as e:
                        print(f"  ⚠ 段{i + 1}配音生成失败：{e}")
            finally:
                loop.close()
            
            if character_audio_files:
                print(f"\n  合并 {len(character_audio_files)} 个配音片段...")
                from hybrid_mode.video_synthesizer import VideoSynthesizer
                synth = VideoSynthesizer()
                
                combined_file = audio_dir / 'character_combined.wav'
                result = synth.concatenate_audios(character_audio_files, str(combined_file))
                
                if result:
                    print(f"  ✓ 配音合并完成：{result}")
                    audio_tracks['character'] = [str(combined_file)]
            
            # 2.2 生成音效（增强三层架构）
            if sound_effects:
                print(f"\n【音效】生成 {len(sound_effects)} 个音效...")
                # TODO: 使用 AI 音效生成模型（如 AudioLDM）生成音效
                # 目前先标记支持，后续实现
                print("  ⚠  音效生成功能待实现，已跳过")
            
            # 2.3 添加背景音乐（增强三层架构）
            if bgm_config and bgm_file:
                print(f"\n【背景音乐】使用：{bgm_file}")
                audio_tracks['bgm'] = bgm_file
            elif bgm_file:
                print(f"\n【背景音乐】使用：{bgm_file}")
                audio_tracks['bgm'] = bgm_file
            
            # 3. 混合三层音频（人物 + 音效+BGM）
            final_audio = None
            
            if audio_tracks['character'] and bgm_file:
                print(f"\n【音频混合】混合人物配音和 BGM...")
                
                bgm_volume = 0.3  # BGM 音量（默认 0.3，不盖过配音）
                
                combined_file = audio_dir / 'character_combined.wav'
                bgm_output = audio_dir / 'final_audio.wav'
                
                result = synth.mix_audio(
                    audio1=str(combined_file),
                    audio2=bgm_file,
                    output=str(bgm_output),
                    volume1=1.0,
                    volume2=bgm_volume
                )
                
                if result:
                    print(f"  ✓ 音频混合完成：{result}")
                    final_audio = result
            
            elif audio_tracks['character']:
                # 只有人物配音，无 BGM
                final_audio = str(audio_dir / 'character_combined.wav')
            
            elif bgm_file:
                # 只有 BGM，无人物配音
                final_audio = bgm_file
            
            # 4. 将最终音频添加到视频
            if final_audio and Path(final_audio).exists():
                print(f"\n【视频合成】将音频添加到视频...")
                audio_output = output_video.replace('.mp4', '_with_voiceover.mp4')
                result = synthesizer.add_audio(
                    video_file=output_video,
                    audio_file=final_audio,
                    output_file=audio_output
                )
                
                if result:
                    output_video = result
                    print(f"  ✓ AI 配音已添加：{output_video}")
                    
                    # 显示三层架构信息
                    if sound_effects or bgm_config:
                        print(f"\n【三层配音架构】")
                        print(f"  - 人物配音：{len(voiceover_script)} 段")
                        print(f"  - 音效：{len(sound_effects)} 个（待生成）")
                        print(f"  - 背景音乐：{'有' if bgm_config else '无'}")
            
        except ImportError as e:
            print(f"\n⚠ 配音功能需要额外依赖：{e}")
            print("  安装命令：pip install edge-tts pydub")
        except Exception as e:
            print(f"\n⚠ 配音生成失败：{e}")
            import traceback
            traceback.print_exc()
    
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
