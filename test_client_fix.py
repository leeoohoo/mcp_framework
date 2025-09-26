#!/usr/bin/env python3
"""
测试修改后的客户端是否能正确启动二进制服务器
"""
import asyncio
import sys
import os
import stat
from pathlib import Path

# 简化版的客户端类，只包含必要的功能
class TestMCPStdioClient:
    def __init__(self, server_script: str):
        self.server_script = server_script
        self.process = None
        self.is_connected = False

    def _is_executable_binary(self, file_path: str) -> bool:
        """检查文件是否为可执行的二进制文件"""
        try:
            if not os.path.exists(file_path):
                return False
                
            file_stat = os.stat(file_path)
            if not (file_stat.st_mode & stat.S_IEXEC):
                return False
            
            with open(file_path, 'rb') as f:
                header = f.read(4)
                
            if (header.startswith(b'\xcf\xfa\xed\xfe') or  # Mach-O 64-bit
                header.startswith(b'\xfe\xed\xfa\xce') or  # Mach-O 32-bit  
                header.startswith(b'\x7fELF') or           # ELF
                header.startswith(b'MZ')):                 # PE
                return True
                
            return False
            
        except Exception:
            return False

    async def test_connect(self) -> bool:
        """测试连接到 MCP 服务器"""
        try:
            # 检查服务器脚本是否为二进制可执行文件
            if self._is_executable_binary(self.server_script):
                print("✅ 检测到二进制可执行文件，直接执行")
                cmd = [self.server_script, "stdio"]
            else:
                print("✅ 检测到Python脚本，使用Python解释器执行")
                cmd = [sys.executable, self.server_script, "stdio"]
            
            print(f"🚀 启动命令: {' '.join(cmd)}")
            
            # 启动子进程
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 给服务器一点时间启动
            await asyncio.sleep(1.0)
            
            # 检查进程是否还在运行
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                print(f"❌ 服务器启动失败，退出码: {self.process.returncode}")
                print(f"错误输出: {stderr_output.decode()}")
                return False
            
            print("✅ 服务器启动成功，进程正在运行")
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        """断开连接"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                print(f"⚠️ 断开连接时出现警告: {e}")
            finally:
                self.process = None
                self.is_connected = False

async def main():
    """主测试函数"""
    server_path = "/Users/lilei/project/learn/mcp_servers/expert_stream_server/expert-stream-server-macos-arm64"
    
    print("🧪 测试修改后的MCP客户端")
    print(f"📁 服务器路径: {server_path}")
    print("=" * 60)
    
    client = TestMCPStdioClient(server_path)
    
    try:
        success = await client.test_connect()
        if success:
            print("🎉 测试成功！客户端能够正确启动二进制服务器")
            # 等待一会儿再断开
            await asyncio.sleep(2.0)
        else:
            print("💥 测试失败！")
    finally:
        await client.disconnect()
        print("🔚 测试完成")

if __name__ == "__main__":
    asyncio.run(main())