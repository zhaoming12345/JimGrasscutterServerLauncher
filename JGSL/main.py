import sys
import os
from loguru import logger
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QFontDatabase, QFont
from main_window import MainWindow
import signal

def main():
    def load_font_async(font_path):
        try:
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"字体文件 {font_path} 不存在")
            
            if not os.access(font_path, os.R_OK):
                raise PermissionError(f"字体文件 {font_path} 不可读")
                
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id == -1:
                raise ValueError(f"字体文件 {font_path} 无效或损坏")
                
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if not font_families:
                raise ValueError(f"字体文件 {font_path} 不包含有效字体")
            
            return font_families[0]
        except Exception as e:
            logger.warning(f"字体加载失败: {e}")
            return "Arial"
            
    font_path = r"./Assets/HanYiWenHei-85W-Heavy.ttf"
    app = QApplication(sys.argv)
    font_family = load_font_async(font_path)
    font = QFont(font_family)
    font.setPointSize(10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    signal.signal(signal.SIGINT, lambda s, f: window.cleanup_and_exit())
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()