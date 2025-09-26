#!/usr/bin/env python3
"""
测试修改后的MCP客户端对跨平台二进制文件的处理
"""

import os
import stat
import tempfile
import sys

# 添加mcp_framework到路径
sys.path.insert(0, '/Users/lilei/project/learn/mcp_framework')

from mcp_framework.client.base import MCPStdioClient

def create_mock_binary(binary_type: str) -> str:
    """创建模拟的二进制文件"""
    binary_headers = {
        'macos_arm64': b'\xcf\xfa\xed\xfe' + b'\x00' * 12,
        'macos_x86_64': b'\xcf\xfa\xed\xfe' + b'\x00' * 12,
        'macos_i386': b'\xfe\xed\xfa\xce' + b'\x00' * 12,
        'linux_x86_64': b'\x7fELF' + b'\x00' * 12,
        'windows_exe': b'MZ' + b'\x00' * 14,
        'python_script': b'#!/usr/bin/env python3\nprint("hello")',
    }
    
    content = binary_headers.get(binary_type, b'unknown')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.exe' if binary_type == 'windows_exe' else '') as f:
        f.write(content)
        temp_path = f.name
    
    # 设置为可执行
    os.chmod(temp_path, 0o755)
    
    return temp_path

def test_client_binary_detection():
    """测试客户端的二进制文件检测"""
    print("=== MCP客户端跨平台二进制文件检测测试 ===\n")
    
    # 创建一个测试客户端实例
    client = MCPStdioClient("test_server")
    
    test_cases = [
        ('macOS ARM64 (Apple Silicon)', 'macos_arm64', True),
        ('macOS x86_64 (Intel Mac)', 'macos_x86_64', True),
        ('macOS i386 (32-bit Intel)', 'macos_i386', True),
        ('Linux x86_64 (ELF)', 'linux_x86_64', True),
        ('Windows .exe (PE)', 'windows_exe', True),
        ('Python脚本 (shebang)', 'python_script', False),
    ]
    
    # 测试现有的ARM64可执行文件
    existing_binary = "/Users/lilei/project/learn/mcp_servers/expert_stream_server/expert-stream-server-macos-arm64"
    if os.path.exists(existing_binary):
        result = client._is_executable_binary(existing_binary)
        print(f"✓ 现有ARM64可执行文件: {result} (期望: True)")
    
    print()
    
    # 测试各种平台的二进制文件
    for description, binary_type, expected in test_cases:
        temp_file = create_mock_binary(binary_type)
        try:
            result = client._is_executable_binary(temp_file)
            status = "✓" if result == expected else "✗"
            print(f"{status} {description}: {result} (期望: {expected})")
            
            # 如果是二进制文件，测试命令构建逻辑
            if result:
                print(f"    → 将直接执行: {temp_file}")
            else:
                print(f"    → 将用Python执行: {sys.executable} {temp_file}")
                
        finally:
            os.unlink(temp_file)
    
    print("\n=== 命令构建逻辑测试 ===")
    
    # 测试命令构建逻辑
    def simulate_command_building(server_script: str) -> list:
        """模拟客户端的命令构建逻辑"""
        if client._is_executable_binary(server_script):
            return [server_script, "stdio"]
        else:
            return [sys.executable, server_script, "stdio"]
    
    # 测试不同类型文件的命令构建
    test_files = [
        ('二进制文件', create_mock_binary('macos_arm64')),
        ('Python脚本', create_mock_binary('python_script')),
    ]
    
    for description, test_file in test_files:
        try:
            command = simulate_command_building(test_file)
            print(f"✓ {description}: {' '.join(command)}")
        finally:
            os.unlink(test_file)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_client_binary_detection()