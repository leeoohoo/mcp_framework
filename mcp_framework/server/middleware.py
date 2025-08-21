#!/usr/bin/env python3
"""
MCP HTTP 服务器中间件
"""

import logging
import traceback
from datetime import datetime
from aiohttp import web

logger = logging.getLogger(__name__)

@web.middleware
async def cors_middleware(request, handler):
    """CORS 中间件"""
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cache-Control'
    return response

@web.middleware
async def error_middleware(request, handler):
    """错误处理中间件"""
    try:
        return await handler(request)
    except Exception as e:
        logger.error(f"Error handling request {request.path}: {str(e)}")
        logger.error(traceback.format_exc())
        return web.json_response({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }, status=500)

@web.middleware
async def logging_middleware(request, handler):
    """日志中间件"""
    start_time = datetime.now()
    response = await handler(request)
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"{request.method} {request.path} - {response.status} - {duration:.3f}s")
    return response
