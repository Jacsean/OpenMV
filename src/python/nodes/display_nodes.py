"""
显示节点 - 图像显示和可视化
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class ImageViewNode(BaseNode):
    """
    图像显示节点
    用于在界面中显示图像信息和预览
    
    功能说明：
    - 接收图像数据输入
    - 显示图像尺寸、通道数等信息
    - 双击节点可打开图像预览窗口（需在主窗口中实现）
    - 输出状态文本供下游节点使用
    """
    
    __identifier__ = 'display'
    NODE_NAME = '图像显示'
    
    def __init__(self):
        super(ImageViewNode, self).__init__()
        self.add_input('输入图像', color=(100, 100, 255))
        # 添加一个文本输出用于状态显示
        self.add_output('状态', color=(100, 100, 255))
        self.add_text_input('status', '状态', tab='properties')
        # 缓存最后一张处理的图像（用于预览）
        self._cached_image = None
        
    def process(self, inputs):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表
            
        Returns:
            dict: 包含状态信息的字典
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            if image is not None:
                # 缓存图像用于预览
                self._cached_image = image.copy()
                
                # 获取图像信息
                height, width = image.shape[:2]
                channels = image.shape[2] if len(image.shape) == 3 else 1
                
                # 构建状态信息
                status_msg = f"图像尺寸: {width}x{height}"
                if channels > 1:
                    status_msg += f", 通道数: {channels}"
                
                # 计算数据类型和范围
                dtype = str(image.dtype)
                status_msg += f", 类型: {dtype}"
                
                self.set_property('status', status_msg)
                return {'状态': status_msg}
            else:
                self._cached_image = None
                self.set_property('status', '无有效图像')
                return {'状态': '无有效图像'}
        else:
            self._cached_image = None
            self.set_property('status', '无输入')
            return {'状态': '无输入'}
    
    def get_cached_image(self):
        """
        获取缓存的图像（用于预览）
        
        Returns:
            numpy.ndarray or None: 缓存的图像数据
        """
        return self._cached_image
