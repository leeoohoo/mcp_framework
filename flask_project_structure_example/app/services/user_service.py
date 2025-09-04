#!/usr/bin/env python3
"""
用户服务模块
包含用户相关的业务逻辑和MCP工具注册
"""

import time
from typing import Dict, List, Any

class UserService:
    """用户服务类"""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.users_db = {}  # 模拟数据库
        self._init_sample_data()
        self._register_mcp_tools()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        self.users_db = {
            1: {"id": 1, "name": "张三", "email": "zhangsan@example.com", "role": "admin"},
            2: {"id": 2, "name": "李四", "email": "lisi@example.com", "role": "user"},
            3: {"id": 3, "name": "王五", "email": "wangwu@example.com", "role": "user"}
        }
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        
        @self.mcp_server.tool("获取用户信息")
        async def get_user_info(user_id: int) -> Dict[str, Any]:
            """根据用户ID获取用户详细信息"""
            user = self.get_user_by_id(user_id)
            if user:
                return {
                    "success": True,
                    "user": user,
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": f"用户 {user_id} 不存在",
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("获取所有用户")
        async def get_all_users() -> Dict[str, Any]:
            """获取所有用户列表"""
            return {
                "success": True,
                "users": list(self.users_db.values()),
                "total": len(self.users_db),
                "timestamp": time.time()
            }
        
        @self.mcp_server.tool("创建用户")
        async def create_user(name: str, email: str, role: str = "user") -> Dict[str, Any]:
            """创建新用户"""
            try:
                new_user = self.create_user_internal(name, email, role)
                return {
                    "success": True,
                    "user": new_user,
                    "message": "用户创建成功",
                    "timestamp": time.time()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("更新用户信息")
        async def update_user(user_id: int, name: str = None, email: str = None, role: str = None) -> Dict[str, Any]:
            """更新用户信息"""
            try:
                updated_user = self.update_user_internal(user_id, name, email, role)
                if updated_user:
                    return {
                        "success": True,
                        "user": updated_user,
                        "message": "用户信息更新成功",
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"用户 {user_id} 不存在",
                        "timestamp": time.time()
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("删除用户")
        async def delete_user(user_id: int) -> Dict[str, Any]:
            """删除用户"""
            if user_id in self.users_db:
                deleted_user = self.users_db.pop(user_id)
                return {
                    "success": True,
                    "deleted_user": deleted_user,
                    "message": "用户删除成功",
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": f"用户 {user_id} 不存在",
                    "timestamp": time.time()
                }
    
    # Flask服务方法（非MCP工具）
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Flask路由使用的方法"""
        return self.users_db.get(user_id)
    
    def get_all_users_list(self) -> List[Dict[str, Any]]:
        """Flask路由使用的方法"""
        return list(self.users_db.values())
    
    def create_user_internal(self, name: str, email: str, role: str = "user") -> Dict[str, Any]:
        """内部创建用户方法"""
        # 检查邮箱是否已存在
        for user in self.users_db.values():
            if user['email'] == email:
                raise ValueError(f"邮箱 {email} 已被使用")
        
        # 生成新的用户ID
        new_id = max(self.users_db.keys()) + 1 if self.users_db else 1
        
        new_user = {
            "id": new_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.users_db[new_id] = new_user
        return new_user
    
    def update_user_internal(self, user_id: int, name: str = None, email: str = None, role: str = None) -> Dict[str, Any]:
        """内部更新用户方法"""
        if user_id not in self.users_db:
            return None
        
        user = self.users_db[user_id]
        
        if name is not None:
            user['name'] = name
        if email is not None:
            # 检查邮箱是否被其他用户使用
            for uid, u in self.users_db.items():
                if uid != user_id and u['email'] == email:
                    raise ValueError(f"邮箱 {email} 已被其他用户使用")
            user['email'] = email
        if role is not None:
            user['role'] = role
        
        user['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
        return user