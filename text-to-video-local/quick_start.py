#!/usr/bin/env python3
"""
快速启动脚本 - 零依赖启动
- 自动检测 Flask
- 无 Flask 时使用内置 HTTP 服务器
- 有 Flask 时启动完整功能
"""

import os
import sys
import webbrowser
from pathlib import Path

def check_flask():
    """检查 Flask 是否已安装（不导入）"""
    try:
        import importlib.util
        spec = importlib.util.find_spec("flask")
        return spec is not None
    except:
        return False

def install_missing_deps():
    """自动安装缺失的依赖"""
    print("\n📦 检测必要依赖...")
    
    missing = []
    deps = {
        'flask': ('Flask', 'web 服务'),
        'pillow': ('Pillow', '图像处理'),
        'psutil': ('psutil', '系统监控')
    }
    
    for package, (name, desc) in deps.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - 缺失")
            missing.append((package, name))
    
    if missing:
        print("\n正在安装缺失的依赖...")
        import subprocess
        for package, name in missing:
            print(f"  安装 {name}...", end=' ', flush=True)
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("✓")
            except:
                print("✗ 失败")
        
        if not any(m[0] == 'flask' for m in missing):
            print("\n✅ 依赖安装完成！")
    
    return len(missing) == 0

def start_with_flask():
    """启动 Flask 应用"""
    print("\n🚀 正在启动 Flask 应用...")
    
    # 动态导入
    from flask import Flask, render_template, jsonify, request
    import threading
    
    # 导入应用
    app_dir = Path(__file__).parent / 'web'
    sys.path.insert(0, str(app_dir))
    from app import app
    
    # 在新线程中打开浏览器
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
    
    # 启动浏览器打开线程
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 运行 Flask 应用
    print("✅ 应用已启动！")
    print("\n🌐 访问地址:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000\n")
    print("按 Ctrl+C 停止服务\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

def start_without_flask():
    """在没有 Flask 时启动简单的 HTTP 服务器"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    
    print("\n⚠️  Flask 未安装，启动快速预览模式...")
    
    class QuickStartHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI 视频生成器 - 预览模式</title>
    <meta http-equiv="refresh" content="0;url=start.html">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; color: white; text-align: center; }
        .container { background: rgba(255,255,255,0.95); color: #333; padding: 40px; border-radius: 20px; max-width: 600px; }
        h1 { color: #667eea; margin-bottom: 20px; }
        p { margin: 15px 0; font-size: 16px; line-height: 1.6; }
        .btn { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; margin: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 视频生成器</h1>
        <p><strong>预览模式（Flask 未安装）</strong></p>
        <p>正在跳转到安装向导...</p>
        <p style="color: #999; font-size: 14px;">如果没有自动跳转，请点击下方按钮：</p>
        <a href="start.html" class="btn">打开安装向导</a>
        <h3 style="margin-top: 30px; color: #f6ad55;">⚠️ 提示</h3>
        <p style="text-align: left; line-height: 2;">
            1. 点击<a href="https://github.com/chaitin/monkeyCode-sandbox/blob/main/text-to-video-local/offline_install.html" style="color: #667eea;">"🚀 打开离线安装器"</a><br>
            2. 选择您的操作系统<br>
            3. 下载并安装 Python<br>
            4. 刷新页面开始使用完整功能
        </p>
    </div>
    <script>
        setTimeout(() => {
            window.location.href = 'start.html';
        }, 1000);
    </script>
</body>
</html>"""
                self.wfile.write(html.encode('utf-8'))
            else:
                super().do_GET()
    
    # 启动服务器
    server = HTTPServer(('0.0.0.0', 8080), QuickStartHandler)
    
    # 后台打开浏览器
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:8080')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("✅ 快速预览模式已启动")
    print("\n🌐 访问地址:")
    print("   http://localhost:8080\n")
    print("💡 提示: 安装 Flask 以获得完整功能:")
    print(f"   {sys.executable} -m pip install flask\n")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")

def main():
    """主函数"""
    print("="*70)
    print("  🎬 AI 视频生成器 - 快速启动")
    print("="*70)
    print()
    print(f"操作系统：{os.name.title()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # 自动安装缺失依赖
    install_missing_deps()
    
    # 检查 Flask
    if check_flask():
        print("\n✅ Flask: 已安装")
        try:
            import importlib.metadata
            version = importlib.metadata.version("flask")
            print(f"   版本：{version}")
        except:
            pass
        
        print("\n启动完整功能模式...")
        start_with_flask()
    else:
        print("\n⚠️  Flask: 未安装")
        start_without_flask()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
