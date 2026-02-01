"""
This is a GUI application designed to facilitate users in testing the functionality of the AP_DS library.
Version number: v2.3.0
The official website of this project https://www.dvsyun.top/ap_ds
PyPi page address: https://pypi.org/project/ap-ds/
Developer: Dvs (DvsXT)
Developer's personal webpage: https://dvsyun.top/me/dvs
"""
import sys
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QFileDialog, QMessageBox, QStyle, QListWidget, 
                             QListWidgetItem, QGroupBox, QMenu, QAction, 
                             QComboBox, QProgressBar, QSplitter, QToolBar,
                             QStatusBar, QSystemTrayIcon)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QSize, QEvent
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QCursor
from player import AudioLibrary
import time

class ModernAudioPlayer(QMainWindow):
    # 自定义信号
    position_changed = pyqtSignal(float)
    state_changed = pyqtSignal(str)
    volume_changed = pyqtSignal(int)
    
    # 播放模式常量
    PLAY_MODE_SEQUENTIAL = 0  # 顺序播放
    PLAY_MODE_SHUFFLE = 1     # 随机播放
    PLAY_MODE_SINGLE = 2      # 单曲循环
    PLAY_MODE_LOOP = 3        # 列表循环
    
    def __init__(self):
        super().__init__()
        
        # 初始化音频库
        try:
            self.audio_lib = AudioLibrary()
            print("音频库初始化成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"音频库初始化失败: {e}")
            self.audio_lib = None
            return
            
        # 初始化变量
        self.current_aid = None
        self.current_file = None
        self.current_file_name = ""
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False
        self.total_duration = 0
        self.playback_start_time = 0
        self.current_position = 0
        self.volume = 80
        self.is_muted = False
        self.last_volume = 80
        
        # 播放模式相关
        self.play_mode = self.PLAY_MODE_SEQUENTIAL
        self.shuffled_indices = []  # 随机播放时的播放顺序
        self.is_shuffle_active = False
        
        # 更新定时器
        self.update_timer = QTimer()
        
        # 初始化UI
        self.init_ui()
        
        # 连接信号和槽
        self.setup_connections()
        
        # 启动更新定时器
        self.update_timer.start(100)  # 100ms更新一次
        
        # 初始化系统托盘
        self.init_system_tray()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Modern Audio Player - Advanced")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置应用程序图标
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        # 设置深色主题
        self.set_dark_theme()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 1. 顶部工具栏
        self.create_toolbar()
        
        # 2. 使用分割器创建左右布局
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：播放控制和信息面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 当前播放信息
        self.create_current_info_panel(left_layout)
        
        # 播放进度控制
        self.create_progress_panel(left_layout)
        
        # 播放控制按钮
        self.create_control_panel(left_layout)
        
        # 音量控制
        self.create_volume_panel(left_layout)
        
        # 播放模式选择
        self.create_playmode_panel(left_layout)
        
        # 右侧：播放列表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # 播放列表标题和操作按钮
        playlist_header = QWidget()
        playlist_header_layout = QHBoxLayout(playlist_header)
        playlist_header_layout.setContentsMargins(0, 0, 0, 0)
        
        playlist_label = QLabel("🎵 播放列表")
        playlist_label.setFont(QFont("Arial", 12, QFont.Bold))
        playlist_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
        
        # 播放列表操作按钮
        playlist_actions = QWidget()
        playlist_actions_layout = QHBoxLayout(playlist_actions)
        playlist_actions_layout.setContentsMargins(0, 0, 0, 0)
        
        self.playlist_clear_button = QPushButton("清空")
        self.playlist_remove_button = QPushButton("移除")
        self.playlist_save_button = QPushButton("保存")
        self.playlist_load_button = QPushButton("加载")
        
        for btn in [self.playlist_clear_button, self.playlist_remove_button, 
                   self.playlist_save_button, self.playlist_load_button]:
            btn.setFixedSize(60, 25)
            btn.setFont(QFont("Arial", 8))
            
        playlist_actions_layout.addWidget(self.playlist_clear_button)
        playlist_actions_layout.addWidget(self.playlist_remove_button)
        playlist_actions_layout.addWidget(self.playlist_save_button)
        playlist_actions_layout.addWidget(self.playlist_load_button)
        playlist_actions_layout.addStretch()
        
        playlist_header_layout.addWidget(playlist_label)
        playlist_header_layout.addWidget(playlist_actions)
        
        right_layout.addWidget(playlist_header)
        
        # 播放列表
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 5px;
                color: #ecf0f1;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #34495e;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3498db, stop: 1 #2980b9
                );
                color: white;
                border: 1px solid #2980b9;
            }
            QListWidget::item:hover {
                background-color: #34495e;
                border: 1px solid #7f8c8d;
            }
            QListWidget::item:alternate {
                background-color: #2d3e50;
            }
        """)
        self.playlist_widget.setAlternatingRowColors(True)
        right_layout.addWidget(self.playlist_widget)
        
        # 播放列表信息
        self.playlist_info_label = QLabel("共 0 首歌曲 | 总时长: 00:00")
        self.playlist_info_label.setFont(QFont("Arial", 9))
        self.playlist_info_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        self.playlist_info_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.playlist_info_label)
        
        # 设置分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # 3. 底部状态栏
        self.create_status_bar()
        
        # 设置按钮样式
        self.set_button_styles()
        
        # 初始化菜单
        self.create_context_menus()
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 文件操作
        self.open_file_action = QAction(
            self.style().standardIcon(QStyle.SP_DirOpenIcon), 
            "打开文件", self
        )
        self.open_folder_action = QAction(
            self.style().standardIcon(QStyle.SP_DirIcon), 
            "打开文件夹", self
        )
        
        toolbar.addAction(self.open_file_action)
        toolbar.addAction(self.open_folder_action)
        toolbar.addSeparator()
        
        # 播放控制
        self.play_action = QAction(
            self.style().standardIcon(QStyle.SP_MediaPlay), 
            "播放", self
        )
        self.pause_action = QAction(
            self.style().standardIcon(QStyle.SP_MediaPause), 
            "暂停", self
        )
        self.stop_action = QAction(
            self.style().standardIcon(QStyle.SP_MediaStop), 
            "停止", self
        )
        self.prev_action = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward), 
            "上一首", self
        )
        self.next_action = QAction(
            self.style().standardIcon(QStyle.SP_MediaSkipForward), 
            "下一首", self
        )
        
        toolbar.addAction(self.play_action)
        toolbar.addAction(self.pause_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.prev_action)
        toolbar.addAction(self.next_action)
        toolbar.addSeparator()
        
        # 播放模式
        self.playmode_combo = QComboBox()
        self.playmode_combo.addItem("顺序播放", self.PLAY_MODE_SEQUENTIAL)
        self.playmode_combo.addItem("随机播放", self.PLAY_MODE_SHUFFLE)
        self.playmode_combo.addItem("单曲循环", self.PLAY_MODE_SINGLE)
        self.playmode_combo.addItem("列表循环", self.PLAY_MODE_LOOP)
        self.playmode_combo.setFixedWidth(120)
        toolbar.addWidget(self.playmode_combo)
        
    def create_current_info_panel(self, layout):
        """创建当前播放信息面板"""
        info_group = QGroupBox("当前播放")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 5px;
                padding-top: 15px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2c3e50, stop: 1 #34495e
                );
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #3498db;
                font-size: 12px;
            }
        """)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # 专辑封面（占位符）
        album_frame = QWidget()
        album_frame.setFixedHeight(150)
        album_frame.setStyleSheet("""
            background-color: #2c3e50;
            border: 2px dashed #3498db;
            border-radius: 8px;
        """)
        album_layout = QVBoxLayout(album_frame)
        album_layout.setAlignment(Qt.AlignCenter)
        
        album_icon = QLabel("🎵")
        album_icon.setFont(QFont("Arial", 48))
        album_icon.setAlignment(Qt.AlignCenter)
        album_layout.addWidget(album_icon)
        
        info_layout.addWidget(album_frame)
        
        # 歌曲信息
        self.current_file_label = QLabel("未选择歌曲")
        self.current_file_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.current_file_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setWordWrap(True)
        
        self.song_info_label = QLabel("艺术家: 未知 | 专辑: 未知")
        self.song_info_label.setFont(QFont("Arial", 9))
        self.song_info_label.setStyleSheet("color: #bdc3c7; padding: 3px;")
        self.song_info_label.setAlignment(Qt.AlignCenter)
        
        info_layout.addWidget(self.current_file_label)
        info_layout.addWidget(self.song_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
    def create_progress_panel(self, layout):
        """创建进度控制面板"""
        progress_group = QGroupBox("播放进度")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2ecc71;
                font-size: 12px;
            }
        """)
        
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        
        # 时间显示
        time_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFont(QFont("Arial", 11))
        self.current_time_label.setStyleSheet("color: #ecf0f1;")
        
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setFont(QFont("Arial", 11))
        self.total_time_label.setStyleSheet("color: #ecf0f1;")
        self.total_time_label.setAlignment(Qt.AlignRight)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        progress_layout.addLayout(time_layout)
        
        # 进度条
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #27ae60;
                background: #2c3e50;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2ecc71, stop: 1 #27ae60
                );
                border: 1px solid #27ae60;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #34495e;
                border: 1px solid #27ae60;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #ecf0f1, stop: 1 #bdc3c7
                );
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
                border: 1px solid #7f8c8d;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #ffffff, stop: 1 #ecf0f1
                );
                border: 2px solid #2ecc71;
            }
        """)
        progress_layout.addWidget(self.position_slider)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
    def create_control_panel(self, layout):
        """创建控制按钮面板"""
        control_group = QGroupBox("播放控制")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #e74c3c;
                font-size: 12px;
            }
        """)
        
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        # 创建控制按钮
        buttons = [
            ("⏮", "上一首", self.play_previous, 50, 50),
            ("⏪", "快退10秒", lambda: self.seek_relative(-10), 45, 45),
            ("▶", "播放", self.play_pause, 60, 60),
            ("⏩", "快进10秒", lambda: self.seek_relative(10), 45, 45),
            ("⏭", "下一首", self.play_next, 50, 50),
            ("⏹", "停止", self.stop, 45, 45),
        ]
        
        for icon, tooltip, slot, w, h in buttons:
            btn = QPushButton(icon)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedSize(w, h)
            btn.setToolTip(tooltip)
            btn.clicked.connect(slot)
            
            # 为播放按钮特殊处理
            if icon == "▶":
                self.play_button = btn
            elif icon == "⏹":
                self.stop_button = btn
                
            control_layout.addWidget(btn)
            
        control_layout.insertStretch(0, 1)
        control_layout.addStretch(1)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
    def create_volume_panel(self, layout):
        """创建音量控制面板"""
        volume_group = QGroupBox("音量控制")
        volume_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #9b59b6;
                font-size: 12px;
            }
        """)
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(10)
        
        # 静音按钮
        self.mute_button = QPushButton("🔊")
        self.mute_button.setFont(QFont("Arial", 12))
        self.mute_button.setFixedSize(40, 40)
        self.mute_button.setToolTip("静音")
        
        # 音量滑块
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 128)
        self.volume_slider.setValue(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #8e44ad;
                background: #2c3e50;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #9b59b6, stop: 1 #8e44ad
                );
                border: 1px solid #8e44ad;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #34495e;
                border: 1px solid #8e44ad;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #ecf0f1, stop: 1 #bdc3c7
                );
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
                border: 1px solid #7f8c8d;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #ffffff, stop: 1 #ecf0f1
                );
                border: 2px solid #9b59b6;
            }
        """)
        
        # 音量标签
        self.volume_label = QLabel("80")
        self.volume_label.setFont(QFont("Arial", 11))
        self.volume_label.setFixedWidth(30)
        self.volume_label.setStyleSheet("color: #ecf0f1;")
        
        volume_layout.addWidget(self.mute_button)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)
        
    def create_playmode_panel(self, layout):
        """创建播放模式面板"""
        playmode_group = QGroupBox("播放模式")
        playmode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f39c12;
                border-radius: 10px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #f39c12;
                font-size: 12px;
            }
        """)
        
        playmode_layout = QVBoxLayout()
        playmode_layout.setSpacing(8)
        
        # 播放模式描述
        self.playmode_desc_label = QLabel("顺序播放: 按列表顺序播放，播放完停止")
        self.playmode_desc_label.setFont(QFont("Arial", 9))
        self.playmode_desc_label.setStyleSheet("color: #bdc3c7;")
        self.playmode_desc_label.setWordWrap(True)
        
        # 模式按钮组
        mode_buttons_layout = QHBoxLayout()
        
        self.mode_sequential = QPushButton("顺序")
        self.mode_shuffle = QPushButton("随机")
        self.mode_single = QPushButton("单曲")
        self.mode_loop = QPushButton("列表")
        
        for btn in [self.mode_sequential, self.mode_shuffle, 
                   self.mode_single, self.mode_loop]:
            btn.setFixedSize(60, 30)
            btn.setCheckable(True)
            
        # 设置顺序播放为默认选中
        self.mode_sequential.setChecked(True)
        
        mode_buttons_layout.addWidget(self.mode_sequential)
        mode_buttons_layout.addWidget(self.mode_shuffle)
        mode_buttons_layout.addWidget(self.mode_single)
        mode_buttons_layout.addWidget(self.mode_loop)
        mode_buttons_layout.addStretch()
        
        playmode_layout.addWidget(self.playmode_desc_label)
        playmode_layout.addLayout(mode_buttons_layout)
        
        playmode_group.setLayout(playmode_layout)
        layout.addWidget(playmode_group)
        
        # 添加弹簧使布局更紧凑
        layout.addStretch()
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet("color: #7f8c8d;")
        
        # 播放状态
        self.play_status_label = QLabel("已停止")
        self.play_status_label.setFont(QFont("Arial", 9))
        self.play_status_label.setStyleSheet("color: #3498db;")
        
        # 时间显示
        self.time_status_label = QLabel("00:00 / 00:00")
        self.time_status_label.setFont(QFont("Arial", 9))
        self.time_status_label.setStyleSheet("color: #2ecc71;")
        
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.play_status_label)
        self.status_bar.addPermanentWidget(self.time_status_label)
        
    def create_context_menus(self):
        """创建上下文菜单"""
        # 播放列表右键菜单
        self.playlist_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self.show_playlist_context_menu)
        
    def set_dark_theme(self):
        """设置深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 44, 52))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.Base, QColor(30, 33, 40))
        palette.setColor(QPalette.AlternateBase, QColor(35, 38, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(220, 220, 220))
        palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(50, 54, 63))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(66, 139, 202))
        palette.setColor(QPalette.Highlight, QColor(66, 139, 202))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)
        
    def set_button_styles(self):
        """设置按钮样式"""
        # 控制按钮样式
        control_button_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #34495e, stop: 1 #2c3e50
                );
                color: #ecf0f1;
                border: 2px solid #3498db;
                border-radius: 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9
                );
                border: 2px solid #2980b9;
                color: white;
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #3498db
                );
            }
            QPushButton:checked {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2ecc71, stop: 1 #27ae60
                );
                border: 2px solid #27ae60;
                color: white;
            }
        """
        
        # 播放按钮特殊样式
        play_button_style = """
            QPushButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2ecc71, stop: 1 #27ae60
                );
                color: white;
                border: 2px solid #27ae60;
                border-radius: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #2ecc71
                );
                border: 2px solid #2ecc71;
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #27ae60
                );
            }
        """
        
        # 设置播放按钮样式
        self.play_button.setStyleSheet(play_button_style)
        
        # 设置其他控制按钮样式
        for btn in [self.stop_button, self.mute_button]:
            btn.setStyleSheet(control_button_style)
            
        # 模式按钮样式
        mode_button_style = """
            QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #f39c12;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f39c12;
                color: white;
            }
            QPushButton:checked {
                background-color: #e67e22;
                color: white;
                border: 2px solid #d35400;
            }
        """
        
        for btn in [self.mode_sequential, self.mode_shuffle, 
                   self.mode_single, self.mode_loop]:
            btn.setStyleSheet(mode_button_style)
            
        # 播放列表按钮样式
        playlist_button_style = """
            QPushButton {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
            }
        """
        
        for btn in [self.playlist_clear_button, self.playlist_remove_button,
                   self.playlist_save_button, self.playlist_load_button]:
            btn.setStyleSheet(playlist_button_style)
            
    def setup_connections(self):
        """连接信号和槽"""
        # 工具栏动作连接
        self.open_file_action.triggered.connect(self.open_file)
        self.open_folder_action.triggered.connect(self.open_folder)
        self.play_action.triggered.connect(self.play_pause)
        self.pause_action.triggered.connect(self.pause)
        self.stop_action.triggered.connect(self.stop)
        self.prev_action.triggered.connect(self.play_previous)
        self.next_action.triggered.connect(self.play_next)
        
        # 播放模式按钮连接
        self.mode_sequential.clicked.connect(lambda: self.set_play_mode(self.PLAY_MODE_SEQUENTIAL))
        self.mode_shuffle.clicked.connect(lambda: self.set_play_mode(self.PLAY_MODE_SHUFFLE))
        self.mode_single.clicked.connect(lambda: self.set_play_mode(self.PLAY_MODE_SINGLE))
        self.mode_loop.clicked.connect(lambda: self.set_play_mode(self.PLAY_MODE_LOOP))
        
        # 播放模式组合框连接
        self.playmode_combo.currentIndexChanged.connect(self.on_playmode_changed)
        
        # 播放列表按钮连接
        self.playlist_clear_button.clicked.connect(self.clear_playlist)
        self.playlist_remove_button.clicked.connect(self.remove_selected_items)
        self.playlist_save_button.clicked.connect(self.save_playlist)
        self.playlist_load_button.clicked.connect(self.load_playlist)
        
        # 滑块连接
        self.position_slider.sliderMoved.connect(self.seek_position)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # 播放列表连接
        self.playlist_widget.itemDoubleClicked.connect(self.playlist_item_double_clicked)
        
        # 静音按钮
        self.mute_button.clicked.connect(self.toggle_mute)
        
        # 定时器连接
        self.update_timer.timeout.connect(self.update_ui)
        
    def init_system_tray(self):
        """初始化系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            play_action = QAction("播放/暂停", self)
            play_action.triggered.connect(self.play_pause)
            
            stop_action = QAction("停止", self)
            stop_action.triggered.connect(self.stop)
            
            next_action = QAction("下一首", self)
            next_action.triggered.connect(self.play_next)
            
            show_action = QAction("显示窗口", self)
            show_action.triggered.connect(self.show_normal)
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_application)
            
            tray_menu.addAction(play_action)
            tray_menu.addAction(stop_action)
            tray_menu.addAction(next_action)
            tray_menu.addSeparator()
            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # 托盘图标点击事件
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
    def show_playlist_context_menu(self, position):
        """显示播放列表右键菜单"""
        menu = QMenu()
        
        play_action = QAction("播放", self)
        play_action.triggered.connect(lambda: self.play_selected_item())
        
        remove_action = QAction("移除", self)
        remove_action.triggered.connect(self.remove_selected_items)
        
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(self.clear_playlist)
        
        menu.addAction(play_action)
        menu.addAction(remove_action)
        menu.addSeparator()
        menu.addAction(clear_action)
        
        menu.exec_(self.playlist_widget.mapToGlobal(position))
        
    def open_file(self):
        """打开单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.ogg *.flac *.m4a *.aac);;所有文件 (*.*)"
        )
        
        if file_path:
            self.add_to_playlist(file_path)
            if len(self.playlist) == 1:  # 如果是第一个文件，自动加载
                self.load_file(file_path)
                
    def open_folder(self):
        """打开文件夹并添加所有音频文件"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        
        if folder_path:
            # 清空当前播放列表
            self.playlist.clear()
            self.playlist_widget.clear()
            self.shuffled_indices.clear()
            
            # 遍历文件夹中的音频文件
            audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        file_path = os.path.join(root, file)
                        self.add_to_playlist(file_path)
            
            if self.playlist:
                self.status_label.setText(f"已添加 {len(self.playlist)} 个文件到播放列表")
                self.update_playlist_info()
                
                # 如果当前没有在播放，自动加载第一个文件
                if not self.is_playing:
                    self.load_file(self.playlist[0])
                    
    def add_to_playlist(self, file_path):
        """添加文件到播放列表"""
        if file_path not in self.playlist:
            self.playlist.append(file_path)
            file_name = os.path.basename(file_path)
            
            # 获取文件信息
            try:
                duration_result = self.audio_lib.get_audio_duration(file_path, is_file=True)
                if isinstance(duration_result, tuple):
                    duration = 0
                else:
                    duration = int(duration_result) if duration_result else 0
                    
                duration_str = self.format_time(duration)
                display_text = f"{file_name} ({duration_str})"
            except:
                display_text = file_name
                
            item = QListWidgetItem(f"🎵 {display_text}")
            item.setData(Qt.UserRole, file_path)
            item.setToolTip(file_path)
            self.playlist_widget.addItem(item)
            
            # 设置高亮当前播放的项目
            if self.current_file == file_path:
                item.setSelected(True)
                self.playlist_widget.scrollToItem(item)
                
            # 更新播放列表信息
            self.update_playlist_info()
            
    def update_playlist_info(self):
        """更新播放列表信息"""
        count = len(self.playlist)
        
        # 计算总时长
        total_seconds = 0
        for file_path in self.playlist:
            try:
                duration_result = self.audio_lib.get_audio_duration(file_path, is_file=True)
                if isinstance(duration_result, tuple):
                    continue
                total_seconds += int(duration_result) if duration_result else 0
            except:
                continue
                
        total_time = self.format_time(total_seconds)
        self.playlist_info_label.setText(f"共 {count} 首歌曲 | 总时长: {total_time}")
        
    def remove_selected_items(self):
        """移除选中的播放列表项"""
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return
            
        reply = QMessageBox.question(
            self, "确认", f"确定要移除选中的 {len(selected_items)} 个项目吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                file_path = item.data(Qt.UserRole)
                if file_path in self.playlist:
                    index = self.playlist.index(file_path)
                    self.playlist.pop(index)
                    
                    # 如果移除的是当前播放的文件
                    if file_path == self.current_file:
                        self.stop()
                        self.current_file = None
                        self.current_index = -1
                        
                self.playlist_widget.takeItem(self.playlist_widget.row(item))
                
            self.update_playlist_info()
            
    def save_playlist(self):
        """保存播放列表到文件"""
        if not self.playlist:
            QMessageBox.warning(self, "警告", "播放列表为空，无法保存")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存播放列表", "", "播放列表文件 (*.m3u);;文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for item_path in self.playlist:
                        f.write(item_path + '\n')
                        
                self.status_label.setText(f"播放列表已保存到: {file_path}")
                QMessageBox.information(self, "成功", "播放列表保存成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存播放列表失败: {e}")
                
    def load_playlist(self):
        """从文件加载播放列表"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载播放列表", "", "播放列表文件 (*.m3u *.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # 清空当前播放列表
                self.playlist.clear()
                self.playlist_widget.clear()
                self.shuffled_indices.clear()
                
                for line in lines:
                    line = line.strip()
                    if line and os.path.exists(line):
                        self.add_to_playlist(line)
                        
                if self.playlist:
                    self.status_label.setText(f"已加载 {len(self.playlist)} 个文件")
                    QMessageBox.information(self, "成功", "播放列表加载成功！")
                else:
                    QMessageBox.warning(self, "警告", "播放列表文件为空或文件路径无效")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载播放列表失败: {e}")
                
    def clear_playlist(self):
        """清空播放列表"""
        if not self.playlist:
            return
            
        reply = QMessageBox.question(
            self, "确认", "确定要清空播放列表吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.playlist.clear()
            self.playlist_widget.clear()
            self.shuffled_indices.clear()
            self.current_index = -1
            self.current_file = None
            self.current_file_label.setText("未选择歌曲")
            self.song_info_label.setText("艺术家: 未知 | 专辑: 未知")
            self.update_playlist_info()
            
            # 停止当前播放
            if self.is_playing and self.current_aid:
                self.stop()
                
    def load_file(self, file_path):
        """加载音频文件"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            # 停止当前播放
            if self.is_playing and self.current_aid:
                try:
                    self.audio_lib.stop_audio(self.current_aid)
                except:
                    pass
                    
            self.is_playing = False
            self.is_paused = False
            self.play_button.setText("▶")
            
            # 设置当前文件
            self.current_file = file_path
            self.current_file_name = os.path.basename(file_path)
            
            # 更新显示信息
            self.current_file_label.setText(self.current_file_name)
            
            # 尝试提取艺术家和专辑信息
            file_dir = os.path.dirname(file_path)
            folder_name = os.path.basename(file_dir)
            self.song_info_label.setText(f"艺术家: 未知 | 专辑: {folder_name}")
            
            # 更新当前索引
            if file_path in self.playlist:
                self.current_index = self.playlist.index(file_path)
                
                # 如果是随机播放模式，更新随机索引
                if self.play_mode == self.PLAY_MODE_SHUFFLE:
                    if not self.shuffled_indices:
                        self.generate_shuffle_indices()
                        
            # 高亮当前播放的项目
            for i in range(self.playlist_widget.count()):
                item = self.playlist_widget.item(i)
                if item.data(Qt.UserRole) == file_path:
                    item.setSelected(True)
                    self.playlist_widget.scrollToItem(item)
                    
                    # 更新项目文本，添加播放标志
                    current_text = item.text()
                    if not current_text.startswith("▶ "):
                        item.setText("▶ " + current_text.lstrip("🎵 ▶ "))
                else:
                    item.setSelected(False)
                    # 移除其他项目的播放标志
                    text = item.text()
                    if text.startswith("▶ "):
                        item.setText("🎵 " + text[2:])
            
            # 获取音频时长
            try:
                duration_result = self.audio_lib.get_audio_duration(file_path, is_file=True)
                if isinstance(duration_result, tuple):
                    self.total_duration = 300  # 默认5分钟
                else:
                    self.total_duration = float(duration_result) if duration_result else 300
            except:
                self.total_duration = 300
                
            # 更新总时长显示
            self.total_time_label.setText(self.format_time(self.total_duration))
            
            # 加载音频到内存
            try:
                if self.current_aid:
                    try:
                        old_file = self.audio_lib._get_file_path_by_aid(self.current_aid)
                        if old_file in self.audio_lib._audio_cache:
                            self.audio_lib._audio_cache.pop(old_file, None)
                        elif old_file in self.audio_lib._music_cache:
                            self.audio_lib._music_cache.pop(old_file, None)
                    except:
                        pass
                        
                self.current_aid = self.audio_lib.new_aid(file_path)
                print(f"加载音频成功，AID: {self.current_aid}")
                
                # 设置音量和播放速度
                self.audio_lib.set_volume(self.current_aid, self.volume)

                
                self.status_label.setText(f"已加载: {self.current_file_name}")
                self.play_status_label.setText("已加载")
                
            except Exception as e:
                raise Exception(f"加载音频失败: {e}")
                
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载文件失败: {e}")
            self.status_label.setText(f"加载失败: {e}")
            
    def play_selected_item(self):
        """播放选中的项目"""
        selected_items = self.playlist_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            file_path = item.data(Qt.UserRole)
            self.load_file(file_path)
            if not self.is_playing:
                self.play_pause()
                
    def playlist_item_double_clicked(self, item):
        """播放列表项双击事件"""
        file_path = item.data(Qt.UserRole)
        self.load_file(file_path)
        if not self.is_playing:
            self.play_pause()
            
    def play_pause(self):
        """播放/暂停"""
        if not self.current_file or not self.current_aid:
            if self.playlist:
                # 如果没有当前文件，但有播放列表，播放第一个
                self.load_file(self.playlist[0])
                if self.current_aid:
                    self.start_playback()
            else:
                self.status_label.setText("请先选择音频文件")
            return
            
        try:
            if not self.is_playing:
                self.start_playback()
            else:
                if self.is_paused:
                    self.resume_playback()
                else:
                    self.pause_playback()
                    
        except Exception as e:
            print(f"播放控制失败: {e}")
            self.status_label.setText(f"播放失败: {e}")
            
    def start_playback(self):
        """开始播放"""
        print(f"开始播放，AID: {self.current_aid}")
        try:
            self.current_aid = self.audio_lib.play_from_memory(self.current_file)
        except Exception as e:
            print(f"从内存播放失败，尝试从文件播放: {e}")
            self.current_aid = self.audio_lib.play_from_file(self.current_file)
        
        self.is_playing = True
        self.is_paused = False
        self.play_button.setText("⏸")
        self.playback_start_time = time.time()
        self.current_position = 0
        
        # 设置音量和播放速度
        self.audio_lib.set_volume(self.current_aid, self.volume)
        
        self.status_label.setText(f"正在播放: {self.current_file_name}")
        self.play_status_label.setText("播放中")
        self.state_changed.emit("playing")
        
    def pause_playback(self):
        """暂停播放"""
        print("暂停播放")
        self.audio_lib.pause_audio(self.current_aid)
        self.is_paused = True
        self.play_button.setText("▶")
        self.current_position = time.time() - self.playback_start_time
        self.status_label.setText(f"已暂停: {self.current_file_name}")
        self.play_status_label.setText("已暂停")
        self.state_changed.emit("paused")
        
    def resume_playback(self):
        """恢复播放"""
        print("恢复播放")
        self.audio_lib.play_audio(self.current_aid)
        self.is_paused = False
        self.play_button.setText("⏸")
        self.playback_start_time = time.time() - self.current_position
        self.status_label.setText(f"正在播放: {self.current_file_name}")
        self.play_status_label.setText("播放中")
        self.state_changed.emit("playing")
        
    def pause(self):
        """暂停播放（工具栏专用）"""
        if self.is_playing and not self.is_paused:
            self.pause_playback()
            
    def stop(self):
        """停止播放"""
        if self.is_playing and self.current_aid:
            try:
                print("停止播放")
                played_time = self.audio_lib.stop_audio(self.current_aid)
                print(f"已停止播放，播放时长: {played_time:.2f}秒")
                
                self.is_playing = False
                self.is_paused = False
                self.play_button.setText("▶")
                self.position_slider.setValue(0)
                self.current_position = 0
                self.current_time_label.setText("00:00")
                
                self.status_label.setText(f"已停止: {self.current_file_name}")
                self.play_status_label.setText("已停止")
                self.state_changed.emit("stopped")
                
            except Exception as e:
                print(f"停止播放失败: {e}")
                self.status_label.setText(f"停止失败: {e}")
                
    def play_previous(self):
        """播放上一首"""
        if not self.playlist:
            return
            
        if self.current_index >= 0:
            if self.play_mode == self.PLAY_MODE_SHUFFLE:
                self.play_previous_shuffle()
            else:
                if self.current_index > 0:
                    self.current_index -= 1
                elif self.play_mode == self.PLAY_MODE_LOOP:
                    self.current_index = len(self.playlist) - 1
                else:
                    return
                    
                file_path = self.playlist[self.current_index]
                self.load_file(file_path)
                if not self.is_playing:
                    self.play_pause()
                    
    def play_previous_shuffle(self):
        """随机播放模式下的上一首"""
        if not self.shuffled_indices:
            self.generate_shuffle_indices()
            
        current_shuffle_index = self.get_current_shuffle_index()
        if current_shuffle_index > 0:
            new_index = self.shuffled_indices[current_shuffle_index - 1]
            self.current_index = new_index
            file_path = self.playlist[self.current_index]
            self.load_file(file_path)
            if not self.is_playing:
                self.play_pause()
                
    def play_next(self):
        """播放下一首"""
        if not self.playlist:
            return
            
        if self.play_mode == self.PLAY_MODE_SINGLE:
            # 单曲循环，重新播放当前歌曲
            if self.current_file:
                self.load_file(self.current_file)
                if not self.is_playing:
                    self.play_pause()
            return
            
        if self.current_index >= 0:
            if self.play_mode == self.PLAY_MODE_SHUFFLE:
                self.play_next_shuffle()
            else:
                if self.current_index < len(self.playlist) - 1:
                    self.current_index += 1
                elif self.play_mode == self.PLAY_MODE_LOOP:
                    self.current_index = 0
                else:
                    # 顺序播放到最后一首，停止播放
                    self.stop()
                    return
                    
                file_path = self.playlist[self.current_index]
                self.load_file(file_path)
                if not self.is_playing:
                    self.play_pause()
                    
    def play_next_shuffle(self):
        """随机播放模式下的下一首"""
        if not self.shuffled_indices:
            self.generate_shuffle_indices()
            
        current_shuffle_index = self.get_current_shuffle_index()
        if current_shuffle_index < len(self.shuffled_indices) - 1:
            new_index = self.shuffled_indices[current_shuffle_index + 1]
            self.current_index = new_index
            file_path = self.playlist[self.current_index]
            self.load_file(file_path)
            if not self.is_playing:
                self.play_pause()
        else:
            # 随机播放列表结束，重新生成或停止
            if self.play_mode == self.PLAY_MODE_SHUFFLE:
                self.generate_shuffle_indices()
                if self.shuffled_indices:
                    self.current_index = self.shuffled_indices[0]
                    file_path = self.playlist[self.current_index]
                    self.load_file(file_path)
                    if not self.is_playing:
                        self.play_pause()
                        
    def generate_shuffle_indices(self):
        """生成随机播放的索引列表"""
        if not self.playlist:
            return
            
        indices = list(range(len(self.playlist)))
        random.shuffle(indices)
        
        # 确保当前播放的歌曲不在第一个位置（如果可能）
        if self.current_index in indices and indices[0] == self.current_index and len(indices) > 1:
            indices[0], indices[1] = indices[1], indices[0]
            
        self.shuffled_indices = indices
        
    def get_current_shuffle_index(self):
        """获取当前歌曲在随机播放列表中的位置"""
        if self.current_index in self.shuffled_indices:
            return self.shuffled_indices.index(self.current_index)
        return -1
        
    def set_play_mode(self, mode):
        """设置播放模式"""
        self.play_mode = mode
        
        # 更新按钮状态
        self.mode_sequential.setChecked(mode == self.PLAY_MODE_SEQUENTIAL)
        self.mode_shuffle.setChecked(mode == self.PLAY_MODE_SHUFFLE)
        self.mode_single.setChecked(mode == self.PLAY_MODE_SINGLE)
        self.mode_loop.setChecked(mode == self.PLAY_MODE_LOOP)
        
        # 更新组合框
        self.playmode_combo.setCurrentIndex(mode)
        
        # 更新模式描述
        descriptions = [
            "顺序播放: 按列表顺序播放，播放完停止",
            "随机播放: 随机播放列表中的歌曲",
            "单曲循环: 重复播放当前歌曲",
            "列表循环: 按列表顺序循环播放"
        ]
        self.playmode_desc_label.setText(descriptions[mode])
        
        # 如果是随机播放模式，生成随机索引
        if mode == self.PLAY_MODE_SHUFFLE:
            self.generate_shuffle_indices()
            
        self.status_label.setText(f"播放模式已切换: {self.playmode_combo.currentText()}")
        
    def on_playmode_changed(self, index):
        """播放模式组合框变化"""
        mode = self.playmode_combo.currentData()
        self.set_play_mode(mode)
        
    def toggle_mute(self):
        """切换静音"""
        if not self.is_muted:
            self.last_volume = self.volume_slider.value()
            self.volume_slider.setValue(0)
            self.mute_button.setText("🔇")
            self.is_muted = True
        else:
            self.volume_slider.setValue(self.last_volume)
            self.mute_button.setText("🔊")
            self.is_muted = False
            
    def set_volume(self, value):
        """设置音量"""
        self.volume = value
        self.volume_label.setText(str(value))
        
        if self.current_aid and self.is_playing:
            try:
                self.audio_lib.set_volume(self.current_aid, value)
            except Exception as e:
                print(f"设置音量失败: {e}")
                
        # 更新静音状态
        if value == 0:
            self.is_muted = True
            self.mute_button.setText("🔇")
        else:
            self.is_muted = False
            self.mute_button.setText("🔊")
            
        self.volume_changed.emit(value)
        
    def on_speed_changed(self, index):
        """播放速度变化"""
        pass
    def seek_position(self, value):
        """跳转到指定位置"""
        if self.total_duration > 0:
            position = (value / 1000.0) * self.total_duration
            if self.is_playing and self.current_aid:
                try:
                    self.audio_lib.seek_audio(self.current_aid, position)
                    self.playback_start_time = time.time() - position
                    self.current_position = position
                except Exception as e:
                    print(f"跳转失败: {e}")
                    
    def seek_relative(self, seconds):
        """相对跳转（快进/快退）"""
        if self.is_playing and self.current_aid and self.total_duration > 0:
            current_time = time.time() - self.playback_start_time
            new_position = max(0, min(self.total_duration, current_time + seconds))
            
            try:
                self.audio_lib.seek_audio(self.current_aid, new_position)
                self.playback_start_time = time.time() - new_position
                self.current_position = new_position
            except Exception as e:
                print(f"跳转失败: {e}")
                
    def update_ui(self):
        """更新UI"""
        try:
            if self.is_playing and not self.is_paused and self.current_aid:
                if self.playback_start_time > 0:
                    current_time = time.time() - self.playback_start_time
                    self.current_position = current_time
                    
                    # 防止超出总时长
                    if self.total_duration > 0 and current_time >= self.total_duration:
                        current_time = self.total_duration
                        # 歌曲播放结束，根据播放模式处理
                        self.on_track_end()
                        
                        if not self.is_playing:
                            return
                    
                    # 更新时间显示
                    self.current_time_label.setText(self.format_time(current_time))
                    self.time_status_label.setText(
                        f"{self.format_time(current_time)} / {self.format_time(self.total_duration)}"
                    )
                    
                    # 更新进度条
                    if self.total_duration > 0:
                        progress_value = int((current_time / self.total_duration) * 1000)
                        self.position_slider.setValue(progress_value)
                        
        except Exception as e:
            print(f"更新UI时出错: {e}")
            
    def on_track_end(self):
        """处理歌曲播放结束"""
        if self.play_mode == self.PLAY_MODE_SINGLE:
            # 单曲循环，重新播放
            self.load_file(self.current_file)
            self.start_playback()
        else:
            # 其他模式，播放下一首
            self.play_next()
            
    def format_time(self, seconds):
        """格式化时间显示"""
        if not seconds:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def show_normal(self):
        """显示窗口"""
        self.show()
        self.activateWindow()
        self.raise_()
        
    def on_tray_icon_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()
            
    def quit_application(self):
        """退出应用程序"""
        self.cleanup()
        QApplication.quit()
        
    def closeEvent(self, event):
        """关闭窗口事件"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # 如果有托盘图标，最小化到托盘
            self.hide()
            event.ignore()
            self.tray_icon.showMessage(
                "Modern Audio Player",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # 否则正常退出
            self.cleanup()
            event.accept()
            
    def cleanup(self):
        """清理资源"""
        try:
            if self.audio_lib:
                print("清理音频库资源...")
                if self.current_aid and self.is_playing:
                    try:
                        self.audio_lib.stop_audio(self.current_aid)
                    except:
                        pass
                self.audio_lib.clear_memory_cache()
        except Exception as e:
            print(f"清理资源时出错: {e}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Modern Audio Player")
    app.setApplicationDisplayName("Modern Audio Player")
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置应用程序图标
    app.setWindowIcon(QIcon(":icons/media-play"))
    
    player = ModernAudioPlayer()
    player.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
