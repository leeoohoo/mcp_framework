"""
MCP 框架 - 用于快速构建 MCP 服务器的 Python 框架
"""

from .core.base import (
    BaseMCPServer,
    EnhancedMCPServer  # 添加这行
)

from .core.decorators import (
    ParamSpec,
    ServerParamSpec,
    AnnotatedDecorators,
    Required,
    Optional,
    Enum,
    IntRange,
    # 添加别名
    Required as R,
    Optional as O, 
    Enum as E,
    # 添加参数类型
    ServerParam,
    StringParam,
    SelectParam,
    BooleanParam,
    PathParam
)

from .core.config import (
    ServerConfig,
    ServerParameter,
    ConfigManager,
    ServerConfigManager,
    ServerConfigAdapter
)

from .core.launcher import (
    run_server,
    run_server_main
)

from .core.simple_launcher import (
    SimpleLauncher,
    simple_main,
    run_server as simple_run_server,
    start_server
)

from .core.utils import (
    setup_logging,
    check_dependencies
)

from .server.http_server import MCPHTTPServer

# 客户端 SDK
from .client import (
    MCPStdioClient,
    ConfigClient,
    ToolsClient
)

__version__ = "0.1.1"

__all__ = [
    # 核心类
    'BaseMCPServer',
    'EnhancedMCPServer',  # 添加这行
    
    # 装饰器和参数规范
    'ParamSpec',
    'ServerParamSpec',
    'AnnotatedDecorators',
    'Required',
    'Optional',
    'Enum',
    'IntRange',
    # 添加别名和参数类型
    'R',
    'O',
    'E',
    'ServerParam',
    'StringParam',
    'SelectParam',
    'BooleanParam',
    'PathParam',
    
    # 配置
    'ServerConfig',
    'ServerParameter',
    'ConfigManager',
    'ServerConfigManager',
    'ServerConfigAdapter',
    
    # 启动器
    'run_server',
    'run_server_main',
    'SimpleLauncher',
    'simple_main',
    'simple_run_server',
    'start_server',
    'setup_logging',
    'check_dependencies',
    
    # HTTP 服务器
    'MCPHTTPServer',
    
    # 客户端 SDK
    'MCPStdioClient',
    'ConfigClient',
    'ToolsClient'
]
