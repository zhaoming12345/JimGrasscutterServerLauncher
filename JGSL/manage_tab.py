from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QInputDialog, QDialog, QFormLayout, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
import os, json
from pathlib import Path
from loguru import logger
import shutil
import psutil
from config_editor import ConfigEditorDialog


class InstanceConfigDialog(QDialog):
    def __init__(self, parent=None, config=None, root_dir=None):
        super().__init__(parent)
        self.root_dir = root_dir or parent.root_dir
        self.setWindowTitle('实例配置')
        self.setWindowModality(Qt.ApplicationModal)
        layout = QFormLayout()

        self.global_config = self.load_global_config()

        self.instance_name = QLineEdit()
        self.java_path = QLineEdit()
        self.java_path.setPlaceholderText('留空使用全局配置')
        self.jvm_pre_args = QLineEdit()
        self.jvm_pre_args.setPlaceholderText('留空使用全局配置')
        self.jvm_post_args = QLineEdit()
        self.jvm_post_args.setPlaceholderText('留空使用全局配置')
        self.grasscutter_path = QLineEdit()
        self.grasscutter_path.setPlaceholderText('Grasscutter.jar路径')
        self.grasscutter_path_btn = QPushButton('选择Grasscutter.jar')
        self.grasscutter_path_btn.clicked.connect(self.select_grasscutter_path)

        layout.addRow('实例名称:', self.instance_name)
        layout.addRow('Java.exe路径:', self.java_path)
        layout.addRow('jvm前置参数:', self.jvm_pre_args)
        layout.addRow('jvm后置参数:', self.jvm_post_args)
        layout.addRow('Grasscutter.jar路径:', self.grasscutter_path)
        layout.addRow(self.grasscutter_path_btn)

        self.accept_btn = QPushButton('保存')
        self.accept_btn.clicked.connect(self.accept)
        layout.addRow(self.accept_btn)

        self.setLayout(layout)

        if config:
            self.instance_name.setText(config.get('instance_name', ''))
            java_path = config.get('java_path', '')
            if java_path == '':
                java_path = self.global_config['default_java_version']
                if java_path == '':
                    java_path = self.find_latest_java()
            self.java_path.setText(java_path)
            self.jvm_pre_args.setText(' '.join(config.get('jvm_pre_args', [])))
            self.jvm_post_args.setText(' '.join(config.get('jvm_post_args', [])))
            self.grasscutter_path.setText(config.get('grasscutter_path', ''))

    def load_global_config(self):
        logger.info('加载全局配置')
        global_config_path = os.path.join(self.root_dir, 'Config', 'JGSL.json')
        if os.path.exists(global_config_path):
            with open(global_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'default_java_version': '',
            'default_jvm_pre_args': [],
            'default_jvm_post_args': []
        }

    def find_latest_java(self):
        java_dir = os.path.join(self.root_dir, 'Java')
        if not os.path.exists(java_dir):
            return ''
        latest_version = None
        latest_version_path = None
        for version_dir in os.listdir(java_dir):
            version_path = os.path.join(java_dir, version_dir)
            if os.path.isdir(version_path):
                java_executable = os.path.join(version_path, 'bin', 'java.exe')
                if os.path.exists(java_executable):
                    if latest_version is None or version_dir > latest_version:
                        latest_version = version_dir
                        latest_version_path = java_executable
        return latest_version_path or ''

    def select_grasscutter_path(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择Grasscutter.jar文件', '', 'JAR文件 (*.jar)')
        if file_name:
            self.grasscutter_path.setText(file_name)
            logger.debug(f'选择Grasscutter路径: {file_name}')

    def accept(self):
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        instance_name = self.instance_name.text()
        if any(char in instance_name for char in invalid_chars):
            QMessageBox.warning(self, '错误', '实例名称包含非法字符: \\ / : * ? " < > |')
            return
        if not Path(self.grasscutter_path.text()).exists():
            QMessageBox.warning(self, '错误', 'Grasscutter.jar路径不存在')
            return
        self.instance_config = {
            'instance_name': instance_name,
            'java_path': self.java_path.text() or self.global_config['default_java_version'],
            'jvm_pre_args': self.jvm_pre_args.text().split() or self.global_config['default_jvm_pre_args'],
            'jvm_post_args': self.jvm_post_args.text().split() or self.global_config.get('default_jvm_post_args', []),
            'grasscutter_path': self.grasscutter_path.text(),
            'cluster_role': 'HYBRID'  # 确保新实例默认为独立角色
        }
        super().accept()


class ManageTab(QWidget):
    def __init__(self):
        super().__init__()
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.server_list = QListWidget()
        self.create_btn = QPushButton('新建实例')
        self.edit_config_btn = QPushButton('编辑Grasscutter配置文件')
        self.edit_btn = QPushButton('修改实例配置')
        self.delete_btn = QPushButton('删除实例')

        layout = QVBoxLayout()
        layout.addWidget(self.server_list)
        layout.addWidget(self.create_btn)
        layout.addWidget(self.edit_config_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

        # 自动扫描实例
        servers_path = os.path.join(self.root_dir, "Servers")
        if not os.path.exists(servers_path):
            os.makedirs(servers_path, exist_ok=True)
        valid_servers = [
            instance_name for instance_name in os.listdir(servers_path)
            if os.path.isdir(os.path.join(servers_path, instance_name)) and os.path.exists(os.path.join(servers_path, instance_name, 'JGSL', 'Config.json'))
        ]
        self.server_list.addItems(valid_servers)

        self.create_btn.clicked.connect(self.create_instance)
        self.edit_config_btn.clicked.connect(self.open_config_editor)
        self.edit_btn.clicked.connect(self.edit_instance)
        self.delete_btn.clicked.connect(self.delete_instance)

    def create_instance(self):
        dialog = InstanceConfigDialog(self, root_dir=self.root_dir)
        if dialog.exec_():
            self.save_config(dialog.instance_config, is_new=True)

    def open_config_editor(self):
        current_item = self.server_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '警告', '请选择一个实例')
            return
        instance_name = current_item.text()
        instance_dir = os.path.join(self.root_dir, 'Servers', instance_name)
        config_path = os.path.join(instance_dir, 'config.json')
        if not os.path.exists(config_path):
            QMessageBox.warning(self, '错误', 'config.json不存在')
            return
        config_editor = ConfigEditorDialog(self, config_path)
        config_editor.exec_()

    def edit_instance(self):
        current_item = self.server_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '警告', '请选择一个实例')
            return
        instance_name = current_item.text()
        instance_dir = os.path.join(self.root_dir, 'Servers', instance_name)
        config_path = os.path.join(instance_dir, 'JGSL', 'Config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"实例配置文件 {config_path} 解析失败: {e}")
            QMessageBox.warning(self, '错误', f"实例配置文件 {config_path} 解析失败")
            return
        except Exception as e:
            logger.error(f"读取实例配置文件 {config_path} 时发生未知错误: {e}")
            QMessageBox.warning(self, '错误', f"读取实例配置文件 {config_path} 时发生未知错误")
            return
        config['instance_name'] = instance_name
        original_instance_name = instance_name # 保存原始实例名称
        dialog = InstanceConfigDialog(self, config, root_dir=self.root_dir)
        if dialog.exec_():
            self.save_config(dialog.instance_config, is_new=False, original_instance_name=original_instance_name)

    def save_config(self, config, is_new=True, original_instance_name=None): # 添加 original_instance_name 参数
        logger.info('正在保存实例配置')
        new_instance_name = config['instance_name']
        new_instance_dir = os.path.join(self.root_dir, 'Servers', new_instance_name)
        config_dir = os.path.join(new_instance_dir, 'JGSL')
        config_path = os.path.join(config_dir, 'Config.json')

        # 处理重命名逻辑
        if not is_new and original_instance_name and original_instance_name != new_instance_name:
            original_instance_dir = os.path.join(self.root_dir, 'Servers', original_instance_name)
            if os.path.exists(original_instance_dir):
                try:
                    # 检查新名称是否已存在
                    if os.path.exists(new_instance_dir):
                        QMessageBox.warning(self, '错误', f'实例名称 "{new_instance_name}" 已存在，请选择其他名称。')
                        return
                    # 重命名文件夹
                    shutil.move(original_instance_dir, new_instance_dir)
                    logger.info(f'实例文件夹已从 "{original_instance_name}" 重命名为 "{new_instance_name}"')
                except OSError as e:
                    logger.error(f'重命名实例文件夹失败: {e}')
                    QMessageBox.warning(self, '错误', f'重命名实例文件夹失败: {e}')
                    return
            else:
                logger.warning(f'原始实例文件夹 "{original_instance_dir}" 不存在，无法重命名。将创建新实例。')
                # 如果原始文件夹不存在，则按新实例处理，确保目录存在
                os.makedirs(config_dir, exist_ok=True)
        else:
            # 确保新实例或未重命名的实例目录存在
            os.makedirs(config_dir, exist_ok=True)

        if is_new and os.path.exists(os.path.join(new_instance_dir, 'JGSL', 'Config.json')):
            # 检查新实例的配置文件是否存在，而不是检查目录是否存在
            # 因为重命名逻辑可能已经创建了目录
            QMessageBox.warning(self, '错误', '实例已存在')
            return
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            if is_new:
                # 创建标准目录结构
                dirs_to_create = ['resources', 'data', 'packets', 'plugins', 'cache']
                for directory in dirs_to_create:
                    dir_path = Path(new_instance_dir) / directory # 使用新的实例目录
                    try:
                        dir_path.mkdir(exist_ok=True)
                    except (PermissionError, FileExistsError) as e:
                        logger.error(f"创建目录 {dir_path} 失败: {e}")
                        QMessageBox.warning(self, '错误', f"创建目录 {dir_path} 失败: {e}")
                logger.success("成功创建实例目录结构")
            self.refresh_server_list()
            logger.success(f'实例 {new_instance_name} 配置已保存') # 使用新的实例名称
        except OSError as e:
            logger.error(f"保存实例配置文件失败 | 路径: {config_path} | 错误: {str(e)}")
            QMessageBox.warning(self, '错误', f'保存配置文件失败，请检查目录权限\n错误详情: {str(e)}')
            return

    def refresh_server_list(self):
        self.server_list.clear()
        servers_path = os.path.join(self.root_dir, 'Servers')
        if os.path.exists(servers_path):
            for instance_name in os.listdir(servers_path):
                instance_dir = os.path.join(servers_path, instance_name)
                if os.path.isdir(instance_dir) and os.path.exists(os.path.join(instance_dir, 'JGSL')):
                    self.server_list.addItem(instance_name)

    def delete_instance(self):
        current_item = self.server_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '警告', '请选择一个实例')
            return
        instance_name = current_item.text()
        instance_dir = os.path.join(self.root_dir, 'Servers', instance_name)
        reply = QMessageBox.question(self, '确认删除', f'确定要删除实例 {instance_name} 吗？此操作将删除所有相关文件且无法恢复。', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 检查实例是否正在运行
                instance_running = False
                for proc in psutil.process_iter(['name']):
                    try:
                        if instance_name in proc.info['name']:
                            instance_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                if instance_running:
                    # 终止实例进程
                    for proc in psutil.process_iter(['name']):
                        try:
                            if instance_name in proc.info['name']:
                                proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                            logger.error(f"终止进程 {proc.info['name']} 失败: {e}")
                            QMessageBox.warning(self, '错误', f"终止进程 {proc.info['name']} 失败: {e}")
                            return
                shutil.rmtree(instance_dir)
                logger.success(f'实例 {instance_name} 已删除')
                QMessageBox.information(self, '成功', f'实例 {instance_name} 已删除')
                self.refresh_server_list()
            except Exception as e:
                logger.error(f"删除实例 {instance_name} 失败: {e}")
                QMessageBox.warning(self, '错误', f"删除实例 {instance_name} 失败: {e}")