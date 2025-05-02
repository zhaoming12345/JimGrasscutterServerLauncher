from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QFont, QIcon

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # 项目标题
        title = QLabel('JimGrasscutterServerLauncher')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        # 项目链接
        self.add_link(layout, 
                    QIcon('Assets/JGSL-Logo.ico'),
                    '本项目GitHub仓库',
                    'https://github.com/Jimmy32767255/JimGrasscutterServerLauncher')

        # Grasscutter链接
        self.add_link(layout,
                    QIcon('Assets/Grasscutter-Logo.ico'),
                    'Grasscutter项目',
                    'https://github.com/Grasscutters/Grasscutter')

        self.setLayout(layout)

    def add_link(self, layout, icon, text, url):
        link_label = QLabel()
        link_label.setText(f'<html><a href="{url}">{text}</a></html>')
        link_label.setOpenExternalLinks(False)
        link_label.linkActivated.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        link_label.setStyleSheet('color: #2a82da; text-decoration: underline;')
        layout.addWidget(link_label)