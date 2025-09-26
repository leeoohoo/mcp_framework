#!/usr/bin/env python3
"""
测试跨平台二进制文件检测功能
"""

import os
import stat
import tempfile

def _is_executable_binary(file_path: str) -> bool:
    """
    检查文件是否为可执行的二进制文件
    支持多种平台和架构的二进制格式检测
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为可执行二进制文件
    """
    try:
        # 检查文件是否存在且可执行
        if not os.path.exists(file_path):
            return False
            
        file_stat = os.stat(file_path)
        if not (file_stat.st_mode & stat.S_IEXEC):
            return False
        
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
            return True
        
        # 2. ELF 格式 (Linux/Unix)
        # 支持各种架构: x86, x86_64, ARM, ARM64, MIPS, PowerPC 等
        if header.startswith(b'\x7fELF'):
            return True
        
        # 3. PE 格式 (Windows)
        # .exe, .dll, .sys 等文件
        if header.startswith(b'MZ'):
            # 进一步验证是否为有效的PE文件
            if len(header) >= 16:
                # 检查PE签名位置
                try:
                    pe_offset = int.from_bytes(header[12:16], byteorder='little')
                    if pe_offset < len(header):
                        return True
                except:
                    pass
            # 即使无法验证PE签名，MZ开头的可执行文件通常也是有效的
            return True
        
        # 4. 其他可能的二进制格式
        # COFF (Common Object File Format)
        if (header.startswith(b'\x4c\x01') or  # i386
            header.startswith(b'\x64\x86') or  # x86_64
            header.startswith(b'\xc4\x01')):   # ARM
            return True
        
        # 5. 脚本文件但有shebang的情况
        # 虽然是文本文件，但如果有shebang且可执行，也应该直接执行
        if header.startswith(b'#!'):
            # 这是脚本文件，不是二进制文件，返回False让Python解释器处理
            return False
            
        return False
        
    except Exception:
        return False

def create_test_file(content: bytes, executable: bool = True) -> str:
    """创建测试文件"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    if executable:
        os.chmod(temp_path, 0o755)
    else:
        os.chmod(temp_path, 0o644)
    
    return temp_path

def test_binary_detection():
    """测试二进制文件检测功能"""
    print("=== 跨平台二进制文件检测测试 ===\n")
    
    test_cases = [
        # (描述, 文件内容, 是否可执行, 期望结果)
        ("Mach-O ARM64 (Apple Silicon)", b'\xcf\xfa\xed\xfe' + b'\x00' * 12, True, True),
        ("Mach-O x86_64 (Intel Mac)", b'\xcf\xfa\xed\xfe' + b'\x00' * 12, True, True),
        ("Mach-O 32-bit big-endian", b'\xfe\xed\xfa\xce' + b'\x00' * 12, True, True),
        ("Mach-O 32-bit little-endian", b'\xce\xfa\xed\xfe' + b'\x00' * 12, True, True),
        ("ELF Linux/Unix", b'\x7fELF' + b'\x00' * 12, True, True),
        ("Windows PE (.exe)", b'MZ' + b'\x00' * 14, True, True),
        ("COFF i386", b'\x4c\x01' + b'\x00' * 14, True, True),
        ("COFF x86_64", b'\x64\x86' + b'\x00' * 14, True, True),
        ("COFF ARM", b'\xc4\x01' + b'\x00' * 14, True, True),
        ("Shell脚本 (shebang)", b'#!/bin/bash\necho "hello"', True, False),
        ("Python脚本 (shebang)", b'#!/usr/bin/env python3\nprint("hello")', True, False),
        ("普通文本文件", b'This is a text file', True, False),
        ("不可执行的二进制文件", b'\xcf\xfa\xed\xfe' + b'\x00' * 12, False, False),
    ]
    
    # 测试现有的ARM64可执行文件
    existing_binary = "/Users/lilei/project/learn/mcp_servers/expert_stream_server/expert-stream-server-macos-arm64"
    if os.path.exists(existing_binary):
        result = _is_executable_binary(existing_binary)
        print(f"✓ 现有ARM64可执行文件: {result} (期望: True)")
    
    print()
    
    # 测试各种格式
    for description, content, executable, expected in test_cases:
        temp_file = create_test_file(content, executable)
        try:
            result = _is_executable_binary(temp_file)
            status = "✓" if result == expected else "✗"
            print(f"{status} {description}: {result} (期望: {expected})")
        finally:
            os.unlink(temp_file)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_binary_detection()