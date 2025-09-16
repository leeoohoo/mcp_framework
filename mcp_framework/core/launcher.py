#!/usr/bin/env python3
"""
MCP 框架服务器启动器
提供便利的服务器启动功能
"""

import asyncio
import logging
import sys
from typing import Optional, Dict, Any

from .utils import (
    parse_command_line_args,
    create_server_config_from_args,
    setup_logging_from_args,
    check_dependencies,
    create_port_based_config_manager,
    list_all_port_configs
)
from .base import BaseMCPServer
from ..server import MCPHTTPServer

logger = logging.getLogger(__name__)


async def run_server(
    server_instance: BaseMCPServer,
    server_name: str = "MCP Server",
    default_port: int = 8080,
    default_host: str = "localhost",
    required_dependencies: Optional[list] = None,
    custom_args: Optional[Dict[str, Any]] = None
) -> None:
    """
    便利的服务器启动函数
    
    Args:
        server_instance: MCP 服务器实例
        server_name: 服务器名称（用于命令行帮助）
        default_port: 默认端口号
        default_host: 默认主机
        required_dependencies: 必需的依赖包列表
        custom_args: 自定义参数字典，会覆盖命令行参数
    """
    try:
        # 检查依赖
        if required_dependencies:
            for dep in required_dependencies:
                try:
                    __import__(dep)
                except ImportError:
                    print(f"❌ 缺少依赖包: {dep}")
                    print(f"请运行: pip install {dep}")
                    sys.exit(1)
        
        # 通用依赖检查
        if not check_dependencies():
            sys.exit(1)

        # 解析命令行参数
        args = parse_command_line_args(
            server_name=server_name,
            default_port=default_port,
            default_host=default_host
        )
        
        # 应用自定义参数
        if custom_args:
            args.update(custom_args)

        # 设置日志
        setup_logging_from_args(args)

        # 创建服务器配置
        config = create_server_config_from_args(args)
        
        # 根据端口号创建专用的配置管理器
        port_config_manager = create_port_based_config_manager(server_name, config.port)
        
        # 为服务器实例设置正确的配置管理器
        server_instance.server_config_manager = port_config_manager
        
        # 检查是否存在该端口的配置文件，如果不存在则创建
        if not port_config_manager.config_exists():
            print(f"📝 为端口 {config.port} 创建新的配置文件...")
            # 创建完整的默认配置，包含所有ServerConfig字段
            default_config = config.to_dict()
            port_config_manager.save_server_config(default_config)
            print(f"✅ 配置文件已创建: {port_config_manager.config_file}")
        else:
            print(f"📂 使用现有配置文件: {port_config_manager.config_file}")
            # 加载现有配置并合并命令行参数
            existing_config = port_config_manager.load_server_config()
            
            # 先用ServerConfig默认值作为基础，确保所有必需字段都存在
            default_config = config.to_dict()
            # 然后用现有配置覆盖（保留用户自定义字段）
            merged_config = {**default_config, **existing_config}
            # 最后用命令行参数覆盖（命令行参数优先级最高）
            merged_config.update({k: v for k, v in config.to_dict().items() if v is not None})
            
            from .config import ServerConfig
            config = ServerConfig.from_dict(merged_config)
            
            # 保存合并后的完整配置，确保配置文件包含所有必需字段
            port_config_manager.save_server_config(merged_config)
            
            # 配置服务器实例，使用合并后的配置
            server_instance.configure_server(merged_config)

        # 初始化服务器
        print(f"🔧 初始化 {server_name}...")
        try:
            await server_instance.startup()
            print("✅ 服务器初始化成功")
        except Exception as e:
            print(f"⚠️  初始化警告: {e}")
            print("💡 某些功能可能需要通过配置页面设置后重启服务器")

        # 创建适配器，将ServerConfigManager包装为ConfigManager接口
        from .config import ServerConfigAdapter
        config_adapter = ServerConfigAdapter(port_config_manager)
        
        # 创建 HTTP 服务器，使用正确的配置管理器
        http_server = MCPHTTPServer(server_instance, config, config_adapter)
        
        # 将HTTP服务器实例关联到MCP服务器，以便test_page.py可以获取端口信息
        server_instance._http_server = http_server

        print(f"🚀 {server_name} 启动中...")
        print(f"📍 服务器地址: http://{config.host}:{config.port}")
        print(f"🛠️  设置页面: http://{config.host}:{config.port}/setup")
        print(f"🧪 测试页面: http://{config.host}:{config.port}/test")
        print(f"⚙️  配置页面: http://{config.host}:{config.port}/config")
        print(f"💚 健康检查: http://{config.host}:{config.port}/health")
        print(f"🌊 流式API: http://{config.host}:{config.port}/api/streaming/")
        print(f"🎯 服务器版本: {server_instance.name} v{server_instance.version}")
        print(f"🛠️  已注册工具: {len(server_instance.tools)} 个")
        print(f"📁 已注册资源: {len(server_instance.resources)} 个")
        print(f"📋 配置文件: {port_config_manager.config_file.name}")
        
        # 显示其他端口的配置信息
        all_configs = list_all_port_configs(server_name)
        if all_configs['total_configs'] > 1:
            other_ports = [p for p in all_configs['ports'] if p != config.port]
            if other_ports:
                print(f"📚 其他端口配置: {', '.join(map(str, other_ports))}")
        elif all_configs['total_configs'] == 0:
            print(f"📝 这是第一个为 {server_name} 创建的配置文件")
        
        if hasattr(server_instance, 'get_server_parameters'):
            params = server_instance.get_server_parameters()
            print(f"⚙️  服务器参数: {len(params)} 个")
        
        print("按 Ctrl+C 停止服务器")

        # 启动 HTTP 服务器
        runner = await http_server.start()

        # 保持服务器运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务器...")
            # 先关闭MCP服务器
            try:
                await server_instance.shutdown()
            except Exception as e:
                logger.warning(f"关闭MCP服务器时出现警告: {e}")
            # 再关闭HTTP服务器
            await http_server.stop(runner)
            print("✅ 服务器已安全关闭")

    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        print(f"❌ 服务器启动失败: {e}")
        # 确保在启动失败时也清理资源
        try:
            if 'server_instance' in locals():
                await server_instance.shutdown()
        except Exception as cleanup_error:
            logger.warning(f"清理资源时出现警告: {cleanup_error}")
        sys.exit(1)


def run_server_main(
    server_instance: BaseMCPServer,
    server_name: str = "MCP Server",
    default_port: int = 8080,
    default_host: str = "localhost",
    required_dependencies: Optional[list] = None,
    custom_args: Optional[Dict[str, Any]] = None
) -> None:
    """
    同步版本的服务器启动函数，处理事件循环和异常
    
    这是推荐的主函数入口点
    """
    try:
        asyncio.run(run_server(
            server_instance=server_instance,
            server_name=server_name,
            default_port=default_port,
            default_host=default_host,
            required_dependencies=required_dependencies,
            custom_args=custom_args
        ))
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        print(f"❌ 程序异常退出: {e}")
        sys.exit(1)