#!/bin/bash

# MCP Framework Windows 构建便捷脚本
# 使用 Docker 在 macOS/Linux 上构建 Windows 版本

set -e

echo "🚀 Starting MCP Framework Windows build..."

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is available"

# 创建 dist 目录
mkdir -p dist

# 构建 Windows 版本
echo "🐳 Building Windows version using Docker..."
python build_cross_platform.py --platform windows --no-test

if [ $? -eq 0 ]; then
    echo "✅ Windows build completed successfully!"
    echo "📦 Check the dist/ directory for Windows packages"
    ls -la dist/ | grep -i windows || echo "No Windows packages found in dist/"
else
    echo "❌ Windows build failed"
    exit 1
fi