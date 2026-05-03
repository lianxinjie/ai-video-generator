#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 安装器 - 通过 Web 界面显示安装进度
"""

import http.server
import socketserver
import json
import subprocess
import threading
import os
import sys
import time
from pathlib import Path

PORT = 8081
LOG_FILE = "install_progress.log"

# 全局变量存储安装状态
install_status = {
    "running": False,
    "progress": 0,
    "logs": [],
    "success": False,
    "error": None
}

class InstallHandler:
    """安装执行器"""
    
    def __init__(self):
        self.log_callback = None
    
    def log(self, message):
        """记录日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        install_status["logs"].append(log_line)
        print(log_line)
        
        # 追加到日志文件
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    def run_install(self):
        """执行安装"""
        install_status["running"] = True
        install_status["progress"] = 0
        install_status["logs"] = []
        install_status["success"] = False
        install_status["error"] = None
        
        try:
            self.log("="*60)
            self.log("AI 视频生成器 - 开始安装")
            self.log("="*60)
            
            # Step 1: 检查 Python
            self.log("[1/4] 检查 Python 环境...")
            install_status["progress"] = 10
            
            import sys
            python_version = sys.version.split()[0]
            if not python_version.startswith("3."):
                self.log(f"[!] Python 版本不匹配：{python_version}")
                install_status["error"] = f"Python 版本不匹配：{python_version}"
                return
            
            self.log(f"[✓] Python {python_version} 已安装")
            install_status["progress"] = 25
            
            # Step 2: 安装依赖
            self.log("[2/4] 安装项目依赖...")
            self.log("正在执行：pip install flask pillow psutil")
            install_status["progress"] = 35
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "flask", "pillow", "psutil"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self.log(f"[!] 安装失败：{result.stderr}")
                install_status["error"] = result.stderr
                install_status["progress"] = 40
                return
            
            self.log("[✓] 依赖安装完成")
            install_status["progress"] = 60
            
            # Step 3: 完成
            self.log("[3/4] 安装完成！")
            install_status["progress"] = 80
            
            # Step 4: 启动应用
            self.log("[4/4] 正在启动应用...")
            install_status["progress"] = 90
            
            self.log("="*60)
            self.log("✅ 安装成功！应用即将启动...")
            self.log("="*60)
            
            install_status["success"] = True
            install_status["progress"] = 100
            install_status["running"] = False
            
        except Exception as e:
            self.log(f"[!] 错误：{str(e)}")
            install_status["error"] = str(e)
            install_status["running"] = False

class WebHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(install_status).encode())
        elif self.path == "/api/start":
            # 异步启动安装
            threading.Thread(target=InstallHandler().run_install).start()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"started": True}).encode())
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理 POST 请求"""
        self.do_GET()
    
    def log_message(self, format, *args):
        """禁用 HTTP 日志"""
        pass

def start_server():
    """启动 Web 服务器"""
    with socketserver.TCPServer(("", PORT), WebHandler) as httpd:
        print(f"Web 安装服务器已启动")
        print(f"请访问：http://localhost:{PORT}")
        print(f"按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

def main():
    """主函数"""
    print("="*60)
    print("  AI 视频生成器 - Web 安装器")
    print("="*60)
    print()
    
    # 创建 Web 界面 HTML
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 视频生成器 - 安装进度</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #667eea; margin-bottom: 10px; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; }
        .progress-section { text-align: center; margin: 30px 0; }
        .progress-bar {
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-success { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); }
        .log-box {
            background: #1a202c;
            color: #48bb78;
            padding: 20px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
        }
        .status-running { background: #bee3f8; color: #2c5282; }
        .status-success { background: #c6f6d5; color: #22543d; }
        .status-error { background: #fed7d7; color: #742a2a; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 视频生成器</h1>
        <div class="subtitle">安装进度</div>
        
        <div id="start-section">
            <p style="text-align: center; color: #4a5568; margin: 30px 0; font-size: 16px;">
                点击下方按钮开始安装 Python 依赖<br>
                安装过程约需 2-5 分钟
            </p>
            <div style="text-align: center;">
                <button class="btn" id="btn-start" onclick="startInstall()">
                    🚀 开始安装
                </button>
            </div>
        </div>
        
        <div id="progress-section" class="hidden">
            <div class="status status-running" id="status-running">
                ⏳ 安装进行中...
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
            </div>
            <div class="log-box" id="log-output"></div>
        </div>
        
        <div id="success-section" class="hidden">
            <div class="status status-success">
                ✅ 安装成功！
            </div>
            <p style="text-align: center; color: #4a5568; margin: 20px 0;">
                应用即将启动，请稍候...
            </p>
            <div style="text-align: center;">
                <p style="color: #667eea; font-size: 14px;">
                    如果应用没有自动启动，请点击下方按钮：
                </p>
                <button class="btn btn-success" onclick="window.open('http://localhost:5000', '_blank')" style="margin-top: 10px;">
                    打开应用
                </button>
            </div>
        </div>
        
        <div id="error-section" class="hidden">
            <div class="status status-error">
                ❌ 安装失败
            </div>
            <p id="error-message" style="text-align: center; color: #742a2a; margin: 20px 0;"></p>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn" onclick="location.reload()">重试</button>
            </div>
        </div>
    </div>
    
    <script>
        let pollingInterval = null;
        
        async function startInstall() {
            try {
                const response = await fetch('/api/start', { method: 'POST' });
                const result = await response.json();
                
                if (result.started) {
                    document.getElementById('start-section').classList.add('hidden');
                    document.getElementById('progress-section').classList.remove('hidden');
                    startPolling();
                }
            } catch (error) {
                alert('启动失败：' + error);
            }
        }
        
        function startPolling() {
            pollingInterval = setInterval(checkStatus, 1000);
        }
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                // 更新进度
                document.getElementById('progress-fill').style.width = status.progress + '%';
                document.getElementById('progress-fill').textContent = status.progress + '%';
                
                // 更新日志
                const logBox = document.getElementById('log-output');
                logBox.innerHTML = status.logs.map(log => '<div>' + log + '</div>').join('');
                logBox.scrollTop = logBox.scrollHeight;
                
                // 检查完成状态
                if (status.success) {
                    clearInterval(pollingInterval);
                    setTimeout(() => {
                        document.getElementById('progress-section').classList.add('hidden');
                        document.getElementById('success-section').classList.remove('hidden');
                        
                        // 2 秒后打开应用
                        setTimeout(() => {
                            window.open('http://localhost:5000', '_blank');
                        }, 2000);
                    }, 1000);
                }
                
                if (status.error) {
                    clearInterval(pollingInterval);
                    document.getElementById('progress-section').classList.add('hidden');
                    document.getElementById('error-section').classList.remove('hidden');
                    document.getElementById('error-message').textContent = status.error;
                }
            } catch (error) {
                console.error('检查状态失败:', error);
            }
        }
    </script>
</body>
</html>"""
    
    # 写入 HTML 文件
    html_path = Path(__file__).parent / "install_ui.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Web 界面已创建：{html_path}")
    print()
    
    # 打开浏览器
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}")
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
