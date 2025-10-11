#!/usr/bin/env python3
"""
自定义配置目录使用示例

这个示例展示了如何在 MCP Framework 中指定自定义的配置目录。
"""

import os
import sys
from pathlib import Path

# 添加项目路径到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_framework.core.base import BaseMCPServer
from mcp_framework.core.launcher import run_server_main

class ExampleServer(BaseMCPServer):
    """示例服务器"""
    
    def __init__(self):
        super().__init__()
        
    async def initialize(self):
        """初始化服务器"""
        pass
        
    async def handle_list_tools(self):
        """列出可用工具"""
        return {
            "tools": [
                {
                    "name": "hello",
                    "description": "Say hello",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name to greet"
                            }
                        }
                    }
                }
            ]
        }
    
    async def handle_tool_call(self, name: str, arguments: dict):
        """处理工具调用"""
        if name == "hello":
            name_arg = arguments.get("name", "World")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Hello, {name_arg}!"
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

def main():
    """主函数 - 演示不同的配置目录指定方式"""
    
    print("🚀 MCP Framework 自定义配置目录示例\n")
    
    print("📋 支持的配置目录指定方式:")
    print("1. 命令行参数: --config-dir /path/to/config")
    print("2. 环境变量: export MCP_CONFIG_DIR=/path/to/config")
    print("3. 默认行为: 使用当前目录下的 config 文件夹\n")
    
    print("💡 使用示例:")
    print("# 方式1: 使用命令行参数")
    print("python example_custom_config_dir.py --config-dir /tmp/my_mcp_config --port 8080")
    print()
    print("# 方式2: 使用环境变量")
    print("export MCP_CONFIG_DIR=/home/user/.mcp_configs")
    print("python example_custom_config_dir.py --port 8080")
    print()
    print("# 方式3: 使用默认配置目录")
    print("python example_custom_config_dir.py --port 8080")
    print()
    
    # 检查是否设置了自定义配置目录
    config_dir_from_env = os.environ.get('MCP_CONFIG_DIR')
    config_dir_from_args = None
    
    # 简单解析命令行参数中的 --config-dir
    if '--config-dir' in sys.argv:
        try:
            idx = sys.argv.index('--config-dir')
            if idx + 1 < len(sys.argv):
                config_dir_from_args = sys.argv[idx + 1]
        except (ValueError, IndexError):
            pass
    
    print("🔍 当前配置:")
    if config_dir_from_args:
        print(f"   配置目录 (命令行): {config_dir_from_args}")
    elif config_dir_from_env:
        print(f"   配置目录 (环境变量): {config_dir_from_env}")
    else:
        print(f"   配置目录 (默认): {Path.cwd() / 'config'}")
    
    print("\n🎯 配置文件将保存在指定的配置目录中")
    print("   文件名格式: {server_name}_port_{port}_server_config.json")
    print()
    
    # 创建服务器实例
    server = ExampleServer()
    
    # 启动服务器 (配置目录会根据命令行参数或环境变量自动确定)
    print("🚀 启动服务器...")
    run_server_main(
        server_instance=server,
        server_name="ExampleServer",
        default_port=8080,
        default_host="localhost"
    )

if __name__ == "__main__":
    main()