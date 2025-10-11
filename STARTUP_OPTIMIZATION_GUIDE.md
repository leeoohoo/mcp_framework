# MCP Framework 启动优化指南

## 📋 问题分析

MCP Framework 打包的可执行文件启动缓慢的主要原因：

### 1. PyInstaller 配置问题
- 过度使用 `--collect-all` 导致包体积过大
- 包含了大量不必要的模块和依赖
- 缺乏优化选项（如 `--optimize`, `--strip`）

### 2. 启动时检查过多
- 虚拟环境创建增加构建时间
- 大量的依赖检查和模块导入分析
- 运行时模块发现和加载

### 3. 运行模式选择
- HTTP 模式比 stdio 模式启动更慢
- 不必要的 Web 界面初始化

## 🚀 优化方案

### 方案 1: 使用优化构建器

#### 1.1 使用内置优化选项

```bash
# 使用优化构建
mcp-build --optimize

# 或者构建特定服务器
mcp-build --server my_server.py --optimize
```

#### 1.2 使用独立优化构建器

```bash
# 使用优化构建器
python optimized_build.py my_server.py

# 创建快速启动器
python optimized_build.py my_server.py --create-launcher

# 生成启动脚本
python optimized_build.py my_server.py --create-startup-script
```

### 方案 2: 启动优化工具

#### 2.1 优化现有脚本

```bash
# 优化脚本并测试性能
python startup_optimization.py my_server.py --benchmark

# 只优化不测试
python startup_optimization.py my_server.py
```

#### 2.2 使用生成的优化启动器

```bash
# 使用优化后的快速启动器
python my_server_fast.py

# 或者使用环境变量优化
source env_my_server.sh
python my_server.py
```

### 方案 3: 环境变量优化

在运行前设置以下环境变量：

```bash
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=0
```

或者在 Python 脚本开头添加：

```python
import os
os.environ.update({
    'PYTHONOPTIMIZE': '2',
    'PYTHONDONTWRITEBYTECODE': '1',
    'PYTHONUNBUFFERED': '1',
    'PYTHONHASHSEED': '0'
})
```

### 方案 4: 使用简化启动器

修改服务器脚本使用 `simple_main`：

```python
from mcp_framework import simple_main

# 原来的复杂启动方式
# if __name__ == "__main__":
#     run_server_main(server, "MyServer")

# 优化后的简化启动方式
if __name__ == "__main__":
    simple_main(server, "MyServer")
```

### 方案 5: 选择合适的运行模式

```bash
# 推荐：使用 stdio 模式（最快）
python my_server.py stdio

# 避免：HTTP 模式（较慢）
python my_server.py http 8080
```

## 📊 性能对比

| 优化方案 | 启动时间改善 | 文件大小减少 | 实施难度 |
|---------|-------------|-------------|----------|
| 优化构建 | 40-60% | 30-50% | 简单 |
| 启动优化工具 | 20-40% | 0% | 简单 |
| 环境变量优化 | 10-20% | 0% | 极简单 |
| 简化启动器 | 30-50% | 0% | 简单 |
| stdio 模式 | 50-70% | 0% | 极简单 |

## 🛠️ 最佳实践

### 1. 开发阶段
```bash
# 快速测试构建
mcp-build --server my_server.py --optimize --no-test
```

### 2. 生产部署
```bash
# 完整优化构建
mcp-build --optimize --include-source

# 使用启动优化
python startup_optimization.py my_server.py --benchmark
```

### 3. 持续集成
```bash
# CI/CD 脚本
export PYTHONOPTIMIZE=2
mcp-build --optimize --no-test
```

### 4. 用户分发
```bash
# 创建用户友好的启动包
python optimized_build.py my_server.py --create-launcher --create-startup-script
```

## 🔧 高级优化技巧

### 1. 自定义 PyInstaller 配置

创建 `.spec` 文件进行精细控制：

```python
# my_server.spec
a = Analysis(
    ['my_server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['mcp_framework.core.base'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='my_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,  # 可能导致兼容性问题
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    optimize=2,
)
```

### 2. 使用 Nuitka 编译器

```bash
# 安装 Nuitka
pip install nuitka

# 编译服务器
python -m nuitka --onefile --follow-imports my_server.py
```

### 3. 创建自定义 PyInstaller Hook

```python
# hook-mcp_framework.py
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('mcp_framework.core')
```

### 4. 延迟导入策略

```python
# 在服务器代码中使用延迟导入
def get_heavy_module():
    import heavy_module
    return heavy_module

# 只在需要时导入
if some_condition:
    module = get_heavy_module()
```

## 🚨 注意事项

### 1. 兼容性问题
- UPX 压缩可能在某些系统上导致问题
- 过度优化可能影响功能完整性
- 测试优化后的可执行文件

### 2. 调试困难
- 优化构建的可执行文件难以调试
- 保留未优化版本用于开发

### 3. 平台差异
- Windows 和 Unix 系统的优化选项不同
- 测试目标平台的兼容性

## 📝 使用示例

### 完整优化工作流程

```bash
# 1. 创建服务器脚本
cat > weather_server.py << 'EOF'
from mcp_framework import EnhancedMCPServer, simple_main

server = EnhancedMCPServer(name="Weather", version="1.0.0")

@server.tool()
def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny"

if __name__ == "__main__":
    simple_main(server, "WeatherServer")
EOF

# 2. 优化构建
mcp-build --server weather_server.py --optimize

# 3. 创建启动优化
python startup_optimization.py weather_server.py --benchmark

# 4. 测试性能
echo "Testing original..."
time python weather_server.py --help

echo "Testing optimized..."
time python weather_server_fast.py --help

# 5. 使用优化的可执行文件
./dist/Weather
```

### 批量优化脚本

```bash
#!/bin/bash
# optimize_all.sh

echo "🚀 批量优化 MCP 服务器"

# 发现所有服务器脚本
for server in *_server.py; do
    if [ -f "$server" ]; then
        echo "📦 优化 $server..."
        
        # 优化构建
        mcp-build --server "$server" --optimize --no-test
        
        # 创建启动优化
        python startup_optimization.py "$server"
        
        echo "✅ $server 优化完成"
    fi
done

echo "🎉 所有服务器优化完成！"
```

## 🔍 故障排除

### 常见问题

1. **优化后无法启动**
   ```bash
   # 检查依赖
   python startup_optimization.py my_server.py --benchmark
   
   # 使用标准构建
   mcp-build --server my_server.py
   ```

2. **功能缺失**
   ```bash
   # 添加缺失的隐藏导入
   mcp-build --server my_server.py --optimize --no-test
   ```

3. **启动仍然很慢**
   ```bash
   # 使用 stdio 模式
   python my_server.py stdio
   
   # 检查环境变量
   env | grep PYTHON
   ```

## 📚 参考资源

- [PyInstaller 官方文档](https://pyinstaller.readthedocs.io/)
- [Python 性能优化指南](https://docs.python.org/3/howto/perf_profiling.html)
- [MCP Framework 文档](./README.md)

---

**提示**: 建议从简单的优化开始（环境变量、stdio 模式），然后逐步应用更高级的优化技术。