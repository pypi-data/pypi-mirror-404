# 工具函数模块
# 提供 Web 框架中常用的工具函数。

import base64
import hashlib
import hmac
import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union
from email.utils import formatdate, parsedate_tz
import calendar
import time


# 类型别名
BytesLike = Union[bytes, bytearray, memoryview]
StringLike = Union[str, bytes]


def tob(data: StringLike, encoding: str = 'utf-8') -> bytes:
    """将字符串转换为字节"""
    if isinstance(data, str):
        return data.encode(encoding)
    return bytes(data) if data is not None else b''


def touni(data: StringLike, encoding: str = 'utf-8', errors: str = 'strict') -> str:
    """将字节转换为字符串"""
    if isinstance(data, bytes):
        return data.decode(encoding, errors)
    return str(data) if data is not None else ''


def html_escape(text: str) -> str:
    """转义 HTML 特殊字符"""
    text = text.replace('&', '&')
    text = text.replace('<', '<')
    text = text.replace('>', '>')
    text = text.replace('"', '"')
    text = text.replace("'", '&#039;')
    return text


def html_quote(text: str) -> str:
    """转义并引用字符串，用于 HTTP 属性"""
    return '"%s"' % html_escape(text).replace('\n', '&#10;').replace('\r', '&#13;').replace('\t', '&#9;')


def parse_auth(header: str) -> Optional[Tuple[str, str]]:
    """解析 HTTP Basic 认证头"""
    try:
        method, data = header.split(' ', 1)
        if method.lower() == 'basic':
            decoded = base64.b64decode(data).decode('utf-8')
            if ':' in decoded:
                username, password = decoded.split(':', 1)
                return username, password
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        pass
    return None


def parse_qs(qs: str) -> Dict[str, List[str]]:
    """解析查询字符串"""
    result: Dict[str, List[str]] = {}
    
    if not qs:
        return result
    
    for pair in qs.split('&'):
        if not pair:
            continue
        
        if '=' in pair:
            key, value = pair.split('=', 1)
        else:
            key, value = pair, ''
        
        key = urllib.parse.unquote(key.replace('+', ' '))
        value = urllib.parse.unquote(value.replace('+', ' '))
        
        if key in result:
            result[key].append(value)
        else:
            result[key] = [value]
    
    return result


def parse_date(date_str: str) -> Optional[int]:
    """解析 HTTP 日期字符串为 Unix 时间戳"""
    try:
        ts = parsedate_tz(date_str)
        if ts:
            return calendar.timegm(ts[:8] + (0,)) - (ts[9] or 0)
    except (TypeError, ValueError):
        pass
    return None


def http_date(timestamp: Optional[float] = None) -> str:
    """将时间戳格式化为 HTTP 日期字符串"""
    if timestamp is None:
        timestamp = time.time()
    return formatdate(timestamp, usegmt=True)


def json_dumps(obj: Any, **kwargs) -> str:
    """JSON 序列化，使用标准库的 json 模块"""
    # 默认设置 ensure_ascii=False 以支持中文显示
    if 'ensure_ascii' not in kwargs:
        kwargs['ensure_ascii'] = False
    return json.dumps(obj, **kwargs)


def json_loads(data: str, **kwargs) -> Any:
    """JSON 反序列化，使用标准库的 json 模块"""
    return json.loads(data, **kwargs)


def _lscmp(a: str, b: str) -> bool:
    """常量时间字符串比较（防止时序攻击）"""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def secure_compare(a: str, b: str) -> bool:
    """安全字符串比较"""
    return _lscmp(a, b)


def create_signature(secret: str, data: bytes, digestmod: Any = hashlib.sha256) -> str:
    """创建 HMAC 签名"""
    return base64.b64encode(
        hmac.new(tob(secret), data, digestmod=digestmod).digest()
    ).decode('ascii')


def verify_signature(secret: str, data: bytes, signature: str, digestmod: Any = hashlib.sha256) -> bool:
    """验证 HMAC 签名"""
    expected = create_signature(secret, data, digestmod)
    return secure_compare(signature, expected)


def parse_range_header(header: str, maxlen: int) -> List[Tuple[int, int]]:
    """解析 HTTP Range 头"""
    if not header or not header.startswith('bytes='):
        return []
    
    ranges = []
    for range_spec in header[6:].split(','):
        if '-' not in range_spec:
            continue
        
        start_str, end_str = range_spec.split('-', 1)
        
        try:
            if not start_str:  # bytes=-100
                start = max(0, maxlen - int(end_str))
                end = maxlen
            elif not end_str:  # bytes=100-
                start = int(start_str)
                end = maxlen
            else:  # bytes=100-200
                start = int(start_str)
                end = min(int(end_str) + 1, maxlen)
            
            if 0 <= start < end <= maxlen:
                ranges.append((start, end))
        except ValueError:
            pass
    
    return ranges


def parse_content_type(header: str) -> Tuple[str, Dict[str, str]]:
    """解析 Content-Type 头"""
    if not header:
        return '', {}
    
    parts = header.split(';', 1)
    content_type = parts[0].strip().lower()
    
    params = {}
    if len(parts) > 1:
        for param in parts[1].split(';'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key.strip()] = value.strip().strip('"')
    
    return content_type, params


def normalize_path(path: str) -> str:
    """规范化 URL 路径"""
    # 移除重复的斜杠
    path = re.sub(r'/{2,}', '/', path)
    # 确保以 / 开头
    if not path.startswith('/'):
        path = '/' + path
    # 移除末尾的 /（除非是根路径）
    if path != '/' and path.endswith('/'):
        path = path[:-1]
    return path


def path_shift(script_name: str, path_info: str, shift: int = 1) -> Tuple[str, str]:
    """将路径片段从 PATH_INFO 移动到 SCRIPT_NAME 或反之"""
    if shift == 0:
        return script_name, path_info
    
    path_list = path_info.strip('/').split('/')
    script_list = script_name.strip('/').split('/')
    
    if path_list and path_list[0] == '':
        path_list = []
    if script_list and script_list[0] == '':
        script_list = []
    
    if 0 < shift <= len(path_list):
        moved = path_list[:shift]
        script_list.extend(moved)
        path_list = path_list[shift:]
    elif 0 > shift >= -len(script_list):
        moved = script_list[shift:]
        path_list = moved + path_list
        script_list = script_list[:shift]
    else:
        empty = 'SCRIPT_NAME' if shift < 0 else 'PATH_INFO'
        raise ValueError(f"Cannot shift. Nothing left from {empty}")
    
    new_script_name = '/' + '/'.join(script_list)
    new_path_info = '/' + '/'.join(path_list)
    
    if path_info.endswith('/') and path_list:
        new_path_info += '/'
    
    return new_script_name, new_path_info


class cached_property:
    """缓存属性装饰器"""
    
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
    
    def __get__(self, obj, cls):
        if obj is None:
            return self
        
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value