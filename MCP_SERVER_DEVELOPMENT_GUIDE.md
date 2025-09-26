# MCP 服务器开发指南

本指南将详细介绍如何使用 MCP Framework 开发高质量的 MCP 服务器，包括最新的装饰器使用方式和 OpenAI 格式的调用方法。

## 📋 目录

1. [快速开始](#快速开始)
2. [装饰器 API 详解](#装饰器-api-详解)
3. [工具定义](#工具定义)
4. [流式工具](#流式工具)
5. [资源管理](#资源管理)
6. [服务器参数配置](#服务器参数配置)
7. [OpenAI 格式调用](#openai-格式调用)
8. [角色权限控制](#角色权限控制)
9. [最佳实践](#最佳实践)
10. [完整示例](#完整示例)

## 🚀 快速开始

### 安装框架

```bash
pip install mcp-framework
```

### 创建基础服务器

```python
#!/usr/bin/env python3
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required, Optional
from typing import Annotated

class MyMCPServer(EnhancedMCPServer):
    """我的 MCP 服务器"""
    
    def __init__(self):
        super().__init__(
            name="my-mcp-server",
            version="1.0.0",
            description="我的第一个 MCP 服务器"
        )
    
    async def initialize(self):
        """服务器初始化"""
        self.logger.info("服务器初始化完成")
    
    @property
    def setup_tools(self):
        """设置工具 - 使用 @property 装饰器"""
        
        @self.tool("计算两个数的和")
        async def add_numbers(
            a: Annotated[int, Required("第一个数字")],
            b: Annotated[int, Required("第二个数字")]
        ) -> int:
            """计算两个数字的和"""
            return a + b

def main():
    server = MyMCPServer()
    run_server_main(
        server_instance=server,
        server_name="MyMCPServer",
        default_port=8080
    )

if __name__ == "__main__":
    main()
```

## 🎯 装饰器 API 详解

### 核心装饰器

MCP Framework 提供了三个核心装饰器：

- `@self.tool()` - 定义普通工具
- `@self.streaming_tool()` - 定义流式工具
- `@self.resource()` - 定义资源

### 参数注解

使用 `typing.Annotated` 和框架提供的参数规范来定义参数：

```python
from mcp_framework.core.decorators import Required, Optional, Enum, IntRange
from typing import Annotated

# 必需参数
name: Annotated[str, Required("用户名称")]

# 可选参数（带默认值）
count: Annotated[int, Optional("数量", default=10)] = 10

# 枚举参数
mode: Annotated[str, Enum("模式", ["fast", "normal", "slow"])]

# 整数范围参数
age: Annotated[int, IntRange("年龄", min_value=0, max_value=120)]
```

## 🔧 工具定义

### 基础工具

```python
@property
def setup_tools(self):
    """设置工具"""
    
    @self.tool("获取当前时间")
    async def get_current_time() -> str:
        """获取当前时间"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    @self.tool("文本处理")
    async def process_text(
        text: Annotated[str, Required("要处理的文本")],
        operation: Annotated[str, Enum("操作类型", ["upper", "lower", "reverse"])],
        repeat: Annotated[int, Optional("重复次数", default=1)] = 1
    ) -> str:
        """处理文本"""
        result = text
        
        if operation == "upper":
            result = result.upper()
        elif operation == "lower":
            result = result.lower()
        elif operation == "reverse":
            result = result[::-1]
        
        return result * repeat
```

### 复杂数据类型

```python
from typing import Dict, List, Any

@self.tool("数据分析")
async def analyze_data(
    data: Annotated[List[Dict[str, Any]], Required("要分析的数据列表")],
    analysis_type: Annotated[str, Optional("分析类型", default="summary")] = "summary"
) -> Dict[str, Any]:
    """分析数据并返回结构化结果"""
    if not data:
        return {"error": "数据为空"}
    
    result = {
        "total_count": len(data),
        "analysis_type": analysis_type,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if analysis_type == "summary":
        result["summary"] = {
            "first_item": data[0] if data else None,
            "last_item": data[-1] if data else None
        }
    
    return result
```

## 🌊 流式工具

流式工具适用于需要实时输出结果的场景，如长时间运行的任务、大量数据处理等。

### 基础流式工具

```python
@self.streaming_tool("生成数字序列")
async def generate_sequence(
    start: Annotated[int, Required("起始数字")],
    end: Annotated[int, Required("结束数字")],
    delay: Annotated[float, Optional("延迟时间（秒）", default=0.1)] = 0.1
):
    """生成数字序列"""
    for i in range(start, end + 1):
        yield f"数字: {i}\n"
        await asyncio.sleep(delay)
```

### 进度报告流式工具

```python
@self.streaming_tool("模拟长时间任务")
async def simulate_long_task(
    task_name: Annotated[str, Required("任务名称")],
    duration: Annotated[int, Optional("持续时间（秒）", default=10)] = 10
):
    """模拟长时间运行的任务"""
    yield f"开始执行任务: {task_name}\n"
    yield f"预计耗时: {duration} 秒\n\n"
    
    for i in range(duration):
        progress = ((i + 1) / duration) * 100
        yield f"进度: {progress:.1f}% - 步骤 {i+1}/{duration} 完成\n"
        await asyncio.sleep(1)
    
    yield f"\n任务 '{task_name}' 执行完成！\n"
```

### 文件处理流式工具

```python
@self.streaming_tool("处理大文件")
async def process_large_file(
    file_path: Annotated[str, Required("文件路径")],
    chunk_size: Annotated[int, Optional("块大小", default=1024)] = 1024
):
    """流式处理大文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            line_count = 0
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                lines = chunk.count('\n')
                line_count += lines
                
                yield f"已处理 {line_count} 行\n"
                await asyncio.sleep(0.1)
        
        yield f"文件处理完成，总共 {line_count} 行\n"
    except Exception as e:
        yield f"处理文件时出错: {str(e)}\n"
```

## 📁 资源管理

资源用于提供静态或动态内容，如文件、配置信息等。

```python
@property
def setup_tools(self):
    """设置工具和资源"""
    
    # 定义资源
    @self.resource(
        uri="file://config.json",
        name="服务器配置",
        description="服务器配置文件",
        mime_type="application/json"
    )
    async def get_config():
        """获取服务器配置"""
        config = {
            "server_name": self.name,
            "version": self.version,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources)
        }
        return json.dumps(config, indent=2)
    
    @self.resource(
        uri="file://status.txt",
        name="服务器状态",
        description="当前服务器运行状态",
        mime_type="text/plain"
    )
    async def get_status():
        """获取服务器状态"""
        import psutil
        import datetime
        
        status = f"""服务器状态报告
生成时间: {datetime.datetime.now().isoformat()}
服务器名称: {self.name}
版本: {self.version}
CPU 使用率: {psutil.cpu_percent()}%
内存使用率: {psutil.virtual_memory().percent}%
"""
        return status
```

## ⚙️ 服务器参数配置

服务器参数允许用户在运行时配置服务器行为。

### 定义服务器参数

```python
from mcp_framework.core.decorators import (
    ServerParam, StringParam, SelectParam, BooleanParam, PathParam
)

@property
def setup_server_params(self):
    """设置服务器参数"""
    
    @self.decorators.server_param("api_key")
    async def api_key_param(
        param: Annotated[str, StringParam(
            display_name="API 密钥",
            description="用于访问外部服务的 API 密钥",
            placeholder="请输入 API 密钥",
            required=True
        )]
    ):
        """API 密钥参数"""
        pass
    
    @self.decorators.server_param("model_type")
    async def model_param(
        param: Annotated[str, SelectParam(
            display_name="模型类型",
            description="选择要使用的 AI 模型",
            options=["gpt-3.5-turbo", "gpt-4", "claude-3"],
            default="gpt-3.5-turbo"
        )]
    ):
        """模型类型参数"""
        pass
    
    @self.decorators.server_param("enable_debug")
    async def debug_param(
        param: Annotated[bool, BooleanParam(
            display_name="启用调试模式",
            description="是否启用详细的调试日志",
            default=False
        )]
    ):
        """调试模式参数"""
        pass
    
    @self.decorators.server_param("project_root")
    async def project_root_param(
        param: Annotated[str, PathParam(
            display_name="项目根目录",
            description="服务器操作的根目录路径",
            required=False,
            placeholder="/path/to/project"
        )]
    ):
        """项目根目录参数"""
        pass
```

### 使用配置参数

```python
@self.tool("使用配置的工具")
async def configured_tool(
    query: Annotated[str, Required("查询内容")]
) -> str:
    """使用服务器配置的工具"""
    # 获取配置值
    api_key = self.get_config_value("api_key")
    model_type = self.get_config_value("model_type", "gpt-3.5-turbo")
    enable_debug = self.get_config_value("enable_debug", False)
    project_root = self.get_config_value("project_root", ".")
    
    if enable_debug:
        self.logger.debug(f"使用模型: {model_type}, 项目根目录: {project_root}")
    
    # 使用配置进行处理
    result = f"使用 {model_type} 处理查询: {query}"
    if enable_debug:
        result += f" (调试模式已启用)"
    
    return result
```

## 🤖 OpenAI 格式调用

MCP Framework 支持 OpenAI 兼容的 API 格式，可以与现有的 OpenAI 客户端无缝集成。

### 服务器端点

启动服务器后，以下端点将自动可用：

- **标准 MCP 端点**:
  - `POST /tool/call` - 调用工具
  - `POST /sse/tool/call` - 流式调用工具

- **OpenAI 兼容端点**:
  - `POST /sse/openai/tool/call` - OpenAI 格式流式调用
  - `GET /sse/openai/tool/call` - OpenAI 格式流式调用（GET 方式）

### Python 客户端调用示例

#### 同步调用（非流式）

```python
import requests
import json

def call_mcp_tool_sync(tool_name: str, arguments: dict, base_url: str = "http://localhost:8080"):
    """同步调用 MCP 工具"""
    url = f"{base_url}/tool/call"
    payload = {
        "tool_name": tool_name,
        "arguments": arguments
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    return response.json().get("result", "")

# 使用示例
result = call_mcp_tool_sync(
    tool_name="add_numbers",
    arguments={"a": 10, "b": 20}
)
print(f"结果: {result}")  # 输出: 结果: 30
```

#### 异步流式调用

```python
import aiohttp
import asyncio
import json

async def call_mcp_tool_stream(tool_name: str, arguments: dict, base_url: str = "http://localhost:8080"):
    """异步流式调用 MCP 工具"""
    url = f"{base_url}/sse/openai/tool/call"
    payload = {
        "tool_name": tool_name,
        "arguments": arguments
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
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
                                print(delta["content"], end="", flush=True)
                    except json.JSONDecodeError:
                        continue

# 使用示例
async def main():
    await call_mcp_tool_stream(
        tool_name="generate_sequence",
        arguments={"start": 1, "end": 10}
    )

asyncio.run(main())
```

#### 使用 OpenAI 客户端库

```python
from openai import OpenAI

# 注意：这需要服务器实现完整的 OpenAI 兼容 API
# 当前 MCP Framework 主要支持工具调用格式
client = OpenAI(
    base_url="http://localhost:8080",
    api_key="dummy-key"  # MCP 服务器通常不需要真实的 API 密钥
)

# 调用示例（需要服务器支持 chat/completions 端点）
response = client.chat.completions.create(
    model="mcp-model",
    messages=[
        {"role": "user", "content": "请使用 add_numbers 工具计算 10 + 20"}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "add_numbers",
                "description": "计算两个数的和",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "第一个数字"},
                        "b": {"type": "integer", "description": "第二个数字"}
                    },
                    "required": ["a", "b"]
                }
            }
        }
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### cURL 调用示例

```bash
# 非流式调用
curl -X POST http://localhost:8080/tool/call \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "add_numbers",
       "arguments": {
         "a": 10,
         "b": 20
       }
     }'

# OpenAI 格式流式调用
curl -X POST http://localhost:8080/sse/openai/tool/call \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
       "tool_name": "generate_sequence",
       "arguments": {
         "start": 1,
         "end": 5
       }
     }'
```

## 👥 角色权限控制

角色权限控制允许你为不同的工具指定访问角色，实现细粒度的权限管理。

### 单角色工具

```python
@self.tool("管理员工具", role="admin")
async def admin_tool(
    action: Annotated[str, Required("管理操作")]
) -> str:
    """只有管理员可以使用的工具"""
    return f"执行管理操作: {action}"

@self.tool("分析师工具", role="analyst")
async def analyst_tool(
    data: Annotated[str, Required("要分析的数据")]
) -> str:
    """只有分析师可以使用的工具"""
    return f"分析结果: {data}"
```

### 多角色工具

```python
@self.tool("执行任务", role=["executor", "manager"])
async def execute_task(
    task: Annotated[str, Required("任务描述")]
) -> str:
    """执行者和管理者都可以使用的工具"""
    return f"执行任务: {task}"

@self.tool("审核任务", role=["manager", "supervisor", "admin"])
async def review_task(
    task_id: Annotated[str, Required("任务ID")]
) -> str:
    """管理者、监督者和管理员可以使用的工具"""
    return f"审核任务 {task_id}"
```

### 无角色限制工具

```python
@self.tool("获取状态")  # 不指定 role 参数
async def get_status() -> str:
    """所有用户都可以使用的工具"""
    return "服务器运行正常"
```

### 流式工具的角色控制

```python
@self.streaming_tool("监控进度", role=["manager", "supervisor"])
async def monitor_progress(
    task_id: Annotated[str, Required("任务ID")]
):
    """管理者和监督者可以使用的流式监控工具"""
    for i in range(10):
        yield f"任务 {task_id} 进度: {(i+1)*10}%\n"
        await asyncio.sleep(1)
```

## 💡 最佳实践

### 1. 错误处理

```python
@self.tool("安全的文件读取")
async def safe_read_file(
    file_path: Annotated[str, Required("文件路径")]
) -> str:
    """安全地读取文件"""
    try:
        # 验证文件路径
        if not file_path or ".." in file_path:
            return "错误: 无效的文件路径"
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"错误: 文件 {file_path} 不存在"
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    except PermissionError:
        return f"错误: 没有权限读取文件 {file_path}"
    except UnicodeDecodeError:
        return f"错误: 文件 {file_path} 编码格式不支持"
    except Exception as e:
        self.logger.error(f"读取文件时发生未知错误: {e}")
        return f"错误: 读取文件时发生未知错误"
```

### 2. 日志记录

```python
@self.tool("带日志的工具")
async def logged_tool(
    operation: Annotated[str, Required("操作类型")]
) -> str:
    """带有详细日志记录的工具"""
    self.logger.info(f"开始执行操作: {operation}")
    
    try:
        # 模拟操作
        await asyncio.sleep(1)
        result = f"操作 {operation} 执行成功"
        
        self.logger.info(f"操作完成: {operation}")
        return result
    
    except Exception as e:
        self.logger.error(f"操作失败: {operation}, 错误: {e}")
        raise
```

### 3. 参数验证

```python
@self.tool("参数验证示例")
async def validated_tool(
    email: Annotated[str, Required("邮箱地址")],
    age: Annotated[int, IntRange("年龄", min_value=0, max_value=120)],
    category: Annotated[str, Enum("分类", ["A", "B", "C"])]
) -> str:
    """带参数验证的工具"""
    import re
    
    # 额外的邮箱验证
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return "错误: 邮箱格式不正确"
    
    return f"验证通过 - 邮箱: {email}, 年龄: {age}, 分类: {category}"
```

### 4. 异步操作

```python
@self.tool("异步网络请求")
async def async_network_request(
    url: Annotated[str, Required("请求URL")]
) -> str:
    """异步网络请求示例"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    return f"请求成功，内容长度: {len(content)}"
                else:
                    return f"请求失败，状态码: {response.status}"
    
    except asyncio.TimeoutError:
        return "错误: 请求超时"
    except Exception as e:
        return f"错误: {str(e)}"
```

## 📝 完整示例

以下是一个完整的 MCP 服务器示例，展示了所有主要功能：

```python
#!/usr/bin/env python3
"""
完整的 MCP 服务器示例
展示了工具定义、流式工具、资源管理、参数配置和角色控制
"""

import asyncio
import datetime
import json
import os
from typing import Dict, List, Any
from typing_extensions import Annotated

from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import (
    Required, Optional, Enum, IntRange,
    ServerParam, StringParam, SelectParam, BooleanParam, PathParam
)


class CompleteMCPServer(EnhancedMCPServer):
    """完整功能的 MCP 服务器示例"""
    
    def __init__(self):
        super().__init__(
            name="complete-mcp-server",
            version="1.0.0",
            description="展示 MCP Framework 所有功能的完整示例服务器"
        )
    
    async def initialize(self):
        """服务器初始化"""
        self.logger.info("Complete MCP Server 初始化完成")
        
        # 初始化一些状态
        self.task_counter = 0
        self.active_tasks = {}
    
    @property
    def setup_server_params(self):
        """设置服务器参数"""
        
        @self.decorators.server_param("api_key")
        async def api_key_param(
            param: Annotated[str, StringParam(
                display_name="API 密钥",
                description="用于访问外部服务的 API 密钥",
                placeholder="请输入 API 密钥",
                required=True
            )]
        ):
            """API 密钥参数"""
            pass
        
        @self.decorators.server_param("work_mode")
        async def work_mode_param(
            param: Annotated[str, SelectParam(
                display_name="工作模式",
                description="选择服务器的工作模式",
                options=["development", "production", "testing"],
                default="development"
            )]
        ):
            """工作模式参数"""
            pass
        
        @self.decorators.server_param("enable_logging")
        async def logging_param(
            param: Annotated[bool, BooleanParam(
                display_name="启用详细日志",
                description="是否启用详细的调试日志",
                default=True
            )]
        ):
            """日志参数"""
            pass
    
    @property
    def setup_tools(self):
        """设置工具和资源"""
        
        # === 基础工具 ===
        
        @self.tool("获取服务器信息")
        async def get_server_info() -> Dict[str, Any]:
            """获取服务器基本信息"""
            return {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "tools_count": len(self.tools),
                "resources_count": len(self.resources),
                "uptime": "运行中",
                "work_mode": self.get_config_value("work_mode", "development")
            }
        
        @self.tool("计算器")
        async def calculator(
            operation: Annotated[str, Enum("运算类型", ["add", "subtract", "multiply", "divide"])],
            a: Annotated[float, Required("第一个数字")],
            b: Annotated[float, Required("第二个数字")]
        ) -> str:
            """基础计算器"""
            try:
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    if b == 0:
                        return "错误: 除数不能为零"
                    result = a / b
                else:
                    return f"错误: 不支持的运算类型 {operation}"
                
                return f"{a} {operation} {b} = {result}"
            
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        # === 角色控制工具 ===
        
        @self.tool("管理员工具", role="admin")
        async def admin_tool(
            action: Annotated[str, Required("管理操作")]
        ) -> str:
            """只有管理员可以使用的工具"""
            self.logger.info(f"管理员执行操作: {action}")
            return f"管理员操作 '{action}' 执行成功"
        
        @self.tool("数据分析", role=["analyst", "manager"])
        async def analyze_data(
            data: Annotated[List[float], Required("数据列表")],
            analysis_type: Annotated[str, Optional("分析类型", default="basic")] = "basic"
        ) -> Dict[str, Any]:
            """数据分析工具（分析师和管理者可用）"""
            if not data:
                return {"error": "数据为空"}
            
            result = {
                "analysis_type": analysis_type,
                "count": len(data),
                "sum": sum(data),
                "average": sum(data) / len(data),
                "min": min(data),
                "max": max(data)
            }
            
            if analysis_type == "detailed":
                result["variance"] = sum((x - result["average"]) ** 2 for x in data) / len(data)
                result["std_dev"] = result["variance"] ** 0.5
            
            return result
        
        # === 流式工具 ===
        
        @self.streaming_tool("生成报告")
        async def generate_report(
            topic: Annotated[str, Required("报告主题")],
            sections: Annotated[int, IntRange("章节数量", min_value=1, max_value=10)] = 3
        ):
            """生成结构化报告"""
            yield f"# {topic} 报告\n\n"
            yield f"生成时间: {datetime.datetime.now().isoformat()}\n\n"
            
            for i in range(sections):
                yield f"## 第 {i+1} 章节\n\n"
                yield f"这是关于 '{topic}' 的第 {i+1} 个章节的内容。"
                yield f"在这个章节中，我们将详细讨论相关的概念和应用。\n\n"
                await asyncio.sleep(0.5)
            
            yield "## 总结\n\n"
            yield f"以上就是关于 '{topic}' 的完整报告，共包含 {sections} 个章节。\n"
        
        @self.streaming_tool("任务监控", role=["manager", "supervisor"])
        async def monitor_task(
            task_name: Annotated[str, Required("任务名称")],
            duration: Annotated[int, Optional("监控时长（秒）", default=10)] = 10
        ):
            """任务监控工具（管理者和监督者可用）"""
            task_id = f"task_{self.task_counter}"
            self.task_counter += 1
            self.active_tasks[task_id] = task_name
            
            yield f"开始监控任务: {task_name} (ID: {task_id})\n"
            yield f"监控时长: {duration} 秒\n\n"
            
            for i in range(duration):
                progress = ((i + 1) / duration) * 100
                yield f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                yield f"任务 {task_id} 进度: {progress:.1f}%\n"
                await asyncio.sleep(1)
            
            del self.active_tasks[task_id]
            yield f"\n任务 {task_id} 监控完成\n"
        
        # === 资源定义 ===
        
        @self.resource(
            uri="file://server-config.json",
            name="服务器配置",
            description="当前服务器配置信息",
            mime_type="application/json"
        )
        async def get_server_config():
            """获取服务器配置"""
            config = {
                "server": {
                    "name": self.name,
                    "version": self.version,
                    "description": self.description
                },
                "runtime": {
                    "work_mode": self.get_config_value("work_mode", "development"),
                    "logging_enabled": self.get_config_value("enable_logging", True),
                    "active_tasks": len(self.active_tasks)
                },
                "statistics": {
                    "tools_count": len(self.tools),
                    "resources_count": len(self.resources),
                    "task_counter": self.task_counter
                }
            }
            return json.dumps(config, indent=2, ensure_ascii=False)
        
        @self.resource(
            uri="file://active-tasks.txt",
            name="活跃任务列表",
            description="当前正在运行的任务列表",
            mime_type="text/plain"
        )
        async def get_active_tasks():
            """获取活跃任务列表"""
            if not self.active_tasks:
                return "当前没有活跃的任务"
            
            lines = ["活跃任务列表:", "=" * 20]
            for task_id, task_name in self.active_tasks.items():
                lines.append(f"- {task_id}: {task_name}")
            
            lines.append(f"\n总计: {len(self.active_tasks)} 个任务")
            return "\n".join(lines)


def main():
    """主函数"""
    server = CompleteMCPServer()
    
    print("=" * 60)
    print("完整功能 MCP 服务器示例")
    print("=" * 60)
    print()
    print("功能特性:")
    print("✅ 基础工具定义")
    print("✅ 流式工具支持")
    print("✅ 角色权限控制")
    print("✅ 服务器参数配置")
    print("✅ 资源管理")
    print("✅ OpenAI 兼容 API")
    print("✅ 错误处理和日志")
    print()
    print("可用工具:")
    print("- get_server_info: 获取服务器信息")
    print("- calculator: 基础计算器")
    print("- admin_tool: 管理员工具 (role: admin)")
    print("- analyze_data: 数据分析 (role: analyst, manager)")
    print("- generate_report: 生成报告 (流式)")
    print("- monitor_task: 任务监控 (流式, role: manager, supervisor)")
    print()
    print("可用资源:")
    print("- file://server-config.json: 服务器配置")
    print("- file://active-tasks.txt: 活跃任务列表")
    print()
    print("=" * 60)
    
    # 启动服务器
    run_server_main(
        server_instance=server,
        server_name="CompleteMCPServer",
        default_port=8080
    )


if __name__ == "__main__":
    main()
```

## 🚀 启动和测试

### 启动服务器

```bash
python your_server.py
```

### 访问 Web 界面

- **配置页面**: http://localhost:8080/config
- **测试页面**: http://localhost:8080/test
- **设置页面**: http://localhost:8080/setup
- **健康检查**: http://localhost:8080/health

### 测试工具调用

```bash
# 测试基础工具
curl -X POST http://localhost:8080/tool/call \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "get_server_info",
       "arguments": {}
     }'

# 测试流式工具
curl -X POST http://localhost:8080/sse/openai/tool/call \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
       "tool_name": "generate_report",
       "arguments": {
         "topic": "人工智能发展",
         "sections": 3
       }
     }'
```

## 📚 总结

本指南涵盖了使用 MCP Framework 开发服务器的所有核心概念：

1. **装饰器 API**: 使用 `@property` 和装饰器定义工具
2. **类型注解**: 使用 `Annotated` 和参数规范定义参数
3. **流式工具**: 支持实时输出的长时间运行任务
4. **资源管理**: 提供静态和动态内容
5. **参数配置**: 运行时可配置的服务器参数
6. **OpenAI 兼容**: 支持 OpenAI 格式的 API 调用
7. **角色控制**: 基于角色的工具访问权限
8. **最佳实践**: 错误处理、日志记录、参数验证等

通过遵循本指南，你可以快速构建功能强大、易于维护的 MCP 服务器。

---

**更多资源**:
- [MCP Framework GitHub](https://github.com/your-repo/mcp_framework)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [示例服务器集合](https://github.com/leeoohoo/mcp_servers)