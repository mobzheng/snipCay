#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QSlider, QLabel, QStyle, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTime, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QFont, QColor, QPainter, QTextDocument


class VideoPlayer(QWidget):
    # 自定义信号
    position_changed = pyqtSignal(int)  # 播放位置变化信号
    state_changed = pyqtSignal(bool)    # 播放状态变化信号
    
    def __init__(self):
        """初始化视频播放器"""
        super().__init__()
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)  # 设置默认音量为70%
        
        self.media_path = None
        self.duration = 0
        
        # 字幕相关属性
        self.current_subtitle = None
        self.subtitle_font = QFont("Arial", 16)
        self.subtitle_color = QColor(255, 255, 255)  # 白色
        self.subtitle_background = QColor(0, 0, 0, 128)  # 半透明黑色
        self.subtitle_position = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        
        # 设置界面
        self.setup_ui()
        
        # 设置信号连接
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频控件
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setStyleSheet("background-color: black;")
        
        # 连接媒体播放器和视频控件
        self.media_player.setVideoOutput(self.video_widget)
        
        # 添加视频控件到布局
        layout.addWidget(self.video_widget)
        
        # 创建控制面板
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.setSpacing(10)  # 增加控件间距
        
        # 播放/暂停按钮
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setFixedSize(32, 32)
        controls_layout.addWidget(self.play_button)
        
        # 时间和进度条区域
        time_slider_layout = QHBoxLayout()
        
        # 当前时间标签
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("color: white;")
        self.time_label.setFixedWidth(70)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_slider_layout.addWidget(self.time_label)
        
        # 进度条
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        time_slider_layout.addWidget(self.position_slider)
        
        # 总时长标签
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("color: white;")
        self.duration_label.setFixedWidth(70)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        time_slider_layout.addWidget(self.duration_label)
        
        # 添加时间和进度条区域到主控制布局
        controls_layout.addLayout(time_slider_layout, 1)
        
        # 音量控制区域
        volume_layout = QHBoxLayout()
        
        # 音量按钮
        self.volume_button = QPushButton()
        self.volume_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.volume_button.setFixedSize(32, 32)
        volume_layout.addWidget(self.volume_button)
        
        # 音量滑块
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        volume_layout.addWidget(self.volume_slider)
        
        # 添加音量控制区域到主控制布局
        controls_layout.addLayout(volume_layout)
        
        # 创建控制面板容器
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: #333;")
        controls_frame.setLayout(controls_layout)
        
        # 添加控制面板到主布局
        layout.addWidget(controls_frame)
        
    def setup_connections(self):
        """设置视频播放器信号连接"""
        # 连接播放器状态变化信号
        self.media_player.playbackStateChanged.connect(self.update_play_button)
        
        # 连接播放器位置变化信号
        self.media_player.positionChanged.connect(self.update_position)
        # 直接在位置变化时发送自定义信号
        self.media_player.positionChanged.connect(self.emit_position_direct)
        
        # 连接播放器持续时间变化信号
        self.media_player.durationChanged.connect(self.update_duration)
        
        # 连接错误信号
        self.media_player.errorOccurred.connect(self.handle_error)
        
        # 连接媒体状态变化信号
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # 连接按钮动作
        self.play_button.clicked.connect(self.toggle_play)
        # self.stop_button.clicked.connect(self.stop)  # 移除这一行
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.sliderMoved.connect(self.set_volume)
        self.volume_button.clicked.connect(self.toggle_mute)

    def handle_error(self, error):
        """处理播放器错误"""
        if error != QMediaPlayer.Error.NoError:
            error_msg = "未知错误"
            if error == QMediaPlayer.Error.ResourceError:
                error_msg = "无法加载媒体资源"
            elif error == QMediaPlayer.Error.FormatError:
                error_msg = "不支持的媒体格式"
            elif error == QMediaPlayer.Error.NetworkError:
                error_msg = "网络错误"
            elif error == QMediaPlayer.Error.AccessDeniedError:
                error_msg = "访问被拒绝"
            print(f"播放器错误: {error_msg}")

    def handle_media_status(self, status):
        """处理媒体状态变化"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            print("媒体加载完成")
            # 确保视频输出和音频输出已正确设置
            if not self.media_player.hasVideo():
                self.media_player.setVideoOutput(self.video_widget)
            if not self.audio_output:
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)
                self.audio_output.setVolume(0.7)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("无效的媒体文件")
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            print("没有加载媒体文件")
        elif status == QMediaPlayer.MediaStatus.BufferedMedia:
            print("媒体已缓冲")
        elif status == QMediaPlayer.MediaStatus.StalledMedia:
            print("媒体播放已暂停")
        # 连接视频输出相关信号
        if hasattr(self, 'video_output'):
            # 尝试连接视频输出的信号
            pass
        
    def set_media(self, file_path):
        """加载媒体文件"""
        self.media_path = file_path
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        
        # 重置进度条
        self.position_slider.setValue(0)
        self.time_label.setText("00:00:00")
        
        self.stop()
        
    def get_media_path(self):
        """获取当前媒体路径"""
        return self.media_path
    
    def has_media(self):
        """检查是否有加载媒体"""
        return self.media_path is not None
        
    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def play(self):
        """播放视频"""
        if not self.has_media():
            print("没有加载媒体文件")
            return
            
        if not self.media_player:
            print("播放器未初始化")
            return
            
        # 确保视频输出已设置
        if not self.media_player.hasVideo():
            self.media_player.setVideoOutput(self.video_widget)
            
        # 确保音频输出已设置
        if not self.audio_output:
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.7)
            
        # 检查媒体状态
        media_status = self.media_player.mediaStatus()
        if media_status == QMediaPlayer.MediaStatus.NoMedia:
            print("没有加载媒体文件")
            return
        elif media_status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("无效的媒体文件")
            return
            
        # 开始播放
        self.media_player.play()
        
        # 更新播放按钮状态
        self.update_play_button(QMediaPlayer.PlaybackState.PlayingState)
        
    def pause(self):
        """暂停播放"""
        self.media_player.pause()
        
    def stop(self):
        """停止播放"""
        self.media_player.stop()
        
    def set_position(self, position):
        """设置播放位置"""
        self.media_player.setPosition(int(position))
        
    def seek(self, position_ms):
        """
        跳转到指定时间点
        
        Args:
            position_ms (int): 目标时间点（毫秒）
        """
        # 转换毫秒到视频播放器使用的格式
        position = position_ms
        self.media_player.setPosition(position)
    
    def get_position(self):
        """获取当前播放位置（毫秒）"""
        position = self.media_player.position()
        self.position_changed.emit(position)
        return position
        
    def set_volume(self, volume):
        """设置音量"""
        self.audio_output.setVolume(volume / 100.0)
        
    def toggle_mute(self):
        """切换静音状态"""
        self.audio_output.setMuted(not self.audio_output.isMuted())
        
        # 更新图标
        if self.audio_output.isMuted():
            self.volume_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
        else:
            self.volume_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        
    def update_position(self, position):
        """更新播放位置"""
        # 更新滑块位置（不触发sliderMoved信号）
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        
        # 更新时间标签，只显示当前时间，不显示总时长
        current_info = self.format_time(position)
        self.time_label.setText(current_info)
        
    def update_duration(self, duration):
        """更新媒体总时长"""
        self.duration = duration
        self.position_slider.setRange(0, duration)
        
        # 格式化时间
        time = QTime(0, 0, 0).addMSecs(duration)
        format_string = "hh:mm:ss" if duration > 3600000 else "mm:ss"
        self.duration_label.setText(time.toString(format_string))
        
    def update_play_button(self, state):
        """更新播放按钮状态"""
        is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.state_changed.emit(is_playing)
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        
    def is_playing(self):
        """检查是否正在播放"""
        return self.media_player.isPlaying()
        

    def format_time(self, milliseconds):
        """格式化时间（毫秒转为时:分:秒）"""
        if milliseconds < 0:
            milliseconds = 0
            
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        
        seconds %= 60
        minutes %= 60
        
        # 根据视频长度决定是否显示小时
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def handle_playing_changed(self, playing):
        """处理播放状态变化"""
        if playing:
            self.position_timer.start()
        else:
            self.position_timer.stop()
    
    def emit_position(self):
        """发送当前位置信号"""
        if self.media_player.isPlaying():
            position = self.get_position()
            self.position_changed.emit(position)

    def emit_position_direct(self, position):
        """直接发送位置信号，替代定时器方法"""
        # 可以添加节流逻辑，比如每200ms才发送一次信号
        if not hasattr(self, '_last_emit_time') or position - getattr(self, '_last_emit_time', 0) >= 200:
            self._last_emit_time = position
            self.position_changed.emit(position)

    def get_duration(self):
        """获取视频总时长（毫秒）"""
        return self.media_player.duration()
        return 0

    def paintEvent(self, event):
        """重写绘制事件以显示字幕"""
        if self.current_subtitle:
            painter = QPainter(self)
            doc = QTextDocument()
            doc.setDefaultFont(self.subtitle_font)
            
            # 设置字幕样式，使用类属性而不是硬编码颜色
            color_str = f"rgb({self.subtitle_color.red()},{self.subtitle_color.green()},{self.subtitle_color.blue()})"
            bg_color_str = f"rgba({self.subtitle_background.red()},{self.subtitle_background.green()},{self.subtitle_background.blue()},{self.subtitle_background.alpha()/255})"
            html = f'<div style="color: {color_str}; background-color: {bg_color_str}; padding: 5px;">{self.current_subtitle}</div>'
            doc.setHtml(html)
            
            # 计算字幕位置
            x = (self.width() - doc.size().width()) / 2
            y = self.height() - doc.size().height() - 20  # 距离底部20像素
            
            # 绘制字幕
            painter.translate(x, y)
            doc.drawContents(painter)
            
    def set_subtitle(self, text):
        """设置当前字幕文本"""
        self.current_subtitle = text
        self.update()  # 触发重绘
        
    def set_subtitle_font(self, font):
        """设置字幕字体"""
        self.subtitle_font = font
        self.update()
        
    def set_subtitle_color(self, color):
        """设置字幕颜色"""
        self.subtitle_color = color
        self.update()
        
    def set_subtitle_background(self, color):
        """设置字幕背景颜色"""
        self.subtitle_background = color
        self.update()