"""
视频聚类页 (F6)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QHeaderView, QGroupBox, QProgressDialog, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.clustering import ClusteringEngine

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ClusterWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list, list, list)
    error = pyqtSignal(str)

    def __init__(self, engine, videos, behaviors, num_users, k):
        super().__init__()
        self.engine = engine
        self.videos = videos
        self.behaviors = behaviors
        self.num_users = num_users
        self.k = k

    def run(self):
        try:
            features = self.engine.build_video_features(
                self.videos, self.behaviors, self.num_users,
                progress_callback=lambda c, t: self.progress.emit(c, t)
            )
            labels, centers = self.engine.kmeans(features, self.k, max_iter=30)
            cluster_info = self.engine.get_cluster_info(labels, self.videos, "video")
            self.finished.emit(labels, centers, cluster_info)
        except Exception as e:
            self.error.emit(str(e))


class VClusterPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.engine = ClusteringEngine()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("🗂 视频聚类分析 (F6)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("基于观看用户分布构建视频特征向量，使用 K-Means 聚类将相似视频分组。")
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 参数区
        param_group = QGroupBox("聚类参数")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("聚类数 K:"))
        self.k_spin = QSpinBox()
        self.k_spin.setRange(2, 20)
        self.k_spin.setValue(5)
        param_layout.addWidget(self.k_spin)

        self.run_btn = QPushButton("开始聚类")
        self.run_btn.clicked.connect(self._on_run)
        param_layout.addWidget(self.run_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d;")
        param_layout.addWidget(self.status_label)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 结果区
        splitter = QSplitter(Qt.Horizontal)

        # 左侧: 簇列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("聚类结果"))

        self.cluster_table = QTableWidget()
        self.cluster_table.setColumnCount(3)
        self.cluster_table.setHorizontalHeaderLabels(["簇ID", "视频数", "主要类目"])
        self.cluster_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.cluster_table.setAlternatingRowColors(True)
        self.cluster_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cluster_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cluster_table.currentCellChanged.connect(self._on_cluster_selected)
        left_layout.addWidget(self.cluster_table)
        splitter.addWidget(left)

        # 右侧: 详情+图表
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.detail_label = QLabel("选择一个簇查看详情")
        self.detail_label.setStyleSheet("color: #7f8c8d;")
        right_layout.addWidget(self.detail_label)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(["视频ID", "标题", "类目", "标签"])
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.detail_table)

        # 图表
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        splitter.addWidget(right)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

        self._cluster_info = []

    def _on_run(self):
        if not self.mw.behaviors:
            QMessageBox.warning(self, "提示", "请先生成或加载数据！")
            return

        k = self.k_spin.value()
        self.run_btn.setEnabled(False)
        self.status_label.setText("正在聚类...")

        self.worker = ClusterWorker(
            self.engine, self.mw.videos, self.mw.behaviors,
            len(self.mw.users), k
        )
        self.worker.progress.connect(
            lambda c, t: self.status_label.setText(f"构建特征... {c}/{t}")
        )
        self.worker.finished.connect(self._on_result)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_result(self, labels, centers, cluster_info):
        self.run_btn.setEnabled(True)
        self._cluster_info = cluster_info
        self.status_label.setText(f"聚类完成，共 {len(cluster_info)} 个簇")

        self.cluster_table.setRowCount(len(cluster_info))
        for i, info in enumerate(cluster_info):
            self.cluster_table.setItem(i, 0, QTableWidgetItem(str(info["cluster_id"])))
            self.cluster_table.setItem(i, 1, QTableWidgetItem(str(info["size"])))
            top_cats = info.get("top_categories", [])
            cats_str = ", ".join(f"{c}({n})" for c, n in top_cats[:3])
            self.cluster_table.setItem(i, 2, QTableWidgetItem(cats_str))

        # 绘制簇大小饼图
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        sizes = [info["size"] for info in cluster_info]
        labels_pie = [f"簇{info['cluster_id']}\n({info['size']})" for info in cluster_info]
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
                  '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
                  '#8e44ad', '#27ae60', '#d35400', '#2980b9', '#f1c40f',
                  '#7f8c8d', '#2c3e50', '#95a5a6', '#d4ac0d', '#1f618d']
        ax.pie(sizes, labels=labels_pie, colors=colors[:len(sizes)],
               autopct='%1.1f%%', startangle=90)
        ax.set_title('视频聚类分布')
        self.figure.tight_layout()
        self.canvas.draw()

    def _on_cluster_selected(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._cluster_info):
            return
        info = self._cluster_info[row]
        members = info["members"]
        self.detail_label.setText(f"簇 {info['cluster_id']} 的视频（共 {info['size']}，显示前50）")

        self.detail_table.setRowCount(len(members))
        for i, v in enumerate(members):
            self.detail_table.setItem(i, 0, QTableWidgetItem(str(v.get("video_id", ""))))
            self.detail_table.setItem(i, 1, QTableWidgetItem(v.get("title", "")))
            self.detail_table.setItem(i, 2, QTableWidgetItem(v.get("category", "")))
            self.detail_table.setItem(i, 3, QTableWidgetItem(", ".join(v.get("tags", []))))

    def _on_error(self, err):
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"聚类出错: {err}")
