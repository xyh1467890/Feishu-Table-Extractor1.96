import os
from PyQt5.QtCore import QThread, pyqtSignal
from api.feishu_api import extract_bitable_info
from api.feishu_cookie_api import extract_bitable_info_via_cookie


class FetchDataThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, auth_type, auth_data, feishu_url, fetch_records):
        super().__init__()
        self.auth_type = auth_type  # "token" or "cookie"
        self.auth_data = auth_data
        self.feishu_url = feishu_url
        self.fetch_records = fetch_records

    def run(self):
        try:
            self.progress.emit("正在解析链接...")
            self.progress.emit("正在获取数据表信息...")
            
            if self.auth_type == "token":
                os.environ["FEISHU_USER_TOKEN"] = self.auth_data
                headers = {
                    "Authorization": f"Bearer {self.auth_data}",
                    "Content-Type": "application/json"
                }
                result = extract_bitable_info(
                    self.feishu_url, 
                    headers=headers,
                    fetch_records=self.fetch_records
                )
            elif self.auth_type == "cookie":
                result = extract_bitable_info_via_cookie(
                    self.feishu_url,
                    self.auth_data,
                    fetch_records=self.fetch_records
                )
            else:
                raise ValueError("未知的认证方式")
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
