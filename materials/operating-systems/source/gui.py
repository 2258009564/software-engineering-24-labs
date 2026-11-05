"""
图形用户界面模块
==================
基于 PyQt5 实现的进程调度系统图形界面。

包含五大功能面板：
    1. 进程管理面板 - 创建、撤销、挂起、激活进程
    2. 资源监控面板 - 实时显示内存使用情况和分配状态
    3. 调度可视化面板 - 甘特图展示调度过程
    4. 性能分析面板 - 多算法性能对比图表
    5. 操作日志面板 - 显示所有操作记录

界面采用选项卡（TabWidget）布局，风格简洁专业。
"""

import sys
from typing import List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QTextEdit, QMessageBox, QFileDialog,
    QProgressBar, QFrame, QSplitter, QScrollArea, QGridLayout,
    QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPalette, QPixmap,
    QLinearGradient, QRadialGradient
)

from pcb import PCB, ProcessState, ProcessType
from process_manager import ProcessManager
from resource_manager import ResourceManager
from scheduler import (
    get_scheduler, ScheduleResult, ScheduleEvent,
    FCFSScheduler, SJFScheduler, RRScheduler, EDFScheduler, RMSScheduler
)
from performance import PerformanceAnalyzer

# ============================================================
# 全局样式
# ============================================================
STYLESHEET = """
QMainWindow {
    background-color: #f5f6fa;
}
QTabWidget::pane {
    border: 1px solid #dcdde1;
    background: white;
    border-radius: 4px;
}
QTabWidget::tab-bar {
    alignment: center;
}
QTabBar::tab {
    background: #dcdde1;
    color: #2d3436;
    padding: 8px 24px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
    font-size: 13px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #0984e3;
    color: white;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #dcdde1;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #0984e3;
    color: white;
    border: none;
    padding: 7px 16px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #0873c4;
}
QPushButton:pressed {
    background-color: #0762a8;
}
QPushButton:disabled {
    background-color: #b2bec3;
}
QPushButton[danger="true"] {
    background-color: #e17055;
}
QPushButton[danger="true"]:hover {
    background-color: #d63031;
}
QTableWidget {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    background: white;
    alternate-background-color: #f8f9fa;
    gridline-color: #ecf0f1;
    font-size: 12px;
}
QHeaderView::section {
    background-color: #0984e3;
    color: white;
    padding: 6px;
    border: none;
    font-weight: bold;
    font-size: 12px;
}
QTextEdit {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    background: #2d3436;
    color: #00ff88;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
}
QLabel {
    font-size: 12px;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    padding: 5px 8px;
    border: 1px solid #dcdde1;
    border-radius: 4px;
    font-size: 12px;
}
QProgressBar {
    border: 1px solid #dcdde1;
    border-radius: 4px;
    text-align: center;
    font-size: 12px;
}
QProgressBar::chunk {
    background-color: #0984e3;
    border-radius: 3px;
}
"""

# 进程状态颜色映射
STATE_COLORS = {
    ProcessState.NEW: QColor("#74b9ff"),
    ProcessState.READY: QColor("#55efc4"),
    ProcessState.RUNNING: QColor("#fdcb6e"),
    ProcessState.WAITING: QColor("#fd79a8"),
    ProcessState.SUSPENDED: QColor("#a29bfe"),
    ProcessState.TERMINATED: QColor("#b2bec3"),
}

# 甘特图进程颜色（循环使用）
GANTT_COLORS = [
    QColor("#0984e3"), QColor("#00b894"), QColor("#fdcb6e"),
    QColor("#e17055"), QColor("#a29bfe"), QColor("#00cec9"),
    QColor("#fab1a0"), QColor("#55efc4"), QColor("#74b9ff"),
    QColor("#ffeaa7"),
]


# ============================================================
# 甘特图绘制组件
# ============================================================
class GanttChartWidget(QWidget):
    """
    甘特图组件
    ==========
    自定义绘制调度过程的时间线，直观展示每个进程的执行时段。
    """

    def __init__(self):
        super().__init__()
        self.events: List[ScheduleEvent] = []
        self.algorithm_name: str = ""
        self.setMinimumHeight(250)

    def set_data(self, result: ScheduleResult):
        """设置甘特图数据"""
        self.events = result.events
        self.algorithm_name = result.algorithm_name
        self.update()

    def clear(self):
        """清空甘特图"""
        self.events = []
        self.algorithm_name = ""
        self.update()

    def paintEvent(self, event):
        """绘制甘特图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        margin_left = 50
        margin_right = 30
        margin_top = 40
        margin_bottom = 50
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # 绘制标题
        painter.setPen(QPen(QColor("#2d3436")))
        font_title = QFont("Microsoft YaHei", 11, QFont.Bold)
        painter.setFont(font_title)
        if self.algorithm_name:
            painter.drawText(QRect(0, 5, width, 30), Qt.AlignCenter,
                             f"调度甘特图 — {self.algorithm_name}")
        else:
            painter.drawText(QRect(0, 5, width, 30), Qt.AlignCenter,
                             "调度甘特图（请先执行调度）")
            painter.end()
            return

        if not self.events:
            painter.setPen(QPen(QColor("#b2bec3")))
            painter.drawText(QRect(margin_left, margin_top, chart_width, chart_height),
                             Qt.AlignCenter, "暂无调度数据")
            painter.end()
            return

        # 计算时间范围
        max_time = max(e.end_time for e in self.events)
        if max_time <= 0:
            max_time = 1

        # 绘制坐标轴
        painter.setPen(QPen(QColor("#636e72"), 2))
        # 横轴
        painter.drawLine(margin_left, margin_top + chart_height,
                        margin_left + chart_width, margin_top + chart_height)
        # 纵轴
        painter.drawLine(margin_left, margin_top,
                        margin_left, margin_top + chart_height)

        # 绘制时间刻度
        painter.setPen(QPen(QColor("#636e72")))
        font_small = QFont("Microsoft YaHei", 8)
        painter.setFont(font_small)
        num_ticks = min(20, int(max_time) + 1)
        for i in range(num_ticks + 1):
            tick_val = (max_time / num_ticks) * i
            x = margin_left + (chart_width / num_ticks) * i
            # 刻度线
            painter.drawLine(int(x), margin_top + chart_height,
                           int(x), margin_top + chart_height + 5)
            # 刻度标签
            painter.drawText(QRect(int(x) - 20, margin_top + chart_height + 5,
                                   40, 20), Qt.AlignCenter, f"{tick_val:.1f}")

        # 绘制时间轴标签
        font_label = QFont("Microsoft YaHei", 9)
        painter.setFont(font_label)
        painter.drawText(QRect(margin_left, height - 20, chart_width, 20),
                         Qt.AlignCenter, "时间")

        # 绘制甘特条
        bar_height = min(50, chart_height - 30)
        bar_y = margin_top + (chart_height - bar_height) // 2
        pid_color_map = {}

        for e in self.events:
            x_start = margin_left + (e.start_time / max_time) * chart_width
            x_end = margin_left + (e.end_time / max_time) * chart_width
            bar_width = max(x_end - x_start, 2)

            if e.is_idle:
                color = QColor("#dfe6e9")
            else:
                if e.pid not in pid_color_map:
                    pid_color_map[e.pid] = GANTT_COLORS[len(pid_color_map) % len(GANTT_COLORS)]
                color = pid_color_map[e.pid]

            # 绘制条形
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#2d3436"), 1))
            rect = QRect(int(x_start), bar_y, int(bar_width), bar_height)
            painter.drawRoundedRect(rect, 4, 4)

            # 绘制进程名（如果条够宽）
            if bar_width > 40:
                painter.setPen(QPen(QColor("#ffffff" if not e.is_idle else "#636e72")))
                font_name = QFont("Microsoft YaHei", 9, QFont.Bold)
                painter.setFont(font_name)
                painter.drawText(rect, Qt.AlignCenter, e.name)

        # 绘制PID图例
        legend_y = margin_top + chart_height + 25
        legend_x = margin_left
        for pid, color in pid_color_map.items():
            if pid == -1:
                continue
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#2d3436"), 1))
            painter.drawRoundedRect(int(legend_x), legend_y, 15, 15, 2, 2)
            # 找到进程名
            name = next((e.name for e in self.events if e.pid == pid), f"P{pid}")
            painter.setPen(QPen(QColor("#2d3436")))
            painter.setFont(font_small)
            painter.drawText(QRect(int(legend_x) + 18, legend_y - 2, 100, 18),
                           Qt.AlignLeft | Qt.AlignVCenter, name)
            legend_x += 120
            if legend_x > width - 100:
                legend_x = margin_left
                legend_y += 20

        painter.end()


# ============================================================
# 内存使用图组件
# ============================================================
class MemoryBarWidget(QWidget):
    """
    内存使用条形图组件
    ==================
    以可视化方式展示内存的分配情况。
    """

    def __init__(self):
        super().__init__()
        self.total = 1024
        self.used = 0
        self.blocks = []  # 内存块列表
        self.setMinimumHeight(120)

    def set_data(self, total: int, used: int, blocks=None):
        """设置内存数据"""
        self.total = max(total, 1)
        self.used = used
        self.blocks = blocks or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width() - 100
        height = 60
        x = 50
        y = 30

        # 绘制背景（总内存）
        painter.setBrush(QBrush(QColor("#ecf0f1")))
        painter.setPen(QPen(QColor("#b2bec3"), 2))
        painter.drawRoundedRect(x, y, width, height, 6, 6)

        # 绘制已使用部分
        if self.total > 0 and self.used > 0:
            used_width = int(width * self.used / self.total)
            # 渐变色
            gradient = QLinearGradient(x, y, x + used_width, y)
            gradient.setColorAt(0, QColor("#0984e3"))
            gradient.setColorAt(1, QColor("#00b894"))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, used_width, height, 6, 6)

        # 文字
        painter.setPen(QPen(QColor("#2d3436")))
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        painter.setFont(font)
        pct = (self.used / self.total * 100) if self.total > 0 else 0
        painter.drawText(QRect(x, y, width, height), Qt.AlignCenter,
                        f"已用 {self.used}MB / 总共 {self.total}MB  ({pct:.1f}%)")

        painter.end()


# ============================================================
# 进程管理面板
# ============================================================
class ProcessPanel(QWidget):
    """
    进程管理面板
    ============
    提供创建、撤销、挂起、激活进程的图形界面操作。
    """

    process_updated = pyqtSignal()  # 进程变更信号

    def __init__(self, pm: ProcessManager):
        super().__init__()
        self.pm = pm
        self._init_ui()
        self._refresh_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # === 创建进程区域 ===
        create_group = QGroupBox("创建新进程")
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("如：进程A")
        form_layout.addRow("进程名称：", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["批处理", "分时", "实时"])
        form_layout.addRow("进程类型：", self.type_combo)

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 99)
        self.priority_spin.setValue(0)
        form_layout.addRow("优先级：", self.priority_spin)

        self.arrival_spin = QDoubleSpinBox()
        self.arrival_spin.setRange(0, 999)
        self.arrival_spin.setValue(0)
        self.arrival_spin.setSuffix(" s")
        form_layout.addRow("到达时间：", self.arrival_spin)

        self.burst_spin = QDoubleSpinBox()
        self.burst_spin.setRange(0.5, 999)
        self.burst_spin.setValue(5)
        self.burst_spin.setSuffix(" s")
        form_layout.addRow("服务时间：", self.burst_spin)

        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(1, 2048)
        self.memory_spin.setValue(64)
        self.memory_spin.setSuffix(" MB")
        form_layout.addRow("内存需求：", self.memory_spin)

        self.deadline_spin = QDoubleSpinBox()
        self.deadline_spin.setRange(0, 999)
        self.deadline_spin.setValue(0)
        self.deadline_spin.setSuffix(" s")
        form_layout.addRow("截止时间：", self.deadline_spin)

        self.period_spin = QDoubleSpinBox()
        self.period_spin.setRange(0, 999)
        self.period_spin.setValue(0)
        self.period_spin.setSuffix(" s")
        form_layout.addRow("周期：", self.period_spin)

        create_group.setLayout(form_layout)
        layout.addWidget(create_group)

        # 创建/清空按钮
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("  创建进程  ")
        create_btn.clicked.connect(self._create_process)
        btn_layout.addWidget(create_btn)

        batch_btn = QPushButton("  批量添加示例  ")
        batch_btn.clicked.connect(self._add_sample_processes)
        btn_layout.addWidget(batch_btn)

        clear_btn = QPushButton("  清空全部  ")
        clear_btn.setProperty("danger", True)
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        # === 进程列表 ===
        list_group = QGroupBox("进程列表")
        list_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["PID", "进程名", "状态", "类型", "优先级", "到达时间", "服务时间", "内存(MB)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.table)

        # 操作按钮
        op_layout = QHBoxLayout()
        suspend_btn = QPushButton("  挂起  ")
        suspend_btn.clicked.connect(self._suspend_process)
        op_layout.addWidget(suspend_btn)

        activate_btn = QPushButton("  激活  ")
        activate_btn.clicked.connect(self._activate_process)
        op_layout.addWidget(activate_btn)

        destroy_btn = QPushButton("  撤销  ")
        destroy_btn.setProperty("danger", True)
        destroy_btn.clicked.connect(self._destroy_process)
        op_layout.addWidget(destroy_btn)

        list_layout.addLayout(op_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        layout.addStretch()

    def _create_process(self):
        """创建进程"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入进程名称")
            return

        type_map = {"批处理": ProcessType.BATCH, "分时": ProcessType.TIME_SHARING,
                    "实时": ProcessType.REALTIME}
        ptype = type_map[self.type_combo.currentText()]

        pcb = self.pm.create_process(
            name=name, ptype=ptype, priority=self.priority_spin.value(),
            arrival_time=self.arrival_spin.value(),
            burst_time=self.burst_spin.value(),
            memory_size=self.memory_spin.value(),
            deadline=self.deadline_spin.value(),
            period=self.period_spin.value()
        )

        if pcb:
            self.name_input.clear()
            self._refresh_table()
            self.process_updated.emit()
        else:
            QMessageBox.warning(self, "创建失败", "内存不足，无法创建进程！")

    def _add_sample_processes(self):
        """添加示例进程"""
        samples = [
            ("进程A", ProcessType.BATCH, 0, 0, 8, 128),
            ("进程B", ProcessType.BATCH, 1, 1, 4, 64),
            ("进程C", ProcessType.TIME_SHARING, 2, 2, 6, 256),
            ("进程D", ProcessType.TIME_SHARING, 3, 3, 3, 128),
            ("进程E", ProcessType.REALTIME, 4, 0, 5, 64),
        ]
        for name, ptype, prio, arrival, burst, mem in samples:
            self.pm.create_process(name=name, ptype=ptype, priority=prio,
                                   arrival_time=arrival, burst_time=burst,
                                   memory_size=mem)
        self._refresh_table()
        self.process_updated.emit()

    def _clear_all(self):
        """清空所有进程"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有进程吗？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.pm.clear()
            self._refresh_table()
            self.process_updated.emit()

    def _get_selected_pid(self) -> Optional[int]:
        """获取选中行的PID"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个进程")
            return None
        return int(self.table.item(row, 0).text())

    def _suspend_process(self):
        """挂起进程"""
        pid = self._get_selected_pid()
        if pid and self.pm.suspend_process(pid):
            self._refresh_table()
            self.process_updated.emit()

    def _activate_process(self):
        """激活进程"""
        pid = self._get_selected_pid()
        if pid and self.pm.activate_process(pid):
            self._refresh_table()
            self.process_updated.emit()

    def _destroy_process(self):
        """撤销进程"""
        pid = self._get_selected_pid()
        if pid:
            reply = QMessageBox.question(self, "确认", f"确定要撤销 PID={pid} 的进程吗？",
                                          QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.pm.destroy_process(pid)
                self._refresh_table()
                self.process_updated.emit()

    def _refresh_table(self):
        """刷新进程表格"""
        procs = self.pm.get_all_processes()
        self.table.setRowCount(len(procs))
        for i, p in enumerate(procs):
            self.table.setItem(i, 0, QTableWidgetItem(str(p.pid)))
            self.table.setItem(i, 1, QTableWidgetItem(p.name))
            state_item = QTableWidgetItem(p.state.value)
            state_item.setBackground(STATE_COLORS.get(p.state, QColor("#ffffff")))
            self.table.setItem(i, 2, state_item)
            self.table.setItem(i, 3, QTableWidgetItem(p.ptype.value))
            self.table.setItem(i, 4, QTableWidgetItem(str(p.priority)))
            self.table.setItem(i, 5, QTableWidgetItem(str(p.arrival_time)))
            self.table.setItem(i, 6, QTableWidgetItem(str(p.burst_time)))
            self.table.setItem(i, 7, QTableWidgetItem(str(p.memory_size)))


# ============================================================
# 调度可视化面板
# ============================================================
class SchedulerPanel(QWidget):
    """
    调度可视化面板
    ==============
    选择调度算法并执行，以甘特图形式展示调度结果。
    """

    schedule_done = pyqtSignal(ScheduleResult)

    def __init__(self, pm: ProcessManager):
        super().__init__()
        self.pm = pm
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 算法选择区域
        control_group = QGroupBox("调度控制")
        control_layout = QHBoxLayout()

        control_layout.addWidget(QLabel("选择算法："))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "FCFS - 先来先服务（批处理）",
            "SJF - 短作业优先（批处理）",
            "RR - 时间片轮转（分时）",
            "EDF - 最早截止时间优先（实时）",
            "RMS - 速率单调调度（实时）",
        ])
        control_layout.addWidget(self.algo_combo)

        control_layout.addWidget(QLabel("时间片："))
        self.quantum_spin = QDoubleSpinBox()
        self.quantum_spin.setRange(0.5, 20)
        self.quantum_spin.setValue(2.0)
        self.quantum_spin.setSuffix(" s")
        control_layout.addWidget(self.quantum_spin)

        run_btn = QPushButton("  执行调度  ")
        run_btn.clicked.connect(self._run_schedule)
        control_layout.addWidget(run_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 甘特图
        self.gantt_widget = GanttChartWidget()
        layout.addWidget(self.gantt_widget, stretch=1)

        # 调度结果统计表
        stats_group = QGroupBox("调度结果统计")
        stats_layout = QVBoxLayout()
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels(
            ["PID", "进程名", "到达时间", "服务时间", "完成时间", "周转时间", "等待时间"]
        )
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setAlternatingRowColors(True)
        stats_layout.addWidget(self.stats_table)

        # 汇总信息
        self.summary_label = QLabel("请执行调度以查看结果")
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0984e3; padding: 8px;")
        stats_layout.addWidget(self.summary_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

    def _run_schedule(self):
        """执行调度"""
        processes = self.pm.get_all_processes()
        if not processes:
            QMessageBox.warning(self, "提示", "请先创建进程！")
            return

        algo_map = {"FCFS": "FCFS", "SJF": "SJF", "RR": "RR", "EDF": "EDF", "RMS": "RMS"}
        algo_text = self.algo_combo.currentText()
        algo_key = algo_text.split(" ")[0]
        algo_name = algo_map.get(algo_key, "FCFS")

        import copy
        proc_copy = copy.deepcopy(processes)
        for p in proc_copy:
            p.reset()

        scheduler = get_scheduler(algo_name)
        result = scheduler.schedule(proc_copy, self.quantum_spin.value())

        # 显示甘特图
        self.gantt_widget.set_data(result)

        # 显示统计表
        self.stats_table.setRowCount(len(result.process_stats))
        for i, (pid, stats) in enumerate(result.process_stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(pid)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(stats["进程名"])))
            self.stats_table.setItem(i, 2, QTableWidgetItem(str(stats["到达时间"])))
            self.stats_table.setItem(i, 3, QTableWidgetItem(str(stats["服务时间"])))
            self.stats_table.setItem(i, 4, QTableWidgetItem(str(stats["完成时间"])))
            self.stats_table.setItem(i, 5, QTableWidgetItem(str(stats["周转时间"])))
            self.stats_table.setItem(i, 6, QTableWidgetItem(str(stats["等待时间"])))

        # 汇总
        summary = (f"算法：{result.algorithm_name}  |  "
                   f"总时间：{result.total_time:.1f}s  |  "
                   f"平均周转：{result.avg_turnaround_time:.2f}s  |  "
                   f"平均等待：{result.avg_waiting_time:.2f}s  |  "
                   f"平均响应：{result.avg_response_time:.2f}s  |  "
                   f"CPU利用率：{result.cpu_utilization:.1f}%")
        self.summary_label.setText(summary)

        self.schedule_done.emit(result)


# ============================================================
# 资源监控面板
# ============================================================
class ResourcePanel(QWidget):
    """
    资源监控面板
    ============
    实时显示内存使用情况和分配详情。
    """

    def __init__(self, pm: ProcessManager):
        super().__init__()
        self.pm = pm
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 内存使用概览
        overview_group = QGroupBox("内存使用概览")
        overview_layout = QVBoxLayout()
        self.memory_bar = MemoryBarWidget()
        overview_layout.addWidget(self.memory_bar)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-size: 13px; padding: 8px;")
        overview_layout.addWidget(self.info_label)

        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)

        # 内存块详情表
        block_group = QGroupBox("内存分区详情")
        block_layout = QVBoxLayout()
        self.block_table = QTableWidget()
        self.block_table.setColumnCount(4)
        self.block_table.setHorizontalHeaderLabels(["起始地址", "大小(MB)", "状态", "占用PID"])
        self.block_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.block_table.setAlternatingRowColors(True)
        block_layout.addWidget(self.block_table)
        block_group.setLayout(block_layout)
        layout.addWidget(block_group)

        layout.addStretch()

    def refresh(self):
        """刷新内存显示"""
        info = self.pm.get_memory_info()
        rm = self.pm.resource_manager
        self.memory_bar.set_data(info["总内存(MB)"], info["已用内存(MB)"], rm.blocks)

        info_text = (
            f"  总内存：{info['总内存(MB)']}MB    "
            f"已使用：{info['已用内存(MB)']}MB    "
            f"可用：{info['可用内存(MB)']}MB    "
            f"利用率：{info['内存利用率(%)']}%    "
            f"空闲块：{info['空闲块数']}    "
            f"已分配块：{info['已分配块数']}"
        )
        self.info_label.setText(info_text)

        blocks = rm.get_block_list()
        self.block_table.setRowCount(len(blocks))
        for i, b in enumerate(blocks):
            self.block_table.setItem(i, 0, QTableWidgetItem(str(b["起始地址"])))
            self.block_table.setItem(i, 1, QTableWidgetItem(str(b["大小(MB)"])))
            status_item = QTableWidgetItem(b["状态"])
            if b["状态"] == "已分配":
                status_item.setBackground(QColor("#fab1a0"))
            else:
                status_item.setBackground(QColor("#55efc4"))
            self.block_table.setItem(i, 2, status_item)
            self.block_table.setItem(i, 3, QTableWidgetItem(str(b["PID"])))


# ============================================================
# 性能分析面板
# ============================================================
class PerformancePanel(QWidget):
    """
    性能分析面板
    ============
    对所有进程运行五种调度算法，对比性能指标。
    """

    def __init__(self, pm: ProcessManager):
        super().__init__()
        self.pm = pm
        self.analyzer = PerformanceAnalyzer()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 控制按钮
        ctrl_layout = QHBoxLayout()
        run_all_btn = QPushButton("  运行全部算法对比  ")
        run_all_btn.clicked.connect(self._run_comparison)
        ctrl_layout.addWidget(run_all_btn)

        export_btn = QPushButton("  导出CSV  ")
        export_btn.clicked.connect(self._export_csv)
        ctrl_layout.addWidget(export_btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # 对比表格
        table_group = QGroupBox("算法性能对比")
        table_layout = QVBoxLayout()
        self.compare_table = QTableWidget()
        self.compare_table.setColumnCount(5)
        self.compare_table.setHorizontalHeaderLabels(
            ["算法", "平均周转时间", "平均等待时间", "平均响应时间", "CPU利用率"]
        )
        self.compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.compare_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.compare_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 分析报告
        report_group = QGroupBox("分析报告")
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        report_group.setLayout(report_layout)
        layout.addWidget(report_group, stretch=1)

    def _run_comparison(self):
        """运行所有算法对比"""
        processes = self.pm.get_all_processes()
        if len(processes) < 2:
            QMessageBox.warning(self, "提示", "请至少创建2个进程！")
            return

        self.analyzer.run_all(processes)
        data = self.analyzer.get_comparison_data()

        # 更新表格
        self.compare_table.setRowCount(len(data["algorithms"]))
        for i, algo in enumerate(data["algorithms"]):
            result = self.analyzer.results[algo]
            self.compare_table.setItem(i, 0, QTableWidgetItem(result.algorithm_name))
            self.compare_table.setItem(i, 1, QTableWidgetItem(f"{data['avg_turnaround'][i]:.2f}"))
            self.compare_table.setItem(i, 2, QTableWidgetItem(f"{data['avg_waiting'][i]:.2f}"))
            self.compare_table.setItem(i, 3, QTableWidgetItem(f"{data['avg_response'][i]:.2f}"))
            self.compare_table.setItem(i, 4, QTableWidgetItem(f"{data['cpu_utilization'][i]:.1f}%"))

        # 显示报告
        self.report_text.setPlainText(self.analyzer.get_comparison_report())

    def _export_csv(self):
        """导出CSV"""
        if not self.analyzer.results:
            QMessageBox.warning(self, "提示", "请先运行对比分析！")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "调度算法性能对比.csv", "CSV文件 (*.csv)")
        if filepath:
            self.analyzer.export_to_csv(filepath)
            QMessageBox.information(self, "成功", f"数据已导出至：{filepath}")


# ============================================================
# 操作日志面板
# ============================================================
class LogPanel(QWidget):
    """操作日志面板"""

    def __init__(self, pm: ProcessManager):
        super().__init__()
        self.pm = pm
        layout = QVBoxLayout(self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        clear_btn = QPushButton("  清空日志  ")
        clear_btn.clicked.connect(self._clear_log)
        layout.addWidget(clear_btn)

    def refresh(self):
        """刷新日志"""
        logs = self.pm.get_log()
        self.log_text.setPlainText("\n".join(logs) if logs else "暂无操作记录")

    def _clear_log(self):
        self.pm.creation_log.clear()
        self.log_text.clear()


# ============================================================
# 主窗口
# ============================================================
class MainWindow(QMainWindow):
    """
    主窗口
    ======
    整合所有功能面板，通过选项卡切换。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("进程调度机制设计系统 — 操作系统课程设计")
        self.setMinimumSize(1200, 800)
        self.pm = ProcessManager(total_memory=1024)

        # 创建选项卡
        tabs = QTabWidget()

        self.process_panel = ProcessPanel(self.pm)
        self.scheduler_panel = SchedulerPanel(self.pm)
        self.resource_panel = ResourcePanel(self.pm)
        self.performance_panel = PerformancePanel(self.pm)
        self.log_panel = LogPanel(self.pm)

        tabs.addTab(self.process_panel, "进程管理")
        tabs.addTab(self.scheduler_panel, "调度可视化")
        tabs.addTab(self.resource_panel, "资源监控")
        tabs.addTab(self.performance_panel, "性能分析")
        tabs.addTab(self.log_panel, "操作日志")

        self.setCentralWidget(tabs)

        # 连接信号
        self.process_panel.process_updated.connect(self._on_process_updated)

        # 状态栏
        self.statusBar().showMessage("就绪 | 进程调度机制设计系统 v1.0")

    def _on_process_updated(self):
        """进程变更时刷新相关面板"""
        self.resource_panel.refresh()
        self.log_panel.refresh()
        proc_count = len(self.pm.get_all_processes())
        mem_info = self.pm.get_memory_info()
        self.statusBar().showMessage(
            f"进程数：{proc_count}  |  "
            f"内存：{mem_info['已用内存(MB)']}/{mem_info['总内存(MB)']}MB  |  "
            f"利用率：{mem_info['内存利用率(%)']}%"
        )
