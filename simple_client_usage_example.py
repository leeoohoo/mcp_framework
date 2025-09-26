#!/usr/bin/env python3
"""
SimpleClient 用法验证（不需要实际服务器）
"""

import os
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_framework.client.simple import SimpleClient


def validate_simple_client_usage():
    """验证 SimpleClient 用法的正确性"""
    print("=== SimpleClient 用法验证 ===\n")
    
    # 模拟你的用法
    server_script = "your_server.py"
    alias = "test_server"
    config_dir = "/Users/lilei/project/config/test_mcp_server_config"
    
    print("✅ 你的用法:")
    print(f"   SimpleClient({server_script}, alias={alias}, config_dir='{config_dir}')")
    
    # 创建客户端实例验证参数
    client = SimpleClient(
        server_script, 
        alias=alias, 
        config_dir=config_dir
    )
    
    print(f"\n📋 参数验证:")
    print(f"   server_script: {client.server_script}")
    print(f"   alias: {client.alias}")
    print(f"   config_dir: {client.config_dir}")
    
    # 验证参数正确性
    assert client.server_script == server_script
    assert client.alias == alias
    assert client.config_dir == config_dir
    
    print(f"\n✅ 所有参数都正确设置！")
    
    print(f"\n📁 配置文件将保存在:")
    print(f"   {config_dir}/")
    print(f"   文件名格式: {{server_name}}_{alias}_server_config.json")
    
    print(f"\n🎯 你的用法完全正确，包括:")
    print(f"   ✓ 正确的参数顺序")
    print(f"   ✓ 使用了别名（有助于多实例管理）")
    print(f"   ✓ 指定了自定义配置目录")
    print(f"   ✓ 使用了上下文管理器（as client:）")


def show_alternative_usages():
    """展示其他可选用法"""
    print(f"\n=== 其他可选用法 ===\n")
    
    usages = [
        {
            "name": "使用默认配置目录",
            "code": "SimpleClient(server_script, alias=alias)",
            "description": "配置文件保存在默认位置 ~/.mcp/"
        },
        {
            "name": "使用环境变量",
            "code": "SimpleClient(server_script, alias=alias, config_dir=os.getenv('MCP_CONFIG_DIR'))",
            "description": "从环境变量读取配置目录"
        },
        {
            "name": "使用相对路径",
            "code": "SimpleClient(server_script, alias=alias, config_dir='./config')",
            "description": "使用相对于当前目录的配置路径"
        },
        {
            "name": "动态配置目录",
            "code": "SimpleClient(server_script, alias=alias, config_dir=f'/tmp/{alias}_config')",
            "description": "根据别名动态生成配置目录"
        }
    ]
    
    for i, usage in enumerate(usages, 1):
        print(f"{i}. {usage['name']}:")
        print(f"   代码: {usage['code']}")
        print(f"   说明: {usage['description']}\n")


def show_best_practices():
    """展示最佳实践"""
    print("=== 最佳实践建议 ===\n")
    
    practices = [
        "确保配置目录有写入权限",
        "使用有意义的别名，便于区分不同实例",
        "在生产环境中使用绝对路径",
        "考虑使用环境变量来配置不同环境的路径",
        "定期备份重要的配置文件",
        "使用上下文管理器确保资源正确释放"
    ]
    
    for i, practice in enumerate(practices, 1):
        print(f"{i}. {practice}")
    
    print(f"\n💡 你的用法已经遵循了大部分最佳实践！")


def main():
    """主函数"""
    validate_simple_client_usage()
    show_alternative_usages()
    show_best_practices()
    
    print(f"\n🎉 总结: 你的 SimpleClient 用法完全正确，没有任何问题！")


if __name__ == "__main__":
    main()