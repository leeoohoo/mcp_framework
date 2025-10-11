#!/usr/bin/env python3
"""
MCP Framework 启动优化工具
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import argparse


class StartupOptimizer:
    """启动优化器"""
    
    def __init__(self):
        self.optimizations_applied = []
    
    def apply_environment_optimizations(self):
        """应用环境变量优化"""
        optimizations = {
            'PYTHONOPTIMIZE': '2',  # 启用最高级别优化
            'PYTHONDONTWRITEBYTECODE': '1',  # 不生成.pyc文件
            'PYTHONUNBUFFERED': '1',  # 不缓冲输出
            'PYTHONHASHSEED': '0',  # 固定hash种子
        }
        
        for key, value in optimizations.items():
            if key not in os.environ:
                os.environ[key] = value
                self.optimizations_applied.append(f"设置 {key}={value}")
    
    def optimize_imports(self):
        """优化导入"""
        # 预导入常用模块
        try:
            import json
            import asyncio
            import sys
            import os
            self.optimizations_applied.append("预导入核心模块")
        except ImportError as e:
            print(f"⚠️  导入模块失败: {e}")
    
    def create_optimized_launcher(self, original_script: Path) -> Path:
        """创建优化的启动器"""
        optimized_script = original_script.parent / f"{original_script.stem}_fast.py"
        
        # 读取原始脚本内容来检测服务器实例
        try:
            with open(original_script, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取原始脚本失败: {e}")
            return None
        
        # 检测服务器实例变量名
        server_var = "server"
        if "app = " in content:
            server_var = "app"
        elif "mcp_server = " in content:
            server_var = "mcp_server"
        
        launcher_code = f'''#!/usr/bin/env python3
"""
优化启动器 for {original_script.name}
自动生成的快速启动版本
"""

import os
import sys

# 启动优化环境变量
os.environ.update({{
    'PYTHONOPTIMIZE': '2',
    'PYTHONDONTWRITEBYTECODE': '1',
    'PYTHONUNBUFFERED': '1',
    'PYTHONHASHSEED': '0'
}})

# 预导入核心模块
import json
import asyncio

def main():
    """优化的主函数"""
    try:
        # 导入原始服务器模块
        import sys
        from pathlib import Path
        
        # 添加当前目录到Python路径
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # 导入原始脚本
        module_name = "{original_script.stem}"
        original_module = __import__(module_name)
        
        # 获取服务器实例
        if hasattr(original_module, '{server_var}'):
            server_instance = getattr(original_module, '{server_var}')
            
            # 使用简化启动器
            from mcp_framework import simple_main
            simple_main(server_instance, "{original_script.stem.title()}Server")
        else:
            print("❌ 未找到服务器实例，尝试调用原始main函数")
            if hasattr(original_module, 'main'):
                original_module.main()
            else:
                print("❌ 未找到main函数")
                sys.exit(1)
                
    except ImportError as e:
        print(f"❌ 导入失败: {{e}}")
        print("尝试直接执行原始脚本...")
        
        # 回退到执行原始脚本
        import subprocess
        result = subprocess.run([sys.executable, "{original_script}"] + sys.argv[1:])
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ 启动失败: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        try:
            with open(optimized_script, 'w', encoding='utf-8') as f:
                f.write(launcher_code)
            
            # 设置执行权限
            optimized_script.chmod(0o755)
            
            self.optimizations_applied.append(f"创建优化启动器: {optimized_script}")
            return optimized_script
        except Exception as e:
            print(f"❌ 创建优化启动器失败: {e}")
            return None
    
    def benchmark_startup(self, script_path: Path, mode: str = "stdio") -> float:
        """测试启动时间"""
        print(f"⏱️  测试 {script_path.name} 的启动时间...")
        
        try:
            start_time = time.time()
            
            # 构建测试命令
            cmd = [sys.executable, str(script_path)]
            if mode == "stdio":
                cmd.append("stdio")
            elif mode == "http":
                cmd.extend(["http", "8080"])
            
            # 添加快速退出参数
            cmd.append("--help")
            
            # 运行脚本并立即退出
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=script_path.parent
            )
            
            end_time = time.time()
            startup_time = end_time - start_time
            
            if result.returncode == 0:
                print(f"   ✅ 启动时间: {startup_time:.2f} 秒")
            else:
                print(f"   ⚠️  启动时间: {startup_time:.2f} 秒 (有错误)")
                if result.stderr:
                    print(f"   错误信息: {result.stderr[:200]}...")
            
            return startup_time
            
        except subprocess.TimeoutExpired:
            print("   ❌ 启动超时 (>30秒)")
            return 30.0
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return -1.0
    
    def create_environment_script(self, script_path: Path) -> Path:
        """创建环境变量设置脚本"""
        env_script = script_path.parent / f"env_{script_path.stem}.sh"
        
        env_content = f'''#!/bin/bash
# 启动优化环境变量设置脚本
# 用法: source {env_script.name} && python {script_path.name}

export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=0

echo "✅ 已设置启动优化环境变量"
echo "现在可以运行: python {script_path.name}"
'''
        
        try:
            with open(env_script, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            env_script.chmod(0o755)
            self.optimizations_applied.append(f"创建环境脚本: {env_script}")
            return env_script
        except Exception as e:
            print(f"❌ 创建环境脚本失败: {e}")
            return None
    
    def generate_optimization_report(self) -> str:
        """生成优化报告"""
        report = ["🚀 启动优化报告", "=" * 40]
        
        if self.optimizations_applied:
            report.append("✅ 已应用的优化:")
            for opt in self.optimizations_applied:
                report.append(f"   • {opt}")
        else:
            report.append("❌ 未应用任何优化")
        
        report.extend([
            "",
            "💡 额外建议:",
            "   • 使用 PyInstaller 的 --optimize 选项",
            "   • 考虑使用 stdio 模式而非 HTTP 模式",
            "   • 移除不必要的依赖检查",
            "   • 使用延迟导入策略",
            "   • 考虑使用 Nuitka 编译器",
            "",
            "🔧 使用方法:",
            "   1. 使用优化启动器: python script_fast.py",
            "   2. 设置环境变量: source env_script.sh",
            "   3. 选择stdio模式: python script.py stdio"
        ])
        
        return "\n".join(report)


def optimize_existing_script(script_path: str, benchmark: bool = False):
    """优化现有脚本"""
    script_path = Path(script_path)
    
    if not script_path.exists():
        print(f"❌ 脚本不存在: {script_path}")
        return
    
    optimizer = StartupOptimizer()
    
    print(f"🔧 优化脚本: {script_path.name}")
    print("=" * 50)
    
    # 应用环境优化
    optimizer.apply_environment_optimizations()
    
    # 优化导入
    optimizer.optimize_imports()
    
    # 创建优化启动器
    optimized_script = optimizer.create_optimized_launcher(script_path)
    
    # 创建环境脚本
    env_script = optimizer.create_environment_script(script_path)
    
    # 基准测试
    if benchmark and optimized_script:
        print("\n📊 性能测试:")
        print("-" * 30)
        
        # 测试原始脚本
        original_time = optimizer.benchmark_startup(script_path)
        
        # 测试优化脚本
        if optimized_script.exists():
            optimized_time = optimizer.benchmark_startup(optimized_script)
            
            if original_time > 0 and optimized_time > 0:
                improvement = ((original_time - optimized_time) / original_time) * 100
                print(f"\n📈 性能改善: {improvement:.1f}%")
                if improvement > 0:
                    print(f"   节省时间: {original_time - optimized_time:.2f} 秒")
                else:
                    print("   ⚠️  优化效果不明显，可能需要其他优化策略")
    
    # 生成报告
    report = optimizer.generate_optimization_report()
    print("\n" + report)
    
    print(f"\n✅ 优化完成！")
    if optimized_script:
        print(f"🚀 快速启动: python {optimized_script.name}")
    if env_script:
        print(f"🌍 环境设置: source {env_script.name}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Framework 启动优化工具")
    parser.add_argument("script", help="要优化的脚本路径")
    parser.add_argument("--benchmark", "-b", action="store_true", help="测试启动时间")
    parser.add_argument("--mode", "-m", choices=["stdio", "http"], default="stdio",
                       help="测试模式 (默认: stdio)")
    
    args = parser.parse_args()
    
    if not Path(args.script).exists():
        print(f"❌ 脚本文件不存在: {args.script}")
        sys.exit(1)
    
    optimize_existing_script(args.script, args.benchmark)


if __name__ == "__main__":
    main()