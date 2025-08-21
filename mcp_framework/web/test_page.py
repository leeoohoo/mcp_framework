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
