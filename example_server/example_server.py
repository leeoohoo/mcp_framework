#!/usr/bin/env python3
"""
示例 MCP 服务器

这是一个简单的 MCP 服务器示例，用于测试自动发现和构建功能。
提供基本的文件操作工具。
"""

import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import os
from pathlib import Path

# 创建 FastMCP 应用
app = FastMCP("Example Server")

@app.tool()
def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 要读取的文件路径
    
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

@app.tool()
def list_directory(directory_path: str = ".") -> str:
    """
    列出目录内容
    
    Args:
        directory_path: 目录路径，默认为当前目录
    
    Returns:
        目录内容列表
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"目录不存在: {directory_path}"
        
        if not path.is_dir():
            return f"不是目录: {directory_path}"
        
        items = []
        for item in sorted(path.iterdir()):
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"📄 {item.name} ({size} bytes)")
        
        return "\n".join(items)
    except Exception as e:
        return f"列出目录失败: {e}"

@app.tool()
def get_file_info(file_path: str) -> str:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"文件不存在: {file_path}"
        
        stat = path.stat()
        info = [
            f"文件名: {path.name}",
            f"路径: {path.absolute()}",
            f"大小: {stat.st_size} bytes",
            f"类型: {'目录' if path.is_dir() else '文件'}",
            f"修改时间: {stat.st_mtime}"
        ]
        
        return "\n".join(info)
    except Exception as e:
        return f"获取文件信息失败: {e}"

@app.resource("file://")
def read_file_resource(uri: str) -> str:
    """
    通过 URI 读取文件资源
    
    Args:
        uri: 文件 URI (file://path/to/file)
    
    Returns:
        文件内容
    """
    try:
        # 移除 file:// 前缀
        file_path = uri.replace("file://", "")
        return read_file(file_path)
    except Exception as e:
        return f"读取资源失败: {e}"

if __name__ == "__main__":
    import mcp.server.stdio
    
    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(main())