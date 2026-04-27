"""
中值滤波节点 - 使用中值滤波器去除噪声
"""

from ...base_nodes import AIBaseNode
import cv2
import numpy as np


class MedianBlurNode(AIBaseNode):
    """
    中值滤波节点
    
    使用中值滤波器去除噪声，特别适合椒盐噪声处理
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '中值滤波'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(MedianBlurNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('ksize', '核大小(3-9,奇数)', tab='properties')
        self.set_property('ksize', '5')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            ksize = int(self.get_property('ksize'))
            
            if ksize < 3:
                ksize = 3
            elif ksize > 9:
                ksize = 9
            if ksize % 2 == 0:
                ksize += 1
            
            blurred = cv2.medianBlur(image, ksize)
            self.log_success(f"中值滤波完成 (核大小: {ksize})")
            return {'输出图像': blurred}
            
        except Exception as e:
            self.log_error(f"中值滤波处理错误: {e}")
            return {'输出图像': None}
