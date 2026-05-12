"""
双边滤波节点 - 保边去噪滤波器
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class BilateralFilterNode(BaseNode):
    """
    双边滤波节点
    
    保边去噪滤波器，在平滑的同时保持边缘清晰
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '双边滤波'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(BilateralFilterNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'bilateral_params', '')
        self._param_container.add_spinbox('d', '邻域直径', value=9, min_value=5, max_value=15)
        self._param_container.add_spinbox('sigma_color', '颜色标准差', value=75.0, min_value=50.0, max_value=150.0, double=True)
        self._param_container.add_spinbox('sigma_space', '空间标准差', value=75.0, min_value=50.0, max_value=150.0, double=True)
        
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
            d = int(params.get('d', 9))
            sigma_color = float(params.get('sigma_color', 75.0))
            sigma_space = float(params.get('sigma_space', 75.0))
            
            filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            self.log_success(f"双边滤波完成 (直径: {d})")
            return {'输出图像': filtered}
            
        except Exception as e:
            self.log_error(f"双边滤波处理错误: {e}")
            return {'输出图像': None}