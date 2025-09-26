# MCP Framework Stdio Client SDK 示例

本目录包含了 MCP Framework Stdio Client SDK 的使用示例，展示了如何使用新的 SDK 来简化 stdio 服务调用。

## 文件说明

### 1. `stdio_client_examples.py`
完整的 SDK 使用示例，包含：
- 基础 stdio 客户端使用
- 配置管理客户端使用
- 工具调用客户端使用
- 便捷函数使用
- 错误处理示例

### 2. `sdk_config_test.py`
使用 SDK 重写的配置测试示例，对比原始的 `test_dual_instance_config.py`：
- 代码量减少 70%+
- 自动处理连接和初始化
- 内置错误处理和超时管理
- 支持异步上下文管理器

### 3. `sdk_tools_test.py`
使用 SDK 重写的工具调用测试示例，对比原始的 `test_tool_call.py` 和 `test_tools_list.py`：
- 代码量减少 60%+
- 自动连接和初始化管理
- 内置工具验证和缓存
- 统一的错误处理

## 运行示例

确保你有运行中的 MCP 服务器，然后运行：

```bash
# 运行完整示例
python examples/stdio_client_examples.py

# 运行配置测试示例
python examples/sdk_config_test.py

# 运行工具调用测试示例
python examples/sdk_tools_test.py
```

## SDK 优势

相比原始的手动 stdio 调用代码，新的 SDK 提供了：

1. **简化的 API**：统一的接口，减少样板代码
2. **自动连接管理**：自动处理进程启动、连接和清理
3. **内置错误处理**：统一的异常处理和重试机制
4. **类型安全**：完整的类型提示和验证
5. **异步支持**：原生异步支持，更好的性能
6. **上下文管理**：支持 `async with` 语法，自动资源管理
7. **配置验证**：内置配置验证和默认值处理
8. **工具缓存**：智能工具信息缓存，减少重复请求

## 迁移指南

如果你有现有的 stdio 调用代码，可以按以下步骤迁移到 SDK：

1. **替换连接代码**：
   ```python
   # 原始代码
   process = subprocess.Popen([...])
   # 手动处理 JSON-RPC...
   
   # SDK 代码
   async with MCPStdioClient("server.py") as client:
       # 自动处理连接
   ```

2. **简化请求发送**：
   ```python
   # 原始代码
   request = {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
   # 手动序列化和发送...
   
   # SDK 代码
   result = await client.send_request("method", params)
   ```

3. **使用专用客户端**：
   ```python
   # 配置管理
   async with ConfigClient("server.py") as client:
       config = await client.get_config()
   
   # 工具调用
   async with ToolsClient("server.py") as client:
       result = await client.call_tool("tool_name", params)
   ```