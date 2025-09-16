#!/usr/bin/env python3
"""
MCP 服务器测试页面
"""

import logging
from aiohttp import web
from pathlib import Path
from ..core.base import BaseMCPServer

logger = logging.getLogger(__name__)


class TestPageHandler:
    """测试页面处理器"""

    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.TestPageHandler")

    async def serve_test_page(self, request):
        """测试页面"""
        html_content = self.get_test_page_html(self.mcp_server.name, self.mcp_server.version)
        return web.Response(text=html_content, content_type='text/html')

    def get_test_page_html(self, server_name: str = "MCP Server", server_version: str = "1.0.0") -> str:
        """生成测试页面HTML"""
        # 获取模板文件路径
        template_path = Path(__file__).parent / "templates" / "test_page.html"

        try:
            # 读取HTML模板文件
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 替换模板变量
            html_content = template_content.replace('{{server_name}}', server_name)
            html_content = html_content.replace('{{server_version}}', server_version)
            
            # 设置所有端点变量
            server_host = getattr(self.mcp_server, 'host', 'localhost')
            # 动态获取端口，优先从配置管理器获取
            server_port = 8080  # 默认值
            
            # 尝试从配置管理器获取端口
            if hasattr(self.mcp_server, 'server_config_manager') and self.mcp_server.server_config_manager:
                try:
                    config = self.mcp_server.server_config_manager.load_server_config()
                    if config and 'port' in config:
                        server_port = config['port']
                        logger.info(f"Got port from config manager: {server_port}")
                except Exception as e:
                    logger.warning(f"Failed to get port from config manager: {e}")
            else:
                logger.warning(f"No server_config_manager available: hasattr={hasattr(self.mcp_server, 'server_config_manager')}, value={getattr(self.mcp_server, 'server_config_manager', None)}")
            
            # 如果配置管理器没有端口信息，尝试从HTTP服务器获取
            if server_port == 8080:  # 仍然是默认值
                http_server = getattr(self.mcp_server, '_http_server', None)
                logger.info(f"Checking HTTP server for port: {http_server}")
                if http_server and hasattr(http_server, 'port'):
                    server_port = http_server.port
                    logger.info(f"Got port from HTTP server: {server_port}")
                elif http_server:
                    logger.info(f"HTTP server attributes: {dir(http_server)}")
                    # 尝试其他可能的端口属性
                    for attr in ['_port', 'config', 'server_config']:
                        if hasattr(http_server, attr):
                            attr_value = getattr(http_server, attr)
                            logger.info(f"HTTP server {attr}: {attr_value}")
                            if attr == 'config' and hasattr(attr_value, 'port'):
                                server_port = attr_value.port
                                logger.info(f"Got port from HTTP server config: {server_port}")
                                break
            base_url = f'http://{server_host}:{server_port}'
            
            # 基础端点
            html_content = html_content.replace('{{tools_endpoint}}', f'{base_url}/mcp')
            html_content = html_content.replace('{{resources_endpoint}}', f'{base_url}/mcp')
            html_content = html_content.replace('{{tool_call_endpoint}}', f'{base_url}/tool/call')
            html_content = html_content.replace('{{sse_endpoint}}', f'{base_url}/sse/tool/call')
            html_content = html_content.replace('{{sse_stop_endpoint}}', f'{base_url}/api/streaming/stop')
            
            # OpenAI格式端点
            html_content = html_content.replace('{{openai_sse_endpoint}}', f'{base_url}/sse/openai/tool/call')
            html_content = html_content.replace('{{openai_sse_stop_endpoint}}', f'{base_url}/sse/openai/stop')

            return html_content

        except FileNotFoundError:
            # 如果模板文件不存在，返回简单的错误页面
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Template Not Found</title>
</head>
<body>
    <h1>Error: Template file not found</h1>
    <p>The HTML template file could not be found at: {template_path}</p>
    <p>Please ensure the template file exists in the correct location.</p>
</body>
</html>
            """
        except Exception as e:
            # 其他错误的处理
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Template Error</title>
</head>
<body>
    <h1>Error loading template</h1>
    <p>An error occurred while loading the template: {str(e)}</p>
</body>
</html>
            """
