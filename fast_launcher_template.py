#!/usr/bin/env python3
"""
快速启动器模板 - 最小化启动时间
"""

import sys
import os
import asyncio
from typing import Any

# 设置优化环境变量
os.environ['PYTHONOPTIMIZE'] = '2'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

class FastLauncher:
    """快速启动器 - 跳过不必要的检查"""
    
    def __init__(self, server_instance: Any):
        self.server = server_instance
        self._initialized = False
    
    async def quick_start(self):
        """快速启动 - 最小化初始化"""
        if not self._initialized:
            # 最小化初始化
            if hasattr(self.server, 'initialize'):
                await self.server.initialize()
            self._initialized = True
        
        # 直接启动stdio模式（最快）
        await self._run_stdio()
    
    async def _run_stdio(self):
        """运行stdio模式"""
        try:
            import json
            
            while True:
                try:
                    # 读取输入
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    
                    if not line:
                        break
                    
                    # 处理请求
                    request = json.loads(line.strip())
                    response = await self._handle_request(request)
                    
                    # 输出响应
                    print(json.dumps(response), flush=True)
                    
                except Exception as e:
                    error_response = {
                        "error": {"code": -1, "message": str(e)}
                    }
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            pass
    
    async def _handle_request(self, request):
        """处理请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "tools/list":
                tools = getattr(self.server, 'get_tools', lambda: [])()
                result = {"tools": tools}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.server.handle_tool_call(tool_name, arguments)
            else:
                result = {"error": "Unknown method"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0", 
                "id": request_id,
                "error": {"code": -1, "message": str(e)}
            }

def fast_main(server_instance: Any):
    """快速主函数"""
    launcher = FastLauncher(server_instance)
    asyncio.run(launcher.quick_start())
