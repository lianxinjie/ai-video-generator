# 依赖检测优化报告

## 问题描述

**症状：**
- 依赖安装成功
- 安装后验证通过
- 但前端检测显示"未安装"

**根本原因：**
- 检测逻辑没有详细日志，无法定位问题
- 前端可能缓存了旧的 API 响应
- Python 环境不一致可能性未排除

## 优化方案

### 1. 后端优化 (`web/app.py`)

#### 优化前
```python
packages = {...}  # 包定义

for module_name, info in packages.items():
    spec = importlib.util.find_spec(info.get('module_name', module_name))
    if spec is not None:
        try:
            module = importlib.import_module(...)
            packages[module_name]['installed'] = True
        except:
            pass  # 静默失败
```

**问题：**
- 没有日志输出
- 异常被静默忽略
- 无法知道哪个步骤失败

#### 优化后
```python
print(f"\n[依赖检测] ====== 开始检测 {len(packages)} 个包 ======")
print(f"[依赖检测] Python: {sys.executable}")

for module_name, info in packages.items():
    import_name = info.get('module_name', module_name)
    try:
        # 步骤 1: 检查模块是否存在
        spec = importlib.util.find_spec(import_name)
        
        if spec is None:
            print(f"[依赖检测] ✗ {module_name}: 模块未找到")
            packages[module_name]['installed'] = False
            continue
        
        # 步骤 2: 尝试导入模块
        module = importlib.import_module(import_name)
        
        # 步骤 3: 获取版本信息
        try:
            version = importlib.metadata.version(info['pip_name'])
        except importlib.metadata.PackageNotFoundError:
            version = getattr(module, '__version__', 'unknown')
        
        # 步骤 4: 标记为已安装
        packages[module_name]['installed'] = True
        packages[module_name]['version'] = version
        print(f"[依赖检测] ✓ {module_name}: {version}")
        
    except ModuleNotFoundError as e:
        print(f"[依赖检测] ✗ {module_name}: 模块导入失败 - {str(e)[:50]}")
        packages[module_name]['installed'] = False
    except ImportError as e:
        print(f"[依赖检测] ✗ {module_name}: 导入错误 - {str(e)[:50]}")
        packages[module_name]['installed'] = False
    except Exception as e:
        print(f"[依赖检测] ✗ {module_name}: 未知错误 - {str(e)[:50]}")
        packages[module_name]['installed'] = False

print(f"[依赖检测] 汇总：{installed}/{total} 已安装")
print(f"[依赖检测] 缺少必需：{required_missing if required_missing else '无'}")
print(f"[依赖检测] ====== 检测完成 ======\n")
```

**改进：**
- ✅ 每次检测重新初始化包列表（避免缓存）
- ✅ 显示 Python 可执行文件路径
- ✅ 详细记录每个包的检测状态
- ✅ 区分 ModuleNotFoundError、ImportError、Exception
- ✅ 显示汇总统计

### 2. 前端优化 (`web/templates/setup_wizard.html`)

#### 优化前
```javascript
const response = await fetch('/api/check-dependencies');
const data = await response.json();
```

**问题：**
- 浏览器可能缓存 API 响应
- 没有调试日志

#### 优化后
```javascript
// 添加时间戳防止缓存
const response = await fetch('/api/check-dependencies?t=' + Date.now());
const data = await response.json();

// 调试日志
console.log('[前端] 收到检测响应:', data);
console.log('[前端] 包数量:', Object.keys(data.packages).length);
for (const [name, info] of Object.entries(data.packages)) {
    console.log(`[前端] ${name}: installed=${info.installed}, version=${info.version}`);
}
```

**改进：**
- ✅ 添加时间戳防止浏览器缓存
- ✅ Console.log 显示每个包的状态
- ✅ 便于前端调试

## 测试方法

### 1. 后端日志
```
[依赖检测] ====== 开始检测 10 个包 ======
[依赖检测] Python: C:\Users\...\python.exe
[依赖检测] ✓ flask: 3.1.3
[依赖检测] ✓ torch: 2.11.0+cpu
[依赖检测] ✓ diffusers: 0.38.0
...
[依赖检测] 汇总：10/10 已安装
[依赖检测] 缺少必需：无
[依赖检测] ====== 检测完成 ======
```

### 2. 前端 Console
```
[前端] 收到检测响应：{packages: {...}, summary: {...}}
[前端] 包数量：10
[前端] flask: installed=true, version=3.1.3
[前端] torch: installed=true, version=2.11.0+cpu
[前端] diffusers: installed=true, version=0.38.0
...
```

### 3. 网络请求
- URL: `/api/check-dependencies?t=1683456789`
- 方法：GET
- 响应：`{packages: {...}, summary: {...}}`

## 预期结果

**成功的标志：**
1. Flask 控制台显示所有包检测成功
2. 浏览器 Console 显示 `installed=true`
3. 页面显示所有包为绿色 ✓ 状态
4. 版本信息正确显示

**如果仍然失败：**
- Flask 日志会显示哪个包检测失败
- 错误信息会明确指出原因
- 便于快速定位和修复

## 提交记录

- `perf: 优化依赖检测逻辑` - 后端详细日志
- `feat: 添加前端调试日志和防缓存` - 前端优化
- `docs: 添加 Windows 测试指南` - 测试文档

---

**测试环境：** Windows 10/11, Python 3.13+
**测试版本：** 260501-feat-add-hybrid-mode
