"""
PystdAPI - 纯异步 Web 框架

基于 ASGI 标准的高性能异步 Web 框架，仅依赖 Python 标准库。
"""

__version__ = "0.1.1"
__author__ = "王伟勇"
__license__ = "MIT"

# 导出主要接口
from .app import PystdAPI, create_app
from .exceptions import HTTPError, HTTPResponse, RouteError
from .requests import Request
from .responses import Response, text_response, html_response, json_response, redirect_response, error_response
from .utils import html_escape, parse_auth, json_dumps, json_loads, cached_property
from .routing import Router, Route
from .middleware import (
    Middleware, CORSMiddleware, LoggingMiddleware, ErrorMiddleware, StaticFilesMiddleware,
    cors_middleware, logging_middleware, error_middleware, static_files_middleware
)
from .plugins import (
    Plugin, JSONPlugin, TemplatePlugin, SessionPlugin, AuthPlugin, CORSPlugin,
    json_plugin, template_plugin, session_plugin, auth_plugin, cors_plugin
)
from .templates import TemplateAdapter, SimpleTemplate, StringTemplate, render_template, render_string
from .server import ServerAdapter, ASGIServer, AutoServer, DevelopmentServer, run

# 快捷别名
app = PystdAPI

__all__ = [
    # 核心应用
    'PystdAPI', 'create_app', 'app',
    
    # 请求/响应
    'Request', 'Response', 'text_response', 'html_response', 'json_response', 
    'redirect_response', 'error_response',
    
    # 异常
    'HTTPError', 'HTTPResponse', 'RouteError',
    
    # 工具函数
    'html_escape', 'parse_auth', 'json_dumps', 'json_loads', 'cached_property',
    
    # 路由系统
    'Router', 'Route',
    
    # 中间件
    'Middleware', 'CORSMiddleware', 'LoggingMiddleware', 'ErrorMiddleware', 
    'StaticFilesMiddleware', 'cors_middleware', 'logging_middleware', 
    'error_middleware', 'static_files_middleware',
    
    # 插件系统
    'Plugin', 'JSONPlugin', 'TemplatePlugin', 'SessionPlugin', 'AuthPlugin', 
    'CORSPlugin', 'json_plugin', 'template_plugin', 'session_plugin', 
    'auth_plugin', 'cors_plugin',
    
    # 模板系统
    'TemplateAdapter', 'SimpleTemplate', 'StringTemplate', 'render_template', 
    'render_string',
    
    # 服务器适配器
    'ServerAdapter', 'ASGIServer', 'AutoServer', 'DevelopmentServer', 'run',
    
    # 元数据
    '__version__', '__author__', '__license__',
]