# MCP Framework --output-dir 参数使用指南

## 概述

`mcp-framework` 现在支持 `--output-dir` 参数，允许您指定自定义的构建输出目录，而不是使用默认的 `dist` 目录。

## 功能特性

- ✅ **自定义输出目录**: 指定任意路径作为构建产物的输出位置
- ✅ **避免文件覆盖**: 每个构建可以使用独立的输出目录
- ✅ **支持相对和绝对路径**: 灵活的路径指定方式
- ✅ **跨平台兼容**: 支持 Windows、macOS、Linux
- ✅ **Docker 构建支持**: 跨平台构建时也支持自定义输出目录

## 使用方法

### 基本用法

```bash
# 使用自定义输出目录
python -m mcp_framework.build --server your_server.py --output-dir /path/to/custom/output

# 使用相对路径
python -m mcp_framework.build --server your_server.py --output-dir ./custom_build

# 简写形式
python -m mcp_framework.build --server your_server.py -o ./output
```

### 跨平台构建

```bash
# Linux 平台构建到自定义目录
python -m mcp_framework.build --platform linux --server your_server.py --output-dir ./linux_build

# Windows 平台构建到自定义目录
python -m mcp_framework.build --platform windows --server your_server.py --output-dir ./windows_build

# 所有平台构建到不同目录
python -m mcp_framework.build --platform all --server your_server.py --output-dir ./all_platforms_build
```

### GitHub Actions 中的使用

在 GitHub Actions 工作流中，现在可以为每个服务器使用独立的输出目录：

```yaml
- name: Build Server with Custom Output
  run: |
    mkdir -p "dist/my-server-output"
    python -m mcp_framework.build \
      --platform ${{ matrix.platform }} \
      --server my_server.py \
      --output-dir "dist/my-server-output" \
      --no-test
```

## 目录结构示例

使用 `--output-dir` 参数后的目录结构：

```
project/
├── your_server.py
├── custom_output/          # 自定义输出目录
│   ├── your-server         # 可执行文件
│   ├── your-server-macos-arm64-20250825_161353/  # 打包目录
│   └── your-server-macos-arm64-20250825_161353.tar.gz  # 压缩包
└── dist/                   # 默认目录（如果不使用 --output-dir）
    └── (空或其他构建产物)
```

## 优势

### 1. 避免文件覆盖

之前在 GitHub Actions 中构建多个服务器时，后续的构建会覆盖之前的产物：

```bash
# 问题：第二个构建会覆盖第一个
python -m mcp_framework.build --server server1.py  # 输出到 dist/
python -m mcp_framework.build --server server2.py  # 覆盖 dist/ 中的内容
```

现在可以使用独立目录：

```bash
# 解决方案：使用独立输出目录
python -m mcp_framework.build --server server1.py --output-dir dist/server1
python -m mcp_framework.build --server server2.py --output-dir dist/server2
```

### 2. 更好的组织结构

```bash
# 按服务器类型组织
python -m mcp_framework.build --server file_reader.py --output-dir builds/file-services
python -m mcp_framework.build --server terminal_manager.py --output-dir builds/terminal-services
python -m mcp_framework.build --server expert_stream.py --output-dir builds/ai-services
```

### 3. 版本管理

```bash
# 按版本组织构建产物
python -m mcp_framework.build --server my_server.py --output-dir releases/v1.0.0
python -m mcp_framework.build --server my_server.py --output-dir releases/v1.1.0
```

## 注意事项

1. **目录创建**: 如果指定的输出目录不存在，系统会自动创建
2. **权限要求**: 确保对指定的输出目录有写入权限
3. **路径解析**: 相对路径相对于当前工作目录解析
4. **Docker 构建**: 在 Docker 构建中，输出目录会被映射到容器内的 `/app/dist`

## 测试

项目包含了测试脚本来验证 `--output-dir` 功能：

```bash
# 运行测试
python test_output_dir.py
```

测试会验证：
- 自定义输出目录是否正确创建
- 构建产物是否输出到指定目录
- 默认 `dist` 目录是否保持独立

## 兼容性

- ✅ Python 3.8+
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu 20.04+)
- ✅ Docker 构建环境

---

这个功能特别适合在 CI/CD 环境中使用，可以有效避免构建产物被覆盖的问题，提高构建流程的可靠性。