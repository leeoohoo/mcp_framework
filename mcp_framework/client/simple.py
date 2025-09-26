"""
MCP 简化客户端
提供最简单易用的 MCP 服务器交互接口
"""

import asyncio
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from .base import MCPStdioClient
from .config import ConfigClient
from .tools import ToolsClient, Tool


class SimpleClient:
    """
    MCP 简化客户端 - 统一所有功能的简单接口
    
    这个类整合了配置管理和工具调用功能，提供最简单的使用方式。
    用户只需要知道服务器脚本路径和可选的别名即可开始使用。
    """
    
    def __init__(self, 
                 server_script: str,
                 alias: Optional[str] = None,
                 **kwargs):
        """
        初始化简化客户端
        
        Args:
            server_script: 服务器脚本路径
            alias: 服务器别名（可选）
            **kwargs: 其他可选参数（如超时时间等）
        """
        self.server_script = server_script
        self.alias = alias
        self.kwargs = kwargs
        self._client = None
        self._is_ready = False
    
    async def _ensure_ready(self):
        """确保客户端已准备就绪"""
        if not self._is_ready:
            self._client = ToolsClient(
                server_script=self.server_script,
                alias=self.alias,
                **self.kwargs
            )
            await self._client.connect()
            await self._client.initialize()
            self._is_ready = True
    
    # ==================== 工具相关方法 ====================
    
    async def tools(self) -> List[str]:
        """
        获取所有可用工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        await self._ensure_ready()
        return await self._client.get_tool_names()
    
    async def call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        调用工具（最简单的方式）
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            Dict[str, Any]: 工具执行结果
        """
        await self._ensure_ready()
        return await self._client.call_tool(tool_name, kwargs)
    
    async def tool_info(self, tool_name: str) -> Optional[Tool]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[Tool]: 工具信息，如果不存在则返回 None
        """
        await self._ensure_ready()
        return await self._client.get_tool(tool_name)
    
    async def has_tool(self, tool_name: str) -> bool:
        """
        检查是否有指定工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否存在该工具
        """
        await self._ensure_ready()
        return await self._client.tool_exists(tool_name)
    
    async def call_stream(self, tool_name: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式调用工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Yields:
            str: 流式输出的内容块
            
        Raises:
            Exception: 工具调用失败
        """
        await self._ensure_ready()
        async for chunk in self._client.call_tool_stream(tool_name, kwargs):
            yield chunk
    
    # ==================== 配置相关方法 ====================
    
    async def config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置字典
        """
        await self._ensure_ready()
        try:
            # 创建临时配置客户端
            config_client = ConfigClient(
                server_script=self.server_script,
                alias=self.alias,
                **self.kwargs
            )
            async with config_client:
                return await config_client.get_config()
        except Exception as e:
            print(f"警告: 配置获取失败: {e}")
            return {}
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值
        
        Args:
            key: 配置项键名（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            Any: 配置项的值
        """
        try:
            config_client = ConfigClient(
                server_script=self.server_script,
                alias=self.alias,
                **self.kwargs
            )
            async with config_client:
                return await config_client.get_config_value(key, default)
        except Exception as e:
            print(f"警告: 配置获取失败: {e}")
            return default
    
    async def set(self, key: str, value: Any) -> bool:
        """
        设置配置项的值
        
        Args:
            key: 配置项键名（支持点号分隔的嵌套键）
            value: 要设置的值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            config_client = ConfigClient(
                server_script=self.server_script,
                alias=self.alias,
                **self.kwargs
            )
            async with config_client:
                return await config_client.set_config_value(key, value)
        except Exception as e:
            print(f"警告: 配置设置失败: {e}")
            return False
    
    async def update(self, **kwargs) -> bool:
        """
        批量更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            bool: 更新是否成功
        """
        try:
            config_client = ConfigClient(
                server_script=self.server_script,
                alias=self.alias,
                **self.kwargs
            )
            async with config_client:
                return await config_client.update_config(kwargs)
        except Exception as e:
            print(f"警告: 配置更新失败: {e}")
            return False
    
    # ==================== 上下文管理器 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_ready()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.disconnect()
            self._is_ready = False
    
    def __del__(self):
        """析构函数"""
        if self._client:
            try:
                asyncio.create_task(self._client.disconnect())
            except:
                pass


# ==================== 全局便捷函数 ====================

async def quick_call(server_script: str, 
                    tool_name: str, 
                    alias: Optional[str] = None,
                    **tool_args) -> Dict[str, Any]:
    """
    快速调用工具（一行代码完成）
    
    Args:
        server_script: 服务器脚本路径
        tool_name: 工具名称
        alias: 服务器别名（可选）
        **tool_args: 工具参数
        
    Returns:
        Dict[str, Any]: 工具执行结果
    """
    async with SimpleClient(server_script, alias) as client:
        return await client.call(tool_name, **tool_args)


async def quick_get(server_script: str,
                   config_key: str,
                   alias: Optional[str] = None,
                   default: Any = None) -> Any:
    """
    快速获取配置值
    
    Args:
        server_script: 服务器脚本路径
        config_key: 配置项键名
        alias: 服务器别名（可选）
        default: 默认值
        
    Returns:
        Any: 配置项的值
    """
    async with SimpleClient(server_script, alias) as client:
        return await client.get(config_key, default)


async def quick_set(server_script: str,
                   config_key: str,
                   value: Any,
                   alias: Optional[str] = None) -> bool:
    """
    快速设置配置值
    
    Args:
        server_script: 服务器脚本路径
        config_key: 配置项键名
        value: 要设置的值
        alias: 服务器别名（可选）
        
    Returns:
        bool: 设置是否成功
    """
    async with SimpleClient(server_script, alias) as client:
        return await client.set(config_key, value)


async def quick_update(server_script: str,
                      alias: Optional[str] = None,
                      **config_updates) -> bool:
    """
    快速批量更新配置
    
    Args:
        server_script: 服务器脚本路径
        alias: 服务器别名（可选）
        **config_updates: 要更新的配置项
        
    Returns:
        bool: 更新是否成功
    """
    async with SimpleClient(server_script, alias) as client:
        return await client.update(**config_updates)


async def quick_tools(server_script: str,
                     alias: Optional[str] = None) -> List[str]:
    """
    快速获取工具列表
    
    Args:
        server_script: 服务器脚本路径
        alias: 服务器别名（可选）
        
    Returns:
        List[str]: 工具名称列表
    """
    async with SimpleClient(server_script, alias) as client:
        return await client.tools()


async def quick_call_stream(server_script: str, 
                           tool_name: str, 
                           alias: Optional[str] = None,
                           **tool_args) -> AsyncGenerator[str, None]:
    """
    快速流式调用工具
    
    Args:
        server_script: 服务器脚本路径
        tool_name: 工具名称
        alias: 服务器别名（可选）
        **tool_args: 工具参数
        
    Yields:
        str: 流式输出的内容块
    """
    async with SimpleClient(server_script, alias) as client:
        async for chunk in client.call_stream(tool_name, **tool_args):
            yield chunk


# ==================== 同步包装器（可选） ====================

def sync_call(server_script: str, 
              tool_name: str, 
              alias: Optional[str] = None,
              **tool_args) -> Dict[str, Any]:
    """
    同步版本的快速工具调用
    
    Args:
        server_script: 服务器脚本路径
        tool_name: 工具名称
        alias: 服务器别名（可选）
        **tool_args: 工具参数
        
    Returns:
        Dict[str, Any]: 工具执行结果
    """
    return asyncio.run(quick_call(server_script, tool_name, alias, **tool_args))


def sync_get(server_script: str,
             config_key: str,
             alias: Optional[str] = None,
             default: Any = None) -> Any:
    """
    同步版本的快速配置获取
    
    Args:
        server_script: 服务器脚本路径
        config_key: 配置项键名
        alias: 服务器别名（可选）
        default: 默认值
        
    Returns:
        Any: 配置项的值
    """
    return asyncio.run(quick_get(server_script, config_key, alias, default))


def sync_set(server_script: str,
             config_key: str,
             value: Any,
             alias: Optional[str] = None) -> bool:
    """
    同步版本的快速配置设置
    
    Args:
        server_script: 服务器脚本路径
        config_key: 配置项键名
        value: 要设置的值
        alias: 服务器别名（可选）
        
    Returns:
        bool: 设置是否成功
    """
    return asyncio.run(quick_set(server_script, config_key, value, alias))


def sync_update(server_script: str,
                alias: Optional[str] = None,
                **config_updates) -> bool:
    """
    同步版本的快速配置批量更新
    
    Args:
        server_script: 服务器脚本路径
        alias: 服务器别名（可选）
        **config_updates: 要更新的配置项
        
    Returns:
        bool: 更新是否成功
    """
    return asyncio.run(quick_update(server_script, alias, **config_updates))


def sync_tools(server_script: str,
               alias: Optional[str] = None) -> List[str]:
    """
    同步版本的快速工具列表获取
    
    Args:
        server_script: 服务器脚本路径
        alias: 服务器别名（可选）
        
    Returns:
        List[str]: 工具名称列表
    """
    return asyncio.run(quick_tools(server_script, alias))


def sync_call_stream(server_script: str, 
                    tool_name: str, 
                    alias: Optional[str] = None,
                    **tool_args) -> str:
    """
    同步版本的流式工具调用（收集所有流式输出并返回完整结果）
    
    Args:
        server_script: 服务器脚本路径
        tool_name: 工具名称
        alias: 服务器别名（可选）
        **tool_args: 工具参数
        
    Returns:
        str: 完整的工具执行结果
    """
    async def _collect_stream():
        content = ""
        async for chunk in quick_call_stream(server_script, tool_name, alias, **tool_args):
            content += chunk
        return content
    
    return asyncio.run(_collect_stream())