#!/usr/bin/env python3
"""
MCP 框架配置管理
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .utils import get_config_dir


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = '0.0.0.0'
    port: int = 8080
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    default_dir: Optional[str] = None
    max_connections: int = 100
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        # 过滤掉不支持的字段，只保留ServerConfig支持的字段
        import inspect
        valid_fields = set(inspect.signature(cls).parameters.keys())
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典更新配置"""
        import inspect
        valid_fields = set(inspect.signature(self.__class__).parameters.keys())
        for key, value in data.items():
            if key in valid_fields and hasattr(self, key):
                setattr(self, key, value)


@dataclass
class ServerParameter:
    """服务器参数定义"""
    name: str
    display_name: str
    description: str
    param_type: str  # 'string', 'integer', 'boolean', 'select', 'path'
    default_value: Any = None
    required: bool = True
    options: Optional[List[str]] = None  # 用于 select 类型
    placeholder: Optional[str] = None
    validation_pattern: Optional[str] = None


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_name: str = "server_config.json"):
        self.config_dir = get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / config_name
        self.logger = logging.getLogger(f"{__name__}.ConfigManager")

    def load_config(self) -> ServerConfig:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded config from {self.config_file}")
                return ServerConfig.from_dict(data)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")

        # 返回默认配置
        config = ServerConfig()
        self.save_config(config)  # 保存默认配置
        return config

    def save_config(self, config: ServerConfig) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved config to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    def reset_config(self) -> ServerConfig:
        """重置配置为默认值"""
        config = ServerConfig()
        self.save_config(config)
        return config


class ServerConfigManager:
    """服务器配置管理器"""

    def __init__(self, server_name: str, port: Optional[int] = None, alias: Optional[str] = None):
        self.config_dir = get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持别名和端口号两种方式创建配置文件
        if alias is not None:
            # 使用别名方式
            self.config_file = self.config_dir / f"{server_name}_alias_{alias}_server_config.json"
            self.alias = alias
            self.port = port  # 可选，用于记录
        elif port is not None:
            # 使用端口号方式（向后兼容）
            self.config_file = self.config_dir / f"{server_name}_port_{port}_server_config.json"
            self.port = port
            self.alias = None
        else:
            # 默认配置文件
            self.config_file = self.config_dir / f"{server_name}_server_config.json"
            self.port = None
            self.alias = None
            
        self.server_name = server_name
        self.logger = logging.getLogger(f"{__name__}.ServerConfigManager")

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_file.exists()

    def load_server_config(self) -> Dict[str, Any]:
        """加载服务器配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded server config from {self.config_file}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load server config: {e}")
        return {}

    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """保存服务器配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved server config to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save server config: {e}")
            return False
    
    def list_port_configs(self) -> List[int]:
        """列出所有端口相关的配置文件"""
        ports = []
        pattern = f"{self.server_name}_port_*_server_config.json"
        
        for config_file in self.config_dir.glob(pattern):
            try:
                # 从文件名中提取端口号
                filename = config_file.stem
                port_part = filename.split('_port_')[1].split('_server_config')[0]
                port = int(port_part)
                ports.append(port)
            except (IndexError, ValueError) as e:
                self.logger.warning(f"无法解析配置文件端口号: {config_file}, 错误: {e}")
        
        return sorted(ports)
    
    def delete_port_config(self, port: int) -> bool:
        """删除指定端口的配置文件"""
        port_config_file = self.config_dir / f"{self.server_name}_port_{port}_server_config.json"
        try:
            if port_config_file.exists():
                port_config_file.unlink()
                self.logger.info(f"已删除端口 {port} 的配置文件: {port_config_file}")
                return True
            else:
                self.logger.warning(f"端口 {port} 的配置文件不存在: {port_config_file}")
                return False
        except Exception as e:
            self.logger.error(f"删除端口 {port} 配置文件失败: {e}")
            return False
    
    def list_alias_configs(self) -> List[str]:
        """列出所有别名相关的配置文件"""
        aliases = []
        pattern = f"{self.server_name}_alias_*_server_config.json"
        
        for config_file in self.config_dir.glob(pattern):
            try:
                # 从文件名中提取别名
                filename = config_file.stem
                alias_part = filename.split('_alias_')[1].split('_server_config')[0]
                aliases.append(alias_part)
            except (IndexError, ValueError) as e:
                self.logger.warning(f"无法解析配置文件别名: {config_file}, 错误: {e}")
        
        return sorted(aliases)
    
    def delete_alias_config(self, alias: str) -> bool:
        """删除指定别名的配置文件"""
        alias_config_file = self.config_dir / f"{self.server_name}_alias_{alias}_server_config.json"
        try:
            if alias_config_file.exists():
                alias_config_file.unlink()
                self.logger.info(f"已删除别名 {alias} 的配置文件: {alias_config_file}")
                return True
            else:
                self.logger.warning(f"别名 {alias} 的配置文件不存在: {alias_config_file}")
                return False
        except Exception as e:
            self.logger.error(f"删除别名 {alias} 配置文件失败: {e}")
            return False
    
    def list_all_configs(self) -> Dict[str, Any]:
        """列出所有配置文件（端口和别名）"""
        return {
            'ports': self.list_port_configs(),
            'aliases': self.list_alias_configs(),
            'total_configs': len(self.list_port_configs()) + len(self.list_alias_configs())
        }
    
    @classmethod
    def create_for_port(cls, server_name: str, port: int) -> 'ServerConfigManager':
        """为指定端口创建配置管理器"""
        return cls(server_name, port=port)
    
    @classmethod
    def create_for_alias(cls, server_name: str, alias: str) -> 'ServerConfigManager':
        """为指定别名创建配置管理器"""
        return cls(server_name, alias=alias)
    
    @classmethod
    def create_default(cls, server_name: str) -> 'ServerConfigManager':
        """创建默认配置管理器"""
        return cls(server_name)


class ServerConfigAdapter:
    """将ServerConfigManager适配为ConfigManager接口的适配器"""
    
    def __init__(self, server_config_manager: ServerConfigManager):
        self.server_config_manager = server_config_manager
        self.logger = logging.getLogger(f"{__name__}.ServerConfigAdapter")
    
    def load_config(self) -> ServerConfig:
        """加载配置并转换为ServerConfig对象"""
        config_dict = self.server_config_manager.load_server_config()
        if config_dict:
            try:
                return ServerConfig.from_dict(config_dict)
            except Exception as e:
                self.logger.error(f"Failed to convert config dict to ServerConfig: {e}")
        
        # 返回默认配置
        return ServerConfig()
    
    def save_config(self, config: ServerConfig) -> bool:
        """保存ServerConfig对象"""
        return self.server_config_manager.save_server_config(config.to_dict())
    
    def reset_config(self) -> ServerConfig:
        """重置配置为默认值"""
        config = ServerConfig()
        self.save_config(config)
        return config
    
    def load_server_config(self) -> Dict[str, Any]:
        """直接加载配置字典，包含自定义字段"""
        return self.server_config_manager.load_server_config()
    
    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """直接保存配置字典，包含自定义字段"""
        return self.server_config_manager.save_server_config(config)
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新配置，保留现有的自定义字段"""
        current_config = self.load_server_config()
        current_config.update(config_updates)
        return self.save_server_config(current_config)
    
    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.server_config_manager.config_exists()
    
    @property
    def config_file(self):
        """获取配置文件路径"""
        return self.server_config_manager.config_file
