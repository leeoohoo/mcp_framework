#!/usr/bin/env python3
"""
MCP HTTP 服务器主类
"""

import logging
from datetime import datetime
from aiohttp import web

from ..core.base import BaseMCPServer
from ..core.config import ServerConfig, ConfigManager
from .middleware import cors_middleware, error_middleware, logging_middleware
from .handlers import MCPRequestHandler, APIHandler, ServerConfigHandler, OptionsHandler, SSEHandler
from ..web.setup_page import SetupPageHandler
from ..web.test_page import TestPageHandler
from ..web.config_page import ConfigPageHandler
from ..web.alias_page import AliasPageHandler

logger = logging.getLogger(__name__)


class MCPHTTPServer:
    """通用 MCP HTTP 服务器"""

    def __init__(self, mcp_server: BaseMCPServer, config: ServerConfig, config_manager = None):
        self.mcp_server = mcp_server
        self.config = config
        self.host = config.host
        self.port = config.port
        self.app = web.Application()
        self.logger = logging.getLogger(f"{__name__}.MCPHTTPServer")
        self.start_time = datetime.now()
        # 使用传入的配置管理器，必须提供有效的配置管理器
        if config_manager is None:
            raise ValueError("config_manager is required and cannot be None")
        self.config_manager = config_manager

        # 初始化处理器
        self.mcp_handler = MCPRequestHandler(mcp_server, self.config_manager)
        self.api_handler = APIHandler(mcp_server, self.config_manager)
        self.server_config_handler = ServerConfigHandler(mcp_server)
        self.sse_handler = SSEHandler(mcp_server)  # 新增：SSE 处理器
        self.setup_page_handler = SetupPageHandler(mcp_server)
        self.test_page_handler = TestPageHandler(mcp_server)
        self.config_page_handler = ConfigPageHandler(self.config_manager, mcp_server)
        self.alias_page_handler = AliasPageHandler(self.config_manager, mcp_server)

        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """设置中间件"""
        self.app.middlewares.append(cors_middleware)
        self.app.middlewares.append(error_middleware)
        self.app.middlewares.append(logging_middleware)

    def setup_routes(self):
        """设置路由"""
        # 核心 MCP 路由
        self.app.router.add_post('/mcp', self.mcp_handler.handle_mcp_request)

        # 管理和监控路由
        self.app.router.add_get('/health', self.api_handler.health_check)
        self.app.router.add_get('/info', self.api_handler.server_info)
        self.app.router.add_get('/metrics', self.api_handler.metrics)
        self.app.router.add_get('/version', self.api_handler.version_info)
        self.app.router.add_get('/tools/list', self.api_handler.tools_list)

        # 配置管理路由
        self.app.router.add_get('/config', self.config_page_handler.serve_config_page)
        self.app.router.add_get('/api/config', self.api_handler.get_config)
        self.app.router.add_post('/api/config', self.api_handler.update_config)
        self.app.router.add_post('/api/config/reset', self.api_handler.reset_config)
        self.app.router.add_post('/api/server/restart', self.api_handler.restart_server)

        # 别名管理路由
        self.app.router.add_get('/aliases', self.alias_page_handler.serve_alias_page)
        self.app.router.add_get('/api/aliases', self.alias_page_handler.get_aliases)
        self.app.router.add_post('/api/aliases', self.alias_page_handler.create_alias)
        self.app.router.add_delete('/api/aliases/{alias}', self.alias_page_handler.delete_alias)
        self.app.router.add_delete('/api/ports/{port}', self.alias_page_handler.delete_port_config)

        # 服务器配置和启动路由
        self.app.router.add_get('/setup', self.setup_page_handler.serve_setup_page)
        self.app.router.add_get('/api/server/parameters', self.server_config_handler.get_server_parameters)
        self.app.router.add_post('/api/server/configure', self.server_config_handler.configure_server)
        self.app.router.add_post('/api/server/start', self.server_config_handler.start_configured_server)
        self.app.router.add_get('/api/server/status', self.server_config_handler.get_server_status)

        # SSE 路由 - 新增
        self.app.router.add_get('/sse/tool/call', self.sse_handler.handle_sse_tool_call)
        self.app.router.add_post('/sse/tool/call', self.sse_handler.handle_sse_tool_call)
        self.app.router.add_get('/sse/info', self.sse_handler.handle_sse_info)
        
        # OpenAI 格式的 SSE 路由 - 新增
        self.app.router.add_get('/sse/openai/tool/call', self.sse_handler.handle_sse_tool_call_openai)
        self.app.router.add_post('/sse/openai/tool/call', self.sse_handler.handle_sse_tool_call_openai)
        
        # SSE 路由 - 兼容 /mcp 前缀
        self.app.router.add_get('/mcp/sse/tool/call', self.sse_handler.handle_sse_tool_call)
        self.app.router.add_post('/mcp/sse/tool/call', self.sse_handler.handle_sse_tool_call)
        self.app.router.add_get('/mcp/sse/info', self.sse_handler.handle_sse_info)
        
        # OpenAI 格式的 SSE 路由 - 兼容 /mcp 前缀
        self.app.router.add_get('/mcp/sse/openai/tool/call', self.sse_handler.handle_sse_tool_call_openai)
        self.app.router.add_post('/mcp/sse/openai/tool/call', self.sse_handler.handle_sse_tool_call_openai)

        # 流式控制路由 - 新增
        self.app.router.add_post('/api/streaming/stop', self.api_handler.stop_streaming_session)
        self.app.router.add_post('/api/streaming/stop-all', self.api_handler.stop_all_streaming)
        self.app.router.add_post('/api/streaming/resume', self.api_handler.resume_streaming)
        self.app.router.add_get('/api/streaming/status', self.api_handler.get_streaming_status)

        # 静态文件服务（用于测试页面）
        self.app.router.add_get('/', self.serve_home_page)
        self.app.router.add_get('/test', self.test_page_handler.serve_test_page)
        self.app.router.add_get('/favicon.ico', self.serve_favicon)

        # 测试路由
        self.app.router.add_get('/test/cors', self.api_handler.test_cors)
        self.app.router.add_post('/test/cors', self.api_handler.test_cors)

        # 通用 OPTIONS 处理
        self.app.router.add_route('OPTIONS', '/{path:.*}', OptionsHandler.handle_options)

    async def serve_home_page(self, request):
        """首页 - 根据服务器状态决定显示内容"""
        if not self.mcp_server._initialized:
            # 服务器未初始化，重定向到设置页面
            return web.Response(
                status=302,
                headers={'Location': '/setup'}
            )
        else:
            # 服务器已运行，显示测试页面
            return await self.test_page_handler.serve_test_page(request)

    async def serve_favicon(self, request):
        """返回空的 favicon，避免浏览器报错"""
        # 返回 204 No Content，浏览器会忽略图标
        return web.Response(status=204)

    async def start(self):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        self.logger.info(f"MCP HTTP Server started on http://{self.host}:{self.port}")
        self.logger.info(f"Setup page: http://{self.host}:{self.port}/setup")
        self.logger.info(f"Test page: http://{self.host}:{self.port}/test")

        return runner

    async def stop(self, runner):
        """停止服务器"""
        await runner.cleanup()
        self.logger.info("MCP HTTP Server stopped")
