#!/usr/bin/env python3
"""
MCP 框架装饰器系统
支持类型注解的参数定义
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, get_origin, get_args
from functools import wraps

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated


# MCPTool和MCPResource类已被删除


@dataclass
class ParamSpec:
    """参数规范定义"""
    description: str
    required: bool = True
    default: Any = None
    type_name: str = "string"
    enum: Optional[List[Any]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None
    example: Optional[Any] = None


# 快捷函数
def Required(description: str, **kwargs) -> ParamSpec:
    """必填参数"""
    return ParamSpec(description=description, required=True, **kwargs)


def Optional(description: str, default: Any = None, type_name: str = None, **kwargs) -> ParamSpec:
    """可选参数"""
    return ParamSpec(description=description, required=False, default=default, type_name=type_name, **kwargs)


def Enum(description: str, values: List[Any], required: bool = True, **kwargs) -> ParamSpec:
    """枚举参数"""
    return ParamSpec(description=description, required=required, enum=values, **kwargs)


def IntRange(description: str, min_val: float = None, max_val: float = None, required: bool = True,
             **kwargs) -> ParamSpec:
    """整数范围参数"""
    return ParamSpec(description=description, required=required, type_name="integer", minimum=min_val, maximum=max_val,
                     **kwargs)


def FloatRange(description: str, min_val: float = None, max_val: float = None, required: bool = True,
               **kwargs) -> ParamSpec:
    """浮点数范围参数"""
    return ParamSpec(description=description, required=required, type_name="number", minimum=min_val, maximum=max_val,
                     **kwargs)


# 更简洁的语法糖
R = Required  # 必填
O = Optional  # 可选
E = Enum  # 枚举


# 类型快捷方式
def Str(description: str, required: bool = True, **kwargs) -> ParamSpec:
    return ParamSpec(description=description, required=required, type_name="string", **kwargs)


def Int(description: str, required: bool = True, **kwargs) -> ParamSpec:
    return ParamSpec(description=description, required=required, type_name="integer", **kwargs)


def Bool(description: str, required: bool = True, **kwargs) -> ParamSpec:
    return ParamSpec(description=description, required=required, type_name="boolean", **kwargs)


def Float(description: str, required: bool = True, **kwargs) -> ParamSpec:
    return ParamSpec(description=description, required=required, type_name="number", **kwargs)


@dataclass
class ServerParamSpec:
    """服务器参数规范"""
    display_name: str
    description: str
    param_type: str = "string"  # 'string', 'integer', 'boolean', 'select', 'path'
    default_value: Any = None
    required: bool = True
    options: Optional[List[str]] = None  # 用于 select 类型
    placeholder: Optional[str] = None
    validation_pattern: Optional[str] = None


# 服务器参数装饰器快捷函数
def ServerParam(display_name: str, description: str, **kwargs) -> ServerParamSpec:
    """服务器参数"""
    return ServerParamSpec(display_name=display_name, description=description, **kwargs)


def StringParam(display_name: str, description: str, **kwargs) -> ServerParamSpec:
    """字符串参数"""
    return ServerParamSpec(display_name=display_name, description=description, param_type="string", **kwargs)


def SelectParam(display_name: str, description: str, options: List[str], **kwargs) -> ServerParamSpec:
    """选择参数"""
    return ServerParamSpec(display_name=display_name, description=description, param_type="select", options=options,
                           **kwargs)


def BooleanParam(display_name: str, description: str, **kwargs) -> ServerParamSpec:
    """布尔参数"""
    return ServerParamSpec(display_name=display_name, description=description, param_type="boolean", **kwargs)


def PathParam(display_name: str, description: str, **kwargs) -> ServerParamSpec:
    """路径参数"""
    return ServerParamSpec(display_name=display_name, description=description, param_type="path", **kwargs)


class AnnotatedDecorators:
    """基于类型注解的装饰器类"""

    def __init__(self, server):
        self.server = server
        self.registered_tools = {}
        self.registered_resources = {}
        self.server_parameters = []

    def tool(self, description: str = None, chunk_size: int = 100, role: Union[str, List[str]] = None):
        """工具装饰器（统一流式架构）"""

        def decorator(func):
            tool_name = func.__name__
            tool_description = description or func.__doc__ or f"Tool: {tool_name}"

            # 解析函数签名生成 input_schema
            input_schema = self._parse_annotated_schema(func)

            # 注册工具（MCPTool类已被删除）
            self.registered_tools[tool_name] = func

            # 创建工具字典并添加到服务器
            tool_dict = {
                'name': tool_name,
                'description': tool_description,
                'input_schema': input_schema,
                'chunk_size': chunk_size
            }
            
            # 添加role信息（如果提供）
            if role is not None:
                # 支持单个角色或角色数组
                if isinstance(role, str):
                    tool_dict['roles'] = [role]
                elif isinstance(role, list):
                    tool_dict['roles'] = role
                else:
                    raise ValueError(f"role参数必须是字符串或字符串列表，得到: {type(role)}")
                # 保持向后兼容性
                tool_dict['role'] = role if isinstance(role, str) else role[0] if role else None
                
            self.server.add_tool(tool_dict)

            # 如果是EnhancedMCPServer，也注册到_tool_handlers
            if hasattr(self.server, '_tool_handlers'):
                self.server._tool_handlers[tool_name] = func

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def streaming_tool(self, description: str = None, chunk_size: int = 50, role: Union[str, List[str]] = None):
        """流式工具装饰器（注册为真正的流式处理器）"""

        def decorator(func):
            tool_name = func.__name__
            tool_description = description or func.__doc__ or f"Streaming Tool: {tool_name}"

            # 解析函数签名生成 input_schema
            input_schema = self._parse_annotated_schema(func)

            # 注册工具（MCPTool类已被删除）
            self.registered_tools[tool_name] = func

            # 创建工具字典并添加到服务器
            tool_dict = {
                'name': tool_name,
                'description': tool_description,
                'input_schema': input_schema,
                'chunk_size': chunk_size
            }
            
            # 添加role信息（如果提供）
            if role is not None:
                # 支持单个角色或角色数组
                if isinstance(role, str):
                    tool_dict['roles'] = [role]
                elif isinstance(role, list):
                    tool_dict['roles'] = role
                else:
                    raise ValueError(f"role参数必须是字符串或字符串列表，得到: {type(role)}")
                # 保持向后兼容性
                tool_dict['role'] = role if isinstance(role, str) else role[0] if role else None
                
            self.server.add_tool(tool_dict)

            # 如果是EnhancedMCPServer，注册到_stream_handlers（真正的流式处理）
            if hasattr(self.server, '_stream_handlers'):
                self.server._stream_handlers[tool_name] = func

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def resource(self, uri: str, name: str = None, description: str = None, mime_type: str = 'text/plain'):
        """资源装饰器"""

        def decorator(func):
            resource_name = name or func.__name__
            resource_description = description or func.__doc__ or f"Resource: {resource_name}"

            # 注册资源（MCPResource类已被删除）
            self.registered_resources[uri] = func

            # 创建资源字典并添加到服务器
            resource_dict = {
                'uri': uri,
                'name': resource_name,
                'description': resource_description,
                'mime_type': mime_type
            }
            self.server.add_resource(resource_dict)

            # 如果是EnhancedMCPServer，也注册到_resource_handlers
            if hasattr(self.server, '_resource_handlers'):
                self.server._resource_handlers[uri] = func

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def server_param(self, name: str):
        """服务器参数装饰器"""

        def decorator(func):
            # 解析函数签名获取参数规范
            sig = inspect.signature(func)
            param_specs = []

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                param_spec = self._extract_server_param_spec(param, name or param_name)
                if param_spec:
                    param_specs.append(param_spec)

            # 如果没有从参数中提取到规范，尝试从函数注解中提取
            if not param_specs and hasattr(func, '__annotations__'):
                for annotation_name, annotation in func.__annotations__.items():
                    if annotation_name != 'return' and isinstance(annotation, ServerParamSpec):
                        # 创建 ServerParameter
                        from .config import ServerParameter
                        server_param = ServerParameter(
                            name=name or annotation_name,
                            display_name=annotation.display_name,
                            description=annotation.description,
                            param_type=annotation.param_type,
                            default_value=annotation.default_value,
                            required=annotation.required,
                            options=annotation.options,
                            placeholder=annotation.placeholder,
                            validation_pattern=annotation.validation_pattern
                        )
                        self.server_parameters.append(server_param)

            # 如果函数有直接的 ServerParamSpec 注解
            if hasattr(func, '__annotations__'):
                for annotation in func.__annotations__.values():
                    if get_origin(annotation) is Annotated:
                        args = get_args(annotation)
                        for meta in args[1:]:
                            if isinstance(meta, ServerParamSpec):
                                from .config import ServerParameter
                                server_param = ServerParameter(
                                    name=name,
                                    display_name=meta.display_name,
                                    description=meta.description,
                                    param_type=meta.param_type,
                                    default_value=meta.default_value,
                                    required=meta.required,
                                    options=meta.options,
                                    placeholder=meta.placeholder,
                                    validation_pattern=meta.validation_pattern
                                )
                                self.server_parameters.append(server_param)
                                break

            return func

        return decorator

    def _extract_server_param_spec(self, param: inspect.Parameter, param_name: str) -> Optional['ServerParameter']:
        """从参数中提取服务器参数规范"""
        annotation = param.annotation

        # 处理 Annotated 类型
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            metadata = args[1:]

            # 查找 ServerParamSpec
            for meta in metadata:
                if isinstance(meta, ServerParamSpec):
                    from .config import ServerParameter
                    return ServerParameter(
                        name=param_name,
                        display_name=meta.display_name,
                        description=meta.description,
                        param_type=meta.param_type,
                        default_value=meta.default_value if meta.default_value is not None else param.default if param.default != inspect.Parameter.empty else None,
                        required=meta.required,
                        options=meta.options,
                        placeholder=meta.placeholder,
                        validation_pattern=meta.validation_pattern
                    )

        return None

    def get_server_parameters(self) -> List['ServerParameter']:
        """获取所有注册的服务器参数"""
        return self.server_parameters

    def _parse_annotated_schema(self, func) -> Dict[str, Any]:
        """解析带注解的函数签名生成 input_schema"""
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            param_spec = self._extract_param_spec(param)

            # 构建属性定义
            prop_def = {
                "type": param_spec.type_name,
                "description": param_spec.description
            }

            # 添加可选属性
            if param_spec.enum:
                prop_def["enum"] = param_spec.enum
            if param_spec.minimum is not None:
                prop_def["minimum"] = param_spec.minimum
            if param_spec.maximum is not None:
                prop_def["maximum"] = param_spec.maximum
            if param_spec.pattern:
                prop_def["pattern"] = param_spec.pattern
            if param_spec.example is not None:
                prop_def["example"] = param_spec.example
            if param_spec.default is not None:
                prop_def["default"] = param_spec.default

            properties[param_name] = prop_def

            # 判断是否必填
            if param_spec.required:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def _extract_param_spec(self, param: inspect.Parameter) -> ParamSpec:
        """从参数中提取 ParamSpec"""
        annotation = param.annotation

        # 处理 Annotated 类型
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            base_type = args[0]
            metadata = args[1:]

            # 查找 ParamSpec
            for meta in metadata:
                if isinstance(meta, ParamSpec):
                    # 如果函数参数有默认值，则自动设置为非必填
                    if param.default != inspect.Parameter.empty:
                        meta.required = False
                        if meta.default is None:
                            meta.default = param.default

                    # 如果ParamSpec没有指定type_name，从base_type推断
                    if not hasattr(meta, 'type_name') or meta.type_name is None or meta.type_name == "string":
                        inferred_type = self._python_type_to_json_type(base_type)
                        meta.type_name = inferred_type

                    return meta

            # 如果没有找到ParamSpec，从base_type创建一个
            type_name = self._python_type_to_json_type(base_type)
            is_optional = get_origin(base_type) is Union and type(None) in get_args(base_type)

            return ParamSpec(
                description=f"Parameter {param.name}",
                required=not is_optional and param.default == inspect.Parameter.empty,
                type_name=type_name,
                default=param.default if param.default != inspect.Parameter.empty else None
            )

        # 处理普通类型注解
        if annotation != inspect.Parameter.empty:
            type_name = self._python_type_to_json_type(annotation)
            is_optional = get_origin(annotation) is Union and type(None) in get_args(annotation)

            return ParamSpec(
                description=f"Parameter {param.name}",
                required=not is_optional and param.default == inspect.Parameter.empty,
                type_name=type_name,
                default=param.default if param.default != inspect.Parameter.empty else None
            )

        # 无类型注解的情况
        return ParamSpec(
            description=f"Parameter {param.name}",
            required=param.default == inspect.Parameter.empty,
            type_name="string",
            default=param.default if param.default != inspect.Parameter.empty else None
        )

    def _python_type_to_json_type(self, python_type) -> str:
        """将 Python 类型转换为 JSON Schema 类型"""
        # 处理 Union 类型（如 Optional[int]）
        if get_origin(python_type) is Union:
            args = get_args(python_type)
            # 过滤掉 None 类型，获取实际类型
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                python_type = non_none_types[0]  # 使用第一个非None类型

        if python_type == str:
            return "string"
        elif python_type == int:
            return "integer"
        elif python_type == float:
            return "number"
        elif python_type == bool:
            return "boolean"
        elif python_type == list or get_origin(python_type) == list:
            return "array"
        elif python_type == dict or get_origin(python_type) == dict:
            return "object"
        else:
            return "string"  # 默认为字符串