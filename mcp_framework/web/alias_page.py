#!/usr/bin/env python3
"""
别名配置管理页面
"""

import json
import logging
from aiohttp import web
from typing import Union
from ..core.config import ConfigManager, ServerConfigAdapter, ServerConfigManager
from ..core.utils import get_config_dir
from pathlib import Path

logger = logging.getLogger(__name__)


class AliasPageHandler:
    """别名配置管理页面处理器"""
    
    def __init__(self, config_manager: Union[ConfigManager, ServerConfigAdapter], mcp_server=None):
        self.config_manager = config_manager
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(f"{__name__}.AliasPageHandler")
    
    async def serve_alias_page(self, request):
        """提供别名管理页面"""
        # 获取当前端口
        current_port = "8080"  # 默认值
        if self.mcp_server:
            server_port = getattr(self.mcp_server, 'port', None)
            if server_port is None:
                # 尝试从HTTP服务器获取端口
                http_server = getattr(self.mcp_server, '_http_server', None)
                if http_server and hasattr(http_server, 'port'):
                    server_port = http_server.port
            if server_port:
                current_port = str(server_port)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>别名配置管理 - MCP Server</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
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
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}

        .header p {{
            color: #718096;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }}

        .nav-tabs {{
            display: flex;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 30px;
        }}

        .nav-tab {{
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            color: #718096;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }}

        .nav-tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}

        .nav-tab:hover {{
            color: #667eea;
            background: #f7fafc;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .alias-list {{
            margin-bottom: 30px;
        }}

        .alias-item {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .alias-info {{
            flex: 1;
        }}

        .alias-name {{
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 5px;
        }}

        .alias-details {{
            color: #718096;
            font-size: 14px;
        }}

        .alias-actions {{
            display: flex;
            gap: 10px;
        }}

        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}

        .btn-primary {{
            background: #667eea;
            color: white;
        }}

        .btn-primary:hover {{
            background: #5a67d8;
        }}

        .btn-danger {{
            background: #e53e3e;
            color: white;
        }}

        .btn-danger:hover {{
            background: #c53030;
        }}

        .btn-secondary {{
            background: #718096;
            color: white;
        }}

        .btn-secondary:hover {{
            background: #4a5568;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4a5568;
        }}

        .form-input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }}

        .form-input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .form-textarea {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            min-height: 100px;
            resize: vertical;
            transition: border-color 0.3s ease;
        }}

        .form-textarea:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}

        .alert-success {{
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            color: #22543d;
        }}

        .alert-error {{
            background: #fed7d7;
            border: 1px solid #feb2b2;
            color: #742a2a;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #718096;
        }}

        .empty-state h3 {{
            margin-bottom: 10px;
            color: #4a5568;
        }}

        .loading {{
            text-align: center;
            padding: 40px;
            color: #718096;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #718096;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏷️ 别名配置管理</h1>
            <p>管理 MCP 服务器实例的别名配置</p>
        </div>

        <a href="/config" class="back-link">← 返回配置页面</a>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('list')">别名列表</button>
            <button class="nav-tab" onclick="showTab('create')">创建别名</button>
            <button class="nav-tab" onclick="showTab('import')">导入配置</button>
        </div>

        <!-- 别名列表标签页 -->
        <div id="list-tab" class="tab-content active">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="alias-count">-</div>
                    <div class="stat-label">别名配置</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="port-count">-</div>
                    <div class="stat-label">端口配置</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-count">-</div>
                    <div class="stat-label">总配置数</div>
                </div>
            </div>

            <div class="alias-list" id="alias-list">
                <div class="loading">正在加载别名配置...</div>
            </div>
        </div>

        <!-- 创建别名标签页 -->
        <div id="create-tab" class="tab-content">
            <form id="create-alias-form">
                <div class="form-group">
                    <label class="form-label" for="alias-name">别名名称</label>
                    <input type="text" id="alias-name" name="alias" class="form-input" 
                           placeholder="例如: my-server" required>
                </div>

                <div class="form-group">
                    <label class="form-label" for="server-name">服务器名称</label>
                    <input type="text" id="server-name" name="server_name" class="form-input" 
                           placeholder="例如: 数据处理服务器" required>
                </div>

                <div class="form-group">
                    <label class="form-label" for="server-port">端口</label>
                    <input type="number" id="server-port" name="port" class="form-input" 
                           placeholder="8080" min="1" max="65535" value="8080">
                </div>

                <div class="form-group">
                    <label class="form-label" for="server-host">主机地址</label>
                    <input type="text" id="server-host" name="host" class="form-input" 
                           placeholder="0.0.0.0" value="0.0.0.0">
                </div>

                <div class="form-group">
                    <label class="form-label" for="log-level">日志级别</label>
                    <select id="log-level" name="log_level" class="form-input">
                        <option value="DEBUG">DEBUG</option>
                        <option value="INFO" selected>INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                    </select>
                </div>

                <button type="submit" class="btn btn-primary">创建别名配置</button>
            </form>
        </div>

        <!-- 导入配置标签页 -->
        <div id="import-tab" class="tab-content">
            <div class="form-group">
                <label class="form-label" for="config-file">选择配置文件</label>
                <input type="file" id="config-file" accept=".json" class="form-input">
            </div>

            <div class="form-group">
                <label class="form-label" for="import-alias">导入后的别名</label>
                <input type="text" id="import-alias" class="form-input" 
                       placeholder="为导入的配置指定别名">
            </div>

            <button onclick="importConfig()" class="btn btn-primary">导入配置</button>
        </div>

        <!-- 消息提示区域 -->
        <div id="message-area"></div>
    </div>

    <script>
        let currentTab = 'list';

        // 显示标签页
        function showTab(tabName) {{
            // 隐藏所有标签页
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // 显示选中的标签页
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            currentTab = tabName;

            // 如果是列表标签页，刷新数据
            if (tabName === 'list') {{
                loadAliases();
            }}
        }}

        // 显示消息
        function showMessage(message, type = 'success') {{
            const messageArea = document.getElementById('message-area');
            const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
            messageArea.innerHTML = `<div class="alert ${{alertClass}}">${{message}}</div>`;
            
            // 3秒后自动隐藏
            setTimeout(() => {{
                messageArea.innerHTML = '';
            }}, 3000);
        }}

        // 加载别名列表
        async function loadAliases() {{
            try {{
                const response = await fetch('/api/aliases');
                const data = await response.json();
                
                if (response.ok) {{
                    displayAliases(data);
                    updateStats(data);
                }} else {{
                    throw new Error(data.error || '加载失败');
                }}
            }} catch (error) {{
                document.getElementById('alias-list').innerHTML = 
                    `<div class="empty-state">
                        <h3>加载失败</h3>
                        <p>${{error.message}}</p>
                        <button onclick="loadAliases()" class="btn btn-primary">重试</button>
                    </div>`;
            }}
        }}

        // 显示别名列表
        function displayAliases(data) {{
            const aliasListElement = document.getElementById('alias-list');
            
            if (data.aliases.length === 0 && data.ports.length === 0) {{
                aliasListElement.innerHTML = 
                    `<div class="empty-state">
                        <h3>暂无配置</h3>
                        <p>点击"创建别名"标签页开始创建第一个别名配置</p>
                    </div>`;
                return;
            }}

            let html = '';

            // 显示别名配置
            if (data.aliases.length > 0) {{
                html += '<h3>🏷️ 别名配置</h3>';
                data.aliases.forEach(alias => {{
                    html += `
                        <div class="alias-item">
                            <div class="alias-info">
                                <div class="alias-name">${{alias.server_name}} (别名: ${{alias.alias}})</div>
                                <div class="alias-details">
                                    端口: ${{alias.port || '未设置'}} | 
                                    主机: ${{alias.host || '未设置'}} | 
                                    日志级别: ${{alias.log_level || '未设置'}}
                                </div>
                            </div>
                            <div class="alias-actions">
                                <button onclick="editAlias('${{alias.alias}}')" class="btn btn-secondary">编辑</button>
                                <button onclick="deleteAlias('${{alias.alias}}')" class="btn btn-danger">删除</button>
                            </div>
                        </div>
                    `;
                }});
            }}

            // 显示端口配置
            if (data.ports.length > 0) {{
                html += '<h3>🔌 端口配置</h3>';
                data.ports.forEach(port => {{
                    html += `
                        <div class="alias-item">
                            <div class="alias-info">
                                <div class="alias-name">${{port.server_name}} (端口: ${{port.port}})</div>
                                <div class="alias-details">
                                    主机: ${{port.host || '未设置'}} | 
                                    日志级别: ${{port.log_level || '未设置'}}
                                </div>
                            </div>
                            <div class="alias-actions">
                                <button onclick="deletePortConfig(${{port.port}})" class="btn btn-danger">删除</button>
                            </div>
                        </div>
                    `;
                }});
            }}

            aliasListElement.innerHTML = html;
        }}

        // 更新统计信息
        function updateStats(data) {{
            document.getElementById('alias-count').textContent = data.aliases.length;
            document.getElementById('port-count').textContent = data.ports.length;
            document.getElementById('total-count').textContent = data.total_configs;
        }}

        // 创建别名配置
        document.getElementById('create-alias-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            try {{
                const response = await fetch('/api/aliases', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(data)
                }});
                
                const result = await response.json();
                
                if (response.ok) {{
                    showMessage('别名配置创建成功！');
                    e.target.reset();
                    // 切换到列表标签页
                    showTab('list');
                }} else {{
                    throw new Error(result.error || '创建失败');
                }}
            }} catch (error) {{
                showMessage(error.message, 'error');
            }}
        }});

        // 删除别名配置
        async function deleteAlias(alias) {{
            if (!confirm(`确定要删除别名 "${{alias}}" 的配置吗？`)) {{
                return;
            }}
            
            try {{
                const response = await fetch(`/api/aliases/${{alias}}`, {{
                    method: 'DELETE'
                }});
                
                const result = await response.json();
                
                if (response.ok) {{
                    showMessage('别名配置删除成功！');
                    loadAliases();
                }} else {{
                    throw new Error(result.error || '删除失败');
                }}
            }} catch (error) {{
                showMessage(error.message, 'error');
            }}
        }}

        // 删除端口配置
        async function deletePortConfig(port) {{
            if (!confirm(`确定要删除端口 "${{port}}" 的配置吗？`)) {{
                return;
            }}
            
            try {{
                const response = await fetch(`/api/ports/${{port}}`, {{
                    method: 'DELETE'
                }});
                
                const result = await response.json();
                
                if (response.ok) {{
                    showMessage('端口配置删除成功！');
                    loadAliases();
                }} else {{
                    throw new Error(result.error || '删除失败');
                }}
            }} catch (error) {{
                showMessage(error.message, 'error');
            }}
        }}

        // 编辑别名配置
        function editAlias(alias) {{
            // 这里可以实现编辑功能
            showMessage('编辑功能正在开发中...', 'error');
        }}

        // 导入配置
        function importConfig() {{
            const fileInput = document.getElementById('config-file');
            const aliasInput = document.getElementById('import-alias');
            
            if (!fileInput.files[0]) {{
                showMessage('请选择配置文件', 'error');
                return;
            }}
            
            if (!aliasInput.value.trim()) {{
                showMessage('请输入别名', 'error');
                return;
            }}
            
            // 这里可以实现导入功能
            showMessage('导入功能正在开发中...', 'error');
        }}

        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', () => {{
            loadAliases();
        }});
    </script>
</body>
</html>
        """
        
        return web.Response(text=html_content, content_type='text/html')

    async def get_aliases(self, request):
        """获取所有别名配置"""
        try:
            config_dir = get_config_dir()
            
            # 搜索所有别名配置文件
            alias_configs = []
            alias_pattern = "*_alias_*_server_config.json"
            for config_file in config_dir.glob(alias_pattern):
                try:
                    filename = config_file.stem
                    # 提取服务器名称和别名
                    parts = filename.split('_alias_')
                    if len(parts) == 2:
                        server_name = parts[0]
                        alias_part = parts[1].split('_server_config')[0]
                        
                        # 读取配置文件内容
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        alias_configs.append({
                            'server_name': server_name,
                            'alias': alias_part,
                            'port': config_data.get('port'),
                            'host': config_data.get('host'),
                            'log_level': config_data.get('log_level'),
                            'config_file': str(config_file)
                        })
                except Exception as e:
                    self.logger.warning(f"解析配置文件失败: {config_file}, 错误: {e}")
            
            # 搜索所有端口配置文件
            port_configs = []
            port_pattern = "*_port_*_server_config.json"
            for config_file in config_dir.glob(port_pattern):
                try:
                    filename = config_file.stem
                    # 提取服务器名称和端口
                    parts = filename.split('_port_')
                    if len(parts) == 2:
                        server_name = parts[0]
                        port_part = parts[1].split('_server_config')[0]
                        
                        # 读取配置文件内容
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        port_configs.append({
                            'server_name': server_name,
                            'port': int(port_part),
                            'host': config_data.get('host'),
                            'log_level': config_data.get('log_level'),
                            'config_file': str(config_file)
                        })
                except Exception as e:
                    self.logger.warning(f"解析配置文件失败: {config_file}, 错误: {e}")
            
            return web.json_response({
                'aliases': alias_configs,
                'ports': port_configs,
                'total_configs': len(alias_configs) + len(port_configs)
            })
            
        except Exception as e:
            self.logger.error(f"获取别名配置失败: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def create_alias(self, request):
        """创建新的别名配置"""
        try:
            data = await request.json()
            
            alias = data.get('alias', '').strip()
            server_name = data.get('server_name', '').strip()
            
            if not alias or not server_name:
                return web.json_response({'error': '别名和服务器名称不能为空'}, status=400)
            
            # 创建配置管理器
            config_manager = ServerConfigManager.create_for_alias(server_name, alias)
            
            # 检查配置是否已存在
            if config_manager.config_exists():
                return web.json_response({'error': f'别名 "{alias}" 的配置已存在'}, status=400)
            
            # 创建配置
            config_data = {
                'host': data.get('host', '0.0.0.0'),
                'port': int(data.get('port', 8080)),
                'log_level': data.get('log_level', 'INFO'),
                'log_file': None,
                'default_dir': None,
                'max_connections': 100,
                'timeout': 30
            }
            
            # 保存配置
            if config_manager.save_server_config(config_data):
                return web.json_response({'message': '别名配置创建成功'})
            else:
                return web.json_response({'error': '保存配置失败'}, status=500)
                
        except Exception as e:
            self.logger.error(f"创建别名配置失败: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_alias(self, request):
        """删除别名配置"""
        try:
            alias = request.match_info['alias']
            
            # 查找对应的配置文件
            config_dir = get_config_dir()
            alias_pattern = f"*_alias_{alias}_server_config.json"
            
            config_files = list(config_dir.glob(alias_pattern))
            if not config_files:
                return web.json_response({'error': f'未找到别名 "{alias}" 的配置'}, status=404)
            
            # 删除配置文件
            for config_file in config_files:
                config_file.unlink()
                self.logger.info(f"已删除配置文件: {config_file}")
            
            return web.json_response({'message': '别名配置删除成功'})
            
        except Exception as e:
            self.logger.error(f"删除别名配置失败: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_port_config(self, request):
        """删除端口配置"""
        try:
            port = int(request.match_info['port'])
            
            # 查找对应的配置文件
            config_dir = get_config_dir()
            port_pattern = f"*_port_{port}_server_config.json"
            
            config_files = list(config_dir.glob(port_pattern))
            if not config_files:
                return web.json_response({'error': f'未找到端口 "{port}" 的配置'}, status=404)
            
            # 删除配置文件
            for config_file in config_files:
                config_file.unlink()
                self.logger.info(f"已删除配置文件: {config_file}")
            
            return web.json_response({'message': '端口配置删除成功'})
            
        except Exception as e:
            self.logger.error(f"删除端口配置失败: {e}")
            return web.json_response({'error': str(e)}, status=500)