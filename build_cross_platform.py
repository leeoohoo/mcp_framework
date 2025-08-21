#!/usr/bin/env python3
"""
MCP Framework 跨平台构建脚本
使用 Docker 支持在 macOS 上构建 Windows 和 Linux 版本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import platform

class MCPFrameworkCrossPlatformBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.current_platform = platform.system().lower()
        
    def check_docker(self):
        """检查 Docker 是否可用"""
        try:
            subprocess.run(["docker", "--version"], 
                         check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def build_native(self, args):
        """在当前平台构建"""
        print(f"🔨 Building MCP Framework for native platform ({self.current_platform})...")
        
        # 对于 MCP Framework，我们构建包而不是服务器脚本
        if args.build_package:
            return self.build_framework_package()
        else:
            cmd = ["python", "mcp_framework/build.py"]
            if args.server:
                cmd.extend(["--server", args.server])
            if args.no_test:
                cmd.append("--no-test")
            if args.no_clean:
                cmd.append("--no-clean")
            if args.include_source:
                cmd.append("--include-source")
                
            try:
                subprocess.run(cmd, check=True, cwd=self.project_root)
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Native build failed: {e}")
                return False
    
    def build_framework_package(self):
        """构建 MCP Framework 包"""
        print("📦 Building MCP Framework package...")
        
        try:
            # 构建源码分发包
            subprocess.run(["python", "setup.py", "sdist"], 
                         check=True, cwd=self.project_root)
            print("   ✅ Source distribution built")
            
            # 构建 wheel 包
            subprocess.run(["python", "setup.py", "bdist_wheel"], 
                         check=True, cwd=self.project_root)
            print("   ✅ Wheel distribution built")
            
            # 运行测试
            subprocess.run(["python", "test_package.py"], 
                         check=True, cwd=self.project_root)
            print("   ✅ Package tests passed")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Framework package build failed: {e}")
            return False
    
    def build_docker(self, target_platform, args):
        """使用 Docker 构建指定平台"""
        print(f"🐳 Building MCP Framework for {target_platform} using Docker...")
        
        # 选择 Dockerfile
        dockerfile = f"Dockerfile.{target_platform}"
        if not (self.project_root / dockerfile).exists():
            print(f"❌ Dockerfile not found: {dockerfile}")
            return False
        
        # 构建 Docker 镜像
        image_name = f"mcp-framework-builder-{target_platform}"
        build_cmd = [
            "docker", "build", 
            "-f", dockerfile,
            "-t", image_name,
            "."
        ]
        
        try:
            print("   Building Docker image...")
            subprocess.run(build_cmd, check=True, cwd=self.project_root)
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker image build failed: {e}")
            return False
        
        # 运行构建容器
        run_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.project_root}/dist:/app/dist",
        ]
        
        # 添加构建参数
        build_args = []
        if args.server:
            build_args.extend(["--server", args.server])
        if args.no_test:
            build_args.append("--no-test")
        if args.no_clean:
            build_args.append("--no-clean")
        if args.include_source:
            build_args.append("--include-source")
            
        run_cmd.extend([image_name] + build_args)
        
        try:
            print("   Running build in container...")
            subprocess.run(run_cmd, check=True, cwd=self.project_root)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker build failed: {e}")
            return False
    
    def build_all_platforms(self, args):
        """构建所有平台"""
        platforms = ["native"]
        
        if self.check_docker():
            platforms.extend(["linux", "windows"])
        else:
            print("⚠️  Docker not available, only building for native platform")
        
        success_count = 0
        total_count = len(platforms)
        
        for platform_name in platforms:
            print(f"\n{'='*50}")
            print(f"Building MCP Framework for {platform_name}")
            print(f"{'='*50}")
            
            if platform_name == "native":
                success = self.build_native(args)
            else:
                success = self.build_docker(platform_name, args)
            
            if success:
                success_count += 1
                print(f"✅ {platform_name} build completed successfully")
            else:
                print(f"❌ {platform_name} build failed")
        
        print(f"\n{'='*50}")
        print(f"Build Summary: {success_count}/{total_count} platforms successful")
        print(f"{'='*50}")
        
        return success_count == total_count

def main():
    parser = argparse.ArgumentParser(description="MCP Framework Cross-platform Build Script")
    parser.add_argument("--platform", "-p", 
                       choices=["native", "linux", "windows", "all"],
                       default="all",
                       help="Target platform to build for")
    parser.add_argument("--server", "-s", 
                       help="Specific server script to build")
    parser.add_argument("--build-package", action="store_true",
                       default=True,
                       help="Build MCP Framework package (default)")
    parser.add_argument("--no-test", action="store_true", 
                       help="Skip running tests")
    parser.add_argument("--no-clean", action="store_true", 
                       help="Skip cleaning build directories")
    parser.add_argument("--include-source", action="store_true", 
                       help="Include source code in package")
    parser.add_argument("--check-docker", action="store_true",
                       help="Check if Docker is available")
    
    args = parser.parse_args()
    
    builder = MCPFrameworkCrossPlatformBuilder()
    
    if args.check_docker:
        if builder.check_docker():
            print("✅ Docker is available")
        else:
            print("❌ Docker is not available")
        return
    
    if args.platform == "all":
        success = builder.build_all_platforms(args)
    elif args.platform == "native":
        success = builder.build_native(args)
    else:
        if not builder.check_docker():
            print("❌ Docker is required for cross-platform builds")
            sys.exit(1)
        success = builder.build_docker(args.platform, args)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()