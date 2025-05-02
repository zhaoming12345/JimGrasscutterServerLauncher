from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QDialog, QFormLayout, QLineEdit, QListWidgetItem, QCheckBox
from PyQt5.QtCore import pyqtSignal
import json
from pathlib import Path

class ClusterConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('集群配置')
        
        self.name_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.dispatch_server_list = QListWidget()
        self.game_servers_list = QListWidget()
        self.game_servers_list.setSelectionMode(QListWidget.MultiSelection)
        
        form_layout = QFormLayout()
        form_layout.addRow('集群名称（英文）：', self.name_edit)
        form_layout.addRow('显示标题：', self.title_edit)
        form_layout.addRow('调度服务器：', self.dispatch_server_list)
        form_layout.addRow('游戏服务器：', self.game_servers_list)
        
        self.ok_btn = QPushButton('确定')
        self.cancel_btn = QPushButton('取消')
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QListWidget

class ClusterTab(QWidget):
    config_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.cluster_list = QListWidget()
        self.create_btn = QPushButton('创建集群')
        self.edit_btn = QPushButton('配置集群')
        self.delete_btn = QPushButton('删除集群')
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.cluster_list)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        
        self.create_btn.clicked.connect(self.show_create_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_cluster)
        
    def load_instances(self):
        root_dir = Path(__file__).parent.parent
        return [d.name for d in (root_dir / 'Servers').iterdir() 
                if d.is_dir() and (d / 'JGSL/Config.json').exists()]
        
    def show_create_dialog(self):
        dialog = ClusterConfigDialog(self)
        dialog.dispatch_server_list.addItems(self.load_instances())
        dialog.game_servers_list.addItems(self.load_instances())
        
        if dialog.exec_() == QDialog.Accepted:
            self.apply_cluster_config(dialog)
            
    def show_edit_dialog(self):
        current_item = self.cluster_list.currentItem()
        if not current_item:
            return
        
        cluster_name = current_item.text()
        dialog = ClusterConfigDialog(self)
        dialog.name_edit.setText(cluster_name)
        dialog.title_edit.setText(self.get_cluster_title(cluster_name))
        dialog.dispatch_server_list.addItems(self.load_instances())
        dialog.game_servers_list.addItems(self.load_instances())
        self.select_current_cluster(dialog, cluster_name)
        dialog.ok_btn.clicked.connect(lambda: self.apply_cluster_config(dialog, cluster_name))
        dialog.exec_()
        
    def select_current_cluster(self, dialog, cluster_name):
        # 选中当前集群的调度服务器
        dispatch_server = self.get_dispatch_server(cluster_name)
        for i in range(dialog.dispatch_server_list.count()):
            if dialog.dispatch_server_list.item(i).text() == dispatch_server:
                dialog.dispatch_server_list.setCurrentRow(i)
                break
        # 选中当前集群的游戏服务器
        for instance in self.get_game_servers(cluster_name):
            for i in range(dialog.game_servers_list.count()):
                if dialog.game_servers_list.item(i).text() == instance:
                    dialog.game_servers_list.item(i).setSelected(True)
        
    def get_dispatch_server(self, cluster_name):
        root_dir = Path(__file__).parent.parent
        for d in (root_dir / 'Servers').iterdir():
            if d.is_dir():
                path = d / 'config.json'
                with open(path, 'r') as f:
                    config = json.load(f)
                    if config['server']['runMode'] == 'DISPATCH_ONLY':
                        regions = config['server']['dispatch']['regions']
                        for region in regions:
                            if region['Name'] == cluster_name:
                                return d.name
        return None
    
    def get_game_servers(self, cluster_name):
        root_dir = Path(__file__).parent.parent
        game_servers = []
        for d in (root_dir / 'Servers').iterdir():
            if d.is_dir():
                path = d / 'JGSL/Config.json'
                with open(path, 'r') as f:
                    jgsl_config = json.load(f)
                    if jgsl_config['cluster_name'] == cluster_name:
                        game_servers.append(d.name)
        return game_servers
    
    def get_cluster_title(self, cluster_name):
        dispatch_server = self.get_dispatch_server(cluster_name)
        if dispatch_server:
            path = Path(__file__).parent.parent / 'Servers' / dispatch_server / 'config.json'
            with open(path, 'r') as f:
                config = json.load(f)
                regions = config['server']['dispatch']['regions']
                for region in regions:
                    if region['Name'] == cluster_name:
                        return region['Title']
        return ''
    
    def apply_cluster_config(self, dialog, old_cluster_name=None):
        is_new_cluster = old_cluster_name is None
        cluster_name = dialog.name_edit.text()
        dispatch_server = dialog.dispatch_server_list.currentItem().text()
        game_servers = [item.text() for item in dialog.game_servers_list.selectedItems()]

        # 更新调度服务器配置
        dispatch_path = Path(__file__).parent.parent / 'Servers' / dispatch_server
        with open(dispatch_path / 'config.json', 'r+') as f:
            config = json.load(f)
            if is_new_cluster:
                config['server']['runMode'] = 'DISPATCH_ONLY'
                config['server']['dispatch']['regions'] = []
            regions = config['server']['dispatch']['regions']
            regions = [
                {
                    'Name': cluster_name,
                    'Title': dialog.title_edit.text(),
                    'Ip': '127.0.0.1',
                    'Port': 22101 + i
                } for i in range(len(game_servers))
            ]
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()

        # 更新游戏服务器配置
        for i, instance in enumerate(game_servers):
            instance_path = Path(__file__).parent.parent / 'Servers' / instance
            # 验证集群角色
            with open(instance_path / 'JGSL/Config.json', 'r') as f:
                jgsl_config = json.load(f)
                if jgsl_config['cluster_role'] != 'GAME':
                    continue
            
            # 更新JGSL配置
            with open(instance_path / 'JGSL/Config.json', 'r+') as f:
                jgsl_config = json.load(f)
                jgsl_config['cluster_name'] = cluster_name
                f.seek(0)
                json.dump(jgsl_config, f, indent=2)
                f.truncate()
            
            # 更新Grasscutter配置
            with open(instance_path / 'config.json', 'r+') as f:
                config = json.load(f)
                config['server']['runMode'] = 'GAME_ONLY'
                config['server']['game']['bindPort'] = 22101 + i
                f.seek(0)
                json.dump(config, f, indent=2)
                f.truncate()
        
        if not is_new_cluster:
            # 清理旧集群配置
            self.delete_cluster(old_cluster_name, True)
            
        self.config_updated.emit()
    
    def delete_cluster(self, cluster_name=None, keep_dispatch_server=False):
        if cluster_name is None:
            current_item = self.cluster_list.currentItem()
            if not current_item:
                return
            cluster_name = current_item.text()
            
        # 遍历所有实例，清理集群配置
        root_dir = Path(__file__).parent.parent
        for d in (root_dir / 'Servers').iterdir():
            if d.is_dir():
                jgsl_path = d / 'JGSL/Config.json'
                with open(jgsl_path, 'r+') as f:
                    jgsl_config = json.load(f)
                    if jgsl_config['cluster_name'] == cluster_name:
                        jgsl_config.pop('cluster_name')
                        f.seek(0)
                        json.dump(jgsl_config, f, indent=2)
                        f.truncate()
                config_path = d / 'config.json'
                with open(config_path, 'r+') as f:
                    config = json.load(f)
                    if config['server']['runMode'] == 'DISPATCH_ONLY':
                        regions = config['server']['dispatch']['regions']
                        for region in regions:
                            if region['Name'] == cluster_name:
                                regions.remove(region)
                                f.seek(0)
                                json.dump(config, f, indent=2)
                                f.truncate()
                        if not keep_dispatch_server and not regions:
                            config['server']['runMode'] = 'STANDALONE'
                            f.seek(0)
                            json.dump(config, f, indent=2)
                            f.truncate()