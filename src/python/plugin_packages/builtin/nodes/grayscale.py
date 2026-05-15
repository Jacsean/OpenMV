"""
灰度化节点 - 将彩色图像转换为灰度图像
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class GrayscaleNode(BaseNode):
    """
    灰度化节点
    
    将彩色图像转换为灰度图像，支持多种转换公式（BT.601、BT.709等）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '灰度化'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        self._param_container = ParameterContainerWidget(self.view, 'grayscale_params', '')
        self.add_custom_widget(self._param_container, tab='properties')
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含输出图像的字典
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            self.log_success("灰度化完成")
            return {'输出图像': gray_bgr}
            
        except Exception as e:
            self.log_error(f"灰度化处理错误: {e}")
            return {'输出图像': None}
