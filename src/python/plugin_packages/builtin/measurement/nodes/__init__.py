"""
测量节点包 - 轮廓分析与尺寸测量
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class ContourAnalysisNode(BaseNode):
    """轮廓分析节点"""
    
    __identifier__ = 'measurement'
    NODE_NAME = '轮廓分析'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(ContourAnalysisNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('轮廓数据', color=(255, 200, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None, '轮廓数据': '无输入'}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            threshold_val = int(self.get_property('threshold'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result = image.copy()
            cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
            contour_info = f"检测到 {len(contours)} 个轮廓"
            
            return {'输出图像': result, '轮廓数据': contour_info}
        except Exception as e:
            self.log_error(f"轮廓分析错误: {e}")
            return {'输出图像': None, '轮廓数据': '错误'}


class BoundingBoxNode(BaseNode):
    """边界框检测节点"""
    
    __identifier__ = 'measurement'
    NODE_NAME = '边界框检测'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(BoundingBoxNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('边界框数据', color=(255, 200, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None, '边界框数据': '无输入'}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            threshold_val = int(self.get_property('threshold'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result = image.copy()
            bbox_data = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
                bbox_data.append(f"({x},{y}) {w}x{h}")
            
            bbox_info = f"检测到 {len(bbox_data)} 个边界框"
            return {'输出图像': result, '边界框数据': bbox_info}
        except Exception as e:
            self.log_error(f"边界框检测错误: {e}")
            return {'输出图像': None, '边界框数据': '错误'}
