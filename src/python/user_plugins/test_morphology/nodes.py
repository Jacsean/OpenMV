"""
测试用形态学操作节点
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class DilateNode(BaseNode):
    """膨胀节点"""
    __identifier__ = 'morphology'
    NODE_NAME = '膨胀'
    
    def __init__(self):
        super(DilateNode, self).__init__()
        self.add_input('输入图像')
        self.add_output('输出图像')
        self.add_text_input('kernel_size', '核大小', tab='properties')
    
    def process(self, inputs=None):
        if inputs and len(inputs) > 0:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            kernel_size = int(self.get_property('kernel_size') or 3)
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            result = cv2.dilate(image, kernel, iterations=1)
            return {'输出图像': result}
        return {'输出图像': None}


class ErodeNode(BaseNode):
    """腐蚀节点"""
    __identifier__ = 'morphology'
    NODE_NAME = '腐蚀'
    
    def __init__(self):
        super(ErodeNode, self).__init__()
        self.add_input('输入图像')
        self.add_output('输出图像')
        self.add_text_input('kernel_size', '核大小', tab='properties')
    
    def process(self, inputs=None):
        if inputs and len(inputs) > 0:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            kernel_size = int(self.get_property('kernel_size') or 3)
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            result = cv2.erode(image, kernel, iterations=1)
            return {'输出图像': result}
        return {'输出图像': None}
