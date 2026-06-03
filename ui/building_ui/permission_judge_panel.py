"""
Permission 评测模块面板
"""
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt

from building_spec.permission_judge import PermissionSingleJudge


class PermissionJudgePanel(QWidget):
    """Permission 评测面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("module_panel")
        
        self.permission_single_judge = PermissionSingleJudge()
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
        
        # Query
        query_label = QLabel("Query（用户需求，多轮每轮一行）")
        query_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        layout.addWidget(query_label)
        
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("第一轮用户需求\n第二轮用户需求\n...")
        self.query_input.setMinimumHeight(80)
        self.query_input.setStyleSheet("""
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
        layout.addWidget(self.query_input)
        
        # Source Base Token 和 Base Tokens 在同一行
        tokens_row = QHBoxLayout()
        tokens_row.setSpacing(14)
        
        # Source Base Token
        source_layout = QVBoxLayout()
        source_label = QLabel("Source Base Token")
        source_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        source_label.setMinimumHeight(22)
        source_layout.addWidget(source_label)
        
        self.source_input = QTextEdit()
        self.source_input.setPlaceholderText("输入 Source Base Token...")
        self.source_input.setFixedHeight(40)
        self.source_input.setStyleSheet("""
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
        source_layout.addWidget(self.source_input)
        tokens_row.addLayout(source_layout)
        
        # Base Tokens
        base_layout = QVBoxLayout()
        base_label = QLabel("Base Tokens（可选，多轮每轮一行）")
        base_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        base_label.setMinimumHeight(22)
        base_layout.addWidget(base_label)
        
        self.base_input = QTextEdit()
        self.base_input.setPlaceholderText("Base Token")
        self.base_input.setFixedHeight(40)
        self.base_input.setStyleSheet("""
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
        base_layout.addWidget(self.base_input)
        tokens_row.addLayout(base_layout)
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
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, "提示", "请输入 Query！")
            return
        
        source_base_token = self.source_input.toPlainText().strip()
        if not source_base_token:
            QMessageBox.warning(self, "提示", "请输入 Source Base Token！")
            return
        
        # 解析查询列表
        queries = [q.strip() for q in query_text.split('\n') if q.strip()]
        
        # 解析 Base Tokens
        base_tokens_text = self.base_input.toPlainText().strip()
        base_tokens = [a.strip() for a in base_tokens_text.split('\n')] if base_tokens_text else None
        
        # 发送请求
        result = self.permission_single_judge.send_request(
            queries=queries,
            source_base_token=source_base_token,
            base_tokens=base_tokens,
            agent="permission"
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
