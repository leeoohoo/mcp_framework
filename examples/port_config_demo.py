#!/usr/bin/env python3
"""
端口配置演示脚本
演示如何根据不同端口创建不同的配置文件
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import (
    create_port_based_config_manager,
    list_all_port_configs,
    parse_command_line_args
)
from core.config import ServerConfig
from core.base import BaseMCPServer
from core.launcher import run_server


class DemoServer(BaseMCPServer):
    """演示服务器"""
    
    def __init__(self):
        super().__init__(
            name="PortConfigDemo",
            version="1.0.0",
            description="演示端口配置功能的服务器"
        )
    
    async def startup(self):
        """服务器启动初始化"""
        print("🎯 演示服务器启动完成")


def demo_port_configs():
    """演示端口配置功能"""
    server_name = "PortConfigDemo"
    
    print("=" * 60)
    print("🚀 MCP 框架端口配置演示")
    print("=" * 60)
    
    # 创建不同端口的配置
    ports = [8080, 8081, 8082]
    
    for port in ports:
        print(f"\n📝 为端口 {port} 创建配置...")
        
        # 创建配置管理器
        config_manager = create_port_based_config_manager(server_name, port)
        
        # 创建配置
        config = ServerConfig(
            host="localhost",
            port=port,
            log_level="INFO",
            max_connections=100 + port,  # 不同端口使用不同的连接数
            timeout=30 + (port - 8080) * 5  # 不同端口使用不同的超时时间
        )
        
        # 保存配置
        if config_manager.save_server_config(config.to_dict()):
            print(f"✅ 端口 {port} 配置已保存: {config_manager.config_file.name}")
        else:
            print(f"❌ 端口 {port} 配置保存失败")
    
    # 列出所有配置
    print(f"\n📚 列出所有 {server_name} 的配置:")
    all_configs = list_all_port_configs(server_name)
    
    print(f"服务器名称: {all_configs['server_name']}")
    print(f"配置文件总数: {all_configs['total_configs']}")
    print(f"端口列表: {all_configs['ports']}")
    
    print("\n📋 详细配置信息:")
    for port, config_data in all_configs['configs'].items():
        if 'error' in config_data:
            print(f"  端口 {port}: 错误 - {config_data['error']}")
        else:
            print(f"  端口 {port}:")
            print(f"    主机: {config_data.get('host', 'N/A')}")
            print(f"    最大连接数: {config_data.get('max_connections', 'N/A')}")
            print(f"    超时时间: {config_data.get('timeout', 'N/A')}")
    
    # 演示删除配置
    print(f"\n🗑️  删除端口 8082 的配置...")
    config_manager_8082 = create_port_based_config_manager(server_name, 8082)
    if config_manager_8082.delete_port_config(8082):
        print("✅ 端口 8082 配置已删除")
    else:
        print("❌ 端口 8082 配置删除失败")
    
    # 再次列出配置
    print(f"\n📚 删除后的配置列表:")
    updated_configs = list_all_port_configs(server_name)
    print(f"剩余端口: {updated_configs['ports']}")
    
    print("\n" + "=" * 60)
    print("✨ 演示完成！")
    print("💡 提示: 现在可以使用不同端口启动服务器:")
    print("   python port_config_demo.py --port 8080")
    print("   python port_config_demo.py --port 8081")
    print("=" * 60)


async def main():
    """主函数"""
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 启动服务器模式
        server = DemoServer()
        await run_server(
            server_instance=server,
            server_name="PortConfigDemo",
            default_port=8080,
            default_host="localhost"
        )
    else:
        # 演示模式
        demo_port_configs()


if __name__ == "__main__":
    asyncio.run(main())