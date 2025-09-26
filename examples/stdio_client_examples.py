#!/usr/bin/env python3
"""
MCP Framework Stdio 客户端 SDK 使用示例
演示如何使用 SDK 与 MCP 服务器进行交互
"""

import asyncio
import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_framework import MCPStdioClient, ConfigClient, ToolsClient


async def basic_client_example():
    """基础客户端使用示例"""
    print("🔧 基础客户端使用示例")
    print("=" * 50)
    
    # 使用基础客户端
    async with MCPStdioClient(
        server_script="file_write_server.py",
        alias="test_no_config",
        startup_timeout=3.0
    ) as client:
        
        # 发送自定义请求
        response = await client.send_request("tools/list")
        print(f"工具列表响应: {response}")


async def config_client_example():
    """配置管理客户端示例"""
    print("\n🔧 配置管理客户端示例")
    print("=" * 50)
    
    async with ConfigClient(
        server_script="file_write_server.py",
        alias="test_no_config"
    ) as client:
        
        # 获取当前配置
        print("📋 获取当前配置...")
        config = await client.get_config()
        print(f"当前配置: {config}")
        
        # 获取特定配置项
        print("\\n🔍 获取特定配置项...")
        server_name = await client.get_config_value("server_name", "未知")
        print(f"服务器名称: {server_name}")
        
        max_file_size = await client.get_config_value("custom_params.max_file_size", 10)
        print(f"最大文件大小: {max_file_size}")
        
        # 更新配置
        print("\\n🔧 更新配置...")
        success = await client.update_config({
            "log_level": "INFO",
            "custom_params": {
                "test_setting": "SDK测试值",
                "max_file_size": 20
            }
        })
        print(f"配置更新{'成功' if success else '失败'}")
        
        # 验证更新后的配置
        print("\\n✅ 验证更新后的配置...")
        updated_config = await client.get_config()
        print(f"更新后配置: {updated_config}")


async def tools_client_example():
    """工具调用客户端示例"""
    print("\\n🔧 工具调用客户端示例")
    print("=" * 50)
    
    async with ToolsClient(
        server_script="file_write_server.py",
        alias="test_no_config"
    ) as client:
        
        # 获取工具列表
        print("📋 获取工具列表...")
        tools = await client.list_tools()
        print(f"可用工具数量: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # 检查特定工具是否存在
        print("\\n🔍 检查工具是否存在...")
        exists = await client.tool_exists("modify_file")
        print(f"modify_file 工具存在: {exists}")
        
        if exists:
            # 获取工具详细信息
            tool = await client.get_tool("modify_file")
            print(f"工具详情: {tool}")
            print(f"输入模式: {tool.input_schema}")
            
            # 验证工具参数
            print("\\n✅ 验证工具参数...")
            validation = await client.validate_tool_arguments("modify_file", {
                "file_path": "test.txt",
                "action": "create",
                "content": "测试内容"
            })
            print(f"参数验证结果: {validation}")
            
            # 调用工具（创建文件）
            print("\\n🛠️ 调用工具创建文件...")
            try:
                result = await client.call_tool("modify_file", {
                    "file_path": "sdk_test.txt",
                    "action": "create",
                    "content": "这是通过 SDK 创建的测试文件\\n包含多行内容"
                })
                print(f"工具调用结果: {result}")
                
                # 查看文件内容
                print("\\n📖 查看文件内容...")
                view_result = await client.call_tool("modify_file", {
                    "file_path": "sdk_test.txt",
                    "action": "view"
                })
                print(f"文件内容: {view_result}")
                
                # 清理测试文件
                print("\\n🗑️ 清理测试文件...")
                cleanup_result = await client.call_tool("modify_file", {
                    "file_path": "sdk_test.txt",
                    "action": "remove"
                })
                print(f"清理结果: {cleanup_result}")
                
            except Exception as e:
                print(f"工具调用失败: {e}")


async def convenience_functions_example():
    """便捷函数使用示例"""
    print("\\n🔧 便捷函数使用示例")
    print("=" * 50)
    
    # 使用便捷函数获取配置
    from mcp_framework.client.config import get_server_config, update_server_config
    from mcp_framework.client.tools import list_server_tools, call_server_tool
    
    try:
        # 获取服务器配置
        print("📋 使用便捷函数获取配置...")
        config = await get_server_config("file_write_server.py", "test_no_config")
        print(f"服务器配置: {config}")
        
        # 获取工具列表
        print("\\n📋 使用便捷函数获取工具列表...")
        tools = await list_server_tools("file_write_server.py", "test_no_config")
        print(f"工具列表: {[tool.name for tool in tools]}")
        
        # 调用工具
        print("\\n🛠️ 使用便捷函数调用工具...")
        result = await call_server_tool(
            "file_write_server.py",
            "modify_file",
            {
                "file_path": "convenience_test.txt",
                "action": "create",
                "content": "便捷函数测试文件"
            },
            alias="test_no_config"
        )
        print(f"工具调用结果: {result}")
        
        # 清理
        await call_server_tool(
            "file_write_server.py",
            "modify_file",
            {
                "file_path": "convenience_test.txt",
                "action": "remove"
            },
            alias="test_no_config"
        )
        print("✅ 测试文件已清理")
        
    except Exception as e:
        print(f"便捷函数调用失败: {e}")


async def error_handling_example():
    """错误处理示例"""
    print("\\n🔧 错误处理示例")
    print("=" * 50)
    
    try:
        async with ToolsClient(
            server_script="file_write_server.py",
            alias="test_no_config"
        ) as client:
            
            # 尝试调用不存在的工具
            print("❌ 尝试调用不存在的工具...")
            try:
                await client.call_tool("nonexistent_tool", {})
            except Exception as e:
                print(f"预期的错误: {e}")
            
            # 尝试使用错误的参数调用工具
            print("\\n❌ 尝试使用错误参数调用工具...")
            try:
                await client.call_tool("modify_file", {
                    "invalid_param": "value"
                })
            except Exception as e:
                print(f"预期的错误: {e}")
                
    except Exception as e:
        print(f"连接错误: {e}")


async def main():
    """主函数"""
    print("🚀 MCP Framework Stdio 客户端 SDK 示例")
    print("=" * 60)
    
    try:
        # 运行各种示例
        await basic_client_example()
        await config_client_example()
        await tools_client_example()
        await convenience_functions_example()
        await error_handling_example()
        
        print("\\n🎉 所有示例运行完成！")
        
    except Exception as e:
        print(f"\\n❌ 示例运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))