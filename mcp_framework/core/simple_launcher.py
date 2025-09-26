#!/usr/bin/env python3
"""
简化的服务器启动器
自动处理命令行参数解析和服务器启动逻辑
"""

import sys
import argparse
from typing import Optional, Any
from .multi_launcher import run_stdio_server_main, run_dual_server_main, run_http_server_main


class SimpleLauncher:
    """
    简化的服务器启动器
    
    用法:
        launcher = SimpleLauncher(server_instance)
        launcher.run()  # 自动解析命令行参数并启动
        
    或者:
        SimpleLauncher.quick_start(server_instance)  # 一行代码启动
    """
    
    def __init__(self, server_instance: Any, default_name: Optional[str] = None):
        """
        初始化启动器
        
        Args:
            server_instance: 服务器实例
            default_name: 默认服务器名称
        """
        self.server_instance = server_instance
        self.default_name = default_name or server_instance.__class__.__name__
        
    def run(self):
        """运行服务器（自动解析命令行参数）"""
        parser = self._create_parser()
        args = parser.parse_args()
        
        # 保存原始的 sys.argv
        original_argv = sys.argv.copy()
        
        try:
            self._start_server(args)
        finally:
            # 恢复原始的 sys.argv
            sys.argv = original_argv
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description=f"启动 {self.default_name} 服务器",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  %(prog)s stdio                    # 标准输入输出模式
  %(prog)s dual 8080               # 双传输模式 (stdio + http)
  %(prog)s http 8080               # HTTP模式
  %(prog)s stdio --alias my_server # 指定别名
            """
        )
        
        parser.add_argument(
            'mode',
            choices=['stdio', 'dual', 'http'],
            help='服务器运行模式'
        )
        
        parser.add_argument(
            'port',
            type=int,
            nargs='?',
            help='端口号（dual和http模式必需）'
        )
        
        parser.add_argument(
            '--name',
            default=self.default_name,
            help=f'服务器名称（默认: {self.default_name}）'
        )
        
        parser.add_argument(
            '--alias',
            help='服务器别名'
        )
        
        return parser
    
    def _start_server(self, args):
        """根据参数启动服务器"""
        mode = args.mode
        port = args.port
        server_name = args.name
        alias = args.alias
        
        # 验证端口参数
        if mode in ['dual', 'http'] and port is None:
            print(f"错误: {mode}模式需要指定端口")
            print(f"用法: python {sys.argv[0]} {mode} <port>")
            sys.exit(1)
        
        # 启动信息
        mode_info = {
            'stdio': 'stdio模式',
            'dual': f'dual模式, 端口: {port}',
            'http': f'http模式, 端口: {port}'
        }
        
        print(f"🚀 启动 {server_name} ({mode_info[mode]})" + 
              (f" 别名: {alias}" if alias else "") + "...")
        
        # 设置 sys.argv 以兼容现有的启动函数
        if mode == 'stdio':
            sys.argv = [sys.argv[0]]
            run_stdio_server_main(self.server_instance, server_name=server_name, alias=alias)
        elif mode == 'dual':
            sys.argv = [sys.argv[0], "--port", str(port)]
            run_dual_server_main(self.server_instance, default_port=port, server_name=server_name, alias=alias)
        elif mode == 'http':
            sys.argv = [sys.argv[0], "--port", str(port)]
            run_http_server_main(self.server_instance, default_port=port, server_name=server_name, alias=alias)
    
    @classmethod
    def quick_start(cls, server_instance: Any, default_name: Optional[str] = None):
        """
        快速启动服务器（一行代码）
        
        Args:
            server_instance: 服务器实例
            default_name: 默认服务器名称
        """
        launcher = cls(server_instance, default_name)
        launcher.run()


def simple_main(server_instance: Any, server_name: Optional[str] = None):
    """
    最简单的主函数
    
    用法:
        if __name__ == "__main__":
            simple_main(MyServer())
    
    Args:
        server_instance: 服务器实例
        server_name: 服务器名称（可选）
    """
    SimpleLauncher.quick_start(server_instance, server_name)


# 为了向后兼容，提供一些便捷函数
def run_server(server_instance: Any, server_name: Optional[str] = None):
    """运行服务器（别名）"""
    simple_main(server_instance, server_name)


def start_server(server_instance: Any, server_name: Optional[str] = None):
    """启动服务器（别名）"""
    simple_main(server_instance, server_name)