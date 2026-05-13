"""
亮度对比度调整节点 - 调整图像的亮度和对比度
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class BrightnessContrastNode(BaseNode):
    """
    亮度对比度调整节点
    
    调整图像的亮度和对比度，支持线性变换
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '亮度对比度'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(BrightnessContrastNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'bc_params', '')
        self._param_container.add_spinbox('alpha', '对比度', value=1.0, min_value=0.5, max_value=3.0, double=True)
        self._param_container.add_spinbox('beta', '亮度', value=0, min_value=-100, max_value=100)
        
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
            alpha = float(params.get('alpha', 1.0))
            beta = float(params.get('beta', 0))
            
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            self.log_success(f"亮度对比度调整完成 (对比度: {alpha}, 亮度: {beta})")
            return {'输出图像': adjusted}
            
        except Exception as e:
            self.log_error(f"亮度对比度调整错误: {e}")
            return {'输出图像': None}