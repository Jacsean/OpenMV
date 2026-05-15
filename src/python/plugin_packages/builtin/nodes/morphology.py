"""
形态学操作节点 - 支持腐蚀、膨胀、开运算、闭运算等多种形态学操作
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class MorphologyNode(BaseNode):
    """
    形态学操作节点
    
    支持多种形态学运算：
    - erode: 腐蚀
    - dilate: 膨胀
    - open: 开运算（先腐蚀后膨胀）
    - close: 闭运算（先膨胀后腐蚀）
    - gradient: 形态学梯度（膨胀-腐蚀）
    - top hat: 顶帽（原图-开运算结果）
    - black hat: 黑帽（闭运算结果-原图）
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '形态学操作'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(MorphologyNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        
        self._param_container = ParameterContainerWidget(self.view, 'morphology_params', '')
        self._param_container.add_combobox('operation', '运算方法',
                                           items=['erode', 'dilate', 'gradient', 'open', 'close', 'top hat', 'black hat'])
        self._param_container.add_spinbox('iterations', '处理次数', value=1, min_value=1, max_value=10)
        
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')
    
    def _on_param_changed(self, name, value):
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
            operation = params.get('operation', 'erode')
            iterations = int(params.get('iterations', 1))
            
            # 限制处理次数在1-10之间
            iterations = max(1, min(10, iterations))
            
            # 如果是彩色图像，先转换为灰度
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 创建结构元素（3x3矩形）
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            
            # 执行形态学操作
            operation_map = {
                'erode': cv2.MORPH_ERODE,
                'dilate': cv2.MORPH_DILATE,
                'open': cv2.MORPH_OPEN,
                'close': cv2.MORPH_CLOSE,
                'gradient': cv2.MORPH_GRADIENT,
                'top hat': cv2.MORPH_TOPHAT,
                'black hat': cv2.MORPH_BLACKHAT
            }
            
            morph_type = operation_map.get(operation, cv2.MORPH_ERODE)
            result = cv2.morphologyEx(gray, morph_type, kernel, iterations=iterations)
            
            # 转换回BGR格式以便后续处理
            result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
            self.log_success(f"形态学操作完成 ({operation}, 次数: {iterations})")
            return {'输出图像': result_bgr}
            
        except Exception as e:
            self.log_error(f"形态学操作处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {'输出图像': None}