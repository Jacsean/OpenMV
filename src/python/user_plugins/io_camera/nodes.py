"""
图像相机节点包 - 图像采集与IO操作
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class ImageLoadNode(BaseNode):
    """
    加载图像节点
    从本地文件加载图像
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '加载图像'
    
    def __init__(self):
        super(ImageLoadNode, self).__init__()
        self.add_output('输出图像')
        self.add_text_input('file_path', '文件路径', tab='properties')
        self._image = None
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        file_path = self.get_property('file_path')
        if file_path:
            try:
                self._image = cv2.imread(file_path)
                if self._image is not None:
                    return {'输出图像': self._image}
                else:
                    print(f"无法读取图像: {file_path}")
                    return {'输出图像': None}
            except Exception as e:
                print(f"加载图像错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}


class ImageSaveNode(BaseNode):
    """
    保存图像节点
    将图像保存到本地文件
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '保存图像'
    
    def __init__(self):
        super(ImageSaveNode, self).__init__()
        self.add_input('输入图像', color=(255, 100, 100))
        self.add_text_input('save_path', '保存路径', tab='properties')
        self.add_text_input('status', '状态', tab='properties')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            save_path = self.get_property('save_path')
            
            if save_path:
                try:
                    result = cv2.imwrite(save_path, image)
                    if result:
                        status_msg = f'保存成功: {save_path}'
                        self.set_property('status', status_msg)
                        return {'status': status_msg}
                    else:
                        status_msg = '保存失败'
                        self.set_property('status', status_msg)
                        return {'status': status_msg}
                except Exception as e:
                    status_msg = f'错误: {str(e)}'
                    self.set_property('status', status_msg)
                    return {'status': status_msg}
            else:
                status_msg = '未指定保存路径'
                self.set_property('status', status_msg)
                return {'status': status_msg}
        
        status_msg = '无输入图像'
        self.set_property('status', status_msg)
        return {'status': status_msg}


class ImageViewNode(BaseNode):
    """
    图像显示节点
    用于显示图像，支持双击打开预览窗口
    
    功能说明：
    - 接收图像数据输入
    - 缓存最后一张处理的图像
    - 双击节点可打开图像预览窗口（在主窗口中实现）
    - 显示图像尺寸、通道数等信息
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '图像显示'
    
    def __init__(self):
        super(ImageViewNode, self).__init__()
        # 添加输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        # 添加输出端口（传递图像）
        self.add_output('输出图像', color=(100, 255, 100))
        # 添加状态信息显示
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
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is not None:
                try:
                    # 缓存图像用于预览
                    self._cached_image = image.copy()
                    
                    # 获取图像信息
                    height, width = image.shape[:2]
                    channels = image.shape[2] if len(image.shape) == 3 else 1
                    
                    # 构建状态信息
                    status_msg = f"图像尺寸: {width}x{height}"
                    if channels > 1:
                        status_msg += f", 通道数: {channels}"
                    
                    # 计算数据类型
                    dtype = str(image.dtype)
                    status_msg += f", 类型: {dtype}"
                    
                    self.set_property('status', status_msg)
                    
                    # 输出图像供下游节点使用
                    return {'输出图像': image}
                    
                except Exception as e:
                    error_msg = f"处理错误: {str(e)}"
                    self.set_property('status', error_msg)
                    print(f"图像显示节点错误: {e}")
                    return {'输出图像': None}
            else:
                self._cached_image = None
                self.set_property('status', '无有效图像')
                return {'输出图像': None}
        else:
            self._cached_image = None
            self.set_property('status', '无输入')
            return {'输出图像': None}
    
    def get_cached_image(self):
        """
        获取缓存的图像（用于预览）
        
        Returns:
            numpy.ndarray or None: 缓存的图像数据
        """
        return self._cached_image
