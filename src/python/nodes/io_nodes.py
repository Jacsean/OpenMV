"""
IO节点 - 图像输入输出节点
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class ImageLoadNode(BaseNode):
    """
    图像加载节点
    用于从文件加载图像
    """
    
    # 定义节点标识符和名称
    __identifier__ = 'io'
    NODE_NAME = '图像加载'
    
    def __init__(self):
        super(ImageLoadNode, self).__init__()
        self.add_output('图像输出')
        # 添加文件路径输入框，用户可以直接输入路径或双击编辑
        self.add_text_input('file_path', '文件路径（可直接输入或双击编辑）')
        self._image = None
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
        file_path = self.get_property('file_path')
        if file_path:
            try:
                self._image = cv2.imread(file_path)
                if self._image is not None:
                    return {'图像输出': self._image}
                else:
                    print(f"无法读取图像: {file_path}")
                    return {'图像输出': None}
            except Exception as e:
                print(f"加载图像错误: {e}")
                return {'图像输出': None}
        return {'图像输出': None}


class ImageSaveNode(BaseNode):
    """
    图像保存节点
    用于将图像保存到文件
    """
    
    # 定义节点标识符和名称
    __identifier__ = 'io'
    NODE_NAME = '图像保存'
    
    def __init__(self):
        super(ImageSaveNode, self).__init__()
        self.add_input('图像输入', color=(255, 100, 100))
        # 添加保存路径输入框
        self.add_text_input('save_path', '保存路径（可直接输入或双击编辑）')
        self.add_text_input('status', '状态', tab='properties')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        """
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
