"""
相似用户分析页 (F3)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QHeaderView, QGroupBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.similarity import SimilarityEngine

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SimilarityWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, engine, uid, top_k):
        super().__init__()
        self.engine = engine
        self.uid = uid
        self.top_k = top_k

    def run(self):
        try:
            result = self.engine.find_similar_users(
                self.uid, self.top_k,
                progress_callback=lambda c, t: self.progress.emit(c, t)
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SimilarPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.sim_engine = SimilarityEngine()
        self._matrix_built = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("🔍 相似用户分析 (F3)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("基于协同过滤，使用余弦相似度和稀疏矩阵(CSR)计算用户间的兴趣相似程度，使用最小堆维护 Top-K 结果。")
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 参数区
        param_group = QGroupBox("分析参数")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("用户ID:"))
        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("输入用户ID (0-9999)")
        self.uid_input.setMaximumWidth(200)
        param_layout.addWidget(self.uid_input)

        param_layout.addWidget(QLabel("Top-K:"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(5, 100)
        self.topk_spin.setValue(20)
        param_layout.addWidget(self.topk_spin)

        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.clicked.connect(self._on_analyze)
        param_layout.addWidget(self.analyze_btn)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 结果区
        result_layout = QHBoxLayout()

        # 表格
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.result_label = QLabel("分析结果")
        self.result_label.setStyleSheet("color: #7f8c8d;")
        table_layout.addWidget(self.result_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["排名", "用户ID", "用户昵称", "相似度"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.table)
        result_layout.addWidget(table_widget, 3)

        # 图表
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        result_layout.addWidget(chart_widget, 2)

        layout.addLayout(result_layout)

    def _on_analyze(self):
        if not self.mw.behaviors:
            QMessageBox.warning(self, "提示", "请先生成或加载数据！")
            return

        uid_text = self.uid_input.text().strip()
        if not uid_text:
            QMessageBox.warning(self, "提示", "请输入用户ID！")
            return

        try:
            uid = int(uid_text)
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数字ID！")
            return

        if uid < 0 or uid >= len(self.mw.users):
            QMessageBox.warning(self, "提示", f"用户ID应在 0-{len(self.mw.users)-1} 之间！")
            return

        # 构建矩阵（首次）
        if not self._matrix_built:
            self.progress_dlg = QProgressDialog("正在构建用户-视频交互矩阵...", "取消", 0, 100, self)
            self.progress_dlg.setWindowModality(Qt.WindowModal)
            self.progress_dlg.show()

            self.sim_engine.build_matrix(
                self.mw.users, self.mw.behaviors,
                progress_callback=lambda c, t: self.progress_dlg.setValue(int(c/t*100))
            )
            self._matrix_built = True
            self.progress_dlg.close()

        top_k = self.topk_spin.value()
        self.analyze_btn.setEnabled(False)
        self.result_label.setText("正在计算相似用户...")

        self.worker = SimilarityWorker(self.sim_engine, uid, top_k)
        self.worker.progress.connect(
            lambda c, t: self.result_label.setText(f"正在计算... {c}/{t}")
        )
        self.worker.finished.connect(lambda r: self._on_result(uid, r))
        self.worker.error.connect(lambda e: self._on_error(e))
        self.worker.start()

    def _on_result(self, target_uid, results):
        self.analyze_btn.setEnabled(True)
        self.result_label.setText(f"用户 {target_uid} 的 Top-{len(results)} 相似用户")

        self.table.setRowCount(len(results))
        for i, (uid, score) in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(uid)))
            name = self.mw.users[uid]["name"] if uid < len(self.mw.users) else ""
            self.table.setItem(i, 2, QTableWidgetItem(name))
            self.table.setItem(i, 3, QTableWidgetItem(f"{score:.4f}"))

        # 绘制柱状图
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if results:
            top10 = results[:10]
            labels = [f"U{uid}" for uid, _ in top10]
            scores = [s for _, s in top10]
            bars = ax.barh(range(len(labels)), scores, color='#3498db')
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels)
            ax.set_xlabel('相似度')
            ax.set_title(f'用户 {target_uid} 的 Top-10 相似用户')
            ax.invert_yaxis()
        self.figure.tight_layout()
        self.canvas.draw()

    def _on_error(self, err):
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"分析出错: {err}")
