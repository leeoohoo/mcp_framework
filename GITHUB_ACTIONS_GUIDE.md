# GitHub Actions 跨平台构建指南

本指南介绍如何使用 GitHub Actions 自动构建 MCP Framework 项目的跨平台可执行文件。

## 概述

更新后的 GitHub Actions 工作流支持以下平台的自动构建：
- **Linux x86_64** - 在 Ubuntu 最新版本上构建
- **Windows x86_64** - 在 Windows 最新版本上构建  
- **macOS Intel (x86_64)** - 在 macOS 13 上构建，适用于 Intel Mac
- **macOS Apple Silicon (ARM64)** - 在 macOS 最新版本上构建，适用于 M1/M2 Mac

## 工作流触发条件

工作流会在以下情况下自动触发：

1. **推送到主分支**：`main` 或 `develop` 分支
2. **创建标签**：以 `v` 开头的标签（如 `v1.0.0`）
3. **Pull Request**：针对 `main` 分支的 PR
4. **手动触发**：通过 GitHub 界面手动运行

## 手动触发构建

### 通过 GitHub 界面

1. 进入你的 GitHub 仓库
2. 点击 "Actions" 标签页
3. 选择 "MCP Framework Cross-Platform Build" 工作流
4. 点击 "Run workflow" 按钮
5. 选择构建平台：
   - `native`：仅构建当前运行器的原生平台
   - `linux`：仅构建 Linux 平台
   - `windows`：仅构建 Windows 平台
   - `all`：构建所有支持的平台

### 通过 GitHub CLI

```bash
# 构建所有平台
gh workflow run "MCP Framework Cross-Platform Build" --field build_platform=all

# 仅构建 Linux 平台
gh workflow run "MCP Framework Cross-Platform Build" --field build_platform=linux
```

## 构建产物

### Artifacts 下载

每次构建完成后，可以从 Actions 页面下载构建产物：

- `mcp-framework-linux-x86_64` - Linux 可执行文件
- `mcp-framework-windows-x86_64` - Windows 可执行文件
- `mcp-framework-macos-x86_64` - macOS Intel 可执行文件
- `mcp-framework-macos-arm64` - macOS Apple Silicon 可执行文件
- `mcp-framework-docker-cross-platform` - Docker 跨平台构建测试产物

### 自动发布

当推送以 `v` 开头的标签时，工作流会自动创建 GitHub Release，包含所有平台的构建产物。

## 工作流配置详解

### 构建矩阵

```yaml
strategy:
  matrix:
    include:
      # Linux x86_64
      - os: ubuntu-latest
        platform: linux
        arch: x86_64
        python-version: '3.11'
      # Windows x86_64
      - os: windows-latest
        platform: windows
        arch: x86_64
        python-version: '3.11'
      # macOS Intel x86_64
      - os: macos-13
        platform: macos
        arch: x86_64
        python-version: '3.11'
      # macOS Apple Silicon ARM64 (M1/M2)
      - os: macos-latest
        platform: macos
        arch: arm64
        python-version: '3.11'
```

### 关键步骤

1. **环境准备**：安装 Python 和依赖
2. **框架安装**：以开发模式安装 MCP Framework
3. **测试运行**：执行单元测试
4. **创建测试服务器**：动态生成测试用的 MCP 服务器
5. **构建可执行文件**：使用 `mcp-build` 命令构建
6. **上传产物**：将构建结果上传为 Artifacts

## Docker 跨平台构建

工作流还包含 Docker 跨平台构建测试，验证：
- Linux 平台的 Docker 构建
- Windows 平台的 Docker 构建

这确保了跨平台构建功能在 CI/CD 环境中的稳定性。

## 自定义工作流

### 为你的项目定制

如果你要为自己的 MCP 服务器项目使用此工作流，需要：

1. **复制工作流文件**到你的项目的 `.github/workflows/` 目录
2. **修改测试服务器创建步骤**，替换为你的实际服务器文件
3. **更新构建命令**：
   ```yaml
   - name: Build executables using mcp-build
     run: |
       mcp-build --platform native --server your_server.py --no-test
   ```

### 添加额外平台

如需支持其他架构，可以在矩阵中添加：

```yaml
# 添加 Linux ARM64 支持
- os: ubuntu-latest
  platform: linux
  arch: arm64
  python-version: '3.11'
```

## 故障排除

### 常见问题

1. **构建失败**：检查依赖是否正确安装
2. **Docker 构建失败**：确保 Docker 服务可用
3. **权限问题**：确保 `GITHUB_TOKEN` 有足够权限

### 调试技巧

1. **查看构建日志**：在 Actions 页面查看详细日志
2. **本地测试**：使用相同的命令在本地测试
3. **分步调试**：注释掉部分步骤，逐步排查问题

## 最佳实践

1. **定期更新**：保持 GitHub Actions 版本最新
2. **缓存依赖**：考虑添加依赖缓存以加速构建
3. **并行构建**：利用矩阵策略并行构建多个平台
4. **安全考虑**：不要在日志中暴露敏感信息

## 示例：完整的发布流程

1. **开发完成**：在本地完成开发和测试
2. **推送代码**：推送到 `develop` 分支触发测试构建
3. **创建 PR**：向 `main` 分支创建 Pull Request
4. **合并代码**：PR 合并后触发主分支构建
5. **创建标签**：创建版本标签（如 `v1.0.0`）
6. **自动发布**：GitHub Actions 自动创建 Release

通过这个完整的 CI/CD 流程，你可以确保每个版本都经过充分测试，并自动生成所有平台的可执行文件。