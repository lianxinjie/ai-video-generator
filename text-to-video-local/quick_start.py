#!/usr/bin/env python3
"""
渐进式安装快速启动脚本
- 零依赖启动
- Web 界面引导安装
- 按需安装依赖
"""

import os
import sys
import subprocess
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import threading
import webbrowser

class QuickStartHandler(SimpleHTTPRequestHandler):
    """处理 Web 请求 - 支持安装向导"""
    
    def __init__(self, *args, **kwargs):
        # 设置根目录为 web 目录
        os.chdir(Path(__file__).parent / 'web')
        super().__init__(*args, directory='web')
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/':
            # 检查 Flask 是否安装，决定显示哪个页面
            if self.check_flask():
                self.path = '/templates/index.html'
            else:
                self.path = '/templates/install.html'
        elif self.path == '/api/status':
            self.send_json(self.get_status())
            return
        elif self.path == '/api/check-dependencies':
            self.send_json(self.check_dependencies())
            return
        
        return super().do_GET()
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/install-dependencies':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            self.send_json(self.install_dependencies(data))
            return
        
        return super().do_POST()
    
    def check_flask(self):
        """检查 Flask 是否已安装"""
        try:
            import flask
            return True
        except ImportError:
            return False
    
    def send_json(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def get_status(self):
        """获取系统状态"""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'flask_installed': self.check_flask(),
            'dependencies': self.check_dependencies()
        }
    
    def check_dependencies(self):
        """检查依赖安装状态"""
        deps = {}
        
        # Flask
        try:
            import flask
            deps['flask'] = {'installed': True, 'version': flask.__version__, 'required': True}
        except ImportError:
            deps['flask'] = {'installed': False, 'required': True}
        
        # Pillow
        try:
            from PIL import Image
            deps['pillow'] = {'installed': True, 'required': False}
        except ImportError:
            deps['pillow'] = {'installed': False, 'required': False}
        
        # psutil
        try:
            import psutil
            deps['psutil'] = {'installed': True, 'required': False}
        except ImportError:
            deps['psutil'] = {'installed': False, 'required': False}
        
        # PyTorch (可选)
        try:
            import torch
            deps['torch'] = {'installed': True, 'version': torch.__version__, 'required': False}
        except ImportError:
            deps['torch'] = {'installed': False, 'required': False}
        
        # 计算进度
        total = len([d for d in deps.values() if d['required']])
        installed = sum(1 for d in deps.values() if d['required'] and d['installed'])
        deps['progress'] = {
            'installed': installed,
            'total': total,
            'percentage': int(installed / total * 100) if total > 0 else 0
        }
        
        return deps
    
    def install_dependencies(self, data=None):
        """安装依赖"""
        if data is None:
            data = {}
        
        packages = data.get('packages', ['flask', 'pillow', 'psutil'])
        
        result = {
            'success': True,
            'packages': [],
            'output': [],
            'errors': []
        }
        
        for package in packages:
            try:
                output_lines = []
                
                # 根据包选择 index url
                index_url = ''
                if package == 'torch':
                    # 检测是否有 GPU
                    has_gpu = False
                    if sys.platform == 'win32':
                        try:
                            result_proc = subprocess.run(
                                ['where', 'nvidia-smi'],
                                capture_output=True
                            )
                            has_gpu = result_proc.returncode == 0
                        except:
                            pass
                    else:
                        try:
                            result_proc = subprocess.run(
                                ['which', 'nvidia-smi'],
                                capture_output=True
                            )
                            has_gpu = result_proc.returncode == 0
                        except:
                            pass
                    
                    if has_gpu:
                        index_url = '--index-url https://download.pytorch.org/whl/cu121'
                    else:
                        index_url = '--index-url https://download.pytorch.org/whl/cpu'
                
                # 执行安装
                cmd = [sys.executable, '-m', 'pip', 'install', package, '-q']
                if index_url:
                    cmd.extend(index_url.split())
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                stdout, _ = process.communicate()
                
                if process.returncode == 0:
                    result['packages'].append({
                        'name': package,
                        'installed': True
                    })
                    result['output'].append(f"✓ 安装 {package} 成功")
                else:
                    result['packages'].append({
                        'name': package,
                        'installed': False,
                        'error': stdout
                    })
                    result['errors'].append(f"✗ 安装 {package} 失败：{stdout}")
                
            except Exception as e:
                result['packages'].append({
                    'name': package,
                    'installed': False,
                    'error': str(e)
                })
                result['errors'].append(f"✗ 安装 {package} 异常：{e}")
        
        # 重新检查依赖
        result['dependencies'] = self.check_dependencies()
        
        result['success'] = len(result['errors']) == 0
        
        return result
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[Web] {self.address_string()} - {args[0]}")

def start_quick_server(port=8080):
    """启动快速预览服务器"""
    try:
        server = HTTPServer(('0.0.0.0', port), QuickStartHandler)
        
        print()
        print("="*70)
        print("  🌐 快速预览模式")
        print("="*70)
        print()
        print(f"  访问地址：http://localhost:{port}")
        print(f"  访问地址：http://127.0.0.1:{port}")
        print()
        print("  📦 检测到 Flask 未安装")
        print("  ✅ Web 界面将引导您完成安装")
        print()
        print("  按 Ctrl+C 停止服务")
        print()
        print("="*70)
        print()
        
        # 自动打开浏览器
        def open_browser():
            webbrowser.open(f'http://localhost:{port}')
        
        threading.Timer(1.5, open_browser).start()
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n错误：{e}")
        return False
    
    return True

def start_flask_app(port=5000):
    """启动 Flask 应用"""
    try:
        sys.path.insert(0, 'web')
        from app import app
        
        print()
        print("="*70)
        print("  🚀 完整功能模式")
        print("="*70)
        print()
        print(f"  访问地址：http://localhost:{port}")
        print(f"  访问地址：http://127.0.0.1:{port}")
        print()
        print("  ✅ 所有功能已就绪")
        print()
        print("  按 Ctrl+C 停止服务")
        print()
        print("="*70)
        print()
        
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        return True
        
    except Exception as e:
        print(f"❌ Flask 启动失败：{e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print("  AI 视频生成器 - 快速启动")
    print("="*70)
    print()
    
    # 系统信息
    if sys.platform == 'win32':
        os_name = "Windows"
    elif sys.platform == 'darwin':
        os_name = "macOS"
    else:
        os_name = "Linux"
    
    print(f"操作系统：{os_name}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # 检查 Flask
    try:
        import flask
        has_flask = True
        print("✅ Flask: 已安装 (" + flask.__version__ + ")")
    except ImportError:
        has_flask = False
        print("⚠️  Flask: 未安装")
    
    print()
    
    # 启动服务
    if has_flask:
        print("正在启动完整功能 Web 服务...")
        start_flask_app(5000)
    else:
        print("正在启动快速预览 Web 服务...")
        success = start_quick_server(8080)
        
        if not success:
            print()
            print("建议：")
            print("  1. 手动安装 Flask:")
            print(f"     {sys.executable} -m pip install flask")
            print()
            print("  2. 或使用安装向导:")
            print("     浏览器访问 http://localhost:8080")
            print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
