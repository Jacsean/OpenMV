"""
Laplacian边缘检测、Harris角点检测、Hough直线检测、Hough圆检测节点
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class LaplacianNode(BaseNode):
    """Laplacian边缘检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Laplacian边缘检测'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(LaplacianNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('ksize', '核大小(1-7,奇数)', tab='properties')
        self.set_property('ksize', '1')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            ksize = int(self.get_property('ksize'))
            if ksize < 1: ksize = 1
            elif ksize > 7: ksize = 7
            if ksize % 2 == 0: ksize += 1
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize)
            laplacian_abs = cv2.convertScaleAbs(laplacian)
            laplacian_bgr = cv2.cvtColor(laplacian_abs, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': laplacian_bgr}
        except Exception as e:
            self.log_error(f"Laplacian边缘检测错误: {e}")
            return {'输出图像': None}


class HarrisCornerNode(BaseNode):
    """Harris角点检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Harris角点检测'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(HarrisCornerNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('block_size', '邻域大小(2-10)', tab='properties')
        self.set_property('block_size', '2')
        self.add_text_input('ksize', 'Sobel核大小(1-7)', tab='properties')
        self.set_property('ksize', '3')
        self.add_text_input('k', 'Harris参数(0.04-0.06)', tab='properties')
        self.set_property('k', '0.04')
        self.add_text_input('threshold', '阈值(0.001-0.01)', tab='properties')
        self.set_property('threshold', '0.01')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            block_size = int(self.get_property('block_size'))
            ksize = int(self.get_property('ksize'))
            k = float(self.get_property('k'))
            threshold = float(self.get_property('threshold'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray = np.float32(gray)
            dst = cv2.cornerHarris(gray, block_size, ksize, k)
            
            result = image.copy()
            result[dst > threshold * dst.max()] = [0, 0, 255]
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Harris角点检测错误: {e}")
            return {'输出图像': None}


class HoughLinesNode(BaseNode):
    """Hough直线检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Hough直线检测'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(HoughLinesNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('rho', '距离精度(像素)', tab='properties')
        self.set_property('rho', '1')
        self.add_text_input('theta', '角度精度(弧度)', tab='properties')
        self.set_property('theta', '0.0174533')
        self.add_text_input('threshold', '最小投票数', tab='properties')
        self.set_property('threshold', '50')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            rho = float(self.get_property('rho'))
            theta = float(self.get_property('theta'))
            threshold = int(self.get_property('threshold'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLines(edges, rho, theta, threshold)
            
            result = image.copy()
            if lines is not None:
                for line in lines:
                    rho_val, theta_val = line[0]
                    a = np.cos(theta_val)
                    b = np.sin(theta_val)
                    x0 = a * rho_val
                    y0 = b * rho_val
                    x1 = int(x0 + 1000 * (-b))
                    y1 = int(y0 + 1000 * (a))
                    x2 = int(x0 - 1000 * (-b))
                    y2 = int(y0 - 1000 * (a))
                    cv2.line(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Hough直线检测错误: {e}")
            return {'输出图像': None}


class HoughCirclesNode(BaseNode):
    """Hough圆检测节点"""
    
    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Hough圆检测'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(HoughCirclesNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('dp', '累加器分辨率(1-2)', tab='properties')
        self.set_property('dp', '1')
        self.add_text_input('min_dist', '最小圆心距离', tab='properties')
        self.set_property('min_dist', '20')
        self.add_text_input('param1', 'Canny高阈值', tab='properties')
        self.set_property('param1', '100')
        self.add_text_input('param2', '圆心检测阈值', tab='properties')
        self.set_property('param2', '30')
        self.add_text_input('min_radius', '最小半径', tab='properties')
        self.set_property('min_radius', '0')
        self.add_text_input('max_radius', '最大半径', tab='properties')
        self.set_property('max_radius', '0')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            dp = int(self.get_property('dp'))
            min_dist = int(self.get_property('min_dist'))
            param1 = int(self.get_property('param1'))
            param2 = int(self.get_property('param2'))
            min_radius = int(self.get_property('min_radius'))
            max_radius = int(self.get_property('max_radius'))
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp, min_dist,
                                      param1=param1, param2=param2,
                                      minRadius=min_radius, maxRadius=max_radius)
            
            result = image.copy()
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for circle in circles[0, :]:
                    center = (circle[0], circle[1])
                    radius = circle[2]
                    cv2.circle(result, center, 1, (0, 100, 100), 3)
                    cv2.circle(result, center, radius, (255, 0, 255), 2)
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Hough圆检测错误: {e}")
            return {'输出图像': None}
