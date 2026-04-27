"""
图像旋转节点 - 按指定角度旋转图像
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class RotateNode(AIBaseNode):
    """
    图像旋转节点
    
    按指定角度旋转图像，支持任意中心点和缩放比例
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像旋转'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(RotateNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('angle', '旋转角度(-180~180)', tab='properties')
        self.set_property('angle', '0')
        self.add_text_input('scale', '缩放比例(0.1-2.0)', tab='properties')
        self.set_property('scale', '1.0')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            angle = float(self.get_property('angle'))
            scale = float(self.get_property('scale'))
            
            h, w = image.shape[:2]
            center = (w / 2, h / 2)
            
            M = cv2.getRotationMatrix2D(center, angle, scale)
            
            abs_cos = abs(M[0, 0])
            abs_sin = abs(M[0, 1])
            new_w = int(h * abs_sin + w * abs_cos)
            new_h = int(h * abs_cos + w * abs_sin)
            
            M[0, 2] += new_w / 2 - center[0]
            M[1, 2] += new_h / 2 - center[1]
            
            rotated = cv2.warpAffine(image, M, (new_w, new_h))
            self.log_success(f"图像旋转完成 (角度: {angle}°, 缩放: {scale})")
            return {'输出图像': rotated}
            
        except Exception as e:
            self.log_error(f"图像旋转处理错误: {e}")
            return {'输出图像': None}
