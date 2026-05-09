#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 增强版
- 支持云端 AI 整合功能
- 自动检测与安装依赖
- 完善的错误处理与日志
- 支持本地模型和云端 AI 双模式
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# =====================
# 全局配置
# =====================
PROJECT_ROOT = Path(__file__).parent.absolute()
WEB_DIR = PROJECT_ROOT / "web"
MODELS_DIR = PROJECT_ROOT / "models"
CLOUD_COOKIES_DIR = PROJECT_ROOT / "cloud_cookies"
LOG_FILE = PROJECT_ROOT / "quick_start.log"

# 确保必要目录存在
for dir_path in [WEB_DIR, MODELS_DIR, CLOUD_COOKIES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# =====================
# 日志工具函数
# =====================
def log(message, level="INFO"):
    """记录日志到文件和控制台"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    # 输出到控制台
    if level == "ERROR":
        print(f"  ❌ {message}")
    elif level == "WARNING":
        print(f"  ⚠️  {message}")
    elif level == "SUCCESS":
        print(f"  ✅ {message}")
    else:
        print(f"  ℹ️  {message}")
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass


# =====================
# 依赖检查与安装
# =====================
def check_flask():
    """检查 Flask 是否已安装（不导入）"""
    try:
        import importlib.util
        spec = importlib.util.find_spec("flask")
        return spec is not None
    except Exception as e:
        log(f"Flask 检查失败：{e}", "ERROR")
        return False


def install_missing_deps():
    """自动安装缺失的依赖"""
    log("检测必要依赖...")
    
    missing = []
    deps = {
        'flask': ('Flask', 'Web 服务'),
        'pillow': ('Pillow', '图像处理'),
        'psutil': ('psutil', '系统监控'),
        'pydub': ('pydub', '音频处理'),
        'edge_tts': ('edge-tts', '语音合成'),
        'transformers': ('transformers', 'AI 模型'),
        'huggingface_hub': ('huggingface-hub', '模型下载')
    }
    
    for package, (name, desc) in deps.items():
        try:
            __import__(package.replace('-', '_'))
            log(f"{name} - 已安装", "SUCCESS")
        except ImportError:
            log(f"{name} - 缺失", "WARNING")
            missing.append((package, name))
    
    if missing:
        log("正在安装缺失的依赖...")
        import subprocess
        
        for package, name in missing:
            log(f"  安装 {name}...", "INFO")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package, "-q"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    log(f"  {name} 安装成功", "SUCCESS")
                else:
                    log(f"  {name} 安装失败：{result.stderr[:200]}", "ERROR")
            except subprocess.TimeoutExpired:
                log(f"  {name} 安装超时", "ERROR")
            except Exception as e:
                log(f"  {name} 安装异常：{e}", "ERROR")
    
    return len(missing) == 0


# =====================
# 云端 AI 配置检查
# =====================
def check_cloud_ai_config():
    """检查云端 AI 配置"""
    log("检查云端 AI 配置...", "INFO")
    
    # 确保目录存在
    if not CLOUD_COOKIES_DIR.exists():
        CLOUD_COOKIES_DIR.mkdir(parents=True, exist_ok=True)
        log("创建云端 AI 配置目录", "SUCCESS")
    
    # 统计配置数量
    config_files = list(CLOUD_COOKIES_DIR.glob("*.json"))
    if config_files:
        log(f"找到 {len(config_files)} 个云端 AI 配置", "SUCCESS")
        for config_file in config_files[:5]:  # 显示前 5 个
            log(f"  - {config_file.stem}", "INFO")
    else:
        log("暂无云端 AI 配置，可通过 Web 界面添加", "INFO")
    
    return True


# =====================
# Flask 应用启动（增强版）
# =====================
def start_with_flask():
    """启动 Flask 应用（增强错误处理）"""
    log("启动 Flask 应用...", "INFO")
    
    try:
        # 1. 预检查 app.py 是否有语法错误
        log("预检查 web/app.py 语法...", "INFO")
        import subprocess
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); from web.app import app"
        ], capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=30)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()[:500] if result.stderr else "未知错误"
            log(f"app.py 语法检查失败：{error_msg}", "ERROR")
            log("建议：先修复 web/app.py 中的语法错误", "WARNING")
            return False, None
        
        log("app.py 语法检查通过", "SUCCESS")
        
        # 2. 导入 Flask 和应用
        from flask import Flask, render_template, jsonify, request
        sys.path.insert(0, str(WEB_DIR))
        from app import app
        
        # 3. 启动浏览器线程
        def open_browser():
            time.sleep(2.5)
            webbrowser.open('http://localhost:5000')
            log("已自动打开浏览器", "INFO")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # 4. 返回应用对象（由 main 函数启动）
        log("Flask 应用初始化成功", "SUCCESS")
        return True, app
        
    except ImportError as e:
        log(f"导入错误：{e}", "ERROR")
        log("请运行：pip install flask", "WARNING")
        return False, None
    except Exception as e:
        log(f"Flask 启动异常：{e}", "ERROR")
        import traceback
        log(f"详细错误：{traceback.format_exc()}", "ERROR")
        return False, None


# =====================
# 无 Flask 时的 HTTP 服务器
# =====================
def start_without_flask():
    """在没有 Flask 时启动简单的 HTTP 服务器"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    
    log("Flask 未安装，启动快速预览模式...", "WARNING")
    
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
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; color: white; text-align: center; }
        .container { background: rgba(255,255,255,0.95); color: #333; padding: 40px; border-radius: 20px; max-width: 600px; }
        h1 { color: #667eea; margin-bottom: 20px; }
        p { margin: 15px 0; font-size: 16px; line-height: 1.6; }
        .btn { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; margin: 10px; }
        .success { color: #4CAF50; }
        .error { color: #F44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 视频生成器</h1>
        <p><strong>预览模式（Flask 未安装）</strong></p>
        <p class="success">✅ 核心服务已启动</p>
        <p>请安装 Flask 以获得完整功能：</p>
        <code style="background: #f5f5f5; padding: 10px; display: block; margin: 10px 0;">""" + sys.executable + """ -m pip install flask</code>
        <p style="color: #999; font-size: 14px;">当前可用功能：</p>
        <ul style="text-align: left;">
            <li>✅ 基础文件服务</li>
            <li>✅ 静态页面访问</li>
            <li>❌ 云端 AI 整合</li>
            <li>❌ 模型下载管理</li>
            <li>❌ 视频生成功能</li>
        </ul>
        <a href="web/templates/setup_wizard.html" class="btn">打开安装向导</a>
    </div>
</body>
</html>"""
                self.wfile.write(html.encode('utf-8'))
            else:
                super().do_GET()
    
    # 启动服务器
    server = HTTPServer(('0.0.0.0', 8080), QuickStartHandler)
    
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://localhost:8080')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    log("快速预览模式已启动", "SUCCESS")
    log("访问地址：http://localhost:8080", "INFO")
    log("提示：安装 Flask 以获得完整功能", "WARNING")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("服务已停止", "INFO")


# =====================
# 主函数
# =====================
def print_banner():
    """打印启动横幅"""
    print("=" * 70)
    print("  🎬 AI 视频生成器 - 快速启动")
    print("=" * 70)
    print()
    print(f"操作系统：{os.name.title()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"项目路径：{PROJECT_ROOT}")
    print("=" * 70)


def main():
    """主函数"""
    print_banner()
    
    # 1. 安装依赖
    deps_ok = install_missing_deps()
    
    # 2. 检查云端 AI 配置
    cloud_ok = check_cloud_ai_config()
    
    # 3. 检查 Flask
    if check_flask():
        log("Flask: 已安装", "SUCCESS")
        try:
            import importlib.metadata
            version = importlib.metadata.version("flask")
            log(f"版本：{version}", "INFO")
        except:
            pass
        
        log("启动完整功能模式...", "INFO")
        
        # 4. 启动 Flask 应用
        success, app = start_with_flask()
        
        if success and app:
            log("=" * 70, "INFO")
            log("✅ 所有功能初始化完成！", "SUCCESS")
            log("=" * 70, "INFO")
            log("\n🌐 访问地址:", "INFO")
            log("   http://localhost:5000", "INFO")
            log("   http://127.0.0.1:5000", "INFO")
            log("\n📋 功能列表:", "INFO")
            log("   ✅ 云端 AI 整合（豆包/文心一言/通义千问）", "SUCCESS")
            log("   ✅ 模型下载管理（断点续传/多线程）", "SUCCESS")
            log("   ✅ FFmpeg 管理（自动下载/解压）", "SUCCESS")
            log("   ✅ 视频生成（本地模型/云端 AI 双模式）", "SUCCESS")
            log("\n按 Ctrl+C 停止服务\n", "INFO")
            
            # 启动 Flask 应用
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        else:
            log("Flask 启动失败，切换到快速预览模式", "WARNING")
            start_without_flask()
    else:
        log("Flask: 未安装", "WARNING")
        start_without_flask()
    
    return 0


# =====================
# 程序入口
# =====================
if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 程序已由用户中断退出")
        sys.exit(0)
    except Exception as e:
        log(f"程序异常退出：{e}", "ERROR")
        import traceback
        log(f"详细错误：{traceback.format_exc()}", "ERROR")
        sys.exit(1)
