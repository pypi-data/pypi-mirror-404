"""
路由系统模块

定义路由器和路由对象，用于 URL 匹配和请求分发。
"""

import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple
from urllib.parse import urlencode

from .exceptions import RouteError, RouteSyntaxError, RouteBuildError
from .utils import cached_property


class Router:
    """
    路由器
    
    管理路由规则，匹配 URL 到处理函数。
    """
    
    # 默认模式匹配规则
    DEFAULT_PATTERN = '[^/]+'
    DEFAULT_FILTER = 're'
    
    # 每个正则表达式的最大分组数
    MAX_GROUPS_PER_PATTERN = 99
    
    def __init__(self, strict: bool = False):
        """
        初始化路由器
        
        Args:
            strict: 是否严格匹配顺序（静态路由不再优先检查）
        """
        self.rules: List[Tuple] = []  # 所有规则
        self._groups: Dict[Tuple[str, str], int] = {}  # 正则表达式索引
        self.builder: Dict[str, List] = {}  # URL 构建数据结构
        self.static: Dict[str, Dict[str, Tuple]] = {}  # 静态路由
        self.dyna_routes: Dict[str, List] = {}  # 动态路由
        self.dyna_regexes: Dict[str, List] = {}  # 动态路由正则表达式
        self.strict_order = strict
        
        # 内置过滤器
        self.filters = {
            're': lambda conf: (self._flatten_re(conf or self.DEFAULT_PATTERN), None, None),
            'int': lambda conf: (r'-?\d+', int, lambda x: str(int(x))),
            'float': lambda conf: (r'-?[\d.]+', float, lambda x: str(float(x))),
            'path': lambda conf: (r'.+?', None, None),
        }
    
    def add_filter(self, name: str, func: Callable) -> None:
        """添加自定义过滤器"""
        self.filters[name] = func
    
    def _flatten_re(self, pattern: str) -> str:
        """将正则表达式中的捕获组转换为非捕获组"""
        if '(' not in pattern:
            return pattern
        
        def replace(match):
            if len(match.group(1)) % 2:
                return match.group(0)
            return match.group(1) + '(?:'
        
        return re.sub(r'(\\*)(\(\?P<[^>]+>|\((?!\?))', replace, pattern)
    
    def _iter_tokens(self, rule: str):
        """迭代路由规则中的令牌"""
        offset, prefix = 0, ''
        pattern = re.compile(r'(\\*)(?:(?::([a-zA-Z_][a-zA-Z_0-9]*)?()(?:#(.*?)#)?)|(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)(?::((?:\\\\.|[^\\\\>])+)?)?)?>))')
        
        for match in pattern.finditer(rule):
            prefix += rule[offset:match.start()]
            groups = match.groups()
            
            if len(groups[0]) % 2:  # 转义的通配符
                prefix += match.group(0)[len(groups[0]):]
                offset = match.end()
                continue
            
            if prefix:
                yield prefix, None, None
            
            name, filtr, conf = groups[4:7] if groups[2] is None else groups[1:4]
            yield name, filtr or 'default', conf or None
            offset, prefix = match.end(), ''
        
        if offset <= len(rule) or prefix:
            yield prefix + rule[offset:], None, None
    
    def add(self, rule: str, method: str, target: Any, name: Optional[str] = None) -> None:
        """添加路由规则"""
        anons = 0  # 匿名通配符数量
        keys: List[str] = []  # 参数名列表
        pattern = ''  # 正则表达式模式
        filters: List[Tuple[str, Callable]] = []  # 过滤器列表
        builder: List[Tuple[Optional[str], Any]] = []  # URL 构建器
        is_static = True
        
        for key, mode, conf in self._iter_tokens(rule):
            if mode:
                is_static = False
                if mode == 'default':
                    mode = self.DEFAULT_FILTER
                
                mask, in_filter, out_filter = self.filters[mode](conf)
                
                if not key:
                    pattern += f'(?:{mask})'
                    key = f'anon{anons}'
                    anons += 1
                else:
                    pattern += f'(?P<{key}>{mask})'
                    keys.append(key)
                
                if in_filter:
                    filters.append((key, in_filter))
                builder.append((key, out_filter or str))
            elif key:
                pattern += re.escape(key)
                builder.append((None, key))
        
        self.builder[rule] = builder
        if name:
            self.builder[name] = builder
        
        # 静态路由优化
        if is_static and not self.strict_order:
            self.static.setdefault(method, {})
            self.static[method][self.build(rule)] = (target, None)
            return
        
        # 编译正则表达式
        try:
            re_pattern = re.compile(f'^({pattern})$')
            re_match = re_pattern.match
        except re.error as e:
            raise RouteSyntaxError(f"无效的路由规则: {rule} ({e})")
        
        # 创建参数提取函数
        if filters:
            def getargs(path: str) -> Dict[str, Any]:
                match = re_match(path)
                if not match:
                    return {}
                
                args = match.groupdict()
                for name, wildcard_filter in filters:
                    if name in args:
                        try:
                            # 先对 URL 编码的参数进行解码，添加异常处理
                            try:
                                decoded_value = urllib.parse.unquote(args[name])
                            except Exception:
                                # 如果解码失败，使用原始值
                                decoded_value = args[name]
                            args[name] = wildcard_filter(decoded_value)
                        except ValueError:
                            from .exceptions import HTTPError
                            raise HTTPError(400, '路径格式错误')
                return args
        elif re_pattern.groupindex:
            def getargs(path: str) -> Dict[str, str]:
                match = re_match(path)
                if not match:
                    return {}
                
                args = match.groupdict()
                # 对提取的参数值进行 URL 解码，添加异常处理
                for name in args:
                    try:
                        args[name] = urllib.parse.unquote(args[name])
                    except Exception:
                        # 如果解码失败，保持原始值
                        pass
                return args
        else:
            getargs = None
        
        flatpat = self._flatten_re(pattern)
        whole_rule = (rule, flatpat, target, getargs)
        
        # 检查重复路由
        if (flatpat, method) in self._groups:
            import warnings
            warnings.warn(f'路由 <{method} {rule}> 覆盖了之前定义的路由', RuntimeWarning, stacklevel=3)
            self.dyna_routes[method][self._groups[(flatpat, method)]] = whole_rule
        else:
            self.dyna_routes.setdefault(method, []).append(whole_rule)
            self._groups[(flatpat, method)] = len(self.dyna_routes[method]) - 1
        
        self._compile(method)
    
    def _compile(self, method: str) -> None:
        """编译路由正则表达式"""
        all_rules = self.dyna_routes[method]
        comborules = self.dyna_regexes[method] = []
        
        for x in range(0, len(all_rules), self.MAX_GROUPS_PER_PATTERN):
            some = all_rules[x:x + self.MAX_GROUPS_PER_PATTERN]
            combined = '|'.join(f'(^{flatpat}$)' for _, flatpat, _, _ in some)
            combined_re = re.compile(combined).match
            rules = [(target, getargs) for _, _, target, getargs in some]
            comborules.append((combined_re, rules))
    
    def build(self, route_name: str, *anons: Any, **query: Any) -> str:
        """构建 URL
        
        Args:
            route_name: 路由名称或路由规则
            *anons: 匿名参数（按顺序传递）
            **query: 命名参数和查询参数
            
        Returns:
            构建的 URL 字符串
        """
        builder = self.builder.get(route_name)
        if not builder:
            raise RouteBuildError(f"没有找到名为 {route_name} 的路由", route_name)
        
        try:
            # 创建参数字典的副本，避免修改原始参数
            params = query.copy()
            
            # 处理匿名参数
            for i, value in enumerate(anons):
                param_name = f'anon{i}'
                # 检查是否与命名参数冲突
                if param_name in params:
                    raise RouteBuildError(f'参数名冲突: {param_name} 既作为匿名参数又作为命名参数')
                params[param_name] = value
            
            # 构建 URL
            url_parts = []
            for n, f in builder:
                if n:  # 命名参数
                    if n not in params:
                        raise RouteBuildError(f'缺少 URL 参数: {n}')
                    url_parts.append(f(params[n]))
                else:  # 静态部分
                    url_parts.append(f)
            
            url = ''.join(url_parts)
            
            # 移除已使用的参数
            for n, _ in builder:
                if n:
                    params.pop(n, None)
            
            # 添加查询参数
            if params:
                url += '?' + urlencode(params)
            
            return url
        except KeyError as e:
            raise RouteBuildError(f'缺少 URL 参数: {e.args[0]}')
    
    def match(self, method: str, path: str) -> Tuple[Any, Dict[str, Any]]:
        """匹配路由"""
        method = method.upper()
        
        # 检查静态路由
        if not self.strict_order and method in self.static and path in self.static[method]:
            target, getargs = self.static[method][path]
            return target, getargs(path) if getargs else {}
        
        # 检查动态路由
        if method in self.dyna_regexes:
            for combined, rules in self.dyna_regexes[method]:
                match = combined(path)
                if match:
                    target, getargs = rules[match.lastindex - 1]
                    return target, getargs(path) if getargs else {}
        
        # 检查其他方法
        allowed = set()
        
        # 检查静态路由的其他方法
        for other_method in self.static:
            if other_method != method and path in self.static[other_method]:
                allowed.add(other_method)
        
        # 检查动态路由的其他方法
        for other_method in self.dyna_regexes:
            if other_method != method:
                for combined, _ in self.dyna_regexes[other_method]:
                    if combined(path):
                        allowed.add(other_method)
                        break
        
        if allowed:
            from .exceptions import HTTPError
            allow_header = ','.join(sorted(allowed))
            raise HTTPError(405, "方法不允许", Allow=allow_header)
        
        # 没有找到匹配的路由
        from .exceptions import HTTPError
        raise HTTPError(404, f"未找到: {path}")


class Route:
    """
    路由对象
    
    封装路由回调函数和元数据。
    """
    
    def __init__(
        self,
        app: Any,
        rule: str,
        method: str,
        callback: Callable,
        name: Optional[str] = None,
        plugins: Optional[List] = None,
        skiplist: Optional[List] = None,
        **config,
    ):
        """
        初始化路由对象
        
        Args:
            app: 所属应用
            rule: 路由规则
            method: HTTP 方法
            callback: 回调函数
            name: 路由名称
            plugins: 插件列表
            skiplist: 跳过的插件列表
            **config: 路由配置
        """
        self.app = app
        self.rule = rule
        self.method = method.upper()
        self.callback = callback
        self.name = name
        self.plugins = plugins or []
        self.skiplist = skiplist or []
        self.config = config.copy()
    
    @cached_property
    def call(self) -> Callable:
        """应用插件后的回调函数"""
        return self._make_callback()
    
    def reset(self) -> None:
        """重置缓存"""
        self.__dict__.pop('call', None)
    
    def _make_callback(self) -> Callable:
        """创建应用了插件的回调函数"""
        callback = self.callback
        
        # 应用插件
        for plugin in self._all_plugins():
            if hasattr(plugin, 'apply'):
                callback = plugin.apply(callback, self)
            else:
                callback = plugin(callback)
        
        return callback
    
    def _all_plugins(self):
        """获取所有应用的插件"""
        unique = set()
        
        # 应用全局插件
        for plugin in reversed(self.app.plugins + self.plugins):
            if True in self.skiplist:
                break
            
            name = getattr(plugin, 'name', False)
            if name and (name in self.skiplist or name in unique):
                continue
            
            if plugin in self.skiplist or type(plugin) in self.skiplist:
                continue
            
            if name:
                unique.add(name)
            
            yield plugin
    
    def __repr__(self) -> str:
        callback_name = getattr(self.callback, '__name__', 'unknown')
        module_name = getattr(self.callback, '__module__', 'unknown')
        return f'<Route {self.method} {self.rule} -> {module_name}.{callback_name}>'