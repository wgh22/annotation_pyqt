import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """
    应用程序的主入口点。
    初始化 QApplication 和 MainWindow。
    """
    app = QApplication(sys.argv)
    
    # 应用一个简单的样式表以获得更好的外观
    app.setStyleSheet("""
        QWidget {
            font-size: 11pt;
        }
        QPushButton {
            padding: 8px;
            border-radius: 4px;
            background-color: #4a69bd;
            color: white;
            border: 1px solid #3c5aa6;
        }
        QPushButton:hover {
            background-color: #5d7dd2;
        }
        QPushButton:pressed {
            background-color: #3c5aa6;
        }
        QDockWidget {
            font-weight: bold;
        }
        QTableWidget {
            gridline-color: #e0e0e0;
        }
    """)

    main_window = MainWindow()
    app.installEventFilter(main_window)
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
