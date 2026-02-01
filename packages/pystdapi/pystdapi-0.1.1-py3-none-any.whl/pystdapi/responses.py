"""
响应对象模块

定义 HTTP 响应对象，用于构建和发送 HTTP 响应。
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from http.cookies import SimpleCookie

from .utils import http_date, json_dumps
from .exceptions import HTTP_STATUS_CODES


class Response:
    """
    HTTP 响应对象
    
    用于构建和发送 HTTP 响应。
    """
    
    def __init__(
        self,
        body: Any = "",
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化响应对象
        
        Args:
            body: 响应体，可以是字符串、字节、字典或列表
            status: HTTP 状态码
            headers: 响应头
            content_type: 内容类型
            **kwargs: 额外参数（为了兼容性）
        """
        self.status = status
        self._body = body
        self._headers = headers or {}
        self._cookies = SimpleCookie()
        
        # 设置默认内容类型
        if content_type:
            self._headers['Content-Type'] = content_type
        elif 'Content-Type' not in self._headers:
            if isinstance(body, (dict, list)):
                self._headers['Content-Type'] = 'application/json; charset=utf-8'
            else:
                self._headers['Content-Type'] = 'text/plain; charset=utf-8'
        
        # 忽略额外的kwargs参数，避免错误
    
    @property
    def body(self) -> bytes:
        """获取响应体字节"""
        if isinstance(self._body, bytes):
            return self._body
        elif isinstance(self._body, str):
            return self._body.encode('utf-8')
        elif isinstance(self._body, (dict, list)):
            return json_dumps(self._body).encode('utf-8')
        else:
            return str(self._body).encode('utf-8')
    
    @property
    def headers(self) -> List[Tuple[bytes, bytes]]:
        """获取 ASGI 格式的头部列表"""
        result = []
        
        # 添加自定义头部
        for key, value in self._headers.items():
            result.append((key.encode('latin-1'), value.encode('latin-1')))
        
        # 添加 Cookie 头部
        if self._cookies:
            for cookie in self._cookies.values():
                result.append((b'Set-Cookie', cookie.OutputString().encode('latin-1')))
        
        # 添加 Content-Length
        body_length = len(self.body)
        result.append((b'Content-Length', str(body_length).encode('latin-1')))
        
        # 添加日期头部
        result.append((b'Date', http_date().encode('latin-1')))
        
        return result
    
    def set_header(self, name: str, value: str) -> None:
        """设置响应头"""
        self._headers[name] = value
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取响应头"""
        return self._headers.get(name, default)
    
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ) -> None:
        """设置 Cookie"""
        self._cookies[key] = value
        
        if max_age is not None:
            self._cookies[key]['max-age'] = max_age
        
        if expires is not None:
            self._cookies[key]['expires'] = expires
        
        if path:
            self._cookies[key]['path'] = path
        
        if domain:
            self._cookies[key]['domain'] = domain
        
        if secure:
            self._cookies[key]['secure'] = True
        
        if httponly:
            self._cookies[key]['httponly'] = True
        
        if samesite:
            self._cookies[key]['samesite'] = samesite
    
    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: Optional[str] = None,
    ) -> None:
        """删除 Cookie"""
        self.set_cookie(
            key,
            value="",
            max_age=0,
            expires=http_date(0),
            path=path,
            domain=domain,
        )
    
    async def send(self, send: callable) -> None:
        """发送响应（ASGI 接口）"""
        # 发送响应开始消息
        await send({
            'type': 'http.response.start',
            'status': self.status,
            'headers': self.headers,
        })
        
        # 发送响应体
        await send({
            'type': 'http.response.body',
            'body': self.body,
        })
    
    @classmethod
    def text(cls, text: str, status: int = 200, **kwargs) -> 'Response':
        """创建文本响应"""
        return cls(text, status, content_type='text/plain; charset=utf-8', **kwargs)
    
    @classmethod
    def html(cls, html: str, status: int = 200, **kwargs) -> 'Response':
        """创建 HTML 响应"""
        return cls(html, status, content_type='text/html; charset=utf-8', **kwargs)
    
    @classmethod
    def json(cls, data: Any, status: int = 200, **kwargs) -> 'Response':
        """创建 JSON 响应"""
        return cls(data, status, content_type='application/json; charset=utf-8', **kwargs)
    
    @classmethod
    def redirect(cls, url: str, status: int = 302) -> 'Response':
        """创建重定向响应"""
        response = cls(status=status)
        response.set_header('Location', url)
        return response
    
    @classmethod
    def error(cls, status: int, message: Optional[str] = None) -> 'Response':
        """创建错误响应"""
        if message is None:
            message = HTTP_STATUS_CODES.get(status, 'Unknown Error')
        
        error_data = {
            'error': {
                'code': status,
                'message': message,
            }
        }
        
        return cls.json(error_data, status)
    
    def __repr__(self) -> str:
        status_text = HTTP_STATUS_CODES.get(self.status, 'Unknown')
        return f'<Response {self.status} {status_text}>'


# 常用响应快捷方式
def text_response(text: str, status: int = 200, **kwargs) -> Response:
    """创建文本响应"""
    return Response.text(text, status, **kwargs)


def html_response(html: str, status: int = 200, **kwargs) -> Response:
    """创建 HTML 响应"""
    return Response.html(html, status, **kwargs)


def json_response(data: Any, status: int = 200, **kwargs) -> Response:
    """创建 JSON 响应"""
    return Response.json(data, status, **kwargs)


def redirect_response(url: str, status: int = 302) -> Response:
    """创建重定向响应"""
    return Response.redirect(url, status)


def error_response(status: int, message: Optional[str] = None) -> Response:
    """创建错误响应"""
    return Response.error(status, message)