"""
Laplacian边缘检测节点
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class LaplacianNode(BaseNode):
    """Laplacian边缘检测节点"""

    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Laplacian算子'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}

    def __init__(self):
        super(LaplacianNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'laplacian_params', '')
        self._param_container.add_spinbox('ksize', '核大小(1-7,奇数)', value=1, min_value=1, max_value=7)
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
            ksize = int(params.get('ksize', 1))
            if ksize < 1: ksize = 1
            elif ksize > 7: ksize = 7
            if ksize % 2 == 0: ksize += 1

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize)
            laplacian_abs = cv2.convertScaleAbs(laplacian)
            laplacian_bgr = cv2.cvtColor(laplacian_abs, cv2.COLOR_GRAY2BGR)

            return {'输出图像': laplacian_bgr}
        except Exception as e:
            self.log_error(f"Laplacian边缘检测错误: {e}")
            return {'输出图像': None}
