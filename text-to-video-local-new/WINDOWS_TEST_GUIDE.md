# Windows 环境依赖检测测试指南

## 问题背景
之前依赖安装成功但检测显示未安装，现已优化检测逻辑。

## 优化内容

### 后端优化
1. **每次检测重新初始化包列表** - 避免缓存问题
2. **详细检测日志** - 显示 Python 路径和每个包状态
3. **异常处理** - 捕获 ModuleNotFoundError、ImportError 等
4. **清晰的检测步骤**:
   - 步骤 1: 检查模块是否存在 (find_spec)
   - 步骤 2: 尝试导入模块 (import_module)
   - 步骤 3: 获取版本信息 (metadata.version)
   - 步骤 4: 标记为已安装 (installed=True)

### 前端优化
1. **添加时间戳** - 防止浏览器缓存 API 响应
2. **console.log 调试** - 显示每个包的 detected 状态
3. **数据遍历验证** - 确认收到正确的 JSON

## 测试步骤

### 1. 拉取最新代码
```powershell
cd ai-video-generator
git fetch origin
git reset --hard origin/260501-feat-add-hybrid-mode
```

### 2. 完全重启服务
```powershell
# 停止当前服务 (Ctrl+C)
taskkill /F /IM python.exe

# 重新启动
python quick_start.py
```

### 3. 访问 Setup 页面
```
http://localhost:5000/setup
```

### 4. 查看 Flask 控制台输出

**应该看到类似日志：**
```
[依赖检测] ====== 开始检测 10 个包 ======
[依赖检测] Python: C:\Users\...\python.exe
[依赖检测] ✓ flask: 3.1.3
[依赖检测] ✓ PIL: 12.2.0
[依赖检测] ✓ torch: 2.11.0+cpu
[依赖检测] ✓ diffusers: 0.38.0
[依赖检测] ✓ modelscope: 1.36.3
[依赖检测] ✓ pydub: 0.25.1
[依赖检测] ✓ transformers: 5.8.0
[依赖检测] ✓ huggingface_hub: 1.13.0
[依赖检测] ✓ edge_tts: 7.2.8
[依赖检测] ✓ psutil: 7.2.2
[依赖检测] 汇总：10/10 已安装
[依赖检测] 缺少必需：无
[依赖检测] ====== 检测完成 ======
```

### 5. 打开浏览器开发者工具

**按 F12 打开开发者工具：**

1. **Console 标签** - 应该看到：
   ```
   [前端] 收到检测响应：{packages: {...}, summary: {...}}
   [前端] 包数量：10
   [前端] flask: installed=true, version=3.1.3
   [前端] torch: installed=true, version=2.11.0+cpu
   [前端] diffusers: installed=true, version=0.38.0
   ...
   ```

2. **Network 标签** - 查看 API 响应：
   - 找到 `api/check-dependencies?t=123456789`
   - 点击请求
   - 查看 **Response** 标签
   - 确认 JSON 中 `packages.*.installed=true`

### 6. 检查页面显示

**所有包应该显示：**
- ✓ Flask (必需) - 3.1.3
- ✓ Pillow (必需) - 12.2.0
- ✓ PyTorch (必需) - 2.11.0+cpu
- ✓ Diffusers (必需) - 0.38.0
- ✓ ModelScope (必需) - 1.36.3
- ✓ Pydub (可选) - 0.25.1
- ✓ Transformers (必需) - 5.8.0
- ✓ Huggingface Hub (必需) - 1.13.0
- ✓ Edge TTS (可选) - 7.2.8
- ✓ psutil (必需) - 7.2.2

**如果还有未显示的，请提供：**
1. Flask 控制台的完整检测日志
2. 浏览器 Console 的完整输出
3. Network 中 API 响应的 JSON 内容

## 常见问题

### Q: 控制台没有检测日志
**A:** Flask 服务可能没有重新加载
```powershell
taskkill /F /IM python.exe
python quick_start.py
```

### Q: 浏览器 Console 没有日志
**A:** 页面可能使用了缓存
- 按 **Ctrl + Shift + R** 强制刷新
- 或 **Ctrl + F5** 清除缓存刷新

### Q: API 返回 404
**A:** 代码可能没有更新
```powershell
git log --oneline -3
# 应该看到最新的 commit
```

## 测试通过标准

- [ ] Flask 控制台显示所有包检测成功
- [ ] 浏览器 Console 显示 `installed=true`
- [ ] 页面显示所有包为绿色 ✓ 状态
- [ ] 版本信息正确显示

---

**测试完成后，请将结果反馈给开发团队！**
