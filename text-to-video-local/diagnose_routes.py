#!/usr/bin/env python3
"""诊断 Flask 路由注册问题"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from web.app import app

print("=" * 70)
print(" Flask 路由诊断")
print("=" * 70)
print(f"应用：{app}")
print(f"路由数：{len(app.url_map._rules)}")
print()

# 检查关键 API
critical_apis = [
    ('检查依赖', '/api/check-dependencies'),
    ('安装依赖', '/api/install-dependencies'),
    ('任务状态', '/api/task/<task_id>'),
    ('下载 FFmpeg', '/api/download-ffmpeg'),
]

print("关键 API 检查:")
for name, api in critical_apis:
    found = False
    for rule in app.url_map.iter_rules():
        if api.replace('<task_id>', '') in str(rule):
            found = True
            break
    status = '✅' if found else '❌'
    print(f"  {status} {name}: {api}")

print()
print("=" * 70)
print(" 如果所有 API 都显示 ✅，但前端仍然 404:")
print("  1. 确认 Flask 服务已重启")
print("  2. 检查浏览器控制台的网络请求 URL")
print("  3. 确认请求方法是 POST 还是 GET")
print("=" * 70)
