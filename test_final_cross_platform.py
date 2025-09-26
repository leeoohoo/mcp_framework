#!/usr/bin/env python3
"""
最终的跨平台二进制文件检测测试
验证MCP客户端对真实跨平台文件的处理能力
"""

import os
import sys
import glob

# 添加mcp_framework到路径
sys.path.insert(0, '/Users/lilei/project/learn/mcp_framework')

from mcp_framework.client.base import MCPStdioClient

def test_final_cross_platform():
    """最终的跨平台测试"""
    print("=== 最终跨平台二进制文件检测测试 ===\n")
    
    # 创建客户端实例
    client = MCPStdioClient("test_server")
    
    # 定义测试用例
    test_cases = [
        {
            'file': 'test_files/expert-stream-server-macos-arm64',
            'platform': 'macOS ARM64 (Apple Silicon)',
            'expected': True,
            'format': 'Mach-O'
        },
        {
            'file': 'test_files/expert-stream-server-macos-x86_64', 
            'platform': 'macOS x86_64 (Intel Mac)',
            'expected': True,
            'format': 'Mach-O'
        },
        {
            'file': 'test_files/expert-stream-server-windows-x86_64.exe',
            'platform': 'Windows x86_64',
            'expected': True,
            'format': 'PE'
        },
        {
            'file': 'test_files/file-reader-server-macos-arm64',
            'platform': 'macOS ARM64 (Apple Silicon)',
            'expected': True,
            'format': 'Mach-O'
        },
        {
            'file': 'test_files/file-reader-server-macos-x86_64',
            'platform': 'macOS x86_64 (Intel Mac)', 
            'expected': True,
            'format': 'Mach-O'
        }
    ]
    
    print("🔍 测试跨平台二进制文件检测：\n")
    
    success_count = 0
    total_count = 0
    
    for test_case in test_cases:
        file_path = test_case['file']
        platform = test_case['platform']
        expected = test_case['expected']
        format_type = test_case['format']
        
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue
            
        total_count += 1
        
        # 测试二进制检测
        is_binary = client._is_executable_binary(file_path)
        
        # 检查结果
        if is_binary == expected:
            status = "✅"
            success_count += 1
        else:
            status = "❌"
        
        print(f"{status} {platform} ({format_type})")
        print(f"    文件: {file_path}")
        print(f"    检测结果: {'二进制文件' if is_binary else '非二进制文件'}")
        print(f"    期望结果: {'二进制文件' if expected else '非二进制文件'}")
        
        # 显示将要执行的命令
        if is_binary:
            command = f"{file_path} stdio"
        else:
            command = f"{sys.executable} {file_path} stdio"
        print(f"    执行命令: {command}")
        print()
    
    print("📊 测试结果统计：")
    print(f"    总测试数: {total_count}")
    print(f"    成功数: {success_count}")
    print(f"    失败数: {total_count - success_count}")
    print(f"    成功率: {success_count/total_count*100:.1f}%" if total_count > 0 else "    成功率: N/A")
    
    print("\n🎯 支持的平台和格式：")
    print("    ✅ macOS ARM64 (Apple Silicon) - Mach-O 格式")
    print("    ✅ macOS x86_64 (Intel Mac) - Mach-O 格式") 
    print("    ✅ Windows x86_64 - PE 格式")
    print("    ✅ Linux x86_64 - ELF 格式 (理论支持)")
    print("    ✅ 其他架构 - COFF 格式 (理论支持)")
    
    print("\n🔧 客户端行为：")
    print("    • 二进制文件: 直接执行 (file_path stdio)")
    print("    • Python脚本: 通过解释器执行 (python file_path stdio)")
    print("    • 自动检测文件格式和架构")
    print("    • 支持跨平台部署")
    
    if success_count == total_count and total_count > 0:
        print("\n🎉 所有测试通过！跨平台二进制文件检测功能正常工作。")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败，请检查相关问题。")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_final_cross_platform()