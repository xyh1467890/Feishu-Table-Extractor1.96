APP_STYLE = """
QMainWindow, QWidget#central {
    background-color: #f5f7fa;
}
QWidget#left_panel {
    background-color: #ffffff;
    border-right: 1px solid #e4e7ed;
}
QWidget#right_panel {
    background-color: #f5f7fa;
}
QLabel {
    color: #303133;
    font-family: -apple-system, "Microsoft YaHei", "Segoe UI", sans-serif;
}
QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #303133;
    letter-spacing: 1px;
}
QLabel#subtitle {
    font-size: 13px;
    color: #909399;
}
QLabel#section_title {
    font-size: 13px;
    font-weight: 700;
    color: #606266;
    margin-top: 15px;
    margin-bottom: 5px;
}
QLabel#info_text {
    color: #606266;
    font-size: 13px;
    line-height: 1.5;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 10px 14px;
    color: #303133;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #409eff;
    background-color: #ffffff;
}
QPushButton {
    background-color: #ffffff;
    color: #606266;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #ecf5ff;
    color: #409eff;
    border-color: #c6e2ff;
}
QPushButton:pressed {
    background-color: #ecf5ff;
    color: #3a8ee6;
    border-color: #3a8ee6;
}
QPushButton#primary_btn {
    background-color: #409eff;
    color: white;
    font-size: 14px;
    padding: 14px;
    border-radius: 8px;
    border: none;
}
QPushButton#primary_btn:hover {
    background-color: #66b1ff;
}
QPushButton#primary_btn:pressed {
    background-color: #3a8ee6;
}
QPushButton#primary_btn:disabled {
    background-color: #a0cfff;
    color: #ffffff;
}
QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #909399;
    padding: 8px 16px 8px 0px;
    font-size: 14px;
    font-weight: 600;
    border-bottom: 2px solid transparent;
    margin-right: 16px;
}
QTabBar::tab:selected {
    color: #409eff;
    border-bottom: 2px solid #409eff;
}
QTabBar::tab:hover:!selected {
    color: #303133;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 16px;
    color: #303133;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #dcdfe6;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #c0c4cc;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #dcdfe6;
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #c0c4cc;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QCheckBox {
    color: #606266;
    font-size: 13px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #409eff;
    border: 1px solid #409eff;
}
"""
