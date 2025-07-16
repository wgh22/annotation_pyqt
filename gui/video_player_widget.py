import os
import cv2
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

# Import the timeline widget
from gui.timeline_widget import AnnotationTimelineWidget

class VideoPlayerWidget(QWidget):
    """
    一个用于直接播放MP4视频文件的自定义控件。
    它包含一个显示标签、一个导航滑块和播放控制按钮。
    """
    # 当帧索引改变时发出信号，携带新的帧号。
    frameChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_capture = None
        self.current_frame_index = -1
        self.total_frames = 0
        self.is_playing = False
        self.segment_end_frame = -1 # 用于跟踪片段播放的结束帧

        # --- UI 元素 ---
        self.image_label = QLabel("Please select a video project to start.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: black; color: white; }")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        
        self.segment_info_label = QLabel("Click a segment on the timeline to see its instruction.")
        self.segment_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.segment_info_label.setStyleSheet("QLabel { color: #2d3436; font-style: italic; }")

        self.timeline = AnnotationTimelineWidget()
        
        self.play_pause_button = QPushButton("Play")
        self.prev_frame_button = QPushButton("<< Prev")
        self.next_frame_button = QPushButton("Next >>")
        
        self.current_frame_label = QLabel("Frame: N/A")
        self.frame_number_label = QLabel("Total Frames: 0")

        # --- 布局 ---
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.prev_frame_button)
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(self.next_frame_button)
        control_layout.addStretch()
        control_layout.addWidget(self.current_frame_label)
        control_layout.addStretch()
        control_layout.addWidget(self.frame_number_label)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label, 1)
        main_layout.addWidget(self.slider, 0)
        main_layout.addWidget(self.segment_info_label, 0)
        main_layout.addWidget(self.timeline, 0) 
        main_layout.addLayout(control_layout, 0)
        self.setLayout(main_layout)

        # --- 用于播放的定时器 ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance_frame)

        # --- 连接 ---
        self.slider.valueChanged.connect(self.set_frame_by_slider)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.prev_frame_button.clicked.connect(self.go_to_prev_frame)
        self.next_frame_button.clicked.connect(self.go_to_next_frame)
        self.timeline.segmentClicked.connect(self.play_segment)

    def load_video(self, video_path: str):
        """
        加载指定的MP4视频文件并准备播放。
        """
        self.stop_playback()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        if not os.path.exists(video_path):
            self.image_label.setText(f"Video file not found:\n{video_path}")
            self._reset_player_state()
            return
        
        self.video_capture = cv2.VideoCapture(video_path)
        if not self.video_capture.isOpened():
            self.image_label.setText(f"Could not open video file:\n{video_path}")
            self._reset_player_state()
            return

        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        
        self.timer.setInterval(int(1000 / fps) if fps > 0 else 40)

        if self.total_frames > 0:
            self.slider.setRange(0, self.total_frames - 1)
            self.frame_number_label.setText(f"Total Frames: {self.total_frames}")
            self.segment_info_label.setText("Click a segment on the timeline to see its instruction.")
            self.set_frame_by_index(0)
        else:
            self.image_label.setText("Video has no frames.")
            self._reset_player_state()
            
    def _reset_player_state(self):
        """重置播放器状态。"""
        self.total_frames = 0
        self.current_frame_index = -1
        self.slider.setRange(0, 0)
        self.current_frame_label.setText("Frame: N/A")
        self.timeline.set_data([], 0)
        self.segment_info_label.setText("Click a segment on the timeline to see its instruction.")

    def set_frame_by_index(self, index: int):
        """
        通过帧索引号显示对应的视频帧。
        """
        if not self.video_capture or not (0 <= index < self.total_frames):
            return
            
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.video_capture.read()

        if ret and index != self.current_frame_index:
            self.current_frame_index = index
            self._display_frame(frame)
            if not self.slider.isSliderDown():
                self.slider.setValue(index)
            self.current_frame_label.setText(f"Frame: {index}")
            self.frameChanged.emit(index)

    def set_frame_by_slider(self, index: int):
        """当滑块被手动拖动时调用。"""
        self.set_frame_by_index(index)

    def _display_frame(self, frame):
        """将OpenCV的帧（BGR）转换为QPixmap并显示。"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def toggle_play_pause(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
            
    def start_playback(self):
        if self.total_frames > 0:
            self.is_playing = True
            self.play_pause_button.setText("Pause")
            self.timer.start()

    def stop_playback(self):
        self.is_playing = False
        self.play_pause_button.setText("Play")
        self.timer.stop()
        self.segment_end_frame = -1 
        #self.segment_info_label.setText("Click a segment on the timeline to see its instruction.")

    def advance_frame(self):
        """定时器调用的方法，用于播放下一帧。"""
        if self.segment_end_frame != -1 and self.current_frame_index >= self.segment_end_frame:
            self.stop_playback()
            return

        if self.video_capture:
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self._display_frame(frame)
                self.slider.setValue(self.current_frame_index)
                self.current_frame_label.setText(f"Frame: {self.current_frame_index}")
                self.frameChanged.emit(self.current_frame_index)
            else:
                self.stop_playback()

    def go_to_next_frame(self):
        if self.total_frames > 0:
            next_index = min(self.current_frame_index + 1, self.total_frames - 1)
            self.set_frame_by_index(next_index)

    def go_to_prev_frame(self):
        if self.total_frames > 0:
            prev_index = max(self.current_frame_index - 1, 0)
            self.set_frame_by_index(prev_index)
    
    def cleanup(self):
        """释放视频捕获对象。"""
        if self.video_capture:
            self.video_capture.release()

    def resizeEvent(self, event):
        """处理窗口大小调整以重新缩放图像。"""
        super().resizeEvent(event)
        if self.video_capture and self.current_frame_index != -1:
            self.set_frame_by_index(self.current_frame_index)

    def update_annotations(self, annotations: list):
        """Public method to refresh the timeline display."""
        self.timeline.set_data(annotations, self.total_frames)

    def play_segment(self, start_frame: int, end_frame: int, instruction: str):
        """
        UPDATED: Public method to play a specific segment and display its instruction.
        """
        if self.total_frames == 0:
            return
        self.stop_playback()
        self.segment_end_frame = end_frame
        self.segment_info_label.setText(f"Playing: {instruction}")
        self.set_frame_by_index(start_frame)
        # Use a short delay to ensure the frame is displayed before playback starts
        QTimer.singleShot(50, self.start_playback)
