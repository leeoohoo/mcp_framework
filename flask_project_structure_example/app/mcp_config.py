#!/usr/bin/env python3
"""
MCP服务器配置和初始化
这个文件负责创建和配置MCP服务器实例
"""

from mcp_framework import EnhancedMCPServer

# 创建全局MCP服务器实例
mcp_server = EnhancedMCPServer(
    name="flask-integrated-mcp-server",
    version="1.0.0",
    description="集成到Flask项目中的MCP服务器"
)

mcp_server1 = EnhancedMCPServer(
    name="flask-integrated-mcp-server",
    version="1.0.0",
    description="集成到Flask项目中的MCP服务器"
)

# 可以在这里添加全局配置
mcp_server.config = {
    "max_concurrent_requests": 10,
    "timeout": 30,
    "enable_cors": True
}

# 导出服务器实例供其他模块使用
__all__ = ['mcp_server']