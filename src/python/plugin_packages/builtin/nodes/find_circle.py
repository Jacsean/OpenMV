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
        
        self.add_output('标注图像', color=(100, 255, 100))
        self.add_output('检测数量', color=(100, 100, 255))
        self.add_output('统计数据', color=(255, 255, 100))

        self.add_spinbox('gaussian_size', '高斯模糊核大小', value=3, min_value=1, max_value=15, tab='properties')
        self.add_spinbox('adaptive_win', '自适应窗口大小', value=15, min_value=3, max_value=31, tab='properties')
        self.add_spinbox('area_min', '最小面积', value=10, min_value=1, max_value=999999, tab='properties')
        self.add_spinbox('area_max', '最大面积', value=100000, min_value=1, max_value=999999, tab='properties')
        self.add_spinbox('center_dev_thresh', '中心偏差阈值', value=5.0, min_value=0.0, max_value=100.0, double=True, tab='properties')
        self.add_spinbox('radius_dev_thresh', '半径偏差阈值', value=0.1, min_value=0.0, max_value=1.0, double=True, tab='properties')

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
            "selected_contour_area": 0.0,
            "circles": []
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

            circle_data = {
                "center": {"x": round(cx + roi_x, 2), "y": round(cy + roi_y, 2)},
                "radius": round(radius, 2),
                "area": round(area, 2),
                "fit_error": round(circle_error, 4),
                "circularity": round(min(area / (np.pi * radius**2), 1.0) if radius > 0 else 0, 4)
            }
            result["circles"].append(circle_data)

        if result["circles"]:
            best_circle = min(result["circles"], key=lambda c: c["fit_error"])
            result["center"] = (best_circle["center"]["x"], best_circle["center"]["y"])
            result["radius"] = best_circle["radius"]
            result["selected_contour_area"] = best_circle["area"]
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
            dict: 包含标注图像、检测数量和统计数据的字典
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_error("未接收到输入图像")
                return {
                    '标注图像': None,
                    '检测数量': 0,
                    '统计数据': {}
                }

            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]

            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {
                    '标注图像': None,
                    '检测数量': 0,
                    '统计数据': {}
                }

            result_image = image.copy()
            if len(result_image.shape) == 2:
                result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)

            if self._current_template is None or self._current_template not in self._templates:
                roi_x = int(image.shape[1] * 0.25)
                roi_y = int(image.shape[0] * 0.25)
                roi_w = int(image.shape[1] * 0.5)
                roi_h = int(image.shape[0] * 0.5)
                roi = (roi_x, roi_y, roi_w, roi_h)
                self._learn_template("default_template", image, roi)

            circles_data = []
            detect_count = 0

            if self._current_template is not None:
                template = self._templates[self._current_template]
                hole = self._detect_hole(image, template["roi"])

                for idx, circle in enumerate(hole["circles"]):
                    center = (int(circle["center"]["x"]), int(circle["center"]["y"]))
                    radius = int(circle["radius"])
                    
                    cv2.circle(result_image, center, radius, (0, 255, 0), 2)
                    cv2.circle(result_image, center, 3, (0, 0, 255), -1)

                    if hole["valid"] and template.get("std_center"):
                        deviation = self._calc_deviation(
                            (circle["center"]["x"], circle["center"]["y"]),
                            circle["radius"],
                            template["std_center"],
                            template["std_radius"]
                        )
                        circle["deviation"] = deviation
                        circle["within_threshold"] = deviation["within_threshold"]
                    else:
                        circle["deviation"] = None
                        circle["within_threshold"] = True

                    circle["index"] = idx
                    circles_data.append(circle)

                detect_count = len(circles_data)

                self._detect_stats["total_detect"] += 1
                if detect_count > 0:
                    self._detect_stats["valid_detect"] += 1
                self._detect_stats["avg_time_ms"] = round(
                    (self._detect_stats["avg_time_ms"] * (self._detect_stats["total_detect"] - 1) + hole["time_ms"])
                    / self._detect_stats["total_detect"], 2
                )

                if detect_count > 0:
                    self.log_success(f"圆检测完成 (检测到 {detect_count} 个圆)")
                else:
                    self.log_warning("未检测到有效圆")
            else:
                self.log_warning("无有效模板")

            stats_data = {
                'total_count': detect_count,
                'filtered_count': detect_count,
                'circles': circles_data,
                'detection_stats': self._detect_stats,
                'current_template': self._current_template,
                'algorithm_version': '1.0.0'
            }

            return {
                '标注图像': result_image,
                '检测数量': detect_count,
                '统计数据': stats_data
            }

        except Exception as e:
            self.log_error(f"圆检测处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                '标注图像': None,
                '检测数量': 0,
                '统计数据': {}
            }
