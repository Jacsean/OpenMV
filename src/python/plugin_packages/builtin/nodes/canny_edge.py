"""
Canny边缘检测节点 - 使用Canny算法检测图像边缘
"""

# from Qt.QtWidgets import QWidget
from shared_libs.node_base import BaseNode
from PySide2.QtWidgets import QDial, QVBoxLayout, QWidget    # 导入 QDial 和 QVBoxLayout 控件
import cv2
import numpy as np


class CannyEdgeNode(BaseNode):
    """Canny边缘检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Canny算子'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(CannyEdgeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        dial = QDial()
        dial.setRange(0, 255)
        dial.setSingleStep(50)
        dial.valueChanged.connect(self.value_changed)
        # dial.sliderMoved.connect(self.dial_position)
        # dial.sliderPressed.connect(self.dial_pressed)
        # dial.sliderReleased.connect(self.dial_released)
        container=QWidget()
        layout=QVBoxLayout(container)
        layout.addWidget(dial)
        self.add_custom_widget(container)

        self.add_text_input('threshold1', '低阈值(0-255)', tab='properties')
        self.set_property('threshold1', '50')
        self.add_text_input('threshold2', '高阈值(0-255)', tab='properties')
        self.set_property('threshold2', '150')

    def value_changed(self, value):
        self.set_property('threshold1', str(value))

    # def dial_position(self, position):
    #     self.set_property('threshold1', str(value))

    # def dial_pressed(self):
    #     self.set_property('threshold1', str(value))

    # def dial_released(self):
    #     self.set_property('threshold1', str(value))
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            threshold1 = int(self.get_property('threshold1'))
            threshold2 = int(self.get_property('threshold2'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, threshold1, threshold2)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': edges_bgr}
        except Exception as e:
            self.log_error(f"Canny边缘检测错误: {e}")
            return {'输出图像': None}
