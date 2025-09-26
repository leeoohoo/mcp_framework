"""
MCP Stdio 客户端基础类
提供与 MCP 服务器进行 stdio 通信的基础功能
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional, List, Union
from pathlib import Path


class MCPStdioClient:
    """MCP Stdio 客户端基础类"""
    
    def __init__(self, 
                 server_script: str,
                 alias: Optional[str] = None,
                 server_args: Optional[List[str]] = None,
                 client_name: str = "mcp-framework-client",
                 client_version: str = "1.0.0",
                 startup_timeout: float = 5.0,
                 response_timeout: float = 30.0):
        """
        初始化 MCP Stdio 客户端
        
        Args:
            server_script: 服务器脚本路径
            alias: 服务器别名（如果服务器支持）
            server_args: 额外的服务器参数
            client_name: 客户端名称
            client_version: 客户端版本
            startup_timeout: 启动超时时间（秒）
            response_timeout: 响应超时时间（秒）
        """
        self.server_script = server_script
        self.alias = alias
        self.server_args = server_args or []
        self.client_name = client_name
        self.client_version = client_version
        self.startup_timeout = startup_timeout
        self.response_timeout = response_timeout
        
        self.process = None
        self.request_id = 0
        self.is_connected = False
        self.is_initialized = False
    
    def get_next_id(self) -> int:
        """获取下一个请求ID"""
        self.request_id += 1
        return self.request_id
    
    async def connect(self) -> bool:
        """
        连接到 MCP 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建启动命令
            cmd = [sys.executable, self.server_script, "stdio"]
            
            # 添加别名参数
            if self.alias:
                cmd.extend(["--alias", self.alias])
            
            # 添加其他参数
            cmd.extend(self.server_args)
            
            # 启动子进程
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 给服务器一点时间启动
            await asyncio.sleep(0.1)
            
            # 检查进程是否还在运行
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                raise Exception(f"服务器启动失败: {stderr_output.decode()}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            await self.disconnect()
            raise Exception(f"连接服务器失败: {e}")
    
    async def send_request(self, 
                          method: str, 
                          params: Optional[Dict[str, Any]] = None,
                          timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        发送 JSON-RPC 请求
        
        Args:
            method: 方法名
            params: 参数字典
            timeout: 超时时间（秒），None 使用默认值
            
        Returns:
            Dict[str, Any]: 响应数据
            
        Raises:
            Exception: 通信错误或超时
        """
        if not self.is_connected:
            raise Exception("客户端未连接")
        
        # 构建请求
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.get_next_id()
        }
        
        if params:
            request["params"] = params
        
        request_json = json.dumps(request) + "\n"
        
        try:
            # 检查进程状态
            if self.process.returncode is not None:
                raise Exception(f"服务器进程已退出，返回码: {self.process.returncode}")
            
            # 发送请求
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # 读取响应
            timeout_value = timeout or self.response_timeout
            response = await asyncio.wait_for(
                self._read_response(),
                timeout=timeout_value
            )
            
            return response
            
        except asyncio.TimeoutError:
            raise Exception(f"请求超时 ({timeout_value}s): {method}")
        except Exception as e:
            raise Exception(f"发送请求失败: {e}")
    
    async def _read_response(self) -> Dict[str, Any]:
        """
        读取 JSON-RPC 响应
        
        Returns:
            Dict[str, Any]: 解析后的响应
        """
        max_attempts = 10  # 减少最大尝试次数
        line_timeout = 5.0  # 每行读取超时时间
        
        for attempt in range(max_attempts):
            try:
                # 为每行读取添加超时
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=line_timeout
                )
                
                if not response_line:
                    raise Exception("连接已断开")
                
                line_text = response_line.decode().strip()
                
                if not line_text:
                    continue
                
                # 跳过非JSON行（如日志输出）
                # 检查是否以emoji或其他日志标识符开头
                if (line_text.startswith('✅') or 
                    line_text.startswith('📂') or 
                    line_text.startswith('🔍') or 
                    line_text.startswith('❌') or 
                    line_text.startswith('🔧') or 
                    line_text.startswith('🚀') or 
                    line_text.startswith('🎯') or 
                    line_text.startswith('🛠️') or 
                    line_text.startswith('📁') or 
                    line_text.startswith('📡') or 
                    line_text.startswith('👋') or
                    not line_text.startswith('{')):
                    continue
                
                try:
                    response = json.loads(line_text)
                    # 验证这是一个有效的JSON-RPC响应
                    if isinstance(response, dict) and 'jsonrpc' in response:
                        return response
                except json.JSONDecodeError:
                    continue
                    
            except asyncio.TimeoutError:
                # 如果读取超时，说明没有更多输出了
                break
        
        raise Exception("未收到有效的JSON响应")
    
    async def initialize(self, 
                        protocol_version: str = "2024-11-05",
                        capabilities: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化 MCP 连接
        
        Args:
            protocol_version: MCP 协议版本
            capabilities: 客户端能力
            
        Returns:
            bool: 初始化是否成功
        """
        if not self.is_connected:
            raise Exception("客户端未连接")
        
        if self.is_initialized:
            return True
        
        try:
            response = await self.send_request("initialize", {
                "protocolVersion": protocol_version,
                "capabilities": capabilities or {},
                "clientInfo": {
                    "name": self.client_name,
                    "version": self.client_version
                }
            })
            
            if "error" in response:
                raise Exception(f"初始化失败: {response['error']}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            raise Exception(f"MCP 初始化失败: {e}")
    
    async def disconnect(self):
        """断开连接并清理资源"""
        self.is_connected = False
        self.is_initialized = False
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except:
                pass
            finally:
                self.process = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    def __del__(self):
        """析构函数，确保资源清理"""
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
            except:
                pass


class MCPClientError(Exception):
    """MCP 客户端异常"""
    pass


class MCPTimeoutError(MCPClientError):
    """MCP 超时异常"""
    pass


class MCPConnectionError(MCPClientError):
    """MCP 连接异常"""
    pass