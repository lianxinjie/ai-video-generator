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
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent.parent
                )
                
                if result.returncode == 0:
                    tasks[task_id]['status'] = 'completed'
                    
                    # 查找生成的视频文件
                    video_files = list(output_dir.glob('*.mp4'))
                    if video_files:
                        tasks[task_id]['video_url'] = f'/api/output/{task_id}/{video_files[0].name}'
                else:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['error'] = result.stderr
                
                tasks[task_id]['progress'] = 100
            except Exception as e:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = str(e)
                tasks[task_id]['progress'] = 100
        
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


@app.route('/api/task/<task_id>')
def api_task_status(task_id):
    """API: 查询任务状态"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(tasks[task_id])


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
        
        return jsonify({
            'success': True,
            'package_dir': str(output_path.absolute()),
            'files': package_files,
            'recommendation': asdict(scanner.recommendation) if scanner.recommendation else None
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/scanner/download-package', methods=['GET'])
def api_download_package():
    """API: 下载离线安装包"""
    try:
        import zipfile
        from io import BytesIO
        from flask import send_file
        
        package_name = request.args.get('package', '')
        if not package_name:
            return jsonify({'error': '缺少 package 参数'}), 400
        
        package_path = Path(package_name)
        if not package_path.exists():
            return jsonify({'error': f'安装包不存在：{package_name}'}), 404
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in package_path.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(package_path)
                    zipf.write(file, arcname)
        
        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f'{Path(package_name).name}.zip')
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
