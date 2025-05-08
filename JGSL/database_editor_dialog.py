from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QInputDialog, QTreeWidget, QTreeWidgetItem, QSplitter, QMenu, QAction, QWidget, QLabel, QApplication
from PyQt5.QtCore import Qt
from loguru import logger
import pymongo

class DatabaseEditorDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle('MongoDB 数据库编辑器')
        self.setGeometry(150, 150, 1000, 700)
        self.setWindowModality(Qt.ApplicationModal)

        self.current_db = None
        self.current_collection = None

        self.init_ui()
        self.load_databases()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # 左侧:数据库和集合列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.db_list_widget = QListWidget()
        self.db_list_widget.currentItemChanged.connect(self.on_db_selected)
        left_layout.addWidget(QLabel("数据库:"))
        left_layout.addWidget(self.db_list_widget)

        self.collection_list_widget = QListWidget()
        self.collection_list_widget.currentItemChanged.connect(self.on_collection_selected)
        left_layout.addWidget(QLabel("集合:"))
        left_layout.addWidget(self.collection_list_widget)

        splitter.addWidget(left_panel)

        # 右侧:文档查看和编辑区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 查询区域
        query_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText('输入查询语句 (例如: {"name": "John"})，留空查询所有')
        query_layout.addWidget(self.query_input)
        self.query_button = QPushButton('查询')
        self.query_button.clicked.connect(self.load_documents)
        query_layout.addWidget(self.query_button)
        right_layout.addLayout(query_layout)

        self.document_tree_widget = QTreeWidget()
        self.document_tree_widget.setHeaderLabels(['字段', '值'])
        self.document_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.document_tree_widget.customContextMenuRequested.connect(self.open_document_context_menu)
        right_layout.addWidget(self.document_tree_widget)

        # 文档操作按钮
        doc_actions_layout = QHBoxLayout()
        self.add_doc_button = QPushButton('添加文档')
        self.add_doc_button.clicked.connect(self.add_document)
        doc_actions_layout.addWidget(self.add_doc_button)
        # self.edit_doc_button = QPushButton('编辑文档') # 编辑通过右键菜单实现
        # self.edit_doc_button.clicked.connect(self.edit_document)
        # doc_actions_layout.addWidget(self.edit_doc_button)
        self.delete_doc_button = QPushButton('删除文档')
        self.delete_doc_button.clicked.connect(self.delete_document)
        doc_actions_layout.addWidget(self.delete_doc_button)
        right_layout.addLayout(doc_actions_layout)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 800]) # 初始大小
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_databases(self):
        try:
            db_names = self.client.list_database_names()
            # 过滤掉系统数据库
            system_dbs = ['admin', 'config', 'local']
            user_dbs = [name for name in db_names if name not in system_dbs]
            self.db_list_widget.clear()
            self.db_list_widget.addItems(user_dbs)
        except Exception as e:
            logger.error(f"加载数据库列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载数据库列表失败\n{e}")

    def on_db_selected(self, current_item, previous_item):
        if current_item:
            self.current_db_name = current_item.text()
            self.load_collections(self.current_db_name)
            self.document_tree_widget.clear() # 清空文档显示
        else:
            self.current_db_name = None
            self.collection_list_widget.clear()
            self.document_tree_widget.clear()

    def load_collections(self, db_name):
        try:
            db = self.client[db_name]
            collection_names = db.list_collection_names()
            self.collection_list_widget.clear()
            self.collection_list_widget.addItems(collection_names)
        except Exception as e:
            logger.error(f"加载集合列表失败 (数据库: {db_name}): {e}")
            QMessageBox.critical(self, "错误", f"加载集合列表失败 (数据库: {db_name})\n{e}")

    def on_collection_selected(self, current_item, previous_item):
        if current_item:
            self.current_collection_name = current_item.text()
            self.load_documents()
        else:
            self.current_collection_name = None
            self.document_tree_widget.clear()

    def load_documents(self):
        if not self.current_db_name or not self.current_collection_name:
            return

        self.document_tree_widget.clear()
        try:
            db = self.client[self.current_db_name]
            collection = db[self.current_collection_name]
            
            query_str = self.query_input.text().strip()
            query_filter = {}
            if query_str:
                try:
                    # 尝试将查询字符串解析为字典
                    import json
                    query_filter = json.loads(query_str)
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "查询错误", "查询语句格式不正确，请输入有效的JSON。")
                    return
            
            # 限制日志数量，避免加载过多数据卡死UI
            documents = collection.find(query_filter).limit(100) 
            for doc in documents:
                doc_id_str = str(doc.get('_id', 'N/A'))
                item = QTreeWidgetItem(self.document_tree_widget, [f"_id: {doc_id_str}"])
                item.setData(0, Qt.UserRole, doc) # 存储整个文档对象
                self.populate_tree_item(item, doc)
            self.document_tree_widget.expandAll()
        except Exception as e:
            logger.error(f"加载文档失败 (数据库: {self.current_db_name}, 集合: {self.current_collection_name}): {e}")
            QMessageBox.critical(self, "错误", f"加载文档失败 (数据库: {self.current_db_name}, 集合: {self.current_collection_name})\n{e}")

    def populate_tree_item(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                # 对于 _id 字段，我们已经在父项显示，这里可以跳过或以不同方式显示
                if key == '_id' and parent_item.text(0).startswith('_id:'):
                    continue 
                child_item = QTreeWidgetItem(parent_item, [str(key)])
                child_item.setData(0, Qt.UserRole, parent_item.data(0, Qt.UserRole)) # 传递文档引用
                child_item.setData(1, Qt.UserRole, key) # 存储字段名
                self.populate_tree_item(child_item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                child_item = QTreeWidgetItem(parent_item, [f"[{index}]"])
                child_item.setData(0, Qt.UserRole, parent_item.data(0, Qt.UserRole)) # 传递文档引用
                child_item.setData(1, Qt.UserRole, parent_item.text(0) + f".[{index}]") # 存储字段路径
                self.populate_tree_item(child_item, value)
        else:
            parent_item.setText(1, str(data))
            parent_item.setData(2, Qt.UserRole, data) # 存储原始值

    def open_document_context_menu(self, position):
        item = self.document_tree_widget.itemAt(position)
        if not item:
            return

        menu = QMenu()
        # 仅当选中了字段值（第二列有文本）或者该项代表一个可直接复制的父级项（如_id）时，才显示复制值
        # 并且确保不是顶层的文档ID项（它没有父项，或者父项是根）
        is_value_node = bool(item.text(1)) 
        is_document_id_node = item.text(0).startswith("_id:") and not item.parent()

        if is_value_node or is_document_id_node:
            copy_value_action = QAction('复制值', self)
            copy_value_action.triggered.connect(lambda: self.copy_item_value(item))
            menu.addAction(copy_value_action)

        # 添加“修改值”选项，仅当它是叶子节点（有值）且不是_id字段时
        if is_value_node and not item.text(0).lower() == '_id' and not item.text(0).startswith("_id:") :
            # 确保不是数组/对象节点本身，而是其下的具体值节点
            # 通常，有值的节点其第一列是字段名，第二列是值
            # 数组和对象的父节点，其第二列通常为空
            if item.childCount() == 0: # 确保是叶子节点
                modify_value_action = QAction('修改值', self)
                modify_value_action.triggered.connect(lambda: self.modify_item_value(item))
                menu.addAction(modify_value_action)

        # 复制字段名 (如果第一列有文本且不是文档ID节点)
        if item.text(0) and not is_document_id_node:
            copy_key_action = QAction('复制字段名', self)
            copy_key_action.triggered.connect(lambda: self.copy_item_key(item))
            menu.addAction(copy_key_action)

        menu.exec_(self.document_tree_widget.viewport().mapToGlobal(position))

    def copy_item_value(self, item):
        # 如果是文档ID项
        if item.text(0).startswith("_id:") and not item.parent():
            doc_id_str = item.text(0).split(": ", 1)[1]
            clipboard = QApplication.clipboard()
            clipboard.setText(doc_id_str)
            logger.info(f"文档ID '{doc_id_str}' 已复制到剪贴板")
        elif item.text(1): # 如果第二列有值
            value_to_copy = item.text(1)
            clipboard = QApplication.clipboard()
            clipboard.setText(value_to_copy)
            logger.info(f"值 '{value_to_copy}' 已复制到剪贴板")
        else:
            logger.warning("尝试复制一个没有值的项目")

    def copy_item_key(self, item):
        if item.text(0):
            key_to_copy = item.text(0)
            clipboard = QApplication.clipboard()
            clipboard.setText(key_to_copy)
            logger.info(f"字段名 '{key_to_copy}' 已复制到剪贴板")
        else:
            logger.warning("尝试复制一个没有字段名的项目")

    def modify_item_value(self, item):
        if not self.current_db_name or not self.current_collection_name:
            QMessageBox.warning(self, "错误", "未选择数据库或集合")
            return

        doc_data = item.data(0, Qt.UserRole) # 获取存储在顶层父项的完整文档
        if not doc_data or not isinstance(doc_data, dict) or '_id' not in doc_data:
            # 尝试从父项获取文档数据
            parent = item.parent()
            while parent and not parent.data(0, Qt.UserRole):
                parent = parent.parent()
            if parent and parent.data(0, Qt.UserRole):
                doc_data = parent.data(0, Qt.UserRole)
            else:
                # 如果还是找不到，就从根文档项获取
                top_level_item = item
                while top_level_item.parent():
                    top_level_item = top_level_item.parent()
                doc_data = top_level_item.data(0, Qt.UserRole)
                if not doc_data or not isinstance(doc_data, dict) or '_id' not in doc_data:
                    logger.error(f"无法获取文档数据或文档ID进行修改。Item text: {item.text(0)}, {item.text(1)}")
                    QMessageBox.critical(self, "错误", "无法获取文档数据或文档ID进行修改")
                    return
        
        doc_id = doc_data['_id']
        field_path_parts = []
        current_item = item
        # 从当前项向上追溯，构建字段路径
        # 我们需要找到存储字段名的那个data(1, Qt.UserRole)
        # 对于 populate_tree_item 的逻辑，字段名存储在当前项的 data(1, Qt.UserRole) 中
        # 或者，如果当前项是数组元素，它的 text(0) 是 "[index]"
        temp_item = item
        while temp_item and temp_item.parent(): # 排除最顶层的文档ID项
            field_name_or_index = temp_item.data(1, Qt.UserRole) # 优先使用存储的字段名
            if field_name_or_index is None: # 备用方案，从文本获取（可能不准确，特别是对于复杂嵌套）
                field_name_or_index = temp_item.text(0)
                if field_name_or_index.startswith("[") and field_name_or_index.endswith("]"):
                    try:
                        field_name_or_index = int(field_name_or_index[1:-1]) # 转换为整数索引
                    except ValueError:
                        pass #保持字符串形式
            
            if field_name_or_index is not None:
                 # 检查是否已经是完整的路径（针对数组元素）
                if isinstance(field_name_or_index, str) and '.' in field_name_or_index:
                    field_path_parts = field_name_or_index.split('.') + field_path_parts
                    # 如果是这种情况，通常意味着我们已经得到了从父级传递下来的完整路径的一部分
                    # 但这里我们需要的是从当前节点到其直接父节点的键或索引
                    # 重新审视路径构建逻辑
                    # 实际上，data(1, Qt.UserRole) 在 populate_tree_item 中存储的是当前节点的字段名或索引
                    field_path_parts.insert(0, str(field_name_or_index))
                else:
                    field_path_parts.insert(0, str(field_name_or_index))
            temp_item = temp_item.parent()
            # 如果父项是文档ID项，则停止
            if temp_item and temp_item.text(0).startswith("_id:") and not temp_item.parent():
                break
        
        # 清理和修正路径，移除最顶层的文档ID部分（如果误包含）
        # 并且移除重复的路径部分
        # 这里的路径构建逻辑比较复杂，需要确保准确性
        # 重新思考路径构建：我们只需要从当前修改的 item 向上找到其在文档结构中的路径
        # 每个 item 的 data(1, Qt.UserRole) 存储了它自己的 key 或 index (相对于其父 item)
        field_path_parts_new = []
        curr = item
        while curr and curr.parent(): # 确保不是根文档项
            key_or_index = curr.data(1, Qt.UserRole)
            if key_or_index is not None:
                field_path_parts_new.insert(0, str(key_or_index))
            else: # 备用：如果 UserRole 没有存，尝试从 text(0) 获取，但这通常是字段名
                # 对于值节点，text(0) 是字段名，text(1) 是值。我们需要的是字段名。
                # 对于数组父节点，text(0) 是字段名，其子节点的 text(0) 是 "[index]"
                # 对于对象父节点，text(0) 是字段名，其子节点的 text(0) 是子字段名
                # 这个逻辑分支可能不总是需要，因为 UserRole 应该存了
                field_name = curr.text(0)
                if field_name.startswith("[") and field_name.endswith("]"):
                    try:
                        field_path_parts_new.insert(0, int(field_name[1:-1]))
                    except ValueError:
                         field_path_parts_new.insert(0, field_name)
                else:
                    field_path_parts_new.insert(0, field_name)

            curr = curr.parent()
            if curr and curr.text(0).startswith("_id:") and not curr.parent(): # 到达文档根节点
                break
        field_path = '.'.join(str(p) for p in field_path_parts_new)

        if not field_path:
            logger.error(f"无法确定要修改的字段路径。Item: {item.text(0)}")
            QMessageBox.critical(self, "错误", "无法确定要修改的字段路径")
            return

        current_value_str = item.text(1)
        # 尝试将当前值转换为原始类型，以便输入对话框能正确显示和处理
        original_value = item.data(2, Qt.UserRole) # 从 setData(2, Qt.UserRole, data) 获取
        if original_value is None: # 如果没有存储原始值，则使用字符串形式
            original_value = current_value_str

        # 根据原始值的类型，决定使用 QInputDialog.getText, getInt, getDouble, getItem
        new_value_str, ok = "", False
        if isinstance(original_value, bool):
            items = ["True", "False"]
            current_selection = "True" if original_value else "False"
            text, ok = QInputDialog.getItem(self, "修改值", f"字段 '{field_path}':", items, items.index(current_selection), False)
            if ok and text:
                new_value_str = text == "True"
        elif isinstance(original_value, int):
            num, ok = QInputDialog.getInt(self, "修改值", f"字段 '{field_path}':", value=original_value)
            if ok:
                new_value_str = num
        elif isinstance(original_value, float):
            num, ok = QInputDialog.getDouble(self, "修改值", f"字段 '{field_path}':", value=original_value)
            if ok:
                new_value_str = num
        else: # 默认为字符串
            text, ok = QInputDialog.getText(self, "修改值", f"字段 '{field_path}':", text=current_value_str)
            if ok and text is not None:
                new_value_str = text

        if ok:
            try:
                # 尝试转换回原始类型，如果输入的是数字但字段原来是字符串，这里需要小心
                # 或者，让用户输入JSON片段来支持更复杂类型？目前先简单处理
                # 对于数字类型，QInputDialog已经返回了正确的类型
                # 对于布尔类型，也已处理
                # 对于字符串，直接使用
                # 如果原始类型是其他（如ObjectId，Date等），这里可能需要更复杂的处理
                # 目前，我们假设MongoDB驱动能处理好Python类型到BSON类型的转换
                value_to_set = new_value_str 
                if isinstance(original_value, (int, float, bool)) and not isinstance(new_value_str, type(original_value)):
                    try:
                        if isinstance(original_value, bool):
                            value_to_set = str(new_value_str).lower() in ['true', '1', 'yes']
                        elif isinstance(original_value, int):
                            value_to_set = int(new_value_str)
                        elif isinstance(original_value, float):
                            value_to_set = float(new_value_str)
                    except ValueError:
                        QMessageBox.warning(self, "类型错误", f"输入的值 '{new_value_str}' 无法转换为原始类型 '{type(original_value).__name__}' 将尝试作为字符串更新。")
                        # 如果转换失败，可能还是按字符串处理，或者提示用户
                        pass # value_to_set 保持 QInputDialog 的输出

                db = self.client[self.current_db_name]
                collection = db[self.current_collection_name]
                result = collection.update_one({'_id': doc_id}, {'$set': {field_path: value_to_set}})

                if result.modified_count > 0:
                    logger.info(f"文档 '{doc_id}' 中字段 '{field_path}' 已更新为 '{value_to_set}'")
                    QMessageBox.information(self, "成功", f"字段 '{field_path}' 已更新")
                    self.load_documents()  # 重新加载文档以显示更改
                elif result.matched_count == 0:
                    logger.error(f"更新失败：未找到文档 '{doc_id}'")
                    QMessageBox.critical(self, "错误", f"更新失败：未找到文档 '{doc_id}'")
                else:
                    logger.info(f"文档 '{doc_id}' 中字段 '{field_path}' 未发生变化 (新旧值可能相同)")
                    QMessageBox.information(self, "提示", "字段值未发生变化 (新旧值可能相同)")
            except Exception as e:
                logger.error(f"更新数据库失败: {e}")
                QMessageBox.critical(self, "错误", f"更新数据库失败\n{e}")

    def add_document(self):
        if not self.current_db_name or not self.current_collection_name:
            QMessageBox.warning(self, "提示", "请先选择一个数据库和集合")
            return

        doc_content, ok = QInputDialog.getMultiLineText(self, '添加新文档', 
                                                        '请输入文档内容 (JSON格式):',
                                                        '{}\n')
        if ok and doc_content:
            try:
                import json
                new_doc = json.loads(doc_content)
                db = self.client[self.current_db_name]
                collection = db[self.current_collection_name]
                result = collection.insert_one(new_doc)
                logger.info(f"文档已添加, ID: {result.inserted_id}")
                QMessageBox.information(self, "成功", f"文档已成功添加\nID: {result.inserted_id}")
                self.load_documents() # 刷新文档列表
            except json.JSONDecodeError:
                QMessageBox.critical(self, "错误", "输入的文档内容不是有效的JSON格式")
            except Exception as e:
                logger.error(f"添加文档失败: {e}")
                QMessageBox.critical(self, "错误", f"添加文档失败\n{e}")

    def edit_document_content(self, item):
        if not item or not self.current_db_name or not self.current_collection_name:
            return
        
        original_doc = item.data(0, Qt.UserRole)
        if not original_doc or not isinstance(original_doc, dict):
            logger.warning("无法获取原始文档数据进行编辑")
            return

        doc_id = original_doc.get('_id')
        if not doc_id:
            QMessageBox.warning(self, "错误", "无法获取文档ID，无法编辑。")
            return

        try:
            import json
            # 为了更好的编辑体验，将ObjectId转换为字符串，但提交时可能需要转回
            editable_doc = json.dumps(original_doc, indent=4, default=str) 
        except Exception as e:
            QMessageBox.critical(self, "错误", f"准备编辑的文档数据序列化失败\n{e}")
            return

        doc_content, ok = QInputDialog.getMultiLineText(self, f'编辑文档 (ID: {doc_id})',
                                                        '文档内容 (JSON格式):',
                                                        editable_doc)
        if ok and doc_content:
            try:
                updated_doc_data = json.loads(doc_content)
                # _id 字段通常不允许直接修改，如果用户修改了，需要提醒或处理
                if '_id' in updated_doc_data and updated_doc_data['_id'] != doc_id:
                    # 实际应用中，MongoDB不允许直接修改_id，这里我们替换整个文档（除了_id）
                    # 或者，如果允许修改_id，则需要先删除旧文档，再插入新文档，但这通常不推荐
                    QMessageBox.warning(self, "警告", "文档的 _id 字段不应被修改。如需更改，请删除后重新添加。")
                    # 恢复原始_id，避免尝试修改它
                    updated_doc_data['_id'] = doc_id 
                
                db = self.client[self.current_db_name]
                collection = db[self.current_collection_name]
                
                # 使用 replace_one 来替换整个文档，确保 _id 匹配
                # 如果只想更新部分字段，可以使用 update_one 和 $set 操作符
                result = collection.replace_one({'_id': doc_id}, updated_doc_data)

                if result.modified_count > 0:
                    logger.info(f"文档 {doc_id} 已更新")
                    QMessageBox.information(self, "成功", f"文档 {doc_id} 已成功更新")
                    self.load_documents() # 刷新
                elif result.matched_count == 0:
                    QMessageBox.warning(self, "未找到", f"未找到要更新的文档 {doc_id}。")
                else:
                    QMessageBox.information(self, "无更改", f"文档 {doc_id} 内容未发生变化。")

            except json.JSONDecodeError:
                QMessageBox.critical(self, "错误", "输入的文档内容不是有效的JSON格式")
            except Exception as e:
                logger.error(f"更新文档 {doc_id} 失败: {e}")
                QMessageBox.critical(self, "错误", f"更新文档 {doc_id} 失败\n{e}")

    def delete_document_content(self, item):
        if not item or not self.current_db_name or not self.current_collection_name:
            return

        original_doc = item.data(0, Qt.UserRole)
        if not original_doc or not isinstance(original_doc, dict):
            logger.warning("无法获取原始文档数据进行删除")
            return

        doc_id = original_doc.get('_id')
        if not doc_id:
            QMessageBox.warning(self, "错误", "无法获取文档ID，无法删除。")
            return

        reply = QMessageBox.question(self, '确认删除',
                                     f"确定要删除文档 (ID: {doc_id}) 吗此操作不可恢复！",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                db = self.client[self.current_db_name]
                collection = db[self.current_collection_name]
                result = collection.delete_one({'_id': doc_id})
                if result.deleted_count > 0:
                    logger.info(f"文档 {doc_id} 已删除")
                    QMessageBox.information(self, "成功", f"文档 {doc_id} 已成功删除")
                    self.load_documents() # 刷新
                else:
                    QMessageBox.warning(self, "未找到", f"未找到要删除的文档 {doc_id}。")
            except Exception as e:
                logger.error(f"删除文档 {doc_id} 失败: {e}")
                QMessageBox.critical(self, "错误", f"删除文档 {doc_id} 失败\n{e}")

    def delete_document(self):
        selected_items = self.document_tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择一个要删除的文档")
            return
        # 通常QTreeWidget只允许单选，但以防万一取第一个
        item_to_delete = selected_items[0]
        # 确保是顶层文档项
        if not item_to_delete.parent():
            self.delete_document_content(item_to_delete)
        else:
            QMessageBox.warning(self, "提示", "请选择文档的根节点进行删除操作。")

# 为了方便测试，添加一个简单的启动入口
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QLabel
    import sys

    # 模拟一个 MongoDB 客户端连接 (需要本地运行 MongoDB 服务)
    class MockMongoClient:
        def __init__(self, uri, serverSelectionTimeoutMS=None):
            self.uri = uri
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=serverSelectionTimeoutMS)
            try:
                self.client.admin.command('ping') # 测试连接
                logger.info(f"成功连接到测试 MongoDB: {uri}")
            except Exception as e:
                logger.error(f"连接测试 MongoDB 失败: {e}")
                raise

        def list_database_names(self):
            return self.client.list_database_names()

        def __getitem__(self, db_name):
            return self.client[db_name]

    app = QApplication(sys.argv)
    try:
        # 替换为你的 MongoDB 连接字符串
        mongo_client = MockMongoClient("mongodb://127.0.0.1:27017/") 
        dialog = DatabaseEditorDialog(client=mongo_client)
        dialog.show()
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText(f"无法初始化数据库编辑器: {e}")
        error_dialog.setInformativeText("请确保 MongoDB 服务正在运行并且连接配置正确。")
        error_dialog.setWindowTitle("初始化错误")
        error_dialog.exec_()
        sys.exit(1)

    sys.exit(app.exec_())