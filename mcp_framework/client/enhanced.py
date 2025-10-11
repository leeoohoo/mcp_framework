"""
增强版的MCPStdioClient，专门处理二进制版本的输出问题
"""

import asyncio
import json
from typing import Dict, Any
from .base import MCPStdioClient

class EnhancedMCPStdioClient(MCPStdioClient):
    """
    增强版的MCPStdioClient，专门处理二进制版本的输出问题
    
    主要改进：
    1. 增强的过滤逻辑：能够识别并跳过更多类型的非JSON调试输出
    2. 增加重试机制：提供connect_with_retry和initialize_with_retry方法
    3. 更长的超时时间：适应二进制版本的启动时间
    4. 调试模式：可选的详细调试输出，帮助诊断问题
    """
    
    def __init__(self, *args, **kwargs):
        # 提取debug_mode参数，避免传递给父类
        self.debug_mode = kwargs.pop('debug_mode', False)
        super().__init__(*args, **kwargs)
    
    async def _read_response(self) -> Dict[str, Any]:
        """
        增强版的响应读取方法，更好地处理二进制版本的输出
        """
        max_attempts = 20  # 增加最大尝试次数
        line_timeout = 10.0  # 增加每行读取超时时间
        
        if self.debug_mode:
            print("🔍 [DEBUG] 开始读取响应...")
        
        for attempt in range(max_attempts):
            try:
                # 为每行读取添加超时
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=line_timeout
                )
                
                if not response_line:
                    if self.debug_mode:
                        print("🔍 [DEBUG] 连接已断开")
                    raise Exception("连接已断开")
                
                line_text = response_line.decode().strip()
                
                if not line_text:
                    continue
                
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 第{attempt+1}行: {repr(line_text)}")
                
                # 增强的过滤逻辑 - 跳过所有非JSON行
                if self._should_skip_line(line_text):
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] 跳过非JSON行")
                    continue
                
                # 尝试解析JSON
                try:
                    response = json.loads(line_text)
                    # 验证这是一个有效的JSON-RPC响应
                    if isinstance(response, dict) and 'jsonrpc' in response:
                        if self.debug_mode:
                            print(f"🔍 [DEBUG] 找到有效JSON-RPC响应: {response}")
                        return response
                    else:
                        if self.debug_mode:
                            print(f"🔍 [DEBUG] JSON格式正确但不是JSON-RPC响应")
                except json.JSONDecodeError:
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] JSON解析失败")
                    continue
                    
            except asyncio.TimeoutError:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 第{attempt+1}次读取超时")
                # 如果读取超时，继续尝试而不是立即退出
                continue
            except Exception as e:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 读取异常: {e}")
                break
        
        raise Exception("未收到有效的JSON响应")
    
    def _should_skip_line(self, line_text: str) -> bool:
        """
        增强的行过滤逻辑
        """
        # 空行
        if not line_text.strip():
            return True
        
        # 以emoji开头的调试信息
        emoji_prefixes = [
            '✅', '📂', '🔍', '❌', '🔧', '🚀', '🎯', '🛠️', 
            '📁', '📡', '👋', '🤖', '📤', '📥', '⚠️', '💡',
            '🔗', '🌟', '🎉', '🔥', '💪', '🚨', '📋', '📊'
        ]
        
        for emoji in emoji_prefixes:
            if line_text.startswith(emoji):
                return True
        
        # 特定的文本模式
        text_patterns = [
            'Required parameter missing',
            'Failed to save default configuration',
            'Failed to get tools from HTTP MCP server',
            'Cannot connect to host',
            'Connect call failed',
            '发送EOF',
            '按 Ctrl+C',
            'Multiple exceptions',
            '服务器版本:',
            '已注册工具:',
            '已注册资源:',
            '活跃传输:',
            '协议:',
            '格式:',
            '停止服务器'
        ]
        
        for pattern in text_patterns:
            if pattern in line_text:
                return True
        
        # 列表项和缩进项
        list_prefixes = ['•', '  •', '    -', '  -', '- ', '    • ']
        for prefix in list_prefixes:
            if line_text.startswith(prefix):
                return True
        
        # 不以{开头的行（JSON必须以{开头）
        if not line_text.startswith('{'):
            return True
        
        return False
    
    async def connect_with_retry(self, max_retries: int = 3) -> bool:
        """
        带重试的连接方法
        """
        for attempt in range(max_retries):
            try:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 连接尝试 {attempt + 1}/{max_retries}")
                
                success = await self.connect()
                if success:
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] 连接成功")
                    return True
                else:
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] 连接失败，尝试重试...")
                    await asyncio.sleep(1)
            except Exception as e:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 连接异常: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise
        
        return False
    
    async def initialize_with_retry(self, max_retries: int = 3, **kwargs) -> bool:
        """
        带重试的初始化方法
        """
        for attempt in range(max_retries):
            try:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 初始化尝试 {attempt + 1}/{max_retries}")
                
                success = await self.initialize(**kwargs)
                if success:
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] 初始化成功")
                    return True
                else:
                    if self.debug_mode:
                        print(f"🔍 [DEBUG] 初始化失败，尝试重试...")
                    await asyncio.sleep(1)
            except Exception as e:
                if self.debug_mode:
                    print(f"🔍 [DEBUG] 初始化异常: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise
        
        return False