#!/usr/bin/env python3
"""
PystdAPI 命令行工具

提供创建项目、运行服务器等命令行功能。
"""

import argparse
import os
import sys
import shutil
from pathlib import Path


def create_project(project_name: str, template: str = "basic"):
    """创建新项目"""
    print(f"创建项目: {project_name}")
    
    # 创建项目目录
    project_dir = Path(project_name)
    if project_dir.exists():
        print(f"错误: 目录 '{project_name}' 已存在")
        return False
    
    project_dir.mkdir(parents=True)
    
    # 根据模板创建文件
    if template == "basic":
        create_basic_project(project_dir)
    elif template == "api":
        create_api_project(project_dir)
    elif template == "full":
        create_full_project(project_dir)
    else:
        print(f"错误: 未知模板 '{template}'")
        return False
    
    print(f"项目创建成功: {project_dir.absolute()}")
    print(f"进入项目目录: cd {project_name}")
    print(f"运行项目: python app.py")
    
    return True


def create_basic_project(project_dir: Path):
    """创建基础项目"""
    # 创建 app.py
    app_content = '''#!/usr/bin/env python3
"""
PystdAPI 基础项目
"""

from pystdapi import PystdAPI

app = PystdAPI(name="myapp", debug=True)

@app.get("/")
async def index(request):
    return {"message": "Hello, PystdAPI!"}

@app.get("/hello/<name>")
async def hello(request, name):
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    print("启动服务器: http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000)
'''
    
    (project_dir / "app.py").write_text(app_content, encoding="utf-8")
    
    # 创建 requirements.txt
    requirements = '''# PystdAPI 项目依赖
# 由于 PystdAPI 仅依赖 Python 标准库，这里不需要额外依赖
# 如果你需要其他功能，可以在这里添加
'''
    
    (project_dir / "requirements.txt").write_text(requirements, encoding="utf-8")
    
    # 创建 README.md
    readme = f'''# {project_dir.name}

基于 PystdAPI 框架的 Web 应用。

## 快速开始

1. 安装 Python 3.7+
2. 复制 pystdapi 目录到项目
3. 运行应用: `python app.py`

## 项目结构

```
{project_dir.name}/
├── app.py          # 主应用文件
├── requirements.txt # 依赖文件
└── README.md       # 项目说明
```

## 开发

启动开发服务器:
```bash
python app.py
```

访问 http://127.0.0.1:8000 查看应用。
'''
    
    (project_dir / "README.md").write_text(readme, encoding="utf-8")


def create_api_project(project_dir: Path):
    """创建 API 项目"""
    create_basic_project(project_dir)
    
    # 创建 api 目录
    api_dir = project_dir / "api"
    api_dir.mkdir()
    
    # 创建 __init__.py
    (api_dir / "__init__.py").write_text("# API 模块\n", encoding="utf-8")
    
    # 创建 users.py
    users_content = '''"""
用户 API
"""

from pystdapi import PystdAPI

app = PystdAPI()

# 模拟用户数据
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
}

@app.get("/api/users")
async def get_users(request):
    """获取用户列表"""
    return {"users": list(users_db.values())}

@app.get("/api/users/<user_id:int>")
async def get_user(request, user_id):
    """获取单个用户"""
    if user_id in users_db:
        return {"user": users_db[user_id]}
    else:
        return {"error": "User not found"}, 404

@app.post("/api/users")
async def create_user(request):
    """创建用户"""
    data = await request.json()
    
    # 生成新用户 ID
    new_id = max(users_db.keys()) + 1 if users_db else 1
    
    user = {
        "id": new_id,
        "name": data.get("name", ""),
        "email": data.get("email", ""),
    }
    
    users_db[new_id] = user
    
    return {"message": "User created", "user": user}, 201

@app.put("/api/users/<user_id:int>")
async def update_user(request, user_id):
    """更新用户"""
    if user_id not in users_db:
        return {"error": "User not found"}, 404
    
    data = await request.json()
    
    # 更新用户信息
    users_db[user_id].update({
        "name": data.get("name", users_db[user_id]["name"]),
        "email": data.get("email", users_db[user_id]["email"]),
    })
    
    return {"message": "User updated", "user": users_db[user_id]}

@app.delete("/api/users/<user_id:int>")
async def delete_user(request, user_id):
    """删除用户"""
    if user_id not in users_db:
        return {"error": "User not found"}, 404
    
    deleted_user = users_db.pop(user_id)
    
    return {"message": "User deleted", "user": deleted_user}
'''
    
    (api_dir / "users.py").write_text(users_content, encoding="utf-8")
    
    # 更新 app.py
    app_content = '''#!/usr/bin/env python3
"""
PystdAPI API 项目
"""

from pystdapi import PystdAPI
from pystdapi.middleware import cors_middleware
from pystdapi.plugins import json_plugin

# 导入 API 模块
from api import users

app = PystdAPI(name="api_project", debug=True)

# 添加中间件和插件
app.add_middleware(cors_middleware(allow_origins=["*"]))
app.add_plugin(json_plugin())

# 挂载 API 路由
app.mount("/", users.app)

@app.get("/")
async def index(request):
    return {
        "message": "PystdAPI API 项目",
        "endpoints": [
            "/api/users",
            "/api/users/<id>",
        ],
        "methods": {
            "/api/users": ["GET", "POST"],
            "/api/users/<id>": ["GET", "PUT", "DELETE"],
        }
    }

if __name__ == "__main__":
    print("启动 API 服务器: http://127.0.0.1:8000")
    print("API 文档: http://127.0.0.1:8000/")
    app.run(host="127.0.0.1", port=8000)
'''
    
    (project_dir / "app.py").write_text(app_content, encoding="utf-8")


def create_full_project(project_dir: Path):
    """创建完整项目"""
    create_api_project(project_dir)
    
    # 创建 templates 目录
    templates_dir = project_dir / "templates"
    templates_dir.mkdir()
    
    # 创建基础模板
    base_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav>
        <a href="/">首页</a>
        <a href="/about">关于</a>
        <a href="/api/users">用户API</a>
    </nav>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2023 PystdAPI 项目</p>
    </footer>
</body>
</html>
'''
    
    (templates_dir / "base.html").write_text(base_template, encoding="utf-8")
    
    # 创建首页模板
    index_template = '''{% extends "base.html" %}

{% block content %}
<div class="hero">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
</div>

<div class="features">
    <div class="feature">
        <h3>异步高性能</h3>
        <p>基于 Python asyncio，支持高并发</p>
    </div>
    <div class="feature">
        <h3>零依赖</h3>
        <p>仅使用 Python 标准库</p>
    </div>
    <div class="feature">
        <h3>模块化设计</h3>
        <p>清晰的架构，易于扩展</p>
    </div>
</div>
{% endblock %}
'''
    
    (templates_dir / "index.html").write_text(index_template, encoding="utf-8")
    
    # 创建静态文件目录
    static_dir = project_dir / "static"
    static_dir.mkdir()
    
    css_dir = static_dir / "css"
    css_dir.mkdir()
    
    # 创建 CSS 文件
    css_content = '''/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

nav {
    background-color: #4CAF50;
    padding: 1rem;
    display: flex;
    gap: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

nav a:hover {
    background-color: #45a049;
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.hero {
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 3rem;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.hero p {
    font-size: 1.2rem;
    opacity: 0.9;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.feature {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.feature:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.feature h3 {
    color: #4CAF50;
    margin-bottom: 1rem;
    font-size: 1.5rem;
}

footer {
    text-align: center;
    padding: 2rem;
    background-color: #333;
    color: white;
    margin-top: 3rem;
}
'''
    
    (css_dir / "style.css").write_text(css_content, encoding="utf-8")
    
    # 更新 app.py 添加模板支持
    app_content = (project_dir / "app.py").read_text(encoding="utf-8")
    
    # 添加模板相关导入和路由
    new_content = app_content.replace(
        'from pystdapi.plugins import json_plugin',
        '''from pystdapi.plugins import json_plugin, template_plugin
from pystdapi.templates import SimpleTemplate'''
    ).replace(
        'app.add_plugin(json_plugin())',
        '''app.add_plugin(json_plugin())
app.add_plugin(template_plugin(
    template_adapter=SimpleTemplate,
    search_path="./templates",
    cache=True
))'''
    ).replace(
        '@app.get("/")',
        '''@app.get("/")
async def index(request):
    return {
        "template": "index.html",
        "title": "欢迎使用 PystdAPI",
        "message": "一个纯异步的 Python Web 框架"
    }

@app.get("/about")
async def about(request):
    return {
        "template": "base.html",
        "title": "关于我们",
        "content": "<h2>关于 PystdAPI</h2><p>这是一个基于 ASGI 标准的高性能异步 Web 框架。</p>"
    }

@app.get("/static/<path:path>")
async def static_file(request, path):
    """静态文件服务"""
    import os
    from pystdapi.responses import Response
    
    safe_path = os.path.join(".", "static", path)
    safe_path = os.path.normpath(safe_path)
    
    if not safe_path.startswith(os.path.abspath(".")):
        return {"error": "Access denied"}, 403
    
    if os.path.isfile(safe_path):
        with open(safe_path, "rb") as f:
            content = f.read()
        
        import mimetypes
        content_type, _ = mimetypes.guess_type(safe_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        return Response(content, content_type=content_type)
    else:
        return {"error": "File not found"}, 404

# 原来的路由'''
    )
    
    (project_dir / "app.py").write_text(new_content, encoding="utf-8")


def run_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = False, reload: bool = False):
    """运行开发服务器"""
    print(f"启动服务器: http://{host}:{port}")
    
    # 这里应该导入并运行用户的应用
    # 由于这是一个通用工具，我们假设用户有一个 app.py 文件
    import subprocess
    import sys
    
    cmd = [sys.executable, "app.py"]
    
    if debug:
        cmd.append("--debug")
    
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("错误: 未找到 app.py 文件")
        print("请确保在当前目录运行，或先创建一个项目")
        return False
    except KeyboardInterrupt:
        print("\n服务器已停止")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PystdAPI 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s new myproject          # 创建新项目
  %(prog)s new myapi --template api  # 创建 API 项目
  %(prog)s run                    # 运行开发服务器
  %(prog)s run --port 8080       # 在指定端口运行
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # new 命令
    new_parser = subparsers.add_parser("new", help="创建新项目")
    new_parser.add_argument("name", help="项目名称")
    new_parser.add_argument("--template", choices=["basic", "api", "full"], 
                          default="basic", help="项目模板")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行开发服务器")
    run_parser.add_argument("--host", default="127.0.0.1", help="主机地址")
    run_parser.add_argument("--port", type=int, default=8000, help="端口号")
    run_parser.add_argument("--debug", action="store_true", help="调试模式")
    run_parser.add_argument("--reload", action="store_true", help="热重载")
    
    # version 命令
    subparsers.add_parser("version", help="显示版本信息")
    
    args = parser.parse_args()
    
    if args.command == "new":
        create_project(args.name, args.template)
    elif args.command == "run":
        run_server(args.host, args.port, args.debug, args.reload)
    elif args.command == "version":
        from pystdapi import __version__
        print(f"PystdAPI {__version__}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()