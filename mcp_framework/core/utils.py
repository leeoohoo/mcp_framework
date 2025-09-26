#!/usr/bin/env python3
"""
MCP 框架工具函数
"""

import sys
import os
import argparse
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List


def is_frozen():
    """检测是否为 PyInstaller 打包的可执行文件"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_resource_path(relative_path):
    """获取资源文件路径，兼容打包环境"""
    if is_frozen():
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_data_dir():
    """获取数据目录"""
    if is_frozen():
        # 打包后使用可执行文件旁边的目录
        return Path(sys.executable).parent / "data"
    else:
        return Path.cwd() / "data"


def get_config_dir():
    """获取配置目录"""
    if is_frozen():
        # 打包后使用可执行文件旁边的目录
        return Path(sys.executable).parent / "config"
    else:
        return Path.cwd() / "config"


def parse_command_line_args(server_name: str = "MCP Server", 
                           default_port: int = 8080,
                           default_host: str = "localhost") -> Dict[str, Any]:
    """
    解析命令行参数
    
    Args:
        server_name: 服务器名称，用于帮助信息
        default_port: 默认端口号
        default_host: 默认主机
        
    Returns:
        解析后的参数字典
    """
    parser = argparse.ArgumentParser(
        description=f"{server_name} - MCP Framework based server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --port 8001                    # 使用端口 8001
  %(prog)s --host 0.0.0.0 --port 9000    # 绑定所有接口，端口 9000  
  %(prog)s --log-level DEBUG              # 启用调试日志
  %(prog)s --log-file server.log          # 保存日志到文件
        """
    )
    
    # 服务器配置参数
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=default_port,
        help=f'服务器端口号 (默认: {default_port})'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=default_host,
        help=f'服务器主机地址 (默认: {default_host})'
    )
    
    # 日志配置参数
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='日志文件路径 (可选，不指定则只输出到控制台)'
    )
    
    # 其他配置参数
    parser.add_argument(
        '--config-dir',
        type=str,
        help='配置文件目录 (可选)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str, 
        help='数据文件目录 (可选)'
    )
    
    parser.add_argument(
        '--max-connections',
        type=int,
        default=100,
        help='最大连接数 (默认: 100)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='请求超时时间(秒) (默认: 30)'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 转换为字典格式
    return {
        'host': args.host,
        'port': args.port,
        'log_level': args.log_level,
        'log_file': args.log_file,
        'config_dir': args.config_dir,
        'data_dir': args.data_dir,
        'max_connections': args.max_connections,
        'timeout': args.timeout
    }


def create_server_config_from_args(args: Dict[str, Any]):
    """
    从命令行参数创建服务器配置
    
    Args:
        args: parse_command_line_args 返回的参数字典
        
    Returns:
        ServerConfig 实例
    """
    # 延迟导入避免循环导入
    from .config import ServerConfig
    
    # 过滤掉 None 值
    config_data = {k: v for k, v in args.items() if v is not None}
    
    # 移除非 ServerConfig 字段
    server_config_fields = {
        'host', 'port', 'log_level', 'log_file', 'max_connections', 'timeout'
    }
    
    filtered_config = {k: v for k, v in config_data.items() if k in server_config_fields}
    
    return ServerConfig(**filtered_config)


def create_port_based_config_manager(server_name: str, port: int):
    """
    根据端口号创建配置管理器
    
    Args:
        server_name: 服务器名称
        port: 端口号
        
    Returns:
        ServerConfigManager 实例
    """
    # 延迟导入避免循环导入
    from .config import ServerConfigManager
    
    return ServerConfigManager.create_for_port(server_name, port)


def create_default_config_manager(server_name: str):
    """
    创建默认配置管理器
    
    Args:
        server_name: 服务器名称
        
    Returns:
        ServerConfigManager 实例
    """
    # 延迟导入避免循环导入
    from .config import ServerConfigManager
    
    return ServerConfigManager.create_default(server_name)


def list_all_port_configs(server_name: str) -> Dict[str, Any]:
    """
    列出所有端口相关的配置信息
    
    Args:
        server_name: 服务器名称
        
    Returns:
        包含端口配置信息的字典
    """
    # 延迟导入避免循环导入
    from .config import ServerConfigManager
    
    # 创建一个临时的配置管理器来访问方法
    temp_manager = ServerConfigManager.create_default(server_name)
    ports = temp_manager.list_port_configs()
    
    config_info = {
        'server_name': server_name,
        'total_configs': len(ports),
        'ports': ports,
        'configs': {}
    }
    
    # 加载每个端口的配置信息
    for port in ports:
        port_manager = ServerConfigManager.create_for_port(server_name, port)
        if port_manager.config_exists():
            try:
                config_data = port_manager.load_server_config()
                config_info['configs'][port] = config_data
            except Exception as e:
                config_info['configs'][port] = {'error': str(e)}
    
    return config_info


def setup_logging(log_level=logging.INFO, log_file=None):
    """设置日志配置"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = get_data_dir() / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def setup_logging_from_args(args: Dict[str, Any]) -> None:
    """
    从命令行参数设置日志
    
    Args:
        args: parse_command_line_args 返回的参数字典
    """
    log_level = getattr(logging, args.get('log_level', 'INFO').upper())
    log_file = args.get('log_file')
    setup_logging(log_level, log_file)


def check_dependencies():
    """检查依赖包"""
    try:
        import aiohttp
        return True
    except ImportError:
        print("❌ aiohttp is required. Please install it:")
        print("pip install aiohttp")
        return False


def parse_key_value_config(config_str: str, 
                          separator: str = ',',
                          key_value_separator: str = ':',
                          extra_fields: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    通用的键值对配置解析器
    
    Args:
        config_str: 配置字符串，格式如 "key1:value1,key2:value2"
        separator: 条目分隔符，默认为逗号
        key_value_separator: 键值分隔符，默认为冒号
        extra_fields: 为每个解析出的条目添加的额外字段
        
    Returns:
        解析后的配置列表，每个元素是包含键值对的字典
        
    Examples:
        >>> parse_key_value_config("server1:http://localhost:8001,server2:http://localhost:8002")
        [{'key': 'server1', 'value': 'http://localhost:8001'}, 
         {'key': 'server2', 'value': 'http://localhost:8002'}]
         
        >>> parse_key_value_config("name1:url1,name2:url2", extra_fields={'description': 'MCP服务器'})
        [{'key': 'name1', 'value': 'url1', 'description': 'MCP服务器'}, 
         {'key': 'name2', 'value': 'url2', 'description': 'MCP服务器'}]
    """
    if not config_str or not config_str.strip():
        return []
    
    result = []
    extra_fields = extra_fields or {}
    
    for entry in config_str.split(separator):
        entry = entry.strip()
        if key_value_separator in entry:
            key, value = entry.split(key_value_separator, 1)
            item = {
                'key': key.strip(),
                'value': value.strip()
            }
            # 添加额外字段
            item.update(extra_fields)
            result.append(item)
    
    return result


def parse_mcp_servers_config(config_str: str) -> List[Dict[str, str]]:
    """
    解析MCP服务器配置字符串
    
    这是 parse_key_value_config 的特化版本，专门用于解析MCP服务器配置
    
    Args:
        config_str: MCP服务器配置字符串，格式如 "server1:url1,server2:url2"
        
    Returns:
        MCP服务器配置列表，每个元素包含 name, url, description 字段
        
    Examples:
        >>> parse_mcp_servers_config("expert:http://localhost:8001,search:http://localhost:8002")
        [{'name': 'expert', 'url': 'http://localhost:8001', 'description': 'expert MCP服务器'}, 
         {'name': 'search', 'url': 'http://localhost:8002', 'description': 'search MCP服务器'}]
    """
    parsed = parse_key_value_config(config_str)
    
    # 转换为MCP服务器格式
    servers = []
    for item in parsed:
        servers.append({
            'name': item['key'],
            'url': item['value'],
            'description': f"{item['key']} MCP服务器"
        })
    
    return servers
