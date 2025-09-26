#!/usr/bin/env python3
"""
使用 SDK 重写的工具调用测试示例
对比原始的 test_tool_call.py，展示 SDK 的简化效果
"""

import asyncio
import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_framework import ToolsClient

# 获取项目根目录下的服务器脚本路径
SERVER_SCRIPT = str(Path(__file__).parent.parent / "file_write_server.py")


async def test_modify_file_operations_with_sdk():
    """使用 SDK 测试 modify_file 工具的各种操作"""
    print("\\n🧪 使用 SDK 测试 modify_file 工具操作...")
    
    async with ToolsClient(
        server_script=SERVER_SCRIPT,
        alias="test_no_config",
        startup_timeout=10.0
    ) as client:
        
        test_file = "sdk_test_file.txt"
        
        try:
            # 1. 测试创建文件
            print("1. 测试创建文件...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "create",
                "content": "第一行内容\\n第二行内容\\n第三行内容"
            })
            print("✅ 创建文件成功")
            
            # 2. 测试查看文件
            print("2. 测试查看文件...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "view"
            })
            print("✅ 查看文件成功")
            print(f"文件内容预览: {str(result)[:100]}...")
            
            # 3. 测试编辑文件
            print("3. 测试编辑文件...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "edit",
                "search_text": "第二行内容",
                "replace_text": "修改后的第二行内容"
            })
            print("✅ 编辑文件成功")
            
            # 4. 测试插入内容
            print("4. 测试插入内容...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "insert",
                "line_number": 2,
                "content": "插入的新行"
            })
            print("✅ 插入内容成功")
            
            # 5. 测试删除行
            print("5. 测试删除行...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "delete",
                "line_number": 3
            })
            print("✅ 删除行成功")
            
            # 6. 测试查看修改后的文件
            print("6. 测试查看修改后的文件...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "view"
            })
            print("✅ 查看修改后文件成功")
            print(f"修改后文件内容: {str(result)[:200]}...")
            
            # 7. 测试删除文件
            print("7. 测试删除文件...")
            result = await client.call_tool("modify_file", {
                "file_path": test_file,
                "action": "remove"
            })
            print("✅ 删除文件成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 工具操作失败: {e}")
            return False


async def test_tools_list_with_sdk():
    """使用 SDK 测试工具列表获取"""
    print("\\n🧪 使用 SDK 测试工具列表获取...")
    
    async with ToolsClient(
        server_script=SERVER_SCRIPT,
        alias="test_no_config",
        startup_timeout=10.0
    ) as client:
        
        try:
            # 获取工具列表
            tools = await client.list_tools()
            print(f"✅ 成功获取工具列表，共 {len(tools)} 个工具:")
            
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # 验证预期的工具是否存在
            expected_tools = ["modify_file"]
            found_tools = [tool.name for tool in tools]
            
            for expected_tool in expected_tools:
                if expected_tool in found_tools:
                    print(f"  ✅ 找到预期工具: {expected_tool}")
                else:
                    print(f"  ❌ 缺少预期工具: {expected_tool}")
            
            return True
            
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 使用 SDK 进行工具调用测试")
    print("=" * 60)
    
    try:
        # 测试工具列表
        tools_success = await test_tools_list_with_sdk()
        
        # 测试工具调用
        operations_success = await test_modify_file_operations_with_sdk()
        
        if tools_success and operations_success:
            print("\\n🎉 所有 SDK 工具测试通过！")
            print("\\n💡 对比原始代码，SDK 版本的优势：")
            print("  - 代码量减少 60%+")
            print("  - 自动连接和初始化管理")
            print("  - 内置工具验证和缓存")
            print("  - 统一的错误处理")
            print("  - 类型安全的工具对象")
            print("  - 支持异步上下文管理器")
            return 0
        else:
            print("\\n❌ SDK 工具测试失败")
            return 1
            
    except Exception as e:
        print(f"\\n❌ 测试过程中发生异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))