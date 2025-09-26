#!/usr/bin/env python3
"""
调试 config_dir 参数传递问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp_framework'))

from mcp_framework.core.utils import parse_command_line_args, get_config_dir
from mcp_framework.core.config import ServerConfigManager

def test_config_dir_parsing():
    """测试配置目录参数解析"""
    print("=== 测试配置目录参数解析 ===")
    
    # 模拟命令行参数
    original_argv = sys.argv.copy()
    
    try:
        # 测试1: 带有 --config-dir 参数
        sys.argv = ['test_script.py', '--config-dir', '/Users/lilei/project/learn/mcp_framework/config', '--port', '8080']
        print(f"模拟命令行: {' '.join(sys.argv)}")
        
        args = parse_command_line_args("expert-server-annotated")
        print(f"解析结果: {args}")
        print(f"config_dir: {args.get('config_dir')}")
        
        # 测试 get_config_dir 函数
        config_dir = get_config_dir(args.get('config_dir'))
        print(f"get_config_dir 结果: {config_dir}")
        
        # 测试 ServerConfigManager 创建
        manager = ServerConfigManager("expert-server-annotated", alias="test", custom_config_dir=args.get('config_dir'))
        print(f"ServerConfigManager 配置文件路径: {manager.config_file}")
        print(f"ServerConfigManager 配置目录: {manager.config_dir}")
        
    finally:
        sys.argv = original_argv

def test_direct_config_dir():
    """直接测试配置目录功能"""
    print("\n=== 直接测试配置目录功能 ===")
    
    custom_dir = "/Users/lilei/project/learn/mcp_framework/config"
    print(f"自定义配置目录: {custom_dir}")
    
    # 测试 get_config_dir
    config_dir = get_config_dir(custom_dir)
    print(f"get_config_dir 结果: {config_dir}")
    
    # 测试 ServerConfigManager
    manager = ServerConfigManager("expert-server-annotated", alias="test", custom_config_dir=custom_dir)
    print(f"ServerConfigManager 配置文件路径: {manager.config_file}")
    print(f"ServerConfigManager 配置目录: {manager.config_dir}")
    
    # 检查目录是否存在
    print(f"配置目录是否存在: {manager.config_dir.exists()}")
    print(f"配置文件是否存在: {manager.config_file.exists()}")

if __name__ == "__main__":
    test_config_dir_parsing()
    test_direct_config_dir()