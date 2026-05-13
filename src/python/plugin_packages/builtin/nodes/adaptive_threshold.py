"""
自适应阈值节点 - 根据局部区域自动调整二值化阈值
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class AdaptiveThresholdNode(BaseNode):
    """
    自适应阈值节点
    
    根据局部区域自动调整二值化阈值，适用于光照不均匀的图像
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '自适应阈值'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(AdaptiveThresholdNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_spinbox('block_size', '块大小', value=11, min_value=3, max_value=15, tab='properties')
        self.add_spinbox('C', '常数C', value=2, min_value=-10, max_value=10, tab='properties')
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            block_size = int(self.get_property('block_size'))
            C = int(self.get_property('C'))
            
            # 参数验证和修正
            if block_size < 3:
                block_size = 3
            elif block_size > 15:
                block_size = 15
            if block_size % 2 == 0:
                block_size += 1
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # 执行自适应阈值处理
            binary = cv2.adaptiveThreshold(
                gray, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                block_size, 
                C
            )
            binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            self.log_success(f"自适应阈值处理完成 (块大小: {block_size}, C: {C})")
            return {'输出图像': binary_bgr}
            
        except Exception as e:
            self.log_error(f"自适应阈值处理错误: {e}")
            return {'输出图像': None}
