"""
图像显示节点 - 用于显示图像，支持双击打开预览窗口
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class ImageViewNode(BaseNode):
    """
    图像显示节点
    
    用于显示图像，支持双击打开预览窗口（在主窗口中实现）
    
    功能说明：
    - 接收图像数据输入
    - 缓存最后一张处理的图像
    - 双击节点可打开图像预览窗口（在主窗口中实现）
    - 显示图像尺寸、通道数等信息
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '图像显示'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ImageViewNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口（传递图像）
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 状态信息显示
        self.add_text_input('status', '状态信息', tab='properties')
        
        # 缓存最后一张处理的图像（用于预览）
        self._cached_image = None
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表，inputs[0]为第一个端口的输入
            
        Returns:
            dict: 输出端口名称 -> 数据
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self._cached_image = None
                self.set_property('status', '无输入')
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self._cached_image = None
                self.set_property('status', '无有效图像')
                return {'输出图像': None}
            
            # Step 1: 缓存图像用于预览
            self._cached_image = image.copy()
            
            # Step 2: 获取图像信息
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            
            # Step 3: 构建状态信息
            status_msg = f"图像尺寸: {width}x{height}"
            if channels > 1:
                status_msg += f", 通道数: {channels}"
            
            dtype = str(image.dtype)
            status_msg += f", 类型: {dtype}"
            
            self.set_property('status', status_msg)
            
            # Step 4: 输出图像供下游节点使用
            return {'输出图像': image}
            
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            self.set_property('status', error_msg)
            self.log_error(f"图像显示节点错误: {e}")
            return {'输出图像': None}
    
    def get_cached_image(self):
        """
        获取缓存的图像（用于预览）
        
        Returns:
            numpy.ndarray or None: 缓存的图像数据
        """
        return self._cached_image
