"""
匹配定位节点包 - 模板匹配与特征点匹配
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class ContourAnalysisNode(BaseNode):
    """灰度匹配节点（基于轮廓）"""
    
    __identifier__ = 'match_location'
    NODE_NAME = '灰度匹配'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(ContourAnalysisNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            threshold_val = int(self.get_property('threshold'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result = image.copy()
            cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"灰度匹配错误: {e}")
            return {'输出图像': None}


class BoundingBoxNode(BaseNode):
    """相关性匹配节点（基于模板匹配）"""
    
    __identifier__ = 'match_location'
    NODE_NAME = '相关性匹配'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(BoundingBoxNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('template_path', '模板路径', tab='properties')
        self.add_text_input('threshold', '阈值(0-1)', tab='properties')
        self.set_property('threshold', '0.8')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            template_path = self.get_property('template_path')
            threshold_val = float(self.get_property('threshold'))
            
            if not template_path:
                return {'输出图像': image}
            
            template = cv2.imread(template_path)
            if template is None:
                return {'输出图像': image}
            
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
            
            result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            output = image.copy()
            h, w = gray_template.shape[:2]
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            
            if max_val >= threshold_val:
                cv2.rectangle(output, top_left, bottom_right, (0, 255, 0), 2)
            
            return {'输出图像': output}
        except Exception as e:
            self.log_error(f"相关性匹配错误: {e}")
            return {'输出图像': None}


class ShapeMatchNode(BaseNode):
    """形状匹配节点（基于Hu矩）"""
    
    __identifier__ = 'match_location'
    NODE_NAME = '形状匹配'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(ShapeMatchNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('template_path', '模板路径', tab='properties')
        self.add_text_input('method', '匹配方法', tab='properties')
        self.set_property('method', '1')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            template_path = self.get_property('template_path')
            method = int(self.get_property('method'))
            
            if not template_path:
                return {'输出图像': image}
            
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return {'输出图像': image}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            _, template_binary = cv2.threshold(template, 127, 255, cv2.THRESH_BINARY)
            template_contours, _ = cv2.findContours(template_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not template_contours:
                return {'输出图像': image}
            
            template_moment = cv2.moments(template_contours[0])
            template_hu = cv2.HuMoments(template_moment)
            
            result = image.copy()
            for contour in contours:
                moment = cv2.moments(contour)
                hu = cv2.HuMoments(moment)
                score = cv2.matchShapes(template_hu, hu, method, 0)
                
                if score < 0.1:  # 阈值
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"形状匹配错误: {e}")
            return {'输出图像': None}


# 导入迁移的模板节点
from .template_creator import TemplateCreatorNode
from .template_match import TemplateMatchNode
