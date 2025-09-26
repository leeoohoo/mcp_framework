#!/usr/bin/env python3
"""
测试二进制文件检测功能
"""
import os
import stat

def is_executable_binary(file_path: str) -> bool:
    """
    检查文件是否为可执行的二进制文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为可执行二进制文件
    """
    try:
        # 检查文件是否存在且可执行
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
            
        file_stat = os.stat(file_path)
        if not (file_stat.st_mode & stat.S_IEXEC):
            print(f"文件不可执行: {file_path}")
            return False
        
        # 读取文件开头几个字节来判断文件类型
        with open(file_path, 'rb') as f:
            header = f.read(4)
            
        print(f"文件头字节: {header.hex()}")
        
        # 检查是否为常见的二进制文件格式
        # Mach-O (macOS): cf fa ed fe 或 fe ed fa ce
        # ELF (Linux): 7f 45 4c 46
        # PE (Windows): 4d 5a
        if (header.startswith(b'\xcf\xfa\xed\xfe') or  # Mach-O 64-bit
            header.startswith(b'\xfe\xed\xfa\xce') or  # Mach-O 32-bit  
            header.startswith(b'\x7fELF') or           # ELF
            header.startswith(b'MZ')):                 # PE
            print("检测到二进制可执行文件")
            return True
            
        print("不是二进制可执行文件")
        return False
        
    except Exception as e:
        print(f"检测过程中出错: {e}")
        return False

if __name__ == "__main__":
    file_path = "/Users/lilei/project/learn/mcp_servers/expert_stream_server/expert-stream-server-macos-arm64"
    print(f"测试文件: {file_path}")
    result = is_executable_binary(file_path)
    print(f"检测结果: {result}")