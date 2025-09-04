# Flask + MCP Framework 集成示例

这个项目展示了如何在Flask应用中集成MCP Framework，实现传统REST API和AI友好的MCP工具并存的架构。

## 🏗️ 项目结构

```
flask_project_structure_example/
├── app/
│   ├── __init__.py              # Flask应用工厂
│   ├── mcp_config.py            # MCP服务器配置
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py      # 用户服务 + MCP工具
│   │   └── product_service.py   # 产品服务 + MCP工具
│   └── routes/
│       ├── __init__.py
│       └── api.py               # Flask REST API路由
├── run.py                       # 主启动文件
├── requirements.txt             # 项目依赖
└── README.md                    # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

启动后会同时运行：
- **Flask API**: http://localhost:5001
- **MCP服务器**: http://localhost:8080

## 🔧 架构特点

### 双重接口设计

这个项目的核心特点是**同一业务逻辑，双重访问接口**：

1. **Flask REST API** - 适合传统Web应用
2. **MCP工具接口** - 适合AI代理和智能助手

### 服务层设计

每个服务类（如`UserService`、`ProductService`）都包含：

- **业务逻辑方法** - 核心业务功能
- **Flask API方法** - 供REST API调用
- **MCP工具注册** - 供AI代理调用

```python
class UserService:
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self._register_mcp_tools()  # 注册MCP工具
    
    def _register_mcp_tools(self):
        @self.mcp_server.tool("获取用户信息")
        async def get_user_info(user_id: int):
            # 调用内部业务逻辑
            return self.get_user_by_id(user_id)
    
    def get_user_by_id(self, user_id: int):
        # 核心业务逻辑
        return self.users_db.get(user_id)
```

## 📡 API测试

### Flask REST API

```bash
# 获取首页信息
curl http://localhost:5001/

# 获取所有用户
curl http://localhost:5001/api/users

# 获取单个用户
curl http://localhost:5001/api/users/1

# 创建用户
curl -X POST http://localhost:5001/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "新用户", "email": "new@example.com", "role": "user"}'

# 获取所有产品
curl http://localhost:5001/api/products

# 按分类获取产品
curl "http://localhost:5001/api/products?category=electronics"
```

### MCP工具接口

```bash
# 获取可用工具列表
curl http://localhost:8080/tools/list

# 调用用户相关工具
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_user_info", "arguments": {"user_id": 1}}'

curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_all_users", "arguments": {}}'

# 调用产品相关工具
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_products_list", "arguments": {"category": "electronics", "limit": 5}}'

curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "search_products", "arguments": {"keyword": "手机"}}'

# 获取分类统计
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_category_stats", "arguments": {}}'
```

## 🎯 使用场景

### 1. 传统Web应用

使用Flask REST API为Web前端、移动应用提供数据接口：

```javascript
// 前端JavaScript调用
fetch('/api/users')
  .then(response => response.json())
  .then(data => console.log(data));
```

### 2. AI代理集成

使用MCP工具让AI助手访问你的业务数据：

```python
# AI代理可以调用
await mcp_client.call_tool("get_user_info", {"user_id": 123})
await mcp_client.call_tool("search_products", {"keyword": "笔记本"})
```

### 3. 混合场景

- Web应用处理用户交互
- AI助手提供智能推荐和查询
- 共享同一套业务逻辑和数据

## 🔄 扩展指南

### 添加新服务

1. 在`app/services/`下创建新的服务文件
2. 实现业务逻辑和MCP工具注册
3. 在`app/__init__.py`中初始化服务
4. 在`app/routes/api.py`中添加对应的REST API

### 添加数据库

```python
# 在服务类中集成数据库
from flask_sqlalchemy import SQLAlchemy

class UserService:
    def __init__(self, mcp_server, db):
        self.mcp_server = mcp_server
        self.db = db
        # ...
```

### 添加认证

```python
# 在MCP工具中添加认证
@self.mcp_server.tool("获取用户信息")
async def get_user_info(user_id: int, auth_token: str):
    if not self.verify_token(auth_token):
        raise ValueError("认证失败")
    # ...
```

## 🎉 优势总结

1. **代码复用** - 同一业务逻辑支持多种访问方式
2. **架构清晰** - 服务层、路由层分离
3. **易于扩展** - 新增功能只需在服务层实现
4. **AI友好** - 自动为AI代理提供工具接口
5. **向后兼容** - 不影响现有Flask应用

## 📝 注意事项

1. **端口冲突** - 确保5001和8080端口可用
2. **线程安全** - 注意共享数据的线程安全性
3. **错误处理** - 在生产环境中完善错误处理
4. **性能优化** - 根据需要添加缓存和数据库连接池
5. **安全考虑** - 在生产环境中添加认证和授权

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个示例项目！