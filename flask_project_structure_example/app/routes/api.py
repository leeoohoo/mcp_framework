#!/usr/bin/env python3
"""
Flask API路由
提供REST API接口，与MCP工具并行存在
"""

from flask import Flask, jsonify, request
import time

def register_api_routes(app: Flask, user_service, product_service):
    """注册API路由"""
    
    @app.route('/')
    def index():
        """首页"""
        return jsonify({
            "message": "Flask + MCP Framework 集成示例",
            "services": {
                "flask_api": "http://localhost:5000/api",
                "mcp_server": "http://localhost:8080"
            },
            "mcp_info": {
                "name": app.mcp_server.name,
                "version": app.mcp_server.version,
                "tools_count": len(app.mcp_server._tool_handlers)
            },
            "timestamp": time.time()
        })
    
    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({
            "status": "healthy",
            "services": {
                "flask": "running",
                "mcp_server": "running",
                "user_service": "active",
                "product_service": "active"
            },
            "timestamp": time.time()
        })
    
    # ===== 用户相关API =====
    
    @app.route('/api/users', methods=['GET'])
    def get_users():
        """获取所有用户（Flask API）"""
        users = user_service.get_all_users_list()
        return jsonify({
            "success": True,
            "users": users,
            "total": len(users),
            "source": "flask_api"
        })
    
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        """获取单个用户（Flask API）"""
        user = user_service.get_user_by_id(user_id)
        if user:
            return jsonify({
                "success": True,
                "user": user,
                "source": "flask_api"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"用户 {user_id} 不存在",
                "source": "flask_api"
            }), 404
    
    @app.route('/api/users', methods=['POST'])
    def create_user():
        """创建用户（Flask API）"""
        data = request.get_json()
        
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要字段: name, email",
                "source": "flask_api"
            }), 400
        
        try:
            new_user = user_service.create_user_internal(
                name=data['name'],
                email=data['email'],
                role=data.get('role', 'user')
            )
            return jsonify({
                "success": True,
                "user": new_user,
                "message": "用户创建成功",
                "source": "flask_api"
            }), 201
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "source": "flask_api"
            }), 400
    
    # ===== 产品相关API =====
    
    @app.route('/api/products', methods=['GET'])
    def get_products():
        """获取所有产品（Flask API）"""
        category = request.args.get('category', 'all')
        products = product_service.get_all_products()
        
        if category != 'all':
            products = [p for p in products if p['category'] == category]
        
        return jsonify({
            "success": True,
            "products": products,
            "total": len(products),
            "category": category,
            "source": "flask_api"
        })
    
    @app.route('/api/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        """获取单个产品（Flask API）"""
        product = product_service.get_product_by_id(product_id)
        if product:
            return jsonify({
                "success": True,
                "product": product,
                "source": "flask_api"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"产品 {product_id} 不存在",
                "source": "flask_api"
            }), 404
    
    @app.route('/api/products', methods=['POST'])
    def create_product():
        """创建产品（Flask API）"""
        data = request.get_json()
        
        required_fields = ['name', 'category', 'price']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "success": False,
                "error": f"缺少必要字段: {', '.join(required_fields)}",
                "source": "flask_api"
            }), 400
        
        try:
            new_product = product_service.create_product_internal(
                name=data['name'],
                category=data['category'],
                price=float(data['price']),
                stock=int(data.get('stock', 0)),
                description=data.get('description', '')
            )
            return jsonify({
                "success": True,
                "product": new_product,
                "message": "产品创建成功",
                "source": "flask_api"
            }), 201
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "source": "flask_api"
            }), 400
    
    @app.route('/api/products/<int:product_id>/stock', methods=['PATCH'])
    def update_product_stock(product_id):
        """更新产品库存（Flask API）"""
        data = request.get_json()
        
        if not data or 'stock_change' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要字段: stock_change",
                "source": "flask_api"
            }), 400
        
        try:
            updated_product = product_service.update_stock_internal(
                product_id=product_id,
                stock_change=int(data['stock_change'])
            )
            if updated_product:
                return jsonify({
                    "success": True,
                    "product": updated_product,
                    "message": f"库存更新成功，变化量: {data['stock_change']}",
                    "source": "flask_api"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"产品 {product_id} 不存在",
                    "source": "flask_api"
                }), 404
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "source": "flask_api"
            }), 400
    
    # ===== MCP信息API =====
    
    @app.route('/api/mcp/info')
    def mcp_info():
        """获取MCP服务器信息"""
        return jsonify({
            "mcp_server": {
                "name": app.mcp_server.name,
                "version": app.mcp_server.version,
                "description": app.mcp_server.description,
                "tools_count": len(app.mcp_server._tool_handlers),
                "tools": list(app.mcp_server._tool_handlers.keys())
            },
            "endpoints": {
                "tools_list": "http://localhost:8080/tools/list",
                "tools_call": "http://localhost:8080/tools/call"
            },
            "source": "flask_api"
        })
    
    @app.route('/api/comparison')
    def api_comparison():
        """展示Flask API vs MCP工具的对比"""
        return jsonify({
            "message": "Flask API 和 MCP 工具对比",
            "flask_api": {
                "description": "传统的REST API，适合Web应用和移动应用",
                "endpoints": [
                    "GET /api/users - 获取用户列表",
                    "GET /api/users/<id> - 获取单个用户",
                    "POST /api/users - 创建用户",
                    "GET /api/products - 获取产品列表",
                    "POST /api/products - 创建产品"
                ],
                "advantages": [
                    "标准HTTP协议",
                    "易于缓存",
                    "支持各种客户端",
                    "成熟的生态系统"
                ]
            },
            "mcp_tools": {
                "description": "MCP工具，适合AI代理和智能助手",
                "tools": list(app.mcp_server._tool_handlers.keys()),
                "advantages": [
                    "AI友好的接口",
                    "自动生成文档",
                    "类型安全",
                    "支持流式处理"
                ]
            },
            "integration_benefits": [
                "同一业务逻辑，多种访问方式",
                "Flask处理传统Web请求",
                "MCP处理AI代理请求",
                "代码复用，维护简单"
            ]
        })