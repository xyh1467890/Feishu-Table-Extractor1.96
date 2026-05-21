from PyQt5.QtCore import QThread, pyqtSignal


class GetCookieThread(QThread):
    cookie_received = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            self.progress.emit("正在启动浏览器...")
            
            # 导入 selenium 相关库
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_experimental_option("detach", True)
            
            self.progress.emit("正在打开飞书网页...")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            driver.get("https://www.feishu.cn/")
            
            self.progress.emit("请在浏览器中登录飞书账户...")
            self.progress.emit("登录完成后点击应用中的确定按钮")
            
            # 保存 driver 引用，以便主程序可以控制
            self.driver = driver
            
            # 等待用户登录（这里我们不阻塞，让主程序处理）
            # 实际上，我们需要一个更好的方式来等待用户登录
            
        except ImportError:
            self.error.emit("缺少必要的库，请先运行: pip install selenium webdriver-manager")
        except Exception as e:
            self.error.emit(f"启动浏览器失败: {str(e)}")
    
    def get_cookie_after_login(self):
        """在用户登录后获取 Cookie"""
        try:
            if not hasattr(self, 'driver') or not self.driver:
                self.error.emit("浏览器未启动")
                return
            
            self.progress.emit("正在获取 Cookie...")
            cookies = self.driver.get_cookies()
            
            # 转换为字符串格式
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # 关闭浏览器
            try:
                self.driver.quit()
            except:
                pass
            
            self.cookie_received.emit(cookie_str)
            
        except Exception as e:
            self.error.emit(f"获取 Cookie 失败: {str(e)}")
