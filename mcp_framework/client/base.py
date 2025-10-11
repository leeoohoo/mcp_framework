"""
MCP Stdio 客户端基础类
提供与 MCP 服务器进行 stdio 通信的基础功能
"""

import asyncio
import json
import sys
import os
import stat
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
                 response_timeout: float = 30.0,
                 config_dir: Optional[str] = None):
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
            config_dir: 自定义配置目录路径
        """
        self.server_script = server_script
        self.alias = alias
        self.server_args = server_args or []
        self.client_name = client_name
        self.client_version = client_version
        self.startup_timeout = startup_timeout
        self.response_timeout = response_timeout
        self.config_dir = config_dir
        
        self.process = None
        self.request_id = 0
        self.is_connected = False
        self.is_initialized = False
    
    def get_next_id(self) -> int:
        """获取下一个请求ID"""
        self.request_id += 1
        return self.request_id
    
    def _is_executable_binary(self, file_path: str) -> bool:
        """
        检查文件是否为可执行的二进制文件
        支持多种平台和架构的二进制格式检测
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为可执行二进制文件
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False
                
            file_stat = os.stat(file_path)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
            
            # 读取文件开头更多字节来判断文件类型
            with open(file_path, 'rb') as f:
                header = f.read(16)  # 读取更多字节以支持更复杂的检测
                
            if len(header) < 4:
                return False
                
            # 检查各种二进制文件格式
            
            # 1. Mach-O 格式 (macOS)
            # ARM64 (Apple Silicon): cf fa ed fe
            # x86_64 (Intel Mac): cf fa ed fe (64-bit) 或 ce fa ed fe (64-bit big-endian)
            # i386 (32-bit Intel): fe ed fa ce 或 ce fa ed fe
            if (header.startswith(b'\xcf\xfa\xed\xfe') or  # Mach-O 64-bit little-endian (ARM64/x86_64)
                header.startswith(b'\xfe\xed\xfa\xcf') or  # Mach-O 64-bit big-endian
                header.startswith(b'\xfe\xed\xfa\xce') or  # Mach-O 32-bit big-endian
                header.startswith(b'\xce\xfa\xed\xfe')):   # Mach-O 32-bit little-endian
                return is_executable  # Mach-O文件需要可执行权限
            
            # 2. ELF 格式 (Linux/Unix)
            # 支持各种架构: x86, x86_64, ARM, ARM64, MIPS, PowerPC 等
            if header.startswith(b'\x7fELF'):
                return is_executable  # ELF文件需要可执行权限
            
            # 3. PE 格式 (Windows)
            # .exe, .dll, .sys 等文件
            if header.startswith(b'MZ'):
                # Windows PE文件，即使没有可执行权限也应该被识别
                # 进一步验证是否为有效的PE文件
                if len(header) >= 16:
                    # 检查PE签名位置
                    try:
                        pe_offset = int.from_bytes(header[12:16], byteorder='little')
                        if pe_offset < len(header):
                            return True
                    except:
                        pass
                # 即使无法验证PE签名，MZ开头的文件通常也是有效的PE文件
                return True
            
            # 4. 其他可能的二进制格式
            # COFF (Common Object File Format)
            if (header.startswith(b'\x4c\x01') or  # i386
                header.startswith(b'\x64\x86') or  # x86_64
                header.startswith(b'\xc4\x01')):   # ARM
                return is_executable  # COFF文件需要可执行权限
            
            # 5. 脚本文件但有shebang的情况
            # 虽然是文本文件，但如果有shebang且可执行，也应该直接执行
            if header.startswith(b'#!'):
                # 这是脚本文件，不是二进制文件，返回False让Python解释器处理
                return False
                
            return False
            
        except Exception:
            return False

    async def connect(self) -> bool:
        """
        连接到 MCP 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 检查服务器脚本是否为二进制可执行文件
            if self._is_executable_binary(self.server_script):
                # 直接执行二进制文件
                cmd = [self.server_script, "stdio"]
            else:
                # 使用Python解释器执行脚本
                cmd = [sys.executable, self.server_script, "stdio"]
            
            # 添加别名参数
            if self.alias:
                cmd.extend(["--alias", self.alias])
            
            # 添加配置目录参数
            if self.config_dir:
                cmd.extend(["--config-dir", self.config_dir])
            
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
                    line_text.startswith('Required parameter') or
                    line_text.startswith('Failed to') or
                    line_text.startswith('发送EOF') or
                    line_text.startswith('按 Ctrl+C') or
                    line_text.startswith('Cannot connect to host') or
                    line_text.startswith('•') or  # 列表项
                    line_text.startswith('  •') or  # 缩进的列表项
                    line_text.startswith('    -') or  # 缩进的子项
                    line_text.startswith('  -') or  # 缩进的子项
                    line_text.startswith('- ') or  # 列表项
                    line_text.strip() == '' or  # 空行
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