"""
Hough圆检测节点
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class HoughCirclesNode(BaseNode):
    """Hough圆检测节点"""

    __identifier__ = 'feature_extraction'
    NODE_NAME = 'Hough圆'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}

    def __init__(self):
        super(HoughCirclesNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'hough_circles_params', '')
        self._param_container.add_spinbox('dp', '累加器分辨率(1-2)', value=1, min_value=1, max_value=2)
        self._param_container.add_spinbox('min_dist', '最小圆心距离', value=20, min_value=1, max_value=100)
        self._param_container.add_spinbox('param1', 'Canny高阈值', value=100, min_value=1, max_value=500)
        self._param_container.add_spinbox('param2', '圆心检测阈值', value=30, min_value=1, max_value=500)
        self._param_container.add_spinbox('min_radius', '最小半径', value=0, min_value=0, max_value=1000)
        self._param_container.add_spinbox('max_radius', '最大半径', value=0, min_value=0, max_value=1000)
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
            dp = int(params.get('dp', 1))
            min_dist = int(params.get('min_dist', 20))
            param1 = int(params.get('param1', 100))
            param2 = int(params.get('param2', 30))
            min_radius = int(params.get('min_radius', 0))
            max_radius = int(params.get('max_radius', 0))

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp, min_dist,
                                      param1=param1, param2=param2,
                                      minRadius=min_radius, maxRadius=max_radius)

            result = image.copy()
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for circle in circles[0, :]:
                    center = (circle[0], circle[1])
                    radius = circle[2]
                    cv2.circle(result, center, 1, (0, 100, 100), 3)
                    cv2.circle(result, center, radius, (255, 0, 255), 2)

            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"Hough圆检测错误: {e}")
            return {'输出图像': None}
