from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QProgressBar, QLabel, QSlider, QHBoxLayout, QDialog, QDialogButtonBox, QMessageBox, QTreeWidget, QTreeWidgetItem,QSpacerItem,QSizePolicy,QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import requests
import shutil
import os
import json
from loguru import logger
import re
import patoolib
import patoolib.util

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    
    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.logger = logger
    
    def run(self):
        try:
            self.logger.info(f'开始下载 {self.url}')
            with requests.get(self.url, stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                try:
                    try:
                        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
                        test_file = os.path.join(os.path.dirname(self.save_path), 'test.tmp')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                    except Exception as e:
                        raise PermissionError(f'目录 {os.path.dirname(self.save_path)} 无写入权限: {e}')
                    with open(self.save_path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int(downloaded / total_size * 100)
                            self.logger.trace(f'下载进度 {progress}%')
                            self.progress_signal.emit(progress)
                    self.finished_signal.emit(self.save_path)
                except PermissionError as e:
                    self.logger.error(f'文件写入权限检查失败: {e}')
                    self.finished_signal.emit(f'Error: {str(e)}')
                except Exception as e:
                    self.logger.error(f'文件写入失败: {e}')
                    self.finished_signal.emit(f'Error: {str(e)}')
        except Exception as e:
            self.logger.error(f'下载失败: {e} | URL: {self.url}')
            self.finished_signal.emit(f'Error: {str(e)}')

class InstanceSelectionDialog(QDialog):
    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'选择 {category} 的目标实例')
        layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        self.refresh_instances()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.list_widget)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def refresh_instances(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        servers_path = os.path.join(root_dir, 'Servers')
        valid_servers = [
            name for name in os.listdir(servers_path)
            if os.path.isdir(os.path.join(servers_path, name)) 
            and os.path.exists(os.path.join(servers_path, name, 'JGSL', 'Config.json'))
        ]
        self.list_widget.clear()
        self.list_widget.addItems(valid_servers)

class DownloadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.logger = logger
        self.current_instance = None
        self.category_paths = {
            'MongoDB 数据库社区版': os.path.join(self.root_dir, 'Database'),
            'Java运行时': os.path.join(self.root_dir, 'Java'),
            '服务端核心': os.path.join(self.root_dir, 'Servers'),
            '插件': os.path.join(self.root_dir, 'Servers'),
            '卡池配置文件': os.path.join(self.root_dir, 'Servers')
        }
        self.category_subdirs = {
            '插件': 'plugins',
            '卡池配置文件': 'data'
        }
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('可下载组件')
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(15)
        self.tree.setStyleSheet('QTreeView::item { padding: 5px }')
        self._init_tree_data()
        
        self.download_btn = QPushButton('下载选中项目')
        self.download_queue = {}
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
        QProgressBar {
        margin-left: 0px;
        height: 20px;
        }
        """)
        self.status_label = QLabel('准备就绪')
        self.unavailable_label = QLabel('<h2 style="color: red;">⚠️ 该功能暂时不可用，正在修复中！</h2>')
        self.unavailable_label.setAlignment(Qt.AlignCenter)
        self.thread_count_label = QLabel('线程数: 64')
        self.thread_count_slider = QSlider(Qt.Horizontal)
        self.thread_count_slider.setRange(1, 128)
        self.thread_count_slider.setValue(64)
        self.thread_count_slider.valueChanged.connect(self.update_thread_count)
        self.thread_count = 64
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.addWidget(self.tree,7)
        layout.addWidget(self.unavailable_label)
        layout.addWidget(self.download_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(self.thread_count_label)
        thread_layout.addWidget(self.thread_count_slider, stretch=8)
        thread_layout.addStretch(1)
        thread_layout.setSpacing(10)
        layout.addLayout(thread_layout)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # 镜像源选择
        self.mirror_combo = QComboBox()
        self.load_mirrors()
        mirror_layout = QHBoxLayout()
        mirror_layout.addWidget(QLabel('GitHub镜像源(仅适用于GitHub资源):'))
        mirror_layout.addWidget(self.mirror_combo, stretch=1)
        layout.insertLayout(0, mirror_layout)
        
        self.setLayout(layout)
        self.download_btn.clicked.connect(self.start_download)
        self.mirror_combo.currentTextChanged.connect(self.on_mirror_changed)
    
    def load_mirrors(self):
        """从配置文件加载镜像源列表"""
        mirror_path = os.path.join(self.root_dir, 'Config', 'mirror-list.json')
        try:
            with open(mirror_path, 'r', encoding='utf-8') as f:
                mirrors = json.load(f)
                self.mirror_combo.clear()
                for mirror in mirrors:
                    self.mirror_combo.addItem(mirror['name'], mirror['url'])
        except Exception as e:
            self.logger.error(f'加载镜像源失败: {e}')
            self.mirror_combo.addItem('默认源', '')
    
    def on_mirror_changed(self, text):
        """镜像源变更处理"""
        self.current_mirror = self.mirror_combo.currentData()
    
    def _init_tree_data(self):
        # 从JSON配置文件加载下载列表
        config_path = os.path.join(self.root_dir, 'Config', 'download-list.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category in data['categories']:
                    root = QTreeWidgetItem(self.tree)
                    root.setText(0, category['name'])
                    for item in category['items']:
                        child = QTreeWidgetItem(root)
                        child.setText(0, item['name'])
                        child.setData(0, 1, item['url'])
        except Exception as e:
            self.logger.error(f'加载下载列表失败: {e}')
            QMessageBox.critical(self, '错误', '下载列表配置文件损坏或不存在')

    def update_thread_count(self, value):
        self.thread_count = value
        self.thread_count_label.setText(f'线程数: {value}')
    
    def start_download(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        save_path = os.path.join(self.root_dir, 'DownloadTemp')
        try:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            if not os.access(save_path, os.W_OK):
                raise PermissionError(f'目录 {save_path} 无写入权限')
        except Exception as e:
            self.logger.error(f'目录检查失败: {e}')
            QMessageBox.critical(self, '错误', f'目录检查失败: {e}')
            return
        for selected_item in selected_items:
            category = selected_item.parent().text(0)
            if category in ['服务端核心', '插件', '卡池配置文件']:
                dialog = InstanceSelectionDialog(category, self)
                dialog.refresh_instances()
                if not dialog.list_widget.count() > 0:
                    QMessageBox.warning(self, '警告', '请先创建至少一个实例')
                    return
                if dialog.exec_() == QDialog.Accepted:
                    if dialog.list_widget.currentItem():
                        instance_name = dialog.list_widget.currentItem().text()
                        self.current_instance = instance_name
                        save_path = os.path.join(save_path, instance_name)
                    else:
                        QMessageBox.warning(self, '警告', '未选择实例')
                        return
                else:
                    return
            selected = selected_item.text(0)
            save_path = os.path.join(save_path, selected)
            # 自动创建实例目录
            try:
                os.makedirs(save_path, exist_ok=True)
                self.logger.success(f'成功创建目录: {save_path}')
            except Exception as e:
                self.logger.error(f'目录创建失败: {e}')
                QMessageBox.critical(self, '错误', f'目录创建失败: {e}')
                return
            # 获取下载URL并应用镜像源
            url = selected_item.data(0, 1)
            if self.current_mirror:
                url = url.replace('https://github.com', self.current_mirror)
            thread = DownloadThread(url, save_path)
            thread.progress_signal.connect(self.update_progress)
            thread.finished_signal.connect(self.download_finished)
            thread.start()
            self.download_queue[thread] = thread
    
    def update_progress(self, value):
        total = sum(t.isRunning() for t in self.download_queue.values())
        if total > 0:
            progress = int(sum(t.progress_signal.emit(0) for t in self.download_queue.values()) / total)
        else:
            progress = 0
        self.progress_bar.setValue(progress)
    
    def download_finished(self, msg):
        if msg.startswith('Error'):
            self.logger.error(f'下载失败: {msg}')
            QMessageBox.critical(self, '错误', msg)
            self.status_label.setText(msg)
            self.progress_bar.reset()
            # 尝试移除下载队列中的线程
            for thread, _ in list(self.download_queue.items()): # 使用list进行迭代，因为我们可能会修改字典
                if not thread.isRunning():
                    del self.download_queue[thread]
            return

        self.logger.success(f'文件下载完成: {msg}')
        self.status_label.setText(f'文件下载完成: {msg}')
        self.progress_bar.reset()

        # 检查是否是压缩包
        file_path = msg
        file_name = os.path.basename(file_path)
        extracted_path = None
        is_archive = False
        archive_extensions = (".zip", ".rar", ".7z", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2") # 常见压缩包后缀
        if any(file_name.endswith(ext) for ext in archive_extensions):
            is_archive = True
            try:
                # 创建解压目标路径，例如 DownloadTemp/instance_name/archive_name_extracted
                extract_to_dir_name = f"{os.path.splitext(file_name)[0]}_extracted"
                extract_to_full_path = os.path.join(os.path.dirname(file_path), extract_to_dir_name)
                os.makedirs(extract_to_full_path, exist_ok=True)
                self.logger.info(f'开始解压 {file_path} 到 {extract_to_full_path}')
                self.status_label.setText(f'正在解压 {file_name}...') # 更新状态
                patoolib.extract_archive(file_path, outdir=extract_to_full_path, verbosity=-1) # verbosity=-1 静默模式
                self.logger.success(f'文件解压完成: {extract_to_full_path}')
                extracted_path = extract_to_full_path
                # 移动解压后的文件，然后删除原始压缩包和临时解压目录
                self.move_file(extracted_path, is_extracted_folder=True)
                try:
                    os.remove(file_path) # 删除原始压缩包
                    self.logger.info(f'已删除原始压缩包: {file_path}')
                except Exception as e:
                    self.logger.error(f'删除原始压缩包失败: {file_path},错误: {e}')

            except patoolib.util.PatoolError as e:
                self.logger.error(f'解压失败: {e}，将尝试直接移动原始文件。')
                QMessageBox.warning(self, '解压失败', f'解压 {file_name} 失败: {e}\n将尝试移动原始压缩包。')
                self.move_file(file_path) # 解压失败，移动原始文件
            except Exception as e:
                self.logger.error(f'解压过程中发生未知错误: {e}')
                QMessageBox.critical(self, '错误', f'解压 {file_name} 时发生未知错误: {e}')
                self.move_file(file_path) # 其他错误，也尝试移动原始文件
        else:
            self.move_file(file_path)

        # 尝试移除下载队列中的线程
        for thread, _ in list(self.download_queue.items()): # 使用list进行迭代，因为我们可能会修改字典
            if not thread.isRunning():
                del self.download_queue[thread]
    
    def move_file(self, source_path, is_extracted_folder=False):
        if not os.path.exists(source_path):
            self.logger.error(f'源文件/目录不存在: {source_path}')
            QMessageBox.critical(self, '错误', f'源文件/目录不存在: {source_path}')
            return

        source_path = os.path.normpath(source_path)
        original_file_name_for_tree_lookup = os.path.basename(source_path) # 用于在树中查找的原始文件名
        if is_extracted_folder:
            # 如果是解压后的文件夹，我们需要找到原始压缩包的名称来确定下载项目
            # 假设解压后的文件夹名为 'xxx_extracted', 原始文件名为 'xxx.zip'
            if original_file_name_for_tree_lookup.endswith('_extracted'):
                base_name = original_file_name_for_tree_lookup[:-len('_extracted')]
                # 尝试匹配所有可能的压缩包后缀
                possible_archive_extensions = (".zip", ".rar", ".7z", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".jar")
                found_original = False
                for ext in possible_archive_extensions:
                    # 检查DownloadTemp目录下是否存在原始压缩包名，以确定selected_item
                    # 这里的逻辑是，selected_item的text(0)是下载列表中的名称，它可能不带后缀，或者带特定后缀
                    # 我们需要一种方式从解压后的文件夹名反推回下载列表中的项目名
                    # 一个简单的方法是，假设下载列表中的名称就是不带任何已知压缩后缀的文件名
                    # 或者，如果下载项本身就是带后缀的，那我们直接用那个名字
                    # 当前实现中，selected_item.text(0) 就是下载列表中的名字，比如 "grasscutter.jar"
                    # 而下载下来的文件名可能是 "grasscutter.jar"
                    # 解压后可能是 "grasscutter_extracted"
                    # 我们需要通过 "grasscutter_extracted" 找到树中的 "grasscutter.jar" 项
                    # 或者，如果下载项是 "SomePlugin" (url 指向 zip), 下载后是 "SomePlugin.zip", 解压后是 "SomePlugin_extracted"
                    # 我们需要通过 "SomePlugin_extracted" 找到树中的 "SomePlugin" 项

                    # 简化逻辑：我们假设selected_item的text(0)是下载列表中的原始名称（可能不含通用压缩后缀，但可能含.jar这类特殊后缀）
                    # 我们通过解压后的文件夹名（去除了_extracted）来匹配树节点
                    # 这是一个启发式方法，可能不完美
                    items_in_tree = self.tree.findItems(base_name, Qt.MatchStartsWith | Qt.MatchRecursive, 0)
                    if items_in_tree:
                        original_file_name_for_tree_lookup = items_in_tree[0].text(0)
                        found_original = True
                        break
                if not found_original:
                    # 如果找不到，就用去除_extracted的名称
                    original_file_name_for_tree_lookup = base_name
            else:
                # 如果解压文件夹名不规范，直接使用文件夹名在树中查找，可能找不到正确的项目
                pass 

        # 查找下载项目以确定目标路径
        selected_item = None
        # 尝试精确匹配，如果找不到，再尝试用 original_file_name_for_tree_lookup （可能已经去除了压缩包后缀）
        exact_match_items = self.tree.findItems(os.path.basename(source_path), Qt.MatchExactly | Qt.MatchRecursive, 0)
        if exact_match_items:
            selected_item = exact_match_items[0]
        else:
            # 尝试使用 original_file_name_for_tree_lookup (这通常是去除了_extracted后缀的名称)
            heuristic_match_items = self.tree.findItems(original_file_name_for_tree_lookup, Qt.MatchContains | Qt.MatchRecursive, 0)
            if heuristic_match_items:
                selected_item = heuristic_match_items[0]
            else:
                 # 最后尝试，如果原始下载文件名（带后缀）能在树中找到，也用它
                downloaded_file_name_itself = os.path.basename(source_path if not is_extracted_folder else source_path.replace('_extracted', '')) # 获取原始下载文件名
                downloaded_file_name_items = self.tree.findItems(downloaded_file_name_itself, Qt.MatchContains | Qt.MatchRecursive, 0)
                if downloaded_file_name_items:
                    selected_item = downloaded_file_name_items[0]

        if not selected_item:
            self.logger.error(f'移动文件/目录失败：在下载列表中未找到与 "{original_file_name_for_tree_lookup}" 或 "{os.path.basename(source_path)}"相关的项目。')
            QMessageBox.critical(self, '错误', f'移动文件/目录失败：未找到下载项目 "{original_file_name_for_tree_lookup}"。')
            # 如果是解压的文件夹，尝试删除它，因为它没有目标位置
            if is_extracted_folder and os.path.isdir(source_path):
                try:
                    shutil.rmtree(source_path)
                    self.logger.info(f'已删除未找到对应项目的解压文件夹: {source_path}')
                except Exception as e_rm:
                    self.logger.error(f'删除解压文件夹失败: {source_path}, 错误: {e_rm}')
            return

        category_name = selected_item.parent().text(0)
        target_base_path = self.category_paths.get(category_name)

        if not target_base_path:
            self.logger.error(f'未知的分类: {category_name}')
            QMessageBox.critical(self, '错误', f'未知的分类: {category_name}')
            return

        # 特殊处理服务端核心、插件和卡池配置文件，它们需要放到特定实例的目录下
        if category_name in ['服务端核心', '插件', '卡池配置文件']:
            if not self.current_instance:
                self.logger.error('在移动服务端核心、插件或卡池配置文件时，当前实例未设置。')
                QMessageBox.critical(self, '错误', '内部错误：当前实例未设置，无法移动文件。')
                return
            target_base_path = os.path.join(target_base_path, self.current_instance)
            subdir = self.category_subdirs.get(category_name)
            if subdir:
                target_base_path = os.path.join(target_base_path, subdir)
        
        # 确保目标基础路径存在
        try:
            os.makedirs(target_base_path, exist_ok=True)
        except Exception as e:
            self.logger.error(f'创建目标目录失败: {target_base_path}, 错误: {e}')
            QMessageBox.critical(self, '错误', f'创建目标目录失败: {target_base_path}, {e}')
            return

        final_dest_path = os.path.join(target_base_path, os.path.basename(source_path if not is_extracted_folder else original_file_name_for_tree_lookup))
        # 如果是解压的文件夹，目标路径应该是其内容要合并到的目录，而不是创建一个同名文件夹
        # 例如，如果解压后是 a_extracted/file.txt, 目标是 Servers/Instance/plugins/
        # 那么 file.txt 应该移动到 Servers/Instance/plugins/file.txt
        # 而不是 Servers/Instance/plugins/a_extracted/file.txt
        # 因此，如果is_extracted_folder为True，final_dest_path应该是target_base_path

        try:
            if is_extracted_folder and os.path.isdir(source_path):
                self.logger.info(f'开始移动解压后的文件夹内容从 {source_path} 到 {target_base_path}')
                # 移动文件夹中的所有内容
                for item_name in os.listdir(source_path):
                    s_item = os.path.join(source_path, item_name)
                    d_item = os.path.join(target_base_path, item_name)
                    if os.path.isdir(s_item):
                        # 如果目标已存在同名文件夹，先删除，或者合并（这里选择替换）
                        if os.path.exists(d_item) and os.path.isdir(d_item):
                            shutil.rmtree(d_item)
                        shutil.move(s_item, d_item)
                    else:
                        if os.path.exists(d_item):
                            os.remove(d_item)
                        shutil.move(s_item, d_item)
                self.logger.success(f'解压内容成功移动到: {target_base_path}')
                self.status_label.setText(f'解压内容已移至: {target_base_path}')
                # 删除空的源解压文件夹
                try:
                    shutil.rmtree(source_path)
                    self.logger.info(f'已删除空的源解压文件夹: {source_path}')
                except Exception as e_rm_empty:
                    self.logger.warning(f'删除源解压文件夹失败 (可能不为空或权限问题): {source_path}, {e_rm_empty}')
            
            elif not is_extracted_folder and os.path.isfile(source_path):
                # 移动单个文件
                # 目标文件名应该与下载列表中的名称一致，或者就是下载的文件名
                # selected_item.text(0) 是下载列表中的名字
                # os.path.basename(source_path) 是实际下载的文件名
                # 通常情况下，如果下载列表是 grasscutter.jar, 下载的就是 grasscutter.jar
                # 如果下载列表是 GC (url是 .../grasscutter.jar), 下载的还是 grasscutter.jar
                # 我们希望最终的文件名是 selected_item.text(0)
                final_file_dest = os.path.join(target_base_path, selected_item.text(0))
                if os.path.exists(final_file_dest):
                    os.remove(final_file_dest) # 如果目标文件已存在，则替换
                shutil.move(source_path, final_file_dest)
                self.logger.success(f'文件成功移动到: {final_file_dest}')
                self.status_label.setText(f'文件已移至: {final_file_dest}')
            else:
                self.logger.warning(f'源路径 {source_path} 不是预期的文件或文件夹类型，或者处理逻辑未覆盖。')
                # QMessageBox.warning(self, '警告', f'无法处理移动请求：{source_path} 类型未知或不适用当前操作。')
                # 尝试按原样移动，如果它是文件夹但is_extracted_folder为false
                if os.path.isdir(source_path) and not is_extracted_folder:
                    if os.path.exists(final_dest_path):
                        shutil.rmtree(final_dest_path) # 替换目标文件夹
                    shutil.move(source_path, final_dest_path)
                    self.logger.success(f'文件夹成功移动到: {final_dest_path}')
                    self.status_label.setText(f'文件夹已移至: {final_dest_path}')
                else:
                    QMessageBox.warning(self, '警告', f'无法处理移动请求：{source_path} 类型未知或不适用当前操作。')
                    return

            QMessageBox.information(self, '成功', f'{os.path.basename(source_path if not is_extracted_folder else original_file_name_for_tree_lookup)} 已成功处理并移动。')

        except Exception as e:
            self.logger.error(f'移动文件/目录失败 从 {source_path} 到 {target_base_path if is_extracted_folder else final_dest_path}: {e}')
            QMessageBox.critical(self, '错误', f'移动文件/目录失败: {e}')
            # 如果移动失败，尝试清理已解压的文件夹（如果适用）
            if is_extracted_folder and os.path.isdir(source_path):
                self.logger.info(f"移动失败，保留解压文件夹供手动处理: {source_path}")
                # shutil.rmtree(source_path) # 移动失败，可以选择删除解压的文件夹
                # self.logger.info(f'移动失败，已删除解压文件夹: {source_path}')

        # 清理下载队列中完成的线程
        active_threads = False
        for thread, _ in list(self.download_queue.items()):
            if not thread.isRunning():
                del self.download_queue[thread]
            else:
                active_threads = True
        if not active_threads:
            self.progress_bar.reset()
            self.status_label.setText('所有下载已完成')
            self.current_instance = None # 重置当前实例