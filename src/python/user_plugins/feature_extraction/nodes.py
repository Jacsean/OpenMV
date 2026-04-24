"""
特征提取节点包 - 边缘检测、Blob分析、几何匹配
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class CannyEdgeNode(BaseNode):
    """
    Canny边缘检测节点
    使用Canny算法检测图像边缘
    """
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Canny边缘检测'
    
    def __init__(self):
        super(CannyEdgeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('threshold1', '低阈值(0-255)', tab='properties')
        self.set_property('threshold1', '50')
        self.add_text_input('threshold2', '高阈值(0-255)', tab='properties')
        self.set_property('threshold2', '150')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                threshold1 = int(self.get_property('threshold1'))
                threshold2 = int(self.get_property('threshold2'))
                
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                    
                edges = cv2.Canny(gray, threshold1, threshold2)
                edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                return {'输出图像': edges_bgr}
            except Exception as e:
                print(f"Canny边缘检测错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
