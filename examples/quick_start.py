#!/usr/bin/env python3
"""
MCP Framework 快速开始脚本

这个脚本帮助用户快速创建和运行他们的第一个 MCP 服务器。

使用方法:
    python quick_start.py

前提条件:
    pip install mcp-framework
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    MCP Framework 快速开始                    ║
║                                                              ║
║  🚀 欢迎使用 MCP Framework！                                 ║
║  📚 这个脚本将帮助你创建第一个 MCP 服务器                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_mcp_framework():
    """检查 MCP Framework 是否已安装"""
    try:
        import mcp_framework
        print("✅ MCP Framework 已安装")
        return True
    except ImportError:
        print("❌ MCP Framework 未安装")
        print("\n请先安装 MCP Framework:")
        print("  pip install mcp-framework")
        return False

def get_user_input():
    """获取用户输入"""
    print("\n📝 请提供以下信息来创建你的 MCP 服务器:")
    
    project_name = input("\n项目名称 (默认: my-mcp-server): ").strip() or "my-mcp-server"
    server_name = input("服务器名称 (默认: My MCP Server): ").strip() or "My MCP Server"
    description = input("服务器描述 (默认: 我的第一个 MCP 服务器): ").strip() or "我的第一个 MCP 服务器"
    port = input("端口号 (默认: 8080): ").strip() or "8080"
    
    try:
        port = int(port)
    except ValueError:
        print("⚠️ 端口号无效，使用默认端口 8080")
        port = 8080
    
    return {
        "project_name": project_name,
        "server_name": server_name,
        "description": description,
        "port": port
    }

def create_project_directory(project_name):
    """创建项目目录"""
    project_dir = Path(project_name)
    
    if project_dir.exists():
        response = input(f"\n⚠️ 目录 '{project_name}' 已存在。是否覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ 操作已取消")
            return None
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "data").mkdir(exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    
    print(f"✅ 项目目录已创建: {project_dir.absolute()}")
    return project_dir

def create_server_file(project_dir, config):
    """创建服务器文件"""
    server_content = f'''#!/usr/bin/env python3
"""
{config["server_name"]}

{config["description"]}

创建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

运行方式:
    python server.py
    或
    mcp-framework run server.py
"""

from mcp_framework import MCPTool, MCPResource, run_server
from mcp_framework import ServerConfig
import json
import os
from datetime import datetime
from pathlib import Path

# 服务器配置
config = ServerConfig(
    name="{config["server_name"]}",
    version="1.0.0",
    description="{config["description"]}",
    port={config["port"]}
)

# 数据存储
DATA_FILE = Path("data/app_data.json")

def load_data():
    """加载数据"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {{"messages": [], "counter": 0}}

def save_data(data):
    """保存数据"""
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 全局数据
app_data = load_data()

@MCPTool(name="hello", description="友好的问候工具")
def hello_tool(name: str = "World") -> str:
    """
    向指定的人打招呼
    
    Args:
        name: 要问候的人的名字
    
    Returns:
        问候消息
    """
    global app_data
    app_data["counter"] += 1
    message = f"你好，{{name}}！这是第 {{app_data['counter']}} 次问候。"
    
    # 记录消息
    app_data["messages"].append({{
        "type": "greeting",
        "name": name,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }})
    
    save_data(app_data)
    return message

@MCPTool(name="add_message", description="添加消息")
def add_message_tool(message: str, category: str = "general") -> dict:
    """
    添加一条消息到存储中
    
    Args:
        message: 消息内容
        category: 消息分类
    
    Returns:
        添加结果
    """
    global app_data
    
    new_message = {{
        "id": len(app_data["messages"]) + 1,
        "content": message,
        "category": category,
        "timestamp": datetime.now().isoformat()
    }}
    
    app_data["messages"].append(new_message)
    save_data(app_data)
    
    return {{
        "success": True,
        "message": "消息已添加",
        "data": new_message,
        "total_messages": len(app_data["messages"])
    }}

@MCPTool(name="get_messages", description="获取消息列表")
def get_messages_tool(category: str = None, limit: int = 10) -> dict:
    """
    获取消息列表
    
    Args:
        category: 消息分类过滤
        limit: 返回消息数量限制
    
    Returns:
        消息列表
    """
    global app_data
    
    messages = app_data["messages"]
    
    if category:
        messages = [msg for msg in messages if msg.get("category") == category]
    
    # 返回最新的消息
    messages = messages[-limit:] if limit > 0 else messages
    
    return {{
        "success": True,
        "messages": messages,
        "total": len(messages),
        "filter": {{
            "category": category,
            "limit": limit
        }}
    }}

@MCPTool(name="get_stats", description="获取统计信息")
def get_stats_tool() -> dict:
    """
    获取应用统计信息
    
    Returns:
        统计信息
    """
    global app_data
    
    categories = {{}}
    for msg in app_data["messages"]:
        cat = msg.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {{
        "success": True,
        "stats": {{
            "total_messages": len(app_data["messages"]),
            "greeting_counter": app_data["counter"],
            "categories": categories,
            "server_info": {{
                "name": config.name,
                "version": config.version,
                "port": config.port
            }}
        }}
    }}

@MCPResource(uri="data://messages", name="消息数据", description="所有存储的消息")
def get_messages_resource() -> str:
    """
    获取消息资源
    """
    global app_data
    return json.dumps(app_data, indent=2, ensure_ascii=False)

@MCPResource(uri="info://server", name="服务器信息", description="服务器状态和配置")
def get_server_info_resource() -> str:
    """
    获取服务器信息资源
    """
    global app_data
    
    info = {{
        "server": {{
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "port": config.port,
            "started_at": datetime.now().isoformat()
        }},
        "data": {{
            "total_messages": len(app_data["messages"]),
            "greeting_counter": app_data["counter"]
        }},
        "tools": [
            "hello", "add_message", "get_messages", "get_stats"
        ],
        "resources": [
            "data://messages", "info://server"
        ]
    }}
    
    return json.dumps(info, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("🚀 启动 {config["server_name"]}...")
    print(f"📝 描述: {config["description"]}")
    print(f"🌐 端口: {config["port"]}")
    print("\n📚 可用工具:")
    print("  - hello: 问候工具")
    print("  - add_message: 添加消息")
    print("  - get_messages: 获取消息列表")
    print("  - get_stats: 获取统计信息")
    print("\n📦 可用资源:")
    print("  - data://messages: 消息数据")
    print("  - info://server: 服务器信息")
    print("\n🔗 测试命令:")
    print(f"  curl -X POST http://localhost:{config["port"]}/tools/hello -H 'Content-Type: application/json' -d '{{\"name\": \"Alice\"}}'")
    print(f"  curl http://localhost:{config["port"]}/tools")
    print(f"  curl http://localhost:{config["port"]}/resources")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 运行服务器
    run_server(config)
'''
    
    server_file = project_dir / "server.py"
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(server_content)
    
    print(f"✅ 服务器文件已创建: {server_file}")
    return server_file

def create_config_file(project_dir, config):
    """创建配置文件"""
    config_data = {
        "server": {
            "name": config["server_name"],
            "version": "1.0.0",
            "description": config["description"],
            "port": config["port"],
            "debug": False
        },
        "features": {
            "message_storage": True,
            "greeting_counter": True,
            "statistics": True
        },
        "limits": {
            "max_messages": 1000,
            "message_max_length": 1000
        }
    }
    
    config_file = project_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置文件已创建: {config_file}")
    return config_file

def create_requirements_file(project_dir):
    """创建依赖文件"""
    requirements = [
        "mcp-framework>=0.1.0",
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0"
    ]
    
    req_file = project_dir / "requirements.txt"
    with open(req_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(requirements) + '\n')
    
    print(f"✅ 依赖文件已创建: {req_file}")
    return req_file

def create_readme_file(project_dir, config):
    """创建 README 文件"""
    readme_content = f'''# {config["server_name"]}

{config["description"]}

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
# 直接运行
python server.py

# 或使用 MCP Framework CLI
mcp-framework run server.py
```

### 3. 测试服务器

```bash
# 查看所有工具
curl http://localhost:{config["port"]}/tools

# 测试问候工具
curl -X POST http://localhost:{config["port"]}/tools/hello \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Alice"}}'

# 添加消息
curl -X POST http://localhost:{config["port"]}/tools/add_message \\
  -H "Content-Type: application/json" \\
  -d '{{"message": "Hello World!", "category": "test"}}'

# 获取消息列表
curl -X POST http://localhost:{config["port"]}/tools/get_messages \\
  -H "Content-Type: application/json" \\
  -d '{{"limit": 5}}'

# 获取统计信息
curl -X POST http://localhost:{config["port"]}/tools/get_stats \\
  -H "Content-Type: application/json" \\
  -d '{{}}'
```

## 📁 项目结构

```
{config["project_name"]}/
├── server.py                 # 主服务器文件
├── config.json               # 服务器配置
├── requirements.txt          # 依赖列表
├── README.md                 # 项目说明
├── data/                     # 数据目录
│   └── app_data.json         # 应用数据
├── logs/                     # 日志目录
└── tests/                    # 测试目录
```

## 🛠️ 可用工具

- `hello`: 友好的问候工具
- `add_message`: 添加消息到存储
- `get_messages`: 获取消息列表
- `get_stats`: 获取统计信息

## 📦 可用资源

- `data://messages`: 所有存储的消息
- `info://server`: 服务器状态和配置

## 📦 打包部署

### 使用 MCP Framework 构建工具

```bash
# 构建可执行文件
mcp-build server.py

# 构建所有平台版本
mcp-build server.py --all-platforms
```

### 手动使用 PyInstaller

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建可执行文件
pyinstaller --onefile --name {config["project_name"]} server.py
```

## 🤝 下一步

1. 修改 `server.py` 添加更多工具和功能
2. 更新 `config.json` 调整服务器配置
3. 添加测试文件到 `tests/` 目录
4. 使用构建工具打包你的服务器

祝你使用愉快！🎉
'''
    
    readme_file = project_dir / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README 文件已创建: {readme_file}")
    return readme_file

def create_test_file(project_dir, config):
    """创建测试文件"""
    test_content = f'''#!/usr/bin/env python3
"""
{config["server_name"]} 测试文件
"""

import pytest
import json
from pathlib import Path

# 这里可以添加你的测试代码
# 例如:

def test_server_import():
    """测试服务器模块导入"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import server
        assert server.config.name == "{config["server_name"]}"
        assert server.config.port == {config["port"]}
    except ImportError:
        pytest.skip("服务器模块导入失败")

def test_data_operations():
    """测试数据操作"""
    # 这里可以添加数据操作的测试
    pass

if __name__ == "__main__":
    pytest.main([__file__])
'''
    
    test_file = project_dir / "tests" / "test_server.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    # 创建 __init__.py
    init_file = project_dir / "tests" / "__init__.py"
    init_file.touch()
    
    print(f"✅ 测试文件已创建: {test_file}")
    return test_file

def print_next_steps(project_dir, config):
    """打印后续步骤"""
    print("\n" + "=" * 60)
    print("🎉 项目创建成功！")
    print("=" * 60)
    
    print(f"\n📁 项目位置: {project_dir.absolute()}")
    print(f"🌐 服务器端口: {config['port']}")
    
    print("\n🚀 下一步操作:")
    print(f"\n1. 进入项目目录:")
    print(f"   cd {project_dir}")
    
    print(f"\n2. 安装依赖:")
    print(f"   pip install -r requirements.txt")
    
    print(f"\n3. 运行服务器:")
    print(f"   python server.py")
    print(f"   或")
    print(f"   mcp-framework run server.py")
    
    print(f"\n4. 测试服务器:")
    print(f"   curl http://localhost:{config['port']}/tools")
    print(f"   curl -X POST http://localhost:{config['port']}/tools/hello -H 'Content-Type: application/json' -d '{{\"name\": \"Alice\"}}'")
    
    print(f"\n5. 打包部署:")
    print(f"   mcp-build server.py")
    
    print("\n📚 更多信息:")
    print("   - 查看 README.md 了解详细使用说明")
    print("   - 修改 server.py 添加更多功能")
    print("   - 更新 config.json 调整配置")
    
    print("\n🎯 快速测试命令:")
    print(f"   cd {project_dir} && python server.py")
    
    print("\n祝你使用愉快！🎉")

def main():
    """主函数"""
    print_banner()
    
    # 检查 MCP Framework
    if not check_mcp_framework():
        return 1
    
    # 获取用户输入
    config = get_user_input()
    
    # 创建项目目录
    project_dir = create_project_directory(config["project_name"])
    if not project_dir:
        return 1
    
    try:
        # 创建项目文件
        print("\n📝 创建项目文件...")
        create_server_file(project_dir, config)
        create_config_file(project_dir, config)
        create_requirements_file(project_dir)
        create_readme_file(project_dir, config)
        create_test_file(project_dir, config)
        
        # 打印后续步骤
        print_next_steps(project_dir, config)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 创建项目时出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())