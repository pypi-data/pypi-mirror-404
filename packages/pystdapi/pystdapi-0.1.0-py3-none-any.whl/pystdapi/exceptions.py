"""
异常处理模块

定义 ASGI Web 框架中使用的异常类。
"""

import json
from typing import Any, Dict, Optional
from .utils import json_dumps


class PystdAPIException(Exception):
    """PystdAPI 框架的基础异常类"""
    pass


class HTTPResponse(PystdAPIException):
    """
    HTTP 响应异常
    
    用于提前结束请求处理并返回 HTTP 响应。
    """
    
    def __init__(
        self,
        status: int = 200,
        body: Any = "",
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        **kwargs,
    ):
        self.status = status
        self.body = body
        self.headers = headers or {}
        self.content_type = content_type
        
        if content_type and "content-type" not in self.headers:
            self.headers["content-type"] = content_type
            
        super().__init__(f"HTTP {status}")


class HTTPError(HTTPResponse):
    """
    HTTP 错误异常
    
    用于表示 HTTP 错误响应。
    """
    
    def __init__(
        self,
        status: int = 500,
        message: str = "Internal Server Error",
        exception: Optional[Exception] = None,
        traceback: Optional[str] = None,
        **kwargs,
    ):
        self.exception = exception
        self.traceback = traceback
        
        # 构建错误响应体
        error_body = {
            "error": {
                "code": status,
                "message": message,
            }
        }
        
        body = json_dumps(error_body)
        headers = kwargs.pop("headers", {})
        headers["content-type"] = "application/json"
        
        super().__init__(status, body, headers, **kwargs)


class RouteError(PystdAPIException):
    """路由相关异常的基础类"""
    pass


class RouteSyntaxError(RouteError):
    """路由语法错误"""
    pass


class RouteBuildError(RouteError):
    """路由构建错误"""
    pass


class PluginError(PystdAPIException):
    """插件相关异常"""
    pass


class TemplateError(PystdAPIException):
    """模板相关异常"""
    pass


# HTTP 状态码描述
HTTP_STATUS_CODES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}