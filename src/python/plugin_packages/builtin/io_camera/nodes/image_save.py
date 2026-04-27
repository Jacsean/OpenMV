"""
保存图像节点 - 将图像保存到本地文件
"""

from ...base_nodes import AIBaseNode
import cv2
import numpy as np


class ImageSaveNode(AIBaseNode):
    """
    保存图像节点
    
    将图像保存到本地文件，支持常见格式（jpg, png, bmp等）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '保存图像'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ImageSaveNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(255, 100, 100))
        
        # 参数配置
        self.add_text_input('save_path', '保存路径', tab='properties')
        self.add_text_input('status', '状态', tab='properties')
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含状态信息的字典
        """
        try:
            # Step 1: 获取输入图像
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                status_msg = '无输入图像'
                self.set_property('status', status_msg)
                self.log_warning(status_msg)
                return {'status': status_msg}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # Step 2: 获取保存路径
            save_path = self.get_property('save_path')
            
            if not save_path:
                status_msg = '未指定保存路径'
                self.set_property('status', status_msg)
                self.log_warning(status_msg)
                return {'status': status_msg}
            
            # Step 3: 执行保存操作
            result = cv2.imwrite(save_path, image)
            
            if result:
                status_msg = f'保存成功: {save_path}'
                self.set_property('status', status_msg)
                self.log_success(status_msg)
                return {'status': status_msg}
            else:
                status_msg = '保存失败'
                self.set_property('status', status_msg)
                self.log_error(status_msg)
                return {'status': status_msg}
                
        except Exception as e:
            status_msg = f'错误: {str(e)}'
            self.set_property('status', status_msg)
            self.log_error(f"保存图像错误: {e}")
            return {'status': status_msg}
