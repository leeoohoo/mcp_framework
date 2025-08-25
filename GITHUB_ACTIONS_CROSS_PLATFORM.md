# GitHub Actions 跨平台构建指南

本指南介绍如何使用 MCP Framework 的 GitHub Actions 工作流来构建支持 4 个平台的 MCP 服务器。

## 🎯 支持的平台

| 平台 | 架构 | 构建方式 | GitHub Runner |
|------|------|----------|---------------|
| Linux | x86_64 | Docker 跨平台构建 | ubuntu-latest |
| Windows | x86_64 | Docker 跨平台构建 | windows-latest |
| macOS Intel | x86_64 | 本地构建 | macos-13 |
| macOS Apple Silicon | ARM64 | 本地构建 | macos-latest |

## 🚀 快速开始

### 1. 设置工作流文件

工作流文件已经创建在 `.github/workflows/cross-platform-build.yml`，包含以下功能：

- ✅ 自动检测服务器脚本
- ✅ 四平台并行构建
- ✅ 构建产物上传
- ✅ 自动发布到 GitHub Releases
- ✅ 构建状态摘要

### 2. 触发构建

#### 自动触发
```bash
# 推送到主分支触发构建
git push origin main

# 创建标签触发构建和发布
git tag v1.0.0
git push origin v1.0.0
```

#### 手动触发
1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Cross-Platform Build" 工作流
4. 点击 "Run workflow"
5. 输入服务器脚本文件名（例如：`my_server.py`）
6. 选择构建平台（默认为 `all`）

## 📁 项目结构要求

确保您的项目具有以下结构：

```
your-mcp-project/
├── .github/
│   └── workflows/
│       └── cross-platform-build.yml
├── your_server.py              # 您的 MCP 服务器脚本
├── requirements.txt            # 项目依赖（可选）
├── pyproject.toml             # 项目配置
└── README.md
```

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PYTHON_VERSION` | `3.11` | Python 版本 |
| `SERVER_SCRIPT` | `test_server.py` | 服务器脚本文件名 |

### 工作流输入参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `server_script` | string | `test_server.py` | 服务器脚本文件名 |
| `build_platform` | choice | `all` | 构建平台选择 |

## 📦 构建产物

### 产物命名规则

```
{服务器名称}-{平台}-{架构}-{时间戳}.tar.gz
```

示例：
- `my-server-linux-x86_64-20240825_140632.tar.gz`
- `my-server-windows-x86_64-20240825_140632.zip`
- `my-server-macos-x86_64-20240825_140632.tar.gz`
- `my-server-macos-arm64-20240825_140632.tar.gz`

### 产物内容

每个构建产物包含：
- 可执行文件
- 配置文件目录
- 数据文件目录
- 启动脚本（Windows/Linux）
- 依赖文件

## 🎯 使用示例

### 示例 1：构建单个服务器

```yaml
# 手动触发时的输入
server_script: "weather_server.py"
build_platform: "all"
```

### 示例 2：仅构建 macOS 版本

```yaml
server_script: "weather_server.py"
build_platform: "macos"
```

### 示例 3：自动发布

```bash
# 创建发布标签
git tag v1.2.0
git push origin v1.2.0

# 工作流将自动：
# 1. 构建所有平台
# 2. 创建 GitHub Release
# 3. 上传所有构建产物
```

## 🔍 故障排除

### 常见问题

#### 1. 服务器脚本未找到
```
❌ 服务器脚本不存在: my_server.py
```

**解决方案：**
- 确保脚本文件在项目根目录
- 检查文件名拼写
- 确保文件已提交到 Git

#### 2. Docker 构建失败
```
❌ Docker build failed
```

**解决方案：**
- 检查网络连接
- 查看 Docker 日志
- 确保依赖项正确

#### 3. macOS 构建失败
```
❌ macos build failed
```

**解决方案：**
- 检查 Python 版本兼容性
- 确保所有依赖支持 macOS
- 查看具体错误信息

### 调试技巧

#### 1. 启用详细日志

在工作流中添加：
```yaml
- name: Debug build
  run: |
    python -m mcp_framework.build --platform native --server ${{ env.SERVER_SCRIPT }} --no-test
  env:
    PYTHONPATH: .
    DEBUG: 1
```

#### 2. 检查构建环境

```yaml
- name: Debug environment
  run: |
    echo "Python version: $(python --version)"
    echo "Platform: $(python -c 'import platform; print(platform.platform())')"
    echo "Architecture: $(python -c 'import platform; print(platform.machine())')"
    pip list
```

## 📊 性能优化

### 1. 缓存优化

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 2. 并行构建

工作流已配置为并行构建所有平台，通常需要 5-10 分钟完成。

### 3. 构建产物压缩

```yaml
compression-level: 6  # 平衡压缩率和速度
```

## 🔐 安全最佳实践

### 1. 密钥管理

- 使用 GitHub Secrets 存储敏感信息
- 不要在代码中硬编码密钥
- 定期轮换访问令牌

### 2. 权限控制

```yaml
permissions:
  contents: read
  packages: write
  actions: read
```

### 3. 依赖安全

- 定期更新依赖项
- 使用 `pip-audit` 检查安全漏洞
- 固定依赖版本

## 📈 监控和分析

### 1. 构建时间监控

查看 Actions 页面的构建时间趋势，优化慢速步骤。

### 2. 成功率统计

监控不同平台的构建成功率，识别问题平台。

### 3. 产物大小分析

定期检查构建产物大小，优化打包策略。

## 🚀 高级配置

### 1. 自定义构建矩阵

```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        platform: linux
        arch: x86_64
        python-version: '3.11'
        extra-flags: '--optimize'
```

### 2. 条件构建

```yaml
if: contains(github.event.head_commit.message, '[build-all]')
```

### 3. 多服务器构建

```yaml
strategy:
  matrix:
    server: ['server1.py', 'server2.py', 'server3.py']
```

## 📚 相关文档

- [MCP Framework 构建指南](BUILD_CROSS_PLATFORM.md)
- [Docker 跨平台构建](CROSS_PLATFORM_BUILD_GUIDE.md)
- [GitHub Actions 官方文档](https://docs.github.com/en/actions)

## 🤝 贡献

如果您发现问题或有改进建议，请：

1. 创建 Issue 描述问题
2. 提交 Pull Request
3. 更新相关文档

---

**注意：** 确保您的 GitHub 仓库已启用 Actions，并且有足够的 Actions 分钟数来运行跨平台构建。