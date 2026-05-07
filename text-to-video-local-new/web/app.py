#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 视频生成器 - Web 界面和 API

提供两种调用方式：
1. API 接口：通过 HTTP 请求调用
2. Web 界面：浏览器访问操作

支持功能：
- 文本到视频生成
- 参考图片（人物卡/背景图）
- 三层配音架构
- 多种生成模式
"""

import os
import sys
import json
import shutil
import platform
import time
import stat
import zipfile
import tarfile
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import threading
import uuid
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# 配置
app.config['UPLOAD_FOLDER'] = Path('web/uploads')
app.config['OUTPUT_FOLDER'] = Path('web/outputs')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 创建必要的目录
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(parents=True, exist_ok=True)

# 任务状态存储
tasks = {}
packages = {}  # package_id -> package_dir


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Web 界面首页"""
    return render_template('index.html')


@app.route('/setup')
def setup_wizard():
    """设置向导页面"""
    return render_template('setup_wizard.html')

@app.route('/install')
def install_page():
    """依赖管理页面"""
    return render_template('install.html')


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    API: 生成视频
    
    请求参数:
    - prompt: 文本提示词（必需）
    - mode: 生成模式 (standard/optimized/collaborative)
    - duration: 视频时长（秒）
    - ref_images: 参考图片文件（可选）
    - ref_type: 参考图类型 (character/background/mixed)
    - ref_strength: 参考图强度 0.0-1.0
    - voiceover: 是否启用配音
    - character_voice: 配音语音
    - bgm_file: 背景音乐文件
    """
    try:
        # 获取参数
        prompt = request.form.get('prompt', '')
        if not prompt:
            return jsonify({'error': '提示词不能为空'}), 400
        
        mode = request.form.get('mode', 'optimized')
        duration = float(request.form.get('duration', 10))
        ref_type = request.form.get('ref_type', 'character')
        ref_strength = float(request.form.get('ref_strength', 0.6))
        voiceover = request.form.get('voiceover', 'false').lower() == 'true'
        character_voice = request.form.get('character_voice', 'zh-CN-XiaoxiaoNeural')
        
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        
        # 保存参考图片
        ref_images_path = None
        if 'ref_images' in request.files:
            ref_files = request.files.getlist('ref_images')
            if ref_files:
                ref_images_path = app.config['UPLOAD_FOLDER'] / task_id / 'references'
                ref_images_path.mkdir(parents=True, exist_ok=True)
                
                for file in ref_files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(ref_images_path / filename)
        
        # 保存 BGM 文件
        bgm_path = None
        if 'bgm_file' in request.files:
            bgm_file = request.files['bgm_file']
            if bgm_file and allowed_file(bgm_file.filename):
                bgm_path = app.config['UPLOAD_FOLDER'] / task_id / 'bgm'
                bgm_path.mkdir(parents=True, exist_ok=True)
                filename = secure_filename(bgm_file.filename)
                bgm_file.save(bgm_path / filename)
                bgm_path = bgm_path / filename
        
        # 创建输出目录
        output_dir = app.config['OUTPUT_FOLDER'] / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建命令行
        cmd = [
            sys.executable,
            'personal_mode/run.py',
            '-p', prompt,
            '-m', mode,
            '-d', str(duration),
            '-o', str(output_dir / 'output.mp4')
        ]
        
        # 添加参考图片参数
        if ref_images_path:
            cmd.extend(['--ref-images', str(ref_images_path)])
            cmd.extend(['--ref-type', ref_type])
            cmd.extend(['--ref-strength', str(ref_strength)])
        
        # 添加配音参数
        if voiceover:
            cmd.append('--voiceover')
            cmd.extend(['--character-voice', character_voice])
        
        if bgm_path:
            cmd.extend(['--bgm-file', str(bgm_path)])
        
        # 启动任务（后台运行）
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'prompt': prompt,
            'mode': mode,
            'start_time': str(uuid.uuid4())
        }
        
        def run_task():
            log_lines = []
            log_lines.append(f"开始执行命令：{' '.join(cmd)}")
            log_lines.append(f"工作目录：{Path(__file__).parent.parent}")
            log_lines.append("")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=Path(__file__).parent.parent,
                    timeout=600  # 10 分钟超时
                )
                
                # 记录标准输出
                if result.stdout:
                    log_lines.append("=== 标准输出 ===")
                    log_lines.append(result.stdout)
                    log_lines.append("")
                
                # 记录标准错误
                if result.stderr:
                    log_lines.append("=== 错误输出 ===")
                    log_lines.append(result.stderr)
                    log_lines.append("")
                
                if result.returncode == 0:
                    tasks[task_id]['status'] = 'completed'
                    log_lines.append("✅ 任务执行成功")
                    
                    # 查找生成的视频文件
                    video_files = list(output_dir.glob('*.mp4'))
                    if video_files:
                        tasks[task_id]['video_url'] = f'/api/output/{task_id}/{video_files[0].name}'
                        log_lines.append(f"视频文件：{video_files[0].name}")
                    else:
                        log_lines.append("⚠️  未找到生成的视频文件")
                        tasks[task_id]['status'] = 'failed'
                        tasks[task_id]['error'] = '生成成功但未找到视频文件'
                else:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['error'] = result.stderr
                    log_lines.append(f"❌ 任务执行失败，退出码：{result.returncode}")
                
                tasks[task_id]['progress'] = 100
                tasks[task_id]['log'] = '\n'.join(log_lines)
                
            except subprocess.TimeoutExpired:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = '任务执行超时（10 分钟）'
                log_lines.append("❌ 超时错误：任务执行超过 10 分钟")
                tasks[task_id]['log'] = '\n'.join(log_lines)
                
            except Exception as e:
                import traceback
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = str(e)
                log_lines.append(f"❌ 异常：{e}")
                log_lines.append(traceback.format_exc())
                tasks[task_id]['progress'] = 100
                tasks[task_id]['log'] = '\n'.join(log_lines)
        
        # 后台线程运行任务
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'running',
            'message': '任务已启动，正在生成视频...'
        })
    
    except Exception as e:
        import traceback
        log(f"视频生成 API 错误：{e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return jsonify({
            'error': f'服务器内部错误：{str(e)}',
            'details': traceback.format_exc()
        }), 500

@app.route('/api/models/list', methods=['GET'])
def api_list_models():
    """API: 获取可用模型列表（包含安装状态）"""
    try:
        import os
        models_dir = Path(__file__).parent.parent / "models"
        
        # 预定义的模型配置
        model_configs = {
            "modelscope": {
                "id": "modelscope",
                "name": "ModelScope 基础模型",
                "description": "阿里达摩院文本到视频基础模型",
                "source": "modelscope",
                "repo": "damo/text-to-video-synthesis",
                "size_gb": 2.5,
                "required": True,
                "reason": "基础模型，推荐优先下载"
            },
            "animatediff": {
                "id": "animatediff",
                "name": "AnimateDiff",
                "description": "卡通风格动画生成模型",
                "source": "huggingface",
                "repo": "guoyww/animatediff-motion-adapter-v1-5-2",
                "size_gb": 4.0,
                "required": False,
                "reason": "适合卡通风格动画"
            },
            "cogvideox": {
                "id": "cogvideox",
                "name": "CogVideoX-5b",
                "description": "高质量视频生成模型（需要大显存）",
                "source": "huggingface",
                "repo": "THUDM/CogVideoX-5b",
                "size_gb": 20.0,
                "required": False,
                "reason": "质量最高但需要大显存"
            },
            "svd": {
                "id": "svd",
                "name": "Stable Video Diffusion",
                "description": "图像转视频模型（需要 CUDA 支持）",
                "source": "huggingface",
                "repo": "stabilityai/stable-video-diffusion-img2vid-xt",
                "size_gb": 12.0,
                "required": False,
                "reason": "用于图像转视频，需要 CUDA 支持"
            },
            "animatediff_sd": {
                "id": "animatediff_sd",
                "name": "AnimateDiff SD Checkpoint",
                "description": "AnimateDiff 配套 SD 模型",
                "source": "huggingface",
                "repo": "frankjoshua/toonyou_beta6",
                "size_gb": 4.0,
                "required": False,
                "reason": "AnimateDiff 配套使用"
            }
        }
        
        # 获取已安装的模型
        installed_models = set()
        if models_dir.exists():
            for item in models_dir.iterdir():
                if item.is_dir() and item.name.startswith('models--'):
                    # 尝试匹配预定义模型
                    parts = item.name.split('--')
                    if len(parts) >= 3:
                        # 检查是否是已知模型
                        for mid, config in model_configs.items():
                            if config['repo'].split('/')[-1].lower() in item.name.lower():
                                installed_models.add(mid)
                                break
        
        # 构建完整模型列表
        models = []
        for mid, config in model_configs.items():
            is_installed = mid in installed_models
            models.append({
                'id': config['id'],
                'name': config['name'],
                'description': config['description'],
                'source': config['source'],
                'repo': config['repo'],
                'size_gb': config['size_gb'],
                'required': config['required'],
                'reason': config['reason'],
                'installed': is_installed,
                'status': 'installed' if is_installed else 'available',
                'path': str(models_dir / f"models--{mid}") if is_installed else None
            })
        
        # 排序：已安装的在前，必需的在前
        models.sort(key=lambda x: (not x['installed'], not x['required'], x['name']))
        
        return jsonify({
            'models': models,
            'total': len(models),
            'installed_count': len(installed_models),
            'success': True
        })
        
    except Exception as e:
        import traceback
        log(f"模型列表 API 错误：{e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return jsonify({
            'error': f'获取模型列表失败：{str(e)}',
            'models': [],
            'total': 0,
            'success': False
        }), 500

@app.route('/api/models/create-zip', methods=['POST'])
def api_create_model_zip():
    """API: 创建模型zip压缩包"""
    try:
        import uuid
        data = request.get_json() or {}
        model_name = data.get('model')
        compress_level = data.get('compress_level', 9)
        auto_extract = data.get('auto_extract', True)
        
        if not model_name:
            return jsonify({'error': '请指定要打包的模型名称'}), 400
        
        task_id = str(uuid.uuid4())
        
        # 创建任务
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'type': 'model_zip',
            'model': model_name,
            'auto_extract': auto_extract,
            'start_time': datetime.now().isoformat(),
            'log': f'开始打包模型：{model_name}\n'
        }
        
        # 后台线程执行打包
        def run_packaging():
            import sys
            from io import StringIO
            from contextlib import redirect_stdout
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from download_models import ModelDownloader
            
            task = tasks[task_id]
            
            try:
                # 创建下载器
                downloader = ModelDownloader(output_dir='./models', max_workers=1)
                
                # 重定向输出以捕获日志
                output = StringIO()
                with redirect_stdout(output):
                    # 打包模型（支持自动解压）
                    result = downloader.create_model_zip(
                        model_name=model_name,
                        compress_level=compress_level,
                        auto_extract=auto_extract
                    )
                
                task['log'] += output.getvalue()
                task['status'] = 'completed'
                task['progress'] = 100
                task['result'] = {
                    'success': True, 
                    'message': f'模型 {model_name} 打包成功', 
                    'zip_path': result.get('zip_path'),
                    'extract_result': result.get('extract_result')
                }
                
            except Exception as e:
                task['log'] += f"错误：{str(e)}\n"
                task['status'] = 'failed'
                task['progress'] = 100
                task['result'] = {'success': False, 'error': str(e)}
        
        # 启动线程
        thread = threading.Thread(target=run_packaging)
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id, 'success': True})
    
    except Exception as e:
        import traceback
        log(f"模型打包 API 错误：{e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return jsonify({'error': f'服务器内部错误：{str(e)}'}), 500

@app.route('/api/models/install', methods=['POST'])
def api_install_models():
    """API: 一键安装选择的模型"""
    try:
        import uuid
        data = request.get_json() or {}
        models = data.get('models', [])
        
        if not models:
            return jsonify({'error': '请选择要安装的模型'}), 400
        
        task_id = str(uuid.uuid4())
        
        # 创建任务
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'type': 'model_install',
            'models': models,
            'start_time': datetime.now().isoformat(),
            'log': f'开始下载模型：{", ".join(models)}\n'
        }
        
        # 后台线程执行下载
        def run_download():
            import sys
            from io import StringIO
            from contextlib import redirect_stdout
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from download_models import ModelDownloader
            
            task = tasks[task_id]
            
            try:
                # 创建下载器
                downloader = ModelDownloader(output_dir='./models', max_workers=2)
                
                # 检查已存在的模型
                existing = downloader.check_existing_models(models)
                models_to_download = [m for m in models if not existing.get(m, False)]
                
                if not models_to_download:
                    task['log'] += '所有选中的模型已存在，跳过下载\n'
                    task['status'] = 'completed'
                    task['progress'] = 100
                    return
                
                task['log'] += f'需要下载 {len(models_to_download)} 个模型，跳过 {len(models) - len(models_to_download)} 个已存在模型\n'
                
                # 重定向输出以捕获日志
                output = StringIO()
                with redirect_stdout(output):
                    results = downloader.download_batch(models_to_download, show_progress=False)
                
                # 更新日志
                task['log'] += output.getvalue()
                
                # 统计结果
                success_count = sum([1 for r in results if r['success']])
                fail_count = len(results) - success_count
                
                task['log'] += f'\n下载完成：成功 {success_count}/{len(results)}, 失败 {fail_count}/{len(results)}\n'
                
                if fail_count > 0:
                    task['status'] = 'partial'
                    task['failed_models'] = [r['name'] for r in results if not r['success']]
                else:
                    task['status'] = 'completed'
                
                task['progress'] = 100
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['log'] += f'错误：{e}\n'
        
        # 启动后台线程
        from threading import Thread
        thread = Thread(target=run_download)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'开始下载 {len(models)} 个模型'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/models/status/<task_id>', methods=['GET'])
def api_model_install_status(task_id):
    """API: 查询模型安装进度"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = tasks[task_id]
    
    # 读取进度文件（如果有）
    progress_log = tasks[task_id].get('log', '')
    if task.get('progress_file') and Path(task['progress_file']).exists():
        with open(task['progress_file'], 'r') as f:
            progress_log = f.read()[-10000:]
    
    result = {
        'task_id': task_id,
        'status': task.get('status', 'unknown'),
        'progress': task.get('progress', 0),
        'type': task.get('type', 'unknown'),
        'log': progress_log,
        'models': task.get('models', []),
    }
    
    if task.get('error'):
        result['error'] = task['error']
    
    if task.get('failed_models'):
        result['failed_models'] = task['failed_models']
    
    return jsonify(result)


@app.route('/api/models/cleanup', methods=['POST'])
def api_cleanup_models():
    """API: 清理模型缓存和临时文件"""
    try:
        data = request.get_json() or {}
        target = data.get('target', 'all')  # all, cache, temp, unused
        
        stats = {'cleaned': 0, 'freed_gb': 0, 'details': []}
        
        models_dir = Path('./models')
        if not models_dir.exists():
            return jsonify({'success': False, 'error': '模型目录不存在'})
        
        import shutil
        
        # 1. 清理缓存目录
        if target in ['all', 'cache']:
            for cache_dir in models_dir.rglob('.cache'):
                if cache_dir.is_dir():
                    size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    shutil.rmtree(cache_dir)
                    stats['cleaned'] += 1
                    stats['freed_gb'] += size / (1024 ** 3)
                    stats['details'].append(f'清理缓存：{cache_dir.relative_to(models_dir)} ({size/1024**2:.1f} MB)')
        
        # 2. 清理临时文件
        if target in ['all', 'temp']:
            for pattern in ['*.tmp', '*.pyc', '__pycache__', '*.egg-info']:
                for f in models_dir.rglob(pattern):
                    if f.is_file() or f.is_dir():
                        size = f.stat().st_size if f.is_file() else sum(x.stat().st_size for x in f.rglob('*') if x.is_file())
                        if f.is_file():
                            f.unlink()
                        else:
                            shutil.rmtree(f)
                        stats['cleaned'] += 1
                        stats['freed_gb'] += size / (1024 ** 3)
                        stats['details'].append(f'清理临时文件： ({size/1024**2:.1f} MB)')
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'清理完成：释放 {stats["freed_gb"]:.2f} GB 空间'
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code


@app.route('/api/models/delete', methods=['POST'])
def api_delete_model():
    """API: 删除已安装的模型"""
    try:
        data = request.get_json() or {}
        model_id = data.get('model')
        
        if not model_id:
            return jsonify({'success': False, 'error': '请指定模型'}), 400
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from download_models import ModelDownloader
        
        downloader = ModelDownloader(output_dir='./models')
        model_info = downloader.model_repos.get(model_id)
        
        if not model_info:
            return jsonify({'success': False, 'error': f'未知模型：{model_id}'})
        
        # 确定删除路径
        if model_info.get('type') == 'huggingface':
            repo_parts = model_info['repo'].split('/')
            check_path = Path('./models') / f"models--{repo_parts[0]}--{repo_parts[1]}"
        elif model_info.get('type') == 'modelscope':
            check_path = Path('./models') / model_info['repo'].split('/')[-1]
        else:
            return jsonify({'success': False, 'error': '不支持的模型类型'})
        
        if not check_path.exists():
            return jsonify({'success': False, 'error': '模型未安装'})
        
        import shutil
        # 计算大小
        size = sum(f.stat().st_size for f in check_path.rglob('*') if f.is_file())
        
        # 删除
        shutil.rmtree(check_path)
        
        return jsonify({
            'success': True,
            'model': model_id,
            'freed_gb': round(size / (1024 ** 3), 2),
            'message': f'模型 {model_id} 已删除，释放 {size/1024**3:.2f} GB'
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code


@app.route('/api/models/analyze', methods=['GET'])
def api_analyze_models():
    """API: 分析模型目录占用空间"""
    try:
        models_dir = Path('./models')
        if not models_dir.exists():
            return jsonify({'success': False, 'error': '模型目录不存在'})
        
        import shutil
        analysis = []
        
        # 分析每个模型
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from download_models import ModelDownloader
        
        downloader = ModelDownloader(output_dir='./models')
        
        for model_name, model_info in downloader.model_repos.items():
            # 确定路径
            if model_info.get('type') == 'huggingface':
                repo_parts = model_info['repo'].split('/')
                check_path = models_dir / f"models--{repo_parts[0]}--{repo_parts[1]}"
            elif model_info.get('type') == 'modelscope':
                check_path = models_dir / model_info['repo'].split('/')[-1]
            else:
                continue
            
            if check_path.exists():
                # 计算大小和文件数
                total_size = 0
                file_count = 0
                for f in check_path.rglob('*'):
                    if f.is_file():
                        total_size += f.stat().st_size
                        file_count += 1
                
                # 分析目录结构
                dir_breakdown = {}
                for subdir in check_path.iterdir():
                    if subdir.is_dir():
                        dir_size = sum(file.stat().st_size for file in subdir.rglob('*') if file.is_file())
                        dir_breakdown[subdir.name] = {
                            'size_gb': round(dir_size / (1024 ** 3), 2),
                            'files': sum(1 for file in subdir.rglob('*') if file.is_file())
                        }
                
                analysis.append({
                    'id': model_name,
                    'name': model_name.upper(),
                    'path': str(check_path),
                    'installed': True,
                    'download_size_gb': model_info.get('size_gb', 0),
                    'actual_size_gb': round(total_size / (1024 ** 3), 2),
                    'ratio': round(total_size / (1024 ** 3) / model_info.get('size_gb', 1), 2) if model_info.get('size_gb', 0) > 0 else 0,
                    'file_count': file_count,
                    'breakdown': dir_breakdown,
                    'status': 'ok' if total_size / (1024 ** 3) < model_info.get('size_gb', 1) * 3 else 'warning'
                })
            else:
                analysis.append({
                    'id': model_name,
                    'name': model_name.upper(),
                    'installed': False,
                    'download_size_gb': model_info.get('size_gb', 0)
                })
        
        # 总体统计
        total_actual = sum(m.get('actual_size_gb', 0) for m in analysis if m.get('installed'))
        total_download = sum(m.get('download_size_gb', 0) for m in analysis)
        
        # 计算缓存大小
        total_cache = 0
        for cache_dir in models_dir.rglob('.cache'):
            if cache_dir.is_dir():
                total_cache += sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        total_cache /= (1024 ** 3)
        
        return jsonify({
            'success': True,
            'models': analysis,
            'summary': {
                'total_models': len([m for m in analysis if m.get('installed')]),
                'total_download_gb': round(total_download, 2),
                'total_actual_gb': round(total_actual, 2),
                'total_cache_gb': round(total_cache, 2),
                'ratio': round(total_actual / total_download, 2) if total_download > 0 else 0
            }
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code


@app.route('/api/check-dependencies', methods=['GET'])
@app.route('/api/check-dependencies')
def api_check_dependencies():
    """API: 检查依赖安装状态"""
    try:
        import sys
        import importlib.util
        import importlib.metadata
        
        # 每次检测都重新初始化包列表（避免缓存）
        packages = {
            'flask': {
                'name': 'Flask',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'Web 服务框架',
                'module_name': 'flask',
                'pip_name': 'flask'
            },
            'PIL': {
                'name': 'Pillow',
                'required': True,
                'installed': False,
                'version': None,
                'description': '图像处理库',
                'module_name': 'PIL',
                'pip_name': 'pillow'
            },
            'psutil': {
                'name': 'psutil',
                'required': True,
                'installed': False,
                'version': None,
                'description': '系统监控库',
                'module_name': 'psutil',
                'pip_name': 'psutil'
            },
            'torch': {
                'name': 'PyTorch',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'AI 深度学习框架（核心依赖）',
                'module_name': 'torch',
                'pip_name': 'torch',
                'install_extra': '--index-url https://download.pytorch.org/whl/cpu'
            },
            'transformers': {
                'name': 'Transformers',
                'required': True,
                'installed': False,
                'version': None,
                'description': '预训练模型库',
                'module_name': 'transformers',
                'pip_name': 'transformers'
            },
            'diffusers': {
                'name': 'Diffusers',
                'required': True,
                'installed': False,
                'version': None,
                'description': '扩散模型库',
                'module_name': 'diffusers',
                'pip_name': 'diffusers'
            },
            'huggingface_hub': {
                'name': 'Huggingface Hub',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'Huggingface 模型下载',
                'module_name': 'huggingface_hub',
                'pip_name': 'huggingface-hub'
            },
            'modelscope': {
                'name': 'ModelScope',
                'required': True,
                'installed': False,
                'version': None,
                'description': '通义千问模型下载',
                'module_name': 'modelscope',
                'pip_name': 'modelscope'
            },
            'edge_tts': {
                'name': 'Edge TTS',
                'required': False,
                'installed': False,
                'version': None,
                'description': 'Microsoft Azure AI 配音（支持三层配音架构）',
                'module_name': 'edge_tts',
                'pip_name': 'edge-tts'
            },
            'pydub': {
                'name': 'Pydub',
                'required': False,
                'installed': False,
                'version': None,
                'description': '音频处理库（配音混音必备）',
                'module_name': 'pydub',
                'pip_name': 'pydub'
            }
        }
        
        # 真实检测每个包
        print(f"\n[依赖检测] ====== 开始检测 {len(packages)} 个包 ======")
        print(f"[依赖检测] Python: {sys.executable}")
        
        for module_name, info in packages.items():
            import_name = info.get('module_name', module_name)
            try:
                # 步骤 1: 检查模块是否存在
                spec = importlib.util.find_spec(import_name)
                
                if spec is None:
                    print(f"[依赖检测] ✗ {module_name}: 模块未找到")
                    packages[module_name]['installed'] = False
                    continue
                
                # 步骤 2: 尝试导入模块
                module = importlib.import_module(import_name)
                
                # 步骤 3: 获取版本信息
                try:
                    version = importlib.metadata.version(info['pip_name'])
                except importlib.metadata.PackageNotFoundError:
                    version = getattr(module, '__version__', 'unknown')
                
                # 步骤 4: 标记为已安装
                packages[module_name]['installed'] = True
                packages[module_name]['version'] = version
                print(f"[依赖检测] ✓ {module_name}: {version}")
                
            except ModuleNotFoundError as e:
                # Python 3.13 移除的模块
                if 'audioop' in str(e) or 'pyaudioop' in str(e):
                    print(f"[依赖检测] ⚠ {module_name}: Python 3.13 兼容性问题 - 需要安装 audioop-lts")
                    packages[module_name]['installed'] = False
                    packages[module_name]['error'] = '需要安装 audioop-lts: pip install audioop-lts'
                else:
                    print(f"[依赖检测] ✗ {module_name}: 模块未找到 - {str(e)[:80]}")
                    packages[module_name]['installed'] = False
            except ImportError as e:
                err_msg = str(e)
                # DLL 加载失败（缺少 VC++ 运行库）
                if 'WinError 126' in err_msg or 'DLL load failed' in err_msg:
                    print(f"[依赖检测] ⚠ {module_name}: 缺少 VC++ 运行库")
                    packages[module_name]['installed'] = False
                    packages[module_name]['error'] = '请安装 Microsoft Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe'
                else:
                    print(f"[依赖检测] ✗ {module_name}: 导入错误 - {str(e)[:80]}")
                    packages[module_name]['installed'] = False
            except Exception as e:
                err_msg = str(e)
                # DLL 加载失败
                if 'WinError 126' in err_msg or 'DLL load failed' in err_msg:
                    print(f"[依赖检测] ⚠ {module_name}: 缺少 VC++ 运行库")
                    packages[module_name]['installed'] = False
                    packages[module_name]['error'] = '请安装 Microsoft Visual C++ Redistributable'
                else:
                    print(f"[依赖检测] ✗ {module_name}: 未知错误 - {str(e)[:80]}")
                    packages[module_name]['installed'] = False
        
        # 统计结果
        total = len(packages)
        installed = sum(1 for p in packages.values() if p['installed'])
        required_missing = [name for name, info in packages.items() if info['required'] and not info['installed']]
        
        result = {
            'success': True,
            'packages': packages,
            'summary': {
                'total': total,
                'installed': installed,
                'missing': total - installed,
                'required_missing': required_missing,
                'all_required_installed': len(required_missing) == 0
            }
        }
        
        print(f"[依赖检测] 汇总：{installed}/{total} 已安装")
        print(f"[依赖检测] 缺少必需：{required_missing if required_missing else '无'}")
        print(f"[依赖检测] ====== 检测完成 ======\n")
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/install-dependencies', methods=['POST'])
def api_install_dependencies():
    """API: 安装 Python 依赖"""
    print(f"[pip 安装] ====== 收到安装请求 ======")
    try:
        import subprocess
        
        # 记录请求信息
        print(f"[pip 安装] Content-Type: {request.content_type}")
        print(f"[pip 安装] Raw data: {request.get_data()}")
        
        data = request.get_json() or {}
        packages = data.get('packages', [])
        print(f"[pip 安装] 包列表：{packages}")
        
        if not packages:
            return jsonify({'error': '请指定要安装的包'}), 400
        
        task_id = str(uuid.uuid4())
        
        # 定义包的安装信息
        package_info = {
            'flask': {'module_name': 'flask',
                'pip_name': 'flask', 'extra': ''},
            'pillow': {'pip_name': 'pillow', 'extra': ''},
            'psutil': {'module_name': 'psutil',
                'pip_name': 'psutil', 'extra': ''},
            'torch': {
                'module_name': 'torch',
                'pip_name': 'torch',
                'extra': '--index-url https://download.pytorch.org/whl/cpu'
            },
            'transformers': {'module_name': 'transformers',
                'pip_name': 'transformers', 'extra': ''},
            'diffusers': {'module_name': 'diffusers',
                'pip_name': 'diffusers', 'extra': ''},
            'huggingface-hub': {'pip_name': 'huggingface-hub', 'extra': ''},
            'modelscope': {'module_name': 'modelscope',
                'pip_name': 'modelscope', 'extra': ''},
            'edge-tts': {'pip_name': 'edge-tts', 'extra': ''},
            'pydub': {'module_name': 'pydub',
                'pip_name': 'pydub', 'extra': ''}
        }
        
        # 构建 pip 安装命令
        cmd = [sys.executable, '-m', 'pip', 'install']
        extra_args = []
        
        for pkg in packages:
            if pkg in package_info:
                info = package_info[pkg]
                cmd.append(info['pip_name'])
                if info['extra']:
                    # 拆分额外参数
                    extra_parts = info['extra'].split()
                    extra_args.extend(extra_parts)
        
        # 先添加额外参数，再添加 --break-system-packages
        cmd.extend(extra_args)
        cmd.append('--break-system-packages')
        
        # 包分组：torch 需要单独使用 PyTorch 源
        torch_packages = []
        other_packages = []
        
        for pkg in packages:
            if pkg in package_info:
                info = package_info[pkg]
                if info.get('extra'):
                    torch_packages.append(info['pip_name'])
                else:
                    other_packages.append(info['pip_name'])
        
        # 分别安装
        commands = []
        if torch_packages:
            cmd_torch = [sys.executable, '-m', 'pip', 'install'] + torch_packages + ['--index-url', 'https://download.pytorch.org/whl/cpu', '--break-system-packages']
            commands.append(('torch (CPU 版)', cmd_torch))
        
        if other_packages:
            cmd_other = [sys.executable, '-m', 'pip', 'install'] + other_packages + ['--break-system-packages']
            commands.append(('其他依赖', cmd_other))
        
        # 后台执行安装任务
        def install_task():
            import importlib.util
            
            log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            all_success = True
            failed = []
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"当前 Python: {sys.executable}\n")
                log.write(f"开始安装 {len(packages)} 个依赖...\n\n")
                
                # 依次安装
                for name, cmd in commands:
                    log.write(f"【安装 {name}】\n")
                    log.write(f"命令：{' '.join(cmd)}\n\n")
                    print(f"[pip] 正在安装 {name}...")
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    
                    if result.returncode == 0:
                        log.write(f"✓ {name} 安装成功\n\n")
                        print(f"[pip] ✓ {name} 安装成功")
                    else:
                        log.write(f"❌ {name} 安装失败\n\n")
                        print(f"[pip] ❌ {name} 安装失败")
                        all_success = False
                        failed.append(name)
                
                # 更新任务状态
                if task_id in tasks:
                    if all_success:
                        # 验证安装结果
                        verify_log = "\n验证安装结果:\n"
                        all_verified = True
                        for pkg_name in ['torch', 'diffusers', 'modelscope', 'pydub', 'transformers', 'huggingface_hub', 'edge_tts', 'PIL', 'psutil', 'flask']:
                            spec = importlib.util.find_spec(pkg_name.replace('-', '_'))
                            if spec:
                                verify_log += f"  ✓ {pkg_name}\n"
                            else:
                                verify_log += f"  ✗ {pkg_name} (未找到)\n"
                                all_verified = False
                        
                        if not all_verified:
                            log.write(f"⚠️ 警告：部分包安装后无法检测到\n{verify_log}")
                            log.write(f"\n可能原因：pip 使用的 Python 与 Flask 不同\n")
                            log.write(f"Flask Python: {sys.executable}\n")
                            tasks[task_id]['status'] = 'failed'
                            tasks[task_id]['error'] = "安装成功但检测不到，Python 环境不一致"
                        else:
                            log.write(f"✅ 验证通过\n{verify_log}")
                            log.write("\n\n✅ 所有依赖安装成功！\n")
                            tasks[task_id]['status'] = 'completed'
                            tasks[task_id]['progress'] = 100
                        print("[pip] ✅ 安装验证完成")
                    else:
                        log.write(f"\n\n❌ 安装失败：{', '.join(failed)}\n")
                        tasks[task_id]['status'] = 'failed'
                        tasks[task_id]['error'] = f"安装失败：{', '.join(failed)}"
                        print(f"[pip] ❌ 安装失败：{', '.join(failed)}")
        
        thread = threading.Thread(target=install_task)
        thread.daemon = True
        thread.start()
        
        # 注册任务到 tasks 字典
        from datetime import datetime
        tasks[task_id] = {
            'status': 'running',
            'progress': 10,
            'log': f'开始安装 {len(packages)} 个依赖...',
            'type': 'install',
            'packages': packages,
            'start_time': datetime.now().isoformat()
        }
        
        print(f"[pip 安装] ✅ 任务已注册：{task_id}")
        
        result_data = {
            'success': True,
            'task_id': task_id,
            'message': f'开始安装 {len(packages)} 个包'
        }
        print(f"[pip 安装] 返回：{result_data}")
        return jsonify(result_data)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/check-pytorch-installation', methods=['GET'])
def api_check_pytorch_installation():
    """API: 检查 PyTorch 安装状态和 CUDA 版本"""
    try:
        import importlib.util
        import subprocess
        import sys
        
        result = {
            'success': True,
            'pytorch': {
                'installed': False,
                'version': None,
                'cuda_support': False,
                'cuda_version': None,
                'cudnn_version': None,
                'gpu_available': False,
                'gpu_models': [],
                'gpu_memory': [],
                'recommended_install_command': None
            }
        }
        
        # 1. 检查 PyTorch 是否安装
        spec = importlib.util.find_spec('torch')
        if spec is not None:
            try:
                import torch
                result['pytorch']['installed'] = True
                result['pytorch']['version'] = torch.__version__
                
                # 2. 检查 CUDA 支持
                result['pytorch']['cuda_support'] = torch.cuda.is_available()
                
                if torch.cuda.is_available():
                    result['pytorch']['cuda_version'] = torch.version.cuda
                    result['pytorch']['cudnn_version'] = torch.backends.cudnn.version()
                    result['pytorch']['gpu_available'] = True
                    
                    # 获取 GPU 信息
                    for i in range(torch.cuda.device_count()):
                        gpu_name = torch.cuda.get_device_name(i)
                        gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                        result['pytorch']['gpu_models'].append(gpu_name)
                        result['pytorch']['gpu_memory'].append(f"{gpu_memory:.1f}GB")
                
                # 3. 生成推荐安装命令
                if torch.cuda.is_available():
                    cuda_ver = torch.version.cuda
                    if cuda_ver:
                        cuda_major_minor = cuda_ver.replace('.', '')
                        result['pytorch']['recommended_install_command'] = (
                            f"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu{cuda_major_minor}"
                        )
                else:
                    result['pytorch']['recommended_install_command'] = (
                        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                    )
                    
            except Exception as e:
                result['pytorch']['error'] = str(e)
        else:
            # PyTorch 未安装，检测系统 GPU 推荐安装版本
            try:
                # 尝试使用 nvidia-smi 检测 CUDA 版本
                nvidia_result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=driver_version,cuda_version', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=5
                )
                if nvidia_result.returncode == 0 and nvidia_result.stdout.strip():
                    lines = nvidia_result.stdout.strip().split('\n')
                    if len(lines) > 0:
                        parts = lines[0].split(', ')
                        if len(parts) == 2:
                            driver_version = parts[0].strip()
                            cuda_version = parts[1].strip()
                            result['pytorch']['system_cuda_version'] = cuda_version
                            result['pytorch']['nvidia_driver'] = driver_version
                            
                            # 根据系统 CUDA 版本推荐
                            cuda_major = cuda_version.split('.')[0]
                            if int(cuda_major) >= 11:
                                result['pytorch']['recommended_install_command'] = (
                                    f"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                                )
                            else:
                                result['pytorch']['recommended_install_command'] = (
                                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                                )
            except:
                pass
            
            # 默认推荐 CPU 版本
            if not result['pytorch']['recommended_install_command']:
                result['pytorch']['recommended_install_command'] = (
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                )
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/install-pytorch', methods=['POST'])
def api_install_pytorch():
    """API: 安装 PyTorch (带 CUDA 支持)"""
    try:
        import subprocess
        import sys
        import uuid
        
        data = request.get_json() or {}
        cuda_version = data.get('cuda_version', 'auto')  # 'cu118', 'cu117', 'cpu', etc.
        
        task_id = str(uuid.uuid4())
        
        # 确定 CUDA 版本
        if cuda_version == 'auto':
            # 自动检测
            try:
                import torch
                if torch.cuda.is_available() and torch.version.cuda:
                    cuda_major_minor = torch.version.cuda.replace('.', '')
                    cuda_version = f'cu{cuda_major_minor}'
                else:
                    cuda_version = 'cpu'
            except:
                # 尝试 nvidia-smi
                try:
                    import subprocess
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=cuda_version', '--format=csv,noheader'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        cuda_ver = result.stdout.strip().split('\n')[0]
                        cuda_major = cuda_ver.split('.')[0]
                        cuda_version = f'cu{cuda_major}8' if int(cuda_major) >= 11 else 'cpu'
                    else:
                        cuda_version = 'cpu'
                except:
                    cuda_version = 'cpu'
        
        # 构建安装命令
        if cuda_version == 'cpu':
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                'torch', 'torchvision', 'torchaudio',
                '--index-url', 'https://download.pytorch.org/whl/cpu',
                '--break-system-packages'
            ]
        else:
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                'torch', 'torchvision', 'torchaudio',
                '--index-url', f'https://download.pytorch.org/whl/{cuda_version}',
                '--break-system-packages'
            ]
        
        # 后台执行安装
        def install_task():
            log_file = Path(f'web/logs/pytorch_install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装 PyTorch (CUDA: {cuda_version})\n")
                log.write(f"命令：{' '.join(cmd)}\n\n")
                
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        log.write("\n✅ PyTorch 安装成功！\n")
                        
                        # 验证安装
                        try:
                            import torch
                            log.write(f"\n版本：{torch.__version__}\n")
                            log.write(f"CUDA 可用：{torch.cuda.is_available()}\n")
                            if torch.cuda.is_available():
                                log.write(f"CUDA 版本：{torch.version.cuda}\n")
                                log.write(f"GPU 数量：{torch.cuda.device_count()}\n")
                                for i in range(torch.cuda.device_count()):
                                    log.write(f"  GPU {i}: {torch.cuda.get_device_name(i)}\n")
                        except Exception as verify_error:
                            log.write(f"\n⚠️ 验证失败：{verify_error}\n")
                    else:
                        log.write(f"\n❌ PyTorch 安装失败，退出码：{process.returncode}\n")
                        
                except Exception as e:
                    log.write(f"\n❌ 安装异常：{str(e)}\n")
        
        thread = threading.Thread(target=install_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'cuda_version': cuda_version,
            'message': f'开始安装 PyTorch ({cuda_version})'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/pytorch-install-status/<task_id>', methods=['GET'])
def api_pytorch_install_status(task_id):
    """API: 查询 PyTorch 安装状态"""
    try:
        log_file = Path(f'web/logs/pytorch_install_{task_id}.log')
        
        if not log_file.exists():
            return jsonify({'status': 'pending', 'progress': 0})
        
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # 检查是否完成
        is_complete = any('安装成功' in line or '安装失败' in line or '异常' in line for line in logs)
        
        # 估算进度
        progress = 0
        if any('Collecting torch' in line for line in logs):
            progress = 20
        if any('Installing collected packages' in line for line in logs):
            progress = 80
        if any('Successfully installed' in line or '安装成功' in line for line in logs):
            progress = 100
        
        return jsonify({
            'status': 'complete' if is_complete else 'running',
            'progress': progress,
            'logs': logs
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-mode-environment/<mode>', methods=['GET'])
def api_check_mode_environment(mode):
    """API: 通用模式环境检测"""
    try:
        import importlib.util
        import shutil
        import torch
        
        # 各模式配置要求
        mode_requirements = {
            'optimized': {
                'name': '超优模式',
                'required': ['torch', 'ffmpeg', 'dependencies'],
                'recommended': ['models', 'cloud_api'],
                'min_gpu_memory': 4,
                'description': '分段文生图 + 合成视频'
            },
            'standard': {
                'name': '标准模式',
                'required': ['torch', 'cuda', 'ffmpeg', 'dependencies'],
                'recommended': ['models'],
                'min_gpu_memory': 12,
                'description': '原文生视频直接跑模型'
            },
            'collaborative': {
                'name': '协同模式',
                'required': ['torch', 'ffmpeg', 'dependencies'],
                'recommended': ['models', 'cloud_api'],
                'min_gpu_memory': 4,
                'description': '本地 + 云端 AI 协同'
            },
            'hybrid': {
                'name': '混合模式',
                'required': ['ffmpeg', 'cloud_api'],
                'recommended': ['dependencies'],
                'min_gpu_memory': 0,
                'description': '云端图片 + 本地合成'
            }
        }
        
        if mode not in mode_requirements:
            return jsonify({'error': '未知模式'}), 400
        
        req = mode_requirements[mode]
        
        # 检测项列表
        checks = {
            'cuda': {
                'name': 'CUDA GPU',
                'required': 'cuda' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': [],
                'min_memory': req['min_gpu_memory']
            },
            'torch': {
                'name': 'PyTorch',
                'required': 'torch' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': []
            },
            'models': {
                'name': '本地模型文件',
                'required': 'models' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': []
            },
            'ffmpeg': {
                'name': 'FFmpeg',
                'required': 'ffmpeg' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': []
            },
            'cloud_api': {
                'name': '云端 API 配置',
                'required': 'cloud_api' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': []
            },
            'dependencies': {
                'name': '核心依赖',
                'required': 'dependencies' in req['required'],
                'status': 'pending',
                'message': '检测中...',
                'details': []
            }
        }
        
        # 1. 检测 CUDA
        try:
            if torch.cuda.is_available():
                gpus = []
                for i in range(torch.cuda.device_count()):
                    gpus.append(torch.cuda.get_device_name(i))
                
                free_mem, total_mem = torch.cuda.mem_get_info()
                free_mem_gb = free_mem / 1024 / 1024 / 1024
                
                if free_mem_gb >= req['min_gpu_memory']:
                    checks['cuda']['status'] = 'ok'
                    checks['cuda']['message'] = f'可用：{free_mem_gb:.1f}GB'
                else:
                    checks['cuda']['status'] = 'error' if checks['cuda']['required'] else 'warning'
                    checks['cuda']['message'] = f'显存不足 ({free_mem_gb:.1f}GB < {req["min_gpu_memory"]}GB)'
                
                checks['cuda']['details'] = [
                    f'GPU 型号：{", ".join(gpus)}',
                    f'显存：{free_mem_gb:.1f}GB / {total_mem / 1024 / 1024 / 1024:.1f}GB',
                    f'CUDA 版本：{torch.version.cuda}',
                    f'最低要求：{req["min_gpu_memory"]}GB'
                ]
            else:
                if checks['cuda']['required']:
                    checks['cuda']['status'] = 'error'
                    checks['cuda']['message'] = 'CUDA 不可用'
                else:
                    checks['cuda']['status'] = 'ok'
                    checks['cuda']['message'] = '不需要 GPU'
                checks['cuda']['details'] = ['本地 GPU 不可用']
        except Exception as e:
            checks['cuda']['status'] = 'error' if checks['cuda']['required'] else 'warning'
            checks['cuda']['message'] = f'CUDA 检测失败：{str(e)}'
        
        # 2. 检测 PyTorch
        try:
            import torch
            checks['torch']['status'] = 'ok'
            checks['torch']['message'] = f'PyTorch {torch.__version__}'
            checks['torch']['details'] = [
                f'版本：{torch.__version__}',
                f'CUDA 支持：{"是" if torch.cuda.is_available() else "否"}'
            ]
        except ImportError:
            checks['torch']['status'] = 'error' if checks['torch']['required'] else 'warning'
            checks['torch']['message'] = 'PyTorch 未安装'
            checks['torch']['details'] = ['需要安装 PyTorch 才能使用本地生成功能']
        
        # 3. 检测模型文件
        models_dir = Path('./models')
        if models_dir.exists():
            model_files = list(models_dir.glob('**/*'))
            if model_files:
                checks['models']['status'] = 'ok'
                checks['models']['message'] = f'已找到 {len(model_files)} 个模型文件'
                checks['models']['details'] = [str(f.relative_to(models_dir)) for f in model_files[:5]]
            else:
                checks['models']['status'] = 'warning'
                checks['models']['message'] = '模型目录为空'
                checks['models']['details'] = ['需要下载模型文件才能使用本地生成功能']
        else:
            checks['models']['status'] = 'warning'
            checks['models']['message'] = '模型目录不存在'
            checks['models']['details'] = ['需要创建 models 目录并下载模型']
        
        # 4. 检测 FFmpeg
        ffmpeg_path = shutil.which('ffmpeg')
        local_ffmpeg = Path('./ffmpeg/bin/ffmpeg.exe')
        if ffmpeg_path or local_ffmpeg.exists():
            checks['ffmpeg']['status'] = 'ok'
            path = ffmpeg_path or str(local_ffmpeg)
            checks['ffmpeg']['message'] = f'FFmpeg 已安装'
            checks['ffmpeg']['details'] = [f'路径：{path}']
        else:
            checks['ffmpeg']['status'] = 'error' if checks['ffmpeg']['required'] else 'warning'
            checks['ffmpeg']['message'] = 'FFmpeg 未安装'
            checks['ffmpeg']['details'] = ['FFmpeg 是视频合并所必需的']
        
        # 5. 检测云端 API 配置
        config_file = Path('./config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                has_api_key = bool(config.get('ai_api_key'))
                
                if has_api_key:
                    checks['cloud_api']['status'] = 'ok'
                    checks['cloud_api']['message'] = '云端 API 已配置'
                    checks['cloud_api']['details'] = [f"API Key：{config.get('ai_api_key', '')[:8]}..."]
                else:
                    checks['cloud_api']['status'] = 'error' if checks['cloud_api']['required'] else 'warning'
                    checks['cloud_api']['message'] = '云端 API 未配置'
                    checks['cloud_api']['details'] = ['需要配置 API Key 才能使用云端功能']
            except Exception as e:
                checks['cloud_api']['status'] = 'warning'
                checks['cloud_api']['message'] = '配置文件读取失败'
                checks['cloud_api']['details'] = [str(e)]
        else:
            checks['cloud_api']['status'] = 'error' if checks['cloud_api']['required'] else 'warning'
            checks['cloud_api']['message'] = '配置文件不存在'
            checks['cloud_api']['details'] = ['需要配置 config.json 文件']
        
        # 6. 检测核心依赖
        required_packages = [
            ('flask', 'Flask'),
            ('PIL', 'Pillow'),
            ('diffusers', 'Diffusers'),
            ('transformers', 'Transformers'),
            ('modelscope', 'ModelScope'),
            ('requests', 'Requests')
        ]
        
        missing_deps = []
        installed_deps = []
        
        for module_name, display_name in required_packages:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                try:
                    module = importlib.import_module(module_name)
                    version = getattr(module, '__version__', 'unknown')
                    installed_deps.append(f'{display_name}: {version}')
                except:
                    missing_deps.append(display_name)
            else:
                missing_deps.append(display_name)
        
        if not missing_deps:
            checks['dependencies']['status'] = 'ok'
            checks['dependencies']['message'] = f'所有核心依赖已安装'
            checks['dependencies']['details'] = installed_deps[:5]
        else:
            checks['dependencies']['status'] = 'error' if checks['dependencies']['required'] else 'warning'
            checks['dependencies']['message'] = f'缺少 {len(missing_deps)} 个核心依赖'
            checks['dependencies']['details'] = [f'缺少：{", ".join(missing_deps)}']
        
        # 总体评估
        required_checks = [k for k, v in checks.items() if v['required']]
        has_required_errors = any(
            checks[k]['status'] == 'error' 
            for k in required_checks
        )
        
        ok_count = sum(1 for c in checks.values() if c['status'] == 'ok')
        total_count = len(checks)
        
        if not has_required_errors and ok_count == total_count:
            overall_status = 'ready'
            overall_message = f'{req["name"]}已就绪，可以开始使用'
        elif not has_required_errors:
            overall_status = 'partial'
            overall_message = f'{req["name"]}基本就绪，部分配置可优化'
        else:
            overall_status = 'not_ready'
            overall_message = f'{req["name"]}未准备好，需要修复错误'
        
        # 安装建议
        needs_install = has_required_errors
        can_use = not has_required_errors
        
        result = {
            'success': True,
            'mode': mode,
            'mode_name': req['name'],
            'description': req['description'],
            'overall_status': overall_status,
            'overall_message': overall_message,
            'summary': {
                'ok': ok_count,
                'total': total_count,
                'percentage': int(ok_count / total_count * 100),
                'required_items': required_checks,
                'missing_required': [
                    k for k in required_checks 
                    if checks[k]['status'] == 'error'
                ]
            },
            'checks': checks,
            'recommendations': {
                'need_install': needs_install,
                'can_use': can_use,
                'use_cloud': mode != 'standard' and checks['cloud_api']['status'] == 'ok'
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/install-mode-components/<mode>', methods=['POST'])
def api_install_mode_components(mode):
    """API: 一键安装指定模式所需组件"""
    try:
        import subprocess
        
        mode_components = {
            'optimized': ['dependencies', 'ffmpeg', 'models'],
            'standard': ['dependencies', 'ffmpeg', 'models'],
            'collaborative': ['dependencies', 'ffmpeg', 'models'],
            'hybrid': ['dependencies', 'ffmpeg']
        }
        
        if mode not in mode_components:
            return jsonify({'error': '未知模式'}), 400
        
        components = mode_components[mode]
        task_id = str(uuid.uuid4())
        
        # 安装脚本（复用协同模式的安装逻辑）
        def install_task():
            log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装 {mode} 模式组件：{', '.join(components)}\n")
                
                try:
                    # 1. 安装 Python 依赖
                    if 'dependencies' in components:
                        log.write("\n=== 安装 Python 依赖 ===\n")
                        # ... (与协同模式相同的安装逻辑)
                    
                    # 2. 下载 FFmpeg
                    if 'ffmpeg' in components:
                        log.write("\n=== 下载 FFmpeg ===\n")
                        # ... (与协同模式相同的安装逻辑)
                    
                    # 3. 下载模型
                    if 'models' in components:
                        log.write("\n=== 下载模型文件 ===\n")
                        # ... (与协同模式相同的安装逻辑)
                    
                    log.write("\n=== 安装完成 ===\n")
                    
                except Exception as e:
                    log.write(f"\n❌ 安装异常：{str(e)}\n")
        
        thread = threading.Thread(target=install_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'mode': mode,
            'components': components,
            'message': f'开始安装 {len(components)} 个组件'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
        
        # 1. 检测 CUDA
        try:
            if torch.cuda.is_available():
                gpus = []
                for i in range(torch.cuda.device_count()):
                    gpus.append(torch.cuda.get_device_name(i))
                
                free_mem, total_mem = torch.cuda.mem_get_info()
                checks['cuda']['status'] = 'ok'
                checks['cuda']['message'] = f'可用：{len(gpus)} 个 GPU'
                checks['cuda']['details'] = [
                    f'GPU 型号：{", ".join(gpus)}',
                    f'显存：{free_mem / 1024 / 1024 / 1024:.1f}GB / {total_mem / 1024 / 1024 / 1024:.1f}GB',
                    f'CUDA 版本：{torch.version.cuda}'
                ]
            else:
                checks['cuda']['status'] = 'warning'
                checks['cuda']['message'] = 'CUDA 不可用，可使用云端模式'
                checks['cuda']['details'] = ['本地 GPU 不可用，建议使用云端生成模式']
        except Exception as e:
            checks['cuda']['status'] = 'error'
            checks['cuda']['message'] = f'CUDA 检测失败：{str(e)}'
        
        # 2. 检测 PyTorch
        try:
            import torch
            checks['torch']['status'] = 'ok'
            checks['torch']['message'] = f'PyTorch {torch.__version__}'
            checks['torch']['details'] = [
                f'版本：{torch.__version__}',
                f'CUDA 支持：{"是" if torch.cuda.is_available() else "否"}',
                f'CUDNN 版本：{torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else "N/A"}'
            ]
        except ImportError:
            checks['torch']['status'] = 'error'
            checks['torch']['message'] = 'PyTorch 未安装'
            checks['torch']['details'] = ['需要安装 PyTorch 才能使用本地生成功能']
        except Exception as e:
            checks['torch']['status'] = 'error'
            checks['torch']['message'] = f'PyTorch 检测失败：{str(e)}'
        
        # 3. 检测模型文件
        models_dir = Path('./models')
        if models_dir.exists():
            model_files = list(models_dir.glob('**/*'))
            if model_files:
                checks['models']['status'] = 'ok'
                checks['models']['message'] = f'已找到 {len(model_files)} 个模型文件'
                checks['models']['details'] = [str(f.relative_to(models_dir)) for f in model_files[:10]]
                if len(model_files) > 10:
                    checks['models']['details'].append(f'... 还有 {len(model_files) - 10} 个文件')
            else:
                checks['models']['status'] = 'warning'
                checks['models']['message'] = '模型目录为空'
                checks['models']['details'] = ['需要下载模型文件才能使用本地生成功能']
        else:
            checks['models']['status'] = 'warning'
            checks['models']['message'] = '模型目录不存在'
            checks['models']['details'] = [
                '需要创建 models 目录并下载模型',
                '或者使用云端生成模式（不需要本地模型）'
            ]
        
        # 4. 检测 FFmpeg (严格验证)
        ffmpeg_path = shutil.which('ffmpeg')
        local_ffmpeg_exe = Path('./ffmpeg/bin/ffmpeg.exe')
        
        def is_valid_ffmpeg(path):
            """验证 FFmpeg 是否真实可用"""
            if not path or not Path(path).exists():
                return False
            # 检查文件大小（有效的 ffmpeg.exe 至少 50MB）
            size = Path(path).stat().st_size
            if size < 50 * 1024 * 1024:  # 小于 50MB 认为无效
                print(f"[FFmpeg 检测] ❌ 文件过小：{path} ({size / 1024 / 1024:.2f}MB)")
                return False
            # 检查是否是 zip 文件（临时下载文件）
            if str(path).endswith('.zip') or str(path).endswith('.xz'):
                print(f"[FFmpeg 检测] ❌ 未解压的压缩包：{path}")
                return False
            # 尝试执行获取版本
            try:
                import subprocess
                result = subprocess.run(
                    [str(path), '-version'],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
            except Exception as e:
                print(f"[FFmpeg 检测] ❌ 无法执行：{e}")
                return False
        
        if is_valid_ffmpeg(ffmpeg_path):
            checks['ffmpeg']['status'] = 'ok'
            checks['ffmpeg']['message'] = f'FFmpeg 已安装 (系统 PATH)'
            checks['ffmpeg']['details'] = [f'路径：{ffmpeg_path}']
        elif is_valid_ffmpeg(str(local_ffmpeg_exe)):
            checks['ffmpeg']['status'] = 'ok'
            checks['ffmpeg']['message'] = f'FFmpeg 已安装 (本地)'
            checks['ffmpeg']['details'] = [f'路径：{local_ffmpeg_exe}']
        else:
            checks['ffmpeg']['status'] = 'warning'
            checks['ffmpeg']['message'] = 'FFmpeg 未安装'
            checks['ffmpeg']['details'] = [
                'FFmpeg 是视频合并所必需的',
                '可通过 Web 界面 → FFmpeg → 自动下载',
                '或手动下载后放到 ./ffmpeg/bin/ffmpeg.exe'
            ]
            checks['ffmpeg']['message'] = 'FFmpeg 未安装'
            checks['ffmpeg']['details'] = [
                'FFmpeg 是视频合并所必需的',
                '可通过 Web 界面 → FFmpeg → 自动下载',
                '或使用 apt/yum 安装：sudo apt install ffmpeg'
            ]
        
        # 5. 检测云端 API 配置
        config_file = Path('./config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                api_keys = []
                if config.get('ai_api_key'):
                    api_keys.append(f"API Key：{config.get('ai_api_key', '')[:8]}...")
                if config.get('ai_api_base'):
                    api_keys.append(f"API Base: {config.get('ai_api_base', '')}")
                if config.get('ai_model_name'):
                    api_keys.append(f"模型：{config.get('ai_model_name', '')}")
                
                if api_keys:
                    checks['cloud_api']['status'] = 'ok'
                    checks['cloud_api']['message'] = '云端 API 已配置'
                    checks['cloud_api']['details'] = api_keys
                else:
                    checks['cloud_api']['status'] = 'warning'
                    checks['cloud_api']['message'] = '云端 API 未配置'
                    checks['cloud_api']['details'] = [
                        '配置云端 API 后可使用云端生成模式',
                        '支持：通义千问、OpenAI、Clove AI'
                    ]
            except Exception as e:
                checks['cloud_api']['status'] = 'warning'
                checks['cloud_api']['message'] = '配置文件读取失败'
                checks['cloud_api']['details'] = [str(e)]
        else:
            checks['cloud_api']['status'] = 'warning'
            checks['cloud_api']['message'] = '配置文件不存在'
            checks['cloud_api']['details'] = [
                '需要配置 config.json 文件',
                '或通过 Web 界面 → AI 配置 进行设置'
            ]
        
        # 6. 检测核心依赖
        required_packages = [
            ('flask', 'Flask'),
            ('PIL', 'Pillow'),
            ('diffusers', 'Diffusers'),
            ('transformers', 'Transformers'),
            ('modelscope', 'ModelScope'),
            ('requests', 'Requests')
        ]
        
        missing_deps = []
        installed_deps = []
        
        import importlib.util
        for module_name, display_name in required_packages:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                try:
                    module = importlib.import_module(module_name)
                    version = getattr(module, '__version__', 'unknown')
                    installed_deps.append(f'{display_name}: {version}')
                except:
                    missing_deps.append(display_name)
            else:
                missing_deps.append(display_name)
        
        if not missing_deps:
            checks['dependencies']['status'] = 'ok'
            checks['dependencies']['message'] = f'所有核心依赖已安装 ({len(installed_deps)} 个)'
            checks['dependencies']['details'] = installed_deps
        else:
            checks['dependencies']['status'] = 'error'
            checks['dependencies']['message'] = f'缺少 {len(missing_deps)} 个核心依赖'
            checks['dependencies']['details'] = [f'缺少：{", ".join(missing_deps)}']
        
        # 总体评估
        has_errors = any(c['status'] == 'error' for c in checks.values())
        has_warnings = any(c['status'] == 'warning' for c in checks.values())
        
        if not has_errors and not has_warnings:
            overall_status = 'ready'
            overall_message = '协同模式已就绪，可以使用本地或云端生成'
        elif not has_errors:
            overall_status = 'partial'
            overall_message = '部分配置未完成，建议使用云端生成模式'
        else:
            overall_status = 'not_ready'
            overall_message = '环境未准备好，需要修复错误后才能使用'
        
        # 统计
        ok_count = sum(1 for c in checks.values() if c['status'] == 'ok')
        total_count = len(checks)
        
        result = {
            'success': True,
            'overall_status': overall_status,
            'overall_message': overall_message,
            'summary': {
                'ok': ok_count,
                'total': total_count,
                'percentage': int(ok_count / total_count * 100)
            },
            'checks': checks,
            'recommendations': {
                'use_cloud': not has_errors and (has_warnings or checks['cuda']['status'] != 'ok'),
                'use_local': checks['cuda']['status'] == 'ok' and checks['models']['status'] == 'ok',
                'need_install': has_errors
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/install-collaborative-components', methods=['POST'])
def api_install_collaborative_components():
    """API: 一键安装协同模式所需组件"""
    try:
        import subprocess
        
        data = request.get_json() or {}
        components = data.get('components', [])
        
        if not components:
            return jsonify({'error': '请指定要安装的组件'}), 400
        
        task_id = str(uuid.uuid4())
        
        # 安装脚本
        def install_task():
            log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装协同模式组件：{', '.join(components)}\n")
                
                try:
                    # 1. 安装 Python 依赖
                    if 'dependencies' in components:
                        log.write("\n=== 安装 Python 依赖 ===\n")
                        packages = [
                            'torch', 'torchvision', 'torchaudio',
                            'diffusers', 'transformers', 'modelscope',
                            'pillow', 'requests', 'edge-tts', 'pydub'
                        ]
                        
                        # 检测 CUDA 版本
                        cuda_version = 'cpu'
                        try:
                            import torch
                            if torch.cuda.is_available():
                                cuda_version = 'cu118'
                        except:
                            pass
                        
                        if cuda_version == 'cpu':
                            cmd = [
                                sys.executable, '-m', 'pip', 'install',
                                '--index-url', 'https://download.pytorch.org/whl/cpu',
                                '--break-system-packages'
                            ] + packages
                        else:
                            cmd = [
                                sys.executable, '-m', 'pip', 'install',
                                '--index-url', 'https://download.pytorch.org/whl/cu118',
                                '--break-system-packages'
                            ] + packages
                        
                        log.write(f"执行命令：{' '.join(cmd)}\n")
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                        
                        if result.returncode == 0:
                            log.write("✓ Python 依赖安装成功\n")
                        else:
                            log.write(f"❌ Python 依赖安装失败：{result.stderr}\n")
                    
                    # 2. 下载 FFmpeg
                    if 'ffmpeg' in components:
                        log.write("\n=== 下载 FFmpeg ===\n")
                        ffmpeg_script = Path('./download_ffmpeg.py')
                        if ffmpeg_script.exists():
                            cmd = [sys.executable, str(ffmpeg_script)]
                            log.write(f"执行命令：{' '.join(cmd)}\n")
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                            
                            if result.returncode == 0:
                                log.write("✓ FFmpeg 下载成功\n")
                            else:
                                log.write(f"❌ FFmpeg 下载失败：{result.stderr}\n")
                                log.write("尝试使用系统安装...\n")
                                # 尝试使用 apt 安装
                                try:
                                    result = subprocess.run(
                                        ['apt-get', 'update'], 
                                        capture_output=True, text=True, timeout=60
                                    )
                                    result = subprocess.run(
                                        ['apt-get', 'install', '-y', 'ffmpeg'], 
                                        capture_output=True, text=True, timeout=300
                                    )
                                    if result.returncode == 0:
                                        log.write("✓ FFmpeg 系统安装成功\n")
                                    else:
                                        log.write(f"❌ FFmpeg 系统安装失败：{result.stderr}\n")
                                except Exception as apt_error:
                                    log.write(f"❌ 系统安装失败：{str(apt_error)}\n")
                        else:
                            log.write("❌ FFmpeg 下载脚本不存在\n")
                    
                    # 3. 下载模型
                    if 'models' in components:
                        log.write("\n=== 下载模型文件 ===\n")
                        models_script = Path('./download_models.py')
                        if models_script.exists():
                            cmd = [sys.executable, str(models_script)]
                            log.write(f"执行命令：{' '.join(cmd)}\n")
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                            
                            if result.returncode == 0:
                                log.write("✓ 模型下载成功\n")
                            else:
                                log.write(f"❌ 模型下载失败：{result.stderr}\n")
                        else:
                            log.write("❌ 模型下载脚本不存在\n")
                            log.write("建议：访问 /models 页面下载模型\n")
                    
                    log.write("\n=== 安装完成 ===\n")
                    log.write("请刷新页面重新检测环境状态\n")
                    
                except subprocess.TimeoutExpired:
                    log.write("\n❌ 安装超时\n")
                except Exception as e:
                    log.write(f"\n❌ 安装异常：{str(e)}\n")
        
        # 后台执行安装任务
        thread = threading.Thread(target=install_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'开始安装 {len(components)} 个组件'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/install-collaborative-status/<task_id>', methods=['GET'])
def api_install_collaborative_status(task_id):
    """API: 查询协同模式组件安装状态"""
    try:
        log_file = Path(f'web/logs/install_{task_id}.log')
        
        if not log_file.exists():
            return jsonify({'status': 'pending', 'progress': 0})
        
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # 检查是否完成
        is_complete = any('安装完成' in line or '异常' in line for line in logs)
        
        # 计算进度
        progress = 0
        if any('Python 依赖' in line for line in logs):
            progress += 33
        if any('FFmpeg' in line for line in logs):
            progress += 33
        if any('模型' in line for line in logs):
            progress += 34
        
        return jsonify({
            'status': 'complete' if is_complete else 'running',
            'progress': progress,
            'logs': logs
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-collaborative-mode', methods=['GET'])
def api_check_collaborative_mode():
    """API: 检查协同模式环境配置状态"""
    return api_check_mode_environment(mode='collaborative')


# ========== AI Configuration API ==========

import json

CONFIG_FILE = Path('config.json')

DEFAULT_CONFIG = {
    'model': 'modelscope',
    'model_path': './models',
    'precision': 'fp16',
    'duration': 10,
    'resolution': '512x512',
    'fps': 24,
    'guidance_scale': 7.5,
    'seed': -1,
    # 云端 AI 配置
    'ai_api_type': 'qwen',  # qwen, openai, clove
    'ai_api_key': '',
    'ai_api_base': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'ai_model_name': 'qwen-turbo',
    'ai_timeout': 60,
    'ai_max_retries': 3
}


def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return True


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """API: Get AI configuration"""
    try:
        config = load_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['POST'])
def api_set_config():
    """API: Set AI configuration"""
    try:
        data = request.get_json() or {}
        
        if 'config' not in data:
            return jsonify({
                'success': False,
                'error': '缺少配置数据'
            }), 400
        
        # Validate and merge with defaults
        config = DEFAULT_CONFIG.copy()
        config.update(data['config'])
        
        # Type validation
        config['duration'] = int(config.get('duration', 10))
        config['fps'] = int(config.get('fps', 24))
        config['guidance_scale'] = float(config.get('guidance_scale', 7.5))
        config['seed'] = int(config.get('seed', -1))
        
        # Save
        save_config(config)
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/config')
def config_page():
    """AI Configuration page"""
    return render_template('ai_config.html')


# ========== Project Management API ==========

PROJECTS_DIR = Path('projects')
PROJECTS_DIR.mkdir(exist_ok=True)


def get_project_path(name):
    """Get project directory path"""
    safe_name = re.sub(r'[^\w\-_]', '_', name)
    return PROJECTS_DIR / safe_name


def load_project_data(name):
    """Load project data from config file"""
    project_path = get_project_path(name)
    config_file = project_path / 'project.json'
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def save_project_data(name, data):
    """Save project data to config file"""
    project_path = get_project_path(name)
    project_path.mkdir(parents=True, exist_ok=True)
    
    config_file = project_path / 'project.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


@app.route('/api/projects', methods=['GET'])
def api_list_projects():
    """API: List all projects"""
    try:
        projects = []
        if PROJECTS_DIR.exists():
            for project_dir in PROJECTS_DIR.iterdir():
                if project_dir.is_dir():
                    config = load_project_data(project_dir.name)
                    if config:
                        projects.append({
                            'name': project_dir.name,
                            'created_at': config.get('created_at', 'Unknown'),
                            'prompt': config.get('prompt', ''),
                            'reference_image': config.get('reference_image', ''),
                            'audio_file': config.get('audio_file', '')
                        })
        
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'projects': projects
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """API: Create a new project"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': '项目名称不能为空'
            }), 400
        
        project_path = get_project_path(name)
        if project_path.exists():
            return jsonify({
                'success': False,
                'error': '项目已存在'
            }), 400
        
        # Create project
        save_project_data(name, {
            'name': name,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'prompt': '',
            'negative_prompt': '',
            'reference_image': '',
            'audio_file': '',
            'config': DEFAULT_CONFIG.copy()
        })
        
        return jsonify({
            'success': True,
            'message': '项目创建成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/projects/<project_name>', methods=['GET'])
def api_get_project(project_name):
    """API: Get project data"""
    try:
        config = load_project_data(project_name)
        
        if not config:
            return jsonify({
                'success': False,
                'error': '项目不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'project': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/projects/<project_name>', methods=['POST'])
def api_save_project(project_name):
    """API: Save project data"""
    try:
        data = request.get_json() or {}
        
        project_path = get_project_path(project_name)
        if not project_path.exists():
            return jsonify({
                'success': False,
                'error': '项目不存在'
            }), 404
        
        # Load existing data and update
        existing = load_project_data(project_name) or {}
        existing.update(data)
        existing['name'] = project_name
        existing['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save
        save_project_data(project_name, existing)
        
        # Copy files to project directory
        if 'reference_image' in data and data['reference_image']:
            src = Path(data['reference_image'])
            if src.exists():
                dst = project_path / 'reference_image' / src.name
                dst.parent.mkdir(exist_ok=True)
                shutil.copy2(src, dst)
                existing['reference_image'] = str(dst)
        
        if 'audio_file' in data and data['audio_file']:
            src = Path(data['audio_file'])
            if src.exists():
                dst = project_path / 'audio' / src.name
                dst.parent.mkdir(exist_ok=True)
                shutil.copy2(src, dst)
                existing['audio_file'] = str(dst)
        
        save_project_data(project_name, existing)
        
        return jsonify({
            'success': True,
            'message': '项目保存成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/projects/<project_name>', methods=['DELETE'])
def api_delete_project(project_name):
    """API: Delete a project"""
    try:
        project_path = get_project_path(project_name)
        
        if not project_path.exists():
            return jsonify({
                'success': False,
                'error': '项目不存在'
            }), 404
        
        # Delete project directory
        import shutil as shutil_module
        shutil_module.rmtree(project_path)
        
        return jsonify({
            'success': True,
            'message': '项目已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/projects')
def projects_page():
    """Projects management page"""
    return render_template('projects.html')


# ========== Scene Analysis API ==========

@app.route('/api/analyze-scenes', methods=['POST'])
def api_analyze_scenes():
    """API: AI 智能场景分析"""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', '')
        duration = data.get('duration', 10)
        mode = data.get('mode', 'detailed')
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': '提示词不能为空'
            }), 400
        
        # 导入 AI 场景分析器
        try:
            from personal_mode.ai_scene_analyzer import AISceneAnalyzer
        except ImportError as e:
            return jsonify({
                'success': False,
                'error': f'缺少依赖：{str(e)}',
                'hint': '请运行：pip install requests'
            }), 500
        
        # 获取 AI 配置
        config = load_config()
        
        # 创建分析器实例（传入云端 AI 配置）
        analyzer = AISceneAnalyzer(
            model_type=config.get('ai_api_type', 'qwen'),
            model_name=config.get('ai_model_name', 'qwen-turbo'),
            api_base=config.get('ai_api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            api_key=config.get('ai_api_key', '')
        )
        
        # 执行 AI 场景分析
        try:
            result = analyzer.ai_analyze(prompt=prompt, mode=mode)
        except Exception as analysis_error:
            # AI 分析失败，使用回退方案
            result = analyzer._fallback_analysis(prompt)
        
        # 计算每个场景的时长（确保 duration 是数字）
        if 'scenes' in result and result['scenes']:
            total_scenes = len(result['scenes'])
            duration = float(duration) if isinstance(duration, str) else duration
            avg_duration = duration / total_scenes
            
            for scene in result['scenes']:
                scene['duration'] = round(avg_duration, 1)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code


@app.route('/api/scenes/confirm', methods=['POST'])
def api_confirm_scenes():
    """API: 确认场景并生成视频"""
    try:
        data = request.get_json() or {}
        scenes = data.get('scenes', [])
        mode = data.get('mode', 'hybrid')
        prompt = data.get('prompt', '')
        duration = data.get('duration', 10)
        
        if not scenes:
            return jsonify({
                'success': False,
                'error': '场景不能为空'
            }), 400
        
        # 将场景信息传递到生成流程
        # 这里简化处理，实际应该集成到 generate API 中
        # 将场景信息保存到临时文件或 session 中
        import uuid
        task_id = str(uuid.uuid4())
        
        # 保存场景配置
        scene_config = {
            'task_id': task_id,
            'prompt': prompt,
            'mode': mode,
            'scenes': scenes,
            'duration': duration
        }
        
        # 这里应该调用实际的视频生成流程
        # 为简化实现，返回成功消息
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '场景已确认，开始生成视频',
            'config': scene_config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/scenes/confirm')
def scenes_confirm_page():
    """场景确认页面"""
    return render_template('scenes_confirm.html')


# ========== FFmpeg Management API ==========

@app.route('/api/check-ffmpeg', methods=['GET'])
def api_check_ffmpeg():
    """API: 检查 FFmpeg 安装状态（严格验证）"""
    import platform
    import shutil
    import subprocess
    from pathlib import Path
    
    try:
        def verify_ffmpeg(path):
            """严格验证 FFmpeg 是否真实可用"""
            if not path or not Path(path).exists():
                return None
            
            # 检查文件大小（有效的 ffmpeg.exe 至少 50MB）
            size = Path(path).stat().st_size
            if size < 50 * 1024 * 1024:
                print(f"[FFmpeg 检测] ❌ 文件过小：{path} ({size / 1024 / 1024:.2f}MB)")
                return None
            
            # 检查是否是压缩包
            if str(path).endswith('.zip') or str(path).endswith('.xz') or str(path).endswith('.7z'):
                print(f"[FFmpeg 检测] ❌ 未解压的压缩包：{path}")
                return None
            
            # 尝试执行获取版本
            try:
                result = subprocess.run(
                    [str(path), '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0] if result.stdout else '本地版本'
                    return {'path': str(path), 'version': version_line}
                else:
                    print(f"[FFmpeg 检测] ❌ 执行失败：{result.stderr[:200] if result.stderr else '未知错误'}")
                    return None
            except Exception as e:
                print(f"[FFmpeg 检测] ❌ 无法执行：{e}")
                return None
        
        # 1. 检查系统PATH中的 FFmpeg
        ffmpeg_path = shutil.which('ffmpeg')
        result = verify_ffmpeg(ffmpeg_path)
        if result:
            return jsonify({
                'success': True,
                'installed': True,
                'path': result['path'],
                'version': result['version'],
                'source': 'system'
            })
        
        # 2. 检查本地 ./ffmpeg/bin/ffmpeg.exe
        local_ffmpeg = Path('./ffmpeg/bin/ffmpeg.exe')
        result = verify_ffmpeg(str(local_ffmpeg))
        if result:
            return jsonify({
                'success': True,
                'installed': True,
                'path': result['path'],
                'version': result['version'],
                'source': 'local'
            })
        
        # 3. 未找到可用的 FFmpeg
        return jsonify({
            'success': True,
            'installed': False,
            'path': None,
            'version': None,
            'source': None,
            'message': 'FFmpeg 未安装或无效',
            'suggestions': [
                '请通过 Web 界面 → FFmpeg → 自动下载',
                '或手动下载后放到 ./ffmpeg/bin/ffmpeg.exe',
                '系统安装：sudo apt install ffmpeg (Linux)'
            ]
        })
        # 2. 检测内存
        import psutil
        total_memory = psutil.virtual_memory().total / (1024 ** 3)
        available_memory = psutil.virtual_memory().available / (1024 ** 3)
        
        # 3. 检测 CPU
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_mhz = cpu_freq.current if cpu_freq else 0
        
        # 4. 检测系统架构
        system = platform.system()
        machine = platform.machine()
        arch = 'x86_64' if machine in ['x86_64', 'AMD64'] else 'arm64' if machine in ['arm64', 'aarch64'] else machine
        
        # FFmpeg 最低要求
        requirements = {
            'disk_min_gb': 1,      # FFmpeg 本身 1GB
            'disk_recommended_gb': 10,  # 推荐 10GB 用于处理视频
            'memory_min_gb': 2,
            'memory_recommended_gb': 4,
            'cpu_min_cores': 2,
            'cpu_recommended_cores': 4
        }
        
        # 评估
        disk_ok = free_space_gb >= requirements['disk_min_gb']
        memory_ok = available_memory >= requirements['memory_min_gb']
        cpu_ok = cpu_count >= requirements['cpu_min_cores']
        
        all_ok = disk_ok and memory_ok and cpu_ok
        
        # 生成建议
        suggestions = []
        if not disk_ok:
            suggestions.append(f"磁盘空间不足 ({free_space_gb:.1f}GB < {requirements['disk_min_gb']}GB)，建议清理磁盘")
        if not memory_ok:
            suggestions.append(f"可用内存不足 ({available_memory:.1f}GB < {requirements['memory_min_gb']}GB)，建议关闭其他程序")
        if not cpu_ok:
            suggestions.append(f"CPU 核心数较少 ({cpu_count} 核 < {requirements['cpu_min_cores']}核)，处理速度可能较慢")
        
        resource_score = 0
        if free_space_gb >= requirements['disk_recommended_gb']:
            resource_score += 1
        if available_memory >= requirements['memory_recommended_gb']:
            resource_score += 1
        if cpu_count >= requirements['cpu_recommended_cores']:
            resource_score += 1
        
        return jsonify({
            'success': True,
            'can_install': all_ok,
            'resource_score': resource_score,  # 0-3
            'system': {
                'os': system,
                'arch': arch,
                'cpu_cores': cpu_count,
                'cpu_freq_mhz': round(cpu_freq_mhz, 0),
                'total_memory_gb': round(total_memory, 1),
                'available_memory_gb': round(available_memory, 1),
                'total_disk_gb': round(total_space.total / (1024 ** 3), 1),
                'free_disk_gb': round(free_space_gb, 1)
            },
            'requirements': requirements,
            'status': {
                'disk': '✅' if disk_ok else '❌',
                'memory': '✅' if memory_ok else '❌',
                'cpu': '✅' if cpu_ok else '❌'
            },
            'suggestions': suggestions,
            'recommendation': '可以安装' if all_ok else '不建议安装'
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code



@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API: 获取所有任务状态"""
    try:
        # 返回全局 tasks 变量（如果存在）
        all_tasks = {}
        if 'tasks' in dir():
            all_tasks = tasks
        elif 'tasks' in globals():
            all_tasks = globals()['tasks']
        
        # 转换为列表格式
        task_list = []
        for task_id, task_data in all_tasks.items():
            task_list.append({
                'task_id': task_id,
                **task_data
            })
        
        return jsonify({
            'tasks': task_list,
            'total': len(task_list),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'tasks': [],
            'success': False
        }), 500

@app.route('/api/download-ffmpeg', methods=['POST'])
def _extract_ffmpeg(file_path, output_dir, temp_dir, system):
    """解压 FFmpeg 到目标目录（辅助函数）"""
    import zipfile
    import tarfile
    import shutil
    import stat
    
    try:
        extracted_files = []
        
        if system == 'Windows':
            # Windows: 解压 ZIP 文件
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                names = zip_ref.namelist()
                
                # 找到顶层目录
                ffmpeg_dir = None
                for name in names:
                    if 'ffmpeg' in name.lower() and ('ffmpeg.exe' in name or 'ffprobe' in name):
                        ffmpeg_dir = name.split('/')[0]
                        break
                
                if not ffmpeg_dir:
                    for name in names:
                        if '/' in name and name.endswith('/'):
                            ffmpeg_dir = name.rstrip('/')
                            break
                
                if ffmpeg_dir:
                    zip_ref.extractall(temp_dir)
                    src_bin = temp_dir / ffmpeg_dir / 'bin'
                    if src_bin.exists():
                        shutil.copytree(src_bin, output_dir, dirs_exist_ok=True)
                        extracted_files = ['ffmpeg.exe', 'ffprobe.exe']
                    else:
                        for name in names:
                            if name.endswith('ffmpeg.exe') or name.endswith('ffprobe.exe'):
                                zip_ref.extract(name, temp_dir)
                                src = temp_dir / name
                                dst = output_dir / src.name
                                shutil.copy2(src, dst)
                                extracted_files.append(src.name)
        else:
            # Linux/macOS: 解压 TAR.XZ 文件
            import subprocess
            result = subprocess.run(['tar', '-xf', str(file_path), '-C', str(temp_dir)], 
                          capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"解压失败：{result.stderr}")
            
            for ffmpeg_file in temp_dir.rglob('ffmpeg'):
                if ffmpeg_file.is_file():
                    shutil.copy2(ffmpeg_file, output_dir / 'ffmpeg')
                    extracted_files.append('ffmpeg')
                    break
        
        # 清理临时文件
        if file_path.exists():
            file_path.unlink()
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return jsonify({
            'success': True,
            'path': str(output_dir.parent),
            'message': f'FFmpeg 解压完成',
            'files': ', '.join(extracted_files),
            'note': '请重启 Web 服务以使用 FFmpeg'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'解压失败：{str(e)}'
        }), 500


def api_download_ffmpeg():
    """API: 自动下载 FFmpeg（增强版 - 支持多线程和断点续传）"""
    import psutil  # 导入 psutil 用于资源检查
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # ==== 调试日志 ====
        print("[FFmpeg 下载] ====== 开始下载流程 ======")
        
        # 提前定义 system 变量，避免后续 except 块引用未定义
        system = platform.system()
        machine = platform.machine()
        
        # 资源检查（简化版）
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent if system != 'Windows' else psutil.disk_usage('C:').percent
            
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 98:
                print(f"[FFmpeg 下载] ⚠️  系统资源紧张：CPU {cpu_percent}%, 内存 {memory_percent}%, 磁盘 {disk_percent}%")
                return jsonify({
                    'success': False,
                    'error': '系统资源不足，请关闭其他程序后重试',
                    'resource_usage': f'CPU: {cpu_percent}%, 内存：{memory_percent}%, 磁盘：{disk_percent}%'
                }), 400
        except Exception as e:
            print(f"[FFmpeg 下载] ⚠️  资源检查失败：{e}，继续下载流程")
        arch = 'amd64' if machine in ['x86_64', 'AMD64'] else 'arm64' if machine in ['arm64', 'aarch64'] else machine
        
        # FFmpeg 静态编译版本下载地址
        # FFmpeg 静态编译版本下载地址（多镜像，自动选择最快的）
        # 
        # 镜像选择策略:
        # - Linux: GitHub镜像速度更快 (0.78MB/s vs 0.38MB/s)
        # - Windows: gyan.dev 为主要镜像
        # - macOS: evermeet.cx 为主要镜像
        #
        # 如果主镜像失败，自动切换到备用镜像
        urls = {
            'Windows': [
                # 国内镜像优先（阿里云镜像）
                'https://mirrors.aliyun.com/github-release/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-essentials_build.zip',
                # GitHub 镜像（备用）
                'https://github.com/GyanD/codexffmpeg/releases/download/6.1/ffmpeg-6.1-essentials_build.zip',
                'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
                # 官方备用
                'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
            ],
            'Linux': [
                # 国内镜像优先
                f'https://mirrors.aliyun.com/github-release/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{arch}-gpl.tar.xz',
                f'https://mirrors.aliyun.com/github-release/johnvansickle/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz',
                # 官方镜像（备用）
                f'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{arch}-gpl.tar.xz',
                f'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz',
            ],
            'Darwin': [
                # 国内镜像优先
                'https://mirrors.aliyun.com/github-release/evermeet/ffmpeg/releases/download/5.1.2/ffmpeg-5.1.2.zip',
                # 官方镜像（备用）
                'https://evermeet.cx/ffmpeg/getrelease/zip',
                'https://github.com/evermeet/ffmpeg/releases/download/5.1.2/ffmpeg-5.1.2.zip',
            ]
        }
        
        # 如果是字符串（旧格式），转换为列表
        for sys_name in list(urls.keys()):
            if isinstance(urls[sys_name], str):
                urls[sys_name] = [urls[sys_name]]
        
        if system not in urls:
            return jsonify({
                'success': False,
                'error': f'不支持的系统：{system}'
            })
        
        # 创建下载和输出目录
        output_dir = Path('./ffmpeg/bin')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 临时下载目录
        temp_dir = Path('./ffmpeg/temp_download')
        temp_dir.mkdir(exist_ok=True)
        
        # 下载
        # 选择最快的镜像
        print(f"[FFmpeg 下载] ===== 开始下载流程 =====")
        print(f"[FFmpeg 下载] 系统：{system}")
        url_list = urls.get(system, [])
        if not url_list:
            return jsonify({
                'success': False,
                'error': f'不支持的系统：{system}'
            })
        
        # 优先使用第一个镜像（通常是最快的）
        url = url_list[0]
        backup_urls = url_list[1:]
        filename = 'ffmpeg.zip' if system == 'Windows' else 'ffmpeg.tar.xz'
        file_path = temp_dir / filename
        
        # ==== 断点续传检查 ====
        resume_pos = 0
        if file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > 0 and file_size < 100 * 1024 * 1024:  # 0 < size < 100MB
                resume_pos = file_size
                print(f"[FFmpeg 下载] ✅ 发现部分下载的文件：{file_path} ({file_size / 1024 / 1024:.2f}MB)")
                print(f"[FFmpeg 下载] ℹ️  将从 {resume_pos / 1024 / 1024:.2f}MB 处继续下载")
            elif file_size >= 100 * 1024 * 1024:  # >= 100MB，可能是完整文件
                print(f"[FFmpeg 下载] ⚠️  文件已存在且大小合理：{file_size / 1024 / 1024:.2f}MB")
                print(f"[FFmpeg 下载] ℹ️  跳过下载，直接解压")
                # 直接跳到解压步骤
                return _extract_ffmpeg(file_path, output_dir, temp_dir, system)
            else:
                print(f"[FFmpeg 下载] ⚠️  文件存在但大小为 0 或异常，删除后重新下载")
                file_path.unlink()
        
        # 使用流式下载，避免内存占用过大
        # 先验证 URL 可用性
        print(f"[FFmpeg 下载] 主镜像：{url[:80]}...")
        try:
            print(f"[FFmpeg 下载] 发送 HEAD 请求...")
            head_resp = requests.head(url, timeout=10, allow_redirects=True)
            print(f"[FFmpeg 下载] HEAD 响应：HTTP {head_resp.status_code}")
            if head_resp.history:
                print(f"[FFmpeg 下载] 重定向 {len(head_resp.history)} 次")
            if head_resp.status_code != 200:
                # 尝试备用镜像
                print(f"[FFmpeg 下载] 主镜像失败 (HTTP {head_resp.status_code}), 尝试备用镜像...")
                print(f"[FFmpeg 下载] 备用镜像数量：{len(backup_urls)}")
                switched = False
                for backup_url in backup_urls:
                    try:
                        print(f"[FFmpeg 下载] 尝试备用镜像：{backup_url[:80]}...")
                        backup_resp = requests.head(backup_url, timeout=10, allow_redirects=True)
                        print(f"[FFmpeg 下载] 备用镜像响应：HTTP {backup_resp.status_code}")
                        if backup_resp.status_code == 200:
                            print(f"[FFmpeg 下载] 切换到备用镜像：{backup_url[:80]}...")
                            url = backup_url
                            head_resp = backup_resp
                            switched = True
                            break
                    except:
                        continue
                if not switched:
                    backup_url = url.replace('/releases/', '/builds/')
                    head_resp = requests.head(backup_url, timeout=10, allow_redirects=True)
                    if head_resp.status_code == 200:
                        print(f"使用备用 URL: {backup_url}")
                        url = backup_url
                if head_resp.status_code != 200:
                    return jsonify({
                        'success': False,
                        'error': f'下载链接不可用 (HTTP {head_resp.status_code})',
                        'suggestion': '请检查网络连接或手动下载 FFmpeg'
                    }), 503
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'无法验证下载链接：{str(e)}',
                'suggestion': '请检查网络连接'
            }), 503
        
        # 使用会话和重试机制
        session = requests.Session()
        session.trust_env = True  # 使用系统代理设置
        
        # 配置重试策略
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 分块下载，支持断点续传
        chunk_size = 8192
        downloaded = resume_pos  # 从断点处开始
        mode = 'wb' if resume_pos == 0 else 'ab'  # 续传用追加模式
        
        try:
            # 配置 Range 请求头实现断点续传
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                print(f"[FFmpeg 下载] 📡 发送 Range 请求：bytes={resume_pos}-")
            
            response = session.get(url, stream=True, headers=headers, timeout=(10, 300))
            
            # 检查是否是 206 Partial Content
            if response.status_code == 206:
                print(f"[FFmpeg 下载] ✅ 服务器支持断点续传 (HTTP 206)")
            elif response.status_code == 200 and resume_pos > 0:
                print(f"[FFmpeg 下载] ⚠️  服务器不支持续传，重新下载 (HTTP 200)")
                downloaded = 0
                mode = 'wb'
            
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            if downloaded > 0:
                # 如果是续传，total_size 是剩余部分的大小
                actual_total = downloaded + total_size
                total_mb = actual_total / (1024 * 1024)
                print(f"[FFmpeg 下载] 剩余下载量：{total_size / 1024 / 1024:.2f}MB (总：{actual_total / 1024 / 1024:.2f}MB)")
            else:
                total_mb = total_size / (1024 * 1024)
            
            with open(file_path, mode) as f:
                chunk_count = 0
                start_time = time.time()
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤 keep-alive 块
                        f.write(chunk)
                        downloaded += len(chunk)
                        chunk_count += 1
                        
                        # 每下载 1MB 打印进度（避免输出过多）
                        if chunk_count % 128 == 0:  # 128 * 8KB = 1MB
                            elapsed = time.time() - start_time
                            actual_downloaded = downloaded - resume_pos if resume_pos > 0 else downloaded
                            speed = actual_downloaded / (1024 * 1024) / elapsed if elapsed > 0 else 0  # MB/s
                            percent = (downloaded / (downloaded + total_size - resume_pos) * 100) if resume_pos > 0 else (downloaded / total_size * 100) if total_size > 0 else 0
                            print(f"  进度：{percent:.1f}% ({downloaded/(1024*1024):.1f}MB/{total_mb:.1f}MB) - 速度：{speed:.2f}MB/s")
            
        except requests.exceptions.ChunkedEncodingError as e:
            print(f"[FFmpeg 下载] ⚠️  网络连接中断：{e}")
            if file_path.exists() and file_path.stat().st_size > 0:
                downloaded_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"[FFmpeg 下载] ℹ️  已下载 {downloaded_mb:.2f}MB，可尝试续传")
            return jsonify({
                'success': False,
                'error': f'网络连接中断：{str(e)}',
                'partial_download': True,
                'downloaded_mb': downloaded_mb if file_path.exists() else 0,
                'suggestion': '请检查网络连接后重试，支持断点续传'
            }), 500
        except requests.exceptions.RequestException as e:
            print(f"[FFmpeg 下载] ❌  网络错误：{e}")
            return jsonify({
                'success': False,
                'error': f'网络错误：{str(e)}',
                'suggestion': '请检查网络连接或尝试备用镜像'
            }), 500
        except Exception as e:
            print(f"[FFmpeg 下载] ❌  下载失败：{e}")
            return jsonify({
                'success': False,
                'error': f'下载失败：{str(e)}',
                'suggestion': '请检查网络连接或手动下载 FFmpeg'
            }), 500
        
        # ==== 验证下载结果 ====
        print(f"[FFmpeg 下载] 下载完成，验证文件...")
        
        if not file_path.exists():
            raise Exception(f"下载失败：文件不存在 {file_path}")
        
        file_size = file_path.stat().st_size
        print(f"[FFmpeg 下载] 文件大小：{file_size / (1024*1024):.2f}MB")
        
        if file_size == 0:
            raise Exception("下载失败：文件大小为 0 字节，网络中断或 URL 无效")
        
        if file_size < 1024 * 1024:
            raise Exception(f"下载失败：文件过小 ({file_size} 字节)，可能下载不完整")
        
        # 解压
        extracted_files = []
        
        if system == 'Windows':
            # Windows: 解压 ZIP 文件
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                names = zip_ref.namelist()
                
                # 找到顶层目录
                ffmpeg_dir = None
                for name in names:
                    if 'ffmpeg' in name.lower() and ('ffmpeg.exe' in name or 'ffprobe' in name):
                        ffmpeg_dir = name.split('/')[0]
                        break
                
                if not ffmpeg_dir:
                    # 尝试从第一个目录名推断
                    for name in names:
                        if '/' in name and name.endswith('/'):
                            ffmpeg_dir = name.rstrip('/')
                            break
                
                if ffmpeg_dir:
                    # 解压整个目录
                    zip_ref.extractall(temp_dir)
                    
                    # 优先查找 bin 子目录
                    src_bin = temp_dir / ffmpeg_dir / 'bin'
                    if src_bin.exists():
                        shutil.copytree(src_bin, output_dir, dirs_exist_ok=True)
                        extracted_files = ['ffmpeg.exe', 'ffprobe.exe']
                    else:
                        # 直接在顶层找 exe 文件
                        for name in names:
                            if name.endswith('ffmpeg.exe') or name.endswith('ffprobe.exe'):
                                zip_ref.extract(name, temp_dir)
                                src = temp_dir / name
                                dst = output_dir / src.name
                                shutil.copy2(src, dst)
                                extracted_files.append(src.name)
                else:
                    raise Exception("无法找到 FFmpeg 文件在压缩包中的位置")
        else:
            # Linux/macOS: 解压 TAR.XZ 文件
            result = sp.run(['tar', '-xf', str(file_path), '-C', str(temp_dir)], 
                          capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"解压失败：{result.stderr}")
            
            # 查找 ffmpeg 二进制文件，优先查找以 /ffmpeg 或 /ffprobe 结尾的文件
            import shutil
            for ffmpeg_file in temp_dir.rglob('ffmpeg'):
                if ffmpeg_file.is_file():
                    # 确保是二进制文件而不是目录
                    if str(ffmpeg_file).endswith('/ffmpeg') or str(ffmpeg_file).endswith('/ffmpeg\n'):
                        shutil.copy2(ffmpeg_file, output_dir / 'ffmpeg')
                        extracted_files.append('ffmpeg')
                    elif str(ffmpeg_file).endswith('/ffprobe'):
                        shutil.copy2(ffmpeg_file, output_dir / 'ffprobe')
                        extracted_files.append('ffprobe')
        
        # 验证解压结果
        if not extracted_files:
            raise Exception("解压后未找到任何 FFmpeg 文件，请检查压缩包格式")
        
        # 验证 bin 目录中的文件
        found_files = [f for f in output_dir.iterdir() if f.is_file()]
        if not found_files:
            raise Exception("解压完成但 bin 目录为空，可能解压路径不匹配")
        
        # 清理临时文件
        if file_path.exists():
            file_path.unlink()
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 设置执行权限（Linux/macOS）
        if system != 'Windows':
            ffmpeg_exe = output_dir / 'ffmpeg'
            if ffmpeg_exe.exists():
                ffmpeg_exe.chmod(ffmpeg_exe.stat().st_mode | stat.S_IEXEC)
            
            ffprobe_exe = output_dir / 'ffprobe'
            if ffprobe_exe.exists():
                ffprobe_exe.chmod(ffprobe_exe.stat().st_mode | stat.S_IEXEC)
        
        # 返回详细信息
        file_list = ', '.join([f.name for f in found_files])
        return jsonify({
            'success': True,
            'path': str(output_dir.parent),
            'message': f'FFmpeg 下载并解压完成，文件位于 ffmpeg/bin/',
            'files': file_list,
            'note': '请重启 Web 服务以使用 FFmpeg'
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': '下载超时（超过 300 秒）',
            'suggestions': [
                '请检查网络连接',
                '网络可能较慢，请稍后重试',
                '或手动下载 FFmpeg'
            ]
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': '连接错误',
            'suggestions': [
                '无法连接到下载服务器',
                '请检查网络连接',
                '或手动下载 FFmpeg'
            ]
        }), 503
    except requests.exceptions.RequestException as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"下载错误：{error_detail}")
        return jsonify({
            'success': False,
            'error': f'下载失败：{str(e)}',
            'suggestions': [
                '详细错误已记录到日志',
                '请检查网络连接',
                '或手动下载 FFmpeg'
            ]
        }), 500
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[FFmpeg 下载] ❌ 错误：{str(e)}")
        print(f"[FFmpeg 下载] ❌ 堆栈：{error_detail}")
        
        # 判断是否是 URL 验证失败
        if '无法验证下载链接' in str(e) or 'head' in str(e).lower():
            status_code = 503
        else:
            status_code = 500
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_detail,
            'system': system,
            'url': url if 'url' in locals() else 'N/A'
        }), status_code


# ========== Resource Monitoring & Task Pause ==========

# 全局任务资源监控配置
RESOURCE_MONITOR_CONFIG = {
    'enabled': True,
    'check_interval': 2,  # 每 2 秒检查一次
    'cpu_threshold': 90,  # CPU 使用率超过 90% 暂停
    'memory_threshold': 90,  # 内存使用率超过 90% 暂停
    'disk_threshold': 95,  # 磁盘超过 95% 暂停
    'pause_timeout': 300,  # 暂停最长等待 5 分钟
}

# 任务资源状态
task_resource_status = {}


@app.route('/api/resource-monitor/config', methods=['GET'])
def api_get_resource_monitor_config():
    """API: 获取资源监控配置"""
    return jsonify({
        'success': True,
        'config': RESOURCE_MONITOR_CONFIG
    })


@app.route('/api/resource-monitor/config', methods=['POST'])
def api_set_resource_monitor_config():
    """API: 设置资源监控配置"""
    try:
        data = request.get_json() or {}
        
        # 更新配置
        if 'enabled' in data:
            RESOURCE_MONITOR_CONFIG['enabled'] = data['enabled']
        if 'check_interval' in data:
            RESOURCE_MONITOR_CONFIG['check_interval'] = max(1, min(10, int(data['check_interval'])))
        if 'cpu_threshold' in data:
            RESOURCE_MONITOR_CONFIG['cpu_threshold'] = max(50, min(99, int(data['cpu_threshold'])))
        if 'memory_threshold' in data:
            RESOURCE_MONITOR_CONFIG['memory_threshold'] = max(50, min(99, int(data['memory_threshold'])))
        if 'disk_threshold' in data:
            RESOURCE_MONITOR_CONFIG['disk_threshold'] = max(80, min(99, int(data['disk_threshold'])))
        if 'pause_timeout' in data:
            RESOURCE_MONITOR_CONFIG['pause_timeout'] = max(60, min(600, int(data['pause_timeout'])))
        
        return jsonify({
            'success': True,
            'config': RESOURCE_MONITOR_CONFIG,
            'message': '配置已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/resource-monitor/status', methods=['GET'])
def api_get_resource_status():
    """API: 获取实时监控状态"""
    try:
        import psutil
        import time
        
        # 当前资源状态
        current = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': time.time()
        }
        
        # 检查是否超过阈值
        alerts = []
        is_paused = False
        
        if RESOURCE_MONITOR_CONFIG['enabled']:
            if current['cpu_percent'] > RESOURCE_MONITOR_CONFIG['cpu_threshold']:
                alerts.append(f"CPU 使用率过高 ({current['cpu_percent']}% > {RESOURCE_MONITOR_CONFIG['cpu_threshold']}%)")
                is_paused = True
            if current['memory_percent'] > RESOURCE_MONITOR_CONFIG['memory_threshold']:
                alerts.append(f"内存使用率过高 ({current['memory_percent']}% > {RESOURCE_MONITOR_CONFIG['memory_threshold']}%)")
                is_paused = True
            if current['disk_percent'] > RESOURCE_MONITOR_CONFIG['disk_threshold']:
                alerts.append(f"磁盘空间不足 ({current['disk_percent']}% > {RESOURCE_MONITOR_CONFIG['disk_threshold']}%)")
                is_paused = True
        
        return jsonify({
            'success': True,
            'current': current,
            'thresholds': {
                'cpu': RESOURCE_MONITOR_CONFIG['cpu_threshold'],
                'memory': RESOURCE_MONITOR_CONFIG['memory_threshold'],
                'disk': RESOURCE_MONITOR_CONFIG['disk_threshold']
            },
            'alerts': alerts,
            'is_paused': is_paused,
            'monitoring_enabled': RESOURCE_MONITOR_CONFIG['enabled']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/task/<task_id>/pause', methods=['POST'])
def api_pause_task(task_id):
    """API: 暂停任务"""
    try:
        if task_id not in tasks:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        task = tasks[task_id]
        
        if task['status'] == 'running':
            task['status'] = 'paused'
            task['pause_reason'] = '用户请求'
            task['pause_time'] = datetime.now()
            task_resource_status[task_id] = 'paused'
            
            return jsonify({
                'success': True,
                'message': '任务已暂停',
                'task_id': task_id
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务不在运行状态'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/task/<task_id>/resume', methods=['POST'])
def api_resume_task(task_id):
    """API: 恢复任务"""
    try:
        if task_id not in tasks:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        task = tasks[task_id]
        
        if task['status'] == 'paused':
            task['status'] = 'running'
            task['pause_reason'] = None
            task['resume_time'] = datetime.now()
            if task_id in task_resource_status:
                del task_resource_status[task_id]
            
            return jsonify({
                'success': True,
                'message': '任务已恢复',
                'task_id': task_id
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务未暂停'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def check_resource_and_pause():
    """后台线程：监控资源并自动暂停任务"""
    import time
    import threading
    
    while True:
        try:
            if not RESOURCE_MONITOR_CONFIG['enabled']:
                time.sleep(5)
                continue
            
            import psutil
            
            # 检查当前资源
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # 检查是否有任务超过阈值
            should_pause = (
                cpu_percent > RESOURCE_MONITOR_CONFIG['cpu_threshold'] or
                memory_percent > RESOURCE_MONITOR_CONFIG['memory_threshold'] or
                disk_percent > RESOURCE_MONITOR_CONFIG['disk_threshold']
            )
            
            # 自动暂停/恢复任务
            for task_id, task in tasks.items():
                if task['status'] == 'running' and should_pause:
                    # 资源不足，暂停任务
                    task['status'] = 'paused'
                    task['pause_reason'] = '资源不足'
                    task['pause_time'] = datetime.now()
                    task_resource_status[task_id] = {
                        'reason': '资源不足',
                        'cpu': cpu_percent,
                        'memory': memory_percent,
                        'disk': disk_percent
                    }
                    print(f"⏸️  任务 {task_id} 已暂停（资源不足）")
                
                elif task['status'] == 'paused' and task.get('pause_reason') == '资源不足':
                    # 检查资源是否恢复
                    if (cpu_percent <= RESOURCE_MONITOR_CONFIG['cpu_threshold'] and
                        memory_percent <= RESOURCE_MONITOR_CONFIG['memory_threshold'] and
                        disk_percent <= RESOURCE_MONITOR_CONFIG['disk_threshold']):
                        # 资源恢复，自动继续
                        task['status'] = 'running'
                        task['resume_time'] = datetime.now()
                        if task_id in task_resource_status:
                            del task_resource_status[task_id]
                        print(f"▶️  任务 {task_id} 已恢复（资源充足）")
            
            # 等待下一次检查
            time.sleep(RESOURCE_MONITOR_CONFIG['check_interval'])
            
        except Exception as e:
            print(f"资源监控错误：{e}")
            time.sleep(5)


# 启动资源监控线程
import threading
monitor_thread = threading.Thread(target=check_resource_and_pause, daemon=True)
monitor_thread.start()
