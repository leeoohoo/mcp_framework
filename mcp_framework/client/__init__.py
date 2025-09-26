"""
MCP 框架客户端 SDK
提供便捷的 stdio 客户端接口用于与 MCP 服务器通信
"""

from .base import MCPStdioClient
from .config import ConfigClient
from .tools import ToolsClient
from .simple import (
    SimpleClient,
    quick_call, quick_get, quick_set, quick_tools,
    sync_call, sync_get, sync_set, sync_tools
)

__all__ = [
    # 原始客户端类
    'MCPStdioClient',
    'ConfigClient', 
    'ToolsClient',
    
    # 简化客户端
    'SimpleClient',
    
    # 异步便捷函数
    'quick_call',
    'quick_get', 
    'quick_set',
    'quick_tools',
    
    # 同步便捷函数
    'sync_call',
    'sync_get',
    'sync_set', 
    'sync_tools'
]