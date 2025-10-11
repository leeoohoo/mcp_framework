#!/usr/bin/env python3
"""
调试工具列表获取问题的测试脚本
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_framework.client.simple import SimpleClient
from mcp_framework.client.tools import ToolsClient
from mcp_framework.client.enhanced import EnhancedMCPStdioClient


async def test_simple_client():
    """测试 SimpleClient 获取工具列表"""
    print("🔧 测试 SimpleClient 获取工具列表")
    print("=" * 50)
    
    try:
        async with SimpleClient("simple_test_server.py") as client:
            print("✅ 客户端连接成功")
            
            # 获取工具列表
            tools = await client.tools()
            print(f"📋 获取到的工具列表: {tools}")
            print(f"📊 工具数量: {len(tools)}")
            
            # 测试单个工具信息
            if tools:
                tool_name = tools[0]
                tool_info = await client.tool_info(tool_name)
                print(f"🔍 工具 '{tool_name}' 信息: {tool_info}")
            
    except Exception as e:
        print(f"❌ SimpleClient 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_tools_client():
    """测试 ToolsClient 获取工具列表"""
    print("\n🔧 测试 ToolsClient 获取工具列表")
    print("=" * 50)
    
    try:
        async with ToolsClient("simple_test_server.py") as client:
            print("✅ 客户端连接成功")
            
            # 获取工具列表
            tools = await client.list_tools()
            print(f"📋 获取到的工具对象: {tools}")
            print(f"📊 工具数量: {len(tools)}")
            
            # 获取工具名称列表
            tool_names = await client.get_tool_names()
            print(f"📝 工具名称列表: {tool_names}")
            
    except Exception as e:
        print(f"❌ ToolsClient 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_enhanced_client():
    """测试 EnhancedMCPStdioClient 直接发送请求"""
    print("\n🔧 测试 EnhancedMCPStdioClient 直接发送请求")
    print("=" * 50)
    
    try:
        async with EnhancedMCPStdioClient(
            "simple_test_server.py",
            debug_mode=True  # 开启调试模式
        ) as client:
            print("✅ 客户端连接成功")
            
            # 直接发送 tools/list 请求
            response = await client.send_request("tools/list")
            print(f"📡 原始响应: {response}")
            
            # 检查响应格式
            if "result" in response:
                result = response["result"]
                print(f"📋 结果部分: {result}")
                
                if "tools" in result:
                    tools = result["tools"]
                    print(f"🔧 工具列表: {tools}")
                    print(f"📊 工具数量: {len(tools)}")
                else:
                    print("⚠️ 响应中没有 'tools' 字段")
            else:
                print("⚠️ 响应中没有 'result' 字段")
            
    except Exception as e:
        print(f"❌ EnhancedMCPStdioClient 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 开始调试工具列表获取问题")
    print("=" * 60)
    
    # 检查测试服务器是否存在
    server_script = "simple_test_server.py"
    if not os.path.exists(server_script):
        print(f"❌ 测试服务器脚本不存在: {server_script}")
        print("请确保 simple_test_server.py 存在于当前目录")
        return
    
    # 依次运行测试
    await test_enhanced_client()  # 先测试最底层的客户端
    await test_tools_client()     # 再测试工具客户端
    await test_simple_client()    # 最后测试简化客户端
    
    print("\n🏁 调试测试完成")


if __name__ == "__main__":
    asyncio.run(main())