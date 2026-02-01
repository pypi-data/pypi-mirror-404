"""
插件系统模块

定义插件基类和常用插件，用于扩展框架功能。
"""

import json
from typing import Any, Callable, Dict, Optional
from .exceptions import PluginError


class Plugin:
    """
    插件基类
    
    所有插件都应该继承这个类。
    """
    
    name = 'plugin'
    api = 2
    
    def __init__(self, **kwargs):
        """
        初始化插件
        
        Args:
            **kwargs: 插件配置
        """
        self.config = kwargs
    
    def setup(self, app):
        """设置插件"""
        pass
    
    def apply(self, callback, route):
        """应用插件到路由"""
        return callback
    
    def close(self):
        """关闭插件"""
        pass
    
    def __repr__(self):
        return f"<Plugin {self.name}>"


class JSONPlugin(Plugin):
    """
    JSON 插件
    
    自动解析 JSON 请求体和序列化 JSON 响应。
    """
    
    name = 'json'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encoding = kwargs.get('encoding', 'utf-8')
        self.dumps_kwargs = kwargs.get('dumps_kwargs', {})
        self.loads_kwargs = kwargs.get('loads_kwargs', {})
    
    def apply(self, callback, route):
        """应用 JSON 插件"""
        import inspect
        
        if inspect.iscoroutinefunction(callback):
            async def async_wrapper(request, *args, **kwargs):
                # 解析 JSON 请求体
                if request.is_json:
                    try:
                        data = await request.json()
                        if isinstance(data, dict):
                            kwargs.update(data)
                    except (ValueError, json.JSONDecodeError):
                        from .exceptions import HTTPError
                        raise HTTPError(400, 'Invalid JSON')
                
                # 调用原始回调
                result = await callback(request, *args, **kwargs)
                
                # 序列化 JSON 响应
                if isinstance(result, (dict, list)):
                    from .responses import json_response
                    return json_response(result)
                
                return result
            
            return async_wrapper
        else:
            def sync_wrapper(request, *args, **kwargs):
                # 解析 JSON 请求体
                if request.is_json:
                    try:
                        data = request.json()
                        if isinstance(data, dict):
                            kwargs.update(data)
                    except (ValueError, json.JSONDecodeError):
                        from .exceptions import HTTPError
                        raise HTTPError(400, 'Invalid JSON')
                
                # 调用原始回调
                result = callback(request, *args, **kwargs)
                
                # 序列化 JSON 响应
                if isinstance(result, (dict, list)):
                    from .responses import json_response
                    return json_response(result)
                
                return result
            
            return sync_wrapper


class TemplatePlugin(Plugin):
    """
    模板插件
    
    提供模板渲染功能。
    """
    
    name = 'template'
    
    def __init__(self, template_adapter=None, **kwargs):
        super().__init__(**kwargs)
        self.template_adapter = template_adapter
        self.template_settings = kwargs
    
    def setup(self, app):
        """设置模板插件"""
        if self.template_adapter is None:
            # 尝试自动导入模板适配器
            try:
                from .templates import SimpleTemplate
                self.template_adapter = SimpleTemplate
            except ImportError:
                raise PluginError("No template adapter available")
        
        app.template_adapter = self.template_adapter
        app.template_settings = self.template_settings
    
    def apply(self, callback, route):
        """应用模板插件"""
        import inspect
        
        if inspect.iscoroutinefunction(callback):
            async def async_wrapper(request, *args, **kwargs):
                # 调用原始回调
                result = await callback(request, *args, **kwargs)
                
                # 如果是字典，尝试渲染模板
                if isinstance(result, dict) and 'template' in result:
                    template_name = result.pop('template')
                    template_vars = result
                    
                    # 创建模板适配器实例
                    adapter_class = self.template_adapter
                    template_instance = adapter_class(
                        **self.template_settings
                    )
                    
                    # 渲染模板
                    rendered = template_instance.render(template_name, **template_vars)
                    
                    from .responses import html_response
                    return html_response(rendered)
                
                return result
            
            return async_wrapper
        else:
            def sync_wrapper(request, *args, **kwargs):
                # 调用原始回调
                result = callback(request, *args, **kwargs)
                
                # 如果是字典，尝试渲染模板
                if isinstance(result, dict) and 'template' in result:
                    template_name = result.pop('template')
                    template_vars = result
                    
                    # 创建模板适配器实例
                    adapter_class = self.template_adapter
                    template_instance = adapter_class(
                        **self.template_settings
                    )
                    
                    # 渲染模板
                    rendered = template_instance.render(template_name, **template_vars)
                    
                    from .responses import html_response
                    return html_response(rendered)
                
                return result
            
            return sync_wrapper


class SessionPlugin(Plugin):
    """
    会话插件
    
    提供会话管理功能。
    """
    
    name = 'session'
    
    def __init__(self, secret=None, **kwargs):
        super().__init__(**kwargs)
        self.secret = secret
        self.cookie_name = kwargs.get('cookie_name', 'session')
        self.max_age = kwargs.get('max_age', 86400)  # 24小时
        self.secure = kwargs.get('secure', False)
        self.httponly = kwargs.get('httponly', True)
    
    def setup(self, app):
        """设置会话插件"""
        if not self.secret:
            raise PluginError("Session secret is required")
        
        app.session_secret = self.secret
        app.session_config = {
            'cookie_name': self.cookie_name,
            'max_age': self.max_age,
            'secure': self.secure,
            'httponly': self.httponly,
        }
    
    def apply(self, callback, route):
        """应用会话插件"""
        def wrapper(request, *args, **kwargs):
            # 获取会话 ID
            session_id = request.get_cookie(self.cookie_name)
            
            # 创建或加载会话
            session = self._load_session(session_id)
            request.session = session
            
            # 调用原始回调
            result = callback(request, *args, **kwargs)
            
            # 保存会话
            if hasattr(request, 'session') and request.session:
                new_session_id = self._save_session(request.session)
                
                # 设置会话 Cookie
                if isinstance(result, tuple):
                    result, response = result
                else:
                    from .responses import Response
                    response = Response(result) if not isinstance(result, Response) else result
                
                response.set_cookie(
                    self.cookie_name,
                    new_session_id,
                    max_age=self.max_age,
                    secure=self.secure,
                    httponly=self.httponly,
                )
                
                return response
            
            return result
        
        return wrapper
    
    def _load_session(self, session_id):
        """加载会话"""
        # TODO: 实现会话加载逻辑
        return {}
    
    def _save_session(self, session):
        """保存会话"""
        # TODO: 实现会话保存逻辑
        return 'new_session_id'


class AuthPlugin(Plugin):
    """
    认证插件
    
    提供用户认证和授权功能。
    """
    
    name = 'auth'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_model = kwargs.get('user_model')
        self.login_url = kwargs.get('login_url', '/login')
        self.login_redirect = kwargs.get('login_redirect', '/')
    
    def setup(self, app):
        """设置认证插件"""
        app.auth_plugin = self
    
    def apply(self, callback, route):
        """应用认证插件"""
        # 检查路由是否需要认证
        if route.config.get('auth_required', False):
            def wrapper(request, *args, **kwargs):
                # 检查用户是否已认证
                if not self.is_authenticated(request):
                    from .responses import redirect_response
                    return redirect_response(self.login_url)
                
                # 获取当前用户
                request.user = self.get_current_user(request)
                
                # 调用原始回调
                return callback(request, *args, **kwargs)
            
            return wrapper
        
        return callback
    
    def is_authenticated(self, request):
        """检查用户是否已认证"""
        # TODO: 实现认证检查逻辑
        return False
    
    def get_current_user(self, request):
        """获取当前用户"""
        # TODO: 实现用户获取逻辑
        return None
    
    def login_user(self, request, user):
        """用户登录"""
        # TODO: 实现用户登录逻辑
        pass
    
    def logout_user(self, request):
        """用户登出"""
        # TODO: 实现用户登出逻辑
        pass


class CORSPlugin(Plugin):
    """
    CORS 插件
    
    提供跨域资源共享支持。
    """
    
    name = 'cors'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_origins = kwargs.get('allow_origins', ['*'])
        self.allow_methods = kwargs.get('allow_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        self.allow_headers = kwargs.get('allow_headers', ['*'])
        self.allow_credentials = kwargs.get('allow_credentials', False)
        self.max_age = kwargs.get('max_age', 600)
    
    def apply(self, callback, route):
        """应用 CORS 插件"""
        import inspect
        
        if inspect.iscoroutinefunction(callback):
            async def async_wrapper(request, *args, **kwargs):
                # 处理 OPTIONS 预检请求
                if request.method == 'OPTIONS':
                    from .responses import Response
                    response = Response(status=204)
                    
                    # 添加 CORS 头部
                    origin = request.get_header('Origin')
                    if origin and (origin in self.allow_origins or '*' in self.allow_origins):
                        response.set_header('Access-Control-Allow-Origin', origin)
                        response.set_header('Access-Control-Allow-Methods', ', '.join(self.allow_methods))
                        response.set_header('Access-Control-Allow-Headers', ', '.join(self.allow_headers))
                        response.set_header('Access-Control-Max-Age', str(self.max_age))
                        
                        if self.allow_credentials:
                            response.set_header('Access-Control-Allow-Credentials', 'true')
                    
                    return response
                
                # 调用原始回调
                result = await callback(request, *args, **kwargs)
                
                # 添加 CORS 头部到响应
                if isinstance(result, tuple):
                    result, response = result
                else:
                    from .responses import Response
                    response = Response(result) if not isinstance(result, Response) else result
                
                origin = request.get_header('Origin')
                if origin and (origin in self.allow_origins or '*' in self.allow_origins):
                    response.set_header('Access-Control-Allow-Origin', origin)
                    
                    if self.allow_credentials:
                        response.set_header('Access-Control-Allow-Credentials', 'true')
                
                return response
            
            return async_wrapper
        else:
            def sync_wrapper(request, *args, **kwargs):
                # 处理 OPTIONS 预检请求
                if request.method == 'OPTIONS':
                    from .responses import Response
                    response = Response(status=204)
                    
                    # 添加 CORS 头部
                    origin = request.get_header('Origin')
                    if origin and (origin in self.allow_origins or '*' in self.allow_origins):
                        response.set_header('Access-Control-Allow-Origin', origin)
                        response.set_header('Access-Control-Allow-Methods', ', '.join(self.allow_methods))
                        response.set_header('Access-Control-Allow-Headers', ', '.join(self.allow_headers))
                        response.set_header('Access-Control-Max-Age', str(self.max_age))
                        
                        if self.allow_credentials:
                            response.set_header('Access-Control-Allow-Credentials', 'true')
                    
                    return response
                
                # 调用原始回调
                result = callback(request, *args, **kwargs)
                
                # 添加 CORS 头部到响应
                if isinstance(result, tuple):
                    result, response = result
                else:
                    from .responses import Response
                    response = Response(result) if not isinstance(result, Response) else result
                
                origin = request.get_header('Origin')
                if origin and (origin in self.allow_origins or '*' in self.allow_origins):
                    response.set_header('Access-Control-Allow-Origin', origin)
                    
                    if self.allow_credentials:
                        response.set_header('Access-Control-Allow-Credentials', 'true')
                
                return response
            
            return sync_wrapper


# 插件工厂函数
def install_plugin(app, plugin_class, **kwargs):
    """安装插件"""
    plugin = plugin_class(**kwargs)
    plugin.setup(app)
    app.add_plugin(plugin)
    return plugin


# 常用插件快捷方式
def json_plugin(**kwargs):
    """创建 JSON 插件"""
    return JSONPlugin(**kwargs)


def template_plugin(template_adapter=None, **kwargs):
    """创建模板插件"""
    return TemplatePlugin(template_adapter, **kwargs)


def session_plugin(secret, **kwargs):
    """创建会话插件"""
    return SessionPlugin(secret, **kwargs)


def auth_plugin(**kwargs):
    """创建认证插件"""
    return AuthPlugin(**kwargs)


def cors_plugin(**kwargs):
    """创建 CORS 插件"""
    return CORSPlugin(**kwargs)