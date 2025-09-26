#!/usr/bin/env python3
"""
OpenAI 格式的流式返回数据结构和包装器
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass, asdict
from enum import Enum


class StreamEventType(Enum):
    """流式事件类型"""
    CHUNK = "chunk"
    START = "start"
    END = "end"
    ERROR = "error"
    FUNCTION_CALL = "function_call"
    TOOL_CALL = "tool_call"


@dataclass
class OpenAIChoice:
    """OpenAI 格式的选择项"""
    index: int = 0
    delta: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


@dataclass
class OpenAIUsage:
    """OpenAI 格式的使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class OpenAIStreamChunk:
    """OpenAI 格式的流式数据块"""
    id: str
    object: str = "chat.completion.chunk"
    created: int = None
    model: str = "mcp-server"
    choices: list = None
    usage: Optional[OpenAIUsage] = None
    
    def __post_init__(self):
        if self.created is None:
            self.created = int(time.time())
        if self.choices is None:
            self.choices = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}

    def to_sse_data(self) -> str:
        """转换为SSE数据格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


class OpenAIStreamFormatter:
    """OpenAI 格式的流式数据格式化器"""
    
    def __init__(self, model_name: str = "mcp-server", session_id: Optional[str] = None):
        self.model_name = model_name
        self.session_id = session_id or str(uuid.uuid4())
        self.completion_tokens = 0
        
    def create_start_chunk(self, tool_name: str, arguments: Dict[str, Any]) -> OpenAIStreamChunk:
        """创建开始块"""
        return OpenAIStreamChunk(
            id=f"chatcmpl-{self.session_id}",
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    delta={
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": f"call_{tool_name}_{int(time.time())}",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments, ensure_ascii=False)
                            }
                        }]
                    },
                    finish_reason=None
                )
            ]
        )
    
    def create_content_chunk(self, content: str) -> OpenAIStreamChunk:
        """创建内容块"""
        self.completion_tokens += len(content.split())
        return OpenAIStreamChunk(
            id=f"chatcmpl-{self.session_id}",
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    delta={"content": content},
                    finish_reason=None
                )
            ]
        )
    
    def create_function_call_chunk(self, function_name: str, arguments: str) -> OpenAIStreamChunk:
        """创建函数调用块"""
        return OpenAIStreamChunk(
            id=f"chatcmpl-{self.session_id}",
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    delta={
                        "function_call": {
                            "name": function_name,
                            "arguments": arguments
                        }
                    },
                    finish_reason=None
                )
            ]
        )
    
    def create_end_chunk(self, finish_reason: str = "stop") -> OpenAIStreamChunk:
        """创建结束块"""
        return OpenAIStreamChunk(
            id=f"chatcmpl-{self.session_id}",
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    delta={},
                    finish_reason=finish_reason
                )
            ],
            usage=OpenAIUsage(
                completion_tokens=self.completion_tokens,
                total_tokens=self.completion_tokens
            )
        )
    
    def create_error_chunk(self, error_message: str, error_code: str = "internal_error") -> OpenAIStreamChunk:
        """创建错误块"""
        return OpenAIStreamChunk(
            id=f"chatcmpl-{self.session_id}",
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    delta={
                        "content": f"Error: {error_message}"
                    },
                    finish_reason="error"
                )
            ]
        )


class MCPStreamWrapper:
    """MCP 流式数据包装器，将MCP服务器的输出包装成OpenAI格式"""
    
    def __init__(self, model_name: str = "mcp-server"):
        self.model_name = model_name
    
    async def wrap_tool_call_stream(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        stream_generator: AsyncGenerator[str, None],
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """包装工具调用的流式输出为OpenAI格式"""
        formatter = OpenAIStreamFormatter(self.model_name, session_id)
        
        # 发送开始块
        start_chunk = formatter.create_start_chunk(tool_name, arguments)
        yield start_chunk.to_sse_data()
        
        try:
            # 处理流式内容
            async for chunk in stream_generator:
                if isinstance(chunk, str):
                    # 尝试解析为JSON
                    try:
                        chunk_data = json.loads(chunk)
                        # 如果是结构化数据，转换为内容
                        if isinstance(chunk_data, dict):
                            content = json.dumps(chunk_data, ensure_ascii=False)
                        else:
                            content = str(chunk_data)
                    except json.JSONDecodeError:
                        # 纯文本内容
                        content = chunk
                else:
                    # 非字符串类型，转换为JSON字符串
                    content = json.dumps(chunk, ensure_ascii=False)
                
                # 创建内容块
                content_chunk = formatter.create_content_chunk(content)
                yield content_chunk.to_sse_data()
            
            # 发送结束块
            end_chunk = formatter.create_end_chunk()
            yield end_chunk.to_sse_data()
            
        except Exception as e:
            # 发送错误块
            error_chunk = formatter.create_error_chunk(str(e))
            yield error_chunk.to_sse_data()
    
    async def wrap_simple_response(
        self, 
        content: Union[str, Dict[str, Any]], 
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """包装简单响应为OpenAI格式的流式输出"""
        formatter = OpenAIStreamFormatter(self.model_name, session_id)
        
        # 转换内容为字符串
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = str(content)
        
        # 发送内容块
        content_chunk = formatter.create_content_chunk(content_str)
        yield content_chunk.to_sse_data()
        
        # 发送结束块
        end_chunk = formatter.create_end_chunk()
        yield end_chunk.to_sse_data()


def create_openai_sse_response(data: Dict[str, Any]) -> str:
    """创建OpenAI格式的SSE响应"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_done_sse_response() -> str:
    """创建SSE结束响应"""
    return "data: [DONE]\n\n"