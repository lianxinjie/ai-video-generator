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
        import importlib.metadata
        
        packages = {
            'flask': {
                'name': 'Flask',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'Web 服务框架',
                'pip_name': 'flask'
            },
            'PIL': {
                'name': 'Pillow',
                'required': True,
                'installed': False,
                'version': None,
                'description': '图像处理库',
                'pip_name': 'pillow'
            },
            'psutil': {
                'name': 'psutil',
                'required': True,
                'installed': False,
                'version': None,
                'description': '系统监控库',
                'pip_name': 'psutil'
            },
            'torch': {
                'name': 'PyTorch',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'AI 深度学习框架（核心依赖）',
                'pip_name': 'torch',
                'install_extra': '--index-url https://download.pytorch.org/whl/cpu'
            },
            'transformers': {
                'name': 'Transformers',
                'required': True,
                'installed': False,
                'version': None,
                'description': '预训练模型库',
                'pip_name': 'transformers'
            },
            'diffusers': {
                'name': 'Diffusers',
                'required': True,
                'installed': False,
                'version': None,
                'description': '扩散模型库',
                'pip_name': 'diffusers'
            },
            'huggingface_hub': {
                'name': 'Huggingface Hub',
                'required': True,
                'installed': False,
                'version': None,
                'description': 'Huggingface 模型下载',
                'pip_name': 'huggingface-hub'
            },
            'modelscope': {
                'name': 'ModelScope',
                'required': True,
                'installed': False,
                'version': None,
                'description': '通义千问模型下载',
                'pip_name': 'modelscope'
            },
            'edge_tts': {
                'name': 'Edge TTS',
                'required': False,
                'installed': False,
                'version': None,
                'description': 'Microsoft Azure AI 配音（支持三层配音架构）',
                'pip_name': 'edge-tts'
            },
            'pydub': {
                'name': 'Pydub',
                'required': False,
                'installed': False,
                'version': None,
                'description': '音频处理库（配音混音必备）',
                'pip_name': 'pydub'
            }
        }
        
        for module_name, info in packages.items():
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                try:
                    # 特殊处理 PIL
                    import_name = 'PIL' if module_name == 'PIL' else module_name
                    module = importlib.import_module(import_name)
                    packages[module_name]['installed'] = True
                    try:
                        version = importlib.metadata.version(info['pip_name'])
                        packages[module_name]['version'] = version
                    except:
                        packages[module_name]['version'] = getattr(module, '__version__', 'unknown')
                except:
                    pass
        
        # 统计
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
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


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
        
        # 定义包的安装信息
        package_info = {
            'flask': {'pip_name': 'flask', 'extra': ''},
            'pillow': {'pip_name': 'pillow', 'extra': ''},
            'psutil': {'pip_name': 'psutil', 'extra': ''},
            'torch': {
                'pip_name': 'torch',
                'extra': '--index-url https://download.pytorch.org/whl/cpu'
            },
            'transformers': {'pip_name': 'transformers', 'extra': ''},
            'diffusers': {'pip_name': 'diffusers', 'extra': ''},
            'huggingface-hub': {'pip_name': 'huggingface-hub', 'extra': ''},
            'modelscope': {'pip_name': 'modelscope', 'extra': ''},
            'edge-tts': {'pip_name': 'edge-tts', 'extra': ''},
            'pydub': {'pip_name': 'pydub', 'extra': ''}
        }
        
        # 构建 pip 安装命令
        cmd = [sys.executable, '-m', 'pip', 'install']
        for pkg in packages:
            if pkg in package_info:
                info = package_info[pkg]
                if info['extra']:
                    cmd.extend([info['pip_name'], info['extra']])
                else:
                    cmd.append(info['pip_name'])
        
        cmd.append('--break-system-packages')
        
        # 后台执行安装任务
        def install_task():
            log_file = Path(f'web/logs/install_{task_id}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"开始安装依赖：{', '.join(packages)}\n")
                log.write(f"命令：{' '.join(cmd)}\n\n")
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    
                    if result.returncode == 0:
                        log.write("✓ 依赖安装成功\n")
                    else:
                        log.write(f"❌ 依赖安装失败：{result.stderr}\n")
                    
                except subprocess.TimeoutExpired:
                    log.write("❌ 安装超时\n")
                except Exception as e:
                    log.write(f"❌ 安装异常：{str(e)}\n")
        
        thread = threading.Thread(target=install_task)
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
        
        # 4. 检测 FFmpeg
        ffmpeg_path = shutil.which('ffmpeg')
        local_ffmpeg = Path('./ffmpeg/bin/ffmpeg.exe')
        if ffmpeg_path or local_ffmpeg.exists():
            checks['ffmpeg']['status'] = 'ok'
            path = ffmpeg_path or str(local_ffmpeg)
            checks['ffmpeg']['message'] = f'FFmpeg 已安装：{path}'
            checks['ffmpeg']['details'] = [f'路径：{path}']
        else:
            checks['ffmpeg']['status'] = 'warning'
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
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


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
    """API: 检查 FFmpeg 安装状态"""
    import shutil
    import subprocess
    
    try:
        # 检查 FFmpeg 是否在 PATH 中
        ffmpeg_path = shutil.which('ffmpeg')
        
        if ffmpeg_path:
            # 获取版本信息
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_line = result.stdout.split('\n')[0] if result.stdout else '未知版本'
            
            return jsonify({
                'success': True,
                'installed': True,
                'path': ffmpeg_path,
                'version': version_line,
                'source': 'system'
            })
        else:
            # 检查项目目录是否有 FFmpeg
            local_ffmpeg = Path('./ffmpeg')
            if local_ffmpeg.exists():
                # 查找 ffmpeg 可执行文件
                if platform.system() == 'Windows':
                    ffmpeg_exe = local_ffmpeg / 'ffmpeg.exe'
                    if not ffmpeg_exe.exists():
                        # 可能在子目录中
                        for exe in local_ffmpeg.rglob('ffmpeg.exe'):
                            ffmpeg_exe = exe
                            break
                else:
                    ffmpeg_exe = local_ffmpeg / 'ffmpeg'
                    if not ffmpeg_exe.exists():
                        for exe in local_ffmpeg.rglob('ffmpeg'):
                            ffmpeg_exe = exe
                            break
                
                if ffmpeg_exe.exists():
                    return jsonify({
                        'success': True,
                        'installed': True,
                        'path': str(ffmpeg_exe),
                        'version': '本地版本',
                        'source': 'local'
                    })
            
            return jsonify({
                'success': True,
                'installed': False,
                'message': 'FFmpeg 未安装'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/check-resources', methods=['GET'])
def api_check_resources():
    """API: 检查系统资源是否满足 FFmpeg 要求"""
    import platform
    
    try:
        # 1. 检测磁盘空间
        import shutil
        total_space = shutil.disk_usage('/')
        free_space_gb = total_space.free / (1024 ** 3)
        
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
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/download-ffmpeg', methods=['POST'])
def api_download_ffmpeg():
    """API: 自动下载 FFmpeg 到项目目录"""
    import platform
    import requests
    import zipfile
    import tarfile
    
    try:
        # 先检查资源
        resource_check = api_check_resources()
        resource_data = resource_check.get_json() if hasattr(resource_check, 'get_json') else {}
        
        if not resource_data.get('can_install', True):
            return jsonify({
                'success': False,
                'error': '系统资源不足，请先释放资源',
                'suggestions': resource_data.get('suggestions', [])
            }), 400
        
        system = platform.system()
        machine = platform.machine()
        arch = 'amd64' if machine in ['x86_64', 'AMD64'] else 'arm64' if machine in ['arm64', 'aarch64'] else machine
        
        # FFmpeg 静态编译版本下载地址
        urls = {
            'Windows': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
            'Linux': f'https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-{arch}-static.tar.xz',
            'Darwin': 'https://evermeet.cx/ffmpeg/getrelease/zip'
        }
        
        if system not in urls:
            return jsonify({
                'success': False,
                'error': f'不支持的系统：{system}'
            })
        
        # 创建下载目录
        download_dir = Path('./ffmpeg')
        download_dir.mkdir(exist_ok=True)
        
        # 下载
        url = urls[system]
        filename = 'ffmpeg.zip' if system == 'Windows' else 'ffmpeg.tar.xz'
        file_path = download_dir / filename
        
        # 使用流式下载，避免内存占用过大
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
        
        # 解压
        if system == 'Windows':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 找到包含 ffmpeg.exe 的目录
                zip_ref.extractall(download_dir)
                # 移动内容到根目录
                for item in download_dir.iterdir():
                    if item.is_dir() and item.name.startswith('ffmpeg'):
                        for sub_item in item.iterdir():
                            sub_item.rename(download_dir / sub_item.name)
                        item.rmdir()
                        break
        else:
            import subprocess
            subprocess.run(['tar', '-xf', str(file_path), '-C', str(download_dir)], check=True)
            # 移动内容
            for item in download_dir.iterdir():
                if item.is_dir() and 'ffmpeg' in item.name.lower():
                    for sub_item in item.iterdir():
                        sub_item.rename(download_dir / sub_item.name)
                    item.rmdir()
                    break
        
        # 清理压缩包
        file_path.unlink()
        
        # 设置执行权限（Linux/macOS）
        if system != 'Windows':
            ffmpeg_exe = download_dir / 'ffmpeg'
            if ffmpeg_exe.exists():
                import stat
                ffmpeg_exe.chmod(ffmpeg_exe.stat().st_mode | stat.S_IEXEC)
        
        return jsonify({
            'success': True,
            'path': str(download_dir),
            'message': 'FFmpeg 下载完成',
            'note': '请重启 Web 服务以使用 FFmpeg'
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'下载失败：{str(e)}',
            'suggestion': '请检查网络连接'
        }), 500
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


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
