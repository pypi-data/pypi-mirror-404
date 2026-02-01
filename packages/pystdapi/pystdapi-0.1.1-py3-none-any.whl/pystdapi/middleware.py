"""
中间件模块

定义 ASGI 中间件系统，用于处理请求和响应的预处理和后处理。
"""

import functools
from typing import Any, Awaitable, Callable, Dict, List, Optional


class Middleware:
    """
    中间件基类
    
    所有中间件都应该继承这个类或实现相同的接口。
    """
    
    def __init__(self, app: Callable):
        """
        初始化中间件
        
        Args:
            app: ASGI 应用或下一个中间件
        """
        self.app = app
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """
        处理 ASGI 请求
        
        Args:
            scope: 连接范围信息
            receive: 接收消息的回调函数
            send: 发送消息的回调函数
        """
        await self.app(scope, receive, send)


class CORSMiddleware(Middleware):
    """
    CORS 中间件
    
    处理跨域资源共享。
    """
    
    def __init__(
        self,
        app: Callable,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ):
        super().__init__(app)
        
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_cors(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # 添加 CORS 头部
                origin = None
                for key, value in scope.get("headers", []):
                    if key.decode().lower() == "origin":
                        origin = value.decode()
                        break
                
                if origin and (origin in self.allow_origins or "*" in self.allow_origins):
                    headers[b"access-control-allow-origin"] = origin.encode()
                    
                    if self.allow_credentials:
                        headers[b"access-control-allow-credentials"] = b"true"
                    
                    if scope["method"] == "OPTIONS":
                        headers[b"access-control-allow-methods"] = ", ".join(self.allow_methods).encode()
                        headers[b"access-control-allow-headers"] = ", ".join(self.allow_headers).encode()
                        headers[b"access-control-max-age"] = str(self.max_age).encode()
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_with_cors)


class LoggingMiddleware(Middleware):
    """
    日志中间件
    
    记录请求和响应信息。
    """
    
    def __init__(self, app: Callable, logger: Optional[Callable] = None, format: str = "default"):
        super().__init__(app)
        self.logger = logger or print
        self.format = format
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 提取请求信息
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        client = scope.get("client", ("unknown", 0))
        http_version = scope.get("http_version", "1.1")
        
        start_time = None
        status_code = None
        
        async def receive_wrapper():
            nonlocal start_time
            if start_time is None:
                import time
                start_time = time.time()
            return await receive()
        
        async def send_wrapper(message: Dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                # 请求完成，记录响应信息
                import time
                duration = time.time() - start_time if start_time else 0
                
                # 根据格式选择日志输出
                if self.format == "simple":
                    # 简单格式: 127.0.0.1:55993 "GET /favicon.ico" 404
                    self.logger(f'{client[0]}:{client[1]} "{method} {path}" {status_code}')
                elif self.format == "verbose":
                    # 详细格式: 127.0.0.1:55993 - "GET /favicon.ico HTTP/1.1" 404
                    self.logger(f'{client[0]}:{client[1]} - "{method} {path} HTTP/{http_version}" {status_code}')
                else:
                    # 默认格式: [127.0.0.1:55993] GET /favicon.ico - 404
                    self.logger(f'[{client[0]}:{client[1]}] {method} {path} - {status_code}')
            
            await send(message)
        
        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as e:
            # 记录异常
            self.logger(f'[{client[0]}:{client[1]}] {method} {path} - ERROR: {e}')
            raise


class ErrorMiddleware(Middleware):
    """
    错误处理中间件
    
    捕获异常并返回适当的错误响应。
    """
    
    def __init__(self, app: Callable, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            from .responses import error_response
            
            # 根据异常类型确定状态码
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            elif hasattr(e, 'status'):
                status_code = e.status
            
            # 构建错误响应
            if self.debug:
                import traceback
                error_detail = {
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                }
                response = error_response(status_code, str(e))
                response._body = error_detail
            else:
                response = error_response(status_code)
            
            await response.send(send)


class StaticFilesMiddleware(Middleware):
    """
    静态文件中间件
    
    提供静态文件服务。
    """
    
    def __init__(self, app: Callable, directory: str, url_prefix: str = "/static"):
        super().__init__(app)
        self.directory = directory
        self.url_prefix = url_prefix.rstrip("/")
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        # 检查是否为静态文件请求
        if path.startswith(self.url_prefix):
            import os
            from .responses import Response
            
            # 构建文件路径
            relative_path = path[len(self.url_prefix):].lstrip("/")
            file_path = os.path.join(self.directory, relative_path)
            
            # 安全检查：确保文件在指定目录内
            file_path = os.path.abspath(file_path)
            if not file_path.startswith(os.path.abspath(self.directory)):
                await self.app(scope, receive, send)
                return
            
            # 检查文件是否存在
            if os.path.isfile(file_path):
                # 读取文件内容
                with open(file_path, "rb") as f:
                    content = f.read()
                
                # 根据文件扩展名确定内容类型
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"
                
                # 发送文件响应
                response = Response(content, content_type=content_type)
                await response.send(send)
                return
        
        await self.app(scope, receive, send)


def middleware(func: Callable) -> Callable:
    """
    中间件装饰器
    
    将普通函数转换为中间件类。
    """
    
    class DecoratedMiddleware(Middleware):
        async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
            await func(scope, receive, send, self.app)
    
    return DecoratedMiddleware


# 常用中间件快捷方式
def cors_middleware(
    allow_origins: List[str] = None,
    allow_methods: List[str] = None,
    allow_headers: List[str] = None,
    allow_credentials: bool = False,
    max_age: int = 600,
) -> Callable:
    """创建 CORS 中间件"""
    return lambda app: CORSMiddleware(
        app,
        allow_origins=allow_origins,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        allow_credentials=allow_credentials,
        max_age=max_age,
    )


def logging_middleware(logger: Optional[Callable] = None, format: str = "default") -> Callable:
    """创建日志中间件
    
    Args:
        logger: 日志记录器函数，默认为print
        format: 日志格式，可选值: "default", "simple", "verbose"
    """
    return lambda app: LoggingMiddleware(app, logger=logger, format=format)


def error_middleware(debug: bool = False) -> Callable:
    """创建错误处理中间件"""
    return lambda app: ErrorMiddleware(app, debug=debug)


def static_files_middleware(directory: str, url_prefix: str = "/static") -> Callable:
    """创建静态文件中间件"""
    return lambda app: StaticFilesMiddleware(app, directory, url_prefix)