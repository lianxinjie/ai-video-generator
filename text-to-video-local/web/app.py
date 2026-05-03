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