@app.route('/api/scanner/detect', methods=['POST'])
def api_hardware_detect():
    """
    API: 硬件检测与推荐
    
    自动检测当前电脑硬件配置，推荐最优生成模式
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scanner import SystemScanner
        
        # 创建扫描器
        scanner = SystemScanner()
        
        # 扫描硬件
        scanner.scan_all()
        
        # 分析并生成推荐
        scanner.analyze()
        
        # 返回 JSON 报告
        from dataclasses import asdict
        report = {
            'hardware': asdict(scanner.hardware),
            'recommendation': asdict(scanner.recommendation) if scanner.recommendation else None,
            'cpu_tier': scanner._classify_cpu_tier(),
            'gpu_tier': scanner._classify_gpu_tier()
        }
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/report', methods=['GET'])
def api_scanner_report():
    """
    API: 获取扫描报告
    
    返回硬件摘要和推荐方案
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scanner import SystemScanner
        
        scanner = SystemScanner()
        scanner.scan_all()
        scanner.analyze()
        
        from dataclasses import asdict
        
        # 简化报告
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
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/generate-package', methods=['POST'])
def api_generate_package():
    """
    API: 生成个性化离线安装包
    
    根据硬件扫描结果生成定制化的安装脚本和依赖
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id', str(uuid.uuid4()))
        package_dir = data.get('package_dir', f'offline-package-{task_id}')
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scanner import SystemScanner
        from dataclasses import asdict
        
        # 创建扫描器
        scanner = SystemScanner()
        
        # 扫描并分析
        scanner.scan_all()
        scanner.analyze()
        
        # 生成离线包
        output_path = Path(package_dir)
        scanner.generate_offline_package(str(output_path))
        
        # 返回包内容
        package_files = []
        for file in output_path.glob('*'):
            if file.is_file():
                package_files.append({
                    'name': file.name,
                    'size': file.stat().st_size,
                    'path': str(file)
                })
        
        return jsonify({
            'success': True,
            'package_dir': str(output_path.absolute()),
            'files': package_files,
            'recommendation': asdict(scanner.recommendation) if scanner.recommendation else None,
            'message': f'离线包已生成：{len(package_files)} 个文件'
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/scanner/download-package', methods=['GET'])
def api_download_package():
    """
    API: 下载离线安装包
    
    打包并下载个性化安装包
    """
    try:
        package_name = request.args.get('package', 'offline-package')
        package_path = Path(package_name)
        
        if not package_path.exists():
            return jsonify({'error': f'安装包不存在：{package_name}'}), 404
        
        # 创建 ZIP 文件
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in package_path.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(package_path)
                    zipf.write(file, arcname)
        
        zip_buffer.seek(0)
        
        from flask import send_file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{package_name}.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/install', methods=['POST'])
def api_install():
    """
    API: 执行一键安装
    
    在后台运行安装脚本
    """
    try:
        data = request.get_json()
        package_dir = data.get('package_dir')
        
        if not package_dir:
            return jsonify({'error': '缺少 package_dir 参数'}), 400
        
        install_script = Path(package_dir) / 'install.sh'
        if not install_script.exists():
            return jsonify({'error': '安装脚本不存在'}), 404
        
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        
        # 在后台执行安装
        def run_install():
            log_file = Path(f'{package_dir}.log')
            with open(log_file, 'w') as f:
                try:
                    import subprocess
                    result = subprocess.run(
                        ['bash', str(install_script)],
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        cwd=package_dir
                    )
                    tasks[task_id] = {
                        'status': 'completed' if result.returncode == 0 else 'failed',
                        'log_file': str(log_file),
                        'returncode': result.returncode
                    }
                except Exception as e:
                    tasks[task_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }
        
        # 启动后台任务
        tasks[task_id] = {'status': 'running', 'progress': 0}
        threading.Thread(target=run_install, daemon=True).start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '安装任务已启动'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scanner/install-status/<task_id>', methods=['GET'])
def api_install_status(task_id):
    """
    API: 查询安装进度
    """
    try:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        
        result = {
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0)
        }
        
        if task.get('log_file'):
            try:
                with open(task['log_file'], 'r') as f:
                    result['log'] = f.read()[-5000:]  # 返回最后 5000 行
            except:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500