"""
Canny边缘检测节点 - 使用自定义参数容器控件
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
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

        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'canny_params', '')
        
        # 添加参数控件（使用自定义容器）
        self._param_container.add_spinbox('threshold1', '低阈值', value=50, min_value=0, max_value=255)
        self._param_container.add_spinbox('threshold2', '高阈值', value=150, min_value=0, max_value=255)
        
        # 设置值变化回调
        self._param_container.set_value_changed_callback(self._on_param_changed)
        
        # 添加到节点
        self.add_custom_widget(self._param_container, tab='properties')

    def _on_param_changed(self, name, value):
        """参数值变化回调"""
        self.set_property(name, str(value))

    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 从参数容器获取值
            params = self._param_container.get_values_dict()
            threshold1 = int(params.get('threshold1', 50))
            threshold2 = int(params.get('threshold2', 150))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, threshold1, threshold2)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': edges_bgr}
        except Exception as e:
            self.log_error(f"Canny边缘检测错误: {e}")
            return {'输出图像': None}