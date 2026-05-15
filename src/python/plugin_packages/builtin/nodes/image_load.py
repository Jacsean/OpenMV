"""
加载图像节点 - 从本地文件加载图像
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class ImageLoadNode(BaseNode):
    """
    加载图像节点
    
    从本地文件加载图像，支持常见格式（jpg, png, bmp等）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '加载图像'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ImageLoadNode, self).__init__()
        
        # 输出端口
        self.add_output('输出图像')
        
        # 参数配置
        self._param_container = ParameterContainerWidget(self.view, 'image_load_params', '')
        self._param_container.add_text_input('file_path', '文件路径', text='')
        
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')
        
        self._image = None
    
    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据
            
        Returns:
            dict: 包含输出图像的字典
        """
        try:
            params = self._param_container.get_values_dict()
            file_path = params.get('file_path', '')
            
            if not file_path:
                self.log_warning("未指定文件路径")
                return {'输出图像': None}
            
            # 执行图像加载
            self._image = cv2.imread(file_path)
            
            if self._image is not None:
                self.log_success(f"图像加载成功: {file_path}")
                return {'输出图像': self._image}
            else:
                self.log_error(f"无法读取图像: {file_path}")
                return {'输出图像': None}
                
        except Exception as e:
            self.log_error(f"加载图像错误: {e}")
            return {'输出图像': None}
