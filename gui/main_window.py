"""
主窗口

左侧导航栏 + 右侧内容区的布局，菜单栏包含数据管理和分析功能入口。
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QStatusBar, QMenuBar, QAction, QMessageBox, QLabel,
    QProgressDialog, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from gui.pages.overview_page import OverviewPage
from gui.pages.video_page import VideoPage
from gui.pages.user_page import UserPage
from gui.pages.similar_page import SimilarPage
from gui.pages.recommend_page import RecommendPage
from gui.pages.predict_page import PredictPage
from gui.pages.vcluster_page import VClusterPage
from gui.pages.ucluster_page import UClusterPage

from storage.file_manager import load_json, load_csv_all, data_file_exists, DATA_DIR, RESULTS_DIR
import os, shutil


class DataLoader(QThread):
    """后台数据加载线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("正在加载视频数据...")
            videos = load_json("videos.json") or []

            self.progress.emit("正在加载用户数据...")
            users = load_json("users.json") or []

            self.progress.emit("正在加载行为数据...")
            header, rows = load_csv_all("behaviors.csv")
            behaviors = rows or []

            self.finished.emit({
                "videos": videos,
                "users": users,
                "behaviors": behaviors,
            })
        except Exception as e:
            self.error.emit(str(e))


class GenerateThread(QThread):
    """后台数据生成线程"""
    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, video_count=100000, user_count=10000):
        super().__init__()
        self.video_count = video_count
        self.user_count = user_count

    def run(self):
        try:
            from core.data_generator import generate_videos, generate_users, generate_behaviors

            def vid_cb(cur, total):
                self.progress.emit("生成视频", cur, total)

            def user_cb(cur, total):
                self.progress.emit("生成用户", cur, total)

            def beh_cb(cur, total):
                self.progress.emit("生成行为", cur, total)

            videos = generate_videos(self.video_count, vid_cb)
            users = generate_users(self.user_count, user_cb)
            generate_behaviors(users, videos, beh_cb)

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("短视频推荐系统")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # 数据
        self.videos = []
        self.users = []
        self.behaviors = []

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._apply_styles()

        # 尝试加载已有数据
        self._try_load_data()

    def _setup_ui(self):
        """构建界面布局"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航栏
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.setFont(QFont("Microsoft YaHei", 11))

        nav_items = [
            ("📊  系统总览", "overview"),
            ("📹  视频信息库", "videos"),
            ("👤  用户数据库", "users"),
            ("🔍  相似用户分析", "similar"),
            ("🎯  视频推荐", "recommend"),
            ("📈  热度预测", "predict"),
            ("🗂  视频聚类", "vcluster"),
            ("👥  用户聚类", "ucluster"),
        ]

        for text, key in nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, key)
            item.setSizeHint(item.sizeHint().__class__(180, 50))
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        # 右侧内容区
        self.stack = QStackedWidget()

        self.overview_page = OverviewPage(self)
        self.video_page = VideoPage(self)
        self.user_page = UserPage(self)
        self.similar_page = SimilarPage(self)
        self.recommend_page = RecommendPage(self)
        self.predict_page = PredictPage(self)
        self.vcluster_page = VClusterPage(self)
        self.ucluster_page = UClusterPage(self)

        self.stack.addWidget(self.overview_page)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.user_page)
        self.stack.addWidget(self.similar_page)
        self.stack.addWidget(self.recommend_page)
        self.stack.addWidget(self.predict_page)
        self.stack.addWidget(self.vcluster_page)
        self.stack.addWidget(self.ucluster_page)

        layout.addWidget(self.nav_list)
        layout.addWidget(self.stack)

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 数据菜单
        data_menu = menubar.addMenu("数据管理")

        gen_action = QAction("生成模拟数据", self)
        gen_action.triggered.connect(self._on_generate_data)
        data_menu.addAction(gen_action)



        delete_action = QAction("删除所有数据", self)
        delete_action.triggered.connect(self._on_delete_data)
        data_menu.addAction(delete_action)

        # 分析菜单
        analysis_menu = menubar.addMenu("分析功能")

        for i, (text, _) in enumerate([
            ("相似用户分析 (F3)", 3),
            ("视频推荐 (F4)", 4),
            ("热度预测 (F5)", 5),
            ("视频聚类 (F6)", 6),
            ("用户聚类 (F7)", 7),
        ]):
            action = QAction(text, self)
            idx = i + 3  # 跳过前三个导航项
            action.triggered.connect(lambda checked, x=idx: self._navigate_to(x))
            analysis_menu.addAction(action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """设置状态栏"""
        self.status_label = QLabel("就绪")
        self.data_label = QLabel("数据未加载")
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(self.data_label)

    def _apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                outline: none;
                padding-top: 10px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #34495e;
            }
            QMenuBar {
                background-color: #ecf0f1;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
                color: white;
            }
            QStatusBar {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2471a3;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit, QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3498db;
            }
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #eee;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 8px;
            }
        """)

    def _on_nav_changed(self, index):
        """导航切换"""
        self.stack.setCurrentIndex(index)

    def _navigate_to(self, index):
        """跳转到指定页面"""
        self.nav_list.setCurrentRow(index)

    def _on_generate_data(self):
        """生成模拟数据"""
        reply = QMessageBox.question(
            self, "生成数据",
            "将生成 10 万条视频、1 万用户和约 100 万条行为记录。\n"
            "此过程可能需要 1-3 分钟，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        self.progress_dlg = QProgressDialog("正在生成数据...", "取消", 0, 100, self)
        self.progress_dlg.setWindowTitle("数据生成")
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.setMinimumWidth(400)
        self.progress_dlg.show()

        self.gen_thread = GenerateThread()
        self.gen_thread.progress.connect(self._on_gen_progress)
        self.gen_thread.finished.connect(self._on_gen_finished)
        self.gen_thread.error.connect(self._on_gen_error)
        self.gen_thread.start()

    def _on_gen_progress(self, msg, current, total):
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            pct = int(current / total * 100) if total > 0 else 0
            self.progress_dlg.setLabelText(f"{msg}: {current}/{total}")
            self.progress_dlg.setValue(pct)

    def _on_gen_finished(self):
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.close()
        QMessageBox.information(self, "完成", "数据生成完成！")
        self._try_load_data()

    def _on_gen_error(self, err):
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.close()
        QMessageBox.critical(self, "错误", f"生成数据时出错:\n{err}")

    def _on_delete_data(self):
        """删除所有数据文件"""
        reply = QMessageBox.question(
            self, "删除数据",
            "确定要删除所有数据文件吗？\n"
            "包括视频库、用户库、行为日志和分析结果。\n"
            "此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # 删除数据文件
            for f in ['videos.json', 'users.json', 'behaviors.csv']:
                path = os.path.join(DATA_DIR, f)
                if os.path.exists(path):
                    os.remove(path)
            # 删除索引目录
            idx_dir = os.path.join(DATA_DIR, 'indexes')
            if os.path.exists(idx_dir):
                shutil.rmtree(idx_dir)
                os.makedirs(idx_dir, exist_ok=True)
            # 删除结果目录
            if os.path.exists(RESULTS_DIR):
                shutil.rmtree(RESULTS_DIR)
                os.makedirs(RESULTS_DIR, exist_ok=True)

            # 清空内存数据
            self.videos = []
            self.users = []
            self.behaviors = []

            # 刷新UI
            self.status_label.setText("数据已删除")
            self.data_label.setText("📊 视频: 0 | 👤 用户: 0 | 📝 行为: 0")
            self.overview_page.refresh_data()

            QMessageBox.information(self, "完成", "所有数据已删除。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除数据时出错:\n{e}")

    def _try_load_data(self):
        """尝试加载已有数据"""
        if not data_file_exists("videos.json"):
            self.status_label.setText("数据文件不存在，请先生成数据")
            self.data_label.setText("📊 视频: 0 | 👤 用户: 0 | 📝 行为: 0")
            QMessageBox.information(self, "提示", "数据文件不存在，请先通过菜单「数据管理 → 生成模拟数据」生成。")
            return

        # 显示加载进度对话框
        self.load_dlg = QProgressDialog("正在加载数据...", None, 0, 0, self)
        self.load_dlg.setWindowTitle("加载数据")
        self.load_dlg.setWindowModality(Qt.WindowModal)
        self.load_dlg.setMinimumWidth(350)
        self.load_dlg.setCancelButton(None)  # 不可取消
        self.load_dlg.show()
        QApplication.processEvents()

        self.status_label.setText("正在加载数据...")
        self.loader = DataLoader()
        self.loader.progress.connect(self._on_load_progress)
        self.loader.finished.connect(self._on_data_loaded)
        self.loader.error.connect(self._on_load_error)
        self.loader.start()

    def _on_load_progress(self, msg):
        self.status_label.setText(msg)
        if hasattr(self, 'load_dlg') and self.load_dlg:
            self.load_dlg.setLabelText(msg)

    def _on_load_error(self, err):
        if hasattr(self, 'load_dlg') and self.load_dlg:
            self.load_dlg.close()
        QMessageBox.critical(self, "错误", f"加载失败: {err}")

    def _on_data_loaded(self, data):
        """数据加载完成"""
        self.videos = data["videos"]
        self.users = data["users"]
        self.behaviors = data["behaviors"]

        self.status_label.setText("数据加载完成")
        self.data_label.setText(
            f"📊 视频: {len(self.videos):,} | "
            f"👤 用户: {len(self.users):,} | "
            f"📝 行为: {len(self.behaviors):,}"
        )

        # 通知各页面数据已更新
        self.overview_page.refresh_data()
        self.video_page.refresh_data()
        self.user_page.refresh_data()

        # 重置分析页面的缓存（数据变了，旧矩阵无效）
        self.similar_page._matrix_built = False
        self.recommend_page._matrix_built = False
        self.predict_page._series_built = False

        # 关闭进度框并提示
        if hasattr(self, 'load_dlg') and self.load_dlg:
            self.load_dlg.close()

        QMessageBox.information(
            self, "加载完成",
            f"数据加载成功！\n\n"
            f"📊 视频: {len(self.videos):,} 条\n"
            f"👤 用户: {len(self.users):,} 个\n"
            f"📝 行为: {len(self.behaviors):,} 条"
        )

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "短视频推荐系统 v1.0\n\n"
            "数据结构课程大作业\n\n"
            "功能:\n"
            "F1. 视频信息库构建 (10万+)\n"
            "F2. 用户行为模拟 (1万+)\n"
            "F3. 相似用户分析\n"
            "F4. 视频推荐\n"
            "F5. 热度预测\n"
            "F6. 视频聚类\n"
            "F7. 用户聚类"
        )
