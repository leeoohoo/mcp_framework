#!/usr/bin/env python3
"""
测试真实的跨平台二进制文件
请将Downloads目录中的各平台文件复制到当前目录的test_files文件夹中
"""

import os
import stat
import sys
import glob

# 添加mcp_framework到路径
sys.path.insert(0, '/Users/lilei/project/learn/mcp_framework')

from mcp_framework.client.base import MCPStdioClient

def analyze_file_header(file_path: str, max_bytes: int = 32) -> str:
    """分析文件头部信息"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(max_bytes)
        
        # 转换为十六进制字符串
        hex_str = ' '.join(f'{b:02x}' for b in header[:16])
        
        # 尝试识别文件类型
        if header.startswith(b'\xcf\xfa\xed\xfe'):
            return f"Mach-O 64-bit little-endian | {hex_str}"
        elif header.startswith(b'\xfe\xed\xfa\xcf'):
            return f"Mach-O 64-bit big-endian | {hex_str}"
        elif header.startswith(b'\xfe\xed\xfa\xce'):
            return f"Mach-O 32-bit big-endian | {hex_str}"
        elif header.startswith(b'\xce\xfa\xed\xfe'):
            return f"Mach-O 32-bit little-endian | {hex_str}"
        elif header.startswith(b'\x7fELF'):
            return f"ELF (Linux/Unix) | {hex_str}"
        elif header.startswith(b'MZ'):
            return f"PE (Windows .exe/.dll) | {hex_str}"
        elif header.startswith(b'#!'):
            return f"Script with shebang | {header[:20].decode('utf-8', errors='ignore')}"
        else:
            return f"Unknown format | {hex_str}"
            
    except Exception as e:
        return f"Error reading file: {e}"

def test_real_platform_files():
    """测试真实的平台文件"""
    print("=== 真实跨平台文件测试 ===\n")
    
    # 创建测试目录
    test_dir = "test_files"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"已创建测试目录: {test_dir}")
        print("请将Downloads目录中的各平台文件复制到此目录中\n")
    
    # 创建客户端实例
    client = MCPStdioClient("test_server")
    
    # 查找测试文件
    test_patterns = [
        "test_files/*",
        "test_files/**/*",
        "**/expert-stream-server*",  # 查找已知的服务器文件
    ]
    
    test_files = []
    for pattern in test_patterns:
        test_files.extend(glob.glob(pattern, recursive=True))
    
    # 去重并过滤文件
    test_files = list(set([f for f in test_files if os.path.isfile(f)]))
    
    if not test_files:
        print("未找到测试文件。请执行以下步骤：")
        print("1. 将Downloads目录中的各平台文件复制到 test_files/ 目录")
        print("2. 重新运行此脚本")
        print("\n建议的文件类型：")
        print("- macOS ARM64 可执行文件")
        print("- macOS x86_64 可执行文件") 
        print("- Linux x86_64 可执行文件")
        print("- Windows .exe 文件")
        print("- 其他平台的二进制文件")
        return
    
    print(f"找到 {len(test_files)} 个测试文件：\n")
    
    # 测试每个文件
    for file_path in sorted(test_files):
        print(f"📁 文件: {file_path}")
        
        # 检查文件权限
        try:
            file_stat = os.stat(file_path)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
            file_size = file_stat.st_size
            print(f"   大小: {file_size} bytes")
            print(f"   可执行: {is_executable}")
        except Exception as e:
            print(f"   权限检查失败: {e}")
            continue
        
        # 分析文件头
        header_info = analyze_file_header(file_path)
        print(f"   文件头: {header_info}")
        
        # 测试二进制检测
        is_binary = client._is_executable_binary(file_path)
        print(f"   检测结果: {'✓ 二进制文件' if is_binary else '✗ 非二进制文件'}")
        
        # 模拟命令构建
        if is_binary:
            command = [file_path, "stdio"]
            print(f"   执行命令: {' '.join(command)}")
        else:
            command = [sys.executable, file_path, "stdio"]
            print(f"   执行命令: {' '.join(command)}")
        
        print()
    
    print("=== 测试完成 ===")
    print("\n如需添加更多测试文件，请将它们复制到 test_files/ 目录中")

def copy_instructions():
    """显示复制指令"""
    print("=== 文件复制指令 ===")
    print("请在终端中执行以下命令来复制测试文件：")
    print()
    print("# 创建测试目录")
    print("mkdir -p test_files")
    print()
    print("# 复制Downloads中的文件到测试目录")
    print("# 请根据实际文件名调整以下命令：")
    print("cp /Users/lilei/Downloads/*server* test_files/")
    print("cp /Users/lilei/Downloads/*.exe test_files/")
    print("cp /Users/lilei/Downloads/*linux* test_files/")
    print("cp /Users/lilei/Downloads/*macos* test_files/")
    print("cp /Users/lilei/Downloads/*arm64* test_files/")
    print("cp /Users/lilei/Downloads/*x86_64* test_files/")
    print()
    print("# 或者手动复制特定文件：")
    print("# cp /Users/lilei/Downloads/your-binary-file test_files/")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        copy_instructions()
    else:
        test_real_platform_files()