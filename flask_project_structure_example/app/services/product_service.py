#!/usr/bin/env python3
"""
产品服务模块
包含产品相关的业务逻辑和MCP工具注册
"""

import time
from typing import Dict, List, Any, Annotated

class ProductService:
    """产品服务类"""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.products_db = {}  # 模拟数据库
        self._init_sample_data()
        self._register_mcp_tools()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        self.products_db = {
            1: {
                "id": 1,
                "name": "MacBook Pro",
                "category": "electronics",
                "price": 12999.00,
                "stock": 50,
                "description": "苹果笔记本电脑"
            },
            2: {
                "id": 2,
                "name": "iPhone 15",
                "category": "electronics",
                "price": 5999.00,
                "stock": 100,
                "description": "苹果智能手机"
            },
            3: {
                "id": 3,
                "name": "咖啡杯",
                "category": "home",
                "price": 29.90,
                "stock": 200,
                "description": "陶瓷咖啡杯"
            },
            4: {
                "id": 4,
                "name": "办公椅",
                "category": "furniture",
                "price": 899.00,
                "stock": 30,
                "description": "人体工学办公椅"
            }
        }
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        
        @self.mcp_server.tool("获取产品信息")
        async def get_product_info(
            product_id: Annotated[int, "产品ID，必须是正整数"]
        ) -> Dict[str, Any]:
            """根据产品ID获取产品详细信息"""
            product = self.get_product_by_id(product_id)
            if product:
                return {
                    "success": True,
                    "product": product,
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": f"产品 {product_id} 不存在",
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("获取产品列表")
        async def get_products_list(
            category: Annotated[str, "产品分类筛选，可选值：all, electronics, home, furniture"] = "all",
            limit: Annotated[int, "返回结果数量限制，范围：1-100"] = 10
        ) -> Dict[str, Any]:
            """获取产品列表，支持按分类筛选"""
            products = list(self.products_db.values())
            
            if category != "all":
                products = [p for p in products if p["category"] == category]
            
            # 限制返回数量
            products = products[:limit]
            
            return {
                "success": True,
                "products": products,
                "total": len(products),
                "category": category,
                "timestamp": time.time()
            }
        
        @self.mcp_server.tool("搜索产品")
        async def search_products(
            keyword: Annotated[str, "搜索关键词，将在产品名称和描述中查找"],
            category: Annotated[str, "产品分类筛选，可选值：all, electronics, home, furniture"] = "all"
        ) -> Dict[str, Any]:
            """根据关键词搜索产品"""
            results = []
            
            for product in self.products_db.values():
                # 检查分类筛选
                if category != "all" and product["category"] != category:
                    continue
                
                # 检查关键词匹配
                if (keyword.lower() in product["name"].lower() or 
                    keyword.lower() in product["description"].lower()):
                    
                    # 计算相关性分数
                    relevance = 0.0
                    if keyword.lower() in product["name"].lower():
                        relevance += 0.8
                    if keyword.lower() in product["description"].lower():
                        relevance += 0.2
                    
                    result = product.copy()
                    result["relevance"] = relevance
                    results.append(result)
            
            # 按相关性排序
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            return {
                "success": True,
                "keyword": keyword,
                "category": category,
                "results": results,
                "total_found": len(results),
                "timestamp": time.time()
            }
        
        @self.mcp_server.tool("创建产品")
        async def create_product(
            name: Annotated[str, "产品名称，不能为空且不能重复"],
            category: Annotated[str, "产品分类，建议值：electronics, home, furniture"],
            price: Annotated[float, "产品价格，必须大于0"],
            stock: Annotated[int, "初始库存数量，必须大于等于0"] = 0,
            description: Annotated[str, "产品描述，可选"] = ""
        ) -> Dict[str, Any]:
            """创建新产品"""
            try:
                new_product = self.create_product_internal(name, category, price, stock, description)
                return {
                    "success": True,
                    "product": new_product,
                    "message": "产品创建成功",
                    "timestamp": time.time()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("更新库存")
        async def update_stock(
            product_id: Annotated[int, "产品ID，必须是存在的产品"],
            stock_change: Annotated[int, "库存变化量，正数表示增加，负数表示减少"]
        ) -> Dict[str, Any]:
            """更新产品库存（正数增加，负数减少）"""
            try:
                updated_product = self.update_stock_internal(product_id, stock_change)
                if updated_product:
                    return {
                        "success": True,
                        "product": updated_product,
                        "message": f"库存更新成功，变化量: {stock_change}",
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"产品 {product_id} 不存在",
                        "timestamp": time.time()
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.mcp_server.tool("获取分类统计")
        async def get_category_stats() -> Dict[str, Any]:
            """获取各分类的产品统计信息"""
            stats = {}
            
            for product in self.products_db.values():
                category = product["category"]
                if category not in stats:
                    stats[category] = {
                        "count": 0,
                        "total_stock": 0,
                        "avg_price": 0.0,
                        "products": []
                    }
                
                stats[category]["count"] += 1
                stats[category]["total_stock"] += product["stock"]
                stats[category]["products"].append(product["name"])
            
            # 计算平均价格
            for category, data in stats.items():
                category_products = [p for p in self.products_db.values() if p["category"] == category]
                if category_products:
                    data["avg_price"] = sum(p["price"] for p in category_products) / len(category_products)
            
            return {
                "success": True,
                "stats": stats,
                "total_categories": len(stats),
                "timestamp": time.time()
            }
    
    # Flask服务方法（非MCP工具）
    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Flask路由使用的方法"""
        return self.products_db.get(product_id)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Flask路由使用的方法"""
        return list(self.products_db.values())
    
    def create_product_internal(self, name: str, category: str, price: float, stock: int = 0, description: str = "") -> Dict[str, Any]:
        """内部创建产品方法"""
        # 验证输入
        if price < 0:
            raise ValueError("价格不能为负数")
        if stock < 0:
            raise ValueError("库存不能为负数")
        
        # 检查产品名称是否已存在
        for product in self.products_db.values():
            if product['name'].lower() == name.lower():
                raise ValueError(f"产品名称 '{name}' 已存在")
        
        # 生成新的产品ID
        new_id = max(self.products_db.keys()) + 1 if self.products_db else 1
        
        new_product = {
            "id": new_id,
            "name": name,
            "category": category,
            "price": price,
            "stock": stock,
            "description": description,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.products_db[new_id] = new_product
        return new_product
    
    def update_stock_internal(self, product_id: int, stock_change: int) -> Dict[str, Any]:
        """内部更新库存方法"""
        if product_id not in self.products_db:
            return None
        
        product = self.products_db[product_id]
        new_stock = product["stock"] + stock_change
        
        if new_stock < 0:
            raise ValueError(f"库存不足，当前库存: {product['stock']}, 尝试变化: {stock_change}")
        
        product["stock"] = new_stock
        product["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return product