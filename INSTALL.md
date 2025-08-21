# MCP Framework 安装和使用指南

## 安装方式

### 1. 从源码安装（开发模式）

```bash
# 克隆或下载源码到本地
cd mcp_framework

# 安装为可编辑包
pip install -e .

# 或者安装所有依赖（包括开发工具）
pip install -e ".[dev,web,build]"
```

### 2. 从构建的包安装

```bash
# 构建包
python setup.py sdist bdist_wheel

# 安装构建的包
pip install dist/mcp_framework-0.1.0-py3-none-any.whl
```

### 3. 从 PyPI 安装（未来）

```bash
# 当包发布到 PyPI 后
pip install mcp-framework
```

## 验证安装

### 测试导入

```python
import mcp_framework
from mcp_framework import BaseMCPServer, MCPTool, MCPResource
from mcp_framework import ParamSpec, AnnotatedDecorators
from mcp_framework import ServerConfig, run_server

print(f"MCP Framework version: {mcp_framework.__version__}")
```

### 测试命令行工具

```bash
# 查看框架信息
mcp-framework info

# 创建新项目
mcp-framework create my_server --template basic

# 构建服务器
mcp-build --help
```

## 快速开始

### 1. 创建基本服务器

```python
from mcp_framework import BaseMCPServer, ParamSpec, Required

class MyServer(BaseMCPServer):
    def __init__(self):
        super().__init__("my-server", "1.0.0")
        
        # 使用装饰器注册工具
        decorators = self.decorators
        
        @decorators.tool("获取当前时间")
        async def get_time():
            import datetime
            return datetime.datetime.now().isoformat()
        
        @decorators.tool("问候用户")
        async def greet(name: Required("用户名称")):
            return f"Hello, {name}!"

if __name__ == "__main__":
    from mcp_framework import run_server
    server = MyServer()
    run_server(server)
```

### 2. 使用配置管理

```python
from mcp_framework import ServerConfig, ConfigManager

# 创建配置
config = ServerConfig(
    name="my-server",
    version="1.0.0",
    description="我的 MCP 服务器",
    port=8080
)

# 保存配置
manager = ConfigManager("config.json")
manager.save_config(config)

# 加载配置
loaded_config = manager.load_config()
```

### 3. 构建可执行文件

```bash
# 构建当前目录下的所有服务器
mcp-build

# 构建特定服务器
mcp-build --server my_server.py

# 构建时包含源码
mcp-build --include-source

# 只清理构建目录
mcp-build --clean-only
```

## 项目结构

```
mcp_framework/
├── mcp_framework/           # 主包目录
│   ├── __init__.py         # 包初始化和导出
│   ├── core/               # 核心模块
│   │   ├── base.py         # 基础类定义
│   │   ├── decorators.py   # 装饰器系统
│   │   ├── config.py       # 配置管理
│   │   ├── launcher.py     # 服务器启动器
│   │   └── utils.py        # 工具函数
│   ├── server/             # HTTP 服务器
│   ├── web/                # Web 界面
│   ├── build.py            # 构建系统
│   └── cli.py              # 命令行工具
├── setup.py                # 安装配置
├── pyproject.toml          # 项目配置
├── MANIFEST.in             # 包含文件清单
├── README.md               # 项目说明
└── test_package.py         # 包测试脚本
```

## 开发工具

### 运行测试

```bash
# 运行包测试
python test_package.py

# 运行单元测试（如果有）
pytest tests/
```

### 代码格式化

```bash
# 格式化代码
black mcp_framework/

# 检查代码风格
flake8 mcp_framework/

# 类型检查
mypy mcp_framework/
```

### 构建文档

```bash
# 生成文档（如果配置了 Sphinx）
sphinx-build docs docs/_build
```

## 发布到 PyPI

### 1. 准备发布

```bash
# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 构建包
python setup.py sdist bdist_wheel

# 检查包
twine check dist/*
```

### 2. 上传到 PyPI

```bash
# 上传到测试 PyPI
twine upload --repository testpypi dist/*

# 上传到正式 PyPI
twine upload dist/*
```

## 故障排除

### 常见问题

1. **导入错误**：确保包结构正确，所有 `__init__.py` 文件存在
2. **依赖问题**：检查 `requirements.txt` 和 `setup.py` 中的依赖版本
3. **构建失败**：确保 PyInstaller 正确安装，检查隐藏导入
4. **配置文件错误**：验证 `pyproject.toml` 语法正确

### 调试技巧

```bash
# 检查包安装
pip show mcp-framework

# 查看包内容
pip show -f mcp-framework

# 测试导入
python -c "import mcp_framework; print(mcp_framework.__version__)"
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 创建 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件