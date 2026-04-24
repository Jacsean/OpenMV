"""
测量分析节点包 - 尺寸、位置角度、轮廓分析
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class ContourAnalysisNode(BaseNode):
    """
    轮廓分析节点
    检测并分析图像中的轮廓信息
    """
    
    __identifier__ = 'measurement'
    NODE_NAME = '轮廓分析'
    
    def __init__(self):
        super(ContourAnalysisNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('轮廓数据', color=(255, 200, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                threshold_val = int(self.get_property('threshold'))
                
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 二值化
                _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
                
                # 查找轮廓
                contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 绘制轮廓
                result = image.copy()
                cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
                
                # 输出轮廓数量信息
                contour_info = f"检测到 {len(contours)} 个轮廓"
                
                return {'输出图像': result, '轮廓数据': contour_info}
            except Exception as e:
                print(f"轮廓分析错误: {e}")
                return {'输出图像': None, '轮廓数据': '错误'}
        return {'输出图像': None, '轮廓数据': '无输入'}


class BoundingBoxNode(BaseNode):
    """
    边界框检测节点
    检测物体的最小外接矩形
    """
    
    __identifier__ = 'measurement'
    NODE_NAME = '边界框检测'
    
    def __init__(self):
        super(BoundingBoxNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('边界框数据', color=(255, 200, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                threshold_val = int(self.get_property('threshold'))
                
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 二值化
                _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
                
                # 查找轮廓
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 绘制边界框
                result = image.copy()
                bbox_data = []
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    bbox_data.append(f"({x},{y}) {w}x{h}")
                
                bbox_info = f"检测到 {len(bbox_data)} 个边界框"
                
                return {'输出图像': result, '边界框数据': bbox_info}
            except Exception as e:
                print(f"边界框检测错误: {e}")
                return {'输出图像': None, '边界框数据': '错误'}
        return {'输出图像': None, '边界框数据': '无输入'}
