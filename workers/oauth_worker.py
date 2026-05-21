import socket
import threading
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QThread, pyqtSignal
from config.settings import REDIRECT_URI, REDIRECT_PORT


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, callback=None, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            code = query_params['code'][0]
            state = query_params.get('state', [''])[0]
            
            html = """
            <html>
            <head><meta charset="UTF-8"><title>授权成功</title></head>
            <body style="margin:0; padding:80px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f5f7fa;">
                <div style="max-width:400px; margin:0 auto; background:#ffffff; padding:40px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.1); text-align:center; border: 1px solid #e4e7ed;">
                    <div style="font-size:48px; margin-bottom:20px; color:#67c23a;">✓</div>
                    <h2 style="margin:0 0 12px 0; color:#303133; font-size:20px;">授权成功</h2>
                    <p style="margin:0; color:#909399; font-size:14px;">请关闭此页面，返回应用程序</p>
                </div>
            </body>
            </html>
            """.encode('utf-8')
            
            self.wfile.write(html)
            
            if self.callback:
                self.callback(code, state)
        else:
            html = """
            <html>
            <head><meta charset="UTF-8"><title>授权失败</title></head>
            <body style="margin:0; padding:80px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f5f7fa;">
                <div style="max-width:400px; margin:0 auto; background:#ffffff; padding:40px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.1); text-align:center; border: 1px solid #e4e7ed;">
                    <div style="font-size:48px; margin-bottom:20px; color:#f56c6c;">✗</div>
                    <h2 style="margin:0 0 12px 0; color:#303133; font-size:20px;">授权失败</h2>
                    <p style="margin:0; color:#909399; font-size:14px;">未获取到授权码，请重试</p>
                </div>
            </body>
            </html>
            """.encode('utf-8')
            self.wfile.write(html)

    def log_message(self, format, *args):
        pass


class OAuthTokenThread(QThread):
    token_received = pyqtSignal(str)
    error = pyqtSignal(str)
    state_received = pyqtSignal(str, str)

    def __init__(self, app_id, app_secret):
        super().__init__()
        self.app_id = app_id
        self.app_secret = app_secret
        self.server = None
        self.port = REDIRECT_PORT

    def run(self):
        try:
            redirect_uri = REDIRECT_URI
            
            auth_url = (
                f"https://open.feishu.cn/open-apis/authen/v1/index"
                f"?app_id={self.app_id}"
                f"&redirect_uri={redirect_uri}"
                f"&response_type=code"
                f"&state=feishu_auth"
            )
            
            webbrowser.open(auth_url)
            
            def handler_factory(callback):
                def create_handler(*args, **kwargs):
                    return OAuthCallbackHandler(*args, callback=callback, **kwargs)
                return create_handler
            
            auth_code = None
            auth_event = threading.Event()
            
            def on_code_received(code, state):
                nonlocal auth_code
                auth_code = code
                auth_event.set()
            
            self.server = HTTPServer(('localhost', self.port), handler_factory(on_code_received))
            
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            if not auth_event.wait(timeout=300):
                self.error.emit("等待授权超时，请重试")
                return
            
            self.server.shutdown()
            
            if auth_code:
                token_url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
                
                app_access_token = self.get_app_access_token()
                
                if not app_access_token:
                    self.error.emit("获取应用访问令牌失败")
                    return
                
                headers = {
                    "Authorization": f"Bearer {app_access_token}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "grant_type": "authorization_code",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "code": auth_code
                }
                
                response = requests.post(token_url, json=data, headers=headers)
                result = response.json()
                
                if result.get('code') == 0:
                    user_access_token = result.get('data', {}).get('access_token')
                    if user_access_token:
                        self.token_received.emit(user_access_token)
                    else:
                        self.error.emit("未获取到用户访问令牌")
                else:
                    self.error.emit(f"获取用户令牌失败：{result.get('msg', '未知错误')}")
            
        except Exception as e:
            self.error.emit(f"OAuth 流程出错：{str(e)}")
            if self.server:
                self.server.shutdown()

    def get_app_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = requests.post(url, json=data)
        result = response.json()
        if result.get('code') == 0:
            return result.get('app_access_token')
        return None
