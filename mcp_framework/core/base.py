#!/usr/bin/env python3
"""
MCP 框架基础类定义
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable, Set
from dataclasses import dataclass
import inspect
import asyncio
import uuid

from .config import ServerParameter, ServerConfigManager
from .utils import get_data_dir
from .streaming import MCPStreamWrapper, OpenAIStreamFormatter


class BaseMCPServer(ABC):
    """MCP 服务器基类"""

    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.tools: List[dict] = []
        self.resources: List[dict] = []
        self._initialized = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_dir = get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 服务器运行时配置
        self.server_config: Dict[str, Any] = {}
        
        # 完整的配置数据（包括自定义字段）
        self.full_config: Dict[str, Any] = {}

        # 注意：不在这里创建配置管理器，因为它应该由启动器根据端口创建
        # 这避免了创建没有端口号的默认配置文件
        self.server_config_manager = None

        # 流式停止管理
        self._streaming_sessions: Set[str] = set()  # 活跃的流式会话ID
        self._stop_streaming: bool = False  # 全局停止标志
        self._session_stop_flags: Dict[str, bool] = {}  # 单个会话停止标志

        # 配置更新回调机制
        self._config_update_callbacks: List[Callable[[Dict[str, Any], Dict[str, Any]], None]] = []
        
        # OpenAI 格式流式包装器
        self._openai_stream_wrapper = MCPStreamWrapper(model_name=f"{name}-{version}")
        self._enable_openai_format = True  # 默认启用OpenAI格式

    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务器，子类必须实现"""
        pass

    @abstractmethod
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """处理工具调用，子类必须实现"""
        pass

    def get_server_parameters(self) -> List[ServerParameter]:
        """获取服务器配置参数定义，子类可以重写"""
        return []

    async def handle_resource_request(self, uri: str) -> Dict[str, Any]:
        """处理资源请求，子类可以重写"""
        raise NotImplementedError(f"Resource not found: {uri}")

    def _validate_arguments(self, tool_name: str, arguments: Dict[str, Any], input_schema: Dict[str, Any]) -> None:
        """验证工具调用参数的类型和值"""
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])

        # 检查必需参数
        for param_name in required:
            if param_name not in arguments:
                raise ValueError(f"Tool '{tool_name}' missing required parameter: {param_name}")

        # 验证参数类型
        for param_name, value in arguments.items():
            if param_name in properties:
                param_spec = properties[param_name]
                param_type = param_spec.get('type', 'string')

                # 类型验证
                if not self._validate_parameter_type(value, param_type):
                    raise TypeError(
                        f"Tool '{tool_name}' parameter '{param_name}' expected {param_type}, got {type(value).__name__}")

                # 数值范围验证
                if param_type in ['integer', 'number']:
                    minimum = param_spec.get('minimum')
                    maximum = param_spec.get('maximum')
                    if minimum is not None and value < minimum:
                        raise ValueError(
                            f"Tool '{tool_name}' parameter '{param_name}' value {value} is below minimum {minimum}")
                    if maximum is not None and value > maximum:
                        raise ValueError(
                            f"Tool '{tool_name}' parameter '{param_name}' value {value} is above maximum {maximum}")

                # 枚举值验证
                enum_values = param_spec.get('enum')
                if enum_values and value not in enum_values:
                    raise ValueError(
                        f"Tool '{tool_name}' parameter '{param_name}' value '{value}' not in allowed values: {enum_values}")

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """验证参数类型是否匹配"""
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == 'number':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        else:
            return True  # 未知类型，跳过验证

    # 流式停止管理方法
    def start_streaming_session(self) -> str:
        """启动一个新的流式会话，返回会话ID"""
        session_id = str(uuid.uuid4())
        self._streaming_sessions.add(session_id)
        self._session_stop_flags[session_id] = False
        self.logger.debug(f"Started streaming session: {session_id}")
        return session_id

    def stop_streaming_session(self, session_id: str) -> bool:
        """停止指定的流式会话"""
        if session_id in self._streaming_sessions:
            self._session_stop_flags[session_id] = True
            self.logger.info(f"Stopped streaming session: {session_id}")
            return True
        return False

    def stop_all_streaming(self) -> None:
        """停止所有流式输出"""
        self._stop_streaming = True
        # 同时停止所有活跃会话
        for session_id in self._streaming_sessions:
            self._session_stop_flags[session_id] = True
        self.logger.info("Stopped all streaming sessions")

    def resume_streaming(self) -> None:
        """恢复流式输出（清除全局停止标志）"""
        self._stop_streaming = False
        self.logger.info("Resumed streaming")

    def is_streaming_stopped(self, session_id: str = None) -> bool:
        """检查流式输出是否应该停止"""
        # 检查全局停止标志
        if self._stop_streaming:
            return True

        # 检查特定会话停止标志
        if session_id and session_id in self._session_stop_flags:
            return self._session_stop_flags[session_id]

        return False

    def cleanup_streaming_session(self, session_id: str) -> None:
        """清理流式会话"""
        self._streaming_sessions.discard(session_id)
        self._session_stop_flags.pop(session_id, None)
        self.logger.debug(f"Cleaned up streaming session: {session_id}")

    def get_active_streaming_sessions(self) -> List[str]:
        """获取所有活跃的流式会话ID"""
        return list(self._streaming_sessions)

    async def handle_tool_call_stream(self, tool_name: str, arguments: Dict[str, Any], session_id: str = None) -> \
    AsyncGenerator[str, None]:
        """
        统一的流式工具调用处理器
        所有工具都通过此方法输出流式数据
        """
        # 如果没有提供session_id，自动创建一个
        if session_id is None:
            session_id = self.start_streaming_session()

        try:
            # 尝试调用子类的流式实现
            has_streaming_impl = hasattr(self, '_stream_handlers') and tool_name in getattr(self, '_stream_handlers',
                                                                                            {})

            if has_streaming_impl:
                # 使用子类的流式实现
                async for chunk in self._handle_streaming_tool_call(tool_name, arguments, session_id):
                    # 检查是否应该停止
                    if self.is_streaming_stopped(session_id):
                        self.logger.info(f"Streaming stopped for session {session_id}")
                        break
                    yield chunk
            else:
                # 普通工具：先调用普通方法，然后自动分割为流式输出
                result = await self.handle_tool_call(tool_name, arguments)
                async for chunk in self._auto_chunk_result(result, tool_name, session_id):
                    # 检查是否应该停止
                    if self.is_streaming_stopped(session_id):
                        self.logger.info(f"Streaming stopped for session {session_id}")
                        break
                    yield chunk
        finally:
            # 清理会话
            if session_id:
                self.cleanup_streaming_session(session_id)

    async def _handle_streaming_tool_call(self, tool_name: str, arguments: Dict[str, Any], session_id: str = None) -> \
    AsyncGenerator[str, None]:
        """
        处理真正支持流式输出的工具调用，子类应该重写此方法
        """
        # 默认回退到普通调用 + 自动分割
        result = await self.handle_tool_call(tool_name, arguments)
        async for chunk in self._auto_chunk_result(result, tool_name, session_id):
            yield chunk

    async def _auto_chunk_result(self, result: Any, tool_name: str, session_id: str = None) -> AsyncGenerator[
        str, None]:
        """
        自动将结果分割为流式块
        """
        # 获取工具的分割大小设置
        tool = next((t for t in self.tools if t['name'] == tool_name), None)
        chunk_size = tool.get('chunk_size', 100) if tool else 100

        # 转换结果为字符串
        result_str = str(result)

        # 如果结果很短，直接输出
        if len(result_str) <= chunk_size:
            yield result_str
            return

        # 分割长文本
        self.logger.debug(
            f"Auto-chunking result for {tool_name}: {len(result_str)} chars into {chunk_size}-char chunks")

        # 按行分割优先，避免破坏句子结构
        lines = result_str.split('\n')
        current_chunk = ""

        for line in lines:
            # 如果当前行加上已有内容超过块大小
            if len(current_chunk) + len(line) + 1 > chunk_size and current_chunk:
                # 输出当前块
                yield current_chunk
                await asyncio.sleep(0.05)  # 添加小延迟模拟流式效果
                current_chunk = line
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line

        # 输出最后的块
        if current_chunk:
            yield current_chunk

    def _normalize_stream_chunk(self, chunk: Any) -> str:
        """
        标准化流式数据块的格式
        这是一个通用的chunk处理逻辑，可以被子类复用
        """
        import json

        # 添加调试日志
        self.logger.debug(f"_normalize_stream_chunk received: {type(chunk)} - {chunk}")

        # 如果chunk是字典类型，保持其结构化格式
        if isinstance(chunk, dict):
            result = json.dumps(chunk, ensure_ascii=False)
            self.logger.debug(f"_normalize_stream_chunk returning dict as JSON: {result}")
            return result

        # 确保chunk是字符串格式，不是JSON
        if isinstance(chunk, str) and not chunk.startswith('{'):
            self.logger.debug(f"_normalize_stream_chunk returning plain string: {chunk}")
            return chunk
        else:
            # 如果是JSON格式，尝试解析并提取内容
            try:
                data = json.loads(chunk) if isinstance(chunk, str) else chunk
                if isinstance(data, dict) and 'content' in data:
                    result = data['content']
                    self.logger.debug(f"_normalize_stream_chunk extracted content: {result}")
                    return result
                elif isinstance(data, dict) and 'data' in data:
                    result = str(data['data'])
                    self.logger.debug(f"_normalize_stream_chunk extracted data: {result}")
                    return result
                elif isinstance(data, dict) and 'ai_stream_chunk' in data:
                    result = str(data['ai_stream_chunk'])
                    self.logger.debug(f"_normalize_stream_chunk extracted ai_stream_chunk: {result}")
                    return result
                else:
                    result = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(chunk)
                    self.logger.debug(f"_normalize_stream_chunk fallback: {result}")
                    return result
            except Exception as e:
                result = str(chunk)
                self.logger.debug(f"_normalize_stream_chunk exception {e}, returning: {result}")
                return result

    async def _handle_stream_error(self, tool_name: str, error: Exception) -> str:
        """
        处理流式调用中的错误，返回标准化的错误信息
        子类可以重写此方法来自定义错误处理
        """
        import json
        import logging

        logger = logging.getLogger(self.__class__.__name__)
        logger.error(f"流式工具调用失败 {tool_name}: {error}")

        return json.dumps({
            "error": f"流式工具调用失败: {str(error)}"
        }, ensure_ascii=False)

    def tool_supports_streaming(self, tool_name: str) -> bool:
        """所有工具都支持流式输出（统一架构）"""
        return True

    def configure_server(self, config: Dict[str, Any]) -> bool:
        """配置服务器参数"""
        try:
            # 保存旧配置用于回调通知
            old_config = self.server_config.copy()
            
            # 保存完整的配置数据
            self.full_config = config.copy()
            
            # 验证配置参数
            parameters = self.get_server_parameters()
            param_dict = {p.name: p for p in parameters}

            # 更新server_config中的标准参数
            for key, value in config.items():
                if key in param_dict:
                    param = param_dict[key]
                    # 基本类型验证
                    if param.param_type == 'integer' and not isinstance(value, int):
                        try:
                            value = int(value)
                        except ValueError:
                            self.logger.error(f"Invalid integer value for {key}: {value}")
                            return False
                    elif param.param_type == 'boolean' and not isinstance(value, bool):
                        value = str(value).lower() in ('true', '1', 'yes', 'on')

                    self.server_config[key] = value

            # 检查必需参数
            for param in parameters:
                if param.required and param.name not in self.server_config:
                    if param.default_value is not None:
                        self.server_config[param.name] = param.default_value
                    else:
                        self.logger.error(f"Required parameter missing: {param.name}")
                        return False

            # 保存完整的配置字典（包含自定义字段），而不是只保存server_config
            if self.server_config_manager.save_server_config(config):
                self.logger.info(f"Server configured and saved: {config}")
                
                # 通知配置更新回调
                self._notify_config_update(old_config, self.server_config.copy())
                
                return True
            else:
                self.logger.error("Failed to save server configuration")
                return False

        except Exception as e:
            self.logger.error(f"Failed to configure server: {e}")
            return False

    def get_config_value(self, key: str, default=None):
        """获取配置值
        
        支持以下几种访问方式：
        1. 直接访问标准参数：get_config_value('project_root')
        2. 访问嵌套字段：get_config_value('custom_params.max_file_size')
        3. 访问顶级自定义字段：get_config_value('user_settings')
        4. 自动搜索所有嵌套对象：get_config_value('project_root') 会自动查找 custom_params.project_root
        """
        # 首先检查标准参数
        if key in self.server_config:
            return self.server_config[key]
        
        # 然后检查完整配置中的顶级字段
        if key in self.full_config:
            return self.full_config[key]
        
        # 支持点号分隔的嵌套访问（保持向后兼容）
        if '.' in key:
            keys = key.split('.')
            value = self.full_config
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass
        else:
            # 如果是简单键名，自动搜索所有嵌套对象
            found_value = self._search_nested_config(self.full_config, key)
            if found_value is not None:
                return found_value
        
        return default
    
    def _search_nested_config(self, config_dict: Dict[str, Any], target_key: str) -> Any:
        """递归搜索嵌套配置中的指定键
        
        Args:
            config_dict: 要搜索的配置字典
            target_key: 目标键名
            
        Returns:
            找到的值，如果没找到返回 None
        """
        if not isinstance(config_dict, dict):
            return None
            
        # 遍历当前层级的所有键值对
        for key, value in config_dict.items():
            # 如果当前值是字典，递归搜索
            if isinstance(value, dict):
                # 首先检查这个嵌套字典中是否直接包含目标键
                if target_key in value:
                    return value[target_key]
                
                # 如果没有直接找到，继续递归搜索更深层级
                nested_result = self._search_nested_config(value, target_key)
                if nested_result is not None:
                    return nested_result
        
        return None

    def register_config_update_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        """注册配置更新回调函数
        
        Args:
            callback: 回调函数，接收两个参数：(old_config, new_config)
        """
        if callback not in self._config_update_callbacks:
            self._config_update_callbacks.append(callback)
            self.logger.info(f"Registered config update callback: {callback.__name__}")

    def unregister_config_update_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        """取消注册配置更新回调函数"""
        if callback in self._config_update_callbacks:
            self._config_update_callbacks.remove(callback)
            self.logger.info(f"Unregistered config update callback: {callback.__name__}")
    
    def set_openai_format_enabled(self, enabled: bool) -> None:
        """设置是否启用OpenAI格式的流式返回"""
        self._enable_openai_format = enabled
        self.logger.info(f"OpenAI format streaming {'enabled' if enabled else 'disabled'}")
    
    def is_openai_format_enabled(self) -> bool:
        """检查是否启用了OpenAI格式的流式返回"""
        return self._enable_openai_format
    
    async def handle_tool_call_stream_openai(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        session_id: str = None
    ) -> AsyncGenerator[str, None]:
        """处理工具调用并返回OpenAI格式的流式数据
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            session_id: 会话ID，如果为None则自动创建
            
        Yields:
            OpenAI格式的SSE数据字符串
        """
        if not self._enable_openai_format:
            # 如果未启用OpenAI格式，回退到原始流式处理
            async for chunk in self.handle_tool_call_stream(tool_name, arguments, session_id):
                yield chunk
            return
        
        # 如果没有提供session_id，自动创建一个
        if session_id is None:
            session_id = self.start_streaming_session()
        
        try:
            # 获取原始流式生成器
            original_stream = self.handle_tool_call_stream(tool_name, arguments, session_id)
            
            # 使用OpenAI格式包装器包装流式输出
            async for openai_chunk in self._openai_stream_wrapper.wrap_tool_call_stream(
                tool_name, arguments, original_stream, session_id
            ):
                # 检查是否应该停止
                if self.is_streaming_stopped(session_id):
                    self.logger.info(f"OpenAI streaming stopped for session {session_id}")
                    break
                yield openai_chunk
                
        except Exception as e:
            self.logger.error(f"Error in OpenAI streaming for tool {tool_name}: {e}")
            # 发送错误格式的OpenAI响应
            formatter = OpenAIStreamFormatter(self._openai_stream_wrapper.model_name, session_id)
            error_chunk = formatter.create_error_chunk(str(e))
            yield error_chunk.to_sse_data()
        finally:
            # 清理会话
            if session_id:
                self.cleanup_streaming_session(session_id)
    
    async def handle_simple_response_openai(
        self, 
        content: Any, 
        session_id: str = None
    ) -> AsyncGenerator[str, None]:
        """将简单响应包装为OpenAI格式的流式输出
        
        Args:
            content: 响应内容
            session_id: 会话ID
            
        Yields:
            OpenAI格式的SSE数据字符串
        """
        if not self._enable_openai_format:
            # 如果未启用OpenAI格式，直接返回内容
            yield str(content)
            return
        
        try:
            async for openai_chunk in self._openai_stream_wrapper.wrap_simple_response(content, session_id):
                yield openai_chunk
        except Exception as e:
            self.logger.error(f"Error in OpenAI simple response streaming: {e}")
            formatter = OpenAIStreamFormatter(self._openai_stream_wrapper.model_name, session_id)
            error_chunk = formatter.create_error_chunk(str(e))
            yield error_chunk.to_sse_data()

    def _notify_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """通知所有注册的回调函数配置已更新"""
        for callback in self._config_update_callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                self.logger.error(f"Error in config update callback {callback.__name__}: {e}")

    def add_tool(self, tool: dict) -> None:
        """添加工具（去重：同名工具将被替换而不是重复添加）"""
        for idx, existing in enumerate(self.tools):
            if existing.get('name') == tool.get('name'):
                self.tools[idx] = tool
                self.logger.info(f"Replaced existing tool: {tool.get('name')}")
                break
        else:
            self.tools.append(tool)
            self.logger.info(f"Added tool: {tool.get('name')}")

    def add_resource(self, resource: dict) -> None:
        """添加资源（去重：同 URI 的资源将被替换而不是重复添加）"""
        for idx, existing in enumerate(self.resources):
            # 以 URI 作为资源的唯一标识；若缺失则退化到名称判定
            if existing.get('uri') == resource.get('uri') or (
                    existing.get('uri') is None and existing.get('name') == resource.get('name')
            ):
                self.resources[idx] = resource
                self.logger.info(f"Replaced existing resource: {resource.get('uri') or resource.get('name')}")
                break
        else:
            self.resources.append(resource)
            self.logger.info(f"Added resource: {resource.get('name')}")

    def _log_config_info(self, config: Dict[str, Any], sensitive_keys: List[str] = None) -> None:
        """记录配置信息日志"""
        if sensitive_keys is None:
            sensitive_keys = ['api_key', 'password', 'token', 'secret']

        # 记录基本配置信息
        config_items = []
        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                config_items.append(f"{key}={'已设置' if value else '未设置'}")
            elif isinstance(value, str) and len(value) > 100:
                config_items.append(f"{key}={value[:100]}...")
            else:
                config_items.append(f"{key}={value}")

        if config_items:
            self.logger.info(f"🔧 配置信息: {', '.join(config_items)}")

    def _log_tools_info(self) -> None:
        """记录工具信息日志"""
        if self.tools:
            self.logger.info(f"🛠️ 初始化工具列表 (共{len(self.tools)}个，全部支持流式输出):")
            for tool in self.tools:
                chunk_info = f" (分块大小: {tool.get('chunk_size', 100)})" if 'chunk_size' in tool else ""
                self.logger.info(
                    f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}{chunk_info}")

    def _validate_required_config(self, required_keys: List[str]) -> None:
        """验证必需的配置项"""
        missing_keys = []
        for key in required_keys:
            value = self.server_config.get(key)
            if not value:
                missing_keys.append(key)

        if missing_keys:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_keys)}")

    def _get_config_with_defaults(self, config_defaults: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置值，如果不存在则使用默认值"""
        result = {}
        for key, default_value in config_defaults.items():
            result[key] = self.server_config.get(key, default_value)
        return result

    def _setup_decorators_and_log_config(self, required_keys: List[str] = None,
                                         config_defaults: Dict[str, Any] = None,
                                         log_config: bool = True) -> Dict[str, Any]:
        """通用的装饰器设置和配置处理流程"""
        # 触发装饰器注册（如果是 EnhancedMCPServer）
        if hasattr(self, 'setup_tools'):
            _ = self.setup_tools
        if hasattr(self, 'setup_server_params'):
            _ = self.setup_server_params

        # 验证必需配置
        if required_keys:
            self._validate_required_config(required_keys)

        # 获取配置值
        config_values = {}
        if config_defaults:
            config_values = self._get_config_with_defaults(config_defaults)

        # 记录配置信息
        if log_config and config_values:
            self._log_config_info(config_values)

        return config_values

    async def startup(self) -> None:
        """服务器启动时调用"""
        if not self._initialized:
            # 检查是否有外部设置的配置管理器，如果有则重新加载配置
            if hasattr(self, 'server_config_manager') and self.server_config_manager is not None:
                try:
                    print(f"🔍 检查外部配置管理器: {self.server_config_manager.config_file}")
                    if self.server_config_manager.config_exists():
                        config = self.server_config_manager.load_server_config()
                        print(f"📂 加载的配置内容: {config}")
                        result = self.configure_server(config)
                        print(f"⚙️ 配置应用结果: {result}")
                        self.logger.info(f"Reloaded configuration from external config manager: {self.server_config_manager.config_file}")
                    else:
                        print(f"❌ 配置文件不存在: {self.server_config_manager.config_file}")
                except Exception as e:
                    print(f"❌ 配置加载失败: {e}")
                    self.logger.warning(f"Failed to reload config from external config manager: {e}")
            
            await self.initialize()
            self._initialized = True
            self.logger.info(
                f"MCP Server '{self.name}' initialized with {len(self.tools)} tools and {len(self.resources)} resources")

    async def shutdown(self) -> None:
        """服务器关闭时调用"""
        if self._initialized:
            # 清理资源
            self.tools.clear()
            self.resources.clear()
            self._initialized = False
            self.logger.info(f"MCP Server '{self.name}' shutdown completed")


# EnhancedMCPTool类已被删除，因为MCPTool基类已被删除


class EnhancedMCPServer(BaseMCPServer):
    """增强版MCP服务器，支持装饰器和自动工具分发"""

    def __init__(self, name: str, version: str = "1.0.0", description: str = "", config_manager=None):
        super().__init__(name, version, description)
        self._tool_handlers: Dict[str, Callable] = {}
        self._stream_handlers: Dict[str, Callable] = {}
        self._resource_handlers: Dict[str, Callable] = {}

        # 创建装饰器实例
        from .decorators import AnnotatedDecorators
        self.decorators = AnnotatedDecorators(self)
        
        # 如果提供了配置管理器，使用它；否则自动加载配置
        if config_manager:
            self.server_config_manager = config_manager
            # 尝试加载配置
            config = self.server_config_manager.load_server_config()
            if config:
                self.configure_server(config)
                self.logger.info(f"Loaded configuration from provided config manager for server '{self.name}'")
            else:
                self._apply_default_config()
                self.logger.info(f"Applied default configuration for server '{self.name}' (no config file found)")
        else:
            # 自动加载配置
            self._auto_load_config()

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any],
                      handler: Callable, chunk_size: int = 100,
                      stream_handler: Optional[Callable] = None) -> None:
        """注册工具并绑定处理函数"""
        tool = {
            'name': name,
            'description': description,
            'input_schema': input_schema,
            'chunk_size': chunk_size,
            'handler': handler,
            'stream_handler': stream_handler
        }

        self.add_tool(tool)
        self._tool_handlers[name] = handler
        if stream_handler:
            self._stream_handlers[name] = stream_handler

    def register_resource(self, uri: str, name: str, description: str,
                          handler: Callable, mime_type: str = 'text/plain') -> None:
        """注册资源并绑定处理函数"""
        resource = {
            'uri': uri,
            'name': name,
            'description': description,
            'mime_type': mime_type
        }

        self.add_resource(resource)
        self._resource_handlers[uri] = handler

    async def initialize(self) -> None:
        """初始化服务器"""
        # 触发装饰器注册（通过访问setup_tools属性）
        if hasattr(self, 'setup_tools'):
            _ = self.setup_tools
        self.logger.info(f"EnhancedMCPServer '{self.name}' initialized")

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """自动分发工具调用到注册的处理函数"""
        # 首先检查普通工具处理器
        if tool_name in self._tool_handlers:
            handler = self._tool_handlers[tool_name]
        # 如果不在普通处理器中，检查流式处理器（支持流式工具的非流式调用）
        elif tool_name in self._stream_handlers:
            handler = self._stream_handlers[tool_name]
        else:
            raise ValueError(f"Tool '{tool_name}' not found")

        # 如果是流式处理器，需要收集所有输出
        if tool_name in self._stream_handlers and tool_name not in self._tool_handlers:
            try:
                # 获取工具的input_schema进行参数验证
                tool = next((t for t in self.tools if t['name'] == tool_name), None)
                if tool and tool.get('input_schema'):
                    self._validate_arguments(tool_name, arguments, tool['input_schema'])

                # 检查处理函数的签名
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())

                # 调用流式处理器并收集所有输出
                result_chunks = []
                if params and params[0] == 'self':
                    async_gen = handler(**arguments)
                else:
                    async_gen = handler(**arguments)

                async for chunk in async_gen:
                    result_chunks.append(str(chunk))

                # 返回合并后的结果
                return ''.join(result_chunks)
            except Exception as e:
                self.logger.error(f"Tool call failed for '{tool_name}': {e}")
                raise

        try:
            # 获取工具的input_schema进行参数验证
            tool = next((t for t in self.tools if t['name'] == tool_name), None)
            if tool and tool.get('input_schema'):
                self._validate_arguments(tool_name, arguments, tool['input_schema'])

            # 检查处理函数的签名
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())

            # 如果是实例方法，跳过self参数
            if params and params[0] == 'self':
                if inspect.iscoroutinefunction(handler):
                    return await handler(**arguments)
                else:
                    return handler(**arguments)
            else:
                # 静态函数或普通函数
                if inspect.iscoroutinefunction(handler):
                    return await handler(**arguments)
                else:
                    return handler(**arguments)
        except Exception as e:
            self.logger.error(f"Tool call failed for '{tool_name}': {e}")
            raise

    async def handle_tool_call_stream(self, tool_name: str, arguments: Dict[str, Any], session_id: str = None) -> \
    AsyncGenerator[str, None]:
        """自动分发流式工具调用"""
        if tool_name in self._stream_handlers:
            handler = self._stream_handlers[tool_name]
            try:
                # 获取工具的input_schema进行参数验证
                tool = next((t for t in self.tools if t['name'] == tool_name), None)
                if tool and tool.get('input_schema'):
                    self._validate_arguments(tool_name, arguments, tool['input_schema'])

                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())

                if params and params[0] == 'self':
                    # 调用handler获取async generator
                    async_gen = handler(**arguments)
                    self.logger.debug(f"Stream handler returned: {type(async_gen)}")
                    async for chunk in async_gen:
                        self.logger.debug(f"Stream handler yielded chunk: {type(chunk)} - {chunk}")
                        yield self._normalize_stream_chunk(chunk)
                else:
                    # 调用handler获取async generator
                    async_gen = handler(**arguments)
                    self.logger.debug(f"Stream handler returned: {type(async_gen)}")
                    async for chunk in async_gen:
                        self.logger.debug(f"Stream handler yielded chunk: {type(chunk)} - {chunk}")
                        yield self._normalize_stream_chunk(chunk)
            except Exception as e:
                self.logger.error(f"Stream tool call failed for '{tool_name}': {e}")
                yield await self._handle_stream_error(tool_name, e)
        else:
            # 回退到普通调用
            async for chunk in super().handle_tool_call_stream(tool_name, arguments, session_id):
                yield chunk

    async def handle_resource_request(self, uri: str) -> Dict[str, Any]:
        """自动分发资源请求"""
        if uri not in self._resource_handlers:
            raise NotImplementedError(f"Resource not found: {uri}")

        handler = self._resource_handlers[uri]

        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())

            if params and params[0] == 'self':
                if inspect.iscoroutinefunction(handler):
                    return await handler(uri)
                else:
                    return handler(uri)
            else:
                if inspect.iscoroutinefunction(handler):
                    return await handler(uri)
                else:
                    return handler(uri)
        except Exception as e:
            self.logger.error(f"Resource request failed for '{uri}': {e}")
            raise

    def get_server_parameters(self) -> List[ServerParameter]:
        """获取服务器参数定义，支持装饰器配置"""
        # 触发装饰器注册（如果有 setup_tools 或 setup_server_params 属性）
        if hasattr(self, 'setup_tools'):
            _ = self.setup_tools
        if hasattr(self, 'setup_server_params'):
            _ = self.setup_server_params
        
        # 合并装饰器配置的参数和子类定义的参数
        # 检查 decorators 是否已初始化
        decorator_params = []
        if hasattr(self, 'decorators') and self.decorators is not None:
            decorator_params = self.decorators.get_server_parameters() or []

        # 如果子类重写了此方法，也获取其参数
        subclass_params = []
        if hasattr(super(), 'get_server_parameters'):
            try:
                subclass_params = super().get_server_parameters() or []
            except (NotImplementedError, AttributeError):
                pass

        # 合并参数，装饰器参数优先
        all_params = decorator_params + subclass_params

        # 去重（基于参数名）
        seen_names = set()
        unique_params = []
        for param in all_params:
            if param.name not in seen_names:
                unique_params.append(param)
                seen_names.add(param.name)

        return unique_params

    # 提供装饰器直接访问
    def tool(self, description: str = None, chunk_size: int = 100, role = None):
        """工具装饰器"""
        return self.decorators.tool(description=description, chunk_size=chunk_size, role=role)

    def streaming_tool(self, description: str = None, chunk_size: int = 50, role = None):
        """流式工具装饰器"""
        return self.decorators.streaming_tool(description=description, chunk_size=chunk_size, role=role)

    def resource(self, uri: str, name: str = None, description: str = None, mime_type: str = 'text/plain'):
        """资源装饰器"""
        return self.decorators.resource(uri=uri, name=name, description=description, mime_type=mime_type)
    
    def _auto_load_config(self):
        """自动加载配置"""
        try:
            # 创建配置管理器
            if not self.server_config_manager:
                self.server_config_manager = ServerConfigManager(self.name)
            
            # 尝试加载现有配置
            config = self.server_config_manager.load_server_config()
            
            if config:
                # 如果有配置文件，使用配置文件的值
                self.configure_server(config)
                self.logger.info(f"Loaded configuration from file for server '{self.name}'")
            else:
                # 如果没有配置文件，使用服务器参数的默认值
                self._apply_default_config()
                self.logger.info(f"Applied default configuration for server '{self.name}'")
                
        except Exception as e:
            self.logger.warning(f"Failed to auto-load config for server '{self.name}': {e}")
            # 即使加载失败，也尝试应用默认配置
            self._apply_default_config()
    
    def _apply_default_config(self):
        """应用服务器参数的默认值"""
        try:
            # 获取服务器参数定义
            parameters = self.get_server_parameters()
            
            # 构建默认配置
            custom_params = {}
            for param in parameters:
                if param.default_value is not None:
                    custom_params[param.name] = param.default_value
            
            if custom_params:
                # 构建完整的配置结构，包含custom_params
                default_config = {
                    "custom_params": custom_params
                }
                
                # 应用默认配置
                result = self.configure_server(default_config)
                if result:
                    self.logger.info(f"Applied and saved default values for {len(custom_params)} parameters")
                else:
                    self.logger.warning("Failed to save default configuration")
            else:
                self.logger.info("No default values to apply")
                
        except Exception as e:
            self.logger.error(f"Failed to apply default config: {e}")

    def server_param(self, name: str):
        """服务器参数装饰器"""
        return self.decorators.server_param(name=name)
