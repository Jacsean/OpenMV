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
