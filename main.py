import sys
import os

# 添加项目根目录到路径，让子模块能正常导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import FeishuBitableApp


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后
        base_path = sys._MEIPASS
    else:
        # 开发时
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path('icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = FeishuBitableApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
