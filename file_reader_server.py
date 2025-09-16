#!/usr/bin/env python3
"""
File Reader MCP Server (注解版本)
基于 EnhancedMCPServer 和装饰器系统的文件读取服务器

主要功能:
1. read_file_lines - 读取文件指定行范围（流式输出）
2. search_files_by_content - 搜索文件内容（流式输出）  
3. get_files_content - 批量读取文件内容（流式输出）
4. get_project_structure - 获取项目结构（流式输出）
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator
from typing_extensions import Annotated

# Whoosh相关导入
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser
from whoosh.highlight import Highlighter, ContextFragmenter

# 导入文件读取服务
from file_reader_service import FileReaderService

# 导入新的框架
from mcp_framework import (

    MCPHTTPServer,
    ConfigManager,
    setup_logging,
    check_dependencies
)
from mcp_framework.core import EnhancedMCPServer

# 导入装饰器
from mcp_framework.core.decorators import (
    Required as R,
    Optional as O,
    IntRange,
    ServerParam,
    StringParam,
    BooleanParam,
    PathParam
)

# 配置日志
logger = logging.getLogger("file_reader_server")


# FileReaderService 类已移动到独立的 file_reader_service.py 文件中


class FileReaderMCPServer(EnhancedMCPServer):
    """基于注解装饰器的文件读取MCP服务器"""

    def __init__(self):
        super().__init__(
            name="file-reader-server",
            version="1.0.0",
            description="文件读取MCP服务器，基于注解装饰器系统提供流式文件操作功能"
        )
        # 在构造函数中就初始化服务，使用默认值
        self.file_reader_service = FileReaderService()
        logger.info("FileReaderMCPServer initialized")

    @property
    def setup_tools(self):
        """设置工具装饰器"""

        @self.streaming_tool(description="📖 **File Line Range Reader** - Reads specific line ranges from a file and returns content with line numbers.\n" +
                         "✨ Features: Precise line-based reading with 1-based indexing, Support for both relative and absolute file paths\n" +
                         "🎯 Use Cases: Code review and analysis, Understanding specific code sections, Debugging and error investigation\n" +
                         "📋 **Required Parameters**: file_path, start_line, end_line (ALL parameters are mandatory)\n" +
                         "📋 **Usage Example**: {\"file_path\": \"src/main/kotlin/User.kt\", \"start_line\": 10, \"end_line\": 20}\n" +
                         "⚠️ **CRITICAL Output Format**: Returns compressed format like '10:class User {\\n12:private val name\\n14:fun getName()' - gaps in line numbers (e.g., missing 11, 13) indicate empty/blank lines were automatically skipped for efficiency\n" +
                         "💡 Perfect for examining specific code sections without reading entire files. Line number gaps are NORMAL and expected.")
        async def read_file_lines(
                file_path: Annotated[str, R("Path to the file to read (supports both relative and absolute paths)")],
                start_line: Annotated[int, IntRange("Starting line number (1-based indexing)", min_val=1)],
                end_line: Annotated[int, IntRange("Ending line number (1-based indexing, inclusive)", min_val=1)]
        ) -> AsyncGenerator[str, None]:
            """Reads specific line ranges from a file and returns content with line numbers"""
            project_root = self.get_config_value('project_root')
            async for chunk in self.file_reader_service.read_file_lines_stream(file_path, start_line, end_line, Path(project_root)):
                yield self._normalize_stream_chunk(chunk)

        @self.streaming_tool(description="🧠 **Hybrid Intelligent Search** - Combines smart semantic search with global text search for comprehensive results.\n" +
                         "✨ First attempts intelligent search (Class#method format, code structure understanding), then falls back to global text search if no results found.\n" +
                         "🎯 Use cases: API exploration, code understanding, architecture analysis, configuration lookup, constant search.\n" +
                         "💡 Examples: 'UserService#login', 'BaseConfigPOJO', 'DATABASE_URL', 'TODO'\n" +
                         "📋 **Parameter**: query - The search text to find in files\n" +
                         "⚠️ **Output Format**: Shows line numbers like '1:code 3:code' - missing line 2 means it was empty/blank.")
        async def search_files_by_content(
                query: Annotated[str, R("The search text to find in files: supports class names (e.g., UserService), method references (e.g., Class#method), file names, functional descriptions, or exact text matches")]
        ) -> AsyncGenerator[str, None]:
            """Combines smart semantic search with global text search for comprehensive results"""
            project_root = self.get_config_value('project_root')
            async for chunk in self.file_reader_service.search_files_by_content_stream(
                    query, 20, False, 20, None, Path(project_root)
            ):
                yield self._normalize_stream_chunk(chunk)

        # get_files_content 工具已移除

        @self.streaming_tool(description="🏗️ **Project Structure with Line Count** - Retrieves a hierarchical structure of the project with file line counts.\n" +
                         "✨ Provides complete project organization with detailed file information including line counts.\n" +
                         "🎯 Use cases: Understanding project architecture, analyzing code distribution, getting overview of file sizes.\n" +
                         "💡 Examples: Getting project structure with line counts for each file to understand codebase scale")
        async def get_project_structure(
                max_depth: Annotated[int, O("Maximum traversal depth", default=10, minimum=1)] = 10,
                include_hidden: Annotated[bool, O("Whether to include hidden files", default=False)] = False
        ) -> AsyncGenerator[str, None]:
            """Retrieves a hierarchical structure of the project with file line counts"""
            project_root = self.get_config_value('project_root')
            async for chunk in self.file_reader_service.get_project_structure_stream(max_depth, include_hidden, Path(project_root)):
                yield self._normalize_stream_chunk(chunk)



        @self.resource(uri="config://file-reader", name="File Reader Configuration", description="Current file reader configuration information")
        async def file_reader_config_resource(uri: str) -> Dict[str, Any]:
            """Get file reader configuration information"""
            config_info = {
                "project_root": str(self.file_reader_service.get_project_root()),
                "supported_extensions": list(self.file_reader_service.text_extensions),
                "ignored_directories": list(self.file_reader_service.ignore_dirs),
                "server_config": getattr(self, 'server_config', {})
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(config_info, indent=2, ensure_ascii=False)
                    }
                ]
            }

        @self.resource(uri="stats://project", name="Project Statistics", description="Project file and code line count statistics")
        async def project_stats_resource(uri: str) -> Dict[str, Any]:
            """Get project statistics information"""
            # 计算项目统计信息
            total_files = 0
            total_lines = 0
            file_types = {}

            try:
                project_root = self.file_reader_service.get_project_root()
                for file_path in project_root.rglob('*'):
                    if not file_path.is_file():
                        continue

                    relative_path = file_path.relative_to(project_root)
                    if self.file_reader_service._should_ignore_path(relative_path):
                        continue

                    total_files += 1
                    ext = file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1

                    if ext in self.file_reader_service.text_extensions:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = sum(1 for _ in f)
                                total_lines += lines
                        except (UnicodeDecodeError, PermissionError):
                            pass

                stats_info = {
                    "project_root": str(project_root),
                    "total_files": total_files,
                    "total_lines": total_lines,
                    "file_types": file_types,
                    "text_file_extensions": len(self.file_reader_service.text_extensions)
                }

            except Exception as e:
                stats_info = {"error": f"Failed to calculate stats: {str(e)}"}

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(stats_info, indent=2, ensure_ascii=False)
                    }
                ]
            }

        return True

    @property
    def setup_server_params(self):
        """设置服务器参数装饰器"""

        @self.decorators.server_param("project_root")
        async def project_root_param(
                param: Annotated[str, PathParam(
                    display_name="Project Root Directory",
                    description="Root directory path for server operations, leave empty to use current directory",
                    required=False,
                    placeholder="/path/to/project"
                )]
        ):
            """Project root directory parameter"""
            pass

        @self.decorators.server_param("max_file_size")
        async def max_file_size_param(
                param: Annotated[int, ServerParam(
                    display_name="Maximum File Size (MB)",
                    description="Maximum file size allowed for reading, in MB",
                    param_type="integer",
                    default_value=10,
                    required=False
                )]
        ):
            """Maximum file size parameter"""
            pass

        @self.decorators.server_param("enable_hidden_files")
        async def enable_hidden_files_param(
                param: Annotated[bool, BooleanParam(
                    display_name="Enable Hidden Files",
                    description="Whether to allow access to hidden files starting with dot (.)",
                    default_value=False,
                    required=False
                )]
        ):
            """Enable hidden files parameter"""
            pass

        @self.decorators.server_param("search_limit")
        async def search_limit_param(
                param: Annotated[int, ServerParam(
                    display_name="Search Result Limit",
                    description="Maximum number of results returned by search operations",
                    param_type="integer",
                    default_value=50,
                    required=False
                )]
        ):
            """Search result limit parameter"""
            pass

        return True

    async def initialize(self) -> None:
        """初始化服务器（实现基类抽象方法）"""
        # 初始化文件读取服务，传递self作为server参数
        # 服务将通过server获取配置值
        self.file_reader_service = FileReaderService(server=self)
        logger.info("Initialized file reader service with server reference")

    async def on_config_updated(self, config_key: str, new_value: Any) -> None:
        """配置更新回调方法"""
        if config_key == "project_root":
            try:
                # 配置已经在基类中更新，只需要通知服务更新索引目录和监控器
                if self.file_reader_service:
                    project_root = str(new_value).strip() if new_value else ""
                    result = self.file_reader_service.update_project_root(project_root)
                    
                    if "success" in result:
                        logger.info(f"Config updated successfully: {result['message']}")
                    else:
                        logger.error(f"Failed to update project root: {result.get('error', 'Unknown error')}")
                else:
                    # 如果服务未初始化，创建新服务
                    self.file_reader_service = FileReaderService()
                    # 如果有配置值，更新项目根目录
                    if new_value and str(new_value).strip():
                        self.file_reader_service.update_project_root(str(new_value).strip())
                        logger.info(f"Config updated: Created new service with project root: {new_value}")
                    else:
                        logger.info("Config updated: Created new service with current directory as project root")
                    
            except Exception as e:
                logger.error(f"Failed to update config for {config_key}: {e}")
        else:
            logger.info(f"Config updated: {config_key} = {new_value}")

    async def cleanup(self) -> None:
        """服务停止时的清理方法"""
        try:
            if self.file_reader_service:
                # 停止文件监控
                result = self.file_reader_service.stop_monitoring()
                if "success" in result:
                    logger.info(f"文件监控已停止: {result['message']}")
                elif "error" in result:
                    logger.warning(f"停止文件监控时出现问题: {result['error']}")
                else:
                    logger.info(f"文件监控状态: {result['message']}")
            
            # 调用基类的清理方法（如果存在）
            if hasattr(super(), 'cleanup'):
                await super().cleanup()
                
            logger.info("FileReaderMCPServer cleanup completed")
        except Exception as e:
            logger.error(f"清理过程中发生错误: {e}")

    async def shutdown(self) -> None:
        """服务关闭时的处理方法"""
        await self.cleanup()


def main():
    """主函数"""
    try:
        # 导入 MCP 框架启动器
        from mcp_framework import run_server_main
        
        # 创建服务器实例
        server = FileReaderMCPServer()
        
        # 使用 MCP 框架启动器启动服务器
        run_server_main(
            server_instance=server,
            server_name="File Reader MCP Server",
            default_port=8082,
            default_host="localhost",
            required_dependencies=[]
        )
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
