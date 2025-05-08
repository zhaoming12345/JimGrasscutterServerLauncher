from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QEvent, QProcess
from PyQt5.QtGui import QIcon
import qdarkstyle
from launch_tab import LaunchTab
from monitor_tab import MonitorTab
from manage_tab import ManageTab
from download_tab import DownloadTab
from settings_tab import SettingsTab
from cluster_tab import ClusterTab
from database_tab import DatabaseTab
from about_tab import AboutTab
from loguru import logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('JimGrasscutterServerLauncher')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('Assets/JGSL-Logo.ico'))

        # 用于存储运行中的 QProcess 对象，以 PID 为键
        self.running_processes: dict[int, QProcess] = {}

        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # 初始化各个功能页
        self.launch_tab = LaunchTab()
        self.monitor_tab = MonitorTab()
        self.manage_tab = ManageTab()
        self.download_tab = DownloadTab()
        self.settings_tab = SettingsTab()
        self.cluster_tab = ClusterTab()
        self.database_tab = DatabaseTab()
        self.about_tab = AboutTab()

        # 连接 LaunchTab 的信号到 MainWindow 的方法
        self.launch_tab.process_created.connect(self.register_process)
        self.launch_tab.process_finished_signal.connect(self.unregister_process)

        # 选项卡
        self.tabs.addTab(self.launch_tab, '启动')
        self.tabs.addTab(self.monitor_tab, '监控')
        self.tabs.addTab(self.manage_tab, '管理')
        self.tabs.addTab(self.database_tab, '数据库')
        self.tabs.addTab(self.cluster_tab, '集群')
        self.tabs.addTab(self.download_tab, '下载')
        self.tabs.addTab(self.settings_tab, '设置')
        self.tabs.addTab(self.about_tab, '关于')

        # 设置主布局
        self.setCentralWidget(self.tabs)

        # 应用样式
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # 新增:注册 QProcess 对象
    def register_process(self, pid: int, process: QProcess):
        if pid in self.running_processes:
            logger.warning(f"尝试注册已存在的 PID: {pid}")
        else:
            logger.info(f"注册进程 PID: {pid}")
            self.running_processes[pid] = process

    # 新增:注销 QProcess 对象
    def unregister_process(self, pid: int):
        if pid in self.running_processes:
            logger.info(f"注销进程 PID: {pid}")
            del self.running_processes[pid]
        else:
            logger.warning(f"尝试注销不存在的 PID: {pid}")

    # 新增:获取 QProcess 对象
    def get_process(self, pid: int) -> QProcess | None:
        process = self.running_processes.get(pid)
        if not process:
            logger.warning(f"无法找到 PID: {pid} 对应的 QProcess 对象")
        return process

    def cleanup_and_exit(self):
        self.launch_tab.cleanup()
        QApplication.quit()

    def closeEvent(self, event):
        self.cleanup_and_exit()
        event.accept()

    def on_tab_changed(self, index):
        current_tab = self.tabs.widget(index)
        if isinstance(current_tab, MonitorTab):
            current_tab.scan_running_instances()
        elif isinstance(current_tab, ManageTab):
            current_tab.refresh_server_list()