"""
直方图均衡化节点 - 增强图像对比度
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class HistogramEqualizationNode(BaseNode):
    """
    直方图均衡化节点
    
    使用CLAHE（限制对比度自适应直方图均衡化）增强图像对比度，
    适用于低对比度图像的增强处理
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '直方图均衡化'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(HistogramEqualizationNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        self._param_container = ParameterContainerWidget(self.view, 'histogram_params', '')
        self.add_custom_widget(self._param_container, tab='properties')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                
                merged = cv2.merge((cl, a, b))
                result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                result = clahe.apply(image)
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
            self.log_success("直方图均衡化处理完成")
            return {'输出图像': result}
            
        except Exception as e:
            self.log_error(f"直方图均衡化处理错误: {e}")
            return {'输出图像': None}
