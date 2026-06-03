"""
批量调用对话框模块
"""
import sys
import os
# 添加上级目录到路径，这样可以导入 config
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, root_dir)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QMessageBox, QFileDialog, QSpinBox, QComboBox,
    QGroupBox, QTextEdit, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from building_spec.batch_judge import BatchJudge
from building_spec.dashboard_judge import DashboardBatchJudge
from building_spec.workflow_judge import WorkflowBatchJudge
from building_spec.block_judge import BlockBatchJudge
from building_spec.permission_judge import PermissionBatchJudge
from building_spec.table_judge import TableBatchJudge
from config.settings import get_judge_api_key, set_judge_api_key


class BatchJudgeDialog(QDialog):
    """批量调用对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("批量调用 Agent")
        self.setMinimumSize(1000, 900)
        self.file_path = None
        self.is_processing = False
        self.batch_judge = BatchJudge()
        self.dashboard_batch_judge = DashboardBatchJudge()
        self.workflow_batch_judge = WorkflowBatchJudge()
        self.block_batch_judge = BlockBatchJudge()
        self.permission_batch_judge = PermissionBatchJudge()
        self.table_batch_judge = TableBatchJudge()
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                font-size: 14px;
                color: #1f2937;
                background-color: #f8fafc;
            }
        """)
        
        # --- 文件选择区域 ---
        file_section = self._create_file_section()
        layout.addWidget(file_section)
        
        # --- 配置区域 ---
        config_section = self._create_config_section()
        layout.addWidget(config_section)
        
        # --- 结果显示区域 ---
        result_section = self._create_result_section()
        layout.addWidget(result_section, stretch=1)
        
        # --- 按钮区域 ---
        btn_section = self._create_button_section()
        layout.addWidget(btn_section)
    
    def _create_file_section(self):
        """创建文件选择区域"""
        group = QGroupBox("📁 测试用例文件")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 16px;
                color: #1f2937;
                border: none;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 20px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 24px;
                padding: 0 14px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 28, 28, 20)
        
        # 文件路径显示
        path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择您的输入文件（.csv/.xlsx/.xls）")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setMinimumHeight(48)
        self.file_path_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 12px 18px;
                font-size: 14px;
                background-color: #fafafa;
                color: #4b5563;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        path_layout.addWidget(self.file_path_input, stretch=1)
        
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.clicked.connect(self.on_select_file)
        self.select_file_btn.setMinimumHeight(48)
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 32px;
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
        path_layout.addWidget(self.select_file_btn)
        layout.addLayout(path_layout)
        
        return group
    
    def _create_config_section(self):
        """创建配置区域"""
        group = QGroupBox("⚙️ 评估配置")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 16px;
                color: #1f2937;
                border: none;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 20px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 24px;
                padding: 0 14px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 20)
        
        # 第一行：Agent, Mode, API Key
        row1 = QHBoxLayout()
        
        # Agent
        self.agent_widget = QWidget()
        self.agent_widget.setStyleSheet("background-color: #ffffff;")
        agent_layout = QVBoxLayout(self.agent_widget)
        agent_layout.setContentsMargins(0, 0, 0, 0)
        agent_label = QLabel("Agent 类型")
        agent_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 8px; background-color: white;")
        agent_label.setMinimumHeight(22)
        agent_layout.addWidget(agent_label)
        
        self.agent_combo = QComboBox()
        self.agent_combo.addItems(["building", "table", "dashboard", "permission", "workflow", "block"])
        self.agent_combo.setCurrentText("building")
        self.agent_combo.currentTextChanged.connect(self.on_agent_changed)
        self.agent_combo.setMinimumHeight(48)
        self.agent_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                background-color: #ffffff;
                color: #1f2937;
                min-width: 160px;
            }
            QComboBox:hover {
                border-color: #93c5fd;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #64748b;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e5e7eb;
                background-color: #ffffff;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
                padding: 6px;
                border-radius: 8px;
            }
        """)
        agent_layout.addWidget(self.agent_combo)
        row1.addWidget(self.agent_widget)
        
        # Mode
        self.mode_widget = QWidget()
        self.mode_widget.setStyleSheet("background-color: #ffffff;")
        mode_layout = QVBoxLayout(self.mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_label = QLabel("评估模式")
        mode_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 8px; background-color: white;")
        mode_label.setMinimumHeight(22)
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["spec", "freeform"])
        self.mode_combo.setCurrentText("spec")
        self.mode_combo.setMinimumHeight(48)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                background-color: #ffffff;
                color: #1f2937;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #93c5fd;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #64748b;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e5e7eb;
                background-color: #ffffff;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
                padding: 6px;
                border-radius: 8px;
            }
        """)
        mode_layout.addWidget(self.mode_combo)
        row1.addWidget(self.mode_widget)
        
        # API Key
        self.api_key_widget = QWidget()
        self.api_key_widget.setStyleSheet("background-color: #ffffff;")
        api_key_layout = QVBoxLayout(self.api_key_widget)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_label = QLabel("JUDGE_API_KEY（必填）")
        api_key_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 8px; background-color: white;")
        api_key_label.setMinimumHeight(22)
        api_key_layout.addWidget(api_key_label)
        
        api_key_input_widget = QWidget()
        api_key_input_layout = QHBoxLayout(api_key_input_widget)
        api_key_input_layout.setContentsMargins(0, 0, 0, 0)
        api_key_input_layout.setSpacing(8)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 JUDGE_API_KEY...")
        self.api_key_input.setMinimumHeight(48)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                background-color: #fafafa;
                color: #1f2937;
            }
            QLineEdit:hover {
                border-color: #93c5fd;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
            }
        """)
        # 加载已保存的 API Key
        saved_api_key = get_judge_api_key()
        if saved_api_key:
            self.api_key_input.setText(saved_api_key)
        
        self.toggle_api_key_btn = QPushButton("👁")
        self.toggle_api_key_btn.setMinimumWidth(48)
        self.toggle_api_key_btn.setMinimumHeight(48)
        self.toggle_api_key_btn.setMaximumWidth(48)
        self.toggle_api_key_btn.setMaximumHeight(48)
        self.toggle_api_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self.toggle_api_key_btn.clicked.connect(self.toggle_api_key_visibility)
        self.toggle_api_key_btn.setToolTip("显示/隐藏")
        
        api_key_input_layout.addWidget(self.api_key_input, stretch=1)
        api_key_input_layout.addWidget(self.toggle_api_key_btn)
        api_key_layout.addWidget(api_key_input_widget)
        row1.addWidget(self.api_key_widget, stretch=1)
        
        # 安装焦点事件过滤器
        self.api_key_input.installEventFilter(self)
        
        # 并发数
        self.concurrency_widget = QWidget()
        self.concurrency_widget.setStyleSheet("background-color: #ffffff;")
        concurrency_layout = QVBoxLayout(self.concurrency_widget)
        concurrency_layout.setContentsMargins(0, 0, 0, 0)
        concurrency_label = QLabel("并发数")
        concurrency_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 8px; background-color: white;")
        concurrency_label.setMinimumHeight(22)
        concurrency_layout.addWidget(concurrency_label)
        
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setMinimum(1)
        self.concurrency_spin.setMaximum(20)
        self.concurrency_spin.setValue(5)
        self.concurrency_spin.setMinimumHeight(48)
        self.concurrency_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                color: #1f2937;
                background-color: #ffffff;
                min-width: 110px;
            }
            QSpinBox:hover {
                border-color: #93c5fd;
            }
            QSpinBox:focus {
                border-color: #3b82f6;
            }
        """)
        concurrency_layout.addWidget(self.concurrency_spin)
        row1.addWidget(self.concurrency_widget)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # 评估维度（只在 building agent 时显示）
        self.dimensions_widget = QWidget()
        self.dimensions_widget.setStyleSheet("background-color: #ffffff;")
        dim_v_layout = QVBoxLayout(self.dimensions_widget)
        dim_v_layout.setContentsMargins(0, 18, 0, 0)
        dim_v_layout.setSpacing(12)
        
        dimensions_label = QLabel("评估维度")
        dimensions_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 6px; background-color: white;")
        dimensions_label.setMinimumHeight(22)
        dim_v_layout.addWidget(dimensions_label)
        
        dim_layout = QHBoxLayout()
        dim_layout.setSpacing(20)
        
        self.dim_table_checkbox = QCheckBox("📊 Table（表格）")
        self.dim_table_checkbox.setChecked(True)
        self.dim_permission_checkbox = QCheckBox("🔐 Permission（权限）")
        self.dim_permission_checkbox.setChecked(True)
        self.dim_workflow_checkbox = QCheckBox("🔄 Workflow（工作流）")
        self.dim_workflow_checkbox.setChecked(True)
        self.dim_formula_checkbox = QCheckBox("🔢 Formula（公式）")
        self.dim_formula_checkbox.setChecked(True)
        self.dim_dashboard_checkbox = QCheckBox("📈 Dashboard（仪表盘）")
        self.dim_dashboard_checkbox.setChecked(True)
        
        for checkbox in [self.dim_table_checkbox, self.dim_permission_checkbox, 
                        self.dim_workflow_checkbox, self.dim_formula_checkbox,
                        self.dim_dashboard_checkbox]:
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #1f2937;
                    font-size: 13px;
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #d1d5db;
                    border-radius: 5px;
                    background-color: #f9fafb;
                }
                QCheckBox::indicator:hover {
                    border-color: #3b82f6;
                }
                QCheckBox::indicator:checked {
                    background-color: #3b82f6;
                    border-color: #3b82f6;
                }
            """)
            dim_layout.addWidget(checkbox)
        
        dim_layout.addStretch()
        dim_v_layout.addLayout(dim_layout)
        layout.addWidget(self.dimensions_widget)
        
        return group
    
    def _create_result_section(self):
        """创建结果显示区域"""
        group = QGroupBox("📝 评测结果")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 16px;
                color: #1f2937;
                border: none;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 20px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 24px;
                padding: 0 14px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 28, 28, 20)
        
        # 结果输出
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("响应体将显示在这里...")
        self.result_text.setMinimumHeight(30)
        
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 16px;
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
        
        # 关闭
        self.close_btn = QPushButton("关闭")
        self.close_btn.setMinimumWidth(90)
        self.close_btn.setMinimumHeight(36)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #3b82f6;
                border-color: #3b82f6;
                background-color: #eff6ff;
            }
            QPushButton:pressed {
                background-color: #dbeafe;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        # 停止
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setMinimumWidth(90)
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f87171, stop:1 #ef4444);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
            }
            QPushButton:disabled {
                background: #fecaca;
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # 开始
        self.start_btn = QPushButton("开始评估")
        self.start_btn.setMinimumWidth(100)
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60a5fa, stop:1 #3b82f6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:disabled {
                background: #bfdbfe;
            }
        """)
        self.start_btn.clicked.connect(self.on_start_judge)
        layout.addWidget(self.start_btn)
        
        return widget
    
    # === 事件处理 ===
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于监听焦点事件"""
        if obj == self.api_key_input and event.type() == event.Type.FocusOut:
            # 失去焦点时自动保存
            api_key = self.api_key_input.text().strip()
            if api_key:
                set_judge_api_key(api_key)
        return super().eventFilter(obj, event)
    
    def on_agent_changed(self, agent):
        """Agent 类型切换处理"""
        if agent == "building":
            self.dimensions_widget.setVisible(True)
            self.mode_widget.setVisible(True)
        elif agent in ["permission", "table", "dashboard", "workflow", "block"]:
            self.dimensions_widget.setVisible(False)
            self.mode_widget.setVisible(False)
        else:
            self.dimensions_widget.setVisible(False)
            self.mode_widget.setVisible(True)
    
    def on_select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择测试用例文件", 
            "", 
            "CSV and Excel Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx);;Excel Files (*.xls);;All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            self.file_path_input.setText(file_path)
    
    def on_start_judge(self):
        """开始评估"""
        if not self.file_path:
            QMessageBox.warning(self, "提示", "请先选择测试用例文件！")
            return
        
        # 获取配置
        agent = self.agent_combo.currentText()
        mode = self.mode_combo.currentText()
        concurrency = self.concurrency_spin.value()
        
        # 获取评估维度（仅 building agent）
        dimensions = None
        if agent == "building":
            dimensions = []
            if self.dim_table_checkbox.isChecked():
                dimensions.append("table")
            if self.dim_permission_checkbox.isChecked():
                dimensions.append("permission")
            if self.dim_workflow_checkbox.isChecked():
                dimensions.append("workflow")
            if self.dim_formula_checkbox.isChecked():
                dimensions.append("formula")
            if self.dim_dashboard_checkbox.isChecked():
                dimensions.append("dashboard")
            
            if not dimensions:
                QMessageBox.warning(self, "提示", "请至少选择一个评估维度！")
                return
        
        # 更新 UI 状态
        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.select_file_btn.setEnabled(False)
        
        # 读取测试用例
        self.append_result("状态", {"message": "正在读取测试用例文件..."})
        
        try:
            # Dashboard, Workflow, Block, Permission, Table 使用特殊的用例格式（支持多轮对话）
            if agent == "dashboard":
                cases = self.dashboard_batch_judge.read_cases_from_file(self.file_path)
            elif agent == "workflow":
                cases = self.workflow_batch_judge.read_cases_from_file(self.file_path)
            elif agent == "block":
                cases = self.block_batch_judge.read_cases_from_file(self.file_path)
            elif agent == "permission":
                cases = self.permission_batch_judge.read_cases_from_file(self.file_path)
            elif agent == "table":
                cases = self.table_batch_judge.read_cases_from_file(self.file_path)
            else:
                cases = self.batch_judge.read_cases_from_file(self.file_path)
            self.append_result("读取结果", {"message": f"成功读取 {len(cases)} 个测试用例", "case_count": len(cases)})
        except Exception as e:
            self.append_result("错误", {"message": f"读取文件失败：{str(e)}"})
            self.is_processing = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.select_file_btn.setEnabled(True)
            return
        
        # 发送批量请求
        self.append_result("状态", {"message": "正在发送批量请求..."})
        
        # Dashboard, Workflow, Block, Permission 使用特殊的请求格式（不需要 mode，options 在 case 里面，支持多轮对话）
        if agent == "dashboard":
            result = self.dashboard_batch_judge.send_request(
                cases=cases,
                agent=agent,
                concurrency=concurrency
            )
        elif agent == "workflow":
            result = self.workflow_batch_judge.send_request(
                cases=cases,
                agent=agent,
                concurrency=concurrency
            )
        elif agent == "block":
            result = self.block_batch_judge.send_request(
                cases=cases,
                agent=agent,
                concurrency=concurrency
            )
        elif agent == "permission":
            result = self.permission_batch_judge.send_request(
                cases=cases,
                agent=agent,
                concurrency=concurrency
            )
        elif agent == "table":
            # Table agent 使用特殊格式（不需要 mode，options 在顶层，支持多轮对话）
            result = self.table_batch_judge.send_request(
                cases=cases,
                agent=agent,
                concurrency=concurrency
            )
        elif agent == "building":
            # Building agent 需要 dimensions 和 mode
            result = self.batch_judge.send_request(
                cases=cases,
                agent=agent,
                dimensions=dimensions,
                concurrency=concurrency,
                mode=mode
            )
        else:
            # 其他 agent 使用标准格式（不需要 mode）
            result = self.batch_judge.send_request(
                cases=cases,
                agent=agent,
                dimensions=None,
                concurrency=concurrency,
                mode=mode
            )
        
        self.append_result("批量测试响应", result)
        
        # 恢复 UI 状态
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
    
    def on_stop(self):
        """停止"""
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
        self.append_result("状态", {"message": "已停止"})
    
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
    
    def toggle_api_key_visibility(self):
        """切换 API Key 显示/隐藏"""
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_api_key_btn.setText("🙈")
            self.toggle_api_key_btn.setToolTip("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.toggle_api_key_btn.setText("👁")
            self.toggle_api_key_btn.setToolTip("显示")
        
        # 自动保存
        api_key = self.api_key_input.text().strip()
        if api_key:
            set_judge_api_key(api_key)
