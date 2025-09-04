#!/usr/bin/env python3
"""
主启动文件
同时启动Flask应用和MCP服务器
"""

import threading
import time
import signal
import sys
from app import create_app
from app.mcp_config import mcp_server
from mcp_framework import run_server_main

def start_mcp_server():
    """在单独线程中启动MCP服务器"""
    try:
        print("🚀 启动MCP服务器...")
        run_server_main(
            server_instance=mcp_server,
            server_name="flask-integrated-mcp-server",
            default_port=8080
        )
    except Exception as e:
        print(f"❌ MCP服务器启动失败: {e}")
        sys.exit(1)

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\n🛑 正在关闭服务...")
    sys.exit(0)

def main():
    """主函数"""
    print("="*60)
    print("🎉 Flask + MCP Framework 集成服务启动")
    print("="*60)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建Flask应用
    flask_app = create_app()
    
    # 在后台线程启动MCP服务器
    mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
    mcp_thread.start()
    
    # 等待MCP服务器启动
    print("⏳ 等待MCP服务器启动...")
    time.sleep(2)
    
    print("\n📡 服务地址:")
    print(f"   Flask API: http://localhost:5001")
    print(f"   MCP服务器: http://localhost:8080")
    print("\n🔧 测试命令:")
    print("   # 测试Flask API")
    print("   curl http://localhost:5001/")
    print("   curl http://localhost:5001/api/users")
    print("   \n   # 测试MCP服务器")
    print("   curl http://localhost:8080/tools/list")
    print("   curl -X POST http://localhost:8080/tools/call \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"name\": \"get_user_info\", \"arguments\": {\"user_id\": 1}}'")
    print("\n" + "="*60)
    
    try:
        # 启动Flask应用
        flask_app.run(
            host='0.0.0.0',
            port=5001,  # 改为5001端口避免冲突
            debug=False,  # 生产环境建议设为False
            use_reloader=False  # 避免与MCP服务器冲突
        )
    except Exception as e:
        print(f"❌ Flask应用启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()