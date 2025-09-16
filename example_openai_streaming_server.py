#!/usr/bin/env python3
"""
OpenAI 格式流式返回示例服务器

这个示例展示了如何使用 MCP 框架的 OpenAI 格式流式返回功能。
服务器提供了几个工具来演示不同类型的流式输出。
使用现代装饰器方式定义工具。
"""

import asyncio
import json
from typing import Dict, Any, AsyncGenerator
from typing_extensions import Annotated
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required, Optional


class OpenAIStreamingExampleServer(EnhancedMCPServer):
    """OpenAI 格式流式返回示例服务器"""
    
    def __init__(self):
        super().__init__(
            name="openai-streaming-example",
            version="1.0.0",
            description="演示 OpenAI 格式流式返回的示例服务器"
        )
    
    async def initialize(self):
        """初始化服务器"""
        self.logger.info("OpenAI Streaming Example Server initialized")
    
    @property
    def setup_tools(self):
        """设置工具和资源"""
        
        # 使用装饰器定义工具
        @self.tool("生成指定长度的文本内容，支持流式输出")
        async def generate_text(
            topic: Annotated[str, Required("文本主题")],
            length: Annotated[int, Optional("生成文本的段落数量", default=3)] = 3,
            streaming: Annotated[bool, Optional("是否使用流式输出", default=True)] = True
        ) -> str:
            """生成文本内容"""
            paragraphs = []
            for i in range(length):
                paragraph = f"这是关于'{topic}'的第{i+1}段内容。" + \
                           f"在这一段中，我们将详细探讨{topic}的各个方面，" + \
                           f"包括其重要性、应用场景以及未来发展趋势。"
                paragraphs.append(paragraph)
            
            return "\n\n".join(paragraphs)
        
        @self.tool("分析数据并返回结构化结果")
        async def analyze_data(
            data: Annotated[list, Required("要分析的数据数组")],
            analysis_type: Annotated[str, Optional("分析类型：summary/detailed/statistical", default="summary")] = "summary"
        ) -> Dict[str, Any]:
            """分析数据"""
            if not data:
                return {"error": "数据为空"}
            
            result = {
                "analysis_type": analysis_type,
                "data_count": len(data),
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            if analysis_type == "summary":
                result["summary"] = {
                    "total_items": len(data),
                    "first_item": data[0] if data else None,
                    "last_item": data[-1] if data else None
                }
            elif analysis_type == "detailed":
                result["detailed_analysis"] = {
                    "items": data,
                    "item_types": [type(item).__name__ for item in data],
                    "unique_items": len(set(str(item) for item in data))
                }
            elif analysis_type == "statistical":
                numeric_data = [item for item in data if isinstance(item, (int, float))]
                if numeric_data:
                    result["statistics"] = {
                        "count": len(numeric_data),
                        "sum": sum(numeric_data),
                        "average": sum(numeric_data) / len(numeric_data),
                        "min": min(numeric_data),
                        "max": max(numeric_data)
                    }
                else:
                    result["statistics"] = {"error": "没有数值型数据"}
            
            return result
        
        # 定义流式工具
        @self.streaming_tool("生成数字序列")
        async def generate_sequence(
            start: Annotated[int, Required("起始数字")],
            end: Annotated[int, Required("结束数字")]
        ):
            """生成数字序列"""
            for i in range(start, end + 1):
                yield f"数字: {i}"
                await asyncio.sleep(0.1)  # 模拟处理时间
        
        @self.streaming_tool("模拟长时间运行的任务，展示流式进度更新")
        async def simulate_long_task(
            task_name: Annotated[str, Required("任务名称")],
            duration: Annotated[int, Optional("任务持续时间（秒）", default=10)] = 10
        ):
            """模拟长时间运行的任务"""
            yield f"开始执行任务: {task_name}\n"
            yield f"预计耗时: {duration} 秒\n\n"
            
            for i in range(duration):
                progress = ((i + 1) / duration) * 100
                yield f"进度: {progress:.1f}% - 步骤 {i+1}/{duration} 完成\n"
                await asyncio.sleep(1)
            
            yield f"\n任务 '{task_name}' 执行完成！\n"
    



def main():
    """主函数"""
    server = OpenAIStreamingExampleServer()
    
    print("="*60)
    print("OpenAI 格式流式返回示例服务器")
    print("="*60)
    print()
    print("这个服务器演示了如何使用 MCP 框架的 OpenAI 格式流式返回功能。")
    print()
    print("可用的工具:")
    print("1. generate_text - 生成文本内容")
    print("2. analyze_data - 分析数据并返回结构化结果")
    print("3. generate_sequence - 生成数字序列（流式）")
    print("4. simulate_long_task - 模拟长时间运行的任务（流式）")
    print()
    print("OpenAI 格式的 SSE 端点:")
    print("- GET/POST /sse/openai/tool/call")
    print("- GET/POST /mcp/sse/openai/tool/call")
    print()
    # 获取实际端口
    import os
    actual_port = os.getenv('MCP_SERVER_PORT', '8080')
    
    print("示例请求:")
    print(f"curl -X POST http://localhost:{actual_port}/tool/call \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{\\')
    print('       "tool_name": "generate_text",\\')
    print('       "arguments": {\\')
    print('         "topic": "人工智能",\\')
    print('         "length": 2\\')
    print('       }\\')
    print('     }\'')
    print()
    print("="*60)
    
    # 启动服务器
    import os
    default_port = int(os.getenv('MCP_SERVER_PORT', '8080'))
    run_server_main(
        server_instance=server,
        server_name="OpenAIStreamingExampleServer",
        default_port=default_port
    )


if __name__ == "__main__":
    main()