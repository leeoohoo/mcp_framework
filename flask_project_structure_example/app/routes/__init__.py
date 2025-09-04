#!/usr/bin/env python3
"""
路由模块初始化
注册所有Flask路由
"""

from flask import Flask
from .api import register_api_routes

def register_routes(app: Flask, user_service, product_service):
    """注册所有路由"""
    register_api_routes(app, user_service, product_service)