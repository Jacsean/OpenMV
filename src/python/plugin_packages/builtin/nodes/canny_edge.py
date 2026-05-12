"""
Canny边缘检测节点 - 使用QDial控件（水平布局）
"""

from Qt.QtWidgets import QWidget
from shared_libs.node_base import BaseNode
import cv2
import numpy as np
from PySide2.QtWidgets import QDial, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtCore import Qt
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget


class NodeDialPairWidget(NodeBaseWidget):
    """
    将两个 QDial 水平排列包装为 NodeGraphQt 兼容的自定义控件
    """
    
    def __init__(self, parent=None, name='', label=''):
        super(NodeDialPairWidget, self).__init__(parent, name, label)
        
        # 创建主容器
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")  # 设置容器背景透明
        main_layout = QHBoxLayout(container)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # === 第一个 QDial（低阈值）===
        threshold1_group = QWidget()
        layout1 = QVBoxLayout(threshold1_group)
        
        self.label1 = QLabel('低阈值')
        self.label1.setAlignment(Qt.AlignCenter)
        self.label1.setStyleSheet("font-size: 10px; color: #aaa;")
        layout1.addWidget(self.label1)
        
        self._dial1 = QDial()
        self._dial1.setRange(0, 255)
        self._dial1.setValue(50)
        self._dial1.setSingleStep(5)
        self._dial1.setNotchesVisible(True)
        self._dial1.setFixedSize(50, 50)  # 设置固定大小
        layout1.addWidget(self._dial1, alignment=Qt.AlignCenter)
        
        self.value_label1 = QLabel('50')
        self.value_label1.setAlignment(Qt.AlignCenter)
        self.value_label1.setStyleSheet("font-size: 10px; font-weight: bold; color: #4CAF50;")
        layout1.addWidget(self.value_label1)
        
        main_layout.addWidget(threshold1_group)
        
        # === 第二个 QDial（高阈值）===
        threshold2_group = QWidget()
        layout2 = QVBoxLayout(threshold2_group)
        
        self.label2 = QLabel('高阈值')
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet("font-size: 10px; color: #aaa;")
        layout2.addWidget(self.label2)
        
        self._dial2 = QDial()
        self._dial2.setRange(0, 255)
        self._dial2.setValue(150)
        self._dial2.setSingleStep(5)
        self._dial2.setNotchesVisible(True)
        self._dial1.setFixedSize(50, 50)  # 设置固定大小
        layout2.addWidget(self._dial2, alignment=Qt.AlignCenter)
        
        self.value_label2 = QLabel('150')
        self.value_label2.setAlignment(Qt.AlignCenter)
        self.value_label2.setStyleSheet("font-size: 10px; font-weight: bold; color: #2196F3;")
        layout2.addWidget(self.value_label2)
        
        main_layout.addWidget(threshold2_group)
        
        # 连接信号
        self._dial1.valueChanged.connect(self.on_dial1_changed)
        self._dial2.valueChanged.connect(self.on_dial2_changed)
        
        # 设置到自定义控件
        self.set_custom_widget(container)
    
    def on_dial1_changed(self, value):
        """低阈值变化时更新显示和属性"""
        self.value_label1.setText(str(value))
        # 通过 node 属性更新节点属性
        if self._node:
            self._node.set_property('threshold1', str(value))
    
    def on_dial2_changed(self, value):
        """高阈值变化时更新显示和属性"""
        self.value_label2.setText(str(value))
        # 通过 node 属性更新节点属性
        if self._node:
            self._node.set_property('threshold2', str(value))
    
    def get_value(self):
        """返回当前值（返回字典格式包含两个阈值）"""
        return {
            'threshold1': str(self._dial1.value()),
            'threshold2': str(self._dial2.value())
        }
    
    def set_value(self, value):
        """设置值"""
        if isinstance(value, dict):
            if 'threshold1' in value:
                self._dial1.setValue(int(value['threshold1']))
            if 'threshold2' in value:
                self._dial2.setValue(int(value['threshold2']))


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

        # 创建并添加水平排列的双旋钮控件
        dial_pair_widget = NodeDialPairWidget(self.view, 'canny_thresholds', '阈值设置')
        self.add_custom_widget(dial_pair_widget, tab='properties')
        
        # 初始化属性（用于 process 方法读取）
        self.create_property('threshold1', '50', tab='properties')
        self.create_property('threshold2', '150', tab='properties')

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
