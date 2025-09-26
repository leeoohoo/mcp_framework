#!/usr/bin/env python3
"""
简单的测试服务器，用于验证 config_dir 功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_framework import EnhancedMCPServer, simple_main
from mcp_framework.core.decorators import Required
from typing import Annotated

class TestServer(EnhancedMCPServer):
    """简单的测试服务器"""
    
    def __init__(self):
        super().__init__(
            name="test_server",
            version="1.0.0",
            description="简单的测试服务器"
        )
        
    @property
    def setup_tools(self):
        """设置工具"""
        
        @self.tool("测试工具")
        async def test_tool(
            message: Annotated[str, Required("消息内容")] = "Hello"
        ) -> str:
            """测试工具"""
            return f"Test response: {message}"

def main():
    """主函数"""
    server = TestServer()
    
    # 运行服务器
    simple_main(server, "test_server")

if __name__ == "__main__":
    main()