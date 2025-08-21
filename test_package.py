#!/usr/bin/env python3
"""
测试 MCP Framework 包的安装和功能
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_package_installation():
    """测试包的安装"""
    print("🧪 Testing package installation...")
    
    # 创建临时虚拟环境
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = Path(temp_dir) / "test_venv"
        
        # 创建虚拟环境
        print("   Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        
        # 确定虚拟环境的 Python 和 pip 路径
        if os.name == "nt":  # Windows
            venv_python = venv_dir / "Scripts" / "python.exe"
            venv_pip = venv_dir / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            venv_python = venv_dir / "bin" / "python"
            venv_pip = venv_dir / "bin" / "pip"
        
        try:
            # 升级 pip
            print("   Upgrading pip...")
            subprocess.run([str(venv_pip), "install", "--upgrade", "pip"], check=True)
            
            # 安装当前包
            print("   Installing mcp-framework...")
            current_dir = Path(__file__).parent
            subprocess.run([str(venv_pip), "install", "-e", str(current_dir)], check=True)
            
            # 测试导入
            print("   Testing imports...")
            test_script = """
import mcp_framework
from mcp_framework import BaseMCPServer, MCPTool, MCPResource
from mcp_framework import ParamSpec, AnnotatedDecorators
from mcp_framework import ServerConfig, run_server
print("✅ All imports successful")
print(f"MCP Framework version: {getattr(mcp_framework, '__version__', 'unknown')}")
"""
            
            result = subprocess.run([str(venv_python), "-c", test_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Import test passed")
                print(f"   Output: {result.stdout.strip()}")
            else:
                print("   ❌ Import test failed")
                print(f"   Error: {result.stderr}")
                return False
            
            # 测试命令行工具
            print("   Testing CLI tools...")
            
            # 测试 mcp-framework 命令
            result = subprocess.run([str(venv_python), "-m", "mcp_framework.cli", "--help"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ mcp-framework CLI test passed")
            else:
                print("   ❌ mcp-framework CLI test failed")
                print(f"   Error: {result.stderr}")
            
            # 测试 mcp-build 命令
            result = subprocess.run([str(venv_python), "-m", "mcp_framework.build", "--help"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ mcp-build CLI test passed")
            else:
                print("   ❌ mcp-build CLI test failed")
                print(f"   Error: {result.stderr}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Installation failed: {e}")
            return False


def test_build_package():
    """测试构建包"""
    print("\n📦 Testing package build...")
    
    try:
        # 运行 setup.py 检查
        result = subprocess.run([sys.executable, "setup.py", "check"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ setup.py check passed")
        else:
            print("   ❌ setup.py check failed")
            print(f"   Error: {result.stderr}")
            return False
        
        # 构建源码分发包
        print("   Building source distribution...")
        result = subprocess.run([sys.executable, "setup.py", "sdist"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Source distribution built successfully")
        else:
            print("   ❌ Source distribution build failed")
            print(f"   Error: {result.stderr}")
            return False
        
        # 构建 wheel 包
        print("   Building wheel...")
        result = subprocess.run([sys.executable, "setup.py", "bdist_wheel"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Wheel built successfully")
        else:
            print("   ❌ Wheel build failed")
            print(f"   Error: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Build test failed: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 Starting MCP Framework package tests...\n")
    
    # 切换到包目录
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    
    success = True
    
    # 测试包安装
    if not test_package_installation():
        success = False
    
    # 测试包构建
    if not test_build_package():
        success = False
    
    if success:
        print("\n🎉 All tests passed! The package is ready for distribution.")
        print("\n📋 Next steps:")
        print("   1. Upload to PyPI: python -m twine upload dist/*")
        print("   2. Install from PyPI: pip install mcp-framework")
        print("   3. Create documentation: sphinx-build docs docs/_build")
    else:
        print("\n❌ Some tests failed. Please fix the issues before distribution.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)