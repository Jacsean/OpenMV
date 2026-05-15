"""
Hough直线检测节点
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class HoughLinesNode(BaseNode):
    """Hough直线检测节点"""

    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Hough直线'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}

    def __init__(self):
        super(HoughLinesNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'hough_lines_params', '')
        self._param_container.add_spinbox('rho', '距离精度(像素)', value=1, min_value=1, max_value=100)
        self._param_container.add_spinbox('theta', '角度精度(弧度)', value=0.0174533, min_value=0.001, max_value=0.1, double=True)
        self._param_container.add_spinbox('threshold', '最小投票数', value=50, min_value=1, max_value=500)
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
            rho = float(params.get('rho', 1))
            theta = float(params.get('theta', 0.0174533))
            threshold = int(params.get('threshold', 50))

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLines(edges, rho, theta, threshold)

            result = image.copy()
            if lines is not None:
                for line in lines:
                    rho_val, theta_val = line[0]
                    a = np.cos(theta_val)
                    b = np.sin(theta_val)
                    x0 = a * rho_val
                    y0 = b * rho_val
                    x1 = int(x0 + 1000 * (-b))
                    y1 = int(y0 + 1000 * (a))
                    x2 = int(x0 - 1000 * (-b))
                    y2 = int(y0 - 1000 * (a))
                    cv2.line(result, (x1, y1), (x2, y2), (0, 255, 0), 2)

            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Hough直线检测错误: {e}")
            return {'输出图像': None}
