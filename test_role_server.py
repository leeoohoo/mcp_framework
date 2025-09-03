#!/usr/bin/env python3
"""
测试role参数功能的MCP服务器
"""

import asyncio
import logging
from mcp_framework.core.base import EnhancedMCPServer
from mcp_framework.core.config import ServerConfig, ConfigManager
from mcp_framework.server.http_server import MCPHTTPServer

# 创建服务器实例
server = EnhancedMCPServer(
    name="Role Test Server",
    version="1.0.0",
    description="测试role参数功能的服务器"
)

@server.tool(role="planner")
def plan_task(task: str) -> str:
    """
    规划任务 - 仅限planner角色
    
    Args:
        task: 要规划的任务
    
    Returns:
        任务规划结果
    """
    return f"为任务 '{task}' 制定的规划：\n1. 分析需求\n2. 制定步骤\n3. 执行计划"

@server.tool(role="executor")
def execute_task(task: str) -> str:
    """
    执行任务 - 仅限executor角色
    
    Args:
        task: 要执行的任务
    
    Returns:
        任务执行结果
    """
    return f"正在执行任务: {task}\n执行状态: 完成"

@server.tool()  # 没有role参数，所有角色都可以使用
def get_status() -> str:
    """
    获取服务器状态 - 通用工具
    
    Returns:
        服务器状态信息
    """
    return "服务器运行正常，所有功能可用"

@server.tool(role="analyst")
def analyze_data(data: str) -> str:
    """
    分析数据 - 仅限analyst角色
    
    Args:
        data: 要分析的数据
    
    Returns:
        数据分析结果
    """
    return f"数据分析结果：\n输入数据: {data}\n分析完成，发现关键模式"

async def main():
    """启动服务器"""
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建服务器配置
    config = ServerConfig(
        host="localhost",
        port=8888
    )
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 创建HTTP服务器
    http_server = MCPHTTPServer(server, config, config_manager)
    
    try:
        # 启动服务器
        runner = await http_server.start()
        print(f"测试服务器已启动: http://localhost:8888")
        print(f"测试URL:")
        print(f"  所有工具: http://localhost:8888/tools/list")
        print(f"  planner工具: http://localhost:8888/tools/list?role=planner")
        print(f"  executor工具: http://localhost:8888/tools/list?role=executor")
        print(f"  analyst工具: http://localhost:8888/tools/list?role=analyst")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        await http_server.stop(runner)

if __name__ == "__main__":
    asyncio.run(main())