import json
import logging
from aiohttp import web
from typing import Union
from ..core.config import ConfigManager, ServerConfigAdapter

logger = logging.getLogger(__name__)


class ConfigPageHandler:
    """配置页面处理器"""
    
    def __init__(self, config_manager: Union[ConfigManager, ServerConfigAdapter], mcp_server=None):
        self.config_manager = config_manager
        self.mcp_server = mcp_server
    
    async def serve_config_page(self, request):
        """提供配置页面"""
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
        
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Server Configuration</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #4a5568;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .config-section {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #2d3748;
            font-weight: 500;
        }

        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }

        .help-text {
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }

        button {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            flex: 1;
        }

        .btn-primary {
            background: #4299e1;
            color: white;
        }

        .btn-primary:hover {
            background: #3182ce;
        }

        .btn-warning {
            background: #ed8936;
            color: white;
        }

        .btn-warning:hover {
            background: #dd6b20;
        }

        .btn-secondary {
            background: #718096;
            color: white;
        }

        .btn-secondary:hover {
            background: #4a5568;
        }

        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: none;
        }

        .alert.success {
            background: #c6f6d5;
            color: #2f855a;
            border: 1px solid #9ae6b4;
        }

        .alert.error {
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #feb2b2;
        }

        .alert.warning {
            background: #fefcbf;
            color: #975a16;
            border: 1px solid #faf089;
        }

        .current-config {
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .current-config h3 {
            margin: 0 0 10px 0;
            color: #2d3748;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #e2e8f0;
        }

        .config-item:last-child {
            border-bottom: none;
        }

        .config-key {
            font-weight: 500;
            color: #4a5568;
        }

        .config-value {
            color: #2d3748;
        }

        .navigation {
            text-align: center;
            margin-top: 30px;
        }

        .nav-link {
            color: #4299e1;
            text-decoration: none;
            margin: 0 15px;
            padding: 10px 20px;
            border: 1px solid #4299e1;
            border-radius: 6px;
            display: inline-block;
            transition: all 0.2s;
        }

        .nav-link:hover {
            background: #4299e1;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>⚙️</span>
                系统配置
            </h1>
            <p>管理 MCP HTTP 服务器的系统配置</p>
        </div>

        <div id="alert" class="alert"></div>

        <div class="current-config">
            <h3>📋 当前配置</h3>
            <div id="current-config-content">
                <!-- 当前配置将通过 JavaScript 加载 -->
            </div>
        </div>

        <form id="configForm">
            <div class="config-section">
                <div class="section-title">🌐 服务器设置</div>

                <div class="form-group">
                    <label for="alias">服务器别名</label>
                    <input type="text" id="alias" name="alias" placeholder="例如: data-server">
                    <div class="help-text">为服务器实例设置别名，用于多实例管理和客户端连接</div>
                </div>

                <div class="form-group">
                    <label for="host">服务器地址</label>
                    <input type="text" id="host" name="host" placeholder="0.0.0.0" value="0.0.0.0" disabled>
                    <div class="help-text">固定为 0.0.0.0 以监听所有网络接口，允许外部访问</div>
                </div>

                <div class="form-group">
                    <label for="port">端口号</label>
                    <input type="number" id="port" name="port" min="1" max="65535" placeholder="{current_port}">
                    <div class="help-text">服务器监听的端口号，修改后需要重启服务器才能生效</div>
                </div>

                <div class="form-group">
                    <label for="max_connections">最大连接数</label>
                    <input type="number" id="max_connections" name="max_connections" min="1" placeholder="100">
                    <div class="help-text">服务器允许的最大并发连接数</div>
                </div>

                <div class="form-group">
                    <label for="timeout">请求超时时间</label>
                    <input type="number" id="timeout" name="timeout" min="1" placeholder="30">
                    <div class="help-text">请求超时时间（秒）</div>
                </div>
            </div>

            <div class="config-section">
                <div class="section-title">📝 日志设置</div>

                <div class="form-group">
                    <label for="log_level">日志级别</label>
                    <select id="log_level" name="log_level">
                        <option value="DEBUG">DEBUG - 详细调试信息</option>
                        <option value="INFO">INFO - 一般信息</option>
                        <option value="WARNING">WARNING - 警告信息</option>
                        <option value="ERROR">ERROR - 错误信息</option>
                        <option value="CRITICAL">CRITICAL - 严重错误</option>
                    </select>
                    <div class="help-text">设置日志输出的详细程度</div>
                </div>

                <div class="form-group">
                    <label for="log_file">日志文件名</label>
                    <input type="text" id="log_file" name="log_file" placeholder="server.log">
                    <div class="help-text">日志文件名，留空则不保存到文件</div>
                </div>
            </div>

            <div class="config-section">
                <div class="section-title">📁 路径设置</div>

                <div class="form-group">
                    <label for="default_dir">默认工作目录</label>
                    <input type="text" id="default_dir" name="default_dir" placeholder="">
                    <div class="help-text">服务器的默认工作目录，留空使用当前目录</div>
                </div>
            </div>

            <div class="button-group">
                <button type="submit" class="btn-primary">
                    💾 保存配置
                </button>
                <button type="button" class="btn-warning" onclick="restartServer()">
                    ♻️ 重启服务器
                </button>
                <button type="button" class="btn-warning" onclick="resetConfig()">
                    🔄 重置为默认
                </button>
                <button type="button" class="btn-secondary" onclick="loadConfig()">
                    📥 重新加载
                </button>
            </div>
        </form>

        <div class="navigation">
            <a href="/aliases" class="nav-link">🏷️ 别名管理</a>
            <a href="/setup" class="nav-link">🚀 服务器设置</a>
            <a href="/test" class="nav-link">🧪 测试页面</a>
            <a href="/health" class="nav-link">💚 健康检查</a>
            <a href="/info" class="nav-link">ℹ️ 服务器信息</a>
        </div>
    </div>

    <script>
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
        });

        // 加载当前配置
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();

                // 填充表单
                Object.keys(config).forEach(key => {
                    const input = document.getElementById(key);
                    if (input) {
                        input.value = config[key] || '';
                    }
                });

                // 显示当前配置
                displayCurrentConfig(config);

            } catch (error) {
                showAlert('加载配置失败: ' + error.message, 'error');
            }
        }

        // 显示当前配置
        function displayCurrentConfig(config) {
            const container = document.getElementById('current-config-content');
            container.innerHTML = '';

            const configItems = [
                { key: 'alias', label: '服务器别名', value: config.alias || '未设置' },
                { key: 'host', label: '服务器地址', value: config.host },
                { key: 'port', label: '端口号', value: config.port },
                { key: 'log_level', label: '日志级别', value: config.log_level },
                { key: 'log_file', label: '日志文件', value: config.log_file || '无' },
                { key: 'default_dir', label: '默认目录', value: config.default_dir || '当前目录' },
                { key: 'max_connections', label: '最大连接数', value: config.max_connections },
                { key: 'timeout', label: '超时时间', value: config.timeout + ' 秒' }
            ];

            configItems.forEach(item => {
                const configItem = document.createElement('div');
                configItem.className = 'config-item';

                const keySpan = document.createElement('span');
                keySpan.className = 'config-key';
                keySpan.textContent = item.label;

                const valueSpan = document.createElement('span');
                valueSpan.className = 'config-value';
                valueSpan.textContent = item.value;

                configItem.appendChild(keySpan);
                configItem.appendChild(valueSpan);
                container.appendChild(configItem);
            });
        }

        // 表单提交处理
        document.getElementById('configForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const config = {};

            // 收集表单数据
            for (let [key, value] of formData.entries()) {
                if (value.trim()) {
                    if (key === 'port' || key === 'max_connections' || key === 'timeout') {
                        config[key] = parseInt(value);
                    } else {
                        config[key] = value.trim();
                    }
                }
            }

            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config)
                });

                const result = await response.json();

                if (result.success) {
                    showAlert('配置保存成功！重启服务器后生效。', 'success');
                    loadConfig(); // 重新加载配置
                } else {
                    showAlert('配置保存失败: ' + result.message, 'error');
                }
            } catch (error) {
                showAlert('配置保存失败: ' + error.message, 'error');
            }
        });

        // 重置配置
        async function resetConfig() {
            if (!confirm('确定要重置配置为默认值吗？此操作不可撤销。')) {
                return;
            }

            try {
                const response = await fetch('/api/config/reset', {
                    method: 'POST'
                });

                const result = await response.json();

                if (result.success) {
                    showAlert('配置已重置为默认值！', 'warning');
                    loadConfig(); // 重新加载配置
                } else {
                    showAlert('重置配置失败: ' + result.message, 'error');
                }
            } catch (error) {
                showAlert('重置配置失败: ' + error.message, 'error');
            }
        }

        // 重启服务器
        async function restartServer() {
            if (!confirm('确认重启服务器以应用新配置吗？当前连接将暂时中断。')) {
                return;
            }
            try {
                const response = await fetch('/api/server/restart', {
                    method: 'POST'
                });
                const result = await response.json();
                if (result.success) {
                    showAlert(result.message || '服务器即将重启以应用新配置…', 'success');
                    // 等待一段时间后刷新页面
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    showAlert('重启失败: ' + (result.message || '未知错误'), 'error');
                }
            } catch (error) {
                showAlert('重启请求失败: ' + error.message, 'error');
            }
        }

        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert ${type}`;
            alert.style.display = 'block';

            // 5秒后自动隐藏
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>
""".format(current_port=current_port)
        
        return web.Response(text=html_content, content_type='text/html')
