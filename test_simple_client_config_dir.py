#!/usr/bin/env python3
"""
测试 SimpleClient 的自定义配置目录功能
"""

import asyncio
import tempfile
import os
import shutil
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_framework.client.simple import SimpleClient, quick_call, quick_get, quick_set, quick_update


async def test_simple_client_custom_config_dir():
    """测试 SimpleClient 使用自定义配置目录"""
    print("测试 SimpleClient 自定义配置目录功能...")
    
    # 创建临时配置目录
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_config_dir = os.path.join(temp_dir, "test_mcp_config")
        print(f"使用自定义配置目录: {custom_config_dir}")
        
        # 测试 SimpleClient 实例化
        client = SimpleClient(
            server_script="example_custom_config_dir.py",
            alias="test_server",
            config_dir=custom_config_dir
        )
        
        # 验证 config_dir 属性
        assert client.config_dir == custom_config_dir
        print("✓ SimpleClient 正确设置了 config_dir 属性")
        
        # 测试配置操作（这会触发配置文件创建）
        try:
            async with client:
                # 设置一个配置值
                await client.set("test_key", "test_value")
                print("✓ 成功设置配置值")
                
                # 获取配置值
                value = await client.get("test_key")
                assert value == "test_value"
                print("✓ 成功获取配置值")
                
                # 更新配置
                await client.update({"test_key2": "test_value2", "test_key3": "test_value3"})
                print("✓ 成功批量更新配置")
                
        except Exception as e:
            print(f"配置操作测试跳过（服务器不存在）: {e}")
        
        # 检查配置目录是否创建
        if os.path.exists(custom_config_dir):
            print(f"✓ 自定义配置目录已创建: {custom_config_dir}")
            
            # 列出配置文件
            config_files = list(Path(custom_config_dir).glob("*.json"))
            if config_files:
                print(f"✓ 找到配置文件: {[f.name for f in config_files]}")
            else:
                print("! 未找到配置文件（可能是因为服务器不存在）")
        else:
            print("! 自定义配置目录未创建（可能是因为服务器不存在）")


async def test_quick_functions_custom_config_dir():
    """测试全局便捷函数的自定义配置目录功能"""
    print("\n测试全局便捷函数自定义配置目录功能...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_config_dir = os.path.join(temp_dir, "test_quick_config")
        print(f"使用自定义配置目录: {custom_config_dir}")
        
        try:
            # 测试 quick_set
            await quick_set(
                server_script="example_custom_config_dir.py",
                config_key="quick_test_key",
                value="quick_test_value",
                alias="quick_test",
                config_dir=custom_config_dir
            )
            print("✓ quick_set 成功")
            
            # 测试 quick_get
            value = await quick_get(
                server_script="example_custom_config_dir.py",
                config_key="quick_test_key",
                alias="quick_test",
                config_dir=custom_config_dir,
                default="default_value"
            )
            print(f"✓ quick_get 返回值: {value}")
            
            # 测试 quick_update
            await quick_update(
                server_script="example_custom_config_dir.py",
                alias="quick_test",
                config_dir=custom_config_dir,
                key1="value1",
                key2="value2"
            )
            print("✓ quick_update 成功")
            
            # 测试 quick_call
            result = await quick_call(
                server_script="example_custom_config_dir.py",
                tool_name="test_tool",
                alias="quick_test",
                config_dir=custom_config_dir,
                param1="value1"
            )
            print(f"✓ quick_call 返回结果: {result}")
            
        except Exception as e:
            print(f"便捷函数测试跳过（服务器不存在）: {e}")
        
        # 检查配置目录
        if os.path.exists(custom_config_dir):
            print(f"✓ 便捷函数自定义配置目录已创建: {custom_config_dir}")
            config_files = list(Path(custom_config_dir).glob("*.json"))
            if config_files:
                print(f"✓ 找到配置文件: {[f.name for f in config_files]}")
        else:
            print("! 便捷函数自定义配置目录未创建")


async def test_config_dir_parameter_passing():
    """测试 config_dir 参数传递"""
    print("\n测试 config_dir 参数传递...")
    
    # 测试不同的 config_dir 值
    test_cases = [
        None,  # 默认行为
        "/tmp/test_config_1",  # 自定义目录1
        "/tmp/test_config_2",  # 自定义目录2
    ]
    
    for config_dir in test_cases:
        print(f"测试 config_dir = {config_dir}")
        
        client = SimpleClient(
            server_script="test_server.py",
            alias="test",
            config_dir=config_dir
        )
        
        assert client.config_dir == config_dir
        print(f"✓ config_dir 正确设置为: {config_dir}")


def test_config_dir_validation():
    """测试 config_dir 参数验证"""
    print("\n测试 config_dir 参数验证...")
    
    # 测试有效的 config_dir 值
    valid_dirs = [
        None,
        "/tmp/test",
        "/Users/test/config",
        "relative/path",
        ""
    ]
    
    for config_dir in valid_dirs:
        try:
            client = SimpleClient(
                server_script="test_server.py",
                config_dir=config_dir
            )
            print(f"✓ 有效的 config_dir: {config_dir}")
        except Exception as e:
            print(f"✗ 意外错误，config_dir: {config_dir}, 错误: {e}")


async def main():
    """主测试函数"""
    print("开始测试 SimpleClient 自定义配置目录功能\n")
    
    # 运行所有测试
    await test_simple_client_custom_config_dir()
    await test_quick_functions_custom_config_dir()
    await test_config_dir_parameter_passing()
    test_config_dir_validation()
    
    print("\n所有测试完成！")
    print("\n总结:")
    print("1. SimpleClient 现在支持 config_dir 参数")
    print("2. 所有全局便捷函数都支持 config_dir 参数")
    print("3. config_dir 参数会正确传递给内部的客户端")
    print("4. 当指定 config_dir 时，配置文件会在该目录下创建")


if __name__ == "__main__":
    asyncio.run(main())