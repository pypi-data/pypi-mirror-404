"""
请求对象模块

定义 ASGI 请求对象，用于封装 HTTP 请求信息。
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs as urllib_parse_qs

from .utils import tob, touni, parse_auth, parse_content_type


class Request:
    """
    ASGI 请求对象
    
    封装 HTTP 请求信息，提供方便的访问接口。
    """
    
    def __init__(self, scope: Dict[str, Any], receive: callable):
        """
        初始化请求对象
        
        Args:
            scope: ASGI 连接范围信息
            receive: 接收消息的回调函数
        """
        self.scope = scope
        self._receive = receive
        self._body: Optional[bytes] = None
        self._json: Optional[Any] = None
        self._form: Optional[Dict[str, List[str]]] = None
        
        # 从 scope 中提取常用信息
        self.method = scope.get('method', 'GET').upper()
        self.path = scope.get('path', '/')
        self.query_string = scope.get('query_string', b'').decode('latin-1')
        self.headers = self._parse_headers(scope.get('headers', []))
        self.client = scope.get('client')
        self.server = scope.get('server')
        
        # 解析查询参数
        self.query = self._parse_query()
    
    def _parse_headers(self, headers: List[Tuple[bytes, bytes]]) -> Dict[str, str]:
        """解析 ASGI 头部信息"""
        result = {}
        for key, value in headers:
            key_str = key.decode('latin-1').title()
            value_str = value.decode('latin-1')
            result[key_str] = value_str
        return result
    
    def _parse_query(self) -> Dict[str, List[str]]:
        """解析查询字符串"""
        if not self.query_string:
            return {}
        
        # 使用 urllib.parse_qs 解析查询字符串
        return urllib_parse_qs(self.query_string, keep_blank_values=True)
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取请求头"""
        return self.headers.get(name.title(), default)
    
    @property
    def content_type(self) -> str:
        """获取 Content-Type 头"""
        return self.get_header('Content-Type', '').lower()
    
    @property
    def content_length(self) -> int:
        """获取 Content-Length 头"""
        length = self.get_header('Content-Length')
        return int(length) if length else 0
    
    @property
    def host(self) -> str:
        """获取 Host 头"""
        return self.get_header('Host', '')
    
    @property
    def user_agent(self) -> str:
        """获取 User-Agent 头"""
        return self.get_header('User-Agent', '')
    
    @property
    def accept(self) -> str:
        """获取 Accept 头"""
        return self.get_header('Accept', '*/*')
    
    @property
    def authorization(self) -> Optional[Tuple[str, str]]:
        """获取认证信息"""
        auth_header = self.get_header('Authorization')
        if auth_header:
            return parse_auth(auth_header)
        return None
    
    async def body(self) -> bytes:
        """获取请求体（异步）"""
        if self._body is not None:
            return self._body
        
        body_parts = []
        more_body = True
        
        while more_body:
            message = await self._receive()
            body = message.get('body', b'')
            more_body = message.get('more_body', False)
            
            if body:
                body_parts.append(body)
        
        self._body = b''.join(body_parts)
        return self._body
    
    async def text(self, encoding: str = 'utf-8') -> str:
        """获取请求体文本（异步）"""
        body = await self.body()
        return body.decode(encoding)
    
    async def json(self) -> Any:
        """获取 JSON 请求体（异步）"""
        if self._json is not None:
            return self._json
        
        content_type, _ = parse_content_type(self.content_type)
        if content_type not in ('application/json', 'text/json'):
            raise ValueError('Content-Type is not JSON')
        
        body_text = await self.text()
        try:
            self._json = json.loads(body_text)
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON: {e}')
        
        return self._json
    
    async def form(self) -> Dict[str, List[str]]:
        """获取表单数据（异步）"""
        if self._form is not None:
            return self._form
        
        content_type, params = parse_content_type(self.content_type)
        
        if content_type == 'application/x-www-form-urlencoded':
            body_text = await self.text(params.get('charset', 'utf-8'))
            self._form = urllib_parse_qs(body_text, keep_blank_values=True)
        elif content_type.startswith('multipart/form-data'):
            # TODO: 实现 multipart/form-data 解析
            self._form = {}
        else:
            self._form = {}
        
        return self._form
    
    def get_cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取 Cookie 值"""
        cookie_header = self.get_header('Cookie')
        if not cookie_header:
            return default
        
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies.get(name, default)
    
    @property
    def cookies(self) -> Dict[str, str]:
        """获取所有 Cookie"""
        cookie_header = self.get_header('Cookie')
        if not cookie_header:
            return {}
        
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    @property
    def is_ajax(self) -> bool:
        """检查是否为 AJAX 请求"""
        xhr_header = self.get_header('X-Requested-With')
        return xhr_header and xhr_header.lower() == 'xmlhttprequest'
    
    @property
    def is_json(self) -> bool:
        """检查是否为 JSON 请求"""
        content_type, _ = parse_content_type(self.content_type)
        return content_type in ('application/json', 'text/json')
    
    @property
    def is_form(self) -> bool:
        """检查是否为表单请求"""
        content_type, _ = parse_content_type(self.content_type)
        return content_type in ('application/x-www-form-urlencoded', 'multipart/form-data')
    
    def __repr__(self) -> str:
        return f'<Request {self.method} {self.path}>'