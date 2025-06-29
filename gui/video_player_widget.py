import os
import cv2
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class VideoPlayerWidget(QWidget):
    """
    A custom widget for playing video frames from a sequence of images.
    It includes a display label, a navigation slider, and playback controls.
    """
    # Signal emitted when the frame index changes, carrying the new frame number.
    frameChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_files = []
        self.current_frame_index = -1
        self.total_frames = 0
        self.is_playing = False

        # --- UI Elements ---
        self.image_label = QLabel("Please select a video folder to start.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: black; color: white; }")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        
        self.play_pause_button = QPushButton("Play")
        self.prev_frame_button = QPushButton("<< Prev")
        self.next_frame_button = QPushButton("Next >>")
        
        self.current_frame_label = QLabel("Frame: N/A")

        # --- Layout ---
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.prev_frame_button)
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(self.next_frame_button)
        control_layout.addStretch()
        control_layout.addWidget(self.current_frame_label)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(self.slider)
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)

        # --- Timer for playback ---
        self.timer = QTimer(self)
        self.timer.setInterval(40) # Corresponds to 25 FPS (1000/40)
        self.timer.timeout.connect(self.next_frame)

        # --- Connections ---
        self.slider.valueChanged.connect(self.set_frame_by_index)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.prev_frame_button.clicked.connect(self.prev_frame)
        self.next_frame_button.clicked.connect(self.next_frame)

    def load_image_sequence(self, img_folder_path: str):
        """
        Loads all image files from a given folder and prepares for playback.
        """
        self.stop_playback()
        self.image_files = []
        if not os.path.isdir(img_folder_path):
            self.image_label.setText(f"Image folder not found:\n{img_folder_path}")
            self.total_frames = 0
            self.slider.setRange(0, 0)
            return

        # Find all png files and sort them numerically
        try:
            files = [f for f in os.listdir(img_folder_path) if f.lower().endswith('.png')]
            self.image_files = sorted(files, key=lambda x: int(os.path.splitext(x)[0]))
            self.image_files = [os.path.join(img_folder_path, f) for f in self.image_files]
        except (ValueError, FileNotFoundError) as e:
             self.image_label.setText(f"Error reading image files:\n{e}")
             return

        self.total_frames = len(self.image_files)
        if self.total_frames > 0:
            self.slider.setRange(0, self.total_frames - 1)
            self.set_frame_by_index(0)
        else:
            self.image_label.setText(f"No images found in:\n{img_folder_path}")
            self.slider.setRange(0, 0)
            self.current_frame_label.setText("Frame: N/A")

    def set_frame_by_index(self, index: int):
        """
        Displays the frame corresponding to the given index.
        """
        if 0 <= index < self.total_frames and self.current_frame_index != index:
            self.current_frame_index = index
            
            # Load image with OpenCV
            image = cv2.imread(self.image_files[index])
            if image is None: return

            # Convert to QPixmap
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

            # Update UI elements
            if not self.slider.isSliderDown():
                self.slider.setValue(index)
            self.current_frame_label.setText(f"Frame: {index}")
            self.frameChanged.emit(index)

    def toggle_play_pause(self):
        """
        Starts or pauses the video playback.
        """
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

    def next_frame(self):
        """Moves to the next frame, looping back to the start if at the end."""
        if self.total_frames > 0:
            next_index = (self.current_frame_index + 1) % self.total_frames
            self.set_frame_by_index(next_index)

    def prev_frame(self):
        """Moves to the previous frame."""
        if self.total_frames > 0:
            next_index = self.current_frame_index - 1
            if next_index < 0:
                next_index = 0
            self.set_frame_by_index(next_index)

    def resizeEvent(self, event):
        """Handle window resize to rescale the image."""
        super().resizeEvent(event)
        if self.total_frames > 0 and self.current_frame_index != -1:
            # Re-set the frame to trigger rescaling
            # This is a simple way to force the pixmap to be recalculated
            idx = self.current_frame_index
            self.current_frame_index = -1 # Force update
            self.set_frame_by_index(idx)

