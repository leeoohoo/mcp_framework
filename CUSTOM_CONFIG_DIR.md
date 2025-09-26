# 自定义配置目录功能

MCP Framework 现在支持用户指定自定义的配置目录，而不是使用默认的配置目录。这个功能提供了更大的灵活性，特别适用于以下场景：

- 多环境部署（开发、测试、生产）
- 容器化部署
- 多用户系统
- 配置文件集中管理

## 支持的配置方式

### 1. 命令行参数（优先级最高）

使用 `--config-dir` 参数指定配置目录：

```bash
python your_server.py --config-dir /path/to/custom/config --port 8080
```

### 2. 环境变量（优先级中等）

设置 `MCP_CONFIG_DIR` 环境变量：

```bash
export MCP_CONFIG_DIR=/path/to/custom/config
python your_server.py --port 8080
```

### 3. 默认行为（优先级最低）

如果没有指定自定义配置目录，系统会使用默认行为：

- **开发环境**：当前工作目录下的 `config` 文件夹
- **打包环境**：可执行文件所在目录下的 `config` 文件夹

## 优先级顺序

配置目录的确定遵循以下优先级顺序：

1. **命令行参数** `--config-dir`
2. **环境变量** `MCP_CONFIG_DIR`
3. **默认行为**

## 使用示例

### 示例 1：开发环境使用自定义目录

```bash
# 使用命令行参数
python example_server.py --config-dir ./dev-config --port 8080

# 使用环境变量
export MCP_CONFIG_DIR=./dev-config
python example_server.py --port 8080
```

### 示例 2：生产环境配置

```bash
# 生产环境配置目录
export MCP_CONFIG_DIR=/etc/mcp-servers/config
python production_server.py --port 8080
```

### 示例 3：容器化部署

```dockerfile
# Dockerfile
ENV MCP_CONFIG_DIR=/app/config
VOLUME ["/app/config"]
```

```bash
# 运行容器时挂载配置目录
docker run -v /host/config:/app/config your-mcp-server
```

### 示例 4：多服务器实例

```bash
# 服务器实例 1
python server.py --config-dir /configs/server1 --port 8080

# 服务器实例 2  
python server.py --config-dir /configs/server2 --port 8081
```

## 配置文件命名规则

无论使用哪种配置目录，配置文件的命名规则保持不变：

- **端口配置**：`{server_name}_port_{port}_server_config.json`
- **别名配置**：`{server_name}_alias_{alias}_server_config.json`
- **默认配置**：`{server_name}_server_config.json`

## 编程接口

如果你在代码中需要创建配置管理器，可以使用以下方法：

```python
from mcp_framework.core.utils import (
    create_port_based_config_manager,
    create_alias_based_config_manager,
    create_default_config_manager
)

# 使用自定义配置目录
config_manager = create_port_based_config_manager(
    server_name="MyServer",
    port=8080,
    custom_config_dir="/path/to/custom/config"
)

# 使用默认配置目录（会检查环境变量）
config_manager = create_port_based_config_manager(
    server_name="MyServer", 
    port=8080
)
```

## 注意事项

1. **目录权限**：确保指定的配置目录具有读写权限
2. **目录创建**：如果指定的目录不存在，系统会自动创建
3. **路径格式**：支持相对路径和绝对路径
4. **向后兼容**：现有的服务器代码无需修改即可使用默认行为

## 故障排除

### 配置目录权限问题

```bash
# 检查目录权限
ls -la /path/to/config/directory

# 修改权限（如果需要）
chmod 755 /path/to/config/directory
```

### 验证配置目录设置

```python
from mcp_framework.core.utils import get_config_dir

# 检查当前使用的配置目录
print(f"当前配置目录: {get_config_dir()}")

# 检查使用自定义目录
print(f"自定义配置目录: {get_config_dir('/custom/path')}")
```

### 环境变量检查

```bash
# 检查环境变量是否设置
echo $MCP_CONFIG_DIR

# 临时设置环境变量
export MCP_CONFIG_DIR=/tmp/test-config
```

## 最佳实践

1. **生产环境**：使用绝对路径和环境变量
2. **开发环境**：使用相对路径和命令行参数
3. **容器部署**：使用环境变量和卷挂载
4. **多实例**：为每个实例使用独立的配置目录
5. **备份**：定期备份配置文件
6. **版本控制**：将配置模板纳入版本控制，但不包含敏感信息

## 迁移指南

如果你已经有现有的 MCP 服务器，迁移到自定义配置目录很简单：

1. **备份现有配置**：
   ```bash
   cp -r ./config /backup/config-$(date +%Y%m%d)
   ```

2. **设置新的配置目录**：
   ```bash
   export MCP_CONFIG_DIR=/new/config/path
   ```

3. **复制配置文件**：
   ```bash
   cp -r ./config/* $MCP_CONFIG_DIR/
   ```

4. **启动服务器**：
   ```bash
   python your_server.py --port 8080
   ```

现在你的服务器将使用新的配置目录！