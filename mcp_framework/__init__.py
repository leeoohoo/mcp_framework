"""
MCP 框架 - 用于快速构建 MCP 服务器的 Python 框架
"""

from .core.base import (
    BaseMCPServer,
    MCPTool,
    MCPResource
)

from .core.decorators import (
    ParamSpec,
    ServerParamSpec,
    AnnotatedDecorators,
    Required,
    Optional,
    Enum,
    IntRange
)

from .core.config import (
    ServerConfig,
    ServerParameter,
    ConfigManager,
    ServerConfigManager
)

from .core.launcher import (
    run_server,
    run_server_main
)

from .core.utils import (
    setup_logging,
    check_dependencies
)

from .server.http_server import MCPHTTPServer

__version__ = "0.1.0"

__all__ = [
    # 核心类
    'BaseMCPServer',
    'MCPTool',
    'MCPResource',
    
    # 装饰器和参数规范
    'ParamSpec',
    'ServerParamSpec',
    'AnnotatedDecorators',
    'Required',
    'Optional',
    'Enum',
    'IntRange',
    
    # 配置
    'ServerConfig',
    'ServerParameter',
    'ConfigManager',
    'ServerConfigManager',
    
    # 启动器
    'run_server',
    'run_server_main',
    'setup_logging',
    'check_dependencies',
    
    # HTTP 服务器
    'MCPHTTPServer'
]
