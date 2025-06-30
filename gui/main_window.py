import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QDockWidget, QListWidget, 
                             QListWidgetItem, QVBoxLayout, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt

# Ensure the sub-packages are found
from gui.video_player_widget import VideoPlayerWidget
from gui.annotation_widget import AnnotationWidget
from logic.data_handler import DataHandler

class MainWindow(QMainWindow):
    """
    The main window of the application.
    It orchestrates the file list, video player, and annotation widgets.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Annotation Tool")
        self.setGeometry(100, 100, 1280, 720)

        # 确定项目根目录以找到 'video' 和 'markout' 文件夹
        # 假设脚本从 'src' 目录内部运行。
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.video_base_dir = os.path.join(self.project_root, 'video')
        self.markout_dir = os.path.join(self.project_root, 'markout')
        
        # --- 业务逻辑处理器 ---
        self.data_handler = DataHandler(markout_dir=self.markout_dir, video_base_dir=self.video_base_dir)
        self.current_video_name = None

        # --- 主要控件 ---
        self.video_list_widget = QListWidget()
        self.video_player = VideoPlayerWidget()
        self.annotation_widget = AnnotationWidget()
        
        self.central_splitter = QSplitter(Qt.Horizontal)
        self.central_splitter.addWidget(self.video_player)
        self.central_splitter.addWidget(self.annotation_widget)
        self.central_splitter.setSizes([800, 480]) # 初始尺寸分布

        # --- 用于视频列表的 Dock 控件 ---
        self.video_list_dock = QDockWidget("Video Projects", self)
        self.video_list_dock.setWidget(self.video_list_widget)
        self.video_list_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.video_list_dock)

        self.setCentralWidget(self.central_splitter)

        # --- 连接 ---
        self.video_list_widget.currentItemChanged.connect(self.handle_video_selection_change)
        self.video_player.frameChanged.connect(self.annotation_widget.update_current_frame)
        self.annotation_widget.requestSave.connect(self.save_current_video_data)

        # --- 填充初始视频列表 ---
        self.populate_video_list()
        
    def populate_video_list(self):
        """扫描视频目录并填充列表控件。"""
        self.video_list_widget.clear()
        if not os.path.exists(self.video_base_dir):
            print(f"Video directory not found: {self.video_base_dir}")
            return
            
        for item in sorted(os.listdir(self.video_base_dir)):
            # 确保每个项目都是一个目录，并且包含一个名为 video.mp4 的文件
            project_path = os.path.join(self.video_base_dir, item)
            video_file_path = os.path.join(project_path, 'video.mp4')
            if os.path.isdir(project_path) and os.path.exists(video_file_path):
                list_item = QListWidgetItem(item)
                self.video_list_widget.addItem(list_item)

    def handle_video_selection_change(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        处理切换视频的逻辑。
        保存旧数据并加载新数据。
        """
        # 为先前选择的视频保存数据
        if previous is not None:
            self.save_video_data(previous.text())

        # 为新选择的视频加载数据
        if current is not None:
            self.current_video_name = current.text()
            self.load_video_data(self.current_video_name)
    
    def load_video_data(self, video_name: str):
        """加载视频的标注数据和对应的MP4文件。"""
        print(f"Loading data for: {video_name}")
        self.setWindowTitle(f"Video Annotation Tool - {video_name}")
        
        # 加载 JSON 数据
        data = self.data_handler.load_data(video_name)
        self.annotation_widget.load_data(data)
        
        # *** CHANGE HERE: Load mp4 file instead of image sequence ***
        video_file_path = os.path.join(self.video_base_dir, video_name, 'video.mp4')
        self.video_player.load_video(video_file_path)

    def save_current_video_data(self):
        """一个槽函数，用于保存当前活动视频的数据。"""
        if self.current_video_name:
            self.save_video_data(self.current_video_name)

    def save_video_data(self, video_name: str):
        """保存给定视频的标注。"""
        if not video_name:
            return
            
        print(f"Saving data for: {video_name}")
        
        # 从标注控件获取数据
        ui_data = self.annotation_widget.get_data()
        
        # 获取基础结构（包括像 relative_path 这样的元数据）
        full_data = self.data_handler.load_data(video_name) # 加载现有的以保留元数据
        
        # 用UI中的数据更新结构
        full_data['abolished'] = ui_data['abolished']
        # 重新构建标注列表以包含正确的 relative_path
        relative_path = full_data.get('relative_path')
        
        formatted_annotations = []
        for ann in ui_data['annotations']:
            formatted_annotations.append(
                self.data_handler.format_annotation(
                    ann['instruction'], ann['start'], ann['end']
                )
            )
            
        full_data['frame_num_total'] = self.video_player.total_frames
        full_data['annotations'] = formatted_annotations
        
        
        # 使用数据处理器保存
        self.data_handler.save_data(video_name, full_data)

    def closeEvent(self, event):
        """
        处理应用程序关闭事件以确保所有数据都已保存。
        """
        reply = QMessageBox.question(self, 'Exit Confirmation',
                                     "Are you sure you want to exit? Any unsaved changes for the current video will be saved.",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.save_current_video_data()
            self.video_player.cleanup() # 确保释放视频文件
            event.accept()
        else:
            event.ignore()

