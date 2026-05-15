"""
Laplacian边缘检测、Harris角点检测、Hough直线检测、Hough圆检测节点
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
