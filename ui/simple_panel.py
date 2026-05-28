import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame
)
from PyQt5.QtCore import Qt


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class SimplePanel(QWidget):
    def __init__(self, parent=None, module_name="仪表盘"):
        super().__init__(parent)
        self.parent_window = parent
        self.module_name = module_name
        self.setObjectName("module_panel")
        
        self.get_cookie_btn = None
        self.confirm_login_btn = None
        self.cookie_status_label = None
        self.clear_cookie_btn = None
        self.cookie_input = None
        self.url_input = None
        self.fetch_button = None
        self.progress_label = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)
        
        # Cookie Authentication Section
        auth_title = QLabel("Cookie 认证")
        auth_title.setObjectName("section_title")
        layout.addWidget(auth_title)
        
        auto_info = QLabel("方式一：浏览器自动提取（推荐）")
        auto_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        layout.addWidget(auto_info)
        
        auto_desc = QLabel("自动打开飞书网页，登录后一键提取 Cookie。")
        auto_desc.setStyleSheet("color: #909399; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(auto_desc)
        
        auto_btn_layout = QHBoxLayout()
        auto_btn_layout.setSpacing(10)
        
        self.get_cookie_btn = QPushButton("🚀 启动浏览器")
        self.get_cookie_btn.setObjectName("cookie_auto_btn")
        self.get_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.get_cookie_btn.clicked.connect(self.parent_window.start_get_cookie if self.parent_window else lambda: None)
        
        self.confirm_login_btn = QPushButton("✓ 已登录，提取 Cookie")
        self.confirm_login_btn.setEnabled(False)
        self.confirm_login_btn.setObjectName("cookie_confirm_btn")
        self.confirm_login_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_login_btn.clicked.connect(self.parent_window.confirm_get_cookie if self.parent_window else lambda: None)
        
        auto_btn_layout.addWidget(self.get_cookie_btn)
        auto_btn_layout.addWidget(self.confirm_login_btn)
        auto_btn_layout.addStretch()
        
        layout.addLayout(auto_btn_layout)
        
        self.cookie_status_label = QLabel("")
        self.cookie_status_label.setStyleSheet("color: #e6a23c; font-size: 12px;")
        layout.addWidget(self.cookie_status_label)
        
        layout.addSpacing(8)
        
        divider_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: #ebeef5; max-height: 1px;")
        or_label = QLabel("           或")
        or_label.setStyleSheet("color: #c0c4cc; font-size: 13px;")
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #ebeef5; max-height: 1px;")
        divider_layout.addWidget(line1)
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(line2)
        layout.addLayout(divider_layout)
        
        layout.addSpacing(8)
        
        manual_header_layout = QHBoxLayout()
        manual_info = QLabel("方式二：手动输入")
        manual_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        
        self.clear_cookie_btn = QPushButton("清空内容")
        self.clear_cookie_btn.setObjectName("clear_btn")
        self.clear_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.clear_cookie_btn.clicked.connect(lambda: self.cookie_input.clear())
        
        manual_header_layout.addWidget(manual_info)
        manual_header_layout.addStretch()
        manual_header_layout.addWidget(self.clear_cookie_btn)
        layout.addLayout(manual_header_layout)
        
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("请在此粘贴完整的飞书 Cookie...")
        self.cookie_input.setMinimumHeight(42)
        self.cookie_input.setClearButtonEnabled(True)
        self.cookie_input.setObjectName("auth_input")
        layout.addWidget(self.cookie_input)
        
        layout.addSpacing(8)
        
        # Target URL Section
        target_title = QLabel(f"目标{self.module_name}")
        target_title.setObjectName("section_title")
        layout.addWidget(target_title)
        
        self.url_input = QLineEdit()
        # 根据模块类型设置不同的 URL 提示
        if self.module_name == "表单":
            self.url_input.setPlaceholderText("https://bytedance.larkoffice.com/share/base/form/...")
        else:
            self.url_input.setPlaceholderText("https://xxx.feishu.cn/base/...")
        self.url_input.setObjectName("url_input")
        layout.addWidget(self.url_input)
        
        layout.addStretch()
        
        # Action Button
        if self.module_name == "仪表盘":
            self.fetch_button = QPushButton("获取仪表盘snapshot")
        else:
            self.fetch_button = QPushButton(f"获取{self.module_name}数据")
        self.fetch_button.setObjectName("primary_btn")
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.parent_window.fetch_data if self.parent_window else lambda: None)
        layout.addWidget(self.fetch_button)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #67c23a; font-size: 13px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.progress_label)
