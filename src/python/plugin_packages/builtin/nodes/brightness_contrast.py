"""
亮度对比度调整节点 - 调整图像的亮度和对比度
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class BrightnessContrastNode(BaseNode):
    """
    亮度对比度调整节点
    
    调整图像的亮度和对比度，支持线性变换
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '亮度对比度'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(BrightnessContrastNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('alpha', '对比度(0.5-3.0)', tab='properties')
        self.set_property('alpha', '1.0')
        self.add_text_input('beta', '亮度(-100~100)', tab='properties')
        self.set_property('beta', '0')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            alpha = float(self.get_property('alpha'))
            beta = float(self.get_property('beta'))
            
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            self.log_success(f"亮度对比度调整完成 (对比度: {alpha}, 亮度: {beta})")
            return {'输出图像': adjusted}
            
        except Exception as e:
            self.log_error(f"亮度对比度调整错误: {e}")
            return {'输出图像': None}
