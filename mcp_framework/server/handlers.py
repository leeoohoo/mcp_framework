#!/usr/bin/env python3
"""
MCP HTTP 服务器请求处理器
"""

import logging
from datetime import datetime
from aiohttp import web
from typing import Dict, Any, Union
import json
import asyncio

from ..core.base import BaseMCPServer
from ..core.config import ConfigManager, ServerConfigAdapter

logger = logging.getLogger(__name__)


class MCPRequestHandler:
    """MCP 请求处理器"""

    def __init__(self, mcp_server: BaseMCPServer, config_manager: Union[ConfigManager, ServerConfigAdapter]):
        self.mcp_server = mcp_server
        self.config_manager = config_manager
        self.start_time = datetime.now()
        self.logger = logging.getLogger(f"{__name__}.MCPRequestHandler")

    async def handle_mcp_request(self, request):
        """处理 MCP 请求"""
        try:
            data = await request.json()
            method = data.get('method')
            params = data.get('params', {})
            request_id = data.get('id')

            self.logger.debug(f"MCP Request: {method} with params: {params}")

            if method == 'initialize':
                result = await self.handle_initialize(params)
            elif method == 'tools/list':
                result = await self.handle_tools_list(params)
            elif method == 'tools/call':
                result = await self.handle_tool_call(params)
            elif method == 'resources/list':
                result = await self.handle_resources_list()
            elif method == 'resources/read':
                result = await self.handle_resource_read(params)
            else:
                raise ValueError(f"Unknown method: {method}")

            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result
            }

        except Exception as e:
            self.logger.error(f"Error in MCP request: {str(e)}")
            response = {
                'jsonrpc': '2.0',
                'id': data.get('id') if 'data' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }

        return web.json_response(response)

    async def handle_initialize(self, params):
        """处理初始化请求"""
        await self.mcp_server.startup()
        return {
            'protocolVersion': '2024-11-05',
            'capabilities': {
                'tools': {},
                'resources': {},
                'streaming': {}  # 新增：声明支持流式响应
            },
            'serverInfo': {
                'name': self.mcp_server.name,
                'version': self.mcp_server.version
            }
        }

    async def handle_tools_list(self, params=None):
        """处理工具列表请求"""
        # 获取role参数
        role = params.get('role') if params else None
        
        if role:
            # 如果指定了role，返回匹配该role的工具和没有role的工具
            filtered_tools = []
            for tool in self.mcp_server.tools:
                # 检查新的roles数组格式
                if 'roles' in tool and tool['roles']:
                    if role in tool['roles']:
                        filtered_tools.append(tool)
                # 向后兼容：检查旧的role格式
                elif tool.get('role') == role:
                    filtered_tools.append(tool)
                # 没有角色限制的工具（通用工具）
                elif tool.get('role') is None and tool.get('roles') is None:
                    filtered_tools.append(tool)
            return {
                'tools': filtered_tools
            }
        else:
            # 如果没有指定role，返回所有工具
            return {
                'tools': self.mcp_server.tools
            }

    def _coerce_value(self, value, expected_type: str):
        """根据期望类型转换单个值"""
        if expected_type == 'integer':
            if isinstance(value, int):
                return value
            if isinstance(value, bool):  # 避免 bool 被当作 int
                return int(value)
            if isinstance(value, (float,)):
                return int(value)
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return None
                return int(v)
        elif expected_type == 'number':
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return None
                return float(v)
        elif expected_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                v = value.strip().lower()
                if v in ('true', '1', 'yes', 'on'): return True
                if v in ('false', '0', 'no', 'off', ''): return False
        elif expected_type == 'array':
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return []
                # 优先尝试 JSON 解析
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
                # 退化为逗号分隔
                return [item.strip() for item in v.split(',') if item.strip() != '']
        elif expected_type == 'object':
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return {}
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    return {}
        elif expected_type == 'string':
            if value is None:
                return ''
            return str(value)
        # 未识别类型，原样返回
        return value

    def _coerce_arguments_with_schema(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """依据工具的 input_schema 将传入参数转换为期望类型，并填充默认值"""
        tool = next((t for t in self.mcp_server.tools if t['name'] == tool_name), None)
        if not tool:
            self.logger.warning(f"Tool '{tool_name}' not found")
            return arguments

        schema = getattr(tool, 'input_schema', {}) or {}
        props: Dict[str, Any] = schema.get('properties', {}) or {}
        self.logger.info(f"Tool '{tool_name}' schema: {schema}")
        self.logger.info(f"Tool '{tool_name}' properties: {props}")
        coerced: Dict[str, Any] = {}

        for key, prop_schema in props.items():
            expected_type = prop_schema.get('type')
            # 允许 JSON Schema 的多类型写法，取第一个
            if isinstance(expected_type, list) and expected_type:
                expected_type = expected_type[0]
            default_present = 'default' in prop_schema
            default_value = prop_schema.get('default')

            if key in arguments:
                raw_val = arguments.get(key)
                # 空字符串按未提供处理，用默认值
                if isinstance(raw_val, str) and raw_val.strip() == '':
                    coerced[key] = default_value if default_present else raw_val
                    continue
                if expected_type:
                    try:
                        coerced_val = self._coerce_value(raw_val, expected_type)
                        # 若转换得到 None 且有默认值，则使用默认
                        if coerced_val is None and default_present:
                            coerced[key] = default_value
                        else:
                            coerced[key] = coerced_val
                    except Exception as e:
                        # 类型转换失败，抛出详细错误信息
                        raise ValueError(
                            f"Parameter '{key}' expects type '{expected_type}' but got '{type(raw_val).__name__}' with value '{raw_val}': {str(e)}")
                else:
                    coerced[key] = raw_val
            else:
                # 未提供参数，若 schema 有默认值则填充
                if default_present:
                    coerced[key] = default_value
        # 保留未在 schema 中声明但传入的参数
        for extra_key, extra_val in arguments.items():
            if extra_key not in coerced:
                coerced[extra_key] = extra_val

        return coerced

    async def handle_tool_call(self, params):
        """处理工具调用请求"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if not tool_name:
            raise ValueError("Tool name is required")

        # 检查工具是否存在
        tool_exists = any(tool['name'] == tool_name for tool in self.mcp_server.tools)
        if not tool_exists:
            raise ValueError(f"Tool '{tool_name}' not found")

        # 基于工具 schema 对参数进行类型转换和默认值填充
        try:
            arguments = self._coerce_arguments_with_schema(tool_name, arguments)
        except Exception as e:
            self.logger.warning(f"Failed to coerce arguments for tool '{tool_name}': {e}")

        result = await self.mcp_server.handle_tool_call(tool_name, arguments)

        return {
            'content': [
                {
                    'type': 'text',
                    'text': str(result)
                }
            ]
        }

    async def handle_resources_list(self):
        """处理资源列表请求"""
        return {
            'resources': self.mcp_server.resources
        }

    async def handle_resource_read(self, params):
        """处理资源读取请求"""
        uri = params.get('uri')
        if not uri:
            raise ValueError("Resource URI is required")

        result = await self.mcp_server.handle_resource_request(uri)
        return result


class SSEHandler:
    """Server-Sent Events 处理器"""

    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.SSEHandler")
        self.start_time = datetime.now()  # 新增：记录 SSE 连接开始时间

    def _coerce_value(self, value, expected_type: str):
        """根据期望类型转换单个值"""
        if expected_type == 'integer':
            if isinstance(value, int):
                return value
            if isinstance(value, bool):  # 避免 bool 被当作 int
                return int(value)
            if isinstance(value, (float,)):
                return int(value)
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return None
                return int(v)
        elif expected_type == 'number':
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return None
                return float(v)
        elif expected_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                v = value.strip().lower()
                if v in ('true', '1', 'yes', 'on'): return True
                if v in ('false', '0', 'no', 'off', ''): return False
        elif expected_type == 'array':
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return []
                # 优先尝试 JSON 解析
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
                # 退化为逗号分隔
                return [item.strip() for item in v.split(',') if item.strip() != '']
        elif expected_type == 'object':
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                v = value.strip()
                if v == '':
                    return {}
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    return {}
        elif expected_type == 'string':
            if value is None:
                return ''
            return str(value)
        # 未识别类型，原样返回
        return value

    def _coerce_arguments_with_schema(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """依据工具的 input_schema 将传入参数转换为期望类型，并填充默认值"""
        tool = next((t for t in self.mcp_server.tools if t['name'] == tool_name), None)
        if not tool:
            self.logger.warning(f"Tool '{tool_name}' not found")
            return arguments

        schema = getattr(tool, 'input_schema', {}) or {}
        props: Dict[str, Any] = schema.get('properties', {}) or {}
        self.logger.info(f"Tool '{tool_name}' schema: {schema}")
        self.logger.info(f"Tool '{tool_name}' properties: {props}")
        coerced: Dict[str, Any] = {}

        for key, prop_schema in props.items():
            expected_type = prop_schema.get('type')
            # 允许 JSON Schema 的多类型写法，取第一个
            if isinstance(expected_type, list) and expected_type:
                expected_type = expected_type[0]
            default_present = 'default' in prop_schema
            default_value = prop_schema.get('default')

            if key in arguments:
                raw_val = arguments.get(key)
                # 空字符串按未提供处理，用默认值
                if isinstance(raw_val, str) and raw_val.strip() == '':
                    coerced[key] = default_value if default_present else raw_val
                    continue
                if expected_type:
                    try:
                        coerced_val = self._coerce_value(raw_val, expected_type)
                        # 若转换得到 None 且有默认值，则使用默认
                        if coerced_val is None and default_present:
                            coerced[key] = default_value
                        else:
                            coerced[key] = coerced_val
                    except Exception as e:
                        # 类型转换失败，抛出详细错误信息
                        raise ValueError(
                            f"Parameter '{key}' expects type '{expected_type}' but got '{type(raw_val).__name__}' with value '{raw_val}': {str(e)}")
                else:
                    coerced[key] = raw_val
            else:
                # 未提供参数，若 schema 有默认值则填充
                if default_present:
                    coerced[key] = default_value
        # 保留未在 schema 中声明但传入的参数
        for extra_key, extra_val in arguments.items():
            if extra_key not in coerced:
                coerced[extra_key] = extra_val

        return coerced

    async def handle_sse_tool_call(self, request):
        """处理 SSE 工具调用请求"""
        # 先创建 SSE 响应，确保所有错误都能通过 SSE 事件返回
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        await response.prepare(request)
        
        session_id = None
        try:
            # 获取查询参数或 POST 数据
            if request.method == 'POST':
                data = await request.json()
                tool_name = data.get('tool_name')
                arguments = data.get('arguments', {})
            else:
                # GET 请求，从查询参数获取
                tool_name = request.query.get('tool_name')
                arguments_str = request.query.get('arguments')

                if arguments_str:
                    # 如果有arguments参数，尝试解析JSON
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}
                        for key, value in request.query.items():
                            if key != 'tool_name':
                                arguments[key] = value
                else:
                    # 如果没有arguments参数，直接从查询参数构建arguments
                    arguments = {}
                    for key, value in request.query.items():
                        if key != 'tool_name':
                            arguments[key] = value

                self.logger.debug(f"Parsed arguments from query params: {arguments}")

            self.logger.info(f"SSE tool call - tool_name: {tool_name}, arguments: {arguments}")

            if not tool_name:
                raise ValueError("Tool name is required")

            # 检查工具是否存在
            tool_exists = any(tool['name'] == tool_name for tool in self.mcp_server.tools)
            if not tool_exists:
                raise ValueError(f"Tool '{tool_name}' not found")

            # 基于工具 schema 对参数进行类型转换和默认值填充
            try:
                self.logger.info(f"Before coercion: {arguments}")
                arguments = self._coerce_arguments_with_schema(tool_name, arguments)
                self.logger.info(f"After coercion: {arguments}")
            except Exception as e:
                self.logger.warning(f"Failed to coerce arguments for tool '{tool_name}': {e}")
                raise ValueError(f"Tool '{tool_name}' missing required parameter: {str(e).split(': ')[-1] if ': ' in str(e) else str(e)}")

            # 创建流式会话
            session_id = self.mcp_server.start_streaming_session()
            
            # 添加会话ID到响应头
            response.headers['X-Session-ID'] = session_id

            # 发送开始事件，包含会话ID
            if not await self._send_sse_event(response, 'start', {
                'tool_name': tool_name,
                'arguments': arguments,
                'session_id': session_id
            }):
                return response  # 连接已关闭，直接返回

            try:
                # 所有工具都使用统一的流式处理
                async for chunk in self.mcp_server.handle_tool_call_stream(tool_name, arguments, session_id):
                    # 检查是否应该停止
                    if self.mcp_server.is_streaming_stopped(session_id):
                        await self._send_sse_event(response, 'stopped',
                                                   {'session_id': session_id, 'reason': 'User requested stop'})
                        break

                    logger.debug(f"SSE Handler received chunk: {type(chunk)} - {chunk}")
                    # 直接发送chunk内容，不再包装在另一个字典中
                    if isinstance(chunk, str):
                        try:
                            # 尝试解析为JSON
                            chunk_data = json.loads(chunk)
                            logger.debug(f"SSE Handler parsed JSON chunk: {chunk_data}")
                            if not await self._send_sse_event(response, 'data', chunk_data):
                                break
                        except json.JSONDecodeError:
                            logger.debug(f"SSE Handler sending plain text chunk: {chunk}")
                            if not await self._send_sse_event(response, 'data', {'chunk': chunk}):
                                break
                    else:
                        logger.debug(f"SSE Handler sending dict chunk: {chunk}")
                        if not await self._send_sse_event(response, 'data', chunk):
                            break  # 连接已关闭，退出循环
                    await asyncio.sleep(0.01)  # 小延迟避免过快发送

                # 发送完成事件
                await self._send_sse_event(response, 'end', {'status': 'completed', 'session_id': session_id})

            except Exception as e:
                # 发送错误事件
                await self._send_sse_event(response, 'error', {
                    'error': str(e),
                    'code': 'TOOL_CALL_ERROR',
                    'session_id': session_id
                })
            finally:
                # 清理会话
                self.mcp_server.cleanup_streaming_session(session_id)

            return response

        except Exception as e:
            self.logger.error(f"SSE tool call error: {str(e)}")
            # 通过 SSE 事件发送错误信息，而不是返回 JSON 响应
            await self._send_sse_event(response, 'error', {
                'error': str(e),
                'code': 'SSE_INIT_ERROR',
                'session_id': session_id
            })
            # 清理会话（如果已创建）
            if session_id:
                self.mcp_server.cleanup_streaming_session(session_id)
        
        return response

    async def _send_sse_event(self, response, event_type: str, data: dict):
        """发送 SSE 事件"""
        try:
            # 检查连接是否仍然有效
            # 使用hasattr检查transport属性是否存在，避免AttributeError
            if (hasattr(response, 'transport') and
                    (response.transport is None or response.transport.is_closing())):
                self.logger.warning(f"SSE连接已关闭，跳过发送事件: {event_type}")
                return False

            # 检查response是否已经准备好
            if not hasattr(response, '_payload_writer') or response._payload_writer is None:
                self.logger.warning(f"SSE响应未准备好，跳过发送事件: {event_type}")
                return False

            event_data = json.dumps(data, ensure_ascii=False)
            message = f"event: {event_type}\ndata: {event_data}\n\n"
            await response.write(message.encode('utf-8'))
            await response.drain()
            return True
        except Exception as e:
            self.logger.warning(f"发送SSE事件失败: {e}")
            return False

    async def handle_sse_info(self, request):
        """提供 SSE 功能信息"""
        # 获取支持流式输出的工具列表（所有工具都支持流式）
        streaming_tools = [tool['name'] for tool in self.mcp_server.tools]

        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'

        await response.prepare(request)

        # 发送服务器信息
        if not await self._send_sse_event(response, 'info', {
            'server_name': self.mcp_server.name,
            'server_version': self.mcp_server.version,
            'streaming_tools': streaming_tools,
            'total_tools': len(self.mcp_server.tools),
            'sse_endpoint': '/sse/tool/call'
        }):
            return response  # 连接已关闭，直接返回

        # 保持连接并定期发送心跳
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                if not await self._send_sse_event(response, 'heartbeat', {
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
                }):
                    break  # 连接已关闭，退出循环
        except Exception:
            # 客户端断开连接
            pass

        return response
    
    async def handle_sse_tool_call_openai(self, request):
        """处理 OpenAI 格式的 SSE 工具调用请求"""
        # 创建 SSE 响应
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        await response.prepare(request)
        
        session_id = None
        try:
            # 获取查询参数或 POST 数据
            if request.method == 'POST':
                data = await request.json()
                tool_name = data.get('tool_name')
                arguments = data.get('arguments', {})
            else:
                # GET 请求，从查询参数获取
                tool_name = request.query.get('tool_name')
                arguments_str = request.query.get('arguments')

                if arguments_str:
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}
                        for key, value in request.query.items():
                            if key != 'tool_name':
                                arguments[key] = value
                else:
                    arguments = {}
                    for key, value in request.query.items():
                        if key != 'tool_name':
                            arguments[key] = value

            self.logger.info(f"OpenAI SSE tool call - tool_name: {tool_name}, arguments: {arguments}")

            if not tool_name:
                raise ValueError("Tool name is required")

            # 检查工具是否存在
            tool_exists = any(tool['name'] == tool_name for tool in self.mcp_server.tools)
            if not tool_exists:
                raise ValueError(f"Tool '{tool_name}' not found")

            # 基于工具 schema 对参数进行类型转换和默认值填充
            try:
                arguments = self._coerce_arguments_with_schema(tool_name, arguments)
            except Exception as e:
                raise ValueError(f"Tool '{tool_name}' missing required parameter: {str(e).split(': ')[-1] if ': ' in str(e) else str(e)}")

            # 创建流式会话
            session_id = self.mcp_server.start_streaming_session()
            
            # 添加会话ID到响应头
            response.headers['X-Session-ID'] = session_id

            try:
                # 使用OpenAI格式的流式处理
                async for openai_chunk in self.mcp_server.handle_tool_call_stream_openai(tool_name, arguments, session_id):
                    # 检查是否应该停止
                    if self.mcp_server.is_streaming_stopped(session_id):
                        # 发送停止事件
                        await response.write(b"data: [DONE]\n\n")
                        break

                    # 直接写入OpenAI格式的SSE数据
                    try:
                        await response.write(openai_chunk.encode('utf-8'))
                        await response.drain()
                    except Exception as write_error:
                        self.logger.warning(f"Failed to write OpenAI SSE data: {write_error}")
                        break
                    
                    await asyncio.sleep(0.01)  # 小延迟避免过快发送

                # 发送完成标记
                await response.write(b"data: [DONE]\n\n")

            except Exception as e:
                # 发送错误事件（OpenAI格式）
                from ..core.streaming import OpenAIStreamFormatter
                formatter = OpenAIStreamFormatter(f"{self.mcp_server.name}-{self.mcp_server.version}", session_id)
                error_chunk = formatter.create_error_chunk(str(e))
                await response.write(error_chunk.to_sse_data().encode('utf-8'))
            finally:
                # 清理会话
                if session_id:
                    self.mcp_server.cleanup_streaming_session(session_id)

            return response

        except Exception as e:
            self.logger.error(f"OpenAI SSE tool call error: {str(e)}")
            # 发送错误事件
            from ..core.streaming import OpenAIStreamFormatter
            formatter = OpenAIStreamFormatter(f"{self.mcp_server.name}-{self.mcp_server.version}", session_id)
            error_chunk = formatter.create_error_chunk(str(e))
            await response.write(error_chunk.to_sse_data().encode('utf-8'))
            
            # 清理会话（如果已创建）
            if session_id:
                self.mcp_server.cleanup_streaming_session(session_id)
        
        return response


class APIHandler:
    """API 处理器"""

    def __init__(self, mcp_server: BaseMCPServer, config_manager: Union[ConfigManager, ServerConfigAdapter]):
        self.mcp_server = mcp_server
        self.config_manager = config_manager
        self.start_time = datetime.now()
        self.logger = logging.getLogger(f"{__name__}.APIHandler")

    async def health_check(self, request):
        """健康检查"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'server': self.mcp_server.name,
            'initialized': self.mcp_server._initialized
        })

    async def server_info(self, request):
        """服务器信息"""
        return web.json_response({
            'name': self.mcp_server.name,
            'version': self.mcp_server.version,
            'description': self.mcp_server.description,
            'tools_count': len(self.mcp_server.tools),
            'resources_count': len(self.mcp_server.resources),
            'initialized': self.mcp_server._initialized,
            'start_time': self.start_time.isoformat(),
            'protocols': ['http', 'sse'],  # 新增：支持的协议列表
            'streaming_tools': [t['name'] for t in self.mcp_server.tools]  # 所有工具都支持流式
        })

    async def metrics(self, request):
        """服务器指标"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return web.json_response({
            'uptime_seconds': uptime,
            'tools_count': len(self.mcp_server.tools),
            'resources_count': len(self.mcp_server.resources),
            'streaming_tools_count': len(self.mcp_server.tools)  # 所有工具都支持流式
        })

    async def version_info(self, request):
        """版本信息"""
        return web.json_response({
            'server_version': self.mcp_server.version,
            'protocol_version': '2024-11-05',
            'features': ['tools', 'resources', 'streaming', 'sse']  # 新增特性列表
        })

    async def tools_list(self, request):
        """工具列表 - 支持role参数过滤"""
        # 获取role查询参数
        role = request.query.get('role')
        
        if role:
            # 如果指定了role，返回匹配该role的工具和没有role的工具
            filtered_tools = []
            for tool in self.mcp_server.tools:
                # 检查新的roles数组格式
                if 'roles' in tool and tool['roles']:
                    if role in tool['roles']:
                        filtered_tools.append(tool)
                # 向后兼容：检查旧的role格式
                elif tool.get('role') == role:
                    filtered_tools.append(tool)
                # 没有角色限制的工具（通用工具）
                elif tool.get('role') is None and tool.get('roles') is None:
                    filtered_tools.append(tool)
            return web.json_response({
                'tools': filtered_tools
            })
        else:
            # 如果没有指定role，返回所有工具
            return web.json_response({
                'tools': self.mcp_server.tools
            })

    async def get_config(self, request):
        """获取当前配置"""
        config = self.config_manager.load_config()
        config_dict = config.to_dict()
        
        # 如果使用的是 ServerConfigAdapter，添加别名信息
        if hasattr(self.config_manager, 'server_config_manager'):
            server_config_manager = self.config_manager.server_config_manager
            config_dict['alias'] = getattr(server_config_manager, 'alias', None)
        
        return web.json_response(config_dict)

    async def update_config(self, request):
        """更新配置"""
        try:
            data = await request.json()

            # 加载当前配置
            current_config = self.config_manager.load_config()
            old_config_dict = current_config.to_dict()

            # 分离别名和其他配置项
            alias_value = data.pop('alias', None)
            
            # 更新配置
            for key, value in data.items():
                if hasattr(current_config, key):
                    setattr(current_config, key, value)

            # 保存配置
            if self.config_manager.save_config(current_config):
                # 如果有别名更新且使用的是 ServerConfigAdapter，更新别名
                if alias_value is not None and hasattr(self.config_manager, 'server_config_manager'):
                    server_config_manager = self.config_manager.server_config_manager
                    server_config_manager.alias = alias_value
                    self.logger.info(f"别名已更新为: {alias_value}")
                
                # 通知MCP服务器配置更新（如果配置项与服务器参数相关）
                new_config_dict = current_config.to_dict()
                if hasattr(self.mcp_server, '_notify_config_update'):
                    self.mcp_server._notify_config_update(old_config_dict, new_config_dict)
                
                return web.json_response({
                    'success': True,
                    'message': 'Configuration updated successfully'
                })
            else:
                return web.json_response({
                    'success': False,
                    'message': 'Failed to save configuration'
                }, status=500)

        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=400)

    async def reset_config(self, request):
        """重置配置"""
        try:
            config = self.config_manager.reset_config()
            return web.json_response({
                'success': True,
                'message': 'Configuration reset to defaults',
                'config': config.to_dict()
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def restart_server(self, request):
        """重启服务器"""
        try:
            # 重新初始化服务器
            await self.mcp_server.shutdown()
            await self.mcp_server.startup()

            return web.json_response({
                'status': 'success',
                'message': 'Server restarted successfully'
            })
        except Exception as e:
            logger.error(f"Failed to restart server: {e}")
            return web.json_response({
                'status': 'error',
                'message': f'Failed to restart server: {str(e)}'
            }, status=500)

    async def test_cors(self, request):
        """测试 CORS"""
        return web.json_response({
            'message': 'CORS test successful',
            'method': request.method,
            'headers': dict(request.headers),
            'timestamp': datetime.now().isoformat()
        })

    async def stop_streaming_session(self, request):
        """停止指定的流式会话"""
        try:
            session_id = request.query.get('session_id')
            if not session_id:
                data = await request.json()
                session_id = data.get('session_id')

            if not session_id:
                return web.json_response({
                    'success': False,
                    'message': 'Session ID is required'
                }, status=400)

            success = self.mcp_server.stop_streaming_session(session_id)
            return web.json_response({
                'success': success,
                'message': f'Session {session_id} stopped' if success else f'Session {session_id} not found'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def stop_all_streaming(self, request):
        """停止所有流式输出"""
        try:
            self.mcp_server.stop_all_streaming()
            return web.json_response({
                'success': True,
                'message': 'All streaming sessions stopped'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def resume_streaming(self, request):
        """恢复流式输出"""
        try:
            self.mcp_server.resume_streaming()
            return web.json_response({
                'success': True,
                'message': 'Streaming resumed'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def get_streaming_status(self, request):
        """获取流式状态"""
        try:
            active_sessions = self.mcp_server.get_active_streaming_sessions()
            return web.json_response({
                'global_stopped': self.mcp_server._stop_streaming,
                'active_sessions': active_sessions,
                'total_active_sessions': len(active_sessions)
            })
        except Exception as e:
            return web.json_response({
                'error': str(e)
            }, status=500)


class ServerConfigHandler:
    """服务器配置处理器"""
    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.ServerConfigHandler")

    async def get_server_parameters(self, request):
        """获取服务器参数定义"""
        try:
            parameters = self.mcp_server.get_server_parameters()
            return web.json_response({
                'success': True,
                'parameters': [
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
            })
        except Exception as e:
            self.logger.error(f"Failed to get server parameters: {e}")
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def configure_server(self, request):
        """配置服务器"""
        try:
            data = await request.json()
            config = data.get('config', {})

            if self.mcp_server.configure_server(config):
                return web.json_response({
                    'success': True,
                    'message': 'Server configured successfully'
                })
            else:
                return web.json_response({
                    'success': False,
                    'message': 'Failed to configure server'
                }, status=400)

        except Exception as e:
            self.logger.error(f"Configuration error: {e}")
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=400)

    async def start_configured_server(self, request):
        """启动已配置的服务器"""
        try:
            if not self.mcp_server._initialized:
                await self.mcp_server.startup()
                return web.json_response({
                    'success': True,
                    'message': 'Server started successfully'
                })
            else:
                return web.json_response({
                    'success': True,
                    'message': 'Server is already running'
                })
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return web.json_response({
                'success': False,
                'message': str(e)
            }, status=500)

    async def get_server_status(self, request):
        """获取服务器状态"""
        # 检查是否已配置：必须有配置数据且已保存
        configured = bool(self.mcp_server.server_config) and self.mcp_server.server_config_manager.config_exists()

        return web.json_response({
            'initialized': self.mcp_server._initialized,
            'configured': configured,
            'name': self.mcp_server.name,
            'version': self.mcp_server.version,
            'config': self.mcp_server.server_config
        })


class OptionsHandler:
    """OPTIONS 请求处理器"""

    @staticmethod
    async def handle_options(request):
        """处理 OPTIONS 请求"""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cache-Control'
            }
        )
