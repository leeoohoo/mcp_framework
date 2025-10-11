
# MCP Framework 使用指南

MCP Framework 是一个强大且易用的 MCP (Model Context Protocol) 服务器开发框架，支持快速构建、部署和管理 MCP 服务器。

## 📋 目录

1. [安装](#安装)
2. [快速开始](#快速开始)
3. [核心概念](#核心概念)
4. [简化启动器](#简化启动器)
5. [HTTP 服务器模式](#http-服务器模式)
6. [Stdio 集成方式](#stdio-集成方式)
7. [装饰器 API](#装饰器-api)
8. [配置管理](#配置管理)
9. [客户端 SDK](#客户端-sdk)
10. [简化客户端](#简化客户端)
11. [最佳实践](#最佳实践)

## 🚀 安装

### 从源码安装（开发模式）

```bash
# 克隆或下载源码到本地
cd mcp_framework

# 安装为可编辑包
pip install -e .

# 或者安装所有依赖（包括开发工具）
pip install -e ".[dev,web,build]"
```

### 验证安装

```python
import mcp_framework
from mcp_framework import EnhancedMCPServer, run_server_main
print(f"MCP Framework version: {mcp_framework.__version__}")
```

## 🎯 快速开始

### 基础服务器示例

```python
#!/usr/bin/env python3
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import R, O
from typing_extensions import Annotated

# 创建服务器实例
server = EnhancedMCPServer(
    name="my-first-server",
    version="1.0.0",
    description="我的第一个MCP服务器"
)

# 定义工具
@server.tool("计算两个数的和")
async def add_numbers(
    a: Annotated[int, R("第一个数字")],
    b: Annotated[int, R("第二个数字")]
):
    """计算两个数字的和"""
    return a + b

@server.tool("获取服务器信息")
async def get_server_info():
    """获取服务器基本信息"""
    return {
        "name": server.name,
        "version": server.version,
        "description": server.description
    }

if __name__ == "__main__":
    # 启动HTTP服务器
    run_server_main(
        server_instance=server,
        server_name="MyFirstServer",
        default_port=8080
    )
```

## 🏗️ 核心概念

### 1. EnhancedMCPServer

`EnhancedMCPServer` 是框架的核心类，提供了：
- 装饰器API用于定义工具和资源
- 自动参数验证和类型转换
- 角色权限控制
- 配置管理
- 流式响应支持

### 2. 装饰器系统

框架提供了四个主要装饰器：
- `@server.tool()` - 定义普通工具
- `@server.streaming_tool()` - 定义流式工具
- `@server.resource()` - 定义资源
- `@server.decorators.server_param()` - 定义服务器配置参数

### 3. 参数注解

#### 工具参数注解
使用 `typing.Annotated` 和框架提供的参数规范：
- `R("描述")` - 必需参数 (Required)
- `O("描述", default=value)` - 可选参数 (Optional)
- `E("描述", options=[...])` - 枚举参数 (Enum)
- `IntRange("描述", min=0, max=100)` - 整数范围参数

#### 服务器参数注解
用于定义服务器配置参数：
- `StringParam("显示名", "描述")` - 字符串配置参数
- `SelectParam("显示名", "描述", options=[...])` - 选择配置参数
- `BooleanParam("显示名", "描述")` - 布尔配置参数
- `PathParam("显示名", "描述")` - 路径配置参数

## 🚀 简化启动器

MCP Framework 提供了 `SimpleLauncher` 类和相关便捷函数，大大简化了服务器的启动流程。无需编写复杂的命令行参数解析和启动逻辑，只需一行代码即可启动服务器。

### 1. 使用 simple_main 函数（推荐）

最简单的服务器启动方式：

```python
#!/usr/bin/env python3
from mcp_framework import EnhancedMCPServer, simple_main
from mcp_framework.core.decorators import R
from typing_extensions import Annotated

# 创建服务器实例
server = EnhancedMCPServer(
    name="my-simple-server",
    version="1.0.0",
    description="使用简化启动器的服务器"
)

@server.tool("问候")
async def greet(name: Annotated[str, R("姓名")]):
    """向用户问候"""
    return f"你好，{name}！"

@server.tool("计算")
async def calculate(
    a: Annotated[float, R("第一个数字")],
    b: Annotated[float, R("第二个数字")]
):
    """计算两个数字的和"""
    return a + b

if __name__ == "__main__":
    # 一行代码启动服务器！
    simple_main(server, "MySimpleServer")
```

### 2. 支持的启动模式

简化启动器支持三种运行模式，每种模式都有详细的启动命令：

#### Stdio 模式（标准输入输出）
```bash
# 基本启动
python my_server.py stdio

# 带别名启动（推荐）
python my_server.py stdio --alias my_server

# 实际示例
python simple_server_example.py stdio --alias simple_test
python simple_stdio_server.py stdio --alias stdio_demo
```

**Stdio 模式特点：**
- 通过标准输入输出与客户端通信
- 适合与 MCP 客户端（如 Claude Desktop）集成
- 轻量级，资源占用少
- 支持流式响应

#### HTTP 模式（Web API）
```bash
# 基本启动（指定端口）
python my_server.py http 8080

# 带别名启动（推荐）
python my_server.py http 8080 --alias my_http_server

# 实际示例
python simple_server_example.py http 8080 --alias simple_http
python file_write_server.py http 9000 --alias file_server
```

**HTTP 模式特点：**
- 提供 RESTful API 接口
- 支持 Web 浏览器访问
- 内置管理界面（设置、测试、配置页面）
- 支持跨域请求
- 适合 Web 应用集成

**HTTP 模式访问地址：**
```
http://localhost:8080/          # 主页
http://localhost:8080/setup     # 设置页面
http://localhost:8080/test      # 测试页面
http://localhost:8080/config    # 配置页面
http://localhost:8080/tools/list # 工具列表 API
```

#### Dual 模式（双重支持）
```bash
# 基本启动
python my_server.py dual 8080

# 带别名启动（推荐）
python my_server.py dual 8080 --alias my_dual_server

# 实际示例
python simple_server_example.py dual 8080 --alias dual_demo
```

**Dual 模式特点：**
- 同时支持 Stdio 和 HTTP 两种通信方式
- 一个服务器实例，两种访问方式
- 适合需要多种客户端接入的场景

### 3. SimpleLauncher 类详解

如果需要更多控制，可以直接使用 `SimpleLauncher` 类：

```python
from mcp_framework.core.simple_launcher import SimpleLauncher

# 方式1：创建实例并运行
launcher = SimpleLauncher(server, "MyServer")
launcher.run()

# 方式2：快速启动
SimpleLauncher.quick_start(server, "MyServer")
```

### 4. 启动命令快速参考

#### 常用启动命令模板

| 模式 | 命令模板 | 说明 |
|------|----------|------|
| **Stdio** | `python server.py stdio --alias <别名>` | 标准输入输出模式 |
| **HTTP** | `python server.py http <端口> --alias <别名>` | Web API 模式 |
| **Dual** | `python server.py dual <端口> --alias <别名>` | 双重模式 |

#### 实际启动命令示例

```bash
# === Stdio 模式启动 ===
python simple_server_example.py stdio --alias demo
python simple_stdio_server.py stdio --alias stdio_test
python file_write_server.py stdio --alias file_ops

# === HTTP 模式启动 ===
python simple_server_example.py http 8080 --alias web_demo
python simple_stdio_server.py http 9000 --alias web_stdio
python file_write_server.py http 8888 --alias web_files

# === Dual 模式启动 ===
python simple_server_example.py dual 8080 --alias full_demo
python simple_stdio_server.py dual 9000 --alias full_stdio
python file_write_server.py dual 8888 --alias full_files

# === 不带别名启动（不推荐） ===
python simple_server_example.py stdio
python simple_server_example.py http 8080
python simple_server_example.py dual 8080
```

#### 启动后验证

```bash
# Stdio 模式验证（通过客户端）
python simple_client_examples.py

# HTTP 模式验证（通过浏览器或curl）
curl http://localhost:8080/tools/list
curl http://localhost:8080/setup

# 查看运行状态
cat running_instances.json
```

### 5. 命令行参数说明

简化启动器自动处理以下命令行参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `mode` | 运行模式：stdio/http/dual | `stdio` |
| `port` | 端口号（http/dual模式必需） | `8080` |
| `--name` | 服务器名称 | `--name MyServer` |
| `--alias` | 服务器别名 | `--alias my_server` |

### 6. 与传统启动方式对比

#### 传统方式（复杂）
```python
import sys
import argparse
from mcp_framework.core.multi_launcher import run_stdio_server_main, run_http_server_main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--alias')
    args = parser.parse_args()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'http':
        run_http_server_main(server, default_port=args.port, alias=args.alias)
    else:
        run_stdio_server_main(server, alias=args.alias)

if __name__ == "__main__":
    main()
```

#### 简化方式（推荐）
```python
from mcp_framework import simple_main

if __name__ == "__main__":
    simple_main(server, "MyServer")
```

### 7. 便捷函数

框架还提供了其他便捷函数：

```python
from mcp_framework import run_server, start_server

# 这些都是 simple_main 的别名
run_server(server, "MyServer")
start_server(server, "MyServer")
```

### 8. 自动功能

简化启动器自动提供：
- ✅ 命令行参数解析
- ✅ 多种运行模式支持
- ✅ 错误处理和验证
- ✅ 启动信息显示
- ✅ 配置管理集成
- ✅ 别名支持

## 🌐 HTTP 服务器模式

### 启动HTTP服务器

```python
from mcp_framework import EnhancedMCPServer, run_server_main

server = EnhancedMCPServer(
    name="http-server-example",
    version="1.0.0"
)

# 定义工具...

if __name__ == "__main__":
    run_server_main(
        server_instance=server,
        server_name="HTTPServer",
        default_port=8080
    )
```

### HTTP API 调用

启动后可以通过以下方式调用：

```bash
# 获取工具列表
curl http://localhost:8080/tools/list

# 调用工具
curl -X POST http://localhost:8080/tool/call \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "add_numbers",
       "arguments": {"a": 10, "b": 20}
     }'

# 流式工具调用
curl -X POST http://localhost:8080/sse/tool/call \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{
       "tool_name": "streaming_tool_name",
       "arguments": {...}
     }'
```

### Web 界面

框架提供了内置的Web界面：
- **配置页面**: http://localhost:8080/config
- **测试页面**: http://localhost:8080/test
- **设置页面**: http://localhost:8080/setup
- **健康检查**: http://localhost:8080/health

## 📡 Stdio 集成方式

### 1. 创建 Stdio 服务器

#### 方式一：使用 run_stdio_server_main（推荐）

```python
#!/usr/bin/env python3
"""
文件操作服务器 - Stdio 模式示例
使用 run_stdio_server_main 简化启动流程
"""
from mcp_framework import EnhancedMCPServer
from mcp_framework.core.multi_launcher import run_stdio_server_main
from mcp_framework.core.decorators import R, O, E, IntRange, StringParam, SelectParam, BooleanParam, PathParam
from typing import Annotated
import sys
import asyncio


# 创建服务器实例
server = EnhancedMCPServer(
    name="simple-stdio-server",
    version="1.0.0",
    description="简单的 Stdio 模式 MCP 服务器示例"
)

# 定义工具
@server.tool("问候")
async def greet(
    name: Annotated[str, R("姓名")]
) -> str:
    """向用户问候"""
    return f"你好，{name}！欢迎使用 MCP 服务器！"

@server.tool("计算")
async def calculate(
    operation: Annotated[str, E("运算类型", ["add", "sub", "mul", "div"])],
    a: Annotated[float, R("第一个数字")],
    b: Annotated[float, R("第二个数字")]
) -> str:
    """执行基本数学运算"""
    try:
        if operation == "add":
            result = a + b
        elif operation == "sub":
            result = a - b
        elif operation == "mul":
            result = a * b
        elif operation == "div":
            if b == 0:
                return "错误：除数不能为零"
            result = a / b
        else:
            return "错误：不支持的运算类型"
        
        return f"{a} {operation} {b} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@server.streaming_tool("倒计时")
async def countdown(
    start: Annotated[int, IntRange("起始数字", min_val=1, max_val=10)] = 5
):
    """流式倒计时"""
    for i in range(start, 0, -1):
        yield f"⏰ {i}..."
        await asyncio.sleep(1)
    yield "🎉 时间到！"

@server.tool("用户信息处理")
def process_user_info(
    name: Annotated[str, R("用户姓名", "请输入用户的真实姓名")],
    age: Annotated[int, IntRange("年龄", min_val=0, max_val=150)],
    email: Annotated[str, O("邮箱地址", "可选的邮箱地址")] = None,
    gender: Annotated[str, E("性别", ["男", "女", "其他"])] = "其他",
    is_vip: Annotated[bool, O("VIP状态", "是否为VIP用户")] = False,
    tags: Annotated[str, O("标签", "用逗号分隔的标签列表")] = ""
):
    """处理用户信息的综合示例，展示各种参数类型"""
    result = f"用户信息：\n"
    result += f"姓名：{name}\n"
    result += f"年龄：{age}岁\n"
    
    if email:
        result += f"邮箱：{email}\n"
    
    result += f"性别：{gender}\n"
    result += f"VIP状态：{'是' if is_vip else '否'}\n"
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        result += f"标签：{', '.join(tag_list)}\n"
    
    return result

@server.tool("文件配置")
def configure_file(
    file_path: Annotated[str, R("文件路径", "要配置的文件路径")],
    encoding: Annotated[str, E("文件编码", ["utf-8", "gbk", "ascii"])] = "utf-8",
    max_size_mb: Annotated[int, IntRange("最大文件大小(MB)", min_val=1, max_val=100)] = 10,
    backup: Annotated[bool, O("是否备份", "处理前是否创建备份")] = True,
    comment: Annotated[str, O("备注信息", "可选的备注信息")] = None
):
    """文件配置示例，展示实际应用场景中的参数组合"""
    config = {
        "文件路径": file_path,
        "编码格式": encoding,
        "最大大小": f"{max_size_mb}MB",
        "自动备份": "启用" if backup else "禁用"
    }
    
    if comment:
        config["备注"] = comment
    
    result = "文件配置信息：\n"
    for key, value in config.items():
        result += f"- {key}：{value}\n"
    
    return result

# 服务器参数配置示例
@server.decorators.server_param("api_key")
async def api_key_param(
    param: Annotated[str, StringParam(
        display_name="API 密钥",
        description="用于访问外部服务的 API 密钥",
        placeholder="请输入您的 API 密钥",
        required=True
    )]
):
    """API 密钥配置参数"""
    pass

@server.decorators.server_param("model_type")
async def model_param(
    param: Annotated[str, SelectParam(
        display_name="AI 模型类型",
        description="选择要使用的 AI 模型",
        options=["gpt-3.5-turbo", "gpt-4", "claude-3", "local-model"],
        default_value="gpt-3.5-turbo"
    )]
):
    """AI 模型选择参数"""
    pass

@server.decorators.server_param("enable_debug")
async def debug_param(
    param: Annotated[bool, BooleanParam(
        display_name="启用调试模式",
        description="是否启用详细的调试日志输出",
        default_value=False
    )]
):
    """调试模式开关参数"""
    pass

@server.decorators.server_param("work_directory")
async def work_dir_param(
    param: Annotated[str, PathParam(
        display_name="工作目录",
        description="服务器的工作根目录路径",
        placeholder="/path/to/workspace",
        required=False,
        default_value="."
    )]
):
    """工作目录路径参数"""
    pass


def main():
    """主函数"""
    # 解析命令行参数
    alias = None
    
    # 支持两种格式：
    # 1. python server.py stdio --alias test
    # 2. python server.py --alias test
    if len(sys.argv) > 1:
        if sys.argv[1] == "stdio" and len(sys.argv) > 3 and sys.argv[2] == "--alias":
            alias = sys.argv[3]
        elif sys.argv[1] == "--alias" and len(sys.argv) > 2:
            alias = sys.argv[2]
    
    # 使用 run_stdio_server_main 启动（自动处理配置、异常等）
    run_stdio_server_main(
        server_instance=server,
        server_name="SimpleStdioServer",
        alias=alias
    )


if __name__ == "__main__":
    main()
```

### 📋 服务器参数配置说明

上面示例中的 `@server.decorators.server_param()` 装饰器用于定义服务器的配置参数。这些参数可以通过配置文件或 Web 界面进行设置：

#### 参数类型说明：

1. **StringParam** - 字符串参数
   - 用于 API 密钥、文件路径等文本配置
   - 支持 `placeholder`、`required`、`default_value` 等属性

2. **SelectParam** - 选择参数  
   - 用于从预定义选项中选择，如模型类型
   - 必须提供 `options` 列表

3. **BooleanParam** - 布尔参数
   - 用于开关类配置，如调试模式
   - 值为 `True` 或 `False`

4. **PathParam** - 路径参数
   - 专门用于文件或目录路径配置
   - 支持路径验证和自动补全

#### 配置文件位置：
```
~/.mcp_framework/configs/{server_name}_port_{port}_server_config.json
```

#### 在工具中使用配置：
```python
@server.tool("使用配置的工具")
def use_config_tool():
    # 获取配置值
    api_key = server.server_config.get("api_key")
    model_type = server.server_config.get("model_type", "gpt-3.5-turbo")
    debug_mode = server.server_config.get("enable_debug", False)
    work_dir = server.server_config.get("work_directory", ".")
    
    return f"配置信息：API密钥={'已设置' if api_key else '未设置'}，模型={model_type}，调试={debug_mode}，目录={work_dir}"
```

#### 方式二：直接使用 MCPStdioServer

```python
#!/usr/bin/env python3
"""
Stdio模式的MCP服务器示例
通过标准输入输出进行JSON-RPC通信
"""
import asyncio
from mcp_framework import EnhancedMCPServer
from mcp_framework.server import MCPStdioServer
from mcp_framework.core.decorators import Required
from typing_extensions import Annotated

# 创建服务器实例
server = EnhancedMCPServer(
    name="stdio-server",
    version="1.0.0",
    description="Stdio模式的MCP服务器"
)

@server.tool("echo")
async def echo_tool(message: Annotated[str, Required("要回显的消息")]):
    """回显消息工具"""
    return f"Echo: {message}"

@server.streaming_tool("count")
async def count_tool(max_count: Annotated[int, Required("计数上限")]):
    """流式计数工具"""
    for i in range(1, max_count + 1):
        yield f"Count: {i}"
        await asyncio.sleep(0.1)

@server.tool("get_server_info")
async def get_server_info():
    """获取服务器信息"""
    return {
        "name": server.name,
        "version": server.version,
        "description": server.description,
        "tools_count": len(server._tools)
    }

async def main():
    """Stdio模式主函数"""
    try:
        # 创建stdio服务器实例
        stdio_server = MCPStdioServer(server)
        
        # 启动服务器（这会阻塞直到服务器停止）
        await stdio_server.start()
        
    except KeyboardInterrupt:
        print("服务器被用户中断")
    except Exception as e:
        print(f"服务器启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 使用客户端 SDK 调用

```python
#!/usr/bin/env python3
import asyncio
from mcp_framework import EnhancedMCPStdioClient, ToolsClient

async def call_stdio_server():
    """调用stdio服务器示例"""
    
    # 方式1：使用增强版客户端（推荐）
    async with EnhancedMCPStdioClient(
        server_script="stdio_server.py",
        startup_timeout=5.0,
        debug_mode=False  # 可设置为True查看详细调试信息
    ) as client:
        # 获取工具列表
        tools = await client.send_request("tools/list")
        print(f"可用工具: {tools}")
        
        # 调用工具
        result = await client.send_request("tools/call", {
            "name": "echo",
            "arguments": {"message": "Hello, MCP!"}
        })
        print(f"调用结果: {result}")
    
    # 方式2：使用工具客户端（更简单）
    async with ToolsClient("stdio_server.py") as client:
        # 直接调用工具
        result = await client.call_tool("echo", {"message": "Hello, World!"})
        print(f"工具调用结果: {result}")
        
        # 流式工具调用
        async for chunk in client.call_tool_streaming("count", {"max_count": 5}):
            print(f"流式输出: {chunk}")

if __name__ == "__main__":
    asyncio.run(call_stdio_server())
```

### 3. 命令行调用

```bash
# 直接运行stdio服务器
python stdio_server.py

# 使用管道进行通信
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | python stdio_server.py

# 使用别名启动
python stdio_server.py --alias my_server
```

### 4. Stdio 通信协议详解

#### JSON-RPC 2.0 格式

MCP Framework 的 stdio 通信基于 JSON-RPC 2.0 协议：

```json
// 请求格式
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

// 响应格式
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "tools": [...]
    }
}

// 错误响应
{
    "jsonrpc": "2.0",
    "id": 1,
    "error": {
        "code": -32600,
        "message": "Invalid Request"
    }
}
```

#### 支持的方法

| 方法 | 描述 | 参数 |
|------|------|------|
| `initialize` | 初始化连接 | `{"protocolVersion": "2024-11-05", "capabilities": {...}}` |
| `tools/list` | 获取工具列表 | `{}` 或 `{"role": "角色名"}` |
| `tools/call` | 调用工具 | `{"name": "工具名", "arguments": {...}}` |
| `resources/list` | 获取资源列表 | `{}` |
| `resources/read` | 读取资源 | `{"uri": "资源URI"}` |
| `config/get` | 获取配置 | `{}` |
| `config/update` | 更新配置 | `{"key": "value", ...}` |

#### 流式调用

对于流式工具，可以使用特殊的流式调用格式：

```json
// 流式请求
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "streaming_tool",
        "arguments": {...},
        "stream": true
    }
}

// 流式响应（多个）
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "type": "tool_result_chunk",
        "tool": "streaming_tool",
        "content": "第一块数据",
        "is_final": false
    }
}
```

### 5. 高级 Stdio 集成模式

#### 与现有应用集成

```python
#!/usr/bin/env python3
"""
将MCP服务器集成到现有应用中
"""
import asyncio
import sys
from mcp_framework import EnhancedMCPServer
from mcp_framework.server import MCPStdioServer
from mcp_framework.core.decorators import Required
from typing_extensions import Annotated

# 假设这是你现有的业务逻辑类
class BusinessLogic:
    def __init__(self):
        self.data = {"users": [], "orders": []}
    
    def get_users(self):
        return self.data["users"]
    
    def create_user(self, name, email):
        user = {"id": len(self.data["users"]) + 1, "name": name, "email": email}
        self.data["users"].append(user)
        return user

# 创建MCP服务器并集成业务逻辑
class IntegratedMCPServer(EnhancedMCPServer):
    def __init__(self):
        super().__init__(
            name="integrated-server",
            version="1.0.0",
            description="集成现有业务逻辑的MCP服务器"
        )
        self.business = BusinessLogic()
    
    async def initialize(self):
        """服务器初始化"""
        await super().initialize()
        self.logger.info("业务逻辑已集成")

# 创建服务器实例
server = IntegratedMCPServer()

# 定义MCP工具，调用业务逻辑
@server.tool("获取用户列表")
async def get_users():
    """获取所有用户"""
    return server.business.get_users()

@server.tool("创建用户")
async def create_user(
    name: Annotated[str, Required("用户名")],
    email: Annotated[str, Required("邮箱地址")]
):
    """创建新用户"""
    return server.business.create_user(name, email)

async def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # Stdio模式
        stdio_server = MCPStdioServer(server)
        await stdio_server.start()
    else:
        # HTTP模式
        from mcp_framework import run_server_main
        run_server_main(server, "IntegratedServer", 8080)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 多进程 Stdio 服务器

```python
#!/usr/bin/env python3
"""
多进程stdio服务器示例
支持同时处理多个客户端连接
"""
import asyncio
import multiprocessing
import sys
from mcp_framework import EnhancedMCPServer
from mcp_framework.server import MCPStdioServer

def create_server():
    """创建服务器实例"""
    server = EnhancedMCPServer(
        name="multi-process-server",
        version="1.0.0"
    )
    
    @server.tool("获取进程ID")
    async def get_process_id():
        import os
        return f"进程ID: {os.getpid()}"
    
    return server

async def stdio_worker():
    """Stdio工作进程"""
    server = create_server()
    stdio_server = MCPStdioServer(server)
    await stdio_server.start()

def start_stdio_process():
    """启动stdio进程"""
    asyncio.run(stdio_worker())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        # 启动多个stdio进程
        processes = []
        for i in range(3):
            p = multiprocessing.Process(target=start_stdio_process)
            p.start()
            processes.append(p)
            print(f"启动stdio进程 {i+1}: PID {p.pid}")
        
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            for p in processes:
                p.terminate()
    else:
        # 单进程模式
        asyncio.run(stdio_worker())
```

### 6. Stdio 调试和监控

#### 调试模式

```python
#!/usr/bin/env python3
"""
Stdio调试模式
"""
import asyncio
import json
import sys
from mcp_framework import EnhancedMCPServer
from mcp_framework.server import MCPStdioServer

class DebugMCPStdioServer(MCPStdioServer):
    """带调试功能的Stdio服务器"""
    
    async def _handle_request(self, request):
        """重写请求处理，添加调试信息"""
        self.logger.info(f"收到请求: {json.dumps(request, ensure_ascii=False)}")
        
        try:
            result = await super()._handle_request(request)
            self.logger.info(f"响应结果: {json.dumps(result, ensure_ascii=False)}")
            return result
        except Exception as e:
            self.logger.error(f"请求处理失败: {e}")
            raise

# 使用调试服务器
server = EnhancedMCPServer("debug-server", "1.0.0")

@server.tool("测试工具")
async def test_tool(data: str):
    return f"处理数据: {data}"

async def main():
    debug_server = DebugMCPStdioServer(server)
    await debug_server.start()

if __name__ == "__main__":
    # 设置调试日志级别
    import logging
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
```

#### 性能监控

```python
#!/usr/bin/env python3
"""
Stdio性能监控
"""
import asyncio
import time
from mcp_framework import EnhancedMCPServer
from mcp_framework.server import MCPStdioServer

class MonitoredMCPServer(EnhancedMCPServer):
    """带性能监控的MCP服务器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            "total_requests": 0,
            "total_time": 0,
            "tool_calls": {}
        }
    
    async def handle_tool_call(self, tool_name, arguments):
        """重写工具调用，添加性能统计"""
        start_time = time.time()
        
        try:
            result = await super().handle_tool_call(tool_name, arguments)
            
            # 更新统计信息
            elapsed = time.time() - start_time
            self.stats["total_requests"] += 1
            self.stats["total_time"] += elapsed
            
            if tool_name not in self.stats["tool_calls"]:
                self.stats["tool_calls"][tool_name] = {"count": 0, "total_time": 0}
            
            self.stats["tool_calls"][tool_name]["count"] += 1
            self.stats["tool_calls"][tool_name]["total_time"] += elapsed
            
            self.logger.info(f"工具 {tool_name} 执行时间: {elapsed:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"工具 {tool_name} 执行失败: {e}")
            raise

# 创建监控服务器
server = MonitoredMCPServer("monitored-server", "1.0.0")

@server.tool("获取性能统计")
async def get_stats():
    """获取服务器性能统计"""
    stats = server.stats.copy()
    if stats["total_requests"] > 0:
        stats["avg_time"] = stats["total_time"] / stats["total_requests"]
    return stats

@server.tool("重置统计")
async def reset_stats():
    """重置性能统计"""
    server.stats = {
        "total_requests": 0,
        "total_time": 0,
        "tool_calls": {}
    }
    return "统计已重置"

async def main():
    stdio_server = MCPStdioServer(server)
    await stdio_server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎨 装饰器 API

### 工具定义

```python
# 基础工具
@server.tool("工具名称")
async def my_tool(param: Annotated[str, Required("参数描述")]):
    return "结果"

# 流式工具
@server.streaming_tool("流式工具")
async def streaming_tool(data: Annotated[str, Required("数据")]):
    for chunk in process_data(data):
        yield chunk

# 角色限制工具
@server.tool("管理员工具", role="admin")
async def admin_tool():
    return "只有管理员可以使用"

@server.tool("多角色工具", role=["user", "admin"])
async def multi_role_tool():
    return "用户和管理员都可以使用"
```

### 资源定义

```python
@server.resource("file://config.json")
async def config_resource():
    """配置文件资源"""
    return {
        "content": "配置内容",
        "mimeType": "application/json"
    }
```

### 服务器参数

```python
from mcp_framework.core.decorators import SelectParam, PathParam

@server.decorators.server_param("model_type")
async def model_param(
    param: Annotated[str, SelectParam(
        display_name="模型类型",
        description="选择要使用的 AI 模型",
        options=["gpt-3.5-turbo", "gpt-4", "claude-3"]
    )]
):
    """模型类型参数"""
    pass

@server.decorators.server_param("project_root")
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

## ⚙️ 配置管理

### 自动配置

框架支持自动配置管理：

```python
# 服务器会自动加载配置文件
server = EnhancedMCPServer(
    name="auto-config-server",
    version="1.0.0"
)

# 配置文件位置：
# ~/.mcp_framework/configs/auto-config-server_port_8080_server_config.json
```

### 手动配置

```python
from mcp_framework.core.config import ServerConfig, ServerConfigManager

# 创建配置
config = ServerConfig(
    name="my-server",
    version="1.0.0",
    port=8080,
    host="0.0.0.0"
)

# 使用配置管理器
config_manager = ServerConfigManager("my-server", 8080)
config_manager.save_server_config(config)

# 在服务器中使用
server = EnhancedMCPServer(
    name="my-server",
    version="1.0.0",
    config_manager=config_manager
)
```

## 📱 客户端 SDK

### EnhancedMCPStdioClient - 增强版客户端（推荐）

```python
from mcp_framework import EnhancedMCPStdioClient

async with EnhancedMCPStdioClient(
    server_script="server.py",
    alias="my_server",
    startup_timeout=5.0,
    debug_mode=False  # 可设置为True查看详细调试信息
) as client:
    # 发送原始请求
    response = await client.send_request("tools/list")
    
    # 调用工具
    result = await client.send_request("tools/call", {
        "name": "tool_name",
        "arguments": {"param": "value"}
    })
```

### ToolsClient - 工具专用客户端

```python
from mcp_framework import ToolsClient

async with ToolsClient("server.py") as client:
    # 获取工具列表
    tools = await client.list_tools()
    
    # 调用工具
    result = await client.call_tool("tool_name", {"param": "value"})
    
    # 流式调用
    async for chunk in client.call_tool_streaming("streaming_tool", params):
        print(chunk)
```

### ConfigClient - 配置专用客户端

```python
from mcp_framework import ConfigClient

async with ConfigClient("server.py") as client:
    # 获取配置
    config = await client.get_config()
    
    # 更新配置
    await client.update_config({"key": "value"})
```

## 🎯 简化客户端

MCP Framework 提供了 `SimpleClient` 类，这是一个统一的简化客户端接口，整合了工具调用和配置管理功能，让客户端使用变得极其简单。

> **🆕 最新更新**: `SimpleClient` 现已支持流式工具调用！可以实时获取长时间运行任务的输出，提供更好的用户体验。支持异步流式调用 `call_stream()`、快速流式调用 `quick_call_stream()` 和同步流式调用 `sync_call_stream()`。

### 📋 简化客户端功能目录

1. [SimpleClient 基础用法](#1-simpleclient-基础用法)
2. [快速函数（一行代码调用）](#2-快速函数一行代码调用)
3. [同步版本（无需 async/await）](#3-同步版本无需-asyncawait)
4. [带别名的服务器调用](#4-带别名的服务器调用)
5. [完整的客户端示例](#5-完整的客户端示例)
6. [错误处理](#6-错误处理)
7. [流式工具调用](#7-流式工具调用) ⭐ **新功能**
   - [基础流式调用](#71-基础流式调用)
   - [快速流式调用](#72-快速流式调用)
   - [同步流式调用](#73-同步流式调用)
   - [流式调用的错误处理](#74-流式调用的错误处理)
   - [流式调用的实际应用场景](#75-流式调用的实际应用场景)
   - [流式调用 vs 普通调用的选择](#76-流式调用-vs-普通调用的选择)
   - [完整示例](#77-完整示例)
8. [与其他客户端的对比](#8-与其他客户端的对比)
9. [最佳实践](#9-最佳实践)

### 1. SimpleClient 基础用法

最简单的客户端使用方式：

```python
#!/usr/bin/env python3
import asyncio
from mcp_framework.client.simple import SimpleClient

async def main():
    # 创建简化客户端
    async with SimpleClient("my_server.py") as client:
        # 获取所有工具
        tools = await client.tools()
        print(f"可用工具: {tools}")
        
        # 调用工具（最简单的方式）
        result = await client.call("greet", name="张三")
        print(f"问候结果: {result}")
        
        # 获取配置
        config = await client.config()
        print(f"当前配置: {config}")
        
        # 设置配置
        await client.set("api_key", "your-api-key")
        
        # 批量更新配置
        await client.update(
            model_type="gpt-4",
            enable_debug=True
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 快速函数（一行代码调用）

对于简单的一次性调用，可以使用快速函数：

```python
import asyncio
from mcp_framework.client.simple import quick_call, quick_get, quick_set, quick_update, quick_tools

async def demo():
    # 快速调用工具
    result = await quick_call("server.py", "calculate", a=10, b=20)
    print(f"计算结果: {result}")
    
    # 快速获取配置
    api_key = await quick_get("server.py", "api_key", default="未设置")
    print(f"API密钥: {api_key}")
    
    # 快速设置配置
    success = await quick_set("server.py", "model_type", "gpt-4")
    print(f"设置成功: {success}")
    
    # 快速批量更新配置
    success = await quick_update("server.py", 
                                model_type="gpt-4", 
                                max_tokens=2048, 
                                temperature=0.7)
    print(f"批量更新成功: {success}")
    
    # 快速获取工具列表
    tools = await quick_tools("server.py")
    print(f"工具列表: {tools}")

asyncio.run(demo())
```

### 3. 同步版本（无需 async/await）

对于不想使用异步的场景，提供了同步版本：

```python
from mcp_framework.client.simple import sync_call, sync_get, sync_set, sync_update, sync_tools

# 同步调用工具
result = sync_call("server.py", "greet", name="李四")
print(f"问候结果: {result}")

# 同步获取配置
config_value = sync_get("server.py", "api_key", default="默认值")
print(f"配置值: {config_value}")

# 同步设置配置
success = sync_set("server.py", "enable_debug", True)
print(f"设置成功: {success}")

# 同步批量更新配置
success = sync_update("server.py", 
                     model_type="gpt-4", 
                     max_tokens=2048, 
                     temperature=0.7)
print(f"批量更新成功: {success}")

# 同步获取工具列表
tools = sync_tools("server.py")
print(f"可用工具: {tools}")
```

### 4. 带别名的服务器调用

如果服务器使用了别名，可以这样调用：

```python
import asyncio
from mcp_framework.client.simple import SimpleClient, quick_call

async def main():
    # 使用别名的客户端
    async with SimpleClient("server.py", alias="my_server") as client:
        result = await client.call("tool_name", param="value")
        print(result)
    
    # 快速调用也支持别名
    result = await quick_call("server.py", "tool_name", alias="my_server", param="value")
    print(result)

asyncio.run(main())
```

### 5. 完整的客户端示例

```python
#!/usr/bin/env python3
"""
简化客户端完整示例
演示所有主要功能
"""
import asyncio
from mcp_framework.client.simple import SimpleClient

async def comprehensive_example():
    """完整的客户端使用示例"""
    
    async with SimpleClient("simple_server_example.py", alias="demo") as client:
        print("=== 工具相关操作 ===")
        
        # 1. 获取工具列表
        tools = await client.tools()
        print(f"可用工具: {tools}")
        
        # 2. 检查工具是否存在
        has_greet = await client.has_tool("greet")
        print(f"是否有greet工具: {has_greet}")
        
        # 3. 获取工具信息
        tool_info = await client.tool_info("greet")
        if tool_info:
            print(f"greet工具信息: {tool_info.description}")
        
        # 4. 调用工具
        if has_greet:
            result = await client.call("greet", name="简化客户端用户")
            print(f"问候结果: {result}")
        
        print("\n=== 配置相关操作 ===")
        
        # 5. 获取当前配置
        config = await client.config()
        print(f"当前配置: {config}")
        
        # 6. 获取特定配置项
        api_key = await client.get("api_key", "未设置")
        print(f"API密钥: {api_key}")
        
        # 7. 设置配置项
        await client.set("test_key", "test_value")
        print("设置了测试配置项")
        
        # 8. 批量更新配置
        update_success = await client.update(
            model_type="gpt-4",
            enable_debug=True,
            max_tokens=1000
        )
        print(f"批量更新配置成功: {update_success}")
        
        # 9. 验证配置更新
        updated_config = await client.config()
        print(f"更新后的配置: {updated_config}")

if __name__ == "__main__":
    asyncio.run(comprehensive_example())
```

### 6. 错误处理

简化客户端内置了错误处理机制：

```python
import asyncio
from mcp_framework.client.simple import SimpleClient

async def error_handling_example():
    try:
        async with SimpleClient("non_existent_server.py") as client:
            result = await client.call("some_tool")
    except Exception as e:
        print(f"客户端错误: {e}")
    
    # 配置操作的错误处理是静默的，返回默认值或False
    async with SimpleClient("server.py") as client:
        # 如果配置获取失败，返回默认值
        value = await client.get("non_existent_key", "default")
        print(f"配置值: {value}")  # 输出: default
        
        # 如果配置设置失败，返回False
        success = await client.set("key", "value")
        print(f"设置成功: {success}")  # 可能输出: False

asyncio.run(error_handling_example())
```

### 7. 流式工具调用

`SimpleClient` 支持流式工具调用，可以实时获取工具执行过程中的输出内容：

#### 7.1 基础流式调用

```python
import asyncio
from mcp_framework.client.simple import SimpleClient

async def streaming_example():
    """流式工具调用示例"""
    
    async with SimpleClient("simple_stdio_server.py", alias="demo") as client:
        print("=== 流式工具调用 ===")
        
        # 调用流式工具，实时获取输出
        print("开始倒计时:")
        async for chunk in client.call_stream("countdown", start=5):
            print(chunk, end="", flush=True)
        print("\n倒计时完成！")
        
        # 调用其他流式工具
        print("\n生成文本:")
        async for chunk in client.call_stream("generate_text", 
                                            prompt="写一首关于春天的诗", 
                                            max_length=100):
            print(chunk, end="", flush=True)
        print("\n文本生成完成！")

if __name__ == "__main__":
    asyncio.run(streaming_example())
```

#### 7.2 快速流式调用

对于一次性的流式调用，可以使用快速函数：

```python
import asyncio
from mcp_framework.client.simple import quick_call_stream

async def quick_streaming_demo():
    """快速流式调用示例"""
    
    print("快速流式调用倒计时:")
    async for chunk in quick_call_stream("simple_stdio_server.py", 
                                       "countdown", 
                                       alias="demo",
                                       start=3):
        print(chunk, end="", flush=True)
    print("\n完成！")

asyncio.run(quick_streaming_demo())
```

#### 7.3 同步流式调用

对于不想使用异步的场景，提供了同步版本（会收集所有流式输出并返回完整结果）：

```python
from mcp_framework.client.simple import sync_call_stream

# 同步流式调用（收集完整输出）
result = sync_call_stream("simple_stdio_server.py", 
                         "countdown", 
                         alias="demo",
                         start=3)
print(f"完整输出: {result}")

# 带别名的同步流式调用
result = sync_call_stream("server.py", 
                         "generate_report", 
                         alias="my_server",
                         topic="月度销售报告",
                         format="markdown")
print(f"生成的报告: {result}")
```

#### 7.4 流式调用的错误处理

```python
import asyncio
from mcp_framework.client.simple import SimpleClient

async def streaming_error_handling():
    """流式调用的错误处理"""
    
    async with SimpleClient("server.py") as client:
        try:
            async for chunk in client.call_stream("non_existent_tool"):
                print(chunk, end="")
        except Exception as e:
            print(f"流式调用错误: {e}")
        
        # 处理流式调用中的部分错误
        try:
            content = ""
            async for chunk in client.call_stream("unstable_tool", param="value"):
                content += chunk
                print(chunk, end="", flush=True)
            print(f"\n完整内容: {content}")
        except Exception as e:
            print(f"\n流式调用中断: {e}")
            print(f"已接收内容: {content}")

asyncio.run(streaming_error_handling())
```

#### 7.5 流式调用的实际应用场景

```python
import asyncio
from mcp_framework.client.simple import SimpleClient

async def practical_streaming_examples():
    """流式调用的实际应用场景"""
    
    async with SimpleClient("ai_server.py", alias="ai") as client:
        
        # 场景1: 实时代码生成
        print("=== 实时代码生成 ===")
        async for chunk in client.call_stream("generate_code", 
                                            language="python",
                                            description="计算斐波那契数列"):
            print(chunk, end="", flush=True)
        
        # 场景2: 长文本翻译
        print("\n\n=== 长文本翻译 ===")
        long_text = "这是一段很长的中文文本..." * 100
        async for chunk in client.call_stream("translate_text",
                                            text=long_text,
                                            target_language="english"):
            print(chunk, end="", flush=True)
        
        # 场景3: 数据处理进度
        print("\n\n=== 数据处理进度 ===")
        async for chunk in client.call_stream("process_large_dataset",
                                            dataset_path="/path/to/data.csv",
                                            operation="analysis"):
            print(chunk, end="", flush=True)
        
        # 场景4: 实时日志输出
        print("\n\n=== 实时日志输出 ===")
        async for chunk in client.call_stream("run_system_command",
                                            command="ls -la",
                                            working_dir="/tmp"):
            print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(practical_streaming_examples())
```

#### 7.6 流式调用 vs 普通调用的选择

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| **快速响应的工具** | 普通调用 `call()` | 无需流式，简单直接 |
| **长时间运行的任务** | 流式调用 `call_stream()` | 实时反馈，用户体验好 |
| **大量文本生成** | 流式调用 `call_stream()` | 逐步显示，避免长时间等待 |
| **数据处理任务** | 流式调用 `call_stream()` | 显示进度，便于监控 |
| **简单查询** | 普通调用 `call()` | 结果简短，无需流式 |
| **AI对话生成** | 流式调用 `call_stream()` | 模拟打字效果，体验自然 |

#### 7.7 完整示例

更多流式功能的完整示例，请参考：
- `simple_streaming_client_example.py` - 包含所有流式功能的详细演示
- 涵盖基础流式调用、快速流式调用、同步流式调用
- 包含错误处理和实际应用场景示例
- 提供普通调用与流式调用的对比演示

### 8. 与其他客户端的对比

#### 传统方式（复杂）
```python
from mcp_framework import ToolsClient, ConfigClient

async def traditional_way():
    # 需要分别创建不同的客户端
    async with ToolsClient("server.py") as tools_client:
        tools = await tools_client.get_tool_names()
        result = await tools_client.call_tool("tool_name", {"param": "value"})
    
    async with ConfigClient("server.py") as config_client:
        config = await config_client.get_config()
        await config_client.set_config_value("key", "value")
```

#### 简化方式（推荐）
```python
from mcp_framework.client.simple import SimpleClient

async def simple_way():
    # 一个客户端搞定所有功能
    async with SimpleClient("server.py") as client:
        tools = await client.tools()
        result = await client.call("tool_name", param="value")
        config = await client.config()
        await client.set("key", "value")
```

### 9. 最佳实践

1. **使用上下文管理器**: 始终使用 `async with` 确保资源正确释放
2. **错误处理**: 工具调用可能抛出异常，配置操作会静默失败
3. **别名使用**: 为服务器设置有意义的别名，便于管理
4. **同步vs异步**: 在异步环境中使用异步版本，简单脚本可以使用同步版本
5. **一次性调用**: 对于简单的一次性操作，使用快速函数更方便
6. **流式调用选择**: 根据任务特性选择普通调用或流式调用，长时间任务优先使用流式
7. **流式输出处理**: 使用 `flush=True` 确保流式输出实时显示，适当添加错误处理
8. **性能考虑**: 流式调用适合大数据量或长时间任务，简单查询使用普通调用即可

## 🔧 高级示例

### 多角色权限控制

```python
#!/usr/bin/env python3
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required
from typing_extensions import Annotated

server = EnhancedMCPServer(
    name="multi-role-server",
    version="1.0.0",
    description="多角色权限控制示例"
)

@server.tool("规划任务", role="planner")
async def plan_task(task: Annotated[str, Required("要规划的任务")]):
    """规划任务 - 仅限planner角色"""
    return f"任务规划: {task}\n步骤: 1.分析需求 2.制定计划 3.分配资源"

@server.tool("执行任务", role=["executor", "manager"])
async def execute_task(task: Annotated[str, Required("要执行的任务")]):
    """执行任务 - executor和manager角色都可以使用"""
    return f"正在执行任务: {task}\n状态: 进行中\n预计完成时间: 30分钟"

@server.tool("获取状态")
async def get_status():
    """获取服务器状态 - 所有角色都可以使用"""
    return "服务器运行正常，所有功能可用"

if __name__ == "__main__":
    print("启动多角色测试服务器...")
    print("测试角色过滤:")
    print("- 获取planner角色工具: curl 'http://localhost:8080/tools/list?role=planner'")
    print("- 获取executor角色工具: curl 'http://localhost:8080/tools/list?role=executor'")
    
    run_server_main(
        server_instance=server,
        server_name="MultiRoleServer",
        default_port=8080
    )
```

### Flask 集成示例

```python
#!/usr/bin/env python3
from flask import Flask
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required
from typing_extensions import Annotated

# Flask 应用
flask_app = Flask(__name__)

@flask_app.route('/api/users')
def get_users():
    return {"users": ["user1", "user2"]}

# MCP 服务器
mcp_server = EnhancedMCPServer(
    name="flask-integrated-server",
    version="1.0.0",
    description="Flask集成的MCP服务器"
)

@mcp_server.tool("获取用户列表")
async def get_users_tool():
    """通过MCP获取用户列表"""
    # 这里可以调用Flask应用的逻辑
    return {"users": ["user1", "user2", "user3"]}

@mcp_server.tool("创建用户")
async def create_user_tool(
    username: Annotated[str, Required("用户名")],
    email: Annotated[str, Required("邮箱")]
):
    """创建新用户"""
    # 集成Flask应用的用户创建逻辑
    return f"用户 {username} 创建成功，邮箱: {email}"

if __name__ == "__main__":
    # 可以同时运行Flask和MCP服务器
    # 这里只启动MCP服务器作为示例
    run_server_main(
        server_instance=mcp_server,
        server_name="FlaskIntegratedServer",
        default_port=8080
    )
```


## 🔗 相关资源

- [MCP Framework GitHub](https://github.com/your-repo/mcp_framework)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [示例服务器集合](https://github.com/leeoohoo/mcp_servers)
- [开发指南](./MCP_SERVER_DEVELOPMENT_GUIDE.md)
- [安装指南](./INSTALL.md)

---

通过本指南，你应该能够快速上手 MCP Framework，构建功能强大的 MCP 服务器。框架提供了灵活的API设计，支持多种部署模式，能够满足不同场景的需求。