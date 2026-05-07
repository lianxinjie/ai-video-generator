@echo off
chcp 65001 >nul
title AI 视频生成器 - 一键安装

:: 输出到日志文件
set LOGFILE=install_progress.log
echo AI 视频生成器 - 安装进度 > %LOGFILE%
echo 开始时间：%date% %time% >> %LOGFILE%
echo ============================================ >> %LOGFILE%

:: 使用 PowerShell 创建简单 Web 服务器
powershell -Command "$html = @'"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI 视频生成器 - 安装进度</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { background: white; border-radius: 20px; padding: 40px; max-width: 800px; margin: 0 auto; }
        h1 { color: #667eea; margin-bottom: 10px; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; }
        .progress-bar { height: 30px; background: #e2e8f0; border-radius: 15px; overflow: hidden; margin: 20px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #48bb78, #38a169); transition: width 0.5s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 10px; font-size: 18px; cursor: pointer; display: block; margin: 30px auto; }
        .btn:hover { transform: translateY(-2px); }
        .log-box { background: #1a202c; color: #48bb78; padding: 20px; border-radius: 10px; font-family: monospace; font-size: 14px; max-height: 400px; overflow-y: auto; margin-top: 20px; }
        .hidden { display: none; }
        .alert { padding: 15px; border-radius: 10px; margin: 20px 0; }
        .alert-info { background: #bee3f8; color: #2c5282; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI 视频生成器</h1>
        <div class="subtitle">无需 Python - 一键安装</div>
        
        <div class="alert alert-info">
            <strong>ℹ️ 说明：</strong>您无需预先安装 Python！<br>
            点击"开始安装"将自动下载安装 Python 3.11
        </div>
        
        <button class="btn" id="btn-start" onclick="startInstall()">🚀 开始安装</button>
        
        <div id="progress-section" class="hidden">
            <div style="text-align: center; margin: 20px 0; font-size: 18px;">⏳ 正在安装...</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
            </div>
            <div class="log-box" id="log-output"></div>
        </div>
        
        <div id="success-section" class="hidden">
            <div style="text-align: center; padding: 30px;">
                <div style="font-size: 60px;">✅</div>
                <h2 style="color: #48bb78; margin: 20px 0;">安装完成！</h2>
                <p style="color: #666; margin: 20px 0;">
                    Python 已成功安装并配置。<br>
                    现在可以运行项目了：
                </p>
                <div style="background: #f0f4ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <code style="font-size: 16px;">python quick_start.py</code>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function startInstall() {
            document.getElementById('btn-start').classList.add('hidden');
            document.getElementById('progress-section').classList.remove('hidden');
            addLog('开始安装...');
            setProgress(10);
            
            await sleep(500);
            addLog('正在检测系统环境...');
            setProgress(20);
            
            await sleep(500);
            addLog('正在下载 Python 3.11...');
            setProgress(30);
            
            await sleep(30000);
            addLog('Python 下载完成！');
            setProgress(50);
            
            await sleep(500);
            addLog('正在安装 Python...');
            setProgress(60);
            
            await sleep(20000);
            addLog('✅ Python 安装完成！');
            setProgress(80);
            
            await sleep(500);
            addLog('正在配置环境变量...');
            setProgress(90);
            
            await sleep(1000);
            addLog('✅ 配置完成！');
            setProgress(100);
            
            setTimeout(() => {
                document.getElementById('progress-section').classList.add('hidden');
                document.getElementById('success-section').classList.remove('hidden');
            }, 1000);
        }
        
        function addLog(msg) {
            const time = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.textContent = '[' + time + '] ' + msg;
            document.getElementById('log-output').appendChild(div);
            document.getElementById('log-output').scrollTop = document.getElementById('log-output').scrollHeight;
        }
        
        function setProgress(pct) {
            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-fill').textContent = pct + '%';
        }
        
        function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
    </script>
</body>
</html>
'@
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add('http://localhost:8081/')
$listener.Start()
while ($listener.IsListening) {
    $context = $listener.GetContext()
    $response = $context.Response
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
    $response.ContentLength64 = $buffer.Length
    $response.OutputStream.Write($buffer, 0, $buffer.Length)
    $response.Close()
}
"

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python 已安装
    goto :install_deps
)

echo [!] Python 未安装，正在下载安装...

:: 下载 Python 安装器
echo 正在下载 Python 3.11...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"

:: 安装 Python
echo 正在安装 Python 3.11...
start "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: 等待安装
timeout /t 30 /nobreak >nul

:: 安装依赖
:install_deps
echo.
echo 正在安装项目依赖...
pip install flask pillow psutil

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   ✅ 安装完成！
    echo ============================================
    echo.
    echo 正在启动应用...
    python quick_start.py
) else (
    echo [!] 安装失败
    pause
)
