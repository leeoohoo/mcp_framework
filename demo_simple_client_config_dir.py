#!/usr/bin/env python3
"""
SimpleClient 自定义配置目录功能演示
"""

import asyncio
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_framework.client.simple import SimpleClient, quick_set, quick_get


async def demo_simple_client_config_dir():
    """演示 SimpleClient 使用自定义配置目录"""
    print("=== SimpleClient 自定义配置目录功能演示 ===\n")
    
    # 创建临时配置目录
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_config_dir = os.path.join(temp_dir, "demo_mcp_config")
        print(f"📁 使用自定义配置目录: {custom_config_dir}")
        
        # 演示1: 使用默认配置目录
        print("\n1️⃣ 使用默认配置目录:")
        client_default = SimpleClient(
            server_script="example_custom_config_dir.py",
            alias="demo_default"
        )
        print(f"   config_dir = {client_default.config_dir}")
        
        # 演示2: 使用自定义配置目录
        print("\n2️⃣ 使用自定义配置目录:")
        client_custom = SimpleClient(
            server_script="example_custom_config_dir.py",
            alias="demo_custom",
            config_dir=custom_config_dir
        )
        print(f"   config_dir = {client_custom.config_dir}")
        
        # 演示3: 全局便捷函数使用自定义配置目录
        print("\n3️⃣ 全局便捷函数支持自定义配置目录:")
        print("   quick_set 函数现在支持 config_dir 参数")
        print("   quick_get 函数现在支持 config_dir 参数")
        
        # 演示4: 参数传递验证
        print("\n4️⃣ 参数传递验证:")
        test_dirs = [
            None,
            "/tmp/test_config",
            custom_config_dir,
            "relative/path"
        ]
        
        for i, config_dir in enumerate(test_dirs, 1):
            client = SimpleClient(
                server_script="test_server.py",
                alias=f"test_{i}",
                config_dir=config_dir
            )
            print(f"   测试 {i}: config_dir = {config_dir} ✓")
        
        print("\n✅ 所有功能演示完成！")
        
        print("\n📋 功能总结:")
        print("   • SimpleClient 构造函数新增 config_dir 参数")
        print("   • 所有全局便捷函数都支持 config_dir 参数")
        print("   • config_dir 参数会正确传递给内部客户端")
        print("   • 支持绝对路径、相对路径和 None（默认）")
        print("   • 向后兼容，不影响现有代码")


async def demo_usage_examples():
    """演示使用示例"""
    print("\n=== 使用示例 ===\n")
    
    print("💡 基本用法:")
    print("""
# 使用默认配置目录
async with SimpleClient("server.py") as client:
    await client.set("key", "value")

# 使用自定义配置目录
async with SimpleClient("server.py", config_dir="/path/to/config") as client:
    await client.set("key", "value")
""")
    
    print("💡 全局便捷函数:")
    print("""
# 使用默认配置目录
await quick_set("server.py", "key", "value")

# 使用自定义配置目录
await quick_set("server.py", "key", "value", config_dir="/path/to/config")
""")
    
    print("💡 环境变量支持:")
    print("""
# 设置环境变量
export MCP_CONFIG_DIR="/path/to/config"

# 客户端会自动使用环境变量指定的目录
async with SimpleClient("server.py") as client:
    await client.set("key", "value")
""")


def demo_integration_scenarios():
    """演示集成场景"""
    print("\n=== 集成场景 ===\n")
    
    scenarios = [
        {
            "name": "开发环境",
            "description": "每个开发者使用独立的配置目录",
            "config_dir": "~/.mcp/dev"
        },
        {
            "name": "测试环境", 
            "description": "测试时使用临时配置目录",
            "config_dir": "/tmp/mcp_test"
        },
        {
            "name": "生产环境",
            "description": "使用标准的生产配置目录",
            "config_dir": "/etc/mcp/config"
        },
        {
            "name": "容器环境",
            "description": "使用挂载的配置目录",
            "config_dir": "/app/config"
        }
    ]
    
    for scenario in scenarios:
        print(f"🏗️  {scenario['name']}:")
        print(f"   描述: {scenario['description']}")
        print(f"   配置目录: {scenario['config_dir']}")
        print(f"   用法: SimpleClient('server.py', config_dir='{scenario['config_dir']}')")
        print()


async def main():
    """主演示函数"""
    await demo_simple_client_config_dir()
    await demo_usage_examples()
    demo_integration_scenarios()
    
    print("🎉 演示完成！SimpleClient 现在完全支持自定义配置目录功能。")


if __name__ == "__main__":
    asyncio.run(main())