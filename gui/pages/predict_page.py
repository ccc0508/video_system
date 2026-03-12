"""
热度预测页 (F5)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QMessageBox, QGroupBox, QGridLayout,
    QProgressDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.predictor import Predictor

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PredictPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.predictor = Predictor()
        self._series_built = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("📈 视频热度预测 (F5)")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        desc = QLabel("基于历史观看时间序列数据，使用移动平均和线性回归预测视频未来热度趋势。")
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 参数区
        param_group = QGroupBox("预测参数")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("视频ID:"))
        self.vid_input = QLineEdit()
        self.vid_input.setPlaceholderText("输入视频ID")
        self.vid_input.setMaximumWidth(200)
        param_layout.addWidget(self.vid_input)

        param_layout.addWidget(QLabel("历史天数:"))
        self.history_spin = QSpinBox()
        self.history_spin.setRange(7, 180)
        self.history_spin.setValue(30)
        param_layout.addWidget(self.history_spin)

        param_layout.addWidget(QLabel("预测天数:"))
        self.predict_spin = QSpinBox()
        self.predict_spin.setRange(3, 30)
        self.predict_spin.setValue(14)
        param_layout.addWidget(self.predict_spin)

        self.predict_btn = QPushButton("开始预测")
        self.predict_btn.clicked.connect(self._on_predict)
        param_layout.addWidget(self.predict_btn)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 视频信息
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #2c3e50; font-size: 13px; margin: 5px;")
        layout.addWidget(self.info_label)

        # 统计卡片
        self.stats_layout = QHBoxLayout()
        self.stat_cards = {}
        for key, label, color in [
            ("total_views", "总观看量", "#3498db"),
            ("avg_daily", "日均观看", "#2ecc71"),
            ("recent_7_days", "近7天观看", "#e74c3c"),
            ("growth_rate", "周增长率(%)", "#f39c12"),
        ]:
            card = self._create_stat_card(label, "—", color)
            self.stat_cards[key] = card
            self.stats_layout.addWidget(card)
        layout.addLayout(self.stats_layout)

        # 图表
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def _create_stat_card(self, title, value, color):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{ background: white; border-radius: 8px; border-left: 4px solid {color}; }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        t = QLabel(title)
        t.setStyleSheet("color: #7f8c8d; font-size: 12px; border: none;")
        v = QLabel(str(value))
        v.setObjectName("stat_value")
        v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; border: none;")

        card_layout.addWidget(t)
        card_layout.addWidget(v)
        return card

    def _on_predict(self):
        if not self.mw.behaviors:
            QMessageBox.warning(self, "提示", "请先生成或加载数据！")
            return

        vid_text = self.vid_input.text().strip()
        if not vid_text:
            QMessageBox.warning(self, "提示", "请输入视频ID！")
            return

        try:
            vid = int(vid_text)
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数字ID！")
            return

        if vid < 0 or vid >= len(self.mw.videos):
            QMessageBox.warning(self, "提示", f"视频ID应在 0-{len(self.mw.videos)-1} 之间！")
            return

        # 构建时间序列（首次）
        if not self._series_built:
            dlg = QProgressDialog("正在构建时间序列...", "取消", 0, 100, self)
            dlg.setWindowModality(Qt.WindowModal)
            dlg.show()

            self.predictor.build_time_series(
                self.mw.behaviors,
                progress_callback=lambda c, t: dlg.setValue(int(c/t*100))
            )
            self._series_built = True
            dlg.close()

        # 显示视频信息
        video = self.mw.videos[vid]
        self.info_label.setText(
            f"📹 视频: {video['title']} | 类目: {video['category']} | "
            f"标签: {', '.join(video.get('tags', []))}"
        )

        # 预测
        history_days = self.history_spin.value()
        predict_days = self.predict_spin.value()
        result = self.predictor.predict(vid, history_days, predict_days)

        if result is None:
            QMessageBox.information(self, "提示", "该视频暂无观看记录。")
            return

        # 更新统计卡片
        stats = result["stats"]
        for key, card in self.stat_cards.items():
            val_label = card.findChild(QLabel, "stat_value")
            if val_label and key in stats:
                val = stats[key]
                val_label.setText(f"{val:,}" if isinstance(val, int) else str(val))

        # 绘制图表
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 历史数据
        hist = result["history"]
        if hist:
            hx = [d for d, _ in hist]
            hy = [v for _, v in hist]
            ax.bar(hx, hy, color='#bdc3c7', alpha=0.5, label='每日观看量', width=0.8)

        # 移动平均
        ma = result["moving_avg"]
        if ma:
            mx = [d for d, _ in ma]
            my = [v for _, v in ma]
            ax.plot(mx, my, color='#3498db', linewidth=2, label='7日移动平均')

        # 预测趋势
        pred = result["prediction"]
        if pred:
            px = [d for d, _ in pred]
            py = [v for _, v in pred]
            ax.plot(px, py, color='#e74c3c', linewidth=2, linestyle='--',
                    marker='o', markersize=4, label='预测趋势')
            # 填充预测区域
            ax.axvspan(0, max(px) if px else 1, alpha=0.05, color='red')

        ax.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('天数（负数=过去, 正数=未来）')
        ax.set_ylabel('观看次数')
        ax.set_title(f'视频 {vid} 热度趋势')
        ax.legend()
        ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
