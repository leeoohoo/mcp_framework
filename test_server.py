#!/usr/bin/env python3
"""
测试服务器 - 用于验证配置文件优先级修复
"""

import asyncio
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required
from typing import Annotated


class TestMCPServer(EnhancedMCPServer):
    """测试 MCP 服务器"""
    
    def __init__(self):
        super().__init__(
            name="TestMCPServer",
            version="1.0.0",
            description="测试配置文件优先级的服务器"
        )
        self._setup_tools()
    
    async def initialize(self):
        """初始化服务器"""
        self.logger.info("TestMCPServer 初始化完成")
        self.logger.info(f"当前配置: {self.config}")
    
    def _setup_tools(self):
        """设置工具"""
        
        @self.tool("获取服务器配置信息")
        async def get_server_config() -> dict:
            """获取当前服务器配置信息"""
            return {
                "host": self.config.host,
                "port": self.config.port,
                "log_level": self.config.log_level,
                "config_file": str(getattr(self.config, 'config_file', 'Unknown'))
            }
        
        @self.tool("简单的加法计算")
        async def add_numbers(
            a: Annotated[int, Required("第一个数字")],
            b: Annotated[int, Required("第二个数字")]
        ) -> int:
            """计算两个数字的和"""
            return a + b


if __name__ == "__main__":
    server = TestMCPServer()
    run_server_main(
        server_instance=server,
        server_name="TestMCPServer",
        default_port=8080
    )