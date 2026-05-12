"""
阈值二值化节点 - 将图像转换为二值图像
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class ThresholdNode(BaseNode):
    """
    阈值二值化节点
    
    将图像转换为二值图像，支持多种阈值类型（普通、反向、截断等）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '阈值二值化'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ThresholdNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'threshold_params', '')
        self._param_container.add_spinbox('threshold', '阈值', value=127, min_value=0, max_value=255)
        self._param_container.add_spinbox('maxval', '最大值', value=255, min_value=0, max_value=255)
        self._param_container.add_combobox('type', '阈值类型', items=['THRESH_BINARY', 'THRESH_BINARY_INV', 'THRESH_TRUNC', 'THRESH_TOZERO'])
        
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
            threshold = float(params.get('threshold', 127))
            maxval = float(params.get('maxval', 255))
            thresh_type = params.get('type', 'THRESH_BINARY')
            
            # 如果是彩色图像，先转换为灰度
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            type_map = {
                'THRESH_BINARY': cv2.THRESH_BINARY,
                'THRESH_BINARY_INV': cv2.THRESH_BINARY_INV,
                'THRESH_TRUNC': cv2.THRESH_TRUNC,
                'THRESH_TOZERO': cv2.THRESH_TOZERO
            }
            thresh_method = type_map.get(thresh_type, cv2.THRESH_BINARY)
            
            _, binary = cv2.threshold(gray, threshold, maxval, thresh_method)
            binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            self.log_success(f"阈值二值化完成 (阈值: {threshold})")
            return {'输出图像': binary_bgr}
            
        except Exception as e:
            self.log_error(f"阈值二值化处理错误: {e}")
            return {'输出图像': None}