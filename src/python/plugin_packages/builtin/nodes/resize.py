"""
图像缩放节点 - 调整图像尺寸
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class ResizeNode(BaseNode):
    """
    图像缩放节点
    
    调整图像尺寸，支持多种插值方法
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像缩放'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ResizeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'resize_params', '')
        self._param_container.add_spinbox('width', '目标宽度', value=640, min_value=1, max_value=4096)
        self._param_container.add_spinbox('height', '目标高度', value=480, min_value=1, max_value=4096)
        self._param_container.add_combobox('interpolation', '插值方法', items=['INTER_NEAREST', 'INTER_LINEAR', 'INTER_CUBIC', 'INTER_AREA'])
        
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
            width = int(params.get('width', 640))
            height = int(params.get('height', 480))
            interp_method = params.get('interpolation', 'INTER_LINEAR')
            
            interp_map = {
                'INTER_NEAREST': cv2.INTER_NEAREST,
                'INTER_LINEAR': cv2.INTER_LINEAR,
                'INTER_CUBIC': cv2.INTER_CUBIC,
                'INTER_AREA': cv2.INTER_AREA
            }
            interpolation = interp_map.get(interp_method, cv2.INTER_LINEAR)
            
            resized = cv2.resize(image, (width, height), interpolation=interpolation)
            self.log_success(f"图像缩放完成 ({width}x{height})")
            return {'输出图像': resized}
            
        except Exception as e:
            self.log_error(f"图像缩放处理错误: {e}")
            return {'输出图像': None}