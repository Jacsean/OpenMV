"""
灰度化节点 - 将彩色图像转换为灰度图像
"""

from ...base_nodes import AIBaseNode
import cv2
import numpy as np


class GrayscaleNode(AIBaseNode):
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
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含输出图像的字典
        """
        try:
            # Step 1: 获取输入图像
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            # Step 2: 执行灰度化转换
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Step 3: 转换回 BGR 格式以便显示
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            self.log_success("灰度化完成")
            return {'输出图像': gray_bgr}
            
        except Exception as e:
            self.log_error(f"灰度化处理错误: {e}")
            return {'输出图像': None}
