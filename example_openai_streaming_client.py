#!/usr/bin/env python3
"""
OpenAI 格式流式返回客户端示例

这个示例展示了如何调用 MCP 框架的 OpenAI 格式流式返回功能。
包含了同步和异步两种调用方式的示例。
"""

import asyncio
import json
import os
import aiohttp
import requests
from typing import AsyncGenerator, Dict, Any


class OpenAIStreamingClient:
    """OpenAI 格式流式返回客户端"""
    
    def __init__(self, base_url: str = None):
        # 支持环境变量配置，默认使用8080端口
        if base_url is None:
            port = os.getenv('MCP_SERVER_PORT', '8080')
            host = os.getenv('MCP_SERVER_HOST', 'localhost')
            base_url = f"http://{host}:{port}"
        self.base_url = base_url.rstrip('/')
        self.sse_endpoint = f"{self.base_url}/sse/openai/tool/call"
    
    def call_tool_sync(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """同步调用工具（非流式）"""
        url = f"{self.base_url}/tool/call"
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json().get("result", "")
    
    def call_tool_stream_sync(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """同步调用工具（流式，阻塞直到完成）"""
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        response = requests.post(
            self.sse_endpoint,
            json=payload,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        
        full_content = ""
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data_str = line[6:]  # 移除 "data: " 前缀
                if data_str.strip() == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            full_content += delta["content"]
                except json.JSONDecodeError:
                    continue
        
        return full_content
    
    async def call_tool_stream_async(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """异步调用工具（流式）"""
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.sse_endpoint,
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # 移除 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def call_tool_stream_async_full(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """异步调用工具（流式，返回完整的 OpenAI 格式数据）"""
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.sse_endpoint,
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # 移除 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            continue


def demo_sync_calls():
    """演示同步调用"""
    print("=" * 60)
    print("同步调用示例")
    print("=" * 60)
    
    client = OpenAIStreamingClient()
    
    # 1. 非流式调用
    print("\n1. 非流式调用 - 数据分析:")
    try:
        result = client.call_tool_sync(
            "analyze_data",
            {
                "data": [1, 2, 3, 4, 5, 10, 20, 30],
                "analysis_type": "statistical"
            }
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
    
    # 2. 流式调用（阻塞）
    print("\n2. 流式调用（阻塞） - 文本生成:")
    try:
        result = client.call_tool_stream_sync(
            "generate_text",
            {
                "topic": "机器学习",
                "length": 2,
                "streaming": True
            }
        )
        print(result)
    except Exception as e:
        print(f"错误: {e}")


async def demo_async_calls():
    """演示异步调用"""
    print("\n" + "=" * 60)
    print("异步调用示例")
    print("=" * 60)
    
    client = OpenAIStreamingClient()
    
    # 1. 异步流式调用 - 只获取内容
    print("\n1. 异步流式调用 - 文本生成（仅内容）:")
    try:
        async for chunk in client.call_tool_stream_async(
            "generate_text",
            {
                "topic": "深度学习",
                "length": 2,
                "streaming": True
            }
        ):
            print(chunk, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"错误: {e}")
    
    # 2. 异步流式调用 - 完整 OpenAI 格式
    print("\n2. 异步流式调用 - 长任务（完整格式）:")
    try:
        chunk_count = 0
        async for data in client.call_tool_stream_async_full(
            "simulate_long_task",
            {
                "task_name": "数据处理任务",
                "duration": 5
            }
        ):
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("-" * 40)
            
            # 只显示前几个 chunk，避免输出过长
            if chunk_count >= 3:
                print("... (省略后续 chunks)")
                break
    except Exception as e:
        print(f"错误: {e}")


async def demo_concurrent_calls():
    """演示并发调用"""
    print("\n" + "=" * 60)
    print("并发调用示例")
    print("=" * 60)
    
    client = OpenAIStreamingClient()
    
    # 创建多个并发任务
    tasks = []
    topics = ["人工智能", "区块链", "量子计算"]
    
    for i, topic in enumerate(topics):
        task = asyncio.create_task(
            collect_stream_content(
                client,
                "generate_text",
                {
                    "topic": topic,
                    "length": 1,
                    "streaming": True
                },
                f"任务{i+1}"
            )
        )
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"\n{result['name']} 结果:")
        print(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])


async def collect_stream_content(
    client: OpenAIStreamingClient,
    tool_name: str,
    arguments: Dict[str, Any],
    task_name: str
) -> Dict[str, str]:
    """收集流式内容"""
    content = ""
    try:
        async for chunk in client.call_tool_stream_async(tool_name, arguments):
            content += chunk
    except Exception as e:
        content = f"错误: {e}"
    
    return {
        "name": task_name,
        "content": content
    }


def main():
    """主函数"""
    print("OpenAI 格式流式返回客户端示例")
    print("请确保示例服务器正在运行: python example_openai_streaming_server.py")
    print()
    
    # 同步调用示例
    demo_sync_calls()
    
    # 异步调用示例
    asyncio.run(demo_async_calls())
    
    # 并发调用示例
    asyncio.run(demo_concurrent_calls())
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()