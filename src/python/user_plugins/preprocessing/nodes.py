"""
预处理节点包 - 滤波、色彩转换、变换、校准
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class GrayscaleNode(BaseNode):
    """
    灰度化节点
    将彩色图像转换为灰度图像
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '灰度化'
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                return {'输出图像': gray_bgr}
            except Exception as e:
                print(f"灰度化处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class GaussianBlurNode(BaseNode):
    """
    高斯模糊节点
    对图像进行高斯模糊处理
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '高斯模糊'
    
    def __init__(self):
        super(GaussianBlurNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('kernel_size', '核大小(3-15,奇数)', tab='properties')
        self.set_property('kernel_size', '5')
        self.add_text_input('sigma_x', 'Sigma X(0-10)', tab='properties')
        self.set_property('sigma_x', '0')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                kernel_size = int(self.get_property('kernel_size'))
                sigma_x = float(self.get_property('sigma_x'))
                
                # 确保核大小为奇数且在有效范围内
                if kernel_size < 3:
                    kernel_size = 3
                elif kernel_size > 15:
                    kernel_size = 15
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x)
                return {'输出图像': blurred}
            except Exception as e:
                print(f"高斯模糊处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
