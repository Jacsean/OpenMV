"""
Harris角点检测节点
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class HarrisCornerNode(BaseNode):
    """Harris角点检测节点"""

    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Harris角点'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}

    def __init__(self):
        super(HarrisCornerNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'harris_params', '')
        self._param_container.add_spinbox('block_size', '邻域大小(2-10)', value=2, min_value=2, max_value=10)
        self._param_container.add_spinbox('ksize', 'Sobel核大小(1-7)', value=3, min_value=1, max_value=7)
        self._param_container.add_spinbox('k', 'Harris参数(0.04-0.06)', value=0.04, min_value=0.04, max_value=0.06, double=True)
        self._param_container.add_spinbox('threshold', '阈值(0.001-0.01)', value=0.01, min_value=0.001, max_value=0.01, double=True)
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')

    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))

    def process(self, inputs=None):
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}

            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            params = self._param_container.get_values_dict()
            block_size = int(params.get('block_size', 2))
            ksize = int(params.get('ksize', 3))
            k = float(params.get('k', 0.04))
            threshold = float(params.get('threshold', 0.01))

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray = np.float32(gray)
            dst = cv2.cornerHarris(gray, block_size, ksize, k)

            result = image.copy()
            result[dst > threshold * dst.max()] = [0, 0, 255]

            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Harris角点检测错误: {e}")
            return {'输出图像': None}
