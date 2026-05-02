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


@app.route('/api/analyze', methods=['POST'])
def api_analyze_scenes():
    """
    API: 智能分析并切分场景
    
    请求参数:
    - prompt: 文本提示词
    - duration: 总时长
    - mode: 分析模式 (keyword/ai)
    """
    try:
        prompt = request.form.get('prompt', '')
        if not prompt:
            return jsonify({'error': '提示词不能为空'}), 400
        
        duration = float(request.form.get('duration', 10))
        mode = request.form.get('mode', 'auto')
        
        # 调用场景分析器
        sys.path.insert(0, 'personal_mode')
        from collaborative_scheduler import CollaborativeScheduler
        
        scheduler = CollaborativeScheduler(
            total_duration=duration,
            segment_duration=2.0,
            enable_scene_analysis=(mode != 'keyword'),
            enable_scene_detection=True
        )
        
        # 执行场景分析
        segments = scheduler.ai_assisted_scene_analysis(prompt)
        
        # 返回场景列表
        return jsonify({
            'success': True,
            'total_scenes': len(segments),
            'total_duration': sum(s.get('duration', 0) for s in segments),
            'scenes': segments
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scenes', methods=['POST'])
def api_save_scenes():
    """
    API: 保存修改后的场景
    
    请求参数:
    - scenes: 场景列表（JSON）
    - task_id: 任务 ID（如果已创建）
    """
    try:
        data = request.json
        scenes = data.get('scenes', [])
        
        if not scenes:
            return jsonify({'error': '场景列表不能为空'}), 400
        
        # 保存场景到临时文件
        task_id = data.get('task_id') or str(uuid.uuid4())
        scenes_file = app.config['OUTPUT_FOLDER'] / task_id / 'scenes.json'
        scenes_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(scenes_file, 'w', encoding='utf-8') as f:
            json.dump({'scenes': scenes}, f, ensure_ascii=False, indent=2)
        
        # 更新任务
        if task_id in tasks:
            tasks[task_id]['scenes'] = scenes
            tasks[task_id]['scenes_confirmed'] = True
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '场景已保存'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scenes/<task_id>', methods=['GET'])
def api_get_scenes(task_id):
    """API: 获取任务场景列表"""
    try:
        # 先从内存中查找
        if task_id in tasks and 'scenes' in tasks[task_id]:
            return jsonify({
                'success': True,
                'scenes': tasks[task_id]['scenes']
            })
        
        # 从文件加载
        scenes_file = app.config['OUTPUT_FOLDER'] / task_id / 'scenes.json'
        if scenes_file.exists():
            with open(scenes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify({
                'success': True,
                'scenes': data.get('scenes', [])
            })
        
        return jsonify({'error': '场景不存在'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scenes/confirm')
def scenes_confirm():
    """场景确认页面"""
    return render_template('scenes_confirm.html')


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
    - scenes: 场景列表（可选，如果提供则跳过自动分析）
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
        
        # 检查是否已提供场景
        scenes = None
        scenes_json = request.form.get('scenes')
        if scenes_json:
            scenes = json.loads(scenes_json)
        
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
        
        # 保存场景（如果有）
        if scenes:
            scenes_file = output_dir / 'scenes.json'
            with open(scenes_file, 'w', encoding='utf-8') as f:
                json.dump({'scenes': scenes}, f, ensure_ascii=False, indent=2)
        
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
        
        # 如果是 collaborative 模式，启用场景分析
        if mode == 'collaborative':
            cmd.append('--enable-scene-detection')
            cmd.append('--enable-scene-refine')
        
        # 启动任务（后台运行）
        tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'prompt': prompt,
            'mode': mode,
            'start_time': str(uuid.uuid4()),
            'scenes': scenes
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
