from loguru import logger
try:
    from PyQt5.QtWidgets import QApplication
    from main_window import MainWindow
    import signal
    import sys


    def main():
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        signal.signal(signal.SIGINT, lambda s, f: window.cleanup_and_exit())
        sys.exit(app.exec_())


    if __name__ == '__main__':
        main()
except Exception as e:
    logger.critical(f"有未处理的异常: {e}")
    input("发生严重错误，按任意键退出")
    sys.exit(1)