#!/usr/bin/env python3
"""
MCP 服务器设置页面
"""

import logging
from aiohttp import web
from ..core.base import BaseMCPServer

logger = logging.getLogger(__name__)


class SetupPageHandler:
    """设置页面处理器"""

    def __init__(self, mcp_server: BaseMCPServer):
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.SetupPageHandler")

    async def serve_setup_page(self, request):
        """服务器设置页面"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Server Setup - {self.mcp_server.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .header h1 {{
            color: #4a5568;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}

        .status {{
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 500;
        }}

        .status.not-configured {{
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #feb2b2;
        }}

        .status.configured {{
            background: #c6f6d5;
            color: #2f855a;
            border: 1px solid #9ae6b4;
        }}

        .status.running {{
            background: #bee3f8;
            color: #2b6cb0;
            border: 1px solid #90cdf4;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        label {{
            display: block;
            margin-bottom: 5px;
            color: #2d3748;
            font-weight: 500;
        }}

        .required {{
            color: #e53e3e;
        }}

        input, select, textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }}

        input:focus, select:focus, textarea:focus {{
            outline: none;
            border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }}

        .help-text {{
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
        }}

        .button-group {{
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }}

        button {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            flex: 1;
        }}

        .btn-primary {{
            background: #4299e1;
            color: white;
        }}

        .btn-primary:hover {{
            background: #3182ce;
        }}

        .btn-success {{
            background: #48bb78;
            color: white;
        }}

        .btn-success:hover {{
            background: #38a169;
        }}

        .btn-secondary {{
            background: #718096;
            color: white;
        }}

        .btn-secondary:hover {{
            background: #4a5568;
        }}

        .alert {{
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: none;
        }}

        .alert.success {{
            background: #c6f6d5;
            color: #2f855a;
            border: 1px solid #9ae6b4;
        }}

        .alert.error {{
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #feb2b2;
        }}

        .server-info {{
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}

        .server-info h3 {{
            margin: 0 0 10px 0;
            color: #2d3748;
        }}

        .navigation {{
            text-align: center;
            margin-top: 20px;
        }}

        .nav-link {{
            color: #4299e1;
            text-decoration: none;
            margin: 0 10px;
        }}

        .nav-link:hover {{
            text-decoration: underline;
        }}

        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>🚀</span>
                MCP Server Setup
            </h1>
            <p>配置并启动 <strong>{self.mcp_server.name}</strong> v{self.mcp_server.version}</p>
        </div>

        <div id="status" class="status not-configured">
            ⚙️ 服务器尚未配置，请填写下方参数
        </div>

        <div class="server-info">
            <h3>📋 服务器信息</h3>
            <p><strong>名称:</strong> {self.mcp_server.name}</p>
            <p><strong>版本:</strong> {self.mcp_server.version}</p>
            <p><strong>描述:</strong> {self.mcp_server.description}</p>
        </div>

        <div id="alert" class="alert"></div>

        <form id="configForm">
            <div id="parameters">
                <!-- 参数将通过 JavaScript 动态加载 -->
            </div>

            <div class="button-group">
                <button type="submit" class="btn-primary" id="configBtn">
                    💾 保存配置
                </button>
                <button type="button" class="btn-success hidden" id="startBtn">
                    🚀 启动服务器
                </button>
                <button type="button" class="btn-secondary" onclick="loadStatus()">
                    🔄 刷新状态
                </button>
            </div>
        </form>

        <div class="navigation">
            <a href="/test" class="nav-link">🧪 测试页面</a>
            <a href="/config" class="nav-link">⚙️ 系统配置</a>
        </div>
    </div>

    <script>
        let serverParameters = [];
        let serverStatus = {{}};

        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {{
            loadParameters();
            loadStatus();
        }});

        // 加载服务器参数定义
        async function loadParameters() {{
            try {{
                const response = await fetch('/api/server/parameters');
                const result = await response.json();

                if (result.success) {{
                    serverParameters = result.parameters;
                    renderParameters();
                }} else {{
                    showAlert('加载参数失败: ' + result.message, 'error');
                }}
            }} catch (error) {{
                showAlert('加载参数失败: ' + error.message, 'error');
            }}
        }}

        // 渲染参数表单
        function renderParameters() {{
            const container = document.getElementById('parameters');
            container.innerHTML = '';

            serverParameters.forEach(param => {{
                const formGroup = document.createElement('div');
                formGroup.className = 'form-group';

                const label = document.createElement('label');
                label.setAttribute('for', param.name);
                label.innerHTML = param.display_name + (param.required ? ' <span class="required">*</span>' : '');

                let input;
                if (param.type === 'select') {{
                    input = document.createElement('select');
                    param.options.forEach(option => {{
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = option;
                        if (option === param.default_value) {{
                            optionElement.selected = true;
                        }}
                        input.appendChild(optionElement);
                    }});
                }} else if (param.type === 'boolean') {{
                    input = document.createElement('select');
                    const trueOption = document.createElement('option');
                    trueOption.value = 'true';
                    trueOption.textContent = '是';
                    const falseOption = document.createElement('option');
                    falseOption.value = 'false';
                    falseOption.textContent = '否';

                    if (param.default_value === true) {{
                        trueOption.selected = true;
                    }} else {{
                        falseOption.selected = true;
                    }}

                    input.appendChild(trueOption);
                    input.appendChild(falseOption);
                }} else {{
                    input = document.createElement('input');
                    input.type = param.type === 'integer' ? 'number' : 'text';
                    if (param.default_value !== null) {{
                        input.value = param.default_value;
                    }}
                    if (param.placeholder) {{
                        input.placeholder = param.placeholder;
                    }}
                }}

                input.id = param.name;
                input.name = param.name;
                input.required = param.required;

                const helpText = document.createElement('div');
                helpText.className = 'help-text';
                helpText.textContent = param.description;

                formGroup.appendChild(label);
                formGroup.appendChild(input);
                formGroup.appendChild(helpText);
                container.appendChild(formGroup);
            }});
        }}

        // 加载服务器状态
        async function loadStatus() {{
            try {{
                const response = await fetch('/api/server/status');
                serverStatus = await response.json();
                updateStatusDisplay();

                // 如果已配置，填充表单
                if (serverStatus.configured && serverStatus.config) {{
                    fillFormWithConfig(serverStatus.config);
                }}
            }} catch (error) {{
                console.error('Failed to load status:', error);
            }}
        }}

            // 更新状态显示
        function updateStatusDisplay() {{
            const statusDiv = document.getElementById('status');
            const configBtn = document.getElementById('configBtn');
            const startBtn = document.getElementById('startBtn');
            
            if (serverStatus.initialized) {{
                statusDiv.className = 'status running';
                statusDiv.innerHTML = '✅ 服务器正在运行';
                configBtn.textContent = '💾 更新配置';
                configBtn.style.display = 'block';
                startBtn.style.display = 'none';
            }} else if (serverStatus.configured) {{
                statusDiv.className = 'status configured';
                statusDiv.innerHTML = '⚙️ 服务器已配置，点击启动按钮开始运行';
                configBtn.textContent = '💾 更新配置';
                startBtn.classList.remove('hidden');
            }} else {{
                statusDiv.className = 'status not-configured';
                statusDiv.innerHTML = '⚙️ 服务器尚未配置，请填写下方参数';
                configBtn.textContent = '💾 保存配置';
                startBtn.classList.add('hidden');
            }}
        }}
        
        // 用配置填充表单
        function fillFormWithConfig(config) {{
            Object.keys(config).forEach(key => {{
                const input = document.getElementById(key);
                if (input) {{
                    input.value = config[key];
                }}
            }});
        }}
        
        // 表单提交处理
        document.getElementById('configForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const config = {{}};
            
            serverParameters.forEach(param => {{
                const value = formData.get(param.name);
                if (value !== null && value !== '') {{
                    if (param.type === 'integer') {{
                        config[param.name] = parseInt(value);
                    }} else if (param.type === 'boolean') {{
                        config[param.name] = value === 'true';
                    }} else {{
                        config[param.name] = value;
                    }}
                }}
            }});
            
            try {{
                const response = await fetch('/api/server/configure', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ config: config }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showAlert('配置保存成功！', 'success');
                    loadStatus(); // 重新加载状态
                }} else {{
                    showAlert('配置保存失败: ' + result.message, 'error');
                }}
            }} catch (error) {{
                showAlert('配置保存失败: ' + error.message, 'error');
            }}
        }});
        
        // 启动服务器
        document.getElementById('startBtn').addEventListener('click', async function() {{
            try {{
                const response = await fetch('/api/server/start', {{
                    method: 'POST'
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showAlert('服务器启动成功！', 'success');
                    loadStatus(); // 重新加载状态
                    
                    // 3秒后跳转到测试页面
                    setTimeout(() => {{
                        window.location.href = '/test';
                    }}, 3000);
                }} else {{
                    showAlert('服务器启动失败: ' + result.message, 'error');
                }}
            }} catch (error) {{
                showAlert('服务器启动失败: ' + error.message, 'error');
            }}
        }});
        
        function showAlert(message, type) {{
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert ${{type}}`;
            alert.style.display = 'block';
            
            // 5秒后自动隐藏
            setTimeout(() => {{
                alert.style.display = 'none';
            }}, 5000);
        }}
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type='text/html')

