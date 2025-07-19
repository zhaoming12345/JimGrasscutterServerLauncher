# -*- coding: utf-8 -*-
# json_editor.py - 可视化 JSON 编辑器 (增强版)

import os
import sys
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem,
    QMessageBox, QComboBox, QAbstractItemView,
    QMenu, QAction, QTextEdit)


class JSONEditor(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.current_json_data = None
        self.page_size = 20
        self.undo_stack = []
        self.initUI()
        if self.file_path:
            self.path_input.setCurrentText(self.file_path)
            self.load_json()

    def initUI(self):
        self.setWindowTitle('JSON 编辑器')
        self.setGeometry(200, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        control_layout = QHBoxLayout()

        self.path_input = QComboBox()
        self.path_input.setEditable(True)
        self.path_input.setInsertPolicy(QComboBox.NoInsert)
        self.path_input.lineEdit().setPlaceholderText("键入路径或在下拉框中选择")
        self.path_input.lineEdit().installEventFilter(self)
        self.load_combo_box_items()

        control_layout.addWidget(self.path_input)

        self.browse_btn = QPushButton('浏览')
        self.browse_btn.clicked.connect(self.browse_file)
        control_layout.addWidget(self.browse_btn)

        self.load_btn = QPushButton('加载')
        self.load_btn.clicked.connect(self.load_json)
        control_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton('保存')
        self.save_btn.clicked.connect(self.save_json)
        control_layout.addWidget(self.save_btn)

        self.undo_btn = QPushButton('撤销')
        self.undo_btn.clicked.connect(self.undo_edit)
        control_layout.addWidget(self.undo_btn)

        layout.addLayout(control_layout)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(['键', '类型', '值'])
        self.tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree)

        self.statusBar().showMessage('就绪')

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        edit_action = QAction(self.tr("编辑值"), self)
        edit_action.triggered.connect(lambda: self.open_edit_dialog(item))
        menu.addAction(edit_action)
        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def open_edit_dialog(self, item):
        old_value = item.text(2)

        dialog = QWidget()
        dialog.setWindowTitle("编辑值")
        dialog.setMinimumSize(400, 300)
        layout = QVBoxLayout(dialog)

        editor = QTextEdit()
        editor.setPlainText(old_value)
        layout.addWidget(editor)

        btn = QPushButton("确定")
        btn.clicked.connect(lambda: self.apply_edit(item, editor.toPlainText(), dialog))
        layout.addWidget(btn)

        dialog.show()

    def apply_edit(self, item, new_value, dialog):
        self.undo_stack.append((item, item.text(2)))
        item.setText(2, new_value)
        dialog.close()

    def undo_edit(self):
        if self.undo_stack:
            item, prev_value = self.undo_stack.pop()
            item.setText(2, prev_value)

    def load_combo_box_items(self):
        try:
            with open("../Config/jsonfileinfo.json", "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    self.path_input.addItem(item['name'], item['path'])
        except Exception as e:
            print(f"无法加载jsonfileinfo.json: {e}")

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("选择JSON文件"), self.tr(""), self.tr("JSON文件 (*.json)"))
        if path:
            self.path_input.setCurrentText(path)

    def load_json(self):
        path = self.path_input.currentText().strip()
        if not os.path.isfile(path):
            QMessageBox.warning(self, self.tr("错误"), self.tr("请选择有效的文件路径"))
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"读取JSON失败: {str(e)}"))
            return

        self.current_json_data = data
        self.file_path = path
        self.populate_tree(data)

    def populate_tree(self, data):
        self.tree.clear()
        root = QTreeWidgetItem(['根', self.get_type(data), ''])
        self.tree.addTopLevelItem(root)
        self.add_items(root, data)
        root.setExpanded(True)

    def add_items(self, parent, value):
        if isinstance(value, dict):
            for k, v in value.items():
                child = QTreeWidgetItem([str(k), self.get_type(v), str(v) if not isinstance(v, (dict, list)) else ''])
                parent.addChild(child)
                self.add_items(child, v)
        elif isinstance(value, list):
            for idx, v in enumerate(value):
                child = QTreeWidgetItem([f"[{idx}]", self.get_type(v), str(v) if not isinstance(v, (dict, list)) else ''])
                parent.addChild(child)
                self.add_items(child, v)

    def get_type(self, v):
        if isinstance(v, dict): return "dict"
        if isinstance(v, list): return "list"
        return type(v).__name__

    def tree_to_json(self):
        def parse_item(item):
            child_count = item.childCount()
            key = item.text(0)
            value_text = item.text(2)
            if child_count == 0:
                try:
                    return json.loads(value_text)
                except:
                    return value_text
            elif all(item.child(i).text(0).startswith('[') for i in range(child_count)):
                return [parse_item(item.child(i)) for i in range(child_count)]
            else:
                return {item.child(i).text(0): parse_item(item.child(i)) for i in range(child_count)}

        root = self.tree.topLevelItem(0)
        return parse_item(root)

    def save_json(self):
        if not self.file_path:
            QMessageBox.warning(self, self.tr("错误"), self.tr("没有文件可以保存"))
            return
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.tree_to_json(), f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, self.tr("成功"), self.tr(f"文件已保存: {self.file_path}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"保存失败: {e}"))

    def eventFilter(self, source, event):
        if source == self.path_input.lineEdit():
            if event.type() == event.FocusIn:
                if source.placeholderText() == self.tr("键入路径或在下拉框中选择"):
                    source.setPlaceholderText("")
            elif event.type() == event.FocusOut:
                if not source.text():
                    source.setPlaceholderText("键入路径或在下拉框中选择")
        return super().eventFilter(source, event)




def edit_itjson(file_path=None):
    app = QApplication(sys.argv)
    editor = JSONEditor(file_path)
    editor.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    edit_itjson()