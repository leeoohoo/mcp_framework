#!/usr/bin/env python3
"""
优化的 MCP Framework 构建系统
专注于减少启动时间和文件大小
"""

import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Set


class OptimizedMCPBuilder:
    """优化的MCP服务器构建器"""

    def __init__(self, server_script=None, output_dir=None):
        self.project_root = Path.cwd()
        self.dist_dir = Path(output_dir).resolve() if output_dir else self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.platform_name = self.get_platform_name()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.server_script = server_script

    def get_platform_name(self) -> str:
        """获取平台名称"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            return f"windows-{machine}"
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "macos-arm64"
            elif machine in ["x86_64", "amd64"]:
                return "macos-x86_64"
            else:
                return f"macos-{machine}"
        elif system == "linux":
            return f"linux-{machine}"
        else:
            return f"{system}-{machine}"

    def create_optimized_spec_file(self, script_path: Path) -> Path:
        """创建优化的.spec文件"""
        script_name = script_path.stem
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 优化的PyInstaller配置
block_cipher = None

# 最小化的隐藏导入 - 只包含必需的模块
hiddenimports = [
    'mcp_framework.core.base',
    'mcp_framework.core.decorators', 
    'mcp_framework.core.launcher',
    'mcp_framework.core.simple_launcher',
    'mcp_framework.server.stdio_server',
    'asyncio',
    'json',
    'sys',
    'os',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'urllib',
    'urllib.request',
    'urllib.parse',
    'http',
    'http.client'
]

# 排除不必要的模块以减少文件大小 - 保守策略
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'PIL',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',
    'django',
    'flask',
    'tornado',
    'jupyter',
    'notebook',
    'IPython',
    'pytest',
    'doctest',
    'pdb',
    'profile',
    'cProfile',
    'pstats',
    'trace',
    'timeit'
    # 注意：不排除 email, urllib, http 等标准库模块，因为很多第三方库依赖它们
]

# 数据文件 - 只包含必需的
datas = []

a = Analysis(
    ['{script_path}'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 移除不必要的二进制文件
a.binaries = [x for x in a.binaries if not any(
    exclude in x[0].lower() for exclude in [
        'qt', 'tk', 'tcl', '_ssl', '_hashlib', '_bz2', '_lzma'
    ]
)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{script_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 启用strip减少文件大小
    upx=False,   # 禁用UPX避免启动延迟
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    optimize=2,  # 启用Python字节码优化
)
'''
        
        spec_file = self.build_dir / f"{script_name}_optimized.spec"
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        return spec_file

    def build_optimized_executable(self, script_path: Path) -> bool:
        """构建优化的可执行文件"""
        script_name = script_path.stem
        print(f"🚀 构建优化版本: {script_name}")
        
        # 创建优化的spec文件
        spec_file = self.create_optimized_spec_file(script_path)
        
        # 构建命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir / f"work_{script_name}"),
            str(spec_file)
        ]
        
        print(f"   🔧 执行PyInstaller...")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"   ❌ 构建失败: {result.stderr}")
            return False
        else:
            print(f"   ✅ 构建成功")
            
            # 显示文件大小
            exe_path = self.dist_dir / script_name
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"   📦 文件大小: {size_mb:.1f} MB")
            
            return True

    def create_startup_optimization_script(self, script_path: Path):
        """创建启动优化脚本"""
        script_name = script_path.stem
        optimized_script = self.project_root / f"{script_name}_optimized.py"
        
        optimization_code = f'''#!/usr/bin/env python3
"""
优化启动的 {script_name}
减少导入时间和初始化开销
"""

import sys
import os

# 启动优化：预设环境变量
os.environ.setdefault('PYTHONOPTIMIZE', '2')
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')

# 延迟导入：只在需要时导入重型模块
def lazy_import():
    """延迟导入重型模块"""
    global mcp_framework_imported
    if not globals().get('mcp_framework_imported'):
        from {script_path.stem} import *
        globals()['mcp_framework_imported'] = True

# 快速启动检查
def quick_start_check():
    """快速启动检查，跳过不必要的验证"""
    # 跳过依赖检查（假设打包时已验证）
    return True

if __name__ == "__main__":
    # 优化的启动流程
    if quick_start_check():
        lazy_import()
        # 调用原始的main函数
        main()
'''
        
        with open(optimized_script, 'w', encoding='utf-8') as f:
            f.write(optimization_code)
        
        return optimized_script

    def clean(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"   已清理: {dir_path}")
                except Exception as e:
                    print(f"   清理失败 {dir_path}: {e}")


def create_fast_launcher_template():
    """创建快速启动器模板"""
    template = '''#!/usr/bin/env python3
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
'''
    return template


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="优化的MCP服务器构建器")
    parser.add_argument("script", help="要构建的服务器脚本")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--create-template", action="store_true", 
                       help="创建快速启动器模板")
    parser.add_argument("--clean", action="store_true", help="构建前清理")
    
    args = parser.parse_args()
    
    if args.create_template:
        template_path = Path("fast_launcher_template.py")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(create_fast_launcher_template())
        print(f"✅ 快速启动器模板已创建: {template_path}")
        return
    
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"❌ 脚本文件不存在: {script_path}")
        sys.exit(1)
    
    builder = OptimizedMCPBuilder(script_path, args.output)
    
    if args.clean:
        builder.clean()
    
    print("🚀 开始优化构建...")
    success = builder.build_optimized_executable(script_path)
    
    if success:
        print("✅ 优化构建完成！")
        print("\n💡 启动优化建议:")
        print("1. 使用 --optimize 2 参数启动Python")
        print("2. 设置环境变量 PYTHONDONTWRITEBYTECODE=1")
        print("3. 考虑使用stdio模式而非HTTP模式")
        print("4. 避免在启动时进行重型计算")
    else:
        print("❌ 构建失败")
        sys.exit(1)


if __name__ == "__main__":
    main()