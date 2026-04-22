"""
处理节点 - 图像处理算法节点
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class GrayscaleNode(BaseNode):
    """
    灰度化节点
    将彩色图像转换为灰度图像
    """
    
    __identifier__ = 'processing'
    NODE_NAME = '灰度化'
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # 转换回BGR格式以便显示
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
    
    __identifier__ = 'processing'
    NODE_NAME = '高斯模糊'
    
    def __init__(self):
        super(GaussianBlurNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_slider('kernel_size', '核大小', 3, 15, 5, tab='properties')
        self.add_slider('sigma_x', 'Sigma X', 0, 10, 0, tab='properties')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                kernel_size = int(self.get_property('kernel_size'))
                sigma_x = float(self.get_property('sigma_x'))
                
                # 确保核大小为奇数
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x)
                return {'输出图像': blurred}
            except Exception as e:
                print(f"高斯模糊处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class CannyEdgeNode(BaseNode):
    """
    Canny边缘检测节点
    使用Canny算法检测图像边缘
    """
    
    __identifier__ = 'processing'
    NODE_NAME = 'Canny边缘检测'
    
    def __init__(self):
        super(CannyEdgeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_slider('threshold1', '低阈值', 0, 255, 50, tab='properties')
        self.add_slider('threshold2', '高阈值', 0, 255, 150, tab='properties')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
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
                # 转换回BGR格式以便显示
                edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                return {'输出图像': edges_bgr}
            except Exception as e:
                print(f"Canny边缘检测错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class ThresholdNode(BaseNode):
    """
    二值化节点
    对图像进行阈值二值化处理
    """
    
    __identifier__ = 'processing'
    NODE_NAME = '二值化'
    
    def __init__(self):
        super(ThresholdNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_slider('threshold', '阈值', 0, 255, 127, tab='properties')
        self.add_combo_menu('type', '类型', items=['BINARY', 'BINARY_INV', 'TRUNC', 'TOZERO', 'TOZERO_INV'], tab='properties')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                threshold_val = int(self.get_property('threshold'))
                type_str = self.get_property('type')
                
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 映射类型字符串到OpenCV常量
                type_map = {
                    'BINARY': cv2.THRESH_BINARY,
                    'BINARY_INV': cv2.THRESH_BINARY_INV,
                    'TRUNC': cv2.THRESH_TRUNC,
                    'TOZERO': cv2.THRESH_TOZERO,
                    'TOZERO_INV': cv2.THRESH_TOZERO_INV
                }
                
                thresh_type = type_map.get(type_str, cv2.THRESH_BINARY)
                _, binary = cv2.threshold(gray, threshold_val, 255, thresh_type)
                
                # 转换回BGR格式以便显示
                binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
                return {'输出图像': binary_bgr}
            except Exception as e:
                print(f"二值化处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
