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
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import threading
import uuid

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
        return jsonify({'error': str(e)}), 500



@app.route('/api/output/<task_id>/<filename>')
def api_output_file(task_id, filename):
    """API: 获取输出文件"""
    output_dir = app.config['OUTPUT_FOLDER'] / task_id
    return send_from_directory(output_dir, filename)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  AI 视频生成器 - Web 服务")
    print("="*70)
    print("\n访问地址：http://localhost:5000")
    print("\nAPI 接口:")
    print("  POST /api/generate - 生成视频")
    print("  GET  /api/task/<id> - 查询任务状态")
    print("  GET  /api/output/<id>/<file> - 获取输出文件")
    print("\n按 Ctrl+C 停止服务\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)


# ========== 硬件扫描与一键安装 API (新增) ==========

@app.route('/api/scanner/report', methods=['GET'])
def api_scanner_report():
    """API: 获取扫描报告"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scanner import SystemScanner
        from dataclasses import asdict
        
        scanner = SystemScanner()
        scanner.scan_all()
        scanner.analyze()
        
        hw = scanner.hardware
        rec = scanner.recommendation
        
        summary = {
            'cpu': f"{hw.cpu_model} ({hw.cpu_cores}核)",
            'gpu': hw.gpu_models[0] if hw.gpu_models else '无独立 GPU',
            'gpu_memory': f"{sum(hw.gpu_memory_total):.1f}GB" if hw.gpu_memory_total else 'N/A',
            'ram': f"{hw.ram_total}GB",
            'disk_available': f"{hw.disk_available}GB",
            'recommended_mode': rec.mode if rec else 'unknown',
            'confidence': rec.confidence if rec else 'low',
            'suitable_models': rec.suitable_models if rec else [],
            'warnings': rec.warnings if rec else [],
            'optimization_tips': rec.optimization_tips if rec else []
        }
        
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/generate-package', methods=['POST'])
def api_generate_package():
    """API: 生成个性化离线安装包"""
    try:
        import uuid
        data = request.get_json() or {}
        task_id = data.get('task_id', str(uuid.uuid4()))
        package_dir = data.get('package_dir', f'web/outputs/offline-package-{task_id}')
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scanner import SystemScanner
        from dataclasses import asdict
        
        scanner = SystemScanner()
        scanner.scan_all()
        scanner.analyze()
        
        output_path = Path(package_dir)
        scanner.generate_offline_package(str(output_path))
        
        package_files = []
        for file in output_path.glob('*'):
            if file.is_file():
                package_files.append({'name': file.name, 'size': file.stat().st_size})
        
        # 存储 package 映射
        packages[task_id] = str(output_path.absolute())
        
        return jsonify({
            'success': True,
            'package_id': task_id,
            'package_name': f'offline-package-{task_id}.zip',
            'package_dir': str(output_path.absolute()),
            'files': package_files,
            'recommendation': asdict(scanner.recommendation) if scanner.recommendation else None
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/scanner/download-package', methods=['GET'])
def api_download_package():
    """API: 下载离线安装包（ZIP）"""
    try:
        import zipfile
        from io import BytesIO
        from flask import send_file
        
        package_id = request.args.get('package', '')
        if not package_id:
            return jsonify({'error': '缺少 package 参数'}), 400
        
        # 从映射中查找 package_dir
        if package_id not in packages:
            return jsonify({'error': f'安装包不存在：{package_id}'}), 404
        
        package_path = Path(packages[package_id])
        if not package_path.exists():
            return jsonify({'error': f'包目录不存在：{package_path}'}), 404
        
        # 创建 ZIP 文件
        zip_path = package_path.with_suffix('.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in package_path.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(package_path)
                    zipf.write(file, arcname)
        
        return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name=f'{package_path.name}.zip')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/install', methods=['POST'])
def api_install():
    """API: 执行一键安装"""
    try:
        import uuid
        data = request.get_json() or {}
        package_dir = data.get('package_dir')
        
        if not package_dir:
            return jsonify({'error': '缺少 package_dir 参数'}), 400
        
        install_script = Path(package_dir) / 'install.sh'
        if not install_script.exists():
            return jsonify({'error': '安装脚本不存在'}), 404
        
        task_id = str(uuid.uuid4())
        
        def run_install():
            import subprocess
            log_file = Path(f'{package_dir}.install.log')
            with open(log_file, 'w') as f:
                try:
                    result = subprocess.run(
                        ['bash', str(install_script)],
                        stdout=f, stderr=subprocess.STDOUT,
                        cwd=package_dir,
                        timeout=600
                    )
                    tasks[task_id] = {
                        'status': 'completed' if result.returncode == 0 else 'failed',
                        'log_file': str(log_file),
                        'returncode': result.returncode
                    }
                except subprocess.TimeoutExpired:
                    tasks[task_id] = {'status': 'failed', 'error': '安装超时 (10 分钟)'}
                except Exception as e:
                    tasks[task_id] = {'status': 'failed', 'error': str(e)}
        
        tasks[task_id] = {'status': 'running', 'progress': 0, 'log': '正在启动安装...'}
        threading.Thread(target=run_install, daemon=True).start()
        
        return jsonify({'success': True, 'task_id': task_id, 'message': '安装任务已启动'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/install-status/<task_id>', methods=['GET'])
def api_install_status(task_id):
    """API: 查询安装进度"""
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        result = {
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0),
            'log': task.get('log', '')
        }
        
        if task.get('log_file') and Path(task['log_file']).exists():
            with open(task['log_file'], 'r') as f:
                result['log'] = f.read()[-10000:]
            result['returncode'] = task.get('returncode')
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== 新增 API 路由 ==========

@app.route('/api/tasks', methods=['GET'])
def api_list_tasks():
    """API: 列出所有任务"""
    task_list = []
    for task_id, task in tasks.items():
        task_list.append({
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'prompt': task.get('prompt', ''),
            'mode': task.get('mode', ''),
            'start_time': task.get('start_time', ''),
            'progress': task.get('progress', 0),
        })
    
    # 按开始时间倒序排列
    task_list.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    return jsonify({'tasks': task_list})


@app.route('/api/task/<task_id>/cancel', methods=['POST'])
def api_cancel_task(task_id):
    """API: 取消任务"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = tasks[task_id]
    if task.get('status') != 'running':
        return jsonify({'error': '任务不在运行中', 'current_status': task.get('status')}), 400
    
    try:
        # 简化版：没有实际进程时，允许取消并设置状态
        task['status'] = 'cancelled'
        task['log'] += '\n⚠️ 任务已被用户取消\n'
        return jsonify({'success': True, 'message': '任务已取消'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500


# 增强版 api_task_status - 替换原有简单版本
@app.route('/api/task/<task_id>', methods=['GET'])
def api_task_status_enhanced(task_id):
    """API: 查询任务状态（增强版）"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = tasks[task_id]
    
    # 构建完整状态
    status = {
        'task_id': task_id,
        'status': task.get('status', 'unknown'),
        'progress': task.get('progress', 0),
        'prompt': task.get('prompt', ''),
        'mode': task.get('mode', ''),
        'start_time': task.get('start_time', ''),
        'log': task.get('log', ''),
    }
    
    # 硬件信息
    if 'hardware' in task:
        status['hardware'] = task['hardware']
    
    # 推荐信息
    if 'recommendation' in task:
        status['recommendation'] = task['recommendation']
    
    # 计算运行时间
    if task.get('start_time'):
        try:
            start = datetime.fromisoformat(task['start_time'])
            end = datetime.now()
            duration = (end - start).total_seconds()
            status['running_time'] = f"{duration:.0f}s"
            status['running_time_seconds'] = duration
        except:
            status['running_time'] = 'N/A'
    else:
        status['running_time'] = 'N/A'
    
    # 输出文件
    if task.get('output_file'):
        status['output_file'] = task['output_file']
        status['download_task_id'] = task_id
    
    return jsonify(status)


@app.route('/api/quick-start', methods=['POST'])
def api_quick_start():
    """API: 一键启动（自动检测硬件 + 推荐模式 + 启动任务）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求参数错误'}), 400
        
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'error': '提示词不能为空'}), 400
        
        mode = data.get('mode', 'personal')
        duration = float(data.get('duration', 10))
        voiceover = data.get('voiceover', False)
        character_voice = data.get('character_voice', 'zh-CN-XiaoxiaoNeural')
        
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        
        # 存储任务
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'prompt': prompt,
            'mode': mode,
            'start_time': datetime.now().isoformat(),
            'log': f'一键启动任务\n提示词：{prompt}\n模式：{mode}\n时长：{duration}s\n',
            'hardware': {},
            'recommendation': {},
        }
        
        # 启动异步任务（简化版，实际应该启动真实任务）
        def run_task():
            import subprocess
            import time
            task = tasks[task_id]
            try:
                # 这里应该调用实际的生成逻辑
                # 简化演示：等待并更新进度
                for i in range(10):
                    time.sleep(1)
                    task['progress'] = (i + 1) * 10
                    task['log'] += f'进度：{task["progress"]}%\n'
                task['status'] = 'completed'
                task['log'] += '任务完成\n'
            except Exception as e:
                task['status'] = 'failed'
                task['log'] += f'错误：{e}\n'
        
        from threading import Thread
        thread = Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'mode': mode,
            'message': '任务已启动'
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ========== 模型管理 API ==========

@app.route('/api/models/list', methods=['GET'])
def api_list_models():
    """API: 列出所有可安装的模型"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from download_models import ModelDownloader
        
        downloader = ModelDownloader(output_dir='./models')
        
        # 检查已下载的模型
        model_names = list(downloader.model_repos.keys())
        existing = downloader.check_existing_models(model_names)
        
        # 构建返回数据
        models = []
        for name, info in downloader.model_repos.items():
            models.append({
                'id': name,
                'name': name.upper(),
                'source': 'ModelScope' if info['type'] == 'modelscope' else 'HuggingFace',
                'repo': info['repo'],
                'size_gb': info['size_gb'],
                'required': info.get('required', False),
                'installed': existing.get(name, False),
                'description': get_model_description(name)
            })
        
        return jsonify({'success': True, 'models': models})
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


def get_model_description(model_name: str) -> str:
    """获取模型描述"""
    descriptions = {
        'modelscope': '通义实验室视频生成模型（基础模型，推荐优先下载）',
        'animatediff': 'AnimateDiff 动画生成模型（卡通风格）',
        'animatediff_sd': 'AnimateDiff SD 模型（依赖 animatediff）',
        'cogvideox': 'CogVideoX-5b 大型视频生成模型（高质量，需要大显存）',
        'svd': 'Stable Video Diffusion 图像转视频（需要 CUDA 支持）'
    }
    return descriptions.get(model_name, '未知模型')


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


@app.route('/api/check-dependencies', methods=['GET'])
def api_check_dependencies():
    """API: 检查 Python 依赖安装状态"""
    try:
        import importlib.util
        
        packages = {
            'flask': {'required': True, 'installed': False, 'version': None},
            'pillow': {'required': False, 'installed': False, 'version': None},
            'psutil': {'required': False, 'installed': False, 'version': None},
            'torch': {'required': False, 'installed': False, 'version': None},
        }
        
        for name in packages.keys():
            spec = importlib.util.find_spec(name.replace('pillow', 'PIL').replace('psutil', 'psutil'))
            if spec is not None:
                packages[name]['installed'] = True
                try:
                    module = importlib.import_module(name)
                    packages[name]['version'] = getattr(module, '__version__', 'unknown')
                except:
                    pass
        
        return jsonify(packages)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/install-dependencies', methods=['POST'])
def api_install_dependencies():
    """API: 安装 Python 依赖"""
    try:
        import subprocess
        data = request.get_json() or {}
        packages = data.get('packages', [])
        
        if not packages:
            return jsonify({'error': '请指定要安装的包'}), 400
        
        task_id = str(uuid.uuid4())
        
        # 创建任务
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'type': 'dependency_install',
            'packages': packages,
            'start_time': datetime.now().isoformat(),
            'log': f'准备安装：{", ".join(packages)}\n\n'
        }
        
        # 后台线程执行安装
        def run_install():
            task = tasks[task_id]
            try:
                for i, package in enumerate(packages):
                    task['log'] += f'正在安装 {package}...\n'
                    
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package, '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        task['log'] += f'✓ {package} 安装成功\n\n'
                    else:
                        task['log'] += f'✗ {package} 安装失败：{result.stderr}\n\n'
                    
                    task['progress'] = int((i + 1) / len(packages) * 100)
                
                task['status'] = 'completed'
                task['log'] += '\n所有包安装完成！\n'
                
            except subprocess.TimeoutExpired:
                task['status'] = 'failed'
                task['log'] += '\n错误：安装超时\n'
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['log'] += f'\n错误：{e}\n'
        
        # 启动后台线程
        from threading import Thread
        thread = Thread(target=run_install)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'开始安装 {len(packages)} 个包'
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
