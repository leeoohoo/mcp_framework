"""
MCP 配置管理客户端
提供便捷的配置获取和更新功能
"""

from typing import Dict, Any, Optional
from .base import MCPStdioClient


class ConfigClient(MCPStdioClient):
    """MCP 配置管理客户端"""
    
    async def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置字典
            
        Raises:
            Exception: 获取配置失败
        """
        if not self.is_initialized:
            raise Exception("客户端未初始化")
        
        response = await self.send_request("config/get")
        
        if "error" in response:
            raise Exception(f"获取配置失败: {response['error']}")
        
        result = response.get("result", {})
        return result.get("config", {})
    
    async def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_updates: 要更新的配置项
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            Exception: 更新配置失败
        """
        if not self.is_initialized:
            raise Exception("客户端未初始化")
        
        params = {"config": config_updates}
        response = await self.send_request("config/update", params)
        
        if "error" in response:
            raise Exception(f"更新配置失败: {response['error']}")
        
        result = response.get("result", {})
        if not result.get("success"):
            error_msg = result.get("error", "未知错误")
            raise Exception(f"配置更新失败: {error_msg}")
        
        return True
    
    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取特定配置项的值
        
        Args:
            key: 配置项键名，支持点号分隔的嵌套键（如 "custom_params.max_file_size"）
            default: 默认值
            
        Returns:
            Any: 配置项的值
        """
        config = await self.get_config()
        
        # 支持嵌套键访问
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    async def set_config_value(self, key: str, value: Any) -> bool:
        """
        设置特定配置项的值
        
        Args:
            key: 配置项键名，支持点号分隔的嵌套键
            value: 要设置的值
            
        Returns:
            bool: 设置是否成功
        """
        # 构建嵌套配置更新
        keys = key.split('.')
        config_update = {}
        current = config_update
        
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                current[k] = value
            else:
                current[k] = {}
                current = current[k]
        
        return await self.update_config(config_update)
    
    async def reset_config(self) -> bool:
        """
        重置配置到默认值
        
        Returns:
            bool: 重置是否成功
        """
        if not self.is_initialized:
            raise Exception("客户端未初始化")
        
        response = await self.send_request("config/reset")
        
        if "error" in response:
            raise Exception(f"重置配置失败: {response['error']}")
        
        result = response.get("result", {})
        return result.get("success", False)
    
    async def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置的有效性
        
        Args:
            config: 要验证的配置
            
        Returns:
            Dict[str, Any]: 验证结果，包含 valid 字段和可能的错误信息
        """
        if not self.is_initialized:
            raise Exception("客户端未初始化")
        
        params = {"config": config}
        response = await self.send_request("config/validate", params)
        
        if "error" in response:
            raise Exception(f"验证配置失败: {response['error']}")
        
        return response.get("result", {"valid": False, "errors": ["未知验证错误"]})


# 便捷函数
async def get_server_config(server_script: str, 
                           alias: Optional[str] = None,
                           **kwargs) -> Dict[str, Any]:
    """
    便捷函数：获取服务器配置
    
    Args:
        server_script: 服务器脚本路径
        alias: 服务器别名
        **kwargs: 其他客户端参数
        
    Returns:
        Dict[str, Any]: 服务器配置
    """
    async with ConfigClient(server_script, alias, **kwargs) as client:
        return await client.get_config()


async def update_server_config(server_script: str,
                              config_updates: Dict[str, Any],
                              alias: Optional[str] = None,
                              **kwargs) -> bool:
    """
    便捷函数：更新服务器配置
    
    Args:
        server_script: 服务器脚本路径
        config_updates: 配置更新
        alias: 服务器别名
        **kwargs: 其他客户端参数
        
    Returns:
        bool: 更新是否成功
    """
    async with ConfigClient(server_script, alias, **kwargs) as client:
        return await client.update_config(config_updates)