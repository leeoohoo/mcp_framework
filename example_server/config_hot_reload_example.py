#!/usr/bin/env python3
"""
配置热更新示例 - 解决 terminal_manager_server 的配置更新问题

这个示例展示了如何使用 MCP 框架的配置热更新功能来解决
terminal_manager_server 中 default_dir 配置更新后不生效的问题。
"""

from mcp_framework import BaseMCPServer, Required, Optional
from typing import Dict, Any, List
import logging
import os


class TerminalService:
    """模拟 TerminalService 类"""
    
    def __init__(self, default_dir: str = None):
        self.default_dir = default_dir or os.getcwd()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"TerminalService initialized with default_dir: {self.default_dir}")
    
    def update_default_dir(self, new_default_dir: str):
        """更新默认工作目录"""
        old_dir = self.default_dir
        self.default_dir = new_default_dir
        self.logger.info(f"Default directory updated from '{old_dir}' to '{new_default_dir}'")
    
    def validate_directory(self, directory: str) -> bool:
        """验证目录是否在允许的默认目录下"""
        if not self.default_dir:
            return True
        
        abs_dir = os.path.abspath(directory)
        abs_default = os.path.abspath(self.default_dir)
        
        is_valid = abs_dir.startswith(abs_default)
        self.logger.info(f"Directory validation: '{directory}' -> {is_valid} (default: {self.default_dir})")
        return is_valid


class TerminalMCPServer(BaseMCPServer):
    """支持配置热更新的终端管理服务器示例"""
    
    def __init__(self):
        super().__init__("terminal-manager", "1.0.0", "Terminal Manager with Hot Config Reload")
        
        # 初始化 TerminalService
        self.terminal_service = None
        
        # 注册配置更新回调
        self.register_config_update_callback(self._on_config_updated)
        
        # 设置装饰器
        decorators = self.decorators
        
        @decorators.server_param(
            name="default_dir",
            display_name="默认工作目录",
            description="终端的默认工作目录路径",
            param_type="path",
            required=False,
            default_value=os.getcwd()
        )
        def setup_default_dir():
            pass
        
        @decorators.tool("创建终端")
        async def create_terminal(
            directory: Optional("工作目录", default="")
        ):
            """创建新的终端实例"""
            if not directory:
                directory = self.terminal_service.default_dir
            
            # 验证目录
            if not self.terminal_service.validate_directory(directory):
                return f"错误：目录 '{directory}' 不在允许的默认目录 '{self.terminal_service.default_dir}' 下"
            
            return f"成功创建终端，工作目录: {directory}"
        
        @decorators.tool("获取当前配置")
        async def get_current_config():
            """获取当前的配置信息"""
            return {
                "default_dir": self.terminal_service.default_dir if self.terminal_service else "未初始化",
                "server_config": self.server_config
            }
    
    def _on_config_updated(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """配置更新回调函数"""
        self.logger.info(f"配置更新回调触发: {old_config} -> {new_config}")
        
        # 检查 default_dir 是否发生变化
        old_default_dir = old_config.get('default_dir')
        new_default_dir = new_config.get('default_dir')
        
        if old_default_dir != new_default_dir and self.terminal_service:
            self.logger.info(f"检测到 default_dir 变化: '{old_default_dir}' -> '{new_default_dir}'")
            self.terminal_service.update_default_dir(new_default_dir)
    
    async def initialize(self) -> None:
        """初始化服务器"""
        # 获取配置中的 default_dir
        default_dir = self.get_config_value('default_dir', os.getcwd())
        
        # 初始化 TerminalService
        self.terminal_service = TerminalService(default_dir)
        
        self.logger.info(f"Terminal MCP Server initialized with default_dir: {default_dir}")
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """处理工具调用"""
        # 这里会被 EnhancedMCPServer 的装饰器系统自动处理
        pass
    
    def get_server_parameters(self) -> List:
        """获取服务器参数"""
        # 这里会被 EnhancedMCPServer 的装饰器系统自动处理
        return []


if __name__ == "__main__":
    import asyncio
    from mcp_framework import run_server
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行服务器
    server = TerminalMCPServer()
    
    print("\n=== 配置热更新示例 ===")
    print("1. 启动服务器后，访问 http://localhost:8080/setup 进行配置")
    print("2. 修改 'default_dir' 配置项")
    print("3. 观察日志输出，可以看到 TerminalService 的 default_dir 会实时更新")
    print("4. 使用 'create_terminal' 工具测试新的目录验证逻辑")
    print("5. 使用 'get_current_config' 工具查看当前配置状态")
    print("\n服务器启动中...\n")
    
    run_server(server)