from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QTabWidget, QCheckBox, QLineEdit, QListWidgetItem, QFormLayout,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import os
import json
from pathlib import Path

class ClusterConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('创建/编辑集群')
        self.resize(800, 600)

        # Nya! 左侧：可用服务器列表
        self.available_servers_list = QListWidget()
        available_servers_layout = QVBoxLayout()
        available_servers_layout.addWidget(QLabel('可用服务器实例:'))
        available_servers_layout.addWidget(self.available_servers_list)

        # Nya! 中间：添加/移除按钮和集群内服务器列表
        self.add_to_cluster_btn = QPushButton('加入集群 ↑')
        self.remove_from_cluster_btn = QPushButton('↓ 移出集群')
        middle_buttons_layout = QVBoxLayout()
        middle_buttons_layout.addStretch()
        middle_buttons_layout.addWidget(self.add_to_cluster_btn)
        middle_buttons_layout.addWidget(self.remove_from_cluster_btn)
        middle_buttons_layout.addStretch()

        # Nya! 右侧：使用 QTabWidget 实现标签页配置
        self.config_tabs = QTabWidget()

        # -- 调度标签页 --
        dispatch_tab = QWidget()
        dispatch_layout = QVBoxLayout()
        self.dispatch_server_list = QListWidget() # Nya! 用于显示集群内的调度服务器
        self.use_internal_dispatch_checkbox = QCheckBox('使用内置调度')
        # Nya! 调度标签页底部的特定布局 (根据设计图调整)
        dispatch_bottom_widget = QWidget()
        dispatch_bottom_layout = QHBoxLayout(dispatch_bottom_widget)
        dispatch_bottom_layout.setContentsMargins(0, 10, 0, 0)
        dispatch_bottom_layout.addWidget(self.use_internal_dispatch_checkbox) # Nya! 复选框放左边
        dispatch_bottom_layout.addStretch()
        dispatch_bottom_layout.addWidget(QLabel('选定为调度服务器:')) # Nya! 标签放中间

        dispatch_layout.addWidget(QLabel("调度服务器列表:"))
        dispatch_layout.addWidget(self.dispatch_server_list)
        dispatch_layout.addStretch()
        dispatch_layout.addWidget(dispatch_bottom_widget)
        dispatch_tab.setLayout(dispatch_layout)
        self.config_tabs.addTab(dispatch_tab, '调度')

        # -- 游戏标签页 --
        game_tab = QWidget()
        game_layout = QVBoxLayout()
        self.game_server_list = QListWidget() # Nya! 用于显示集群内的游戏服务器
        # Nya! 游戏标签页底部的按钮 (根据设计图调整)
        game_bottom_widget = QWidget()
        game_bottom_layout = QHBoxLayout(game_bottom_widget)
        game_bottom_layout.setContentsMargins(0, 10, 0, 0)
        self.config_title_btn = QPushButton('配置标题')
        game_bottom_layout.addWidget(self.config_title_btn) # Nya! 配置标题按钮放左边
        game_bottom_layout.addStretch()

        game_layout.addWidget(QLabel("游戏服务器列表:"))
        game_layout.addWidget(self.game_server_list)
        game_layout.addStretch()
        game_layout.addWidget(game_bottom_widget) # Nya! 添加底部特定控件
        game_tab.setLayout(game_layout)
        self.config_tabs.addTab(game_tab, '游戏')

        # -- 其它标签页 --
        other_tab = QWidget()
        other_layout = QVBoxLayout()
        self.cluster_name_input = QLineEdit()
        self.cluster_name_input.setPlaceholderText('请输入集群名称')
        self.game_server_count_label = QLabel('游戏服务器总数: N/A')
        # Nya! 其它标签页底部的按钮 (根据设计图调整)
        other_bottom_widget = QWidget()
        other_bottom_layout = QHBoxLayout(other_bottom_widget)
        other_bottom_layout.setContentsMargins(0, 10, 0, 0)
        other_bottom_layout.addStretch()

        # Nya! 调整布局 (根据设计图，名称输入框在列表上面)
        other_layout.addWidget(QLabel('请输入集群名称:')) # Nya! 使用 QLabel + QLineEdit
        other_layout.addWidget(self.cluster_name_input)
        other_layout.addStretch()
        other_layout.addWidget(self.game_server_count_label, alignment=QtCore.Qt.AlignRight)
        other_layout.addWidget(other_bottom_widget) # Nya! 添加底部特定控件
        other_tab.setLayout(other_layout)
        self.config_tabs.addTab(other_tab, '其它')

        # Nya! 主布局：三栏水平排列
        main_columns_layout = QHBoxLayout()
        main_columns_layout.addLayout(available_servers_layout, 1)
        main_columns_layout.addLayout(middle_buttons_layout)
        main_columns_layout.addWidget(self.config_tabs, 2)

        # Nya! 底部按钮 (主对话框底部)
        self.ok_btn = QPushButton('确定')
        self.cancel_btn = QPushButton('取消')
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.addStretch()
        bottom_btn_layout.addWidget(self.ok_btn)
        bottom_btn_layout.addWidget(self.cancel_btn)

        # Nya! 整体布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(main_columns_layout)
        main_layout.addLayout(bottom_btn_layout)
        self.setLayout(main_layout)

        # Nya! 信号连接
        self.ok_btn.clicked.connect(self.accept) # Nya! 主确定按钮
        self.cancel_btn.clicked.connect(self.reject) # Nya! 主取消按钮
        self.add_to_cluster_btn.clicked.connect(self.add_server_to_cluster)
        self.remove_from_cluster_btn.clicked.connect(self.remove_server_from_cluster)
        self.config_title_btn.clicked.connect(self.open_title_config) # Nya! 保留标题配置按钮的连接

        self.setModal(True)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Nya! 存储服务器配置的地方
        self.server_configs = {}
        # Nya! 加载可用服务器列表 (示例)
        self.load_available_servers()
        # Nya! 当标签页内的列表变化时，更新游戏服务器计数
        self.game_server_list.model().rowsInserted.connect(self.update_game_server_count)
        self.game_server_list.model().rowsRemoved.connect(self.update_game_server_count)

    def get_instance_role(self, server_name):
        """Nya! 获取服务器实例的角色信息喵~
        
        Args:
            server_name (str): 服务器实例名称
            
        Returns:
            str: 服务器角色，可能是'DISPATCH_ONLY', 'GAME'或'STANDALONE'
        """
        # Nya! 尝试从父窗口获取角色信息
        if self.parent() and hasattr(self.parent(), 'get_instance_role'):
            return self.parent().get_instance_role(server_name)
        # Nya! 否则返回STANDALONE作为默认值
        return 'STANDALONE'

    def add_server_to_cluster(self):
        """Nya! 将选中的可用服务器添加到对应的标签页列表中喵~"""
        selected_items = self.available_servers_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            server_name = item.text() # Nya! 获取原始服务器名

            # Nya! 检查是否已在调度或游戏列表中 (避免重复添加)
            in_dispatch = any(self.dispatch_server_list.item(i).text() == server_name for i in range(self.dispatch_server_list.count()))
            in_game = any(self.game_server_list.item(i).text() == server_name for i in range(self.game_server_list.count()))

            if in_dispatch or in_game:
                # Nya! 如果已经在任一列表，只从可用列表移除即可
                self.available_servers_list.takeItem(self.available_servers_list.row(item))
                continue

            # Nya! 从可用列表移除
            self.available_servers_list.takeItem(self.available_servers_list.row(item))

            # Nya! 根据角色添加到对应的标签页列表
            role = self.get_instance_role(server_name)
            added_to_list = False
            if role == 'DISPATCH_ONLY' or role == 'STANDALONE':
                self.dispatch_server_list.addItem(QListWidgetItem(server_name))
                added_to_list = True
            if role == 'GAME' or role == 'STANDALONE':
                self.game_server_list.addItem(QListWidgetItem(server_name))
                added_to_list = True
            # Nya! 如果不是调度或游戏角色，也暂时不加到特定列表，但已从可用列表移除

        # Nya! 更新游戏服务器计数
        self.update_game_server_count()

    def remove_server_from_cluster(self):
        """Nya! 将选中的集群服务器从当前标签页列表移回到可用列表中喵~"""
        current_tab_index = self.config_tabs.currentIndex()
        active_list = None
        if current_tab_index == 0: # Nya! 调度标签页
            active_list = self.dispatch_server_list
        elif current_tab_index == 1: # Nya! 游戏标签页
            active_list = self.game_server_list
        # Nya! 其它标签页没有服务器列表可以移除

        if not active_list:
            return

        selected_items = active_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            server_name = item.text()

            # Nya! 从当前活动列表移除
            active_list.takeItem(active_list.row(item))

            # Nya! 检查是否还在另一个列表 (调度/游戏) 中
            in_dispatch = any(self.dispatch_server_list.item(i).text() == server_name for i in range(self.dispatch_server_list.count()))
            in_game = any(self.game_server_list.item(i).text() == server_name for i in range(self.game_server_list.count()))

            # Nya! 如果两个列表都不包含该服务器了，则添加回可用列表
            if not in_dispatch and not in_game:
                new_item = QListWidgetItem(server_name)
                role = self.get_instance_role(server_name)
                if role != 'STANDALONE':
                    new_item.setBackground(QtCore.Qt.lightGray)
                    new_item.setToolTip('此服务器可能已属于其他集群或配置为集群角色，加入新集群将覆盖其配置喵~')
                else:
                    new_item.setBackground(QtCore.Qt.white)
                    new_item.setToolTip('')
                self.available_servers_list.addItem(new_item)

        # Nya! 更新游戏服务器计数
        self.update_game_server_count()

    def update_game_server_count(self):
        """Nya! 更新游戏服务器总数标签喵~"""
        count = self.game_server_list.count()
        self.game_server_count_label.setText(f'游戏服务器总数: {count}')

    def load_available_servers(self):
        """Nya! 加载可用的服务器实例列表喵~"""
        # Nya! 这里只是示例，需要替换成实际加载服务器实例的逻辑喵~
        # Nya! 假设我们有一些服务器实例
        servers = [f'server_{i}' for i in range(20)]
        self.available_servers_list.clear() # Nya! 先清空列表
        for server in servers:
            item = QListWidgetItem(server)
            # Nya! 假设根据配置判断角色和状态
            role = self.get_instance_role(server) # Nya! 获取角色
            if role != 'STANDALONE':
                 item.setBackground(QtCore.Qt.lightGray)
                 item.setToolTip('此服务器可能已属于其他集群或配置为集群角色，加入新集群将覆盖其配置喵~')
            else:
                 item.setBackground(QtCore.Qt.white)
            self.available_servers_list.addItem(item)

    def open_title_config(self):
        """Nya! 打开标题配置对话框喵~"""
        print("Nya! 打开标题配置喵~")
        # Nya! TODO: 实现打开标题配置对话框的逻辑

    def accept(self):
        """Nya! 处理确定按钮点击事件，保存集群配置喵~"""
        print("Nya! 主确定按钮点击，开始保存集群配置喵~")
        # Nya! 1. 验证集群名称
        cluster_name = self.cluster_name_input.text().strip()
        if not cluster_name:
            QMessageBox.warning(self, "错误", "集群名称不能为空喵！")
            self.config_tabs.setCurrentIndex(2) # Nya! 切换到"其它"标签页
            self.cluster_name_input.setFocus()
            return
        # Nya! TODO: 添加更严格的集群名称验证 (例如：只能英文、数字、下划线)

        # Nya! 2. 获取调度服务器配置
        dispatch_servers = [self.dispatch_server_list.item(i).text() for i in range(self.dispatch_server_list.count())]
        use_internal = self.use_internal_dispatch_checkbox.isChecked()
        # Nya! 验证调度配置 (例如：必须至少有一个调度服务器，除非使用内置)
        if not use_internal and not dispatch_servers:
            QMessageBox.warning(self, "错误", "请至少指定一个调度服务器，或勾选\"使用内置调度\"喵！")
            self.config_tabs.setCurrentIndex(0) # Nya! 切换到"调度"标签页
            return

        # Nya! 3. 获取游戏服务器配置
        game_servers = [self.game_server_list.item(i).text() for i in range(self.game_server_list.count())]
        # Nya! TODO: 获取游戏服务器标题配置 (如果实现了的话)

        # Nya! 4. 组合集群配置数据
        cluster_config = {
            "name": cluster_name,
            "title": "", # Nya! TODO: 需要添加集群标题输入框
            "dispatch_servers": dispatch_servers,
            "use_internal_dispatch": use_internal,
            "game_servers": game_servers,
            # Nya! TODO: 添加其他需要的配置项
        }
        print(f"Nya! 准备保存的集群配置: {cluster_config}")

        # Nya! 5. 调用父窗口的方法来保存或更新集群
        if self.parent() and hasattr(self.parent(), 'save_cluster_config'):
            self.parent().save_cluster_config(cluster_config)

        # Nya! 如果保存成功，再调用 super().accept()
        super().accept()


class ClusterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('集群管理')
        
        # Nya! 获取根目录路径
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Nya! 创建布局
        layout = QVBoxLayout()
        
        # Nya! 添加控件
        self.cluster_list = QListWidget()
        self.cluster_list.setSelectionMode(QListWidget.SingleSelection)
        
        # Nya! 按钮布局
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton('创建集群')
        self.edit_btn = QPushButton('编辑集群')
        self.delete_btn = QPushButton('删除集群')
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        # Nya! 添加控件到布局
        layout.addWidget(QLabel('集群列表:'))
        layout.addWidget(self.cluster_list)
        layout.addLayout(btn_layout)
        
        # Nya! 设置布局
        self.setLayout(layout)
        
        # Nya! 连接信号
        self.create_btn.clicked.connect(self.create_cluster)
        self.edit_btn.clicked.connect(self.edit_cluster)
        self.delete_btn.clicked.connect(self.delete_cluster)
        
        # Nya! 加载现有集群
        self.load_clusters()
    
    def get_instance_role(self, server_name):
        """Nya! 获取服务器实例角色信息喵~

        Args:
            server_name (str): 服务器实例名称

        Returns:
            str: 服务器角色（DISPATCH_ONLY/GAME/STANDALONE）喵~
        """
        config_path = os.path.join(self.root_dir, 'Servers', server_name, 'JGSL', 'Config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('cluster_role', 'STANDALONE')
        except Exception as e:
            print(f"Nya! 读取服务器角色配置出错: {e}喵~")
            return 'STANDALONE'
    
    def load_clusters(self):
        """Nya! 加载现有集群列表喵~"""
        self.cluster_list.clear()
        # Nya! TODO: 从配置文件加载集群列表
        # Nya! 示例数据
        clusters = ['集群1', '集群2', '集群3']
        for cluster in clusters:
            self.cluster_list.addItem(cluster)
    
    def create_cluster(self):
        """Nya! 创建新集群喵~"""
        dialog = ClusterConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Nya! 保存集群配置
            print("Nya! 集群创建成功喵~")
            self.load_clusters()  # Nya! 重新加载集群列表
    
    def edit_cluster(self):
        """Nya! 编辑现有集群喵~"""
        selected = self.cluster_list.currentItem()
        if not selected:
            QMessageBox.warning(self, '警告', '请先选择一个集群喵~')
            return
        
        dialog = ClusterConfigDialog(self)
        # Nya! TODO: 加载选中集群的配置到对话框
        if dialog.exec_() == QDialog.Accepted:
            # Nya! 更新集群配置
            print(f"Nya! 集群 {selected.text()} 更新成功喵~")
            self.load_clusters()  # Nya! 重新加载集群列表
    
    def delete_cluster(self):
        """Nya! 删除集群喵~"""
        selected = self.cluster_list.currentItem()
        if not selected:
            QMessageBox.warning(self, '警告', '请先选择一个集群喵~')
            return
        
        reply = QMessageBox.question(self, '确认', f'确定要删除集群 {selected.text()} 吗？\n这不会删除集群中的服务器实例，但会清除它们的集群配置喵~', 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Nya! TODO: 删除集群配置
            print(f"Nya! 集群 {selected.text()} 删除成功喵~")
            self.load_clusters()  # Nya! 重新加载集群列表
    
    def save_cluster_config(self, config):
        """Nya! 保存集群配置喵~
        
        Args:
            config (dict): 集群配置信息
        """
        # Nya! TODO: 实现保存集群配置的逻辑
        print(f"Nya! 保存集群配置: {config}喵~")
        
        # Nya! 1. 保存集群配置到文件
        # clusters_dir = os.path.join(self.root_dir, 'JGSL', 'Clusters')
        # os.makedirs(clusters_dir, exist_ok=True)
        # cluster_file = os.path.join(clusters_dir, f"{config['name']}.json")
        # with open(cluster_file, 'w', encoding='utf-8') as f:
        #     json.dump(config, f, ensure_ascii=False, indent=4)
        
        # Nya! 2. 更新服务器实例的集群角色配置
        # for server in config['dispatch_servers']:
        #     if server in config['game_servers']:
        #         role = 'STANDALONE'
        #     else:
        #         role = 'DISPATCH_ONLY'
        #     self._update_server_role(server, role, config['name'])
        
        # for server in config['game_servers']:
        #     if server not in config['dispatch_servers']:
        #         self._update_server_role(server, 'GAME', config['name'])
    
    def _update_server_role(self, server_name, role, cluster_name):
        """Nya! 更新服务器实例的角色配置喵~
        
        Args:
            server_name (str): 服务器实例名称
            role (str): 新角色
            cluster_name (str): 所属集群名称
        """
        # Nya! TODO: 实现更新服务器角色的逻辑
        config_path = os.path.join(self.root_dir, 'Servers', server_name, 'JGSL', 'Config.json')
        try:
            # Nya! 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Nya! 读取现有配置或创建新配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Nya! 更新角色和集群信息
            config['cluster_role'] = role
            config['cluster_name'] = cluster_name
            
            # Nya! 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            print(f"Nya! 已更新服务器 {server_name} 的角色为 {role}，所属集群为 {cluster_name}喵~")
        except Exception as e:
            print(f"Nya! 更新服务器角色配置出错: {e}喵~")