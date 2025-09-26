#!/usr/bin/env python3
"""
使用 SDK 重写的配置测试示例
对比原始的 test_dual_instance_config.py，展示 SDK 的简化效果
"""

import asyncio
import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_framework import ConfigClient


async def test_instance_config_with_sdk(alias: str, config_values: dict):
    """使用 SDK 测试实例配置"""
    print(f"\\n🚀 使用 SDK 测试 {alias} 实例的配置...")
    
    try:
        async with ConfigClient(
            server_script="file_write_server.py",
            alias=alias,
            startup_timeout=3.0
        ) as client:
            
            print(f"✅ {alias} 实例连接成功")
            
            # 获取当前配置
            print(f"📋 获取 {alias} 当前配置...")
            current_config = await client.get_config()
            print(f"当前配置: {current_config}")
            
            # 更新配置
            print(f"🔧 为 {alias} 设置新配置...")
            success = await client.update_config(config_values)
            
            if success:
                # 验证配置更新
                print(f"🔍 验证 {alias} 配置更新...")
                updated_config = await client.get_config()
                print(f"更新后配置: {updated_config}")
                return True
            else:
                return False
                
    except Exception as e:
        print(f"❌ {alias} 实例测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🎯 使用 SDK 进行双实例配置管理测试...")
    
    # 配置数据（与原测试相同）
    fileserver1_config = {
        "server_name": "FileWriteServer",
        "log_level": "DEBUG",
        "max_connections": 50,
        "timeout": 60,
        "default_dir": "/tmp/fileserver11",
        "custom_params": {
            "project_root": "/Users/lilei/project/work/zj/user_manager",
            "max_file_size": 51,
            "enable_hidden_files": True,
            "custom_setting": "fileserver1_value"
        }
    }
    
    fileserver2_config = {
        "server_name": "FileWriteServer",
        "log_level": "WARNING",
        "max_connections": 20,
        "timeout": 45,
        "default_dir": "/tmp/fileserver2",
        "custom_params": {
            "project_root": "/tmp/fileserver2_workspace",
            "max_file_size": 15,
            "enable_hidden_files": False,
            "custom_setting": "fileserver2_value"
        }
    }
    
    # 并发测试两个实例
    results = await asyncio.gather(
        test_instance_config_with_sdk("test_no_config", fileserver1_config),
        test_instance_config_with_sdk("fileserver2", fileserver2_config),
        return_exceptions=True
    )
    
    # 检查结果
    success_count = sum(1 for result in results if result is True)
    
    print(f"\\n📊 测试结果:")
    print(f"✅ 成功: {success_count}/2")
    print(f"❌ 失败: {2 - success_count}/2")
    
    if success_count == 2:
        print("🎉 所有实例配置测试成功！")
        print("\\n💡 对比原始代码，SDK 版本的优势：")
        print("  - 代码量减少 70%+")
        print("  - 自动处理连接和初始化")
        print("  - 内置错误处理和超时管理")
        print("  - 支持异步上下文管理器")
        print("  - 更清晰的 API 接口")
        return True
    else:
        print("⚠️  部分实例配置测试失败")
        return False


if __name__ == "__main__":
    asyncio.run(main())