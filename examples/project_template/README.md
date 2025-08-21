# My MCP Server Project

这是一个使用 MCP Framework 构建的完整服务器项目模板，展示了如何组织、开发和打包一个功能丰富的 MCP 服务器。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 MCP Framework
pip install mcp-framework

# 安装项目依赖
pip install -r requirements.txt

# 安装测试依赖（可选）
pip install -r test_requirements.txt
```

### 2. 运行服务器

```bash
# 直接运行
python my_server.py

# 或使用 MCP Framework CLI
mcp-framework run my_server.py

# 指定配置文件
mcp-framework run my_server.py --config config.json

# 指定端口
mcp-framework run my_server.py --port 8081
```

### 3. 测试服务器

```bash
# 查看所有工具
curl http://localhost:8080/tools

# 查看所有资源
curl http://localhost:8080/resources

# 测试文件读取工具
curl -X POST http://localhost:8080/tools/read_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "config.json"}'

# 测试任务添加工具
curl -X POST http://localhost:8080/tools/add_task \
  -H "Content-Type: application/json" \
  -d '{"title": "测试任务", "description": "这是一个测试任务", "priority": "high"}'
```

## 📁 项目结构

```
my_mcp_project/
├── my_server.py              # 主服务器文件
├── config.json               # 服务器配置
├── requirements.txt          # 主要依赖
├── test_requirements.txt     # 测试依赖
├── build_config.json         # 构建配置
├── README.md                 # 项目说明
├── data/                     # 数据目录
│   └── app_data.json         # 应用数据存储
├── logs/                     # 日志目录
│   └── server.log            # 服务器日志
├── tests/                    # 测试文件
│   ├── test_my_server.py
│   └── __init__.py
└── dist/                     # 构建输出
    ├── my-mcp-server         # 可执行文件
    └── my-mcp-server.zip     # 分发包
```

## 🛠️ 功能特性

### 文件操作工具
- `read_file`: 读取文件内容
- `write_file`: 写入文件内容
- `list_files`: 列出目录文件

### 数据处理工具
- `process_json`: JSON数据处理和验证

### 任务管理工具
- `add_task`: 添加新任务
- `get_tasks`: 获取任务列表

### 系统信息工具
- `get_system_info`: 获取系统资源信息

### 资源
- `config://app`: 应用配置
- `data://store`: 数据存储
- `file://project_info`: 项目信息

## ⚙️ 配置说明

### 服务器配置 (config.json)

```json
{
  "server": {
    "name": "My MCP Server",
    "version": "1.0.0",
    "port": 8080,
    "debug": false
  },
  "features": {
    "file_operations": true,
    "data_processing": true,
    "system_info": true
  },
  "limits": {
    "max_file_size": 10485760,
    "max_files_per_operation": 100
  }
}
```

### 构建配置 (build_config.json)

构建配置文件定义了如何打包你的服务器：

- **platforms**: 目标平台 (native, windows, linux)
- **include_source**: 是否包含源代码
- **create_installer**: 是否创建安装包
- **dependencies**: 依赖管理
- **pyinstaller**: PyInstaller 特定配置

## 📦 打包部署

### 使用 MCP Framework 构建工具

```bash
# 构建当前平台版本
mcp-build --config build_config.json

# 构建所有平台版本
mcp-build --config build_config.json --all-platforms

# 构建特定平台
mcp-build --config build_config.json --platform windows
mcp-build --config build_config.json --platform linux

# 包含源代码
mcp-build --config build_config.json --include-source

# 创建安装包
mcp-build --config build_config.json --create-installer
```

### 使用项目构建脚本

如果你在 MCP Framework 项目目录中：

```bash
# 使用跨平台构建脚本
python build_cross_platform.py --server my_server.py

# 构建所有平台
python build_cross_platform.py --server my_server.py --platform all

# 包含源代码
python build_cross_platform.py --server my_server.py --include-source
```

### Docker 部署

```bash
# 构建 Docker 镜像
docker build -t my-mcp-server .

# 运行容器
docker run -p 8080:8080 my-mcp-server

# 使用 Docker Compose
docker-compose up
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=my_server

# 运行特定测试
pytest tests/test_my_server.py

# 运行性能测试
locust -f tests/performance_test.py
```

## 🔧 开发

### 代码格式化

```bash
# 格式化代码
black my_server.py

# 排序导入
isort my_server.py

# 代码检查
flake8 my_server.py

# 类型检查
mypy my_server.py
```

### 安全检查

```bash
# 安全漏洞扫描
bandit my_server.py

# 依赖安全检查
safety check
```

## 📊 监控和日志

### 日志配置

服务器会自动记录日志到 `logs/server.log`，你可以通过配置文件调整日志级别和格式。

### 性能监控

```bash
# 查看系统资源使用
curl http://localhost:8080/tools/get_system_info

# 查看服务器状态
curl http://localhost:8080/resources/file://project_info
```

## 🚀 部署选项

### 1. 直接部署

将构建好的可执行文件复制到目标服务器：

```bash
# 复制文件
scp dist/my-mcp-server user@server:/opt/mcp/

# 在目标服务器运行
./my-mcp-server --port 8080
```

### 2. 系统服务

创建 systemd 服务文件：

```ini
[Unit]
Description=My MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp
ExecStart=/opt/mcp/my-mcp-server --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. 容器化部署

使用 Docker 进行容器化部署，支持 Kubernetes、Docker Swarm 等编排工具。

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果你遇到问题或有建议：

1. 查看 [MCP Framework 文档](../USAGE_AFTER_INSTALL.md)
2. 搜索已有的 Issues
3. 创建新的 Issue
4. 参与社区讨论

## 📚 更多资源

- [MCP Framework 官方文档](../README.md)
- [跨平台构建指南](../BUILD_CROSS_PLATFORM.md)
- [端口配置指南](../docs/PORT_CONFIG_GUIDE.md)
- [更多示例](../examples/)

祝你使用愉快！🎉