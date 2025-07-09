from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QTableWidget, QAbstractItemView, 
                             QTextEdit, QCheckBox, QHeaderView, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List, Dict, Any

class AnnotationWidget(QWidget):
    """
    一个用于管理视频标注的控件。
    允许设置开始/结束帧，编写说明，并将视频标记为废弃。
    """
    # 请求将当前状态保存到文件的信号
    requestSave = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame = 0
        self.start_frame = -1
        self.end_frame = -1

        # --- UI 元素 ---
        self.main_label = QLabel("Annotation Controls")
        self.main_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.current_frame_label = QLabel("Current Frame: 0")
        
        # 开始/结束帧控件
        self.start_frame_label = QLabel("Start: --")
        self.set_start_button = QPushButton("Set Start")
        self.end_frame_label = QLabel("End: --")
        self.set_end_button = QPushButton("Set End")

        # 指令输入
        self.instruction_label = QLabel("Instruction:")
        self.pre_instruction_menu = QComboBox()
        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText("Describe the action here, or select a pre-defined one.")
        
        # 操作按钮
        self.add_annotation_button = QPushButton("Add Annotation to List")
        self.delete_annotation_button = QPushButton("Delete Selected Annotation")

        # 标注表格
        self.annotations_table = QTableWidget()
        self.annotations_table.setColumnCount(3)
        self.annotations_table.setHorizontalHeaderLabels(["Start", "End", "Instruction"])
        self.annotations_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.annotations_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.annotations_table.verticalHeader().setVisible(False)
        self.annotations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.annotations_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)

        # 复选框
        self.abolish_checkbox = QCheckBox("Abolish")
        self.issue_checkbox = QCheckBox("Issue")
        
        # --- 布局 ---
        v_layout = QVBoxLayout()
        v_layout.addWidget(self.main_label)
        v_layout.addWidget(self.current_frame_label)
        
        start_end_layout = QHBoxLayout()
        start_end_layout.addWidget(self.start_frame_label)
        start_end_layout.addWidget(self.set_start_button)
        start_end_layout.addStretch()
        start_end_layout.addWidget(self.end_frame_label)
        start_end_layout.addWidget(self.set_end_button)
        v_layout.addLayout(start_end_layout)

        instruction_header_layout = QHBoxLayout()
        instruction_header_layout.addWidget(self.instruction_label)
        instruction_header_layout.addWidget(self.pre_instruction_menu)
        instruction_header_layout.addStretch()
        v_layout.addLayout(instruction_header_layout)
        
        v_layout.addWidget(self.instruction_input)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_annotation_button)
        button_layout.addWidget(self.delete_annotation_button)
        v_layout.addLayout(button_layout)
        
        v_layout.addWidget(QLabel("Current Annotations:"))
        v_layout.addWidget(self.annotations_table)
        
        problem_layout = QHBoxLayout()
        problem_layout.addStretch()
        problem_layout.addWidget(self.abolish_checkbox)
        problem_layout.addWidget(self.issue_checkbox)
        v_layout.addLayout(problem_layout)
        
        self.setLayout(v_layout)

        # --- 连接 ---
        self.set_start_button.clicked.connect(self.set_start)
        self.set_end_button.clicked.connect(self.set_end)
        self.add_annotation_button.clicked.connect(self.add_annotation)
        self.delete_annotation_button.clicked.connect(self.delete_selected_annotation)
        # 每当数据更改时发出保存请求
        self.pre_instruction_menu.activated.connect(self.on_pre_instruction_selected)
        self.abolish_checkbox.stateChanged.connect(self.requestSave.emit)
        self.issue_checkbox.stateChanged.connect(self.requestSave.emit)

    def on_pre_instruction_selected(self, index: int):
        """当用户从菜单中选择一项时，填充指令输入框。"""
        # 忽略索引为0的占位符
        if index > 0:
            self.instruction_input.setText(self.pre_instruction_menu.itemText(index))
            
    def update_current_frame(self, frame_number: int):
        """接收来自视频播放器的当前帧号的槽函数。"""
        self.current_frame = frame_number
        self.current_frame_label.setText(f"Current Frame: {frame_number}")

    def set_start(self):
        self.start_frame = self.current_frame
        self.start_frame_label.setText(f"Start: {self.start_frame}")

    def set_end(self):
        self.end_frame = self.current_frame
        self.end_frame_label.setText(f"End: {self.end_frame}")
    
    def add_annotation(self):
        """验证输入并将新标注添加到表格中。"""
        instruction = self.instruction_input.toPlainText().strip()

        # 验证
        if self.start_frame == -1 or self.end_frame == -1:
            QMessageBox.warning(self, "Input Error", "Please set both a start and end frame.")
            return
        if self.start_frame >= self.end_frame:
            QMessageBox.warning(self, "Input Error", "Start frame must be less than end frame.")
            return
        if not instruction:
            QMessageBox.warning(self, "Input Error", "Instruction field cannot be empty.")
            return

        # 添加到表格
        row_position = self.annotations_table.rowCount()
        self.annotations_table.insertRow(row_position)
        self.annotations_table.setItem(row_position, 0, QTableWidgetItem(str(self.start_frame)))
        self.annotations_table.setItem(row_position, 1, QTableWidgetItem(str(self.end_frame)))
        self.annotations_table.setItem(row_position, 2, QTableWidgetItem(instruction))

        # 为下一个标注重置
        self.clear_inputs()
        
        # 触发保存
        self.requestSave.emit()

    def delete_selected_annotation(self):
        """从标注表格中删除当前选定的行。"""
        selected_rows = self.annotations_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select an annotation to delete.")
            return
        
        # 获取第一个选定的行，因为我们处于单行选择模式
        self.annotations_table.removeRow(selected_rows[0].row())
        self.requestSave.emit()

    def clear_inputs(self):
        """为新的标注重置输入字段。"""
        self.start_frame = -1
        self.end_frame = -1
        self.start_frame_label.setText("Start: --")
        self.end_frame_label.setText("End: --")
        self.instruction_input.clear()
        self.pre_instruction_menu.setCurrentIndex(0) # 重置菜单

    def load_data(self, data: Dict[str, Any]):
        """使用从JSON文件加载的数据填充控件。"""
        self.clear_inputs()
        self.annotations_table.setRowCount(0)
        
        # NEW: 加载预设指令
        self.pre_instruction_menu.clear()
        self.pre_instruction_menu.addItem("Select pre-defined instruction...")
        pre_instructions = data.get('pre_instructions', [])
        self.pre_instruction_menu.addItems(pre_instructions)

        # NEW: 加载问题状态
        problem = data.get('problem', {'abolished': False, 'issue': False})
        self.abolish_checkbox.setChecked(problem.get('abolished', False))
        self.issue_checkbox.setChecked(problem.get('issue', False))
        
        annotations = data.get('annotations', [])
        for ann in annotations:
            row_position = self.annotations_table.rowCount()
            self.annotations_table.insertRow(row_position)
            self.annotations_table.setItem(row_position, 0, QTableWidgetItem(str(ann.get('start', ''))))
            self.annotations_table.setItem(row_position, 1, QTableWidgetItem(str(ann.get('end', ''))))
            self.annotations_table.setItem(row_position, 2, QTableWidgetItem(str(ann.get('instruction', ''))))

    def get_data(self) -> Dict[str, Any]:
        """从控件中检索所有当前的标注数据。"""
        annotations = []
        for row in range(self.annotations_table.rowCount()):
            annotations.append({
                "start": int(self.annotations_table.item(row, 0).text()),
                "end": int(self.annotations_table.item(row, 1).text()),
                "instruction": self.annotations_table.item(row, 2).text(),
            })
        
        # NEW: 返回新的数据结构
        return {
            "problem": {
                "abolished": self.abolish_checkbox.isChecked(),
                "issue": self.issue_checkbox.isChecked()
            },
            "annotations": annotations
        }
