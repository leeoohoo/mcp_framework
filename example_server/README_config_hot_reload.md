# MCP框架配置热更新功能

## 问题背景

在使用MCP框架开发服务时，经常遇到配置更新后需要重启服务器才能生效的问题。特别是在 `terminal_manager_server` 中，`default_dir` 配置更新后，内存中的 `TerminalService` 实例不会自动更新，导致新创建的终端仍然使用旧的配置进行验证。

## 解决方案

MCP框架现在提供了配置热更新机制，通过回调函数的方式通知服务器配置发生变化，让开发者可以在配置更新时执行相应的处理逻辑。

## 核心功能

### 1. 配置更新回调机制

在 `BaseMCPServer` 中新增了以下方法：

```python
# 注册配置更新回调
self.register_config_update_callback(callback_function)

# 取消注册回调
self.unregister_config_update_callback(callback_function)
```

### 2. 自动通知机制

当配置通过以下方式更新时，会自动触发回调：
- HTTP API 调用 `/api/config` 更新配置
- 调用 `configure_server()` 方法更新配置

### 3. 回调函数格式

```python
def config_update_callback(old_config: Dict[str, Any], new_config: Dict[str, Any]):
    """配置更新回调函数
    
    Args:
        old_config: 更新前的配置字典
        new_config: 更新后的配置字典
    """
    # 处理配置变化逻辑
    pass
```

## 使用示例

### 基本用法

```python
from mcp_framework import BaseMCPServer

class MyServer(BaseMCPServer):
    def __init__(self):
        super().__init__("my-server", "1.0.0", "My Server")
        
        # 注册配置更新回调
        self.register_config_update_callback(self._on_config_updated)
        
        # 初始化需要热更新的组件
        self.my_service = None
    
    def _on_config_updated(self, old_config, new_config):
        """处理配置更新"""
        # 检查特定配置项是否变化
        if old_config.get('some_param') != new_config.get('some_param'):
            # 更新相关组件
            if self.my_service:
                self.my_service.update_config(new_config.get('some_param'))
    
    async def initialize(self):
        # 初始化组件
        param_value = self.get_config_value('some_param')
        self.my_service = MyService(param_value)
```

### Terminal Manager 示例

参考 `config_hot_reload_example.py` 文件，展示了如何解决 terminal_manager_server 的配置热更新问题：

1. **注册回调**：在服务器初始化时注册配置更新回调
2. **监听变化**：在回调中检查 `default_dir` 是否发生变化
3. **更新组件**：当配置变化时，更新 `TerminalService` 的 `default_dir`

## 测试步骤

1. **启动示例服务器**：
   ```bash
   cd example_server
   python config_hot_reload_example.py
   ```

2. **访问配置页面**：
   打开浏览器访问 `http://localhost:8080/setup`

3. **修改配置**：
   - 找到 "默认工作目录" 配置项
   - 修改为不同的路径
   - 点击保存

4. **观察日志**：
   在终端中可以看到类似输出：
   ```
   INFO - TerminalMCPServer - 配置更新回调触发: {'default_dir': '/old/path'} -> {'default_dir': '/new/path'}
   INFO - TerminalMCPServer - 检测到 default_dir 变化: '/old/path' -> '/new/path'
   INFO - TerminalService - Default directory updated from '/old/path' to '/new/path'
   ```

5. **测试功能**：
   使用 MCP 客户端调用 `create_terminal` 和 `get_current_config` 工具验证配置已生效

## 最佳实践

### 1. 回调函数设计

- **检查变化**：只处理真正发生变化的配置项
- **错误处理**：添加适当的异常处理
- **日志记录**：记录配置变化和处理结果

```python
def _on_config_updated(self, old_config, new_config):
    try:
        # 检查特定配置是否变化
        old_value = old_config.get('param_name')
        new_value = new_config.get('param_name')
        
        if old_value != new_value:
            self.logger.info(f"配置 'param_name' 从 '{old_value}' 更新为 '{new_value}'")
            # 执行更新逻辑
            self._update_component(new_value)
    except Exception as e:
        self.logger.error(f"配置更新处理失败: {e}")
```

### 2. 组件更新策略

- **增量更新**：只更新变化的部分，避免重新初始化整个组件
- **状态保持**：确保更新过程中不丢失重要状态
- **原子操作**：确保更新操作的原子性

### 3. 性能考虑

- **避免频繁更新**：对于频繁变化的配置，考虑添加防抖机制
- **异步处理**：对于耗时的更新操作，考虑异步执行
- **资源清理**：及时清理不再使用的资源

## 注意事项

1. **回调执行顺序**：回调按注册顺序执行，注意依赖关系
2. **异常处理**：回调中的异常不会影响其他回调的执行
3. **配置验证**：框架会先验证配置的有效性，再触发回调
4. **内存管理**：记得在适当时机取消注册回调，避免内存泄漏

## 兼容性

- 该功能向后兼容，现有的服务器代码无需修改即可正常运行
- 只有注册了回调的服务器才会收到配置更新通知
- 支持多个回调函数同时注册

通过这个配置热更新机制，开发者可以轻松解决配置更新后需要重启服务器的问题，提升开发和运维效率。