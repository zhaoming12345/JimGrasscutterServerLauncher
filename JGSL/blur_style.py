#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
为应用程序提供高斯模糊透明效果的样式表
"""

from PyQt5.QtWidgets import QWidget
from loguru import logger

# 主样式表 - 适用于模糊背景
BLUR_STYLE = """
/* 主窗口样式 */
QMainWindow {
    background-color: rgba(30, 30, 30, 160); /* 半透明深色背景 */
    border-radius: 8px;
    border: 1px solid rgba(100, 100, 100, 120);
}

/* 标签页样式 */
QTabWidget::pane {
    background-color: rgba(40, 40, 40, 180);
    border: none;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: rgba(60, 60, 60, 180);
    color: #cccccc;
    padding: 8px 16px;
    margin: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: rgba(80, 80, 80, 200);
    color: white;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(70, 70, 70, 190);
}

/* 按钮样式 */
QPushButton {
    background-color: rgba(70, 70, 70, 180);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: rgba(90, 90, 90, 200);
}

QPushButton:pressed {
    background-color: rgba(50, 50, 50, 200);
}

/* 输入框样式 */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: rgba(50, 50, 50, 180);
    color: white;
    border: 1px solid rgba(100, 100, 100, 120);
    border-radius: 4px;
    padding: 4px;
}

/* 下拉框样式 */
QComboBox {
    background-color: rgba(50, 50, 50, 180);
    color: white;
    border: 1px solid rgba(100, 100, 100, 120);
    border-radius: 4px;
    padding: 4px;
}

/* 滚动条样式 */
QScrollBar:vertical {
    background-color: rgba(40, 40, 40, 120);
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: rgba(100, 100, 100, 150);
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(120, 120, 120, 180);
}
"""

def apply_blur_style(widget: QWidget):
    """
    应用高斯模糊透明效果的样式到指定部件
    
    :param widget: 要应用样式的部件
    """
    try:
        widget.setStyleSheet(BLUR_STYLE)
        logger.info(f"已应用高斯模糊透明样式到 {widget.objectName() if widget.objectName() else type(widget).__name__}")
    except Exception as e:
        logger.error(f"应用高斯模糊透明样式时发生错误: {e}")