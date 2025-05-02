from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QEvent
import qdarkstyle
from launch_tab import LaunchTab
from monitor_tab import MonitorTab
from manage_tab import ManageTab
from download_tab import DownloadTab
from settings_tab import SettingsTab
from cluster_tab import ClusterTab
from about_tab import AboutTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('JimGrasscutterServerLauncher')
        self.setGeometry(100, 100, 800, 600)

        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # 初始化各个功能页
        self.launch_tab = LaunchTab()
        self.monitor_tab = MonitorTab()
        self.manage_tab = ManageTab()
        self.download_tab = DownloadTab()
        self.settings_tab = SettingsTab()
        self.cluster_tab = ClusterTab()
        self.about_tab = AboutTab()

        # 添加选项卡
        self.tabs.addTab(self.launch_tab, '启动')
        self.tabs.addTab(self.monitor_tab, '监控')
        self.tabs.addTab(self.manage_tab, '管理')
        self.tabs.addTab(self.cluster_tab, '集群')
        self.tabs.addTab(self.download_tab, '下载')
        self.tabs.addTab(self.settings_tab, '设置')
        self.tabs.addTab(self.about_tab, '关于')

        # 设置主布局
        self.setCentralWidget(self.tabs)

        # 应用样式
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def cleanup_and_exit(self):
        self.launch_tab.cleanup()
        QApplication.quit()

    def closeEvent(self, event):
        self.cleanup_and_exit()
        event.accept()