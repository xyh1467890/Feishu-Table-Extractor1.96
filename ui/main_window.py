import sys
import os
import json
import webbrowser
import subprocess


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后
        base_path = sys._MEIPASS
    else:
        # 开发时
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTextEdit, QFileDialog, QMessageBox, QCheckBox, 
    QTabWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from ui.styles import APP_STYLE
from config.settings import REDIRECT_PORT
from workers.oauth_worker import OAuthTokenThread
from workers.cookie_worker import GetCookieThread
from workers.fetch_worker import FetchDataThread


class FeishuBitableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("飞书多维表格元数据工具")
        
        self.resize(1200, 900)
        self.setMinimumSize(1000, 700)
        self.current_result = None
        self.oauth_thread = None
        self.get_cookie_thread = None
        self.tabs = None
        self.init_ui()

    def init_ui(self):
        # 基础样式设置，确保复选框等能正常渲染基础形状
        QApplication.instance().setStyle('Fusion')
        self.setStyleSheet(APP_STYLE)
        
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        
        # 整体采用左右分栏布局
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==========================================
        # 左侧控制面板 (Sidebar)
        # ==========================================
        left_panel = QWidget()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(420)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(35, 45, 35, 45)
        left_layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        title = QLabel("飞书多维表格元数据获取工具")
        title.setObjectName("title")
        subtitle = QLabel('需要帮助请联系<a href="https://www.larkoffice.com/invitation/page/add_contact/?token=6e2ma113-ab71-48a6-a684-2c8bb2e38e32" style="color:#409eff; text-decoration:none;">作者</a>')
        subtitle.setObjectName("subtitle")
        subtitle.setOpenExternalLinks(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        left_layout.addLayout(header_layout)
        
        left_layout.addSpacing(15)
        
        # Section 1: Auth
        auth_title = QLabel("认证方式")
        auth_title.setObjectName("section_title")
        left_layout.addWidget(auth_title)
        
        self.tabs = QTabWidget()
        
        # --- OAuth Tab ---
        oauth_tab = QWidget()
        oauth_layout = QVBoxLayout(oauth_tab)
        oauth_layout.setContentsMargins(0, 15, 0, 0)
        oauth_layout.setSpacing(12)
        
        info_label = QLabel(f"通过应用凭证一键获取 User Token。<br><a href='https://open.feishu.cn' style='color:#409eff; text-decoration:none;'>前往开放平台</a> 配置回调 URI: <code style='background:#f5f7fa; padding:2px 6px; border-radius:4px;'>http://localhost:{REDIRECT_PORT}</code>")
        info_label.setObjectName("info_text")
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        oauth_layout.addWidget(info_label)
        
        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("App ID (cli_...)")
        oauth_layout.addWidget(self.app_id_input)
        
        self.app_secret_input = QLineEdit()
        self.app_secret_input.setPlaceholderText("App Secret")
        self.app_secret_input.setEchoMode(QLineEdit.Password)
        oauth_layout.addWidget(self.app_secret_input)
        
        self.login_button = QPushButton("浏览器一键授权")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.start_oauth_flow)
        oauth_layout.addWidget(self.login_button)
        
        self.oauth_status_label = QLabel("")
        self.oauth_status_label.setStyleSheet("color: #409eff; font-size: 12px;")
        oauth_layout.addWidget(self.oauth_status_label)
        oauth_layout.addStretch()
        
        # --- Manual Token Tab ---
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        manual_layout.setContentsMargins(0, 15, 0, 0)
        manual_layout.setSpacing(12)
        
        # 第一行：User Access Token链接
        manual_info1 = QLabel("直接输入已有的 <a href='help:token' style='color:#409eff; text-decoration:none;'>User Access Token</a>。")
        manual_info1.setObjectName("info_text")
        manual_info1.setOpenExternalLinks(False)
        manual_info1.setWordWrap(True)
        manual_info1.setToolTip("点击查看如何获取 User Access Token 的视频教程")
        manual_info1.linkActivated.connect(self.on_manual_info_link_clicked)
        manual_layout.addWidget(manual_info1)
        
        # 第二行：API调试台链接
        manual_info2 = QLabel("<a href='https://open.feishu.cn/api-explorer' style='color:#409eff; text-decoration:none;'>前往 API 调试台</a> 获取。")
        manual_info2.setObjectName("info_text")
        manual_info2.setOpenExternalLinks(True)
        manual_info2.setWordWrap(True)
        manual_layout.addWidget(manual_info2)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("粘贴 User Access Token")
        self.token_input.setEchoMode(QLineEdit.Password)
        manual_layout.addWidget(self.token_input)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.show_token_btn = QPushButton("显示")
        self.show_token_btn.setCheckable(True)
        self.show_token_btn.toggled.connect(self.toggle_token_visibility)
        self.open_api_btn = QPushButton("打开调试台")
        self.open_api_btn.clicked.connect(lambda: webbrowser.open("https://open.feishu.cn/api-explorer"))
        btn_row.addWidget(self.show_token_btn)
        btn_row.addWidget(self.open_api_btn)
        manual_layout.addLayout(btn_row)
        manual_layout.addStretch()
        
        # --- Cookie Tab ---
        cookie_tab = QWidget()
        cookie_layout = QVBoxLayout(cookie_tab)
        cookie_layout.setContentsMargins(0, 15, 0, 0)
        cookie_layout.setSpacing(12)
        
        # 1. 自动获取区域
        auto_info = QLabel("方式一：浏览器自动提取（推荐）")
        auto_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        cookie_layout.addWidget(auto_info)
        
        auto_desc = QLabel("自动打开飞书网页，登录后一键提取 Cookie。")
        auto_desc.setStyleSheet("color: #909399; font-size: 12px; margin-bottom: 5px;")
        cookie_layout.addWidget(auto_desc)
        
        auto_btn_layout = QHBoxLayout()
        auto_btn_layout.setSpacing(10)
        
        self.get_cookie_btn = QPushButton("🚀 启动浏览器")
        self.get_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.get_cookie_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: normal;
            }
            QPushButton:hover { background-color: #66b1ff; }
            QPushButton:pressed { background-color: #3a8ee6; }
            QPushButton:disabled { background-color: #a0cfff; }
        """)
        self.get_cookie_btn.clicked.connect(self.start_get_cookie)
        
        self.confirm_login_btn = QPushButton("✓ 已登录，提取 Cookie")
        self.confirm_login_btn.setEnabled(False)
        self.confirm_login_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_login_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: normal;
            }
            QPushButton:hover { background-color: #85ce61; }
            QPushButton:pressed { background-color: #5daf34; }
            QPushButton:disabled { background-color: #b3e19d; }
        """)
        self.confirm_login_btn.clicked.connect(self.confirm_get_cookie)
        
        auto_btn_layout.addWidget(self.get_cookie_btn)
        auto_btn_layout.addWidget(self.confirm_login_btn)
        auto_btn_layout.addStretch()
        
        cookie_layout.addLayout(auto_btn_layout)
        
        self.cookie_status_label = QLabel("")
        self.cookie_status_label.setStyleSheet("color: #e6a23c; font-size: 12px;")
        cookie_layout.addWidget(self.cookie_status_label)
        
        cookie_layout.addSpacing(5)
        
        # 2. 分隔区
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
        cookie_layout.addLayout(divider_layout)
        
        cookie_layout.addSpacing(5)
        
        # 3. 手动输入区
        manual_header_layout = QHBoxLayout()
        manual_info = QLabel("方式二：手动输入")
        manual_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        
        self.clear_cookie_btn = QPushButton("清空内容")
        self.clear_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.clear_cookie_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #909399;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: normal;
            }
            QPushButton:hover { color: #f56c6c; border-color: #fbc4c4; background-color: #fef0f0; }
        """)
        self.clear_cookie_btn.clicked.connect(lambda: self.cookie_input.clear())
        
        manual_header_layout.addWidget(manual_info)
        manual_header_layout.addStretch()
        manual_header_layout.addWidget(self.clear_cookie_btn)
        cookie_layout.addLayout(manual_header_layout)
        
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("请在此粘贴完整的飞书 Cookie...")
        self.cookie_input.setMinimumHeight(42)
        self.cookie_input.setClearButtonEnabled(True)
        cookie_layout.addWidget(self.cookie_input)
        
        cookie_layout.addStretch()
        
        self.tabs.addTab(manual_tab, "Token")
        self.tabs.addTab(oauth_tab, "OAuth")
        self.tabs.addTab(cookie_tab, "Cookie（不推荐）")
        left_layout.addWidget(self.tabs)
        
        # 标签页切换监听
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        left_layout.addSpacing(10)
        
        # Section 2: Target
        target_title = QLabel("目标数据表")
        target_title.setObjectName("section_title")
        left_layout.addWidget(target_title)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://xxx.feishu.cn/base/...")
        left_layout.addWidget(self.url_input)
        
        self.fetch_records_checkbox = QCheckBox("同时获取数据表记录内容")
        self.fetch_records_checkbox.setChecked(True)
        self.fetch_records_checkbox.setCursor(Qt.PointingHandCursor)
        left_layout.addWidget(self.fetch_records_checkbox)
        
        left_layout.addStretch()
        
        # Action Button
        self.fetch_button = QPushButton("获取数据")
        self.fetch_button.setObjectName("primary_btn")
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.fetch_data)
        left_layout.addWidget(self.fetch_button)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #67c23a; font-size: 13px; font-weight: bold; margin-top: 5px;")
        left_layout.addWidget(self.progress_label)
        
        main_layout.addWidget(left_panel)
        
        # ==========================================
        # 右侧结果面板 (Main Content)
        # ==========================================
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 45, 40, 45)
        right_layout.setSpacing(20)
        
        result_header = QHBoxLayout()
        result_title = QLabel("解析结果")
        result_title.setObjectName("section_title")
        result_title.setStyleSheet("margin: 0;")
        
        self.export_button = QPushButton("导出 JSON")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self.export_json)
        self.export_button.setEnabled(False)
        self.export_button.setFixedWidth(120)
        
        result_header.addWidget(result_title)
        result_header.addStretch()
        result_header.addWidget(self.export_button)
        
        right_layout.addLayout(result_header)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("获取到的 JSON 数据将在这里格式化显示...")
        right_layout.addWidget(self.result_text)
        
        main_layout.addWidget(right_panel)

    def on_tab_changed(self, index):
        """标签页切换时的处理"""
        tab_text = self.tabs.tabText(index)
        if "Cookie" in tab_text:
            # Cookie 标签页：弹框提示
            QMessageBox.warning(
                self, 
                "提示", 
                "注意：Cookie 方式仅可提取当前数据表 JSON 数据，无法批量提取全表 JSON，也不支持读取数据表内记录内容。"
            )
            self.fetch_records_checkbox.setEnabled(False)
            self.fetch_records_checkbox.setChecked(False)
            self.fetch_records_checkbox.setToolTip("Cookie 方式不支持获取记录内容")
        else:
            self.fetch_records_checkbox.setEnabled(True)
            self.fetch_records_checkbox.setChecked(True)
            self.fetch_records_checkbox.setToolTip("")
    
    def on_manual_info_link_clicked(self, link):
        """处理 Token 标签页链接点击"""
        if link == "help:token":
            # 播放视频
            video_path = resource_path("get_user_access_token.mp4")
            if os.path.exists(video_path):
                if sys.platform == "win32":
                    os.startfile(video_path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", video_path])
                else:
                    subprocess.call(["xdg-open", video_path])
            else:
                QMessageBox.warning(self, "提示", f"视频文件不存在：{video_path}")
        elif link.startswith("http"):
            webbrowser.open(link)
    
    def toggle_token_visibility(self, checked):
        if checked:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.show_token_btn.setText("隐藏")
            self.show_token_btn.setStyleSheet("background-color: #409eff; color: white;")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.show_token_btn.setText("显示")
            self.show_token_btn.setStyleSheet("")
    
    def start_get_cookie(self):
        """开始获取 Cookie"""
        self.get_cookie_btn.setEnabled(False)
        self.cookie_status_label.setText("正在准备...")
        
        self.get_cookie_thread = GetCookieThread()
        self.get_cookie_thread.cookie_received.connect(self.on_cookie_received)
        self.get_cookie_thread.error.connect(self.on_get_cookie_error)
        self.get_cookie_thread.progress.connect(self.update_cookie_status)
        self.get_cookie_thread.start()
    
    def confirm_get_cookie(self):
        """确认登录完成，获取 Cookie"""
        if self.get_cookie_thread:
            self.confirm_login_btn.setEnabled(False)
            self.get_cookie_thread.get_cookie_after_login()
    
    def update_cookie_status(self, message):
        """更新 Cookie 状态"""
        self.cookie_status_label.setText(message)
        if "请在浏览器中登录" in message:
            self.confirm_login_btn.setEnabled(True)
    
    def on_cookie_received(self, cookie):
        """获取到 Cookie"""
        self.cookie_input.setText(cookie)
        self.cookie_status_label.setText("✓ Cookie 已自动填入")
        self.get_cookie_btn.setEnabled(True)
        self.confirm_login_btn.setEnabled(False)
        QMessageBox.information(self, "成功", "Cookie 获取成功，已自动填入！")
    
    def on_get_cookie_error(self, error_msg):
        """获取 Cookie 出错"""
        self.cookie_status_label.setText(f"✗ 错误：{error_msg}")
        self.get_cookie_btn.setEnabled(True)
        self.confirm_login_btn.setEnabled(False)
        QMessageBox.critical(self, "错误", error_msg)

    def start_oauth_flow(self):
        app_id = self.app_id_input.text().strip()
        app_secret = self.app_secret_input.text().strip()

        if not app_id:
            QMessageBox.warning(self, "提示", "请输入 App ID")
            return
        if not app_secret:
            QMessageBox.warning(self, "提示", "请输入 App Secret")
            return

        self.login_button.setEnabled(False)
        self.oauth_status_label.setText("正在打开浏览器进行授权...")

        self.oauth_thread = OAuthTokenThread(app_id, app_secret)
        self.oauth_thread.token_received.connect(self.on_token_received)
        self.oauth_thread.error.connect(self.on_oauth_error)
        self.oauth_thread.start()

    def on_token_received(self, token):
        self.token_input.setText(token)
        self.oauth_status_label.setText("✓ 登录成功！Token 已自动填充")
        self.login_button.setEnabled(True)
        QMessageBox.information(self, "成功", "登录成功！Token 已自动填充到输入框中。")

    def on_oauth_error(self, error_msg):
        self.oauth_status_label.setText(f"✗ 错误：{error_msg}")
        self.login_button.setEnabled(True)
        QMessageBox.critical(self, "错误", error_msg)

    def fetch_data(self):
        current_tab_index = self.tabs.currentIndex()
        feishu_url = self.url_input.text().strip()
        fetch_records = self.fetch_records_checkbox.isChecked()

        auth_type = None
        auth_data = None

        if current_tab_index == 0 or current_tab_index == 1:
            # Token 或 OAuth 标签页
            user_token = self.token_input.text().strip()
            if not user_token:
                QMessageBox.warning(self, "提示", "请输入用户 Token")
                return
            auth_type = "token"
            auth_data = user_token
        elif current_tab_index == 2:
            # Cookie 标签页
            cookie = self.cookie_input.text().strip()
            if not cookie:
                QMessageBox.warning(self, "提示", "请输入飞书 Cookie")
                return
            auth_type = "cookie"
            auth_data = cookie

        if not feishu_url:
            QMessageBox.warning(self, "提示", "请输入多维表格链接")
            return

        self.fetch_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.result_text.clear()
        self.progress_label.setStyleSheet("color: #409eff;")

        self.thread = FetchDataThread(auth_type, auth_data, feishu_url, fetch_records)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.on_fetch_finished)
        self.thread.error.connect(self.on_fetch_error)
        self.thread.start()

    def update_progress(self, message):
        self.progress_label.setText(message)

    def on_fetch_finished(self, result):
        self.current_result = result
        json_str = json.dumps(result, ensure_ascii=False, indent=2)
        self.result_text.setText(json_str)
        self.export_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.progress_label.setStyleSheet("color: #67c23a;")
        self.progress_label.setText("✓ 获取成功！")

    def on_fetch_error(self, error_msg):
        self.result_text.setText(f"错误：{error_msg}")
        self.fetch_button.setEnabled(True)
        self.progress_label.setStyleSheet("color: #f56c6c;")
        self.progress_label.setText("✗ 获取失败")
        QMessageBox.critical(self, "错误", f"获取数据失败：{error_msg}")

    def export_json(self):
        if not self.current_result:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存 JSON 文件", 
            "", 
            "JSON 文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_result, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"文件已保存到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")
