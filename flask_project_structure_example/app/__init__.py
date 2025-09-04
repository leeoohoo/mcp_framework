#!/usr/bin/env python3
"""
Flask应用初始化文件
集成MCP框架的Flask项目结构示例
"""

from flask import Flask
from .mcp_config import mcp_server
from .services import UserService, ProductService
from .routes import register_routes

def create_app():
    """Flask应用工厂函数"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['DEBUG'] = True
    
    # 初始化服务（这会自动注册MCP工具）
    user_service = UserService(mcp_server)
    product_service = ProductService(mcp_server)
    
    # 注册Flask路由
    register_routes(app, user_service, product_service)
    
    # 存储服务实例供其他地方使用
    app.user_service = user_service
    app.product_service = product_service
    app.mcp_server = mcp_server
    
    return app