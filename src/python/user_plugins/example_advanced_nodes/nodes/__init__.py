"""
高级节点示例包 - 多输入多输出、复杂参数处理
"""

from ...base_nodes import AIBaseNode
import cv2
import numpy as np


class MultiInputBlendNode(AIBaseNode):
    """多图像混合节点"""
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '多图像混合'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(MultiInputBlendNode, self).__init__()
        self.add_input('图像1', color=(100, 255, 100))
        self.add_input('图像2', color=(100, 255, 100))
        self.add_input('图像3', color=(100, 255, 100))
        self.add_input('图像4', color=(100, 255, 100))
        self.add_output('混合结果', color=(100, 255, 100))
        self.add_text_input('weight1', '权重1(0-1)', tab='properties')
        self.set_property('weight1', '0.25')
        self.add_text_input('weight2', '权重2(0-1)', tab='properties')
        self.set_property('weight2', '0.25')
        self.add_text_input('weight3', '权重3(0-1)', tab='properties')
        self.set_property('weight3', '0.25')
        self.add_text_input('weight4', '权重4(0-1)', tab='properties')
        self.set_property('weight4', '0.25')
    
    def process(self, inputs=None):
        try:
            images = []
            weights = [float(self.get_property(f'weight{i}')) for i in range(1, 5)]
            
            if inputs:
                for i, inp in enumerate(inputs[:4]):
                    if inp is not None and len(inp) > 0:
                        img = inp[0] if isinstance(inp, list) else inp
                        if img is not None:
                            images.append((img, weights[i]))
            
            if not images:
                return {'混合结果': None}
            
            # 归一化权重
            total_weight = sum(w for _, w in images)
            if total_weight == 0:
                return {'混合结果': images[0][0]}
            
            # 加权混合
            result = np.zeros_like(images[0][0], dtype=np.float64)
            for img, weight in images:
                result += img.astype(np.float64) * (weight / total_weight)
            
            return {'混合结果': result.astype(np.uint8)}
        except Exception as e:
            self.log_error(f"多图像混合错误: {e}")
            return {'混合结果': None}


class AdaptiveThresholdNode(AIBaseNode):
    """自适应阈值节点"""
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '自适应阈值'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(AdaptiveThresholdNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('block_size', '块大小(3-15)', tab='properties')
        self.set_property('block_size', '11')
        self.add_text_input('C', '常数C(-10~10)', tab='properties')
        self.set_property('C', '2')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            block_size = int(self.get_property('block_size'))
            C = int(self.get_property('C'))
            
            if block_size < 3: block_size = 3
            elif block_size > 15: block_size = 15
            if block_size % 2 == 0: block_size += 1
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, C)
            binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': binary_bgr}
        except Exception as e:
            self.log_error(f"自适应阈值错误: {e}")
            return {'输出图像': None}


class HistogramEqualizationNode(AIBaseNode):
    """直方图均衡化节点"""
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '直方图均衡化'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(HistogramEqualizationNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                merged = cv2.merge((cl, a, b))
                result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                result = clahe.apply(image)
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"直方图均衡化错误: {e}")
            return {'输出图像': None}
