#!/usr/bin/env python3
"""
MCP 框架统一传输层接口
支持HTTP和stdio等多种通信方式
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Union
from ..core.base import BaseMCPServer
from ..core.config import ServerConfig
from ..server.http_server import MCPHTTPServer
from ..server.stdio_server import MCPStdioServer

logger = logging.getLogger(__name__)


class TransportType(Enum):
    """传输类型枚举"""
    HTTP = "http"
    STDIO = "stdio"


class MCPTransport(ABC):
    """MCP传输层抽象基类"""
    
    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    async def start(self) -> Any:
        """启动传输层"""
        pass
        
    @abstractmethod
    async def stop(self, *args) -> None:
        """停止传输层"""
        pass
        
    @property
    @abstractmethod
    def transport_type(self) -> TransportType:
        """传输类型"""
        pass


class HTTPTransport(MCPTransport):
    """HTTP传输实现"""
    
    def __init__(self, mcp_server: BaseMCPServer, config: ServerConfig, config_manager=None):
        super().__init__(mcp_server)
        self.config = config
        self.config_manager = config_manager
        self.http_server = None
        
    @property
    def transport_type(self) -> TransportType:
        return TransportType.HTTP
        
    async def start(self) -> Any:
        """启动HTTP服务器"""
        if self.config_manager is None:
            raise ValueError("HTTP transport requires config_manager")
            
        self.http_server = MCPHTTPServer(self.mcp_server, self.config, self.config_manager)
        runner = await self.http_server.start()
        
        self.logger.info(f"HTTP服务器启动在 http://{self.config.host}:{self.config.port}")
        return runner
        
    async def stop(self, runner=None) -> None:
        """停止HTTP服务器"""
        if self.http_server and runner:
            await self.http_server.stop(runner)
            self.logger.info("HTTP服务器已停止")


class StdioTransport(MCPTransport):
    """stdio传输实现"""
    
    def __init__(self, mcp_server: BaseMCPServer, config_manager=None):
        super().__init__(mcp_server)
        self.config_manager = config_manager
        self.stdio_server = None
        
    @property
    def transport_type(self) -> TransportType:
        return TransportType.STDIO
        
    async def start(self) -> Any:
        """启动stdio服务器"""
        self.stdio_server = MCPStdioServer(self.mcp_server, self.config_manager)
        self.logger.info("stdio服务器启动")
        await self.stdio_server.start()
        return None
        
    async def stop(self, *args) -> None:
        """停止stdio服务器"""
        if self.stdio_server:
            await self.stdio_server.stop()
            self.logger.info("stdio服务器已停止")


class MCPTransportManager:
    """MCP传输管理器 - 统一管理多种传输方式"""
    
    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.transports: Dict[TransportType, MCPTransport] = {}
        self.active_transports: Dict[TransportType, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.MCPTransportManager")
        
    def add_http_transport(self, config: ServerConfig, config_manager=None) -> 'MCPTransportManager':
        """添加HTTP传输"""
        transport = HTTPTransport(self.mcp_server, config, config_manager)
        self.transports[TransportType.HTTP] = transport
        return self
        
    def add_stdio_transport(self, config_manager=None) -> 'MCPTransportManager':
        """添加stdio传输"""
        transport = StdioTransport(self.mcp_server, config_manager)
        self.transports[TransportType.STDIO] = transport
        return self
        
    async def start_transport(self, transport_type: TransportType) -> Any:
        """启动指定类型的传输"""
        if transport_type not in self.transports:
            raise ValueError(f"Transport type {transport_type} not configured")
            
        transport = self.transports[transport_type]
        result = await transport.start()
        self.active_transports[transport_type] = result
        
        self.logger.info(f"传输 {transport_type.value} 已启动")
        return result
        
    async def stop_transport(self, transport_type: TransportType) -> None:
        """停止指定类型的传输"""
        if transport_type not in self.transports:
            return
            
        transport = self.transports[transport_type]
        result = self.active_transports.get(transport_type)
        
        await transport.stop(result)
        
        if transport_type in self.active_transports:
            del self.active_transports[transport_type]
            
        self.logger.info(f"传输 {transport_type.value} 已停止")
        
    async def start_all(self) -> Dict[TransportType, Any]:
        """启动所有配置的传输"""
        results = {}
        for transport_type in self.transports:
            try:
                result = await self.start_transport(transport_type)
                results[transport_type] = result
            except Exception as e:
                self.logger.error(f"启动传输 {transport_type.value} 失败: {e}")
                raise
        return results
        
    async def stop_all(self) -> None:
        """停止所有活跃的传输"""
        for transport_type in list(self.active_transports.keys()):
            try:
                await self.stop_transport(transport_type)
            except Exception as e:
                self.logger.error(f"停止传输 {transport_type.value} 失败: {e}")
                
    def get_active_transports(self) -> Dict[TransportType, Any]:
        """获取活跃的传输列表"""
        return self.active_transports.copy()
        
    def is_transport_active(self, transport_type: TransportType) -> bool:
        """检查指定传输是否活跃"""
        return transport_type in self.active_transports


# 便利函数
def create_transport_manager(mcp_server: BaseMCPServer) -> MCPTransportManager:
    """创建传输管理器"""
    return MCPTransportManager(mcp_server)


def create_http_only_manager(mcp_server: BaseMCPServer, config: ServerConfig, config_manager=None) -> MCPTransportManager:
    """创建仅HTTP的传输管理器"""
    return (MCPTransportManager(mcp_server)
            .add_http_transport(config, config_manager))


def create_stdio_only_manager(mcp_server: BaseMCPServer, config_manager=None) -> MCPTransportManager:
    """创建仅stdio的传输管理器"""
    return (MCPTransportManager(mcp_server)
            .add_stdio_transport(config_manager))


def create_dual_manager(mcp_server: BaseMCPServer, config: ServerConfig, config_manager=None) -> MCPTransportManager:
    """创建HTTP+stdio双传输管理器"""
    return (MCPTransportManager(mcp_server)
            .add_http_transport(config, config_manager)
            .add_stdio_transport(config_manager))