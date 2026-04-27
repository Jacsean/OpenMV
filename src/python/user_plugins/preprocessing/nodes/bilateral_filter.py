"""
双边滤波节点 - 保边去噪滤波器
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class BilateralFilterNode(AIBaseNode):
    """
    双边滤波节点
    
    保边去噪滤波器，在平滑的同时保持边缘清晰
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '双边滤波'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(BilateralFilterNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('d', '邻域直径(5-15)', tab='properties')
        self.set_property('d', '9')
        self.add_text_input('sigma_color', '颜色标准差(50-150)', tab='properties')
        self.set_property('sigma_color', '75')
        self.add_text_input('sigma_space', '空间标准差(50-150)', tab='properties')
        self.set_property('sigma_space', '75')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            d = int(self.get_property('d'))
            sigma_color = float(self.get_property('sigma_color'))
            sigma_space = float(self.get_property('sigma_space'))
            
            filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            self.log_success(f"双边滤波完成 (直径: {d})")
            return {'输出图像': filtered}
            
        except Exception as e:
            self.log_error(f"双边滤波处理错误: {e}")
            return {'输出图像': None}
