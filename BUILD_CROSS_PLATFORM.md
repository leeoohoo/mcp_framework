# MCP Framework 跨平台构建指南

本 MCP Framework 支持在 macOS 上构建 Windows 和 Linux 版本的可执行文件。

## 前提条件

### 必需
- Python 3.11+
- Docker Desktop（用于跨平台构建，可选）

### 安装 Docker Desktop（可选）
1. 访问 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 下载并安装适合你操作系统的版本
3. 启动 Docker Desktop

**注意**: 如果 Docker 不可用，你仍然可以在对应的目标平台上直接运行构建脚本。

## 构建方法

### 方法 1: 使用跨平台构建脚本（推荐）

```bash
# 构建所有平台（本地 + Linux + Windows）
python build_cross_platform.py --platform all

# 只构建 Windows 版本
python build_cross_platform.py --platform windows

# 只构建 Linux 版本
python build_cross_platform.py --platform linux

# 只构建本地平台
python build_cross_platform.py --platform native

# 构建特定服务器的 Windows 版本
python build_cross_platform.py --platform windows --server weather_server.py
```

### 方法 2: 使用 Docker Compose

```bash
# 构建 Windows 版本
docker-compose --profile build up build-windows

# 构建 Linux 版本
docker-compose --profile build up build-linux

# 构建所有跨平台版本
docker-compose --profile build up
```

### 方法 3: 手动跨平台构建（无需 Docker）

如果 Docker 不可用，你可以在目标平台上直接运行构建脚本：

#### 在 Windows 机器上构建 Windows 版本
1. 安装 Python 3.11+
2. 克隆项目到 Windows 机器
3. 运行构建脚本：
   ```cmd
   python mcp_framework/build.py --no-test
   ```

#### 在 Linux 机器上构建 Linux 版本
1. 安装 Python 3.11+
2. 克隆项目到 Linux 机器
3. 运行构建脚本：
   ```bash
   python mcp_framework/build.py --no-test
   ```

## 构建选项

所有构建方法都支持以下选项：

- `--server <script>`: 构建特定服务器（如 `weather_server.py`）
- `--no-test`: 跳过测试
- `--no-clean`: 跳过清理构建目录
- `--include-source`: 在包中包含源代码
- `--list`: 列出所有可用的服务器脚本

## 输出文件

构建完成后，所有平台的可执行文件和分发包都会保存在 `dist/` 目录中：

```
dist/
├── mcp-framework-macos-arm64-20241220-143022.tar.gz     # macOS 版本
├── mcp-framework-linux-x86_64-20241220-143022.tar.gz    # Linux 版本
├── mcp-framework-windows-amd64-20241220-143022.zip      # Windows 版本
```

## 使用示例

### 快速开始

```bash
# 检查 Docker 是否可用
python build_cross_platform.py --check-docker

# 构建所有平台
python build_cross_platform.py --platform all

# 只构建当前平台（不需要 Docker）
python build_cross_platform.py --platform native
```

### 高级用法

```bash
# 构建特定服务器的所有平台版本
python build_cross_platform.py --platform all --server my_server.py

# 跳过测试，快速构建
python build_cross_platform.py --platform all --no-test

# 包含源代码的完整包
python build_cross_platform.py --platform all --include-source
```

## 故障排除

### Docker 相关问题

1. **Docker 未启动**
   ```bash
   # 检查 Docker 状态
   docker --version
   
   # 启动 Docker Desktop
   open -a Docker
   ```

2. **权限问题**
   ```bash
   # 确保 Docker 有足够权限访问项目目录
   sudo chown -R $(whoami) ./dist
   ```

3. **镜像构建失败**
   ```bash
   # 清理 Docker 缓存
   docker system prune -f
   
   # 重新构建镜像
   docker-compose --profile build up --build
   ```

### 构建问题

1. **依赖缺失**
   - 确保 `requirements.txt` 包含所有必需的依赖
   - 检查特定服务器的 `*_requirements.txt` 文件

2. **PyInstaller 错误**
   - 检查隐藏导入是否完整
   - 查看构建日志中的详细错误信息

3. **平台兼容性**
   - 某些 Python 包可能不支持所有平台
   - 检查依赖的平台兼容性

## 注意事项

1. **性能**: Docker 构建可能比本地构建慢，特别是首次构建时
2. **存储**: 跨平台构建会生成多个大文件，确保有足够的磁盘空间
3. **网络**: Docker 镜像下载需要稳定的网络连接
4. **兼容性**: 确保目标平台支持你使用的 Python 包

## 自动化构建

你可以将跨平台构建集成到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
name: Cross-Platform Build
on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: python mcp_framework/build.py --no-test
```