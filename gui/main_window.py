import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QDockWidget, QListWidget, 
                             QListWidgetItem, QVBoxLayout, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt

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

        # Determine project root to find 'video' and 'markout' folders
        # Assumes the script is run from inside the 'src' directory.
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.video_base_dir = os.path.join(self.project_root, 'video')
        self.markout_dir = os.path.join(self.project_root, 'markout')
        
        # --- Business Logic Handler ---
        self.data_handler = DataHandler(markout_dir=self.markout_dir, video_base_dir=self.video_base_dir)
        self.current_video_name = None

        # --- Main Widgets ---
        self.video_list_widget = QListWidget()
        self.video_player = VideoPlayerWidget()
        self.annotation_widget = AnnotationWidget()
        
        # --- Layout using QSplitter for resizable panels ---
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.central_splitter.addWidget(self.video_player)
        self.central_splitter.addWidget(self.annotation_widget)
        self.central_splitter.setSizes([800, 480]) # Initial size distribution

        # --- Dock Widget for Video List ---
        self.video_list_dock = QDockWidget("Video Projects", self)
        self.video_list_dock.setWidget(self.video_list_widget)
        self.video_list_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.video_list_dock)

        self.setCentralWidget(self.central_splitter)

        # --- Connections ---
        self.video_list_widget.currentItemChanged.connect(self.handle_video_selection_change)
        self.video_player.frameChanged.connect(self.annotation_widget.update_current_frame)
        self.annotation_widget.requestSave.connect(self.save_current_video_data)

        # --- Populate initial video list ---
        self.populate_video_list()
        
    def populate_video_list(self):
        """Scans the video directory and populates the list widget."""
        self.video_list_widget.clear()
        if not os.path.exists(self.video_base_dir):
            print(f"Video directory not found: {self.video_base_dir}")
            return
            
        for item in sorted(os.listdir(self.video_base_dir)):
            if os.path.isdir(os.path.join(self.video_base_dir, item)):
                list_item = QListWidgetItem(item)
                self.video_list_widget.addItem(list_item)

    def handle_video_selection_change(self, current: QListWidgetItem, previous: QListWidgetItem):
        """
        Handles the logic for switching between videos.
        Saves the old data and loads the new data.
        """
        # Save data for the previously selected video
        if previous is not None:
            self.save_video_data(previous.text())

        # Load data for the newly selected video
        if current is not None:
            self.current_video_name = current.text()
            self.load_video_data(self.current_video_name)
    
    def load_video_data(self, video_name: str):
        """Loads annotation data and the corresponding image sequence for a video."""
        print(f"Loading data for: {video_name}")
        self.setWindowTitle(f"Video Annotation Tool - {video_name}")
        
        # Load JSON data
        data = self.data_handler.load_data(video_name)
        self.annotation_widget.load_data(data)
        
        # Load image sequence
        img_folder_path = os.path.join(self.video_base_dir, video_name, 'img')
        self.video_player.load_image_sequence(img_folder_path)

    def save_current_video_data(self):
        """A slot that saves data for the currently active video."""
        if self.current_video_name:
            self.save_video_data(self.current_video_name)

    def save_video_data(self, video_name: str):
        """Saves the annotations for a given video."""
        if not video_name:
            return
            
        print(f"Saving data for: {video_name}")
        
        # Get data from the annotation widget
        ui_data = self.annotation_widget.get_data()
        
        # Get the base structure (which includes metadata like relative_path)
        full_data = self.data_handler.load_data(video_name) # Load existing to preserve metadata
        
        # Update the structure with data from UI
        full_data['abolished'] = ui_data['abolished']
        # Rebuild annotations list to include the correct relative_path
        relative_path = full_data.get('relative_path', self.data_handler._get_default_structure(video_name)['relative_path'])
        
        formatted_annotations = []
        for ann in ui_data['annotations']:
            formatted_annotations.append(
                self.data_handler.format_annotation(
                    ann['instruction'], ann['start'], ann['end']
                )
            )
        full_data['annotations'] = formatted_annotations
        
        # Save using data handler
        self.data_handler.save_data(video_name, full_data)

    def closeEvent(self, event):
        """
        Handles the application closing event to ensure all data is saved.
        """
        reply = QMessageBox.question(self, 'Exit Confirmation',
                                     "Are you sure you want to exit? Any unsaved changes for the current video will be saved.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.save_current_video_data()
            event.accept()
        else:
            event.ignore()

