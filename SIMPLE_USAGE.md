# MCP Framework 简单使用指南

## 最简单的使用方式

### 1. 基本使用 - SimpleClient

```python
import asyncio
from mcp_framework.client.simple import SimpleClient

async def main():
    # 使用上下文管理器，自动处理连接和清理
    async with SimpleClient("your_server.py", alias="my_server") as client:
        # 获取所有工具
        tools = await client.tools()
        print(f"可用工具: {tools}")
        
        # 调用工具
        result = await client.call("tool_name", param1="value1", param2="value2")
        print(f"结果: {result}")
        
        # 检查工具是否存在
        if await client.has_tool("some_tool"):
            result = await client.call("some_tool", data="test")

asyncio.run(main())
```

### 2. 一行代码调用 - 快速函数

```python
import asyncio
from mcp_framework.client.simple import quick_call, quick_tools

async def main():
    # 快速获取工具列表
    tools = await quick_tools("your_server.py", alias="my_server")
    
    # 快速调用工具
    result = await quick_call("your_server.py", "tool_name", 
                             alias="my_server", param1="value1")

asyncio.run(main())
```

### 3. 同步版本（如果你不想用 async/await）

```python
from mcp_framework.client.simple import sync_call, sync_tools

# 同步获取工具列表
tools = sync_tools("your_server.py", alias="my_server")

# 同步调用工具
result = sync_call("your_server.py", "tool_name", 
                  alias="my_server", param1="value1")
```

## 特性

### 🚀 自动进程池管理
- 相同别名的客户端自动复用进程
- 30分钟无使用自动关闭进程
- 进程健康检查和自动恢复

### 🔧 简单配置
- 只需要服务器脚本路径
- 可选的别名用于进程复用
- 自动处理连接和初始化

### 🛡️ 错误处理
- 自动重连机制
- 进程异常自动恢复
- 资源自动清理

## 完整示例

```python
#!/usr/bin/env python3
import asyncio
from mcp_framework.client.simple import SimpleClient

async def demo():
    # 连接到你的 MCP 服务器
    async with SimpleClient("simple_test_server.py", alias="demo") as client:
        
        # 1. 查看所有可用工具
        tools = await client.tools()
        print(f"📋 可用工具: {tools}")
        
        # 2. 调用 echo 工具
        echo_result = await client.call("echo", text="Hello World!")
        print(f"🔊 Echo: {echo_result}")
        
        # 3. 调用数学工具
        math_result = await client.call("add", a=10, b=20)
        print(f"➕ 计算: {math_result}")
        
        # 4. 调用问候工具
        greet_result = await client.call("greet", name="用户", language="中文")
        print(f"👋 问候: {greet_result}")
        
        # 5. 检查工具是否存在
        has_tool = await client.has_tool("echo")
        print(f"🔍 有 echo 工具: {has_tool}")

if __name__ == "__main__":
    asyncio.run(demo())
```

## 注意事项

1. **别名很重要**: 相同别名的客户端会复用同一个进程，提高性能
2. **使用上下文管理器**: 确保资源正确清理
3. **进程池默认开启**: 如果不需要进程池，可以设置 `use_process_pool=False`
4. **异步优先**: 推荐使用异步版本以获得最佳性能

这就是全部！现在你可以用最简单的方式使用 MCP Framework 了！