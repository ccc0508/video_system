"""
视频信息库页 (F1)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QHeaderView, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from data_structures.inverted_index import InvertedIndex


class VideoPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.tag_index = InvertedIndex()
        self.cat_index = InvertedIndex()
        self._current_results = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("📹 视频信息库 (F1)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # 搜索区域
        search_group = QGroupBox("搜索视频")
        search_layout = QHBoxLayout(search_group)

        self.search_type = QComboBox()
        self.search_type.addItems(["按视频ID", "按类目", "按标签", "按标题关键词"])
        self.search_type.setMinimumWidth(120)
        search_layout.addWidget(QLabel("搜索方式:"))
        search_layout.addWidget(self.search_type)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索内容...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        show_all_btn = QPushButton("显示全部(前500条)")
        show_all_btn.clicked.connect(self._show_all)
        search_layout.addWidget(show_all_btn)

        layout.addWidget(search_group)

        # 结果统计
        self.result_label = QLabel("共 0 条视频")
        self.result_label.setStyleSheet("color: #7f8c8d; font-size: 13px; margin: 5px;")
        layout.addWidget(self.result_label)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "视频ID", "标题", "类目", "标签", "时长(秒)", "发布时间", "作者ID"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

    def refresh_data(self):
        """数据加载后构建索引"""
        self.tag_index = InvertedIndex()
        self.cat_index = InvertedIndex()

        for v in self.mw.videos:
            vid = v["video_id"]
            self.cat_index.add(v["category"], vid)
            for tag in v.get("tags", []):
                self.tag_index.add(tag, vid)

        self.result_label.setText(f"共 {len(self.mw.videos):,} 条视频")
        self._show_all()

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索内容！")
            return

        search_type = self.search_type.currentText()
        results = []

        if search_type == "按视频ID":
            try:
                vid = int(query)
                if 0 <= vid < len(self.mw.videos):
                    results = [self.mw.videos[vid]]
                else:
                    QMessageBox.warning(self, "提示", f"视频ID {vid} 不存在！")
                    return
            except ValueError:
                QMessageBox.warning(self, "提示", "请输入有效的数字ID！")
                return

        elif search_type == "按类目":
            ids = self.cat_index.search(query)
            results = [self.mw.videos[i] for i in ids if i < len(self.mw.videos)]

        elif search_type == "按标签":
            ids = self.tag_index.search(query)
            results = [self.mw.videos[i] for i in ids if i < len(self.mw.videos)]

        elif search_type == "按标题关键词":
            results = [v for v in self.mw.videos if query in v.get("title", "")]
            results = results[:500]

        self._display_results(results[:500])
        self.result_label.setText(f"搜索结果: {len(results):,} 条（最多显示前500条）")

    def _show_all(self):
        results = self.mw.videos[:500]
        self._display_results(results)
        self.result_label.setText(f"共 {len(self.mw.videos):,} 条视频（显示前500条）")

    def _display_results(self, results):
        import time
        self.table.setRowCount(len(results))
        for row, v in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(str(v.get("video_id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(v.get("title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(v.get("category", "")))
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(v.get("tags", []))))
            self.table.setItem(row, 4, QTableWidgetItem(str(v.get("duration", ""))))
            ts = v.get("publish_time", 0)
            time_str = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else ""
            self.table.setItem(row, 5, QTableWidgetItem(time_str))
            self.table.setItem(row, 6, QTableWidgetItem(str(v.get("author_id", ""))))
