"""
应用框架模块

定义 ASGI 应用对象，提供 Web 框架的核心功能。
"""

import asyncio
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Union

from .exceptions import HTTPError, HTTPResponse
from .requests import Request
from .responses import Response, text_response, html_response, json_response, redirect_response
from .routing import Router, Route
from .utils import cached_property


class PystdAPI:
    """
    ASGI Web 应用框架
    
    纯异步 Web 框架，基于 ASGI 标准。
    """
    
    def __init__(self, name: str = "pystdapi", debug: bool = False):
        """
        初始化应用
        
        Args:
            name: 应用名称
            debug: 调试模式
        """
        self.name = name
        self.debug = debug
        self.router = Router()
        self.plugins: List[Any] = []
        self.middleware: List[Callable] = []
        self.config: Dict[str, Any] = {}
        self._error_handler: Dict[int, Callable] = {}
        self._hooks: Dict[str, List[Callable]] = {
            'before_request': [],
            'after_request': [],
            'before_response': [],
            'after_response': [],
        }
    
    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self.middleware.append(middleware)
    
    def add_plugin(self, plugin: Any) -> None:
        """添加插件"""
        self.plugins.append(plugin)
    
    def hook(self, name: str) -> Callable:
        """钩子装饰器"""
        def decorator(func: Callable) -> Callable:
            self._hooks.setdefault(name, []).append(func)
            return func
        return decorator
    
    def error_handler(self, code: int) -> Callable:
        """错误处理装饰器"""
        def decorator(func: Callable) -> Callable:
            self._error_handler[code] = func
            return func
        return decorator
    
    def route(
        self,
        rule: str,
        method: str = "GET",
        name: Optional[str] = None,
        **options,
    ) -> Callable:
        """路由装饰器"""
        def decorator(callback: Callable) -> Callable:
            self.add_route(rule, method, callback, name=name, **options)
            return callback
        return decorator
    
    def get(self, rule: str, **options) -> Callable:
        """GET 路由装饰器"""
        return self.route(rule, "GET", **options)
    
    def post(self, rule: str, **options) -> Callable:
        """POST 路由装饰器"""
        return self.route(rule, "POST", **options)
    
    def put(self, rule: str, **options) -> Callable:
        """PUT 路由装饰器"""
        return self.route(rule, "PUT", **options)
    
    def delete(self, rule: str, **options) -> Callable:
        """DELETE 路由装饰器"""
        return self.route(rule, "DELETE", **options)
    
    def patch(self, rule: str, **options) -> Callable:
        """PATCH 路由装饰器"""
        return self.route(rule, "PATCH", **options)
    
    def add_route(
        self,
        rule: str,
        method: str,
        callback: Callable,
        name: Optional[str] = None,
        **options,
    ) -> Route:
        """添加路由"""
        # 创建路由对象
        route = Route(
            app=self,
            rule=rule,
            method=method,
            callback=callback,
            name=name,
            **options,
        )
        
        # 添加到路由器
        self.router.add(rule, method, route, name)
        
        return route
    
    def mount(self, prefix: str, app: 'PystdAPI') -> None:
        """挂载子应用"""
        # TODO: 实现子应用挂载
        pass
    
    async def _handle_request(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """处理单个请求"""
        request = Request(scope, receive)
        
        try:
            # 执行前置钩子
            for hook in self._hooks['before_request']:
                if inspect.iscoroutinefunction(hook):
                    await hook(request)
                else:
                    hook(request)
            
            # 匹配路由
            route, args = self.router.match(request.method, request.path)
            
            # 绑定请求对象
            request.route = route
            
            # 执行路由处理函数
            if inspect.iscoroutinefunction(route.call):
                result = await route.call(request, **args)
            else:
                result = route.call(request, **args)
            
            # 处理响应
            if isinstance(result, Response):
                response = result
            elif isinstance(result, (str, bytes, dict, list)):
                response = self._make_response(result)
            elif isinstance(result, tuple) and len(result) == 2:
                body, status = result
                response = self._make_response(body, status=status)
            else:
                raise HTTPError(500, "无效的响应类型")
            
            # 执行响应前钩子
            for hook in self._hooks['before_response']:
                if inspect.iscoroutinefunction(hook):
                    await hook(request, response)
                else:
                    hook(request, response)
            
            # 发送响应
            await response.send(send)
            
            # 执行响应后钩子
            for hook in self._hooks['after_response']:
                if inspect.iscoroutinefunction(hook):
                    await hook(request, response)
                else:
                    hook(request, response)
            
        except HTTPError as e:
            # 处理 HTTP 错误
            response = await self._handle_error(e, request)
            await response.send(send)
        except Exception as e:
            # 处理其他异常
            if self.debug:
                raise
            
            response = self._handle_exception(e, request)
            await response.send(send)
        
        finally:
            # 执行后置钩子
            for hook in self._hooks['after_request']:
                if inspect.iscoroutinefunction(hook):
                    await hook(request)
                else:
                    hook(request)
    
    def _make_response(self, body: Any, status: int = 200, **kwargs) -> Response:
        """创建响应对象"""
        if isinstance(body, dict) or isinstance(body, list):
            return json_response(body, status, **kwargs)
        elif isinstance(body, str) and body.startswith('<'):
            return html_response(body, status, **kwargs)
        else:
            return text_response(str(body), status, **kwargs)
    
    async def _handle_error(self, error: HTTPError, request: Request) -> Response:
        """处理 HTTP 错误"""
        # 检查是否有自定义错误处理器
        if error.status in self._error_handler:
            handler = self._error_handler[error.status]
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(error, request)
                else:
                    result = handler(error, request)
                
                if isinstance(result, Response):
                    return result
                elif isinstance(result, (str, bytes, dict, list)):
                    return self._make_response(result, status=error.status)
            except Exception:
                pass
        
        # 默认错误处理
        if request.is_json:
            return json_response({
                'error': {
                    'code': error.status,
                    'message': error.body,
                }
            }, status=error.status)
        else:
            return text_response(error.body, status=error.status)
    
    def _handle_exception(self, exception: Exception, request: Request) -> Response:
        """处理异常"""
        if self.debug:
            import traceback
            error_detail = {
                'error': str(exception),
                'traceback': traceback.format_exc(),
            }
            return json_response(error_detail, status=500)
        else:
            return text_response("Internal Server Error", status=500)
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """ASGI 应用接口"""
        # 应用中间件
        app = self._handle_request
        for middleware in reversed(self.middleware):
            app = middleware(app)
        
        # 处理请求
        await app(scope, receive, send)
    
    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: Optional[bool] = None,
        reload: bool = False,
        **options,
    ) -> None:
        """运行开发服务器"""
        import sys
        
        if debug is not None:
            self.debug = debug
        
        # 导入服务器适配器
        from .server import get_server
        
        # 根据 reload 参数选择服务器
        server_name = 'dev' if reload else 'asgi'
        
        # 创建服务器
        # 将reload参数添加到options中，以便get_server可以获取它
        options_with_reload = options.copy()
        options_with_reload['reload'] = reload
        server = get_server(server_name, host=host, port=port, **options_with_reload)
        
        # 运行服务器
        try:
            print(f"Starting server on http://{host}:{port}")
            server.run(self)
        except KeyboardInterrupt:
            print("\nServer stopped")
            sys.exit(0)
    
    def url_for(self, route_name: str, *anons, **kwargs) -> str:
        """构建 URL
        
        Args:
            route_name: 路由名称
            *anons: 匿名参数（按顺序传递）
            **kwargs: 命名参数
            
        Returns:
            构建的 URL 字符串
        """
        return self.router.build(route_name, *anons, **kwargs)


# 快捷函数
def create_app(name: str = "pystdapi", debug: bool = False) -> PystdAPI:
    """创建应用实例"""
    return PystdAPI(name=name, debug=debug)