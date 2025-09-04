#!/usr/bin/env python3
"""
多角色支持测试服务器
测试role参数支持数组格式的功能
"""

import asyncio
from typing_extensions import Annotated
from mcp_framework.core.decorators import Required
from mcp_framework.core.base import EnhancedMCPServer

# 创建服务器实例
server = EnhancedMCPServer(
    name="multi-role-test-server",
    version="1.0.0",
    description="测试多角色功能的MCP服务器"
)

@property
def setup_tools(self):
    # 单角色工具
    @self.tool("规划任务", role="planner")
    async def plan_task(task: Annotated[str, Required("要规划的任务")]):
        """规划任务 - 仅限planner角色"""
        return f"任务规划: {task}\n步骤: 1.分析需求 2.制定计划 3.分配资源"
    
    # 多角色工具 - 使用数组
    @self.tool("执行任务", role=["executor", "manager"])
    async def execute_task(task: Annotated[str, Required("要执行的任务")]):
        """执行任务 - executor和manager角色都可以使用"""
        return f"正在执行任务: {task}\n状态: 进行中\n预计完成时间: 30分钟"
    
    # 多角色流式工具
    @self.streaming_tool("监控进度", role=["manager", "supervisor"])
    async def monitor_progress(project: Annotated[str, Required("项目名称")]):
        """监控项目进度 - manager和supervisor角色可用"""
        stages = ["初始化", "执行中", "质量检查", "完成"]
        for i, stage in enumerate(stages):
            yield f"项目 {project} - 阶段 {i+1}/4: {stage}"
            await asyncio.sleep(0.5)
    
    # 通用工具（无角色限制）
    @self.tool("获取状态")
    async def get_status():
        """获取服务器状态 - 所有角色都可以使用"""
        return "服务器运行正常，所有功能可用"
    
    # 单角色流式工具
    @self.streaming_tool("生成报告", role="analyst")
    async def generate_report(data: Annotated[str, Required("要分析的数据")]):
        """生成分析报告 - 仅限analyst角色"""
        steps = ["数据收集", "数据清洗", "统计分析", "报告生成"]
        for step in steps:
            yield f"报告生成进度: {step} - 数据: {data}"
            await asyncio.sleep(0.3)

# 绑定setup_tools方法到服务器
server.setup_tools = setup_tools.__get__(server, EnhancedMCPServer)

if __name__ == "__main__":
    from mcp_framework import run_server_main
    
    print(f"启动多角色测试服务器...")
    print(f"")
    print(f"测试角色过滤:")
    print(f"- 获取planner角色工具: curl 'http://localhost:8080/tools/list?role=planner'")
    print(f"- 获取executor角色工具: curl 'http://localhost:8080/tools/list?role=executor'")
    print(f"- 获取manager角色工具: curl 'http://localhost:8080/tools/list?role=manager'")
    print(f"- 获取所有工具: curl 'http://localhost:8080/tools/list'")
    print(f"")
    print(f"工具角色配置:")
    print(f"- plan_task: planner")
    print(f"- execute_task: [executor, manager]")
    print(f"- monitor_progress: [manager, supervisor]")
    print(f"- get_status: 无角色限制")
    print(f"- generate_report: analyst")
    print(f"")
    
    run_server_main(
        server_instance=server,
        server_name="MultiRoleTestServer",
        default_port=8080
    )