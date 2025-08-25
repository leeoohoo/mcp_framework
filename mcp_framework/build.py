#!/usr/bin/env python3
"""
MCP Framework 构建系统
集成 PyInstaller 构建功能
"""

import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path
import zipfile
import tarfile
import venv
import tempfile
from datetime import datetime
import ast
import importlib.util
from typing import List, Dict, Any, Set


class MCPServerBuilder:
    """MCP 服务器构建器"""

    def __init__(self, server_script=None, output_dir=None):
        self.project_root = Path.cwd()
        # 支持自定义输出目录
        if output_dir:
            self.dist_dir = Path(output_dir).resolve()
        else:
            self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.platform_name = self.get_platform_name()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.server_script = server_script

    def discover_servers(self) -> List[Path]:
        """自动发现所有服务器脚本"""
        server_files = []
        print("🔍 Discovering server scripts...")

        # 查找所有 *_server.py 文件
        for file_path in self.project_root.glob("*_server.py"):
            if file_path.name not in ["test_server.py", "mcp_server.py"]:
                server_files.append(file_path)
                print(f"   ✅ Found: {file_path.name}")
            else:
                print(f"   ❌ Excluded: {file_path.name}")

        print(f"   Total discovered: {len(server_files)} servers")
        return server_files

    def get_server_config(self, script_path: Path) -> Dict[str, Any]:
        """根据脚本路径生成服务器配置"""
        script_name = script_path.stem
        exe_name = script_name.replace("_", "-")
        spec_file = self.project_root / f"{script_name}.spec"

        return {
            "script": script_path.name,
            "name": exe_name,
            "spec": spec_file.name if spec_file.exists() else None
        }

    def get_platform_name(self) -> str:
        """获取平台名称"""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "windows":
            return f"windows-{machine}"
        elif system == "darwin":
            # 明确区分 Intel Mac 和 Apple Silicon Mac
            if machine in ["arm64", "aarch64"]:
                return "macos-arm64"  # Apple Silicon (M1/M2/M3)
            elif machine in ["x86_64", "amd64"]:
                return "macos-x86_64"  # Intel Mac
            else:
                return f"macos-{machine}"  # 其他未知架构
        elif system == "linux":
            return f"linux-{machine}"
        else:
            return f"{system}-{machine}"

    def clean(self):
        """清理构建目录"""
        print("🧹 Cleaning build directories...")

        dirs_to_clean = [self.dist_dir, self.build_dir, "__pycache__"]

        for dir_path in dirs_to_clean:
            if isinstance(dir_path, str):
                dir_path = self.project_root / dir_path

            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"   Removed: {dir_path}")
                except OSError as e:
                    if "Device or resource busy" in str(e) or e.errno == 16 or "Permission denied" in str(e) or e.errno == 13:
                        # 在 Docker 环境中，挂载的目录无法删除或权限不足，只清理内容
                        print(f"   Clearing contents of mounted directory: {dir_path}")
                        for item in dir_path.iterdir():
                            try:
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            except OSError as perm_error:
                                # 如果是权限问题，尝试修改权限后再删除
                                if "Permission denied" in str(perm_error) or perm_error.errno == 13:
                                    try:
                                        import stat
                                        item.chmod(stat.S_IWRITE | stat.S_IREAD)
                                        if item.is_dir():
                                            shutil.rmtree(item)
                                        else:
                                            item.unlink()
                                    except OSError:
                                        pass  # 最终忽略无法删除的文件
                                else:
                                    pass  # 忽略其他错误
                    else:
                        print(f"   Warning: Could not remove {dir_path}: {e}")

        # 清理 .pyc 文件
        for pyc_file in self.project_root.rglob("*.pyc"):
            try:
                pyc_file.unlink()
            except OSError:
                pass  # 忽略无法删除的 .pyc 文件

        print("✅ Clean completed")

    def analyze_script_imports(self, script_path: Path) -> Set[str]:
        """分析脚本中的导入语句"""
        imports = set()

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

            print(f"   📄 Analyzed imports from {script_path.name}: {sorted(imports)}")
            return imports

        except Exception as e:
            print(f"   ⚠️  Failed to analyze imports from {script_path}: {e}")
            return set()

    def get_requirements_for_script(self, script_path: Path) -> Set[str]:
        """获取脚本的所有依赖"""
        script_name = script_path.stem
        all_requirements = set()

        # 通用依赖
        general_requirements = self.project_root / "requirements.txt"
        if general_requirements.exists():
            with open(general_requirements, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        all_requirements.add(line)

        # 特定服务依赖 - 先在脚本同目录查找，再在项目根目录查找
        script_dir = script_path.parent
        specific_requirements_paths = [
            script_dir / f"{script_name}_requirements.txt",  # 脚本同目录
            self.project_root / f"{script_name}_requirements.txt"  # 项目根目录
        ]
        
        for specific_requirements in specific_requirements_paths:
            if specific_requirements.exists():
                with open(specific_requirements, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            all_requirements.add(line)
                break  # 找到一个就停止

        return all_requirements

    def build_executable(self, script_path: Path, onefile: bool = True) -> bool:
        """构建可执行文件"""
        config = self.get_server_config(script_path)
        script_name = script_path.stem

        print(f"🔨 Building {config['name']} executable for {self.platform_name}...")

        # 创建虚拟环境
        venv_dir = self.build_dir / f"venv_{script_name}"
        if venv_dir.exists():
            shutil.rmtree(venv_dir)

        print(f"   Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)

        # 确定虚拟环境路径
        if platform.system() == "Windows":
            venv_python = venv_dir / "Scripts" / "python.exe"
            venv_pip = venv_dir / "Scripts" / "pip.exe"
            venv_pyinstaller = venv_dir / "Scripts" / "pyinstaller.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
            venv_pip = venv_dir / "bin" / "pip"
            venv_pyinstaller = venv_dir / "bin" / "pyinstaller"

        try:
            # 安装依赖
            if not self.install_dependencies_in_venv(script_path, venv_pip):
                return False

            # 安装 mcp_framework 包本身到虚拟环境
            print(f"   📦 Installing mcp_framework package...")
            # 首先尝试从 PyPI 安装
            result = subprocess.run([str(venv_pip), "install", "mcp-framework"],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                # 如果 PyPI 安装失败，尝试从当前项目目录安装
                print(f"   ⚠️  PyPI installation failed, trying to install from current project...")
                # 查找包含 mcp_framework 的项目根目录
                current_dir = Path(__file__).parent  # mcp_framework 目录
                project_root = current_dir.parent    # 项目根目录
                
                # 检查项目根目录是否包含 setup.py 或 pyproject.toml
                if (project_root / "setup.py").exists() or (project_root / "pyproject.toml").exists():
                    result = subprocess.run([str(venv_pip), "install", "-e", str(project_root)],
                                            capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"   ❌ Failed to install mcp_framework: {result.stderr}")
                        return False
                else:
                    print(f"   ❌ No setup.py or pyproject.toml found in {project_root}")
                    return False
            print(f"   ✅ mcp_framework installed successfully")

            # 安装 PyInstaller
            print(f"   🔧 Installing PyInstaller...")
            result = subprocess.run([str(venv_pip), "install", "pyinstaller>=5.0.0"],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Failed to install PyInstaller: {result.stderr}")
                return False

            # 构建命令
            cmd = [str(venv_pyinstaller)]
            cmd.extend([
                "--name", config['name'],
                "--console",
                "--distpath", str(self.dist_dir),
                "--workpath", str(self.build_dir / f"work_{script_name}"),
                "--specpath", str(self.build_dir / f"spec_{script_name}"),
                "--noconfirm"
            ])
            
            # 在非Docker环境中添加--clean参数，Docker环境中跳过以避免权限问题
            if not os.environ.get('DOCKER_ENV'):
                cmd.insert(1, "--clean")

            if onefile:
                cmd.append("--onefile")

            # 添加隐藏导入
            requirements = self.get_requirements_for_script(script_path)
            for req in requirements:
                pkg_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if pkg_name != "mcp-framework":  # 避免重复添加
                    cmd.extend(["--collect-all", pkg_name])
                    cmd.extend(["--hidden-import", pkg_name])  # 额外添加hidden-import确保包含
            
            # 添加 MCP Framework 的完整收集
            cmd.extend(["--collect-all", "mcp_framework"])
            
            # 添加额外的隐藏导入以确保所有模块都被包含
            mcp_framework_imports = [
                "mcp_framework", "mcp_framework.core", "mcp_framework.core.base",
                "mcp_framework.core.decorators", "mcp_framework.core.config",
                "mcp_framework.core.launcher", "mcp_framework.core.utils",
                "mcp_framework.server", "mcp_framework.server.http_server",
                "mcp_framework.server.handlers", "mcp_framework.server.middleware",
                "mcp_framework.web", "mcp_framework.web.config_page",
                "mcp_framework.web.setup_page", "mcp_framework.web.test_page"
            ]
            for imp in mcp_framework_imports:
                cmd.extend(["--hidden-import", imp])
            
            # 🔥 新增：自动检测并添加本地模块
            script_dir = script_path.parent.resolve()
            local_imports = self.analyze_script_imports(script_path)
            collected_modules = set()
            
            # 创建临时目录来存放本地模块
            temp_modules_dir = self.build_dir / f"temp_modules_{script_name}"
            temp_modules_dir.mkdir(parents=True, exist_ok=True)
            
            # 递归检测本地模块的依赖
            def collect_local_dependencies(module_path: Path, collected: set):
                if module_path.stem in collected:
                    return
                collected.add(module_path.stem)
                
                deps = self.analyze_script_imports(module_path)
                for dep in deps:
                    dep_path = (script_dir / f"{dep}.py").resolve()
                    if dep_path.exists() and dep not in collected:
                        print(f"   📦 Adding local dependency: {dep}")
                        cmd.extend(["--hidden-import", dep])
                        # 复制模块到临时目录
                        temp_dep_path = temp_modules_dir / f"{dep}.py"
                        shutil.copy2(dep_path, temp_dep_path)
                        collect_local_dependencies(dep_path, collected)
            
            # 检测并添加本地模块
            for imp in local_imports:
                # 检查是否是本地模块（同目录下的.py文件）
                local_module_path = (script_dir / f"{imp}.py").resolve()
                if local_module_path.exists():
                    print(f"   📦 Adding local module: {imp}")
                    cmd.extend(["--hidden-import", imp])
                    # 复制模块到临时目录
                    temp_module_path = temp_modules_dir / f"{imp}.py"
                    shutil.copy2(local_module_path, temp_module_path)
                    # 递归收集依赖
                    collect_local_dependencies(local_module_path, collected_modules)
            
            # 将临时目录添加到Python路径
            if temp_modules_dir.exists() and any(temp_modules_dir.iterdir()):
                cmd.extend(["--paths", str(temp_modules_dir)])

            cmd.append(str(script_path))

            print(f"   🔧 Running PyInstaller...")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"   ❌ PyInstaller failed: {result.stderr}")
                return False
            else:
                print("   ✅ Executable built successfully")
                return True

        except Exception as e:
            print(f"❌ Exception during build: {e}")
            return False
        finally:
            # 清理虚拟环境
            if venv_dir.exists():
                shutil.rmtree(venv_dir)

    def install_dependencies_in_venv(self, script_path: Path, venv_pip: Path) -> bool:
        """在虚拟环境中安装依赖"""
        requirements = self.get_requirements_for_script(script_path)

        if requirements:
            temp_req = self.build_dir / f"temp_req_{script_path.stem}.txt"
            temp_req.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_req, 'w', encoding='utf-8') as f:
                for req in sorted(requirements):
                    f.write(f"{req}\n")

            try:
                # 升级 pip - Windows 平台使用更稳定的方式
                if platform.system() == "Windows":
                    # Windows 平台使用 python -m pip 并允许失败
                    result = subprocess.run([str(venv_pip).replace("pip.exe", "python.exe"), "-m", "pip", "install", "--upgrade", "pip", "--no-warn-script-location"],
                                           capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"   ⚠️  pip upgrade skipped on Windows: {result.stderr}")
                else:
                    subprocess.run([str(venv_pip), "install", "--upgrade", "pip"],
                                   check=True, capture_output=True)

                # 安装依赖
                subprocess.run([str(venv_pip), "install", "-r", str(temp_req)],
                               check=True, capture_output=True, text=True)
                print(f"   ✅ Dependencies installed successfully")
                return True

            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install dependencies: {e}")
                return False
            finally:
                if temp_req.exists():
                    temp_req.unlink()
        else:
            print(f"   ⚠️  No requirements to install")

        return True

    def create_package(self, script_path: Path, include_source: bool = False) -> bool:
        """创建分发包"""
        config = self.get_server_config(script_path)
        
        # 确定可执行文件路径
        if platform.system() == "Windows":
            exe_name = f"{config['name']}.exe"
        else:
            exe_name = config['name']

        exe_path = self.dist_dir / exe_name
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False

        # 创建包目录
        package_name = f"{config['name']}-{self.platform_name}-{self.timestamp}"
        package_dir = self.dist_dir / package_name
        package_dir.mkdir(exist_ok=True)

        # 复制可执行文件
        shutil.copy2(exe_path, package_dir / exe_name)

        # 创建 requirements.txt
        self.create_complete_requirements(script_path, package_dir)

        # 复制其他文件
        for file_name in ["README.md", "LICENSE"]:
            file_path = self.project_root / file_name
            if file_path.exists():
                shutil.copy2(file_path, package_dir / file_name)

        # 创建启动脚本
        self.create_startup_scripts(package_dir, exe_name)

        # 包含源代码（可选）
        if include_source:
            source_dir = package_dir / "source"
            source_dir.mkdir(exist_ok=True)
            shutil.copy2(script_path, source_dir / script_path.name)

        # 创建压缩包
        archive_path = self.create_archive(package_dir)
        print(f"✅ Package created: {archive_path}")
        return True

    def create_complete_requirements(self, script_path: Path, package_dir: Path):
        """创建完整的 requirements.txt"""
        requirements = self.get_requirements_for_script(script_path)
        req_file = package_dir / "requirements.txt"
        
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.get_server_config(script_path)['name']} Dependencies\n")
            f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for req in sorted(requirements):
                f.write(f"{req}\n")

    def create_startup_scripts(self, package_dir: Path, exe_name: str):
        """创建启动脚本"""
        # Windows 批处理文件
        if platform.system() == "Windows":
            bat_content = f"""@echo off
echo Starting MCP Server...
"{exe_name}" %*
pause
"""
            with open(package_dir / "start.bat", "w") as f:
                f.write(bat_content)

        # Unix shell 脚本
        sh_content = f"""#!/bin/bash
echo Starting MCP Server...
cd "$(dirname "$0")"
./{exe_name} "$@"
"""
        sh_file = package_dir / "start.sh"
        with open(sh_file, "w") as f:
            f.write(sh_content)

        # 设置执行权限
        if platform.system() != "Windows":
            os.chmod(sh_file, 0o755)
            os.chmod(package_dir / exe_name, 0o755)

    def create_archive(self, package_dir: Path) -> Path:
        """创建压缩包"""
        archive_name = package_dir.name

        if platform.system() == "Windows":
            archive_path = package_dir.parent / f"{archive_name}.zip"
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in package_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir.parent)
                        zf.write(file_path, arcname)
        else:
            archive_path = package_dir.parent / f"{archive_name}.tar.gz"
            with tarfile.open(archive_path, 'w:gz') as tf:
                tf.add(package_dir, arcname=archive_name)

        return archive_path

    def build_all(self, clean: bool = True, test: bool = True, 
                  onefile: bool = True, include_source: bool = False) -> bool:
        """构建所有服务器"""
        if clean:
            self.clean()

        # 创建目录
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)

        # 发现服务器
        if self.server_script:
            servers = [Path(self.server_script)]
        else:
            servers = self.discover_servers()

        if not servers:
            print("❌ No server scripts found")
            return False

        built_servers = []
        for script_path in servers:
            config = self.get_server_config(script_path)
            print(f"\n🔨 Building {config['name']}...")

            # 构建可执行文件
            if not self.build_executable(script_path, onefile=onefile):
                print(f"❌ Failed to build {config['name']}")
                continue

            # 创建分发包
            if not self.create_package(script_path, include_source=include_source):
                print(f"❌ Failed to create package for {config['name']}")
                continue

            built_servers.append(config['name'])

        if not built_servers:
            print("\n❌ No servers were built successfully")
            return False

        print("\n🎉 Build completed successfully!")
        print(f"✅ Successfully built {len(built_servers)} server(s):")
        for server_name in built_servers:
            print(f"   - {server_name}")

        return True


def check_docker():
    """检查 Docker 是否可用"""
    try:
        subprocess.run(["docker", "--version"], 
                     check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_docker_platform(target_platform, args):
    """使用 Docker 构建指定平台"""
    print(f"🐳 Building for {target_platform} using Docker...")
    
    current_dir = Path.cwd()
    
    # 创建临时 Dockerfile
    dockerfile_content = get_dockerfile_content(target_platform)
    dockerfile_path = current_dir / f"Dockerfile.{target_platform}"
    
    try:
        # 写入 Dockerfile
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        
        # 构建 Docker 镜像
        image_name = f"mcp-server-builder-{target_platform}"
        build_cmd = [
            "docker", "build", 
            "--no-cache",  # 强制重新构建，确保使用最新代码
            "-f", str(dockerfile_path),
            "-t", image_name,
            "."
        ]
        
        print("   Building Docker image...")
        subprocess.run(build_cmd, check=True, cwd=current_dir)
        
        # 运行构建容器
        # 支持自定义输出目录
        if args.output_dir:
            dist_dir = Path(args.output_dir).resolve()
        else:
            dist_dir = current_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建Docker运行命令，先准备mcp-build的参数
        mcp_build_args = []
        if args.server:
            mcp_build_args.extend(["--server", args.server])
        if args.output_dir:
            mcp_build_args.extend(["--output-dir", "/app/output"])  # 使用新的挂载点
        if args.no_test:
            mcp_build_args.append("--no-test")
        # Docker环境中默认禁用清理，避免权限问题
        if args.no_clean or True:  # 在Docker中总是禁用清理
            mcp_build_args.append("--no-clean")
        if args.include_source:
            mcp_build_args.append("--include-source")
        
        run_cmd = [
            "docker", "run", "--rm",
            "-v", f"{dist_dir}:/app/output",  # 使用不同的挂载点避免冲突
            "-v", f"{current_dir}:/app/src",
            "-w", "/app/src",  # 设置工作目录为源代码目录
            image_name
        ] + mcp_build_args
        
        print("   Running build in container...")
        subprocess.run(run_cmd, check=True, cwd=current_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        return False
    finally:
        # 清理临时 Dockerfile
        if dockerfile_path.exists():
            dockerfile_path.unlink()


def get_dockerfile_content(platform):
    """获取指定平台的 Dockerfile 内容"""
    if platform == "linux":
        return '''FROM python:3.11-alpine

# 安装系统依赖
RUN apk add --no-cache gcc musl-dev g++ linux-headers

# 设置工作目录
WORKDIR /app

# 设置Docker环境变量，用于跳过PyInstaller的--clean参数
ENV DOCKER_ENV=1

# 安装最新的 mcp-framework
RUN pip install --no-cache-dir --upgrade mcp-framework

# 设置入口点
ENTRYPOINT ["mcp-build"]
'''
    elif platform == "windows":
        return '''FROM python:3.11-windowsservercore

# 设置工作目录
WORKDIR C:\\app

# 安装 mcp-framework
RUN pip install --no-cache-dir mcp-framework

# 设置入口点
ENTRYPOINT ["mcp-build"]
'''
    else:
        raise ValueError(f"Unsupported platform: {platform}")


def run_cross_platform_build(args):
    """运行跨平台构建"""
    print(f"🌍 Running cross-platform build for {args.platform}...")
    
    # 导入 platform 模块
    import platform as platform_module
    
    # 检查 Docker 可用性
    if not check_docker():
        print("❌ Docker is required for cross-platform builds")
        print("   Please install Docker and try again.")
        return False

    if args.platform == "all":
        platforms = ["linux", "windows", "macos"]
        success_count = 0
        
        # 检查当前系统信息
        current_system = platform_module.system().lower()
        current_machine = platform_module.machine().lower()
        
        if current_system == "darwin":
            if current_machine in ["arm64", "aarch64"]:
                print(f"🍎 Running on Apple Silicon Mac (ARM64)")
            elif current_machine in ["x86_64", "amd64"]:
                print(f"🍎 Running on Intel Mac (x86_64)")
            else:
                print(f"🍎 Running on Mac ({current_machine})")
        
        for platform_name in platforms:
            print(f"\n{'='*50}")
            print(f"Building for {platform_name}...")
            print(f"{'='*50}")
            
            if platform_name in ["macos", "linux"]:
                # macOS 和 Linux 构建使用本地构建
                if platform_name == "macos" and platform_module.system().lower() != "darwin":
                    print(f"⚠️  macOS build skipped (not running on macOS)")
                    print(f"   macOS builds can only be performed on macOS systems")
                elif platform_name == "linux" and platform_module.system().lower() not in ["linux", "darwin"]:
                    print(f"⚠️  Linux build skipped (not running on Linux/macOS)")
                    print(f"   Linux builds can be performed on Linux or macOS systems")
                else:
                    builder = MCPServerBuilder(server_script=args.server, output_dir=args.output_dir)
                    if builder.build_all(
                        clean=not args.no_clean,
                        test=not args.no_test,
                        onefile=not args.no_onefile,
                        include_source=args.include_source
                    ):
                        print(f"✅ {platform_name} build successful")
                        success_count += 1
                    else:
                        print(f"❌ {platform_name} build failed")
            else:
                # Windows 仍使用 Docker 构建
                if build_docker_platform(platform_name, args):
                    print(f"✅ {platform_name} build successful")
                    success_count += 1
                else:
                    print(f"❌ {platform_name} build failed")
        
        print(f"\n{'='*50}")
        print(f"Build Summary: {success_count}/{len(platforms)} platforms successful")
        print(f"{'='*50}")
        
        return success_count == len(platforms)
    else:
        if args.platform in ["macos", "linux"]:
            # macOS 和 Linux 构建使用本地构建
            if args.platform == "macos" and platform_module.system().lower() != "darwin":
                print("❌ macOS builds can only be performed on macOS systems")
                print("   Please use a macOS machine or GitHub Actions with macos runners")
                return False
            elif args.platform == "linux" and platform_module.system().lower() not in ["linux", "darwin"]:
                print("❌ Linux builds can be performed on Linux or macOS systems")
                print("   Please use a Linux/macOS machine or GitHub Actions with ubuntu runners")
                return False
            else:
                builder = MCPServerBuilder(server_script=args.server)
                return builder.build_all(
                    clean=not args.no_clean,
                    test=not args.no_test,
                    onefile=not args.no_onefile,
                    include_source=args.include_source
                )
        else:
            # Windows 仍使用 Docker 构建
            return build_docker_platform(args.platform, args)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Server Build Script")
    parser.add_argument("--server", "-s", help="Specific server script to build")
    parser.add_argument("--platform", "-p", 
                       choices=["native", "linux", "windows", "macos", "all"],
                       default="native",
                       help="Target platform to build for (requires Docker for cross-platform)")
    parser.add_argument("--output-dir", "-o", help="Custom output directory for build artifacts")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning")
    parser.add_argument("--no-test", action="store_true", help="Skip tests")
    parser.add_argument("--no-onefile", action="store_true", help="Build as directory")
    parser.add_argument("--include-source", action="store_true", help="Include source")
    parser.add_argument("--clean-only", action="store_true", help="Only clean")
    parser.add_argument("--list", "-l", action="store_true", help="List servers")
    parser.add_argument("--check-docker", action="store_true", help="Check if Docker is available")

    args = parser.parse_args()
    
    # 检查 Docker 可用性
    if args.check_docker:
        if check_docker():
            print("✅ Docker is available")
        else:
            print("❌ Docker is not available")
        return
    
    # 如果是跨平台构建，调用跨平台构建脚本
    if args.platform != "native":
        success = run_cross_platform_build(args)
        sys.exit(0 if success else 1)
    
    # 原有的本地构建逻辑
    builder = MCPServerBuilder(server_script=args.server, output_dir=args.output_dir)

    if args.list:
        servers = builder.discover_servers()
        print("📋 Available server scripts:")
        for server in servers:
            config = builder.get_server_config(server)
            print(f"   - {server.name} → {config['name']}")
        return

    if args.clean_only:
        builder.clean()
        return

    success = builder.build_all(
        clean=not args.no_clean,
        test=not args.no_test,
        onefile=not args.no_onefile,
        include_source=args.include_source
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()