"""
MCP 框架 Web 模块
"""

from .setup_page import SetupPageHandler
from .test_page import TestPageHandler
from .config_page import ConfigPageHandler

__all__ = [
    'SetupPageHandler',
    'TestPageHandler',
    'ConfigPageHandler'
]
