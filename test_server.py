#!/usr/bin/env python3
"""
测试服务器 - 用于验证配置文件优先级修复
"""

import asyncio
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required, ServerParam
from typing import Annotated
import os


class TestMCPServer(EnhancedMCPServer):
    """测试 MCP 服务器"""
    
    def __init__(self):
        super().__init__(
            name="TestMCPServer",
            version="1.0.0",
            description="测试配置文件优先级的服务器"
        )
    
    async def initialize(self):
        """初始化服务器"""
        # 获取配置的测试目录
        test_dir = self.get_config_value('test_directory', '/tmp/test_mcp')
        # 确保测试目录存在
        os.makedirs(test_dir, exist_ok=True)
        
        self.logger.info("TestMCPServer 初始化完成")
        self.logger.info(f"当前配置: {self.config}")
        self.logger.info(f"测试目录: {test_dir}")
    
    @property
    def setup_server_params(self):
        """设置服务器参数 - 通过属性方式触发装饰器注册"""
        # 使用装饰器方式定义服务器配置参数
        @self.decorators.server_param("test_directory")
        async def test_directory_param(
            param: Annotated[str, ServerParam(
                display_name="测试目录",
                description="用于测试的工作目录路径",
                param_type="path",
                default_value="/tmp/test_mcp",
                required=False,
                placeholder="/path/to/test/directory"
            )]
        ):
            """测试目录配置参数"""
            pass
        return True
    
    @property
    def setup_tools(self):
        """设置工具"""
        
        @self.tool("获取服务器配置信息")
        async def get_server_config() -> dict:
            """获取当前服务器配置信息"""
            return {
                "host": self.config.host,
                "port": self.config.port,
                "log_level": self.config.log_level,
                "test_directory": self.get_config_value('test_directory', '/tmp/test_mcp'),
                "config_file": str(getattr(self.config, 'config_file', 'Unknown'))
            }
        
        @self.tool("创建测试文件")
        async def create_test_file(
            filename: Annotated[str, Required("文件名")],
            content: Annotated[str, Required("文件内容")]
        ) -> str:
            """在测试目录中创建一个文件"""
            test_dir = self.get_config_value('test_directory', '/tmp/test_mcp')
            file_path = os.path.join(test_dir, filename)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"文件已创建: {file_path}"
            except Exception as e:
                return f"创建文件失败: {str(e)}"
        
        @self.tool("列出测试目录文件")
        async def list_test_files() -> list:
            """列出测试目录中的所有文件"""
            test_dir = self.get_config_value('test_directory', '/tmp/test_mcp')
            
            try:
                if os.path.exists(test_dir):
                    files = os.listdir(test_dir)
                    return [f for f in files if os.path.isfile(os.path.join(test_dir, f))]
                else:
                    return []
            except Exception as e:
                return [f"错误: {str(e)}"]
        
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