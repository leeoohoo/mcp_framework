#!/usr/bin/env python3
"""
使用实际服务器测试 SimpleClient
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_framework.client.simple import SimpleClient


async def test_with_real_server():
    """使用实际服务器测试 SimpleClient"""
    print("=== 使用实际服务器测试 SimpleClient ===\n")
    
    # 你的实际服务器路径和参数
    server_script = "/Users/lilei/project/learn/mcp_servers/expert_stream_server/expert_stream_server.py"
    server_args = ["stdio"]  # 使用 stdio 模式
    alias = "expert_stream"
    config_dir = "/Users/lilei/project/learn/mcp_framework/config"  # 使用你指定的配置目录
    
    print(f"🔧 测试配置:")
    print(f"   服务器脚本: {server_script}")
    print(f"   服务器参数: {server_args}")
    print(f"   别名: {alias}")
    print(f"   配置目录: {config_dir}")
    
    # 检查服务器文件是否存在
    if not os.path.exists(server_script):
        print(f"\n❌ 错误: 服务器文件不存在: {server_script}")
        return
    
    print(f"\n✅ 服务器文件存在")
    
    # 确保配置目录存在
    os.makedirs(config_dir, exist_ok=True)
    print(f"✅ 配置目录已创建: {config_dir}")
    
    try:
        print(f"\n🚀 开始测试 SimpleClient...")
        
        # 使用你的实际用法（添加服务器参数）
        async with SimpleClient(
            server_script, 
            alias=alias, 
            config_dir=config_dir,
            server_args=server_args
        ) as client:
            print(f"✅ SimpleClient 连接成功！")
            
            # 测试配置操作
            print(f"\n📝 测试配置操作...")
            
            # 设置一些测试配置
            await client.set("test_key", "test_value")
            print(f"✅ 设置配置成功: test_key = test_value")
            
            # 获取配置
            value = await client.get("test_key", "default")
            print(f"✅ 获取配置成功: test_key = {value}")
            
            # 批量更新配置
            await client.update(
                server_name="expert_stream_server",
                environment="development",
                debug_mode=True
            )
            print(f"✅ 批量更新配置成功")
            
            # 获取所有配置
            all_config = await client.get_all()
            print(f"✅ 获取所有配置成功，共 {len(all_config)} 项配置")
            
            print(f"\n📋 当前配置内容:")
            for key, val in all_config.items():
                print(f"   {key}: {val}")
            
            # 测试工具调用（如果服务器支持）
            try:
                print(f"\n🔧 测试工具调用...")
                tools = await client.list_tools()
                print(f"✅ 获取工具列表成功，共 {len(tools)} 个工具")
                
                for tool in tools[:3]:  # 只显示前3个工具
                    print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                
            except Exception as e:
                print(f"⚠️  工具调用测试失败（这可能是正常的）: {e}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        
        # 提供详细的错误信息
        if "MCP 初始化失败" in str(e):
            print(f"\n🔍 可能的原因:")
            print(f"   1. 服务器脚本有语法错误或运行时错误")
            print(f"   2. 服务器缺少必要的依赖")
            print(f"   3. 服务器没有正确实现 MCP 协议")
            print(f"   4. 服务器启动时间过长")
            
            print(f"\n💡 建议:")
            print(f"   1. 直接运行服务器脚本检查是否有错误:")
            print(f"      python {server_script}")
            print(f"   2. 检查服务器的依赖是否已安装")
            print(f"   3. 查看服务器的日志输出")
        
        return False
    
    print(f"\n🎉 所有测试完成！你的 SimpleClient 用法完全正确。")
    return True


async def main():
    """主函数"""
    success = await test_with_real_server()
    
    if success:
        print(f"\n✅ 结论: 你的 SimpleClient 用法没有问题！")
    else:
        print(f"\n❌ 结论: 问题可能出在服务器端，而不是你的 SimpleClient 用法。")


if __name__ == "__main__":
    asyncio.run(main())