from pathlib import Path
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QDialog, QFormLayout, QLineEdit, QListWidgetItem, QCheckBox, QPushButton, QLabel, QTabWidget
from PyQt5.QtCore import pyqtSignal, QRegExp
from PyQt5.QtGui import QValidator, QRegExpValidator
import json

class ClusterConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('集群配置')
        self.tab_widget = QTabWidget()
        
        # 基本配置选项卡
        basic_tab = QWidget()
        self.dispatch_server_list = QListWidget()
        self.game_servers_list = QListWidget()
        self.game_servers_list.setSelectionMode(QListWidget.MultiSelection)
        
        # 游戏服务器配置表格
        self.server_configs = {}
        
        form_layout = QFormLayout()
        form_layout.addRow('调度服务器：', self.dispatch_server_list)
        form_layout.addRow('游戏服务器：', self.game_servers_list)
        
        # 游戏服务器选择变更事件
        self.game_servers_list.itemSelectionChanged.connect(self.update_server_configs)
        
        basic_tab.setLayout(form_layout)
        self.tab_widget.addTab(basic_tab, '基本配置')
        
        # 游戏服务器配置选项卡
        game_config_tab = QWidget()
        self.game_server_port_edit = QLineEdit()
        self.role_limit_edit = QLineEdit()
        self.role_limit_edit.setValidator(QRegExpValidator(QRegExp('[0-9]+')))
        self.role_limit_error_label = QLabel('')
        self.role_limit_error_label.setStyleSheet('color: red;')
        self.banned_accounts_list = QListWidget()
        self.banned_accounts_list.setSelectionMode(QListWidget.MultiSelection)
        self.whitelisted_accounts_list = QListWidget()
        self.whitelisted_accounts_list.setSelectionMode(QListWidget.MultiSelection)
        
        form_layout = QFormLayout()
        form_layout.addRow('游戏服务器端口：', self.game_server_port_edit)
        form_layout.addRow('角色限制：', self.role_limit_edit)
        form_layout.addRow(self.role_limit_error_label)
        form_layout.addRow('封禁账号：', self.banned_accounts_list)
        form_layout.addRow('白名单账号：', self.whitelisted_accounts_list)
        
        game_config_tab.setLayout(form_layout)
        self.tab_widget.addTab(game_config_tab, '游戏服务器配置')
        
        # 服务器独立配置选项卡
        self.server_config_tab = QWidget()
        self.server_config_layout = QVBoxLayout()
        self.server_config_tab.setLayout(self.server_config_layout)
        self.tab_widget.addTab(self.server_config_tab, '服务器独立配置')
        
        self.ok_btn = QPushButton('确定')
        self.cancel_btn = QPushButton('取消')
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        
    def update_server_configs(self):
        # 清空当前配置布局
        while self.server_config_layout.count():
            item = self.server_config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 为每个选中的服务器创建配置项
        selected_servers = [item.text() for item in self.game_servers_list.selectedItems()]
        for server in selected_servers:
            if server not in self.server_configs:
                self.server_configs[server] = {
                    'name': QLineEdit(),
                    'title': QLineEdit(),
                    'name_error': QLabel(''),
                    'title_error': QLabel('')
                }
                self.server_configs[server]['name'].setValidator(QRegExpValidator(QRegExp('[a-zA-Z0-9_]+')))
                self.server_configs[server]['name_error'].setStyleSheet('color: red;')
                self.server_configs[server]['title_error'].setStyleSheet('color: red;')
            
            # 创建服务器配置组
            group_box = QWidget()
            form_layout = QFormLayout()
            form_layout.addRow(f'服务器 {server} 集群名称（英文）：', self.server_configs[server]['name'])
            form_layout.addRow(self.server_configs[server]['name_error'])
            form_layout.addRow(f'服务器 {server} 显示标题：', self.server_configs[server]['title'])
            form_layout.addRow(self.server_configs[server]['title_error'])
            group_box.setLayout(form_layout)
            
            self.server_config_layout.addWidget(group_box)

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
        
        # 监听游戏服务器选择变更，确保在创建新集群时初始化服务器配置
        dialog.game_servers_list.itemSelectionChanged.connect(lambda: self.init_new_server_configs(dialog))
        
        if dialog.exec_() == QDialog.Accepted:
            if self.validate_dialog(dialog):
                self.apply_cluster_config(dialog)
            else:
                dialog.exec_()
                
    def init_new_server_configs(self, dialog):
        # 为新选择的服务器初始化配置
        selected_servers = [item.text() for item in dialog.game_servers_list.selectedItems()]
        for server in selected_servers:
            if server in dialog.server_configs:
                continue
                
            # 初始化配置
            dialog.update_server_configs()
            
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
        if dialog.exec_() == QDialog.Accepted:
            if self.validate_dialog(dialog):
                self.apply_cluster_config(dialog, cluster_name)
            else:
                dialog.exec_()
        
    def select_current_cluster(self, dialog, cluster_name):
        # 选中当前集群的调度服务器
        dispatch_server = self.get_dispatch_server(cluster_name)
        for i in range(dialog.dispatch_server_list.count()):
            if dialog.dispatch_server_list.item(i).text() == dispatch_server:
                dialog.dispatch_server_list.setCurrentRow(i)
                break
        # 选中当前集群的游戏服务器
        game_servers = self.get_game_servers(cluster_name)
        for instance in game_servers:
            for i in range(dialog.game_servers_list.count()):
                if dialog.game_servers_list.item(i).text() == instance:
                    dialog.game_servers_list.item(i).setSelected(True)
        
        # 加载每个游戏服务器的配置
        dialog.update_server_configs()
        for instance in game_servers:
            if instance in dialog.server_configs:
                # 从JGSL配置中获取集群名称和标题
                instance_path = Path(__file__).parent.parent / 'Servers' / instance
                try:
                    with open(instance_path / 'JGSL/Config.json', 'r') as f:
                        jgsl_config = json.load(f)
                        dialog.server_configs[instance]['name'].setText(jgsl_config.get('cluster_name', cluster_name))
                        dialog.server_configs[instance]['title'].setText(jgsl_config.get('cluster_title', self.get_cluster_title(cluster_name)))
                except Exception:
                    # 如果读取失败，使用默认值
                    dialog.server_configs[instance]['name'].setText(cluster_name)
                    dialog.server_configs[instance]['title'].setText(self.get_cluster_title(cluster_name))
        
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
    
    def get_cluster_title(self, cluster_name, server_name=None):
        # 如果指定了服务器名称，优先从该服务器的JGSL配置中获取标题
        if server_name:
            server_path = Path(__file__).parent.parent / 'Servers' / server_name / 'JGSL/Config.json'
            try:
                with open(server_path, 'r') as f:
                    jgsl_config = json.load(f)
                    if 'cluster_title' in jgsl_config and jgsl_config.get('cluster_name') == cluster_name:
                        return jgsl_config['cluster_title']
            except Exception:
                pass
        
        # 如果没有指定服务器或者从服务器配置中获取失败，从调度服务器配置中获取
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
    
    def validate_dialog(self, dialog):
        dispatch_server = dialog.dispatch_server_list.currentItem()
        game_servers = dialog.game_servers_list.selectedItems()
        
        if not dispatch_server:
            for server in dialog.server_configs:
                dialog.server_configs[server]['name_error'].setText('请选择调度服务器')
            return False
        elif not game_servers:
            for server in dialog.server_configs:
                dialog.server_configs[server]['name_error'].setText('请选择游戏服务器')
            return False
        
        # 验证每个服务器的配置
        is_valid = True
        for server_name, config in dialog.server_configs.items():
            # 只验证被选中的服务器
            if server_name not in [item.text() for item in game_servers]:
                continue
                
            name = config['name'].text()
            title = config['title'].text()
            
            if not name:
                config['name_error'].setText('集群名称不能为空')
                is_valid = False
            else:
                config['name_error'].setText('')
                
            if not title:
                config['title_error'].setText('显示标题不能为空')
                is_valid = False
            else:
                config['title_error'].setText('')
        
        return is_valid
    
    def apply_cluster_config(self, dialog, old_cluster_name=None):
        is_new_cluster = old_cluster_name is None
        dispatch_server = dialog.dispatch_server_list.currentItem().text()
        game_servers = [item.text() for item in dialog.game_servers_list.selectedItems()]

        # 更新调度服务器配置
        dispatch_path = Path(__file__).parent.parent / 'Servers' / dispatch_server
        try:
            with open(dispatch_path / 'config.json', 'r+') as f:
                config = json.load(f)
                if is_new_cluster:
                    config['server']['runMode'] = 'DISPATCH_ONLY'
                    config['server']['dispatch']['regions'] = []
                
                # 清空现有区域配置
                config['server']['dispatch']['regions'] = []
                
                # 为每个游戏服务器添加区域配置
                regions = []
                for i, instance in enumerate(game_servers):
                    if instance in dialog.server_configs:
                        server_config = dialog.server_configs[instance]
                        regions.append({
                            'Name': server_config['name'].text(),
                            'Title': server_config['title'].text(),
                            'Ip': '127.0.0.1',
                            'Port': 22101 + i
                        })
                
                config['server']['dispatch']['regions'] = regions
                f.seek(0)
                json.dump(config, f, indent=2)
                f.truncate()
        except Exception as e:
            for server in dialog.server_configs:
                dialog.server_configs[server]['name_error'].setText(f'调度服务器配置失败：{str(e)}')
            return

        # 更新游戏服务器配置
        for i, instance in enumerate(game_servers):
            if instance not in dialog.server_configs:
                continue
                
            instance_path = Path(__file__).parent.parent / 'Servers' / instance
            server_config = dialog.server_configs[instance]
            cluster_name = server_config['name'].text()
            
            try:
                # 验证集群角色
                with open(instance_path / 'JGSL/Config.json', 'r') as f:
                    jgsl_config = json.load(f)
                    if jgsl_config['cluster_role'] != 'GAME':
                        continue
                
                # 更新JGSL配置
                with open(instance_path / 'JGSL/Config.json', 'r+') as f:
                    jgsl_config = json.load(f)
                    jgsl_config['cluster_name'] = cluster_name
                    jgsl_config['cluster_title'] = server_config['title'].text()
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
            except Exception as e:
                server_config['name_error'].setText(f'游戏服务器 {instance} 配置失败：{str(e)}')
                return
        
        if not is_new_cluster:
            # 清理旧集群配置
            self.delete_cluster(old_cluster_name, True)
            
        self.config_updated.emit()
        dialog.accept()
    
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
                try:
                    with open(jgsl_path, 'r+') as f:
                        jgsl_config = json.load(f)
                        if jgsl_config.get('cluster_name') == cluster_name:
                            # 移除集群名称和标题
                            if 'cluster_name' in jgsl_config:
                                jgsl_config.pop('cluster_name')
                            if 'cluster_title' in jgsl_config:
                                jgsl_config.pop('cluster_title')
                            f.seek(0)
                            json.dump(jgsl_config, f, indent=2)
                            f.truncate()
                except Exception:
                    continue
                    
                # 清理调度服务器配置
                try:
                    config_path = d / 'config.json'
                    with open(config_path, 'r+') as f:
                        config = json.load(f)
                        if config['server']['runMode'] == 'DISPATCH_ONLY':
                            regions = config['server']['dispatch']['regions']
                            # 移除所有与该集群相关的区域
                            regions_to_remove = []
                            for region in regions:
                                if region['Name'] == cluster_name:
                                    regions_to_remove.append(region)
                            
                            for region in regions_to_remove:
                                regions.remove(region)
                                
                            f.seek(0)
                            json.dump(config, f, indent=2)
                            f.truncate()
                            
                            # 如果没有区域了，将模式改为STANDALONE
                            if not keep_dispatch_server and not regions:
                                config['server']['runMode'] = 'STANDALONE'
                                f.seek(0)
                                json.dump(config, f, indent=2)
                                f.truncate()
                except Exception:
                    continue