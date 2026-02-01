"""
服务器适配器模块

定义各种服务器适配器，用于运行 ASGI 应用。
"""

import asyncio
import socket
import sys
from typing import Any, Callable, Dict, Optional


class ServerAdapter:
    """
    服务器适配器基类
    
    所有服务器适配器都应该继承这个类。
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8000, **options):
        """
        初始化服务器适配器
        
        Args:
            host: 主机地址
            port: 端口号
            **options: 其他选项
        """
        self.host = host
        self.port = port
        self.options = options
    
    def run(self, handler: Callable) -> None:
        """运行服务器"""
        raise NotImplementedError("子类必须实现此方法")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(host={self.host!r}, port={self.port!r})"


class ASGIServer(ServerAdapter):
    """
    ASGI 服务器适配器
    
    使用标准库的 asyncio 运行 ASGI 应用。
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8000, **options):
        super().__init__(host, port, **options)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def run(self, app: Callable) -> None:
        """运行 ASGI 应用"""
        import asyncio
        import sys
        
        # HTTP 协议适配器：将 (reader, writer) 转换为 ASGI 接口
        async def handle_http(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            """处理 HTTP 请求"""
            import time
            import urllib.parse
            start_time = time.time()
            client_addr = writer.get_extra_info('peername')
            client_ip = client_addr[0] if client_addr else 'unknown'
            client_port = client_addr[1] if client_addr else 0
            
            try:
                # 读取请求行
                request_line = await reader.readline()
                if not request_line:
                    return
                
                # 解析请求行: METHOD PATH HTTP/VERSION
                request_line_str = request_line.decode('latin-1').strip()
                if not request_line_str:
                    return
                
                parts = request_line_str.split()
                if len(parts) != 3:
                    # 无效的请求行
                    writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
                    await writer.drain()
                    writer.close()
                    return
                
                method, raw_path, http_version = parts
                
                # 对路径进行 URL 解码
                decoded_path = urllib.parse.unquote(raw_path)
                
                # 打印访问日志（请求开始）
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {client_ip}:{client_port} - \"{method} {decoded_path} {http_version}\"", end='')
                
                # 读取请求头
                headers = []
                while True:
                    header_line = await reader.readline()
                    if not header_line:
                        break
                    
                    header_line_str = header_line.decode('latin-1').strip()
                    if not header_line_str:
                        break  # 空行表示头部结束
                    
                    if ':' in header_line_str:
                        key, value = header_line_str.split(':', 1)
                        headers.append((key.strip().encode('latin-1'), value.strip().encode('latin-1')))
                
                # 构建 ASGI scope
                scope = {
                    'type': 'http',
                    'asgi': {'version': '3.0', 'spec_version': '2.1'},
                    'http_version': http_version.split('/')[1] if '/' in http_version else '1.1',
                    'method': method,
                    'scheme': 'http',
                    'path': decoded_path,
                    'raw_path': raw_path.encode('latin-1'),
                    'query_string': b'',  # 简化处理，不解析查询参数
                    'headers': headers,
                    'client': writer.get_extra_info('peername'),
                    'server': (self.host, self.port),
                }
                
                # 创建 receive 函数
                body_buffer = b''
                more_body = True
                
                async def receive():
                    nonlocal body_buffer, more_body
                    if more_body:
                        # 读取请求体（简化处理，读取所有可用数据）
                        try:
                            body = await reader.read(8192)
                            more_body = False  # 简化：假设一次读完
                            return {
                                'type': 'http.request',
                                'body': body,
                                'more_body': False,
                            }
                        except Exception:
                            more_body = False
                            return {
                                'type': 'http.request',
                                'body': b'',
                                'more_body': False,
                            }
                    else:
                        # 没有更多数据
                        return {
                            'type': 'http.disconnect',
                        }
                
                # 创建 send 函数
                response_started = False
                
                async def send(message):
                    nonlocal response_started
                    
                    if message['type'] == 'http.response.start':
                        # 发送响应头
                        status = message.get('status', 200)
                        headers = message.get('headers', [])
                        
                        response_line = f'HTTP/1.1 {status} OK\r\n'.encode('latin-1')
                        writer.write(response_line)
                        
                        for key, value in headers:
                            header_line = f'{key.decode("latin-1")}: {value.decode("latin-1")}\r\n'.encode('latin-1')
                            writer.write(header_line)
                        
                        writer.write(b'\r\n')
                        response_started = True
                        
                    elif message['type'] == 'http.response.body':
                        # 发送响应体
                        body = message.get('body', b'')
                        if body:
                            writer.write(body)
                        
                        # 检查是否结束
                        if not message.get('more_body', False):
                            await writer.drain()
                            writer.close()
                
                # 调用 ASGI 应用
                await app(scope, receive, send)
                
                # 记录响应完成
                end_time = time.time()
                duration = end_time - start_time
                print(f" - {duration:.3f}s")
                
            except Exception as e:
                # 错误处理
                end_time = time.time()
                duration = end_time - start_time
                print(f" - 500 Error - {duration:.3f}s")
                
                if not writer.is_closing():
                    try:
                        writer.write(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
                        await writer.drain()
                    except:
                        pass
                writer.close()
        
        # 创建服务器
        async def start_server():
            # Windows 不支持 reuse_port 参数
            server_kwargs = {
                'host': self.host,
                'port': self.port,
                'reuse_address': True,
            }
            if sys.platform != 'win32':
                server_kwargs['reuse_port'] = True
                
            return await asyncio.start_server(handle_http, **server_kwargs)
        
        server = None
        # 运行服务器
        try:
            server = self.loop.run_until_complete(start_server())
            
            # 获取实际绑定的地址和端口
            for sock in server.sockets:
                if sock.family == socket.AF_INET:
                    addr, port = sock.getsockname()
                    print(f"Server started on http://{addr}:{port}")
            
            # 设置信号处理（Windows 不支持）
            if sys.platform != 'win32':
                import signal
                for sig in (signal.SIGINT, signal.SIGTERM):
                    self.loop.add_signal_handler(sig, self.loop.stop)
            
            # 运行事件循环
            self.loop.run_forever()
            
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Server error: {e}")
            raise
        finally:
            if server:
                server.close()
                self.loop.run_until_complete(server.wait_closed())
            self.loop.close()


class AutoServer(ServerAdapter):
    """
    自动选择服务器适配器
    
    根据环境自动选择最佳服务器。
    """
    
    def run(self, app: Callable) -> None:
        """运行应用"""
        # 使用 ASGI 服务器
        server = ASGIServer(self.host, self.port, **self.options)
        server.run(app)


class DevelopmentServer(ServerAdapter):
    """
    开发服务器
    
    提供热重载和调试功能。
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8000, reload: bool = False, **options):
        super().__init__(host, port, **options)
        self.reload = reload
    
    def run(self, app: Callable) -> None:
        """运行开发服务器"""
        if self.reload:
            # 使用热重载
            self._run_with_reload(app)
        else:
            # 普通运行
            server = ASGIServer(self.host, self.port, **self.options)
            server.run(app)
    
    def _run_with_reload(self, app: Callable) -> None:
        """带热重载的运行（使用子进程）"""
        import os
        import sys
        import time
        import subprocess
        import threading
        import signal
        
        # 获取当前文件路径，用于重新加载
        # 注意：这里需要获取主脚本的路径，而不是server.py的路径
        # 我们通过sys.argv[0]获取主脚本路径
        if len(sys.argv) > 0 and sys.argv[0].endswith('.py'):
            current_file = os.path.abspath(sys.argv[0])
        else:
            # 如果没有主脚本，使用当前目录
            current_file = os.path.abspath('.')
        
        server_process = None
        log_thread = None
        stop_log_event = threading.Event()
        
        def start_server():
            """启动服务器子进程"""
            nonlocal server_process, log_thread, stop_log_event
            
            # 重置停止事件
            stop_log_event.clear()
            
            # 构建启动命令 - 运行当前脚本
            # 不再传递--no-reload参数，而是通过环境变量控制
            cmd = [sys.executable, current_file]
            
            # 设置环境变量，告诉子进程不要启用热加载
            env = os.environ.copy()
            env['PYSTDAPI_NO_RELOAD'] = '1'
            
            # 启动子进程
            try:
                server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    env=env
                )
                
                # 检查进程是否成功启动
                time.sleep(0.5)  # 给进程一点启动时间
                if server_process.poll() is not None:
                    # 进程已退出，读取错误信息
                    output = server_process.stdout.read() if server_process.stdout else ""
                    print(f"[热加载] 服务器启动失败: {output}")
                    server_process = None
                    return None
                
                print(f"[热加载] 服务器进程已启动 (PID: {server_process.pid})")
                
            except Exception as e:
                print(f"[热加载] 启动服务器时出错: {e}")
                server_process = None
                return None
            
            # 实时输出子进程日志
            def log_output():
                while not stop_log_event.is_set() and server_process is not None:
                    try:
                        # 使用非阻塞方式读取输出
                        if server_process.stdout:
                            line = server_process.stdout.readline()
                            if not line and server_process.poll() is not None:
                                break
                            if line:
                                print(f"[Server] {line}", end='')
                        else:
                            time.sleep(0.1)
                    except (AttributeError, ValueError, OSError):
                        break
            
            # 创建并启动日志线程
            log_thread = threading.Thread(target=log_output, daemon=True)
            log_thread.start()
            
            return server_process
        
        def stop_server():
            """停止服务器子进程"""
            nonlocal server_process, log_thread, stop_log_event
            
            # 设置停止事件，通知日志线程停止
            stop_log_event.set()
            
            # 等待日志线程结束（最多1秒）
            if log_thread and log_thread.is_alive():
                log_thread.join(timeout=1)
            
            # 停止服务器进程
            if server_process and server_process.poll() is None:
                try:
                    # 尝试优雅终止
                    if sys.platform == 'win32':
                        # Windows使用terminate
                        server_process.terminate()
                    else:
                        # Unix系统使用SIGTERM
                        os.kill(server_process.pid, signal.SIGTERM)
                    
                    # 等待进程结束
                    server_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        # 强制终止
                        if sys.platform == 'win32':
                            server_process.kill()
                        else:
                            os.kill(server_process.pid, signal.SIGKILL)
                        server_process.wait(timeout=1)
                    except:
                        pass
                except (OSError, ProcessLookupError):
                    # 进程可能已经结束
                    pass
                finally:
                    server_process = None
        
        # 优化文件监控 - 参考FastAPI/Flask的做法
        def collect_files():
            """收集需要监控的文件 - 只监控项目相关文件"""
            files = set()
            
            # 1. 首先添加主文件
            if current_file.endswith('.py'):
                files.add(current_file)
            
            # 2. 获取主文件所在目录
            main_dir = os.path.dirname(current_file)
            
            # 3. 只监控主文件目录及其子目录中的.py文件
            for root, dirs, filenames in os.walk(main_dir):
                # 排除常见非源码目录
                dirs[:] = [d for d in dirs if not should_exclude_dir(d)]
                
                for filename in filenames:
                    if filename.endswith('.py'):
                        files.add(os.path.abspath(os.path.join(root, filename)))
            
            # 4. 排除标准库和框架目录（如果它们在监控范围内）
            filtered_files = set()
            for filepath in files:
                if not should_exclude_file(filepath):
                    filtered_files.add(filepath)
            
            return filtered_files
        
        def should_exclude_dir(dirname):
            """检查是否应该排除目录"""
            exclude_patterns = [
                # 隐藏目录
                dirname.startswith('.'),
                # Python缓存
                dirname == '__pycache__',
                # 虚拟环境
                dirname in ['venv', 'env', '.venv', '.env', 'virtualenv'],
                # Node.js
                dirname == 'node_modules',
                # 构建目录
                dirname in ['build', 'dist', 'target'],
                # 版本控制
                dirname in ['.git', '.svn', '.hg'],
            ]
            return any(exclude_patterns)
        
        def should_exclude_file(filepath):
            """检查是否应该排除文件"""
            # 排除标准库文件（通常位于Python安装目录）
            python_lib_path = os.path.dirname(os.__file__)
            if filepath.startswith(python_lib_path):
                return True
            
            # 排除pystdapi框架文件（除非它们被显式导入）
            # 注意：这里我们仍然监控它们，因为它们是框架的一部分
            # 但用户通常不希望修改框架文件时触发重启
            
            # 可以将pystdapi目录添加到排除列表
            pystdapi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pystdapi')
            pystdapi_dir = os.path.abspath(pystdapi_dir)
            if filepath.startswith(pystdapi_dir):
                # 这里我们选择不排除，因为用户可能想修改框架
                # 但可以添加一个配置选项来控制这个行为
                pass
            
            return False
        
        def check_for_changes():
            """检查文件变化"""
            nonlocal watched_files, file_mtimes
            current_files = collect_files()
            
            # 检查新文件
            new_files = current_files - watched_files
            if new_files:
                print(f"[热加载] 检测到新文件: {', '.join(os.path.basename(f) for f in new_files)}")
                watched_files = current_files
                for filepath in new_files:
                    try:
                        file_mtimes[filepath] = os.path.getmtime(filepath)
                    except OSError:
                        pass
                return True
            
            # 检查文件修改时间
            for filepath in watched_files:
                try:
                    mtime = os.path.getmtime(filepath)
                    if filepath not in file_mtimes:
                        file_mtimes[filepath] = mtime
                    elif file_mtimes[filepath] != mtime:
                        print(f"[热加载] 文件已修改: {os.path.basename(filepath)}")
                        file_mtimes[filepath] = mtime
                        return True
                except OSError:
                    # 文件可能被删除
                    if filepath in watched_files:
                        watched_files.remove(filepath)
                        if filepath in file_mtimes:
                            del file_mtimes[filepath]
                        print(f"[热加载] 文件已删除: {os.path.basename(filepath)}")
                        return True
            
            return False
        
        # 初始化文件监控
        watched_files = collect_files()
        file_mtimes = {}
        for filepath in watched_files:
            try:
                file_mtimes[filepath] = os.path.getmtime(filepath)
            except OSError:
                pass
        
        # 启动服务器
        print(f"\n启动开发服务器（带热重载）: http://{self.host}:{self.port}")
        server_process = start_server()
        
        if server_process is None:
            print("[热加载] 服务器启动失败，退出热加载模式")
            print("[热加载] 尝试使用普通模式启动...")
            # 回退到普通模式
            server = ASGIServer(self.host, self.port, **self.options)
            server.run(app)
            return
        
        try:
            # 监控文件变化
            while True:
                time.sleep(1)  # 每秒检查一次
                
                if check_for_changes():
                    print("\n[热加载] 检测到文件变化，重启服务器...")
                    stop_server()
                    time.sleep(0.5)  # 等待旧进程完全停止
                    print("[热加载] 正在启动新服务器...")
                    server_process = start_server()
                    if server_process is None:
                        print("[热加载] 重启失败，退出热加载模式")
                        break
        
        except KeyboardInterrupt:
            print("\n正在停止服务器...")
            stop_server()
            print("服务器已停止")


# 服务器工厂函数
def get_server(server_name: str, host: str = '127.0.0.1', port: int = 8000, **options) -> ServerAdapter:
    """获取服务器适配器"""
    servers = {
        'asgi': ASGIServer,
        'auto': AutoServer,
        'dev': DevelopmentServer,
    }
    
    server_class = servers.get(server_name.lower())
    if not server_class:
        raise ValueError(f"Unknown server: {server_name}")
    
    # 对于DevelopmentServer，需要明确传递reload参数
    if server_class == DevelopmentServer:
        reload = options.pop('reload', False)
        return server_class(host, port, reload=reload, **options)
    else:
        return server_class(host, port, **options)


# 快捷函数
def run(app: Callable, host: str = '127.0.0.1', port: int = 8000, server: str = 'auto', **options) -> None:
    """运行应用"""
    server_adapter = get_server(server, host, port, **options)
    server_adapter.run(app)