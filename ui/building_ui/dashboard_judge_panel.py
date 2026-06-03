"""
Dashboard 评测模块面板
"""
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt

from building_spec.dashboard_judge import DashboardSingleJudge


class DashboardJudgePanel(QWidget):
    """Dashboard 评测面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("module_panel")
        
        self.dashboard_single_judge = DashboardSingleJudge()
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                font-size: 14px;
                color: #1f2937;
                background-color: #f8fafc;
            }
        """)
        
        # --- 单条测试区域 ---
        single_test_section = self._create_single_test_section()
        layout.addWidget(single_test_section)
        
        # --- 结果显示区域 ---
        result_section = self._create_result_section()
        layout.addWidget(result_section, stretch=1)
        
        # --- 按钮区域 ---
        btn_section = self._create_button_section()
        layout.addWidget(btn_section)
    
    def _create_single_test_section(self):
        """创建单条测试区域"""
        group = QGroupBox("🧪 单条测试")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 15px;
                color: #1f2937;
                border: none;
                border-radius: 10px;
                margin-top: 6px;
                padding-top: 20px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 28, 20, 22)
        
        # Queries
        queries_label = QLabel("Queries（多轮对话每轮一行）")
        queries_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        layout.addWidget(queries_label)
        
        self.queries_input = QTextEdit()
        self.queries_input.setPlaceholderText("第一轮用户需求\n第二轮用户需求\n...")
        self.queries_input.setMinimumHeight(80)
        self.queries_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #fafafa;
                color: #1f2937;
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }
            QTextEdit:hover {
                border-color: #93c5fd;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        layout.addWidget(self.queries_input)
        
        # Before Base Token 和 After Base Tokens 在同一行
        tokens_row = QHBoxLayout()
        tokens_row.setSpacing(14)
        
        # Before Base Token
        before_layout = QVBoxLayout()
        before_label = QLabel("Before Base Token")
        before_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        before_label.setMinimumHeight(22)
        before_layout.addWidget(before_label)
        
        self.before_input = QTextEdit()
        self.before_input.setPlaceholderText("输入 Before Base Token...")
        self.before_input.setFixedHeight(40)
        self.before_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
                background-color: #fafafa;
                color: #1f2937;
                min-height: 40px;
                max-height: 40px;
            }
            QTextEdit:hover {
                border-color: #93c5fd;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        before_layout.addWidget(self.before_input)
        tokens_row.addLayout(before_layout)
        
        # After Base Tokens
        after_layout = QVBoxLayout()
        after_label = QLabel("After Base Tokens（可选，多轮每轮一行）")
        after_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        after_label.setMinimumHeight(22)
        after_layout.addWidget(after_label)
        
        self.after_input = QTextEdit()
        self.after_input.setPlaceholderText("After Base Token")
        self.after_input.setFixedHeight(40)
        self.after_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
                background-color: #fafafa;
                color: #1f2937;
                min-height: 40px;
                max-height: 40px;
            }
            QTextEdit:hover {
                border-color: #93c5fd;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        after_layout.addWidget(self.after_input)
        tokens_row.addLayout(after_layout)
        layout.addLayout(tokens_row)
        layout.addSpacing(20)
        
        # 运行按钮
        self.run_btn = QPushButton("运行单条测试")
        self.run_btn.clicked.connect(self.on_single_test)
        self.run_btn.setMinimumHeight(40)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60a5fa, stop:1 #3b82f6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
            }
        """)
        layout.addWidget(self.run_btn)
        
        return group
    
    def _create_result_section(self):
        """创建结果显示区域"""
        group = QGroupBox("📝 评测结果")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 15px;
                color: #1f2937;
                border: none;
                border-radius: 10px;
                margin-top: 6px;
                padding-top: 20px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 28, 20, 22)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("响应体将显示在这里...")
        self.result_text.setMinimumHeight(160)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                background-color: #fafafa;
                color: #1f2937;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        layout.addWidget(self.result_text)
        
        return group
    
    def _create_button_section(self):
        """创建按钮区域"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f8fafc;")
        layout = QHBoxLayout(widget)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addStretch()
        
        return widget
    
    # === 事件处理 ===
    
    def on_single_test(self):
        """单条测试"""
        queries_text = self.queries_input.toPlainText().strip()
        if not queries_text:
            QMessageBox.warning(self, "提示", "请输入 Queries！")
            return
        
        before_base_token = self.before_input.toPlainText().strip()
        if not before_base_token:
            QMessageBox.warning(self, "提示", "请输入 Before Base Token！")
            return
        
        # 解析查询列表
        queries = [q.strip() for q in queries_text.split('\n') if q.strip()]
        
        # 解析 After Base Tokens
        after_tokens_text = self.after_input.toPlainText().strip()
        after_base_tokens = [a.strip() for a in after_tokens_text.split('\n')] if after_tokens_text else None
        
        # 发送请求
        result = self.dashboard_single_judge.send_request(
            queries=queries,
            before_base_token=before_base_token,
            after_base_tokens=after_base_tokens,
            agent="dashboard"
        )
        
        self.append_result("单条测试响应", result)
    
    def append_result(self, title, data):
        """添加结果到文本框"""
        import json
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        content = f"[{timestamp}] {title}\n"
        content += json.dumps(data, indent=2, ensure_ascii=False)
        content += "\n" + "="*60 + "\n\n"
        
        self.result_text.append(content)
        scrollbar = self.result_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

