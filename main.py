import os
import sys
from PyQt5.QtWidgets import QApplication
import argparse
# Make sure Python can find the gui and logic sub-packages
from gui.main_window import MainWindow
from preprocess.preprocess import process_all_bag_files

def main():
    
    BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    BAG_DATA_DIR = os.path.join(BASE_DIR, 'bagdata')
    VIDEO_DIR    = os.path.join(BASE_DIR, 'video')
    MARKOUT_DIR  = os.path.join(BASE_DIR, 'markout')
    # --- Argument Parser ---
    parser = argparse.ArgumentParser(
        description="Rosbag Video Annotation Tool. Preprocesses bag files and launches a GUI for annotation."
    )
    parser.add_argument(
        '--skip-preprocess', 
        action='store_true',
        help="Skip the preprocessing step and directly launch the GUI."
    )
    args = parser.parse_args()
    
    # --- Step 1: Preprocessing (unless skipped) ---
    if not args.skip_preprocess:
        print("--- Starting Preprocessing Step ---")
        try:
            process_all_bag_files(BAG_DATA_DIR, VIDEO_DIR)
            print("--- Preprocessing Finished Successfully ---")
        except Exception as e:
            print(f"An error occurred during preprocessing: {e}")
            return
    else:
        print("--- Preprocessing Skipped ---")
    
    # --- Create necessary directories if they don't exist ---
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(MARKOUT_DIR, exist_ok=True)
    
    # --- Step 2: Launch GUI Application ---
    print("--- Launching Annotation GUI ---")
    """
    应用程序的主入口点。
    初始化 QApplication 和 MainWindow。
    """
    # app = QApplication(sys.argv)
    
    # # 应用一个简单的样式表以获得更好的外观
    # app.setStyleSheet("""
    #     QWidget {
    #         font-size: 11pt;
    #     }
    #     QPushButton {
    #         padding: 8px;
    #         border-radius: 4px;
    #         background-color: #4a69bd;
    #         color: white;
    #         border: 1px solid #3c5aa6;
    #     }
    #     QPushButton:hover {
    #         background-color: #5d7dd2;
    #     }
    #     QPushButton:pressed {
    #         background-color: #3c5aa6;
    #     }
    #     QDockWidget {
    #         font-weight: bold;
    #     }
    #     QTableWidget {
    #         gridline-color: #e0e0e0;
    #     }
    # """)

    # main_window = MainWindow()
    # main_window.show()
    # sys.exit(app.exec_())

if __name__ == '__main__':
    main()
