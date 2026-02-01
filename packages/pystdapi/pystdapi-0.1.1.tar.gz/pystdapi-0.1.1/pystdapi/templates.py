"""
模板适配器模块

定义模板引擎接口和简单模板实现。
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple


class TemplateError(Exception):
    """模板错误"""
    pass


class TemplateAdapter:
    """
    模板适配器基类
    
    所有模板引擎都应该实现这个接口。
    """
    
    def __init__(self, search_path: str = "./views", **settings):
        """
        初始化模板适配器
        
        Args:
            search_path: 模板搜索路径
            **settings: 模板设置
        """
        self.search_path = search_path
        self.settings = settings
    
    def render(self, template_name: str, **context) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            **context: 模板上下文
        
        Returns:
            渲染后的字符串
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def _find_template(self, template_name: str) -> str:
        """查找模板文件"""
        # 检查模板名称是否包含扩展名
        if not template_name.endswith(self.settings.get('extension', '.html')):
            template_name += self.settings.get('extension', '.html')
        
        # 在搜索路径中查找模板
        search_paths = self.search_path.split(os.pathsep) if isinstance(self.search_path, str) else self.search_path
        
        for path in search_paths:
            template_path = os.path.join(path, template_name)
            if os.path.isfile(template_path):
                return template_path
        
        raise TemplateError(f"Template not found: {template_name}")


class SimpleTemplate(TemplateAdapter):
    """
    简单模板引擎
    
    提供基本的模板功能，支持变量替换、条件判断和循环。
    """
    
    def __init__(self, search_path: str = "./views", **settings):
        super().__init__(search_path, **settings)
        self.cache: Dict[str, str] = {}
        self.cache_enabled = settings.get('cache', True)
    
    def render(self, template_name: str, **context) -> str:
        """渲染模板"""
        # 获取模板内容
        template_content = self._load_template(template_name)
        
        # 渲染模板
        return self._render_template(template_content, context)
    
    def _load_template(self, template_name: str) -> str:
        """加载模板"""
        # 检查缓存
        if self.cache_enabled and template_name in self.cache:
            return self.cache[template_name]
        
        # 查找模板文件
        template_path = self._find_template(template_name)
        
        # 读取模板内容
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            raise TemplateError(f"Cannot read template: {template_path} ({e})")
        
        # 缓存模板
        if self.cache_enabled:
            self.cache[template_name] = content
        
        return content
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染模板内容"""
        # 处理包含指令
        template = self._process_includes(template, context)
        
        # 处理条件语句
        template = self._process_conditionals(template, context)
        
        # 处理循环语句
        template = self._process_loops(template, context)
        
        # 处理变量替换
        template = self._process_variables(template, context)
        
        return template
    
    def _process_includes(self, template: str, context: Dict[str, Any]) -> str:
        """处理包含指令"""
        def replace_include(match):
            include_name = match.group(1).strip()
            try:
                include_content = self._load_template(include_name)
                return self._render_template(include_content, context)
            except TemplateError:
                return f"<!-- Include error: {include_name} -->"
        
        # 匹配 {{ include "template.html" }}
        pattern = r'\{\{\s*include\s+"([^"]+)"\s*\}\}'
        return re.sub(pattern, replace_include, template)
    
    def _process_conditionals(self, template: str, context: Dict[str, Any]) -> str:
        """处理条件语句"""
        # 匹配 {% if condition %} ... {% endif %}
        pattern = r'\{%\s*if\s+([^%]+)\s*%\}(.*?)\{%\s*endif\s*%\}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            content = match.group(2)
            
            # 评估条件
            try:
                # 简单的条件评估
                if condition in context and context[condition]:
                    return content
                elif condition.startswith('not ') and condition[4:] in context and not context[condition[4:]]:
                    return content
                elif '==' in condition:
                    var, value = condition.split('==', 1)
                    var = var.strip()
                    value = value.strip().strip('"\'')
                    if var in context and str(context[var]) == value:
                        return content
                elif '!=' in condition:
                    var, value = condition.split('!=', 1)
                    var = var.strip()
                    value = value.strip().strip('"\'')
                    if var in context and str(context[var]) != value:
                        return content
            except Exception:
                pass
            
            return ''
        
        return re.sub(pattern, replace_if, template, flags=re.DOTALL)
    
    def _process_loops(self, template: str, context: Dict[str, Any]) -> str:
        """处理循环语句"""
        # 匹配 {% for item in items %} ... {% endfor %}
        pattern = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
        
        def replace_for(match):
            item_name = match.group(1)
            collection_name = match.group(2)
            content = match.group(3)
            
            if collection_name not in context:
                return ''
            
            collection = context[collection_name]
            if not isinstance(collection, (list, tuple, dict)):
                return ''
            
            result = []
            if isinstance(collection, dict):
                for key, value in collection.items():
                    loop_context = context.copy()
                    loop_context[item_name] = {'key': key, 'value': value}
                    result.append(self._render_template(content, loop_context))
            else:
                for i, item in enumerate(collection):
                    loop_context = context.copy()
                    loop_context[item_name] = item
                    loop_context['loop_index'] = i
                    loop_context['loop_index0'] = i
                    loop_context['loop_first'] = (i == 0)
                    loop_context['loop_last'] = (i == len(collection) - 1)
                    result.append(self._render_template(content, loop_context))
            
            return ''.join(result)
        
        return re.sub(pattern, replace_for, template, flags=re.DOTALL)
    
    def _process_variables(self, template: str, context: Dict[str, Any]) -> str:
        """处理变量替换"""
        def replace_variable(match):
            var_name = match.group(1).strip()
            
            # 支持点号访问嵌套属性
            parts = var_name.split('.')
            value = context
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return ''
            
            # 转义 HTML 特殊字符
            from .utils import html_escape
            return html_escape(str(value))
        
        # 匹配 {{ variable }}
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        return re.sub(pattern, replace_variable, template)


class StringTemplate(TemplateAdapter):
    """
    字符串模板引擎
    
    直接在字符串中渲染模板，不依赖文件系统。
    """
    
    def __init__(self, **settings):
        super().__init__("", **settings)
        self.engine = SimpleTemplate(**settings)
    
    def render(self, template_string: str, **context) -> str:
        """渲染模板字符串"""
        return self.engine._render_template(template_string, context)


# 模板工厂函数
def get_template_adapter(name: str = 'simple', **settings) -> TemplateAdapter:
    """获取模板适配器"""
    adapters = {
        'simple': SimpleTemplate,
        'string': StringTemplate,
    }
    
    adapter_class = adapters.get(name.lower())
    if not adapter_class:
        raise ValueError(f"Unknown template adapter: {name}")
    
    return adapter_class(**settings)


# 快捷函数
def render_template(template_name: str, **context) -> str:
    """渲染模板（使用默认适配器）"""
    adapter = SimpleTemplate()
    return adapter.render(template_name, **context)


def render_string(template_string: str, **context) -> str:
    """渲染模板字符串"""
    adapter = StringTemplate()
    return adapter.render(template_string, **context)