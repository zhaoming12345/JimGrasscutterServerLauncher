import json
from loguru import logger
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

class TitleEditorDialog(QDialog):
    def __init__(self, parent=None, instance_path=None, current_title=""):
        super().__init__(parent)
        self.setWindowTitle(self.tr('编辑实例标题'))
        self.setGeometry(200, 200, 400, 150)
        self.setWindowModality(Qt.ApplicationModal)
        self.instance_path = instance_path
        self.current_title = current_title

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 标题输入框
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel(self.tr('实例标题:')))
        self.title_input = QLineEdit(self.current_title)
        self.title_input.setPlaceholderText(self.tr('请输入实例标题'))
        title_layout.addWidget(self.title_input)
        main_layout.addLayout(title_layout)

        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.tr('保存'))
        self.save_button.clicked.connect(self.save_title)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton(self.tr('取消'))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def save_title(self):
        new_title = self.title_input.text().strip()
        if not new_title:
            QMessageBox.warning(self, self.tr('警告'), self.tr('标题不能为空！'))
            return

        if self.instance_path:
            config_file_path = f"{self.instance_path}/config.json"
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 查找并更新Title
                if 'dispatch' in config_data and 'regions' in config_data['dispatch']:
                    for region in config_data['dispatch']['regions']:
                        if 'name' in region and region['name'] == f"os_{self.instance_path.split('/')[-1]}":
                            region['title'] = new_title
                            break
                    else:
                        # 如果没有找到匹配的region，则添加一个新的
                        new_region = {
                            "name": f"os_{self.instance_path.split('/')[-1]}",
                            "title": new_title,
                            "Ip": config_data['server']['game']['accessAddress'],
                            "Port": config_data['server']['game']['accessPort']
                        }
                        config_data['dispatch']['regions'].append(new_region)
                else:
                    # 如果dispatch或regions不存在，则创建它们
                    config_data.setdefault('dispatch', {}).setdefault('regions', []).append({
                        "name": f"os_{self.instance_path.split('/')[-1]}",
                        "title": new_title,
                        "Ip": config_data['server']['game']['accessAddress'],
                        "Port": config_data['server']['game']['accessPort']
                    })

                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                logger.info(self.tr(f"实例标题已保存到 {config_file_path}"))
                self.accept()
            except Exception as e:
                logger.error(self.tr(f"保存实例标题失败: {e}"))
                QMessageBox.critical(self, self.tr('错误'), self.tr(f'保存标题失败: {e}'))
        else:
            QMessageBox.critical(self, self.tr('错误'), self.tr('无法获取实例路径，无法保存标题。'))
            logger.error(self.tr("实例路径未提供，无法保存标题。"))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = TitleEditorDialog(instance_path=None, current_title='')
    dialog = TitleEditorDialog(instance_path='Servers/4.0.1', current_title='JimServer')
    if dialog.exec_() == QDialog.Accepted:
        logger.info("标题已保存")
    else:
        logger.info("取消保存")
    sys.exit(app.exec_())