"""
圆检测节点 - 基于轮廓分析的圆检测
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np
import time
from typing import Dict, Optional, Tuple


class FindCircleNode(BaseNode):
    """
    圆检测节点

    基于轮廓分析的圆检测算法，支持多模板、偏差校验、亚像素精度

    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """

    __identifier__ = 'feature_extraction'
    NODE_NAME = '圆检测'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    def __init__(self):
        super(FindCircleNode, self).__init__()

        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))

        self.add_text_input('gaussian_size', '高斯模糊核大小', tab='properties')
        self.set_property('gaussian_size', '3')

        self.add_text_input('adaptive_win', '自适应窗口大小', tab='properties')
        self.set_property('adaptive_win', '15')

        self.add_text_input('area_min', '最小面积', tab='properties')
        self.set_property('area_min', '10')

        self.add_text_input('area_max', '最大面积', tab='properties')
        self.set_property('area_max', '100000')

        self.add_text_input('center_dev_thresh', '中心偏差阈值', tab='properties')
        self.set_property('center_dev_thresh', '5.0')

        self.add_text_input('radius_dev_thresh', '半径偏差阈值(0-1)', tab='properties')
        self.set_property('radius_dev_thresh', '0.1')

        self._templates: Dict[str, Dict] = {}
        self._current_template: Optional[str] = None
        self._detect_stats = {
            "total_detect": 0,
            "valid_detect": 0,
            "avg_time_ms": 0.0
        }

    def _preprocess(self, src: np.ndarray, adaptive_win: int) -> Tuple[np.ndarray, np.ndarray]:
        """图像预处理"""
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) if len(src.shape) == 3 else src.copy()
        gaussian_size = int(self.get_property('gaussian_size'))
        if gaussian_size % 2 == 0:
            gaussian_size += 1
        blur = cv2.GaussianBlur(gray, (gaussian_size, gaussian_size), 0)
        binary = cv2.adaptiveThreshold(
            blur, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            adaptive_win, 2
        )
        return binary, gray

    def _calc_deviation(self, detect_center: Tuple[float, float], detect_radius: float,
                       std_center: Tuple[float, float], std_radius: float) -> Dict:
        """计算检测结果与标准模板的偏差"""
        dx = abs(detect_center[0] - std_center[0])
        dy = abs(detect_center[1] - std_center[1])
        center_dev = np.sqrt(dx**2 + dy**2)
        radius_dev = abs(detect_radius - std_radius) / std_radius
        return {
            "center_dev": round(center_dev, 3),
            "radius_dev": round(radius_dev, 3),
            "within_threshold": (center_dev <= float(self.get_property('center_dev_thresh'))) and
                                (radius_dev <= float(self.get_property('radius_dev_thresh')))
        }

    def _detect_hole(self, src: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> Dict:
        """检测圆"""
        start = time.time()
        result = {
            "center": (0.0, 0.0),
            "radius": 0.0,
            "time_ms": 0.0,
            "valid": False,
            "contour_count": 0,
            "selected_contour_area": 0.0
        }

        adaptive_win = int(self.get_property('adaptive_win'))
        bin_img, _ = self._preprocess(src, adaptive_win)
        roi_img = bin_img
        roi_x, roi_y = 0, 0
        if roi is not None:
            roi_x, roi_y, roi_w, roi_h = roi
            roi_img = bin_img[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        contours, _ = cv2.findContours(roi_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        result["contour_count"] = len(contours)

        area_min = float(self.get_property('area_min'))
        area_max = float(self.get_property('area_max'))
        best_contour = None
        best_circle = None
        min_circle_error = float('inf')

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < area_min or area > area_max:
                continue

            cnt_sub = cv2.cornerSubPix(
                bin_img,
                np.float32(cnt.reshape(-1, 2)),
                (5, 5),
                (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )

            (cx, cy), radius = cv2.minEnclosingCircle(cnt_sub)
            cnt_sub_abs = cnt_sub + np.array([roi_x, roi_y])
            distances = np.sqrt((cnt_sub_abs[:, 0] - (cx + roi_x))**2 + (cnt_sub_abs[:, 1] - (cy + roi_y))**2)
            circle_error = np.var(distances)

            if circle_error < min_circle_error:
                min_circle_error = circle_error
                best_contour = cnt
                best_circle = (cx + roi_x, cy + roi_y, radius, area)

        if best_circle is not None:
            result["center"] = (best_circle[0], best_circle[1])
            result["radius"] = best_circle[2]
            result["selected_contour_area"] = best_circle[3]
            result["valid"] = True

        result["time_ms"] = round((time.time() - start) * 1000, 2)
        return result

    def _learn_template(self, template_name: str, src_img: np.ndarray, roi: Tuple[int, int, int, int]) -> bool:
        """学习模板"""
        if src_img is None or template_name in self._templates:
            return False

        adaptive_win = int(self.get_property('adaptive_win'))
        bin_img, _ = self._preprocess(src_img, adaptive_win)
        roi_bin = bin_img[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
        edge_tpl = cv2.Canny(roi_bin, 50, 150)

        hole = self._detect_hole(src_img, roi)
        if not hole["valid"]:
            return False

        self._templates[template_name] = {
            "edge_tpl": edge_tpl,
            "roi": roi,
            "std_center": hole["center"],
            "std_radius": hole["radius"],
            "learn_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        if self._current_template is None:
            self._current_template = template_name

        return True

    def _switch_template(self, template_name: str) -> bool:
        """切换模板"""
        if template_name in self._templates:
            self._current_template = template_name
            return True
        return False

    def process(self, inputs=None):
        """
        处理节点逻辑

        Args:
            inputs: 输入图像

        Returns:
            dict: 包含输出图像的字典
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}

            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]

            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}

            if self._current_template is None or self._current_template not in self._templates:
                roi_x = int(image.shape[1] * 0.25)
                roi_y = int(image.shape[0] * 0.25)
                roi_w = int(image.shape[1] * 0.5)
                roi_h = int(image.shape[0] * 0.5)
                roi = (roi_x, roi_y, roi_w, roi_h)

                self._learn_template("default_template", image, roi)

            if self._current_template is not None:
                template = self._templates[self._current_template]
                hole = self._detect_hole(image, template["roi"])

                if hole["valid"]:
                    deviation = self._calc_deviation(
                        hole["center"], hole["radius"],
                        template["std_center"], template["std_radius"]
                    )
                    hole.update(deviation)
                    hole["valid"] = deviation["within_threshold"]

                    result = image.copy()
                    cv2.circle(result, (int(hole["center"][0]), int(hole["center"][1])),
                                       int(hole["radius"]), (0, 255, 0), 2)
                    cv2.circle(result, (int(hole["center"][0]), int(hole["center"][1])),
                                       3, (0, 0, 255), -1)

                    self.log_success(f"圆检测完成 (中心: {hole['center']}, 半径: {hole['radius']:.2f})")
                    return {'输出图像': result}
                else:
                    self.log_warning("未检测到有效圆")
                    return {'输出图像': image}
            else:
                return {'输出图像': image}

        except Exception as e:
            self.log_error(f"圆检测处理错误: {e}")
            return {'输出图像': None}
