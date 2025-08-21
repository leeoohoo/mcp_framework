#!/usr/bin/env python3
"""
MCP Framework 命令行工具
"""

import click
import sys
from pathlib import Path
from typing import Optional


@click.group()
@click.version_option(version="0.1.0", prog_name="mcp-framework")
def main():
    """MCP Framework - 强大且易用的 MCP 服务器开发框架"""
    pass


@main.command()
@click.argument('name')
@click.option('--port', '-p', default=8080, help='服务器端口号')
@click.option('--template', '-t', default='basic', 
              type=click.Choice(['basic', 'advanced', 'streaming']),
              help='项目模板类型')
@click.option('--output', '-o', help='输出目录')
def create(name: str, port: int, template: str, output: Optional[str]):
    """创建新的 MCP 服务器项目"""
    output_dir = Path(output) if output else Path.cwd() / name
    
    if output_dir.exists():
        click.echo(f"❌ 目录 {output_dir} 已存在")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据模板创建文件
    if template == 'basic':
        create_basic_template(output_dir, name, port)
    elif template == 'advanced':
        create_advanced_template(output_dir, name, port)
    elif template == 'streaming':
        create_streaming_template(output_dir, name, port)
    
    click.echo(f"✅ 项目 '{name}' 创建成功！")
    click.echo(f"📁 位置: {output_dir}")
    click.echo(f"\n🚀 快速开始:")
    click.echo(f"   cd {output_dir}")
    click.echo(f"   pip install -r requirements.txt")
    click.echo(f"   python {name}_server.py")


def create_basic_template(output_dir: Path, name: str, port: int):
    """创建基础模板"""
    server_content = f'''#!/usr/bin/env python3
"""
{name} MCP 服务器
"""

import asyncio
from typing import Annotated
from mcp_framework import EnhancedMCPServer, run_server_main
from mcp_framework.core.decorators import Required, Optional

# 创建服务器实例
server = EnhancedMCPServer(
    name="{name.title()}Server",
    version="1.0.0",
    description="{name} MCP 服务器"
)


@server.tool("示例工具")
async def example_tool(
    message: Annotated[str, Required("要处理的消息")]
) -> str:
    """示例工具函数"""
    return f"处理消息: {{message}}"


@server.tool("计算器")
async def calculator(
    operation: Annotated[str, Required("运算类型 (add/sub/mul/div)")],
    a: Annotated[float, Required("第一个数字")],
    b: Annotated[float, Required("第二个数字")]
) -> float:
    """简单计算器"""
    if operation == "add":
        return a + b
    elif operation == "sub":
        return a - b
    elif operation == "mul":
        return a * b
    elif operation == "div":
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
    else:
        raise ValueError(f"不支持的运算类型: {{operation}}")


if __name__ == "__main__":
    run_server_main(
        server_instance=server,
        server_name="{name.title()}Server",
        default_port={port}
    )
'''
    
    requirements_content = '''mcp-framework>=0.1.0
'''
    
    readme_content = f'''# {name.title()} MCP Server

{name} MCP 服务器项目。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python {name}_server.py
```

## 使用

服务器将在 http://localhost:{port} 启动。
'''
    
    # 写入文件
    (output_dir / f"{name}_server.py").write_text(server_content, encoding='utf-8')
    (output_dir / "requirements.txt").write_text(requirements_content, encoding='utf-8')
    (output_dir / "README.md").write_text(readme_content, encoding='utf-8')


def create_advanced_template(output_dir: Path, name: str, port: int):
    """创建高级模板"""
    # 这里可以添加更复杂的模板
    create_basic_template(output_dir, name, port)
    
    # 添加配置文件
    config_content = f'''{{
    "server_name": "{name.title()}Server",
    "version": "1.0.0",
    "port": {port},
    "host": "localhost",
    "log_level": "INFO",
    "max_connections": 100
}}
'''
    (output_dir / "config.json").write_text(config_content, encoding='utf-8')


def create_streaming_template(output_dir: Path, name: str, port: int):
    """创建流式模板"""
    create_basic_template(output_dir, name, port)
    
    # 添加流式工具示例
    streaming_example = f'''
@server.streaming_tool("流式数据生成器")
async def stream_data(
    count: Annotated[int, Required("生成数据的数量")],
    delay: Annotated[float, Optional("每条数据间的延迟(秒)", default=0.1)]
):
    """流式生成数据"""
    for i in range(count):
        yield f"数据项 {{i+1}}/{{count}}: 当前时间 {{datetime.now()}}"
        await asyncio.sleep(delay)
'''
    
    # 追加到服务器文件
    server_file = output_dir / f"{name}_server.py"
    content = server_file.read_text(encoding='utf-8')
    # 在 if __name__ 之前插入
    content = content.replace(
        'if __name__ == "__main__":',
        f'{streaming_example}\n\nif __name__ == "__main__":'
    )
    # 添加 datetime 导入
    content = content.replace(
        'import asyncio',
        'import asyncio\nfrom datetime import datetime'
    )
    server_file.write_text(content, encoding='utf-8')


@main.command()
@click.option('--version', '-v', is_flag=True, help='显示版本信息')
def info(version: bool):
    """显示框架信息"""
    if version:
        click.echo("MCP Framework v0.1.0")
    else:
        click.echo("🚀 MCP Framework - 强大且易用的 MCP 服务器开发框架")
        click.echo("")
        click.echo("📚 文档: https://mcp-framework.readthedocs.io/")
        click.echo("🐛 问题反馈: https://github.com/mcpframework/mcp_framework/issues")
        click.echo("💬 讨论区: https://github.com/mcpframework/mcp_framework/discussions")


if __name__ == '__main__':
    main()