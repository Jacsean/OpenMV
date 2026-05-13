"""
图像旋转节点 - 按指定角度旋转图像
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class RotateNode(BaseNode):
    """
    图像旋转节点
    
    按指定角度旋转图像，支持任意中心点和缩放比例
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '图像旋转'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(RotateNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'rotate_params', '')
        self._param_container.add_spinbox('angle', '旋转角度', value=0, min_value=-180, max_value=180)
        self._param_container.add_spinbox('scale', '缩放比例', value=1.0, min_value=0.1, max_value=2.0, double=True)
        
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
            angle = float(params.get('angle', 0))
            scale = float(params.get('scale', 1.0))
            
            h, w = image.shape[:2]
            center = (w / 2, h / 2)
            
            M = cv2.getRotationMatrix2D(center, angle, scale)
            
            abs_cos = abs(M[0, 0])
            abs_sin = abs(M[0, 1])
            new_w = int(h * abs_sin + w * abs_cos)
            new_h = int(h * abs_cos + w * abs_sin)
            
            M[0, 2] += new_w / 2 - center[0]
            M[1, 2] += new_h / 2 - center[1]
            
            rotated = cv2.warpAffine(image, M, (new_w, new_h))
            self.log_success(f"图像旋转完成 (角度: {angle}°, 缩放: {scale})")
            return {'输出图像': rotated}
            
        except Exception as e:
            self.log_error(f"图像旋转处理错误: {e}")
            return {'输出图像': None}