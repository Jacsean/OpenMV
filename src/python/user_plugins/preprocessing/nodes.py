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


class MedianBlurNode(BaseNode):
    """
    中值滤波节点
    使用中值滤波器去除噪声，特别适合椒盐噪声
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '中值滤波'
    
    def __init__(self):
        super(MedianBlurNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('ksize', '核大小(3-9,奇数)', tab='properties')
        self.set_property('ksize', '5')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                ksize = int(self.get_property('ksize'))
                
                # 确保核大小为奇数且在有效范围内
                if ksize < 3:
                    ksize = 3
                elif ksize > 9:
                    ksize = 9
                if ksize % 2 == 0:
                    ksize += 1
                
                blurred = cv2.medianBlur(image, ksize)
                return {'输出图像': blurred}
            except Exception as e:
                print(f"中值滤波处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class BilateralFilterNode(BaseNode):
    """
    双边滤波节点
    保边去噪滤波器，在平滑的同时保持边缘清晰
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '双边滤波'
    
    def __init__(self):
        super(BilateralFilterNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('d', '邻域直径(5-15)', tab='properties')
        self.set_property('d', '9')
        self.add_text_input('sigma_color', '颜色标准差(50-150)', tab='properties')
        self.set_property('sigma_color', '75')
        self.add_text_input('sigma_space', '空间标准差(50-150)', tab='properties')
        self.set_property('sigma_space', '75')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                d = int(self.get_property('d'))
                sigma_color = float(self.get_property('sigma_color'))
                sigma_space = float(self.get_property('sigma_space'))
                
                filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
                return {'输出图像': filtered}
            except Exception as e:
                print(f"双边滤波处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class ResizeNode(BaseNode):
    """
    图像缩放节点
    调整图像尺寸，支持多种插值方法
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像缩放'
    
    def __init__(self):
        super(ResizeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('width', '目标宽度', tab='properties')
        self.set_property('width', '640')
        self.add_text_input('height', '目标高度', tab='properties')
        self.set_property('height', '480')
        self.add_combo_menu('interpolation', '插值方法', 
                           items=['INTER_NEAREST', 'INTER_LINEAR', 'INTER_CUBIC', 'INTER_AREA'],
                           tab='properties')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                width = int(self.get_property('width'))
                height = int(self.get_property('height'))
                interp_method = self.get_property('interpolation')
                
                # 选择插值方法
                interp_map = {
                    'INTER_NEAREST': cv2.INTER_NEAREST,
                    'INTER_LINEAR': cv2.INTER_LINEAR,
                    'INTER_CUBIC': cv2.INTER_CUBIC,
                    'INTER_AREA': cv2.INTER_AREA
                }
                interpolation = interp_map.get(interp_method, cv2.INTER_LINEAR)
                
                resized = cv2.resize(image, (width, height), interpolation=interpolation)
                return {'输出图像': resized}
            except Exception as e:
                print(f"图像缩放处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class RotateNode(BaseNode):
    """
    图像旋转节点
    按指定角度旋转图像
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像旋转'
    
    def __init__(self):
        super(RotateNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('angle', '旋转角度(-180~180)', tab='properties')
        self.set_property('angle', '0')
        self.add_text_input('scale', '缩放比例(0.1-2.0)', tab='properties')
        self.set_property('scale', '1.0')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                angle = float(self.get_property('angle'))
                scale = float(self.get_property('scale'))
                
                h, w = image.shape[:2]
                center = (w / 2, h / 2)
                
                # 获取旋转矩阵
                M = cv2.getRotationMatrix2D(center, angle, scale)
                
                # 计算新图像尺寸
                abs_cos = abs(M[0, 0])
                abs_sin = abs(M[0, 1])
                new_w = int(h * abs_sin + w * abs_cos)
                new_h = int(h * abs_cos + w * abs_sin)
                
                # 调整旋转矩阵的平移分量
                M[0, 2] += new_w / 2 - center[0]
                M[1, 2] += new_h / 2 - center[1]
                
                rotated = cv2.warpAffine(image, M, (new_w, new_h))
                return {'输出图像': rotated}
            except Exception as e:
                print(f"图像旋转处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class BrightnessContrastNode(BaseNode):
    """
    亮度对比度调整节点
    调整图像的亮度和对比度
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '亮度对比度'
    
    def __init__(self):
        super(BrightnessContrastNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('alpha', '对比度(0.5-3.0)', tab='properties')
        self.set_property('alpha', '1.0')
        self.add_text_input('beta', '亮度(-100~100)', tab='properties')
        self.set_property('beta', '0')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                alpha = float(self.get_property('alpha'))
                beta = float(self.get_property('beta'))
                
                adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
                return {'输出图像': adjusted}
            except Exception as e:
                print(f"亮度对比度调整错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class ThresholdNode(BaseNode):
    """
    阈值二值化节点
    将图像转换为二值图像
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '阈值二值化'
    
    def __init__(self):
        super(ThresholdNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        self.set_property('threshold', '127')
        self.add_text_input('maxval', '最大值(0-255)', tab='properties')
        self.set_property('maxval', '255')
        self.add_combo_menu('type', '阈值类型',
                           items=['THRESH_BINARY', 'THRESH_BINARY_INV', 'THRESH_TRUNC', 'THRESH_TOZERO'],
                           tab='properties')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                threshold = float(self.get_property('threshold'))
                maxval = float(self.get_property('maxval'))
                thresh_type = self.get_property('type')
                
                # 如果是彩色图像，先转换为灰度
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 选择阈值类型
                type_map = {
                    'THRESH_BINARY': cv2.THRESH_BINARY,
                    'THRESH_BINARY_INV': cv2.THRESH_BINARY_INV,
                    'THRESH_TRUNC': cv2.THRESH_TRUNC,
                    'THRESH_TOZERO': cv2.THRESH_TOZERO
                }
                thresh_method = type_map.get(thresh_type, cv2.THRESH_BINARY)
                
                _, binary = cv2.threshold(gray, threshold, maxval, thresh_method)
                # 转换回BGR格式以便显示
                binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
                
                return {'输出图像': binary_bgr}
            except Exception as e:
                print(f"阈值二值化处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}