"""
中值滤波节点 - 使用中值滤波器去除噪声
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class MedianBlurNode(BaseNode):
    """
    中值滤波节点
    
    使用中值滤波器去除噪声，特别适合椒盐噪声处理
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '中值滤波'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(MedianBlurNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'median_params', '')
        self._param_container.add_spinbox('ksize', '核大小', value=5, min_value=3, max_value=9)
        
        # 设置值变化回调
        self._param_container.set_value_changed_callback(self._on_param_changed)
        
        # 添加到节点
        self.add_custom_widget(self._param_container, tab='properties')
    
    def _on_param_changed(self, name, value):
        """参数值变化回调"""
        self.set_property(name, str(value))
    
    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            params = self._param_container.get_values_dict()
            ksize = int(params.get('ksize', 5))
            
            if ksize < 3:
                ksize = 3
            elif ksize > 9:
                ksize = 9
            if ksize % 2 == 0:
                ksize += 1
            
            blurred = cv2.medianBlur(image, ksize)
            self.log_success(f"中值滤波完成 (核大小: {ksize})")
            return {'输出图像': blurred}
            
        except Exception as e:
            self.log_error(f"中值滤波处理错误: {e}")
            return {'输出图像': None}