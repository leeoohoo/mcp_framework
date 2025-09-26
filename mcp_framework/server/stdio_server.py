#!/usr/bin/env python3
"""
MCP stdio 服务器实现
支持通过标准输入输出进行通信，包含流式传输支持和配置管理
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional, AsyncGenerator
from ..core.base import BaseMCPServer
from ..core.config import ConfigManager

logger = logging.getLogger(__name__)


class MCPStdioServer:
    """MCP stdio 服务器 - 支持流式传输和配置管理"""
    
    def __init__(self, mcp_server: BaseMCPServer, config_manager: Optional[ConfigManager] = None):
        self.mcp_server = mcp_server
        self.config_manager = config_manager
        self.logger = logging.getLogger(f"{__name__}.MCPStdioServer")
        self._running = False
        self._stream_tasks = set()  # 跟踪流式任务
        
    async def start(self):
        """启动stdio服务器"""
        self._running = True
        self.logger.info("MCP stdio服务器启动")
        
        # 初始化MCP服务器
        if not self.mcp_server._initialized:
            await self.mcp_server.initialize()
        
        try:
            # 主循环：读取stdin，处理请求，写入stdout
            while self._running:
                try:
                    # 从stdin读取一行
                    line = await self._read_line()
                    if not line:
                        break
                        
                    # 解析JSON请求
                    try:
                        request = json.loads(line.strip())
                    except json.JSONDecodeError as e:
                        await self._send_error(f"Invalid JSON: {e}")
                        continue
                    
                    # 处理请求 - 支持流式和非流式
                    request_id = request.get("id")
                    method = request.get("method", "")
                    
                    # 检查是否为流式请求
                    if self._is_streaming_request(request):
                        # 创建流式处理任务
                        task = asyncio.create_task(
                            self._handle_streaming_request(request)
                        )
                        self._stream_tasks.add(task)
                        task.add_done_callback(self._stream_tasks.discard)
                    else:
                        # 普通请求处理
                        response = await self._handle_request(request)
                        await self._send_response(response)
                    
                except Exception as e:
                    self.logger.error(f"处理请求时出错: {e}")
                    await self._send_error(f"Internal error: {e}")
                    
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止服务器")
        finally:
            self._running = False
            
    async def stop(self):
        """停止stdio服务器"""
        self._running = False
        
        # 取消所有流式任务
        for task in self._stream_tasks:
            if not task.done():
                task.cancel()
        
        # 等待所有任务完成
        if self._stream_tasks:
            await asyncio.gather(*self._stream_tasks, return_exceptions=True)
            
        self.logger.info("MCP stdio服务器停止")
        
    async def _read_line(self) -> Optional[str]:
        """从stdin异步读取一行"""
        try:
            # 使用线程池执行阻塞的readline操作
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(None, sys.stdin.readline)
            return line if line else None
        except Exception as e:
            self.logger.error(f"读取stdin失败: {e}")
            return None
            
    async def _send_response(self, response: Dict[str, Any]):
        """发送响应到stdout"""
        try:
            json_str = json.dumps(response, ensure_ascii=False)
            print(json_str, flush=True)
        except Exception as e:
            self.logger.error(f"发送响应失败: {e}")
            
    async def _send_error(self, error_message: str):
        """发送错误响应"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": error_message
            },
            "id": None
        }
        await self._send_response(error_response)
        
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            # 检查JSON-RPC格式
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": request.get("id")
                }
            
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # 处理不同的MCP方法
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tool_call(params)
            elif method == "resources/list":
                result = await self._handle_resources_list()
            elif method == "resources/read":
                result = await self._handle_resource_read(params)
            # 配置管理相关方法
            elif method == "config/get":
                result = await self._handle_config_get(params)
            elif method == "config/update":
                result = await self._handle_config_update(params)
            elif method == "config/reset":
                result = await self._handle_config_reset(params)
            elif method == "server/parameters":
                result = await self._handle_server_parameters(params)
            elif method == "server/configure":
                result = await self._handle_server_configure(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
            
        except Exception as e:
            self.logger.error(f"处理请求失败: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                },
                "id": request.get("id")
            }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": self.mcp_server.name,
                "version": self.mcp_server.version
            }
        }
    
    def _is_streaming_request(self, request: Dict[str, Any]) -> bool:
        """判断是否为流式请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        # 检查是否明确要求流式传输
        if params.get("stream", False):
            return True
            
        # 检查特定的流式方法
        streaming_methods = [
            "tools/call_streaming",
            "resources/read_streaming", 
            "completion/stream"
        ]
        
        return method in streaming_methods
    
    async def _handle_streaming_request(self, request: Dict[str, Any]):
        """处理流式请求"""
        try:
            method = request.get("method", "")
            request_id = request.get("id")
            params = request.get("params", {})
            
            # 发送流开始标记
            await self._send_stream_start(request_id)
            
            if method == "tools/call" or method == "tools/call_streaming":
                async for chunk in self._handle_tool_call_streaming(params):
                    await self._send_stream_chunk(request_id, chunk)
                    
            elif method == "resources/read" or method == "resources/read_streaming":
                async for chunk in self._handle_resource_read_streaming(params):
                    await self._send_stream_chunk(request_id, chunk)
                    
            else:
                # 默认流式处理
                response = await self._handle_request(request)
                await self._send_stream_chunk(request_id, response.get("result", {}))
            
            # 发送流结束标记
            await self._send_stream_end(request_id)
            
        except Exception as e:
            self.logger.error(f"流式请求处理失败: {e}")
            await self._send_stream_error(request_id, str(e))
    
    async def _handle_tool_call_streaming(self, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式工具调用"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        try:
            # 检查工具是否支持流式
            if hasattr(self.mcp_server, '_stream_handlers') and tool_name in self.mcp_server._stream_handlers:
                async for chunk in self.mcp_server._stream_handlers[tool_name](**arguments):
                    yield {
                        "type": "tool_result_chunk",
                        "tool": tool_name,
                        "content": chunk
                    }
            else:
                # 回退到普通调用，模拟流式
                result = await self.mcp_server.handle_tool_call(tool_name, arguments)
                
                # 将结果分块发送
                content = str(result.get("content", ""))
                chunk_size = 50  # 每块50字符
                
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    yield {
                        "type": "tool_result_chunk", 
                        "tool": tool_name,
                        "content": chunk,
                        "is_final": i + chunk_size >= len(content)
                    }
                    # 模拟流式延迟
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            yield {
                "type": "error",
                "message": f"工具调用失败: {e}"
            }
    
    async def _handle_resource_read_streaming(self, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式资源读取"""
        uri = params.get("uri", "")
        
        try:
            # 检查资源是否支持流式读取
            if hasattr(self.mcp_server, '_resource_handlers') and uri in self.mcp_server._resource_handlers:
                # 对于资源，暂时不支持流式，直接返回完整内容
                result = await self.mcp_server._resource_handlers[uri]()
                yield {
                    "type": "resource_chunk",
                    "uri": uri,
                    "content": result
                }
            else:
                # 回退到普通读取，模拟流式
                result = await self.mcp_server.handle_resource_request(uri)
                content = result.get("contents", [])
                
                # 分块发送内容
                for i, item in enumerate(content):
                    yield {
                        "type": "resource_chunk",
                        "uri": uri,
                        "content": item,
                        "chunk_index": i,
                        "is_final": i == len(content) - 1
                    }
                    await asyncio.sleep(0.05)  # 模拟流式延迟
                    
        except Exception as e:
            yield {
                "type": "error", 
                "message": f"资源读取失败: {e}"
            }
    
    async def _send_stream_start(self, request_id: Any):
        """发送流开始标记"""
        message = {
            "jsonrpc": "2.0",
            "method": "stream/start",
            "params": {
                "request_id": request_id
            }
        }
        await self._send_response(message)

    async def _send_stream_chunk(self, request_id: Any, chunk: Dict[str, Any]):
        """发送流数据块"""
        message = {
            "jsonrpc": "2.0", 
            "method": "stream/chunk",
            "params": {
                "request_id": request_id,
                "chunk": chunk
            }
        }
        await self._send_response(message)

    async def _send_stream_end(self, request_id: Any):
        """发送流结束标记"""
        message = {
            "jsonrpc": "2.0",
            "method": "stream/end",
            "params": {
                "request_id": request_id
            }
        }
        await self._send_response(message)
    
    async def _send_stream_error(self, request_id: Any, error_message: str):
        """发送流错误"""
        message = {
            "jsonrpc": "2.0",
            "method": "stream/error",
            "params": {
                "request_id": request_id,
                "error": error_message
            }
        }
        await self._send_response(message)
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """处理工具列表请求"""
        return {
            "tools": self.mcp_server.tools
        }
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Missing tool name")
        
        # 调用MCP服务器的工具处理方法
        result = await self.mcp_server.handle_tool_call(tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """处理资源列表请求"""
        return {
            "resources": self.mcp_server.resources
        }
    
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源读取请求"""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Missing resource URI")
        
        # 调用MCP服务器的资源处理方法
        result = await self.mcp_server.handle_resource_request(uri)
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": str(result)
                }
            ]
        }
    
    async def _handle_config_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取配置请求"""
        if not self.config_manager:
            return {
                "error": "Configuration manager not available"
            }
        
        try:
            # 如果配置管理器支持直接字典操作，使用它来获取包含自定义字段的完整配置
            if hasattr(self.config_manager, 'load_server_config'):
                config_dict = self.config_manager.load_server_config()
                return {
                    "config": config_dict
                }
            else:
                # 回退到原有的ServerConfig对象方式
                config = self.config_manager.load_config()
                return {
                    "config": config.to_dict() if hasattr(config, 'to_dict') else config.__dict__
                }
        except Exception as e:
            self.logger.error(f"Failed to get config: {e}")
            return {
                "error": f"Failed to get config: {e}"
            }
    
    async def _handle_config_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新配置请求"""
        if not self.config_manager:
            return {
                "error": "Configuration manager not available"
            }
        
        try:
            config_data = params.get('config', {})
            
            # 如果配置管理器支持直接字典操作，使用它来保留自定义字段
            if hasattr(self.config_manager, 'update_config'):
                success = self.config_manager.update_config(config_data)
            else:
                # 回退到原有的ServerConfig对象方式
                current_config = self.config_manager.load_config()
                
                # 更新配置
                if hasattr(current_config, 'update_from_dict'):
                    current_config.update_from_dict(config_data)
                else:
                    for key, value in config_data.items():
                        if hasattr(current_config, key):
                            setattr(current_config, key, value)
                
                # 保存配置
                success = self.config_manager.save_config(current_config)
            
            if success:
                return {
                    "success": True,
                    "message": "Configuration updated successfully"
                }
            else:
                return {
                    "error": "Failed to save configuration"
                }
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return {
                "error": f"Failed to update config: {e}"
            }
    
    async def _handle_config_reset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理重置配置请求"""
        if not self.config_manager:
            return {
                "error": "Configuration manager not available"
            }
        
        try:
            config = self.config_manager.reset_config()
            return {
                "success": True,
                "message": "Configuration reset successfully",
                "config": config.to_dict() if hasattr(config, 'to_dict') else config.__dict__
            }
        except Exception as e:
            self.logger.error(f"Failed to reset config: {e}")
            return {
                "error": f"Failed to reset config: {e}"
            }
    
    async def _handle_server_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取服务器参数定义请求"""
        try:
            parameters = self.mcp_server.get_server_parameters()
            return {
                "success": True,
                "parameters": [
                    {
                        'name': param.name,
                        'display_name': param.display_name,
                        'description': param.description,
                        'type': param.param_type,
                        'default_value': param.default_value,
                        'required': param.required,
                        'options': param.options,
                        'placeholder': param.placeholder,
                        'validation_pattern': param.validation_pattern
                    } for param in parameters
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to get server parameters: {e}")
            return {
                "error": f"Failed to get server parameters: {e}"
            }
    
    async def _handle_server_configure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置服务器参数请求"""
        try:
            config = params.get('config', {})
            
            if self.mcp_server.configure_server(config):
                return {
                    "success": True,
                    "message": "Server configured successfully"
                }
            else:
                return {
                    "error": "Failed to configure server"
                }
        except Exception as e:
            self.logger.error(f"Failed to configure server: {e}")
            return {
                "error": f"Failed to configure server: {e}"
            }