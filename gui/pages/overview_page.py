"""
系统总览页
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class OverviewPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)

        # 标题
        title = QLabel("📊 系统总览")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("短视频推荐系统 — 数据结构课程大作业")
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # 数据统计卡片
        cards_layout = QHBoxLayout()

        self.video_card = self._create_card("📹 视频数量", "0", "#3498db")
        self.user_card = self._create_card("👤 用户数量", "0", "#2ecc71")
        self.behavior_card = self._create_card("📝 行为记录", "0", "#e74c3c")
        self.category_card = self._create_card("🏷 视频分类", "20", "#f39c12")

        cards_layout.addWidget(self.video_card)
        cards_layout.addWidget(self.user_card)
        cards_layout.addWidget(self.behavior_card)
        cards_layout.addWidget(self.category_card)
        layout.addLayout(cards_layout)

        # 功能说明
        func_group = QGroupBox("系统功能")
        func_layout = QGridLayout(func_group)

        functions = [
            ("F1 视频信息库", "构建10万+视频记录，支持按类目/标签搜索", "📹"),
            ("F2 用户行为模拟", "模拟1万+用户的点击观看行为", "👤"),
            ("F3 相似用户分析", "基于协同过滤计算用户相似度", "🔍"),
            ("F4 视频推荐", "为用户推荐感兴趣的视频", "🎯"),
            ("F5 热度预测", "预测视频未来的观看热度变化", "📈"),
            ("F6 视频聚类", "将相似视频聚成一组", "🗂"),
            ("F7 用户聚类", "将兴趣相似的用户聚成一组", "👥"),
        ]

        for i, (name, desc, icon) in enumerate(functions):
            row, col = divmod(i, 2)
            label = QLabel(f"{icon} <b>{name}</b><br/><span style='color:#7f8c8d'>{desc}</span>")
            label.setStyleSheet(
                "background: white; border: 1px solid #ddd; border-radius: 8px; "
                "padding: 15px; margin: 4px;"
            )
            func_layout.addWidget(label, row, col)

        layout.addWidget(func_group)

        # 数据结构说明
        ds_group = QGroupBox("核心数据结构")
        ds_layout = QGridLayout(ds_group)
        structures = [
            "哈希表 (HashMap) — 视频/用户索引",
            "堆 (Heap) — Top-K/Top-N 选择",
            "稀疏矩阵 (CSR) — 用户-视频交互",
            "倒排索引 — 标签/类目检索",
            "图 (Graph) — 相似度网络",
            "时间序列数组 — 热度预测",
        ]
        for i, s in enumerate(structures):
            row, col = divmod(i, 3)
            lbl = QLabel(f"  ✦ {s}")
            lbl.setStyleSheet("background: white; border: 1px solid #eee; border-radius: 4px; padding: 8px;")
            ds_layout.addWidget(lbl, row, col)

        layout.addWidget(ds_group)
        layout.addStretch()

    def _create_card(self, title, value, color):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid {color};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 13px; border: none;")

        value_label = QLabel(value)
        value_label.setObjectName("card_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold; border: none;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        return card

    def refresh_data(self):
        """刷新数据统计"""
        def _set_card_value(card, value):
            label = card.findChild(QLabel, "card_value")
            if label:
                label.setText(f"{value:,}")

        _set_card_value(self.video_card, len(self.mw.videos))
        _set_card_value(self.user_card, len(self.mw.users))
        _set_card_value(self.behavior_card, len(self.mw.behaviors))
