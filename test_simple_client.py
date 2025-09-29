#!/usr/bin/env python3
"""
测试 SimpleClient 功能
"""

import asyncio
from mcp_framework.client.simple import SimpleClient

async def test_simple_client():
    """测试 SimpleClient 的基本功能"""
    print("=== 测试 SimpleClient ===")
    
    # 使用 expert_stream_server 作为测试服务器
    server_script = "expert_stream_server/expert_stream_server.py"
    
    try:
        # 创建 SimpleClient 实例
        client = SimpleClient(server_script)
        
        print("1. 测试获取工具列表...")
        tools = await client.tools()
        print(f"   可用工具: {tools}")
        
        if tools:
            print("2. 测试工具信息...")
            tool_info = await client.tool_info(tools[0])
            print(f"   工具 '{tools[0]}' 信息: {tool_info}")
            
            print("3. 测试工具调用...")
            # 调用 query_expert_stream 工具
            if "query_expert_stream" in tools:
                result = await client.call("query_expert_stream", question="Hello, how are you?")
                print(f"   调用结果: {result}")
        
        print("4. 测试配置功能...")
        config = await client.config()
        print(f"   当前配置: {config}")
        
        print("5. 测试快速调用功能...")
        # 测试 quick_call 函数
        from mcp_framework.client.simple import quick_call
        quick_result = await quick_call(server_script, "query_expert_stream", question="Quick test")
        print(f"   快速调用结果: {quick_result}")
        
        print("\n✅ SimpleClient 测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_client())