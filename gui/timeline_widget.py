from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QRect

class AnnotationTimelineWidget(QWidget):
    """
    一个自定义控件，用于在时间轴上可视化地显示标注片段。
    """
    # UPDATED: The signal now also emits the instruction string.
    segmentClicked = pyqtSignal(int, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(25)
        self.setToolTip("Click on a segment to play it back.")
        self.annotations = []
        self.total_frames = 0
        self._segment_rects = [] # 存储每个片段的矩形区域，用于点击检测
        self.selected_annotation = None

    def set_data(self, annotations: list, total_frames: int):
        """
        设置要在时间轴上显示的数据。
        """
        self.annotations = annotations
        self.total_frames = total_frames
        self.selected_annotation = None
        self.update() # 触发重绘事件

    def paintEvent(self, event):
        """
        绘制控件的UI。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor("#dfe6e9"))

        if self.total_frames == 0:
            return

        self._segment_rects.clear()
        widget_width = self.width()

        # 绘制所有标注片段
        for i, ann in enumerate(self.annotations):
            start = ann.get('start', 0)
            end = ann.get('end', 0)

            # 计算片段在时间轴上的 x 坐标和宽度
            x_start = (start / self.total_frames) * widget_width
            x_end = (end / self.total_frames) * widget_width
            
           
            if self.selected_annotation and self.selected_annotation == ann:
                color = QColor("#f1c40f") 
            else:
                color = QColor(52,152,219,100)
            segment_rect = QRect(int(x_start), 2, int(x_end - x_start), self.height() - 4)
            self._segment_rects.append((segment_rect, ann))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(segment_rect, 3, 3)

    def mousePressEvent(self, event):
        """
        处理鼠标点击事件。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            for rect, ann in self._segment_rects:
                if rect.contains(event.pos()):
                    instruction = ann.get('instruction', 'No instruction found.')
                    self.segmentClicked.emit(ann['start'], ann['end'], instruction)
                    self.selected_annotation = ann
                    self.update()  # 触发重绘以显示选中状态
                    break
