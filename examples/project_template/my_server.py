#!/usr/bin/env python3
"""
我的 MCP 服务器项目主文件

这是一个完整的项目模板，展示了如何组织和构建一个 MCP 服务器项目。

安装要求:
    pip install -r requirements.txt

运行方式:
    python my_server.py
    或
    mcp-framework run my_server.py

打包方式:
    mcp-build --config build_config.json
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from mcp_framework import MCPTool, MCPResource, run_server
from mcp_framework import ServerConfig

# 项目配置
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = PROJECT_ROOT / "config.json"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

# 加载配置
def load_config() -> Dict[str, Any]:
    """加载项目配置"""
    default_config = {
        "server": {
            "name": "My MCP Server",
            "version": "1.0.0",
            "description": "我的 MCP 服务器项目",
            "port": 8080,
            "debug": False
        },
        "features": {
            "file_operations": True,
            "data_processing": True,
            "web_requests": True,
            "system_info": True
        },
        "limits": {
            "max_file_size": 10485760,  # 10MB
            "max_files_per_operation": 100,
            "request_timeout": 30
        }
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并配置
                default_config.update(user_config)
        except Exception as e:
            print(f"警告: 无法加载配置文件 {CONFIG_FILE}: {e}")
    
    return default_config

# 加载配置
app_config = load_config()
server_config = app_config["server"]

# 创建服务器配置
config = ServerConfig(
    name=server_config["name"],
    version=server_config["version"],
    description=server_config["description"],
    port=server_config["port"],
    debug=server_config["debug"]
)

# 数据存储
class DataStore:
    """简单的数据存储类"""
    
    def __init__(self):
        self.data_file = DATA_DIR / "app_data.json"
        self.data = self.load_data()
    
    def load_data(self) -> Dict[str, Any]:
        """加载数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "files": {},
            "tasks": [],
            "notes": {},
            "settings": {}
        }
    
    def save_data(self):
        """保存数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get(self, key: str, default=None):
        """获取数据"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置数据"""
        self.data[key] = value
        self.save_data()

# 全局数据存储
store = DataStore()

# 文件操作工具
@MCPTool(name="read_file", description="读取文件内容")
def read_file_tool(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    读取指定文件的内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        文件内容和元信息
    """
    if not app_config["features"]["file_operations"]:
        return {"error": "文件操作功能已禁用"}
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {"error": f"文件不存在: {file_path}"}
        
        if path.stat().st_size > app_config["limits"]["max_file_size"]:
            return {"error": "文件太大，超过限制"}
        
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # 记录文件访问
        files_data = store.get("files", {})
        files_data[str(path)] = {
            "last_read": datetime.now().isoformat(),
            "size": path.stat().st_size,
            "encoding": encoding
        }
        store.set("files", files_data)
        
        return {
            "success": True,
            "content": content,
            "file_info": {
                "path": str(path),
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                "encoding": encoding
            }
        }
    
    except Exception as e:
        return {"error": f"读取文件失败: {str(e)}"}

@MCPTool(name="write_file", description="写入文件内容")
def write_file_tool(file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> Dict[str, Any]:
    """
    写入内容到指定文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码
        create_dirs: 是否创建目录
    
    Returns:
        写入结果
    """
    if not app_config["features"]["file_operations"]:
        return {"error": "文件操作功能已禁用"}
    
    try:
        path = Path(file_path)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # 记录文件写入
        files_data = store.get("files", {})
        files_data[str(path)] = {
            "last_written": datetime.now().isoformat(),
            "size": path.stat().st_size,
            "encoding": encoding
        }
        store.set("files", files_data)
        
        return {
            "success": True,
            "message": f"文件已写入: {file_path}",
            "file_info": {
                "path": str(path),
                "size": path.stat().st_size,
                "encoding": encoding
            }
        }
    
    except Exception as e:
        return {"error": f"写入文件失败: {str(e)}"}

@MCPTool(name="list_files", description="列出目录中的文件")
def list_files_tool(directory: str = ".", pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件名模式
        recursive: 是否递归搜索
    
    Returns:
        文件列表
    """
    if not app_config["features"]["file_operations"]:
        return {"error": "文件操作功能已禁用"}
    
    try:
        path = Path(directory)
        
        if not path.exists():
            return {"error": f"目录不存在: {directory}"}
        
        if not path.is_dir():
            return {"error": f"不是目录: {directory}"}
        
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # 限制文件数量
        if len(files) > app_config["limits"]["max_files_per_operation"]:
            files = files[:app_config["limits"]["max_files_per_operation"]]
        
        file_list = []
        for file_path in files:
            try:
                stat = file_path.stat()
                file_list.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "is_file": file_path.is_file(),
                    "is_dir": file_path.is_dir(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception:
                continue
        
        return {
            "success": True,
            "directory": str(path),
            "pattern": pattern,
            "recursive": recursive,
            "files": file_list,
            "count": len(file_list)
        }
    
    except Exception as e:
        return {"error": f"列出文件失败: {str(e)}"}

# 数据处理工具
@MCPTool(name="process_json", description="处理JSON数据")
def process_json_tool(data: str, operation: str = "validate", query: str = None) -> Dict[str, Any]:
    """
    处理JSON数据
    
    Args:
        data: JSON字符串
        operation: 操作类型 (validate, format, query, stats)
        query: JSONPath查询表达式
    
    Returns:
        处理结果
    """
    if not app_config["features"]["data_processing"]:
        return {"error": "数据处理功能已禁用"}
    
    try:
        # 解析JSON
        json_data = json.loads(data)
        
        if operation == "validate":
            return {
                "success": True,
                "message": "JSON格式有效",
                "type": type(json_data).__name__
            }
        
        elif operation == "format":
            formatted = json.dumps(json_data, indent=2, ensure_ascii=False)
            return {
                "success": True,
                "formatted": formatted
            }
        
        elif operation == "stats":
            def get_stats(obj, path=""):
                stats = {"count": 0, "types": {}, "paths": []}
                
                if isinstance(obj, dict):
                    stats["count"] = len(obj)
                    stats["types"]["object"] = stats["types"].get("object", 0) + 1
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key
                        stats["paths"].append(new_path)
                        sub_stats = get_stats(value, new_path)
                        for t, c in sub_stats["types"].items():
                            stats["types"][t] = stats["types"].get(t, 0) + c
                
                elif isinstance(obj, list):
                    stats["count"] = len(obj)
                    stats["types"]["array"] = stats["types"].get("array", 0) + 1
                    for i, item in enumerate(obj):
                        new_path = f"{path}[{i}]"
                        stats["paths"].append(new_path)
                        sub_stats = get_stats(item, new_path)
                        for t, c in sub_stats["types"].items():
                            stats["types"][t] = stats["types"].get(t, 0) + c
                
                else:
                    stats["types"][type(obj).__name__] = stats["types"].get(type(obj).__name__, 0) + 1
                
                return stats
            
            stats = get_stats(json_data)
            return {
                "success": True,
                "stats": stats
            }
        
        else:
            return {"error": f"不支持的操作: {operation}"}
    
    except json.JSONDecodeError as e:
        return {"error": f"JSON格式错误: {str(e)}"}
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}

# 任务管理工具
@MCPTool(name="add_task", description="添加任务")
def add_task_tool(title: str, description: str = "", priority: str = "medium", due_date: str = None) -> Dict[str, Any]:
    """
    添加新任务
    
    Args:
        title: 任务标题
        description: 任务描述
        priority: 优先级 (low, medium, high)
        due_date: 截止日期 (ISO格式)
    
    Returns:
        添加结果
    """
    tasks = store.get("tasks", [])
    
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "due_date": due_date,
        "completed_at": None
    }
    
    tasks.append(task)
    store.set("tasks", tasks)
    
    return {
        "success": True,
        "message": "任务已添加",
        "task": task
    }

@MCPTool(name="get_tasks", description="获取任务列表")
def get_tasks_tool(status: str = "all", priority: str = "all") -> Dict[str, Any]:
    """
    获取任务列表
    
    Args:
        status: 状态过滤 (all, pending, completed, in_progress)
        priority: 优先级过滤 (all, low, medium, high)
    
    Returns:
        任务列表
    """
    tasks = store.get("tasks", [])
    
    filtered_tasks = tasks
    
    if status != "all":
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    
    if priority != "all":
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
    
    return {
        "success": True,
        "tasks": filtered_tasks,
        "total": len(filtered_tasks),
        "filters": {
            "status": status,
            "priority": priority
        }
    }

# 系统信息工具
@MCPTool(name="get_system_info", description="获取系统信息")
def get_system_info_tool() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息
    """
    if not app_config["features"]["system_info"]:
        return {"error": "系统信息功能已禁用"}
    
    import platform
    import psutil
    
    try:
        return {
            "success": True,
            "system": {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"获取系统信息失败: {str(e)}"}

# 资源定义
@MCPResource(uri="config://app", name="应用配置", description="当前应用配置")
def get_app_config_resource() -> str:
    """获取应用配置资源"""
    return json.dumps(app_config, indent=2, ensure_ascii=False)

@MCPResource(uri="data://store", name="数据存储", description="应用数据存储")
def get_data_store_resource() -> str:
    """获取数据存储资源"""
    return json.dumps(store.data, indent=2, ensure_ascii=False)

@MCPResource(uri="file://project_info", name="项目信息", description="项目结构和信息")
def get_project_info_resource() -> str:
    """获取项目信息资源"""
    project_files = []
    for file_path in PROJECT_ROOT.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            try:
                stat = file_path.stat()
                project_files.append({
                    "path": str(file_path.relative_to(PROJECT_ROOT)),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception:
                continue
    
    return json.dumps({
        "project": {
            "root": str(PROJECT_ROOT),
            "name": server_config["name"],
            "version": server_config["version"],
            "description": server_config["description"]
        },
        "files": project_files,
        "structure": {
            "total_files": len(project_files),
            "data_dir": str(DATA_DIR),
            "config_file": str(CONFIG_FILE)
        }
    }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("🚀 启动 MCP 服务器项目...")
    print(f"📝 项目: {server_config['name']} v{server_config['version']}")
    print(f"📁 根目录: {PROJECT_ROOT}")
    print(f"🌐 端口: {server_config['port']}")
    print(f"🔧 调试模式: {'开启' if server_config['debug'] else '关闭'}")
    
    print("\n📚 可用功能:")
    for feature, enabled in app_config["features"].items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature}")
    
    print("\n🛠️ 可用工具:")
    tools = [
        "read_file", "write_file", "list_files",
        "process_json", "add_task", "get_tasks",
        "get_system_info"
    ]
    for tool in tools:
        print(f"  - {tool}")
    
    print("\n📦 可用资源:")
    resources = [
        "config://app", "data://store", "file://project_info"
    ]
    for resource in resources:
        print(f"  - {resource}")
    
    print("\n🔗 测试命令:")
    print(f"  curl http://localhost:{server_config['port']}/tools")
    print(f"  curl http://localhost:{server_config['port']}/resources")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 运行服务器
    run_server(config)