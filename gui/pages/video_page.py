"""
视频信息库页 (F1) — 含搜索和热门排行榜
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QHeaderView, QGroupBox, QTabWidget, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from data_structures.inverted_index import InvertedIndex
from data_structures.heap import MaxHeap

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class VideoPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.tag_index = InvertedIndex()
        self.cat_index = InvertedIndex()
        self._video_stats = {}  # {video_id: {views, likes, favorites}}
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

        # Tab 切换：视频列表 / 热门排行榜
        self.tabs = QTabWidget()

        # === Tab 1: 视频列表 ===
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        list_layout.setContentsMargins(0, 5, 0, 0)

        self.result_label = QLabel("共 0 条视频")
        self.result_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        list_layout.addWidget(self.result_label)

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
        list_layout.addWidget(self.table)

        self.tabs.addTab(list_tab, "📋 视频列表")

        # === Tab 2: 热门排行榜 ===
        rank_tab = QWidget()
        rank_layout = QVBoxLayout(rank_tab)
        rank_layout.setContentsMargins(0, 5, 0, 0)

        # 排行榜参数
        rank_param = QHBoxLayout()

        rank_param.addWidget(QLabel("排序方式:"))
        self.rank_sort = QComboBox()
        self.rank_sort.addItems(["按观看量", "按点赞量", "按收藏量", "按综合热度"])
        rank_param.addWidget(self.rank_sort)

        rank_param.addWidget(QLabel("显示数量:"))
        self.rank_count = QSpinBox()
        self.rank_count.setRange(10, 100)
        self.rank_count.setValue(50)
        rank_param.addWidget(self.rank_count)

        rank_btn = QPushButton("🔥 刷新排行榜")
        rank_btn.clicked.connect(self._refresh_ranking)
        rank_param.addWidget(rank_btn)

        rank_param.addStretch()
        rank_layout.addLayout(rank_param)

        # 排行榜表格
        self.rank_table = QTableWidget()
        self.rank_table.setColumnCount(8)
        self.rank_table.setHorizontalHeaderLabels([
            "排名", "视频ID", "标题", "类目", "👁 观看量", "👍 点赞量", "⭐ 收藏量", "🔥 综合热度"
        ])
        rh = self.rank_table.horizontalHeader()
        rh.setSectionResizeMode(2, QHeaderView.Stretch)
        self.rank_table.setAlternatingRowColors(True)
        self.rank_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rank_table.setSelectionBehavior(QTableWidget.SelectRows)
        rank_layout.addWidget(self.rank_table, 3)

        # 排行榜柱状图
        self.figure = Figure(figsize=(10, 3))
        self.canvas = FigureCanvas(self.figure)
        rank_layout.addWidget(self.canvas, 1)

        self.tabs.addTab(rank_tab, "🔥 热门排行榜")
        layout.addWidget(self.tabs)

    def refresh_data(self):
        """数据加载后构建索引和统计"""
        self.tag_index = InvertedIndex()
        self.cat_index = InvertedIndex()

        for v in self.mw.videos:
            vid = v["video_id"]
            self.cat_index.add(v["category"], vid)
            for tag in v.get("tags", []):
                self.tag_index.add(tag, vid)

        # 统计每个视频的观看/点赞/收藏量
        self._build_video_stats()

        self.result_label.setText(f"共 {len(self.mw.videos):,} 条视频")
        self._show_all()

    def _build_video_stats(self):
        """从行为数据中统计每个视频的观看、点赞、收藏量"""
        self._video_stats = {}

        for b in self.mw.behaviors:
            vid = int(b[1])
            action = b[2]

            if vid not in self._video_stats:
                self._video_stats[vid] = {"views": 0, "likes": 0, "favorites": 0}

            stats = self._video_stats[vid]
            stats["views"] += 1
            if action == "like":
                stats["likes"] += 1
            elif action == "favorite":
                stats["favorites"] += 1

    # ================== 搜索功能 ==================

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索内容！")
            return

        self.tabs.setCurrentIndex(0)  # 搜索时切到列表 Tab

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

    # ================== 热门排行榜 ==================

    def _refresh_ranking(self):
        """使用最大堆取 Top-N 热门视频"""
        if not self._video_stats:
            QMessageBox.warning(self, "提示", "请先生成或加载数据！")
            return

        sort_key = self.rank_sort.currentText()
        top_n = self.rank_count.value()

        # 用最大堆高效取 Top-N
        heap = MaxHeap()
        for vid, stats in self._video_stats.items():
            views = stats["views"]
            likes = stats["likes"]
            favs = stats["favorites"]

            if sort_key == "按观看量":
                score = views
            elif sort_key == "按点赞量":
                score = likes
            elif sort_key == "按收藏量":
                score = favs
            else:  # 综合热度 = views + likes*5 + favorites*10
                score = views + likes * 5 + favs * 10

            heap.insert((score, vid))

        # 提取 Top-N
        ranking = []
        for _ in range(min(top_n, len(heap))):
            score, vid = heap.extract()
            if vid < len(self.mw.videos):
                ranking.append((vid, score))

        self._display_ranking(ranking, sort_key)

    def _display_ranking(self, ranking, sort_key):
        """显示排行榜"""
        self.rank_table.setRowCount(len(ranking))

        # 奖牌颜色
        medal_colors = {0: "#FFD700", 1: "#C0C0C0", 2: "#CD7F32"}

        for row, (vid, score) in enumerate(ranking):
            v = self.mw.videos[vid]
            stats = self._video_stats.get(vid, {"views": 0, "likes": 0, "favorites": 0})

            rank_text = f"🥇 {row+1}" if row == 0 else f"🥈 {row+1}" if row == 1 else f"🥉 {row+1}" if row == 2 else str(row+1)
            self.rank_table.setItem(row, 0, QTableWidgetItem(rank_text))
            self.rank_table.setItem(row, 1, QTableWidgetItem(str(vid)))
            self.rank_table.setItem(row, 2, QTableWidgetItem(v.get("title", "")))
            self.rank_table.setItem(row, 3, QTableWidgetItem(v.get("category", "")))
            self.rank_table.setItem(row, 4, QTableWidgetItem(f"{stats['views']:,}"))
            self.rank_table.setItem(row, 5, QTableWidgetItem(f"{stats['likes']:,}"))
            self.rank_table.setItem(row, 6, QTableWidgetItem(f"{stats['favorites']:,}"))

            heat = stats['views'] + stats['likes'] * 5 + stats['favorites'] * 10
            self.rank_table.setItem(row, 7, QTableWidgetItem(f"{heat:,}"))

            # 前三名高亮
            if row in medal_colors:
                color = QColor(medal_colors[row])
                color.setAlpha(50)
                for col in range(8):
                    item = self.rank_table.item(row, col)
                    if item:
                        item.setBackground(color)

        # 绘制 Top-20 柱状图
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        top20 = ranking[:20]
        if top20:
            labels = [f"V{vid}" for vid, _ in top20]
            values = [s for _, s in top20]
            colors_bar = ['#e74c3c' if i < 3 else '#3498db' if i < 10 else '#bdc3c7'
                          for i in range(len(top20))]
            bars = ax.bar(range(len(labels)), values, color=colors_bar)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, fontsize=8)
            ax.set_ylabel(sort_key.replace("按", ""))
            ax.set_title(f'Top-20 热门视频（{sort_key}）')
            ax.grid(axis='y', alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
