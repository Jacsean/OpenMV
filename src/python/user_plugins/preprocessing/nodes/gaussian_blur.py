"""
高斯模糊节点 - 对图像进行高斯模糊处理
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class GaussianBlurNode(AIBaseNode):
    """
    高斯模糊节点
    
    对图像进行高斯模糊处理，可调节核大小和标准差参数
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '高斯模糊'
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(GaussianBlurNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 参数配置
        self.add_text_input('kernel_size', '核大小(3-15,奇数)', tab='properties')
        self.set_property('kernel_size', '5')
        
        self.add_text_input('sigma_x', 'Sigma X(0-10)', tab='properties')
        self.set_property('sigma_x', '0')
    
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
            
            # Step 2: 读取参数
            kernel_size = int(self.get_property('kernel_size'))
            sigma_x = float(self.get_property('sigma_x'))
            
            # Step 3: 确保核大小为奇数且在有效范围内
            if kernel_size < 3:
                kernel_size = 3
            elif kernel_size > 15:
                kernel_size = 15
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            # Step 4: 执行高斯模糊
            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x)
            
            self.log_success(f"高斯模糊完成 (核大小: {kernel_size})")
            return {'输出图像': blurred}
            
        except Exception as e:
            self.log_error(f"高斯模糊处理错误: {e}")
            return {'输出图像': None}
