"""
用户数据库页 (F2)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QHeaderView, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import time


class UserPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("👤 用户数据库 (F2)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # 搜索区域
        search_group = QGroupBox("搜索用户")
        search_layout = QHBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入用户ID或昵称搜索...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        show_btn = QPushButton("显示全部(前500)")
        show_btn.clicked.connect(self._show_all)
        search_layout.addWidget(show_btn)

        layout.addWidget(search_group)

        # 分割视图
        splitter = QSplitter(Qt.Vertical)

        # 用户表格
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 0, 0)

        self.user_label = QLabel("用户列表")
        self.user_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        user_layout.addWidget(self.user_label)

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels([
            "用户ID", "昵称", "偏好类目", "偏好标签", "注册时间"
        ])
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.currentCellChanged.connect(self._on_user_selected)
        user_layout.addWidget(self.user_table)
        splitter.addWidget(user_widget)

        # 行为记录表格
        beh_widget = QWidget()
        beh_layout = QVBoxLayout(beh_widget)
        beh_layout.setContentsMargins(0, 0, 0, 0)

        self.beh_label = QLabel("用户行为记录（选中用户后显示）")
        self.beh_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        beh_layout.addWidget(self.beh_label)

        self.beh_table = QTableWidget()
        self.beh_table.setColumnCount(5)
        self.beh_table.setHorizontalHeaderLabels([
            "视频ID", "视频标题", "行为类型", "时间", "观看时长(秒)"
        ])
        beh_header = self.beh_table.horizontalHeader()
        beh_header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.beh_table.setAlternatingRowColors(True)
        self.beh_table.setEditTriggers(QTableWidget.NoEditTriggers)
        beh_layout.addWidget(self.beh_table)
        splitter.addWidget(beh_widget)

        splitter.setSizes([400, 300])
        layout.addWidget(splitter)

    def refresh_data(self):
        self._show_all()

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索内容！")
            return

        results = []
        try:
            uid = int(query)
            if 0 <= uid < len(self.mw.users):
                results = [self.mw.users[uid]]
            else:
                QMessageBox.warning(self, "提示", f"用户ID {uid} 不存在！")
                return
        except ValueError:
            results = [u for u in self.mw.users if query in u.get("name", "")]
            results = results[:500]

        self._display_users(results)
        self.user_label.setText(f"搜索结果: {len(results)} 个用户")

    def _show_all(self):
        results = self.mw.users[:500]
        self._display_users(results)
        self.user_label.setText(f"共 {len(self.mw.users):,} 个用户（显示前500）")

    def _display_users(self, users):
        self.user_table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(u.get("user_id", ""))))
            self.user_table.setItem(row, 1, QTableWidgetItem(u.get("name", "")))
            cats = ", ".join(u.get("preference_categories", []))
            self.user_table.setItem(row, 2, QTableWidgetItem(cats))
            tags = ", ".join(u.get("preference_tags", []))
            self.user_table.setItem(row, 3, QTableWidgetItem(tags))
            ts = u.get("register_time", 0)
            ts_str = time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else ""
            self.user_table.setItem(row, 4, QTableWidgetItem(ts_str))

    def _on_user_selected(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        uid_item = self.user_table.item(row, 0)
        if not uid_item:
            return
        uid = int(uid_item.text())
        self._show_user_behaviors(uid)

    def _show_user_behaviors(self, uid):
        user_behs = [b for b in self.mw.behaviors if int(b[0]) == uid]
        user_behs = user_behs[:200]  # 最多显示 200 条

        self.beh_label.setText(f"用户 {uid} 的行为记录（共 {len(user_behs)} 条）")
        self.beh_table.setRowCount(len(user_behs))

        action_map = {"watch": "观看", "like": "点赞", "favorite": "收藏"}

        for row, b in enumerate(user_behs):
            vid = int(b[1])
            self.beh_table.setItem(row, 0, QTableWidgetItem(str(vid)))

            title = ""
            if 0 <= vid < len(self.mw.videos):
                title = self.mw.videos[vid].get("title", "")
            self.beh_table.setItem(row, 1, QTableWidgetItem(title))

            action = action_map.get(b[2], b[2])
            self.beh_table.setItem(row, 2, QTableWidgetItem(action))

            ts = int(b[3])
            ts_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
            self.beh_table.setItem(row, 3, QTableWidgetItem(ts_str))

            self.beh_table.setItem(row, 4, QTableWidgetItem(b[4]))
