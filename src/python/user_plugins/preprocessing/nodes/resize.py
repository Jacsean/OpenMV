"""
图像缩放节点 - 调整图像尺寸
"""

from ...base_nodes import AIBaseNode
import cv2
import numpy as np


class ResizeNode(AIBaseNode):
    """
    图像缩放节点
    
    调整图像尺寸，支持多种插值方法
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像缩放'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ResizeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('width', '目标宽度', tab='properties')
        self.set_property('width', '640')
        self.add_text_input('height', '目标高度', tab='properties')
        self.set_property('height', '480')
        self.add_combo_menu('interpolation', '插值方法', 
                           items=['INTER_NEAREST', 'INTER_LINEAR', 'INTER_CUBIC', 'INTER_AREA'],
                           tab='properties')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            width = int(self.get_property('width'))
            height = int(self.get_property('height'))
            interp_method = self.get_property('interpolation')
            
            interp_map = {
                'INTER_NEAREST': cv2.INTER_NEAREST,
                'INTER_LINEAR': cv2.INTER_LINEAR,
                'INTER_CUBIC': cv2.INTER_CUBIC,
                'INTER_AREA': cv2.INTER_AREA
            }
            interpolation = interp_map.get(interp_method, cv2.INTER_LINEAR)
            
            resized = cv2.resize(image, (width, height), interpolation=interpolation)
            self.log_success(f"图像缩放完成 ({width}x{height})")
            return {'输出图像': resized}
            
        except Exception as e:
            self.log_error(f"图像缩放处理错误: {e}")
            return {'输出图像': None}
