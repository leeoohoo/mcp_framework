#!/usr/bin/env python3
"""
简单的 MCP 服务器示例

这个示例展示了如何使用 pip install mcp-framework 后创建一个基本的 MCP 服务器。

安装要求:
    pip install mcp-framework

运行方式:
    python simple_server_example.py
    或
    mcp-framework run simple_server_example.py
"""

from mcp_framework import MCPTool, MCPResource, run_server
from mcp_framework import ServerConfig
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# 创建服务器配置
config = ServerConfig(
    name="Simple MCP Server",
    version="1.0.0",
    description="一个简单的 MCP 服务器示例，展示基本功能",
    port=8080
)

# 示例数据存储
TODO_LIST = []
NOTES = {}

@MCPTool(name="hello", description="友好的问候工具")
def hello_tool(name: str = "World", language: str = "zh") -> str:
    """
    向指定的人用指定语言打招呼
    
    Args:
        name: 要问候的人的名字
        language: 语言代码 (zh=中文, en=英文)
    
    Returns:
        问候消息
    """
    greetings = {
        "zh": f"你好，{name}！欢迎使用 MCP Framework！",
        "en": f"Hello, {name}! Welcome to MCP Framework!"
    }
    return greetings.get(language, greetings["zh"])

@MCPTool(name="calculate", description="基础数学计算器")
def calculate_tool(a: float, b: float, operation: str = "add") -> Dict[str, Any]:
    """
    执行基础数学运算
    
    Args:
        a: 第一个数字
        b: 第二个数字
        operation: 运算类型 (add, subtract, multiply, divide, power)
    
    Returns:
        包含结果和计算信息的字典
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
        "power": lambda x, y: x ** y
    }
    
    if operation not in operations:
        return {
            "error": f"不支持的运算: {operation}",
            "supported_operations": list(operations.keys())
        }
    
    try:
        result = operations[operation](a, b)
        if result is None:
            return {"error": "除数不能为零"}
        
        return {
            "result": result,
            "operation": operation,
            "operands": [a, b],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@MCPTool(name="add_todo", description="添加待办事项")
def add_todo_tool(task: str, priority: str = "medium") -> Dict[str, Any]:
    """
    添加新的待办事项
    
    Args:
        task: 任务描述
        priority: 优先级 (low, medium, high)
    
    Returns:
        添加结果
    """
    todo_item = {
        "id": len(TODO_LIST) + 1,
        "task": task,
        "priority": priority,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    TODO_LIST.append(todo_item)
    
    return {
        "success": True,
        "message": "待办事项已添加",
        "todo": todo_item,
        "total_todos": len(TODO_LIST)
    }

@MCPTool(name="list_todos", description="列出所有待办事项")
def list_todos_tool(filter_priority: str = None, show_completed: bool = True) -> Dict[str, Any]:
    """
    列出待办事项
    
    Args:
        filter_priority: 按优先级过滤 (low, medium, high)
        show_completed: 是否显示已完成的任务
    
    Returns:
        待办事项列表
    """
    filtered_todos = TODO_LIST.copy()
    
    if not show_completed:
        filtered_todos = [todo for todo in filtered_todos if not todo["completed"]]
    
    if filter_priority:
        filtered_todos = [todo for todo in filtered_todos if todo["priority"] == filter_priority]
    
    return {
        "todos": filtered_todos,
        "total": len(filtered_todos),
        "filters": {
            "priority": filter_priority,
            "show_completed": show_completed
        }
    }

@MCPTool(name="complete_todo", description="标记待办事项为完成")
def complete_todo_tool(todo_id: int) -> Dict[str, Any]:
    """
    标记待办事项为完成
    
    Args:
        todo_id: 待办事项ID
    
    Returns:
        操作结果
    """
    for todo in TODO_LIST:
        if todo["id"] == todo_id:
            todo["completed"] = True
            todo["completed_at"] = datetime.now().isoformat()
            return {
                "success": True,
                "message": f"任务 {todo_id} 已标记为完成",
                "todo": todo
            }
    
    return {
        "success": False,
        "error": f"未找到ID为 {todo_id} 的待办事项"
    }

@MCPTool(name="save_note", description="保存笔记")
def save_note_tool(title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """
    保存一条笔记
    
    Args:
        title: 笔记标题
        content: 笔记内容
        tags: 标签列表
    
    Returns:
        保存结果
    """
    note_id = f"note_{len(NOTES) + 1}"
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    NOTES[note_id] = note
    
    return {
        "success": True,
        "message": "笔记已保存",
        "note": note,
        "total_notes": len(NOTES)
    }

@MCPTool(name="get_note", description="获取笔记")
def get_note_tool(note_id: str) -> Dict[str, Any]:
    """
    根据ID获取笔记
    
    Args:
        note_id: 笔记ID
    
    Returns:
        笔记内容或错误信息
    """
    if note_id in NOTES:
        return {
            "success": True,
            "note": NOTES[note_id]
        }
    else:
        return {
            "success": False,
            "error": f"未找到ID为 {note_id} 的笔记",
            "available_notes": list(NOTES.keys())
        }

@MCPTool(name="search_notes", description="搜索笔记")
def search_notes_tool(query: str, search_in: str = "all") -> Dict[str, Any]:
    """
    搜索笔记
    
    Args:
        query: 搜索关键词
        search_in: 搜索范围 (title, content, tags, all)
    
    Returns:
        搜索结果
    """
    results = []
    query_lower = query.lower()
    
    for note in NOTES.values():
        match = False
        
        if search_in in ["title", "all"] and query_lower in note["title"].lower():
            match = True
        elif search_in in ["content", "all"] and query_lower in note["content"].lower():
            match = True
        elif search_in in ["tags", "all"] and any(query_lower in tag.lower() for tag in note["tags"]):
            match = True
        
        if match:
            results.append(note)
    
    return {
        "query": query,
        "search_in": search_in,
        "results": results,
        "count": len(results)
    }

# 资源定义
@MCPResource(uri="memory://todos", name="待办事项列表", description="当前的待办事项数据")
def get_todos_resource() -> str:
    """
    获取待办事项资源
    """
    return json.dumps({
        "todos": TODO_LIST,
        "total": len(TODO_LIST),
        "completed": len([t for t in TODO_LIST if t["completed"]]),
        "pending": len([t for t in TODO_LIST if not t["completed"]])
    }, indent=2, ensure_ascii=False)

@MCPResource(uri="memory://notes", name="笔记集合", description="当前保存的所有笔记")
def get_notes_resource() -> str:
    """
    获取笔记资源
    """
    return json.dumps({
        "notes": NOTES,
        "total": len(NOTES),
        "note_ids": list(NOTES.keys())
    }, indent=2, ensure_ascii=False)

@MCPResource(uri="file://server_info.json", name="服务器信息", description="服务器状态和配置信息")
def get_server_info_resource() -> str:
    """
    获取服务器信息资源
    """
    return json.dumps({
        "server": {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "port": config.port,
            "started_at": datetime.now().isoformat()
        },
        "stats": {
            "total_todos": len(TODO_LIST),
            "total_notes": len(NOTES),
            "completed_todos": len([t for t in TODO_LIST if t["completed"]])
        },
        "available_tools": [
            "hello", "calculate", "add_todo", "list_todos", 
            "complete_todo", "save_note", "get_note", "search_notes"
        ],
        "available_resources": [
            "memory://todos", "memory://notes", "file://server_info.json"
        ]
    }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("🚀 启动简单 MCP 服务器...")
    print(f"📝 服务器名称: {config.name}")
    print(f"🔧 版本: {config.version}")
    print(f"🌐 端口: {config.port}")
    print("\n📚 可用工具:")
    print("  - hello: 问候工具")
    print("  - calculate: 数学计算")
    print("  - add_todo: 添加待办事项")
    print("  - list_todos: 列出待办事项")
    print("  - complete_todo: 完成待办事项")
    print("  - save_note: 保存笔记")
    print("  - get_note: 获取笔记")
    print("  - search_notes: 搜索笔记")
    print("\n📦 可用资源:")
    print("  - memory://todos: 待办事项数据")
    print("  - memory://notes: 笔记数据")
    print("  - file://server_info.json: 服务器信息")
    print("\n🔗 测试命令:")
    print(f"  curl -X POST http://localhost:{config.port}/tools/hello -H 'Content-Type: application/json' -d '{{\"name\": \"Alice\"}}'")
    print(f"  curl http://localhost:{config.port}/tools")
    print(f"  curl http://localhost:{config.port}/resources")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 运行服务器
    run_server(config)