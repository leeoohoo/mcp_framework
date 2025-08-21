# 端口配置功能指南

## 概述

MCP 框架现在支持根据启动端口自动创建和管理不同的配置文件。这个功能允许您在同一台机器上运行多个服务器实例，每个实例都有自己独立的配置。

## 功能特性

- ✅ **自动配置文件创建**: 根据端口号自动创建独立的配置文件
- ✅ **配置隔离**: 不同端口的配置完全独立，互不影响
- ✅ **配置管理**: 支持列出、加载、保存和删除端口配置
- ✅ **命令行优先**: 命令行参数优先级高于配置文件
- ✅ **向后兼容**: 完全兼容现有的配置系统

## 配置文件命名规则

```
{server_name}_port_{port}_server_config.json
```

例如:
- `MyServer_port_8080_server_config.json` - 端口 8080 的配置
- `MyServer_port_8081_server_config.json` - 端口 8081 的配置
- `MyServer_server_config.json` - 默认配置（不指定端口时）

## 使用方法

### 1. 基本使用

```bash
# 启动服务器在端口 8080（会自动创建配置文件）
python your_server.py --port 8080

# 启动服务器在端口 8081（会创建另一个配置文件）
python your_server.py --port 8081
```

### 2. 编程接口

#### 创建端口配置管理器

```python
from mcp_framework.core.utils import create_port_based_config_manager

# 为特定端口创建配置管理器
config_manager = create_port_based_config_manager("MyServer", 8080)

# 检查配置是否存在
if config_manager.config_exists():
    config = config_manager.load_server_config()
else:
    # 创建新配置
    from mcp_framework.core.config import ServerConfig
    new_config = ServerConfig(host="localhost", port=8080)
    config_manager.save_server_config(new_config.to_dict())
```

#### 列出所有端口配置

```python
from mcp_framework.core.utils import list_all_port_configs

# 获取所有端口配置信息
all_configs = list_all_port_configs("MyServer")
print(f"总配置数: {all_configs['total_configs']}")
print(f"端口列表: {all_configs['ports']}")

# 遍历每个端口的配置
for port, config_data in all_configs['configs'].items():
    print(f"端口 {port}: {config_data}")
```

#### 删除端口配置

```python
from mcp_framework.core.config import ServerConfigManager

# 删除特定端口的配置
config_manager = ServerConfigManager.create_for_port("MyServer", 8080)
if config_manager.delete_port_config(8080):
    print("配置删除成功")
```

### 3. 服务器启动器集成

框架的 `run_server` 函数已经自动集成了端口配置功能：

```python
from mcp_framework.core.launcher import run_server
from mcp_framework.core.base import BaseMCPServer

class MyServer(BaseMCPServer):
    def __init__(self):
        super().__init__(name="MyServer", version="1.0.0")

async def main():
    server = MyServer()
    await run_server(
        server_instance=server,
        server_name="MyServer",
        default_port=8080
    )
```

启动时会自动：
1. 根据端口号创建配置管理器
2. 检查配置文件是否存在
3. 如果不存在，创建新的配置文件
4. 如果存在，加载并合并命令行参数
5. 显示配置文件信息和其他端口的配置

## 配置文件示例

### MyServer_port_8080_server_config.json
```json
{
  "host": "localhost",
  "port": 8080,
  "log_level": "INFO",
  "log_file": null,
  "max_connections": 100,
  "timeout": 30
}
```

### MyServer_port_8081_server_config.json
```json
{
  "host": "0.0.0.0",
  "port": 8081,
  "log_level": "DEBUG",
  "log_file": "server_8081.log",
  "max_connections": 200,
  "timeout": 60
}
```

## 实际应用场景

### 1. 开发环境
```bash
# 开发服务器 - 调试模式
python dev_server.py --port 8080 --log-level DEBUG

# 测试服务器 - 生产模式
python dev_server.py --port 8081 --log-level INFO --host 0.0.0.0
```

### 2. 多租户部署
```bash
# 租户 A
python tenant_server.py --port 8080

# 租户 B  
python tenant_server.py --port 8081

# 租户 C
python tenant_server.py --port 8082
```

### 3. 负载均衡
```bash
# 实例 1
python app_server.py --port 8080 --max-connections 500

# 实例 2
python app_server.py --port 8081 --max-connections 500

# 实例 3
python app_server.py --port 8082 --max-connections 500
```

## 配置优先级

1. **命令行参数** (最高优先级)
2. **端口配置文件** 
3. **默认值** (最低优先级)

例如：
```bash
# 即使配置文件中 log_level 是 INFO，这里会使用 DEBUG
python server.py --port 8080 --log-level DEBUG
```

## 最佳实践

1. **使用描述性的服务器名称**: 便于识别不同的服务器配置
2. **为不同环境使用不同端口**: 开发、测试、生产环境分离
3. **定期清理无用配置**: 使用 `delete_port_config` 删除不再使用的配置
4. **备份重要配置**: 配置文件位于 `config/` 目录下，建议定期备份

## 故障排除

### 配置文件权限问题
```bash
# 确保配置目录有写权限
chmod 755 config/
chmod 644 config/*.json
```

### 端口冲突
```bash
# 检查端口是否被占用
lsof -i :8080

# 使用不同端口
python server.py --port 8081
```

### 配置文件损坏
```python
# 删除损坏的配置文件，系统会自动重新创建
config_manager.delete_port_config(8080)
```

## 演示脚本

运行框架提供的演示脚本来了解功能：

```bash
# 运行演示（创建示例配置）
python examples/port_config_demo.py

# 启动演示服务器
python examples/port_config_demo.py --port 8080
python examples/port_config_demo.py --port 8081
```

## API 参考

### ServerConfigManager

- `__init__(server_name, port=None)`: 创建配置管理器
- `config_exists()`: 检查配置文件是否存在
- `load_server_config()`: 加载配置
- `save_server_config(config)`: 保存配置
- `list_port_configs()`: 列出所有端口配置
- `delete_port_config(port)`: 删除端口配置
- `create_for_port(server_name, port)`: 工厂方法，创建端口配置管理器
- `create_default(server_name)`: 工厂方法，创建默认配置管理器

### 工具函数

- `create_port_based_config_manager(server_name, port)`: 创建端口配置管理器
- `list_all_port_configs(server_name)`: 列出所有端口配置信息