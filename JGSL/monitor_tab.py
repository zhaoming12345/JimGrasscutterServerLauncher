from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QTextEdit, QLineEdit, QHBoxLayout, QDialog, QFormLayout, QDialogButtonBox
from PyQt5.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QObject, pyqtProperty, QEasingCurve, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QLinearGradient, QTextCursor
import psutil
import os
import json
import sys
import time
import datetime
import threading
from loguru import logger
import random # 导入 random 用于生成模拟数据


class CircleProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_value = 0  # 目标值
        self._current_value = 0 # 动画当前值
        self._animation = QPropertyAnimation(self, b'current_value', self) # 动画作用于 current_value
        self._animation.setDuration(500)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.setFixedSize(50, 50)

    # --- Public Method to Set Target --- 
    def set_value(self, target_value):
        # 限制 value 在 0-100
        target_value = max(0, min(100, int(target_value)))

        # 如果目标值与当前目标值相同，则不执行任何操作
        if self._target_value == target_value:
            return

        self._target_value = target_value

        # 如果动画正在运行，先停止
        if self._animation.state() == QPropertyAnimation.Running:
            self._animation.stop()

        # 设置动画的起始值和结束值
        self._animation.setStartValue(self._current_value) # 从当前动画值开始
        self._animation.setEndValue(target_value)

        # 启动动画
        try:
            self._animation.start()
        except Exception as e:
            logger.exception(f'CircleProgress - Failed to start animation: {e}')

    # --- Property for Animation --- 
    @pyqtProperty(int)
    def current_value(self):
        return self._current_value

    @current_value.setter
    def current_value(self, value):
        # 这个 setter 由 QPropertyAnimation 调用
        self._current_value = value
        self.update() # 触发重绘

    # --- Paint Event --- 
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制背景圆
            painter.setPen(Qt.NoPen) # 无边框
            painter.setBrush(QColor(230, 230, 230)) # 浅灰色背景
            painter.drawEllipse(0, 0, 50, 50)

            # 绘制进度条弧形
            painter.setPen(QPen(QColor(76, 175, 80), 3)) # 绿色，线宽3
            # painter.setBrush(Qt.NoBrush) # 不填充
            rect = QRect(2, 2, 46, 46) # 稍微内缩以适应边框
            start_angle = 90 * 16 # 12点钟方向
            span_angle = int(-self._current_value * 3.6 * 16) # 逆时针绘制
            painter.drawArc(rect, start_angle, span_angle)

            # 绘制中心文本
            painter.setPen(QColor(0, 0, 0)) # 黑色文字
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(QRect(0, 0, 50, 50), Qt.AlignCenter, f"{int(self._current_value)}%")
        except Exception as e:
            logger.exception(f'CircleProgress - Error during paintEvent: {e}')


class MonitorPanel(QDialog):
    def __init__(self, instance_name, pid, log_path, debug_mode=False):
        try:
            logger.debug('初始化监控面板 实例:{} PID:{} 日志路径:{} 调试模式:{}', instance_name, pid, log_path, debug_mode)
            super().__init__()
            self.instance_name = instance_name
            self.pid = pid
            self.log_path = log_path
            self.debug_mode = debug_mode # 保存调试模式状态

            self.cpu_usage = CircleProgress()
            self.mem_usage = CircleProgress()
            self.log_text = QTextEdit()
            self.command_input = QLineEdit()
            self.command_button = QPushButton('发送')
            self.stop_button = QPushButton('关闭实例')
            self.stop_button.setStyleSheet("QPushButton { background-color: red; color: white; }")

            # 根据调试模式设置控件和连接信号
            if self.debug_mode:
                self.setWindowTitle(f"{self.instance_name} (调试模式)")
                self.command_input.setPlaceholderText("调试模式下无法发送命令")
                self.command_input.setEnabled(False)
                self.command_button.setEnabled(False)
                self.stop_button.setText("关闭调试面板")
                self.stop_button.clicked.connect(self.close) # 调试模式下关闭按钮直接关闭窗口
                self.log_text.setPlainText("--- 调试模式日志 ---\n" +
                                        "这是模拟的日志输出\n" +
                                        f"时间: {datetime.datetime.now()}\n" +
                                        "CPU: 正在模拟...\n" +
                                        "内存: 正在模拟...\n")
            else:
                self.setWindowTitle(f"{self.instance_name}")
                self.command_button.clicked.connect(self.send_command)
                self.stop_button.clicked.connect(self.stop_instance)
                self.command_input.returnPressed.connect(self.send_command)

            self.log_timer = QTimer()
            self.log_timer.timeout.connect(self.update_log)
            self.resource_timer = QTimer()
            self.resource_timer.timeout.connect(self.update_resource_usage)
            self.resource_timer.start(1000)
            self.current_log = ""
            self.last_log_size = 0

            # 调试模式下不需要计算启动时间或读取真实日志
            if not self.debug_mode:
                try:
                    # 只有在非调试模式且 PID 有效时才计算启动时间
                    if self.pid and self.pid != -1 and psutil.pid_exists(self.pid):
                         self.start_time = datetime.datetime.now() - datetime.timedelta(seconds=time.time() - psutil.Process(self.pid).create_time())
                    else:
                        self.start_time = None # 无效 PID 则不设置启动时间
                        logger.warning("无法获取进程启动时间，PID无效或进程不存在")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.start_time = None
                    logger.error(f"获取进程创建时间失败: {e}")
                self.log_reader_thread = LogReaderThread(self.log_path) # 只有非调试模式才启动日志读取线程
                self.log_reader_thread.log_data_ready.connect(self.append_log)
                self.log_reader_thread.log_error.connect(self.handle_log_error)
                self.log_reader_thread.start()
            else:
                self.start_time = datetime.datetime.now() # 调试模式给个假的启动时间

            self.layout = QVBoxLayout()
            self.layout.addWidget(self.cpu_usage)
            self.layout.addWidget(self.mem_usage)
            self.layout.addWidget(self.stop_button)
            self.layout.addWidget(self.log_text)
            self.layout.addWidget(self.command_input)
            self.layout.addWidget(self.command_button)
            self.setLayout(self.layout)

            self.log_text.setReadOnly(True)
            self.log_text.setLineWrapMode(QTextEdit.NoWrap)
            self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.command_history = []
            # 调试模式下不需要启动 log_timer 
            if not self.debug_mode:
                self.log_timer.start(1000)
                self.update_log() # 非调试模式才需要立即更新日志
            self.update_resource_usage() # 首次更新资源
            logger.info('监控面板初始化成功完成 实例:{} PID:{} 调试模式:{}', instance_name, pid, debug_mode)
        except Exception as e:
            logger.exception('监控面板初始化失败')
            # 即使初始化失败也要尝试显示错误信息
            QMessageBox.critical(self, "错误", f"监控面板初始化失败: {e}")
            # raise # 不再抛出异常，避免程序崩溃

    def update_resource_usage(self):
        try:
            # 调试模式下使用模拟数据
            if self.debug_mode:
                try:
                    cpu_val = random.randint(10, 70)
                    self.cpu_usage.set_value(cpu_val)
                except Exception as e:
                    logger.exception(f'调试模式 - 设置 CPU 模拟值失败: {e}')

                try:
                    # 模拟内存使用，改为百分比
                    mem_val = random.randint(20, 80)
                    self.mem_usage.set_value(mem_val)
                except Exception as e:
                    logger.exception(f'调试模式 - 设置内存模拟值失败: {e}')

                self.update_uptime() # 调试模式也更新假的运行时间
            elif self.pid and self.pid != -1 and psutil.pid_exists(self.pid):
                proc = psutil.Process(self.pid)
                # 使用 set_value 来触发动画效果
                try:
                    cpu_percent = int(proc.cpu_percent(interval=0.1))
                    self.cpu_usage.set_value(cpu_percent)
                except Exception as e:
                    logger.exception(f'更新 CPU 使用率失败: {e}')
                    self.cpu_usage.set_value(0)

                try:
                    mem_percent = int(proc.memory_percent())
                    self.mem_usage.set_value(mem_percent) # 改为内存百分比
                except Exception as e:
                    logger.exception(f'更新内存使用率失败: {e}')
                    self.mem_usage.set_value(0)
                self.update_uptime()
            else:
                self.cpu_usage.set_value(0)
                self.mem_usage.set_value(0)
                # 只有在非调试模式下才记录 PID 无效的警告
                if not self.debug_mode:
                    logger.warning('无效PID:{} 进程状态:{}', self.pid, psutil.pid_exists(self.pid) if self.pid and self.pid != -1 else 'N/A')
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            # 进程消失或无权限访问，资源设为0
            logger.warning(f"访问进程 {self.pid} 信息失败: {e}, 设置值为 0")
            self.cpu_usage.set_value(0)
            self.mem_usage.set_value(0)
            # if not self.debug_mode:
            #     logger.warning(f"访问进程 {self.pid} 信息失败: {e}")
        except Exception as e:
            logger.error(f"更新资源使用情况时发生错误: {e}")
            # 即使发生错误也尝试将值设为0
            try:
                # logger.debug('更新资源 - 发生未知错误，尝试设置值为 0')
                self.cpu_usage.set_value(0)
                self.mem_usage.set_value(0)
            except Exception as inner_e:
                logger.error(f'尝试将资源设置为0时发生内部错误: {inner_e}')

    def update_uptime(self):
        if self.start_time:
            uptime = datetime.datetime.now() - self.start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            # 调试模式标题加上提示
            title_prefix = f"{self.instance_name} (调试模式)" if self.debug_mode else self.instance_name
            self.setWindowTitle(f"{title_prefix} 运行时间：{int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒")

    # 添加处理日志读取线程信号的方法
    def append_log(self, log_content):
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.insertPlainText(log_content)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def handle_log_error(self, error_message):
        logger.error(f"日志读取错误: {error_message}")
        self.log_text.append(f"<font color='red'>日志读取错误: {error_message}</font>")

    # send_command 和 stop_instance 在调试模式下不应该被调用，但保留以防万一
    def send_command(self):
        if self.debug_mode:
            logger.warning("尝试在调试模式下发送命令")
            return
        command = self.command_input.text()
        if not command:
            return
        logger.info(f'向实例 {self.instance_name} (PID: {self.pid}) 发送命令: {command}')
        # 这里需要实现真正的命令发送逻辑，例如通过 stdin 或其他 IPC 方式
        QMessageBox.information(self, "提示", f"命令 '{command}' 已发送 (功能实现中)")
        self.command_input.clear()
        self.command_history.append(command)

    def stop_instance(self):
        if self.debug_mode:
            logger.warning("尝试在调试模式下停止实例")
            self.close() # 调试模式下直接关闭窗口
            return
        reply = QMessageBox.question(self, '确认', f'确定要关闭实例 {self.instance_name} (PID: {self.pid}) 吗？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            logger.info(f'正在尝试关闭实例 {self.instance_name} (PID: {self.pid})')
            try:
                if self.pid and psutil.pid_exists(self.pid):
                    proc = psutil.Process(self.pid)
                    proc.terminate() # 尝试友好终止
                    try:
                        proc.wait(timeout=5) # 等待5秒
                        logger.success(f'实例 {self.instance_name} (PID: {self.pid}) 已成功终止')
                    except psutil.TimeoutExpired:
                        logger.warning(f'实例 {self.instance_name} (PID: {self.pid}) 未能在5秒内终止，尝试强制结束')
                        proc.kill() # 强制结束
                        proc.wait()
                        logger.success(f'实例 {self.instance_name} (PID: {self.pid}) 已强制结束')
                    self.close() # 关闭监控面板
                else:
                    logger.warning(f'实例 {self.instance_name} (PID: {self.pid}) 进程不存在或无效')
                    QMessageBox.warning(self, '错误', '进程不存在或无效')
                    self.close() # 进程不在了也关闭面板
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f'关闭实例 {self.instance_name} (PID: {self.pid}) 时出错: {e}')
                QMessageBox.critical(self, '错误', f'关闭进程时出错: {e}')
                self.close() # 出错了也关闭面板
            except Exception as e:
                logger.exception(f'关闭实例时发生未知错误: {e}')
                QMessageBox.critical(self, '错误', f'关闭进程时发生未知错误: {e}')
                self.close()

    # 重写 closeEvent，确保在关闭窗口时停止定时器和线程
    def closeEvent(self, event):
        # logger.debug(f"关闭监控面板: {self.instance_name} (调试模式: {self.debug_mode})")
        self.resource_timer.stop()
        self.log_timer.stop()
        # 只有非调试模式才有日志读取线程
        if not self.debug_mode and hasattr(self, 'log_reader_thread') and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()
        super().closeEvent(event)

    # update_log 在调试模式下不需要，但保留框架
    def update_log(self):
        if self.debug_mode:
            # 调试模式下可以模拟一些日志更新
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            log_line = f"[{current_time}] 模拟日志条目 CPU: {self.cpu_usage.value}%, Mem: {self.mem_usage.value}MB\n"
            self.append_log(log_line)
            # 限制日志行数，防止过多卡顿
            if self.log_text.document().lineCount() > 50:
                 cursor = self.log_text.textCursor()
                 cursor.movePosition(QTextEdit.Start)
                 cursor.movePosition(QTextEdit.Down, QTextEdit.KeepAnchor, self.log_text.document().lineCount() - 50)
                 cursor.removeSelectedText()
                 cursor.movePosition(QTextEdit.End)
                 self.log_text.setTextCursor(cursor)
            return

        # 以下是非调试模式的原有逻辑，现在由 LogReaderThread 处理
        # try:
        #     if not os.path.exists(self.log_path):
        #         self.log_text.append(f"<font color='red'>日志文件不存在: {self.log_path}</font>")
        #         return
        #     # ... 原有的 update_log 逻辑 ...
        # except Exception as e:
        #     logger.error(f"更新日志时发生错误: {e}")
        pass # 非调试模式的日志更新由 LogReaderThread 负责


class LogReaderThread(QThread):
    log_data_ready = pyqtSignal(str)
    log_error = pyqtSignal(str)
    
    def __init__(self, log_path):
        super().__init__()
        self.log_path = log_path
        self.last_log_size = 0
        self.running = True
        
    def run(self):
        logger.info(f"启动日志读取线程: {self.log_path}")
        while self.running:
            try:
                if not os.path.exists(self.log_path):
                    # 日志文件不存在是正常情况（例如实例刚启动还没生成日志），不需要报错
                    time.sleep(1) # 等待一下再检查
                    continue
                    
                try:
                    current_size = os.path.getsize(self.log_path)
                    # 只有当文件变大时才读取新增内容
                    if current_size > self.last_log_size:
                        try:
                            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                                f.seek(self.last_log_size) # 定位到上次读取的位置
                                new_log = f.read() # 读取新增的内容
                            
                            if new_log: # 确保有新内容才发送信号
                                self.log_data_ready.emit(new_log)
                            self.last_log_size = current_size # 更新最后读取的大小
                        except UnicodeDecodeError as ude:
                            logger.warning('日志文件编码错误: {}', str(ude))
                            self.log_error.emit(f'日志文件编码错误，请检查文件编码')
                            # 编码错误时不再尝试其他编码，直接报告错误
                            time.sleep(5) # 避免频繁报错
                        except Exception as e:
                            self.log_error.emit(f'读取日志文件时发生错误: {str(e)}')
                            time.sleep(1)
                    elif current_size < self.last_log_size:
                        # 文件变小了，可能是日志轮转或被清空了，重置大小
                        logger.info(f"日志文件 {self.log_path} 大小减小，可能已轮转或清空，重置读取位置")
                        self.last_log_size = 0 # 从头开始读取
                        # 可以选择性地清空显示区域或发送一个提示信息
                        self.log_error.emit("日志文件已重置")

                except FileNotFoundError:
                     # 文件在检查大小和打开之间被删除了，忽略这次错误，下次循环会处理
                     logger.warning(f"检查日志文件 {self.log_path} 时文件消失了")
                     self.last_log_size = 0 # 重置大小
                     time.sleep(1)
                except Exception as e:
                    self.log_error.emit(f'检查日志文件大小时发生错误: {str(e)}')
                    time.sleep(1)
                
                time.sleep(0.5) # 稍微降低检查频率
            except Exception as e:
                self.log_error.emit(f'日志读取线程发生严重错误: {str(e)}')
                logger.exception("日志读取线程崩溃")
                self.running = False # 发生严重错误时停止线程
        logger.info(f"日志读取线程停止: {self.log_path}")
    
    def stop(self):
        # logger.debug(f"请求停止日志读取线程: {self.log_path}")
        self.running = False
        # 不需要 quit() 和 wait()，让 run 循环自然结束


# MonitorTab 类保持不变，因为它只负责启动 MonitorPanel 
class MonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.instance_list = QListWidget()
        self.db_status = QLabel("数据库状态：未连接")
        self.instance_status = QLabel("运行实例数：0")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.instance_status)
        self.layout.addWidget(QLabel("运行实例:"))
        self.layout.addWidget(self.instance_list)
        self.layout.addWidget(self.db_status)
        self.start_btn = QPushButton('打开监控面板')
        self.start_btn.clicked.connect(self.open_monitor_panel)
        self.refresh_btn = QPushButton('手动刷新')
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.start_btn)
        self.btn_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(self.btn_layout)
        self.setLayout(self.layout)
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resource_usage)
        self.resource_timer.start(1000)
        self.running_instances = []
        # 使用相对路径获取根目录
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.refresh_btn.clicked.connect(self.on_manual_refresh)

    def open_monitor_panel(self):
        if not self.instance_list.currentItem():
            QMessageBox.warning(self, '警告', '请先选择一个运行实例')
            return
        instance_name = self.instance_list.currentItem().text()
        # 从 running_instances 中查找选定实例的信息
        selected_instance_info = None
        for pid, path in self.running_instances:
            if os.path.basename(path) == instance_name:
                selected_instance_info = (pid, path)
                break
        
        if not selected_instance_info:
             QMessageBox.warning(self, '错误', '选择的实例信息丢失或已停止运行，请刷新列表')
             return

        pid, instance_path = selected_instance_info
        log_file_path = os.path.join(instance_path, "logs", "latest.log")
        lock_path = os.path.join(instance_path, "Running.lock")

        # 再次确认进程是否存在
        if not pid or not psutil.pid_exists(pid):
            QMessageBox.warning(self, '错误', '选择的实例未运行或进程已消失')
            self.scan_running_instances() # 刷新列表
            return
        try:
            proc = psutil.Process(pid)
            # 检查进程名是否是 java.exe (Windows) 或 java (Linux/macOS) 
            if not proc.name().lower().startswith("java"):
                logger.warning('进程类型异常 PID:{} 名称:{} 期望:java*', pid, proc.name())
                QMessageBox.warning(self, '错误', '选择的实例似乎不是Java进程')
                self.scan_running_instances() # 刷新列表
                return
            # 使用 self.monitor_panel 存储引用，防止闪退
            self.monitor_panel = MonitorPanel(instance_name, pid, log_file_path)
            self.monitor_panel.show() # 使用 show() 而不是 exec_() 避免阻塞
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"访问进程 {pid} 信息失败: {e}")
            QMessageBox.critical(self, '错误', f'无法访问进程信息: {e}')
            self.scan_running_instances() # 刷新列表
        except Exception as e:
            logger.error(f"打开监控面板时发生错误: {e}")
            QMessageBox.critical(self, '错误', f'打开监控面板失败: {e}')

    def update_resource_usage(self):
        try:
            db_status = False
            for proc in psutil.process_iter(['name', 'cmdline']):
                if proc.info['name'] == "mongod.exe" and any('dbpath' in part for part in proc.info['cmdline']):
                    db_status = True
            if db_status:
                self.db_status.setText("数据库状态：已连接")
            else:
                self.db_status.setText("数据库状态：未连接")
        except Exception as e:
            logger.error(f"更新资源使用情况时发生错误: {e}")

    def scan_running_instances(self):
        new_running_instances = []
        servers_path = os.path.join(self.root_dir, 'Servers')
        if not os.path.exists(servers_path):
            # 目录不存在就不扫描了
            logger.warning(f'服务器目录 {servers_path} 不存在，无法扫描实例')
            self.running_instances = []
            self.update_instance_display()
            return

        for instance_name in os.listdir(servers_path):
            instance_path = os.path.join(servers_path, instance_name)
            if os.path.isdir(instance_path):
                lock_path = os.path.join(instance_path, "Running.lock")
                if os.path.exists(lock_path):
                    try:
                        with open(lock_path, 'r', encoding='utf-8') as f:
                            lock_data = json.load(f)
                        pid = lock_data.get("pid")
                        if not pid:
                            logger.warning(f'Lock 文件 {lock_path} 中缺少 PID')
                            continue
                        # 检查 PID 是否有效且进程名是否正确
                        if psutil.pid_exists(pid):
                            try:
                                proc = psutil.Process(pid)
                                # 检查进程名是否是 java.exe (Windows) 或 java (Linux/macOS) 
                                if proc.name().lower().startswith("java"):
                                    new_running_instances.append((pid, instance_path))
                                else:
                                    logger.warning(f'PID {pid} 进程名称不符: {proc.name()} (来自 {instance_name})，清理 lock 文件')
                                    os.remove(lock_path) # 清理无效的 lock 文件
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                logger.warning(f'无法访问 PID {pid} (来自 {instance_name})，可能已退出，清理 lock 文件')
                                os.remove(lock_path) # 清理无效的 lock 文件
                        else:
                            logger.warning(f'PID {pid} (来自 {instance_name}) 不存在，清理 lock 文件')
                            os.remove(lock_path) # 清理无效的 lock 文件
                    except json.JSONDecodeError:
                        logger.error(f"Lock 文件 {lock_path} 内容不合法，已忽略")
                        # 可以考虑删除或重命名损坏的 lock 文件
                    except Exception as e:
                        logger.error(f"处理实例 {instance_name} 时发生错误: {e}")
        
        # 比较新旧列表，只在有变化时更新显示
        if set(new_running_instances) != set(self.running_instances):
            logger.info(f"运行实例列表已更新，当前数量: {len(new_running_instances)}")
            self.running_instances = new_running_instances
            self.update_instance_display()
        current_item = self.instance_list.currentItem()
        current_selected = current_item.text() if current_item else None
        
        self.instance_list.clear()
        instance_names = sorted([os.path.basename(path) for pid, path in self.running_instances])
        self.instance_list.addItems(instance_names)
        self.instance_status.setText(f"运行实例数：{len(self.running_instances)}")
        
        # 尝试恢复之前的选中项
        if current_selected:
            items = self.instance_list.findItems(current_selected, Qt.MatchExactly)
            if items:
                self.instance_list.setCurrentItem(items[0])

    def update_instance_display(self):
        """更新实例列表显示"""
        current_item = self.instance_list.currentItem()
        current_selected = current_item.text() if current_item else None
        
        self.instance_list.clear()
        instance_names = sorted([os.path.basename(path) for pid, path in self.running_instances])
        self.instance_list.addItems(instance_names)
        self.instance_status.setText(f"运行实例数：{len(self.running_instances)}")
        
        # 尝试恢复之前的选中项
        if current_selected:
            items = self.instance_list.findItems(current_selected, Qt.MatchExactly)
            if items:
                self.instance_list.setCurrentItem(items[0])
                
    def on_manual_refresh(self):
        logger.info("手动刷新实例列表")
        self.scan_running_instances() # 手动刷新直接调用扫描函数