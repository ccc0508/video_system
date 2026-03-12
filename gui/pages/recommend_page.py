"""
视频推荐页 (F4)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
    QMessageBox, QHeaderView, QGroupBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.similarity import SimilarityEngine
from core.recommender import Recommender


class RecommendWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, list, list)
    error = pyqtSignal(str)

    def __init__(self, sim_engine, recommender, uid, top_k, top_n, videos):
        super().__init__()
        self.sim_engine = sim_engine
        self.recommender = recommender
        self.uid = uid
        self.top_k = top_k
        self.top_n = top_n
        self.videos = videos

    def run(self):
        try:
            similar_users = self.sim_engine.find_similar_users(
                self.uid, self.top_k,
                progress_callback=lambda c, t: self.progress.emit(c, t)
            )
            recommendations = self.recommender.recommend(
                self.uid, similar_users, self.top_n, self.videos
            )
            self.finished.emit(self.uid, similar_users, recommendations)
        except Exception as e:
            self.error.emit(str(e))


class RecommendPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.sim_engine = SimilarityEngine()
        self.recommender = None
        self._matrix_built = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("🎯 视频推荐 (F4)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("基于用户的协同过滤(User-Based CF): 找到相似用户 → 汇总候选视频(哈希表) → 最大堆取 Top-N。")
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 参数区
        param_group = QGroupBox("推荐参数")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("用户ID:"))
        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("0-9999")
        self.uid_input.setMaximumWidth(150)
        param_layout.addWidget(self.uid_input)

        param_layout.addWidget(QLabel("相似用户K:"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(5, 50)
        self.topk_spin.setValue(20)
        param_layout.addWidget(self.topk_spin)

        param_layout.addWidget(QLabel("推荐数N:"))
        self.topn_spin = QSpinBox()
        self.topn_spin.setRange(5, 50)
        self.topn_spin.setValue(20)
        param_layout.addWidget(self.topn_spin)

        self.rec_btn = QPushButton("生成推荐")
        self.rec_btn.clicked.connect(self._on_recommend)
        param_layout.addWidget(self.rec_btn)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 用户信息
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("color: #2c3e50; font-size: 13px; margin: 5px;")
        layout.addWidget(self.user_info_label)

        # 推荐结果表格
        self.result_label = QLabel("推荐结果")
        self.result_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.result_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "排名", "视频ID", "标题", "类目", "推荐得分", "推荐理由"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _on_recommend(self):
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

        # 显示用户信息
        user = self.mw.users[uid]
        self.user_info_label.setText(
            f"👤 用户: {user['name']} (ID: {uid}) | "
            f"偏好类目: {', '.join(user.get('preference_categories', []))}"
        )

        if not self._matrix_built:
            self.progress_dlg = QProgressDialog("正在构建交互矩阵...", "取消", 0, 100, self)
            self.progress_dlg.setWindowModality(Qt.WindowModal)
            self.progress_dlg.show()

            self.sim_engine.build_matrix(
                self.mw.users, self.mw.behaviors,
                progress_callback=lambda c, t: self.progress_dlg.setValue(int(c/t*100))
            )
            self.recommender = Recommender(self.sim_engine)
            self._matrix_built = True
            self.progress_dlg.close()

        top_k = self.topk_spin.value()
        top_n = self.topn_spin.value()
        self.rec_btn.setEnabled(False)
        self.result_label.setText("正在生成推荐...")

        self.worker = RecommendWorker(
            self.sim_engine, self.recommender,
            uid, top_k, top_n, self.mw.videos
        )
        self.worker.progress.connect(
            lambda c, t: self.result_label.setText(f"正在计算相似用户... {c}/{t}")
        )
        self.worker.finished.connect(self._on_result)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_result(self, uid, similar_users, recommendations):
        self.rec_btn.setEnabled(True)
        self.result_label.setText(
            f"为用户 {uid} 推荐了 {len(recommendations)} 个视频 "
            f"（基于 {len(similar_users)} 个相似用户）"
        )

        self.table.setRowCount(len(recommendations))
        for i, rec in enumerate(recommendations):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(rec.get("video_id", ""))))
            self.table.setItem(i, 2, QTableWidgetItem(rec.get("title", "")))
            self.table.setItem(i, 3, QTableWidgetItem(rec.get("category", "")))
            self.table.setItem(i, 4, QTableWidgetItem(f"{rec.get('score', 0):.4f}"))
            self.table.setItem(i, 5, QTableWidgetItem(rec.get("reason", "")))

    def _on_error(self, err):
        self.rec_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"推荐出错: {err}")
