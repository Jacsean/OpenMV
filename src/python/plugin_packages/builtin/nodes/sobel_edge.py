"""
Sobel边缘检测节点 - 使用Sobel算子计算图像梯度
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class SobelEdgeNode(BaseNode):
    """Sobel边缘检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Sobel算子'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(SobelEdgeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_combo_menu('direction', '方向', items=['X方向', 'Y方向', 'XY方向'], tab='properties')
        self.add_text_input('ksize', '核大小(1-7,奇数)', tab='properties')
        self.set_property('ksize', '3')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            direction = self.get_property('direction')
            ksize = int(self.get_property('ksize'))
            
            if ksize < 1: ksize = 1
            elif ksize > 7: ksize = 7
            if ksize % 2 == 0: ksize += 1
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            if direction == 'X方向':
                sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
            elif direction == 'Y方向':
                sobel = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
            else:
                sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
                sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
                sobel = cv2.magnitude(sobel_x, sobel_y)
            
            sobel_abs = cv2.convertScaleAbs(sobel)
            sobel_bgr = cv2.cvtColor(sobel_abs, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': sobel_bgr}
        except Exception as e:
            self.log_error(f"Sobel边缘检测错误: {e}")
            return {'输出图像': None}
