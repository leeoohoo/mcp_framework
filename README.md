# MCP Framework

一个强大且易用的 MCP (Model Context Protocol) 服务器开发框架，支持快速构建、部署和管理 MCP 服务器。

## 🚀 特性

### 核心功能
- **简单易用**: 基于装饰器的 API 设计，快速定义工具和资源
- **类型安全**: 完整的类型注解支持，自动生成 JSON Schema
- **流式支持**: 内置流式响应支持，适合大数据量处理
- **配置管理**: 灵活的配置系统，支持多端口配置
- **自动构建**: 集成 PyInstaller 构建系统，一键生成可执行文件

### 高级特性
- **多平台支持**: Windows、macOS、Linux 跨平台构建
- **依赖管理**: 智能依赖分析和打包
- **热重载**: 开发模式下支持代码热重载
- **日志系统**: 完整的日志记录和调试支持
- **Web 界面**: 内置配置和测试 Web 界面

## 📦 安装

### 从 PyPI 安装

```bash
pip install mcp-framework
```

### 从源码安装

```bash
git clone https://github.com/your-repo/mcp_framework.git
cd mcp_framework
pip install -e .
```

## 🎯 快速开始

### 1. 创建基础服务器

```python
#!/usr/bin/env python3
import asyncio
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required, Optional
from typing import Annotated


class MyMCPServer(EnhancedMCPServer):
    """我的第一个 MCP 服务器"""
    
    def __init__(self):
        super().__init__(
            name="MyMCPServer",
            version="1.0.0",
            description="我的第一个 MCP 服务器"
        )
        self._setup_tools()
    
    async def initialize(self):
        """初始化服务器"""
        self.logger.info("MyMCPServer 初始化完成")
    
    def _setup_tools(self):
        """设置工具和资源"""
        
        # 使用装饰器定义工具
        @self.tool("计算两个数的和")
        async def add_numbers(
            a: Annotated[int, Required("第一个数字")],
            b: Annotated[int, Required("第二个数字")]
        ) -> int:
            """计算两个数字的和"""
            return a + b
        
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
        
        # 定义资源
        @self.resource(
            uri="file://data.txt",
            name="示例数据",
            description="示例数据文件"
        )
        async def get_data():
            return {"content": "这是示例数据", "type": "text/plain"}


# 启动服务器
if __name__ == "__main__":
    server = MyMCPServer()
    run_server_main(
        server_instance=server,
        server_name="MyMCPServer",
        default_port=8080
    )
```

### 2. 运行服务器

```bash
python my_server.py --port 8080 --host localhost
```

## 📚 详细文档

### 装饰器 API

#### 工具装饰器

```python
# 在 _setup_tools 方法中定义工具
def _setup_tools(self):
    # 基础工具
    @self.tool("工具描述")
    async def my_tool(param1: str, param2: int) -> str:
        return f"处理结果: {param1} - {param2}"
    
    # 流式工具
    @self.streaming_tool("流式工具描述")
    async def my_streaming_tool(query: str):
        for i in range(10):
            yield f"处理步骤 {i}: {query}"
            await asyncio.sleep(0.1)
```

#### 参数类型注解

```python
from typing import List, Optional, AsyncGenerator
from typing_extensions import Annotated
from mcp_framework.core.decorators import (
    Required as R,
    Optional as O,
    IntRange,
    ServerParam,
    StringParam,
    BooleanParam,
    PathParam
)

# 在 _setup_tools 方法中定义
def _setup_tools(self):
    # 流式工具参数示例
    @self.streaming_tool(description="📖 **File Line Range Reader** - 流式读取文件指定行范围")
    async def read_file_lines(
        file_path: Annotated[str, R("文件路径（支持相对和绝对路径）")],
        start_line: Annotated[int, IntRange("起始行号（1-based）", min_val=1)],
        end_line: Annotated[int, IntRange("结束行号（1-based，包含）", min_val=1)]
    ) -> AsyncGenerator[str, None]:
        """流式读取文件指定行范围"""
        # 实现代码...
        yield "result"
    
    # 搜索工具参数示例
    @self.tool(description="🔍 **Content Search** - 搜索文件内容")
    async def search_files(
        query_text: Annotated[str, R("搜索关键词")],
        limit: Annotated[int, O("最大结果数量", default=50, minimum=1)] = 50,
        case_sensitive: Annotated[bool, O("是否区分大小写", default=False)] = False,
        file_extensions: Annotated[Optional[List[str]], O("文件扩展名列表，如 ['.py', '.js']")] = None
    ) -> dict:
        """搜索文件内容"""
        return {"results": []}
```

#### 资源装饰器

```python
import json

# 在 _setup_tools 方法中定义
def _setup_tools(self):
    @self.resource(
        uri="file://config.json",
        name="配置文件",
        description="服务器配置文件",
        mime_type="application/json"
    )
    async def get_config():
        return {
            "content": json.dumps({"setting1": "value1"}),
            "type": "application/json"
        }
```

### 服务器配置

#### 配置参数定义

```python
from mcp_framework.core.decorators import (
    ServerParam,
    StringParam,
    SelectParam,
    BooleanParam,
    PathParam
)
from typing import Annotated

# 在 _setup_tools 方法中定义
def _setup_tools(self):
    @self.decorators.server_param("api_key")
    async def api_key_param(
        param: Annotated[str, StringParam(
            display_name="API 密钥",
            description="用于访问外部服务的 API 密钥",
            placeholder="请输入 API 密钥"
        )]
    ):
        """API 密钥参数"""
        pass
    
    @self.decorators.server_param("model_type")
    async def model_param(
        param: Annotated[str, SelectParam(
            display_name="模型类型",
            description="选择要使用的 AI 模型",
            options=["gpt-3.5-turbo", "gpt-4", "claude-3"]
        )]
    ):
        """模型类型参数"""
        pass
    
    @self.decorators.server_param("project_root")
    async def project_root_param(
        param: Annotated[str, PathParam(
            display_name="项目根目录",
            description="服务器操作的根目录路径，留空使用当前目录",
            required=False,
            placeholder="/path/to/project"
        )]
    ):
        """项目根目录参数"""
        pass
    
    @self.decorators.server_param("max_file_size")
    async def max_file_size_param(
        param: Annotated[int, ServerParam(
            display_name="最大文件大小 (MB)",
            description="允许读取的最大文件大小，单位MB",
            param_type="integer",
            default_value=10,
            required=False
        )]
    ):
        """最大文件大小参数"""
        pass
    
    @self.decorators.server_param("enable_hidden_files")
    async def enable_hidden_files_param(
        param: Annotated[bool, BooleanParam(
            display_name="启用隐藏文件",
            description="是否允许访问以点(.)开头的隐藏文件",
            default_value=False,
            required=False
        )]
    ):
        """启用隐藏文件参数
        
        这个装饰器的作用：
        1. 定义一个名为 'enable_hidden_files' 的服务器配置参数
        2. 参数类型为布尔值（BooleanParam）
        3. 在Web配置界面中显示为"启用隐藏文件"选项
        4. 用户可以通过配置界面或配置文件设置此参数
        5. 在工具函数中可通过 self.get_config_value("enable_hidden_files") 获取值
        
        参数说明：
        - display_name: 在配置界面显示的友好名称
        - description: 参数的详细说明
        - default_value: 默认值（False表示默认不启用隐藏文件）
        - required: 是否为必需参数（False表示可选）
        """
        pass
```

#### 配置使用

```python
from mcp_framework.core.decorators import Required
from typing import Annotated

# 在 _setup_tools 方法中定义
def _setup_tools(self):
    @self.tool("使用配置的工具")
    async def configured_tool(query: Annotated[str, Required("查询内容")]):
        # 获取配置值
        api_key = self.get_config_value("api_key")
        model_type = self.get_config_value("model_type", "gpt-3.5-turbo")
        enable_hidden = self.get_config_value("enable_hidden_files", False)
        
        # 使用配置进行处理
        result = f"使用 {model_type} 处理查询: {query}"
        if enable_hidden:
            result += " (包含隐藏文件)"
        return result
```

#### 服务器参数装饰器详解

服务器参数装饰器 `@self.decorators.server_param()` 是 MCP Framework 的核心功能之一，它允许你为服务器定义可配置的参数。

**工作原理：**

1. **参数定义阶段**：使用装饰器定义参数的元数据（名称、类型、默认值等）
2. **配置收集阶段**：框架自动生成配置界面，用户可以设置参数值
3. **运行时使用**：在工具函数中通过 `self.get_config_value()` 获取用户设置的值

**完整示例：**

```python
# 1. 定义参数（在 _setup_tools 方法中）
@self.decorators.server_param("enable_hidden_files")
async def enable_hidden_files_param(
    param: Annotated[bool, BooleanParam(
        display_name="启用隐藏文件",
        description="是否允许访问以点(.)开头的隐藏文件",
        default_value=False,
        required=False
    )]
):
    """定义是否启用隐藏文件的配置参数"""
    pass

# 2. 在工具中使用参数
@self.tool("列出文件")
async def list_files(directory: Annotated[str, Required("目录路径")]):
    # 获取用户配置的参数值
    show_hidden = self.get_config_value("enable_hidden_files", False)
    
    files = []
    for file in os.listdir(directory):
        # 根据配置决定是否包含隐藏文件
        if not show_hidden and file.startswith('.'):
            continue
        files.append(file)
    
    return {"files": files, "show_hidden": show_hidden}
```

**参数类型支持：**

- `StringParam`: 字符串参数
- `BooleanParam`: 布尔参数
- `SelectParam`: 选择参数（下拉菜单）
- `PathParam`: 路径参数
- `ServerParam`: 通用参数（可指定类型）

**配置文件生成：**

框架会自动生成配置文件（如 `server_port_8080_config.json`），用户的设置会保存在其中：

```json
{
  "enable_hidden_files": true,
  "api_key": "your-api-key",
  "model_type": "gpt-4"
}
```

### 多端口配置

框架支持为不同端口创建独立的配置文件：

```bash
# 在不同端口启动服务器，会自动创建对应的配置文件
python server.py --port 8080  # 创建 server_port_8080_config.json
python server.py --port 8081  # 创建 server_port_8081_config.json
```

## 🔨 构建系统

框架集成了强大的构建系统，支持将 MCP 服务器打包为独立的可执行文件。

### 构建功能特性

- **自动发现**: 自动发现项目中的所有服务器脚本
- **依赖分析**: 智能分析和收集依赖包
- **多平台构建**: 支持 Windows、macOS、Linux
- **虚拟环境隔离**: 为每个服务器创建独立的构建环境
- **完整打包**: 生成包含所有依赖的分发包

### 使用构建系统

#### 1. 准备构建脚本

在项目根目录创建 `build.py`（或使用框架提供的构建脚本）：

```python
#!/usr/bin/env python3
from mcp_framework.build import MCPServerBuilder

if __name__ == "__main__":
    builder = MCPServerBuilder()
    builder.build_all()
```

#### 2. 构建命令

```bash
# 构建所有服务器
python build.py

# 构建特定服务器
python build.py --server my_server.py

# 列出所有可构建的服务器
python build.py --list

# 只清理构建目录
python build.py --clean-only

# 跳过测试
python build.py --no-test

# 包含源代码
python build.py --include-source
```

#### 3. 构建输出

构建完成后，会在 `dist/` 目录生成分发包：

```
dist/
├── my-server-macos-arm64-20241201_143022.tar.gz
├── weather-server-macos-arm64-20241201_143025.tar.gz
└── ...
```

每个分发包包含：
- 可执行文件
- 完整的 requirements.txt
- 启动脚本（start.sh / start.bat）
- README 和许可证文件
- 源代码（如果指定 --include-source）

### 依赖管理

构建系统支持多层依赖管理：

1. **通用依赖** (`requirements.txt`): 所有服务器共享的依赖
2. **特定依赖** (`{server_name}_requirements.txt`): 特定服务器的依赖
3. **自动分析**: 从代码中自动分析导入的包

示例文件结构：
```
project/
├── requirements.txt              # 通用依赖
├── weather_server.py
├── weather_server_requirements.txt  # weather_server 特定依赖
├── chat_server.py
├── chat_server_requirements.txt     # chat_server 特定依赖
└── build.py
```

## 🌐 Web 界面

框架提供内置的 Web 管理界面：

```python
from mcp_framework import EnhancedMCPServer
from mcp_framework.web import setup_web_interface

# 在服务器类中启用 Web 界面
class MyMCPServer(EnhancedMCPServer):
    def __init__(self):
        super().__init__(name="MyServer", version="1.0.0")
        # 启用 Web 界面
        setup_web_interface(self, port=8080)
```

访问 `http://localhost:8080/config` 进行配置管理。

## 🔧 高级用法


### 中间件支持

框架提供了中间件系统，用于处理HTTP请求的预处理和后处理。中间件在请求到达具体处理函数之前或响应返回给客户端之前执行特定的逻辑。

#### 内置中间件

框架自动集成了以下核心中间件：

**1. CORS 中间件 (`cors_middleware`)**
- **功能**: 处理跨域资源共享
- **用途**: 允许Web界面从不同域名访问MCP服务器
- **自动配置**: 支持所有常见的HTTP方法和头部

**2. 错误处理中间件 (`error_middleware`)**
- **功能**: 统一处理和格式化错误响应
- **用途**: 捕获异常，记录日志，返回标准化的JSON错误格式
- **安全性**: 避免敏感信息泄露

**3. 日志中间件 (`logging_middleware`)**
- **功能**: 记录HTTP请求的访问日志
- **监控**: 记录请求方法、路径、响应状态码和处理时间
- **调试**: 便于问题排查和性能分析

#### 中间件工作流程

```
请求 → CORS中间件 → 错误处理中间件 → 日志中间件 → 路由处理 → 响应
```

#### 自定义中间件示例

#### 框架中间件实现

框架的中间件在 `MCPHTTPServer` 中自动配置：

```python
from mcp_framework.server.middleware import (
    cors_middleware,
    error_middleware, 
    logging_middleware
)

class MCPHTTPServer:
    def setup_middleware(self):
        """设置中间件"""
        self.app.middlewares.append(cors_middleware)
        self.app.middlewares.append(error_middleware)
        self.app.middlewares.append(logging_middleware)
```

#### 中间件应用场景

**1. 安全控制**
- 跨域资源共享 (CORS)
- 统一错误处理
- 请求日志记录

**2. 监控和调试**
- 请求响应时间统计
- 错误率监控
- 访问日志记录

**3. 自动化处理**
- 响应头标准化
- 错误格式统一
- 请求追踪

#### 使用示例

```python
from mcp_framework import EnhancedMCPServer, run_server_main

class MyMCPServer(EnhancedMCPServer):
    def __init__(self):
        super().__init__(
            name="MyServer", 
            version="1.0.0",
            description="支持内置中间件的MCP服务器"
        )
        self._setup_tools()
    
    async def initialize(self):
        """服务器初始化"""
        self.logger.info("服务器启动，内置中间件已自动配置")
        self.logger.info("CORS、错误处理、日志中间件已启用")
    
    def _setup_tools(self):
        @self.tool("测试工具")
        async def test_tool(message: str) -> str:
            """测试中间件功能的工具"""
            return f"处理消息: {message}"

if __name__ == "__main__":
    server = MyMCPServer()
    run_server_main(
        server_instance=server,
        server_name="MyServer",
        default_port=8080
    )
```

#### 中间件效果验证

启动服务器后，可以通过以下方式验证中间件功能：

```bash
# 测试CORS中间件
curl -H "Origin: http://localhost:3000" http://localhost:8080/health

# 测试错误处理中间件
curl http://localhost:8080/nonexistent

# 查看日志中间件输出
# 在服务器日志中会看到请求记录
```

**注意事项：**
- 中间件在HTTP服务器层面自动配置，无需手动注册
- 所有MCP服务器实例都会自动获得这些中间件功能
- 中间件按照固定顺序执行：CORS → 错误处理 → 日志记录
- 当前版本不支持自定义中间件注册（未来版本可能会支持）
#### 中间件应用场景

**1. 安全控制**
- API密钥验证
- 请求频率限制
- IP白名单/黑名单

**2. 监控和调试**
- 请求响应时间统计
- 错误率监控
- 访问日志记录

**3. 数据处理**
- 请求数据预处理
- 响应数据格式化
- 内容压缩

**4. 缓存优化**
- 响应缓存
- 静态资源缓存
- 数据库查询缓存

#### 配置示例

```python
from mcp_framework import EnhancedMCPServer, run_server_main

class MyMCPServer(EnhancedMCPServer):
    def __init__(self):
        super().__init__(
            name="MyServer", 
            version="1.0.0",
            description="支持中间件的MCP服务器"
        )
        self._setup_tools()
    
    async def initialize(self):
        """服务器初始化"""
        self.logger.info("服务器启动，中间件已自动配置")
        self.logger.info("CORS、错误处理、日志中间件已启用")
    
    def _setup_tools(self):
        @self.tool("测试工具")
        async def test_tool(message: str) -> str:
            """测试中间件功能的工具"""
            return f"处理消息: {message}"

if __name__ == "__main__":
    server = MyMCPServer()
    run_server_main(
        server_instance=server,
        server_name="MyServer",
        default_port=8080
    )
```

通过访问 `http://localhost:8080/health` 可以看到中间件的工作效果，包括CORS头部、访问日志和错误处理。

## 📖 示例项目

查看 `examples/` 目录中的完整示例：

- `examples/port_config_demo.py` - 端口配置演示
- `examples/weather_server.py` - 天气服务器示例
- `examples/file_manager.py` - 文件管理服务器
- `examples/ai_assistant.py` - AI 助手服务器

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## 🆘 支持

- 📚 [文档](https://mcp-framework.readthedocs.io/)
- 🐛 [问题反馈](https://github.com/your-repo/mcp_framework/issues)
- 💬 [讨论区](https://github.com/your-repo/mcp_framework/discussions)
- 📧 [邮件支持](mailto:support@mcpframework.com)

## 🗺️ 路线图

- [ ] 插件系统
- [ ] 图形化配置界面
- [ ] 集群部署支持
- [ ] 性能监控面板
- [ ] Docker 容器化支持
- [ ] 云原生部署模板

---

**MCP Framework** - 让 MCP 服务器开发变得简单而强大！ 🚀