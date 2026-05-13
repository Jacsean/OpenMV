"""
图像金字塔节点 - 支持 PyrDown、PyrUp 和 PyrSegmentation 算法
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class PyramidNode(BaseNode):
    """
    图像金字塔节点

    提供三种图像金字塔操作：
    - PyrDown: 向下采样，尺寸减半
    - PyrUp: 向上采样，尺寸加倍
    - PyrSegmentation: 均值漂移分割 + 连通区域分析

    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """

    __identifier__ = 'preprocessing'
    NODE_NAME = '图像金字塔'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    def __init__(self):
        super(PyramidNode, self).__init__()

        self.add_input('输入图像', color=(100, 255, 100))
        
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('Blob信息', color=(255, 255, 100))

        self.add_combo_menu('algorithm', '算法类型',
                           items=['PyrDown', 'PyrUp', 'PyrSegmentation'],
                           tab='properties')

        self.add_spinbox('levels', '金字塔层数', value=1, min_value=1, max_value=5, tab='properties')

        self.add_combo_menu('border_type', '边界处理',
                           items=['BORDER_DEFAULT', 'BORDER_CONSTANT', 'BORDER_REPLICATE', 'BORDER_REFLECT'],
                           tab='properties')

        self.add_spinbox('spatial_radius', '空间窗口半径', value=5, min_value=1, max_value=50, tab='properties')

        self.add_spinbox('color_radius', '颜色窗口半径', value=10, min_value=1, max_value=100, tab='properties')

        self.add_spinbox('min_size', '最小区域面积', value=100, min_value=1, max_value=999999, tab='properties')

        self.add_combo_menu('connectivity', '连通性',
                           items=['4', '8'],
                           tab='properties')

    def _get_border_type(self, border_str):
        """获取边界处理类型"""
        border_map = {
            'BORDER_DEFAULT': cv2.BORDER_DEFAULT,
            'BORDER_CONSTANT': cv2.BORDER_CONSTANT,
            'BORDER_REPLICATE': cv2.BORDER_REPLICATE,
            'BORDER_REFLECT': cv2.BORDER_REFLECT
        }
        return border_map.get(border_str, cv2.BORDER_DEFAULT)

    def _pyr_down(self, image, levels, border_type):
        """向下采样处理"""
        result = image.copy()
        for _ in range(levels):
            result = cv2.pyrDown(result, borderType=border_type)
        return result

    def _pyr_up(self, image, levels, border_type):
        """向上采样处理"""
        result = image.copy()
        for _ in range(levels):
            result = cv2.pyrUp(result, borderType=border_type)
        return result

    def _pyr_segmentation(self, image, spatial_radius, color_radius, min_size, connectivity):
        """金字塔分割处理"""
        shifted = cv2.pyrMeanShiftFiltering(image, spatialRadius=spatial_radius, colorRadius=color_radius)

        if len(image.shape) == 3:
            gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
        else:
            gray = shifted.copy()

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=connectivity, ltype=cv2.CV_16U
        )

        blobs = []
        colors = [
            (0, 255, 0),
            (255, 0, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (128, 0, 0),
            (0, 128, 0)
        ]

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_size:
                continue

            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            cx, cy = centroids[i]

            mask = (labels == i).astype(np.uint8) * 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            perimeter = cv2.arcLength(contours[0], True) if contours else 0

            if len(image.shape) == 3:
                mean_val = cv2.mean(image, mask=mask)[:3]
            else:
                mean_val = cv2.mean(image, mask=mask)[0]

            blob = {
                'index': i,
                'center': {'x': round(float(cx), 2), 'y': round(float(cy), 2)},
                'area': int(area),
                'perimeter': round(perimeter, 2),
                'bounding_rect': {
                    'x': int(x),
                    'y': int(y),
                    'w': int(w),
                    'h': int(h)
                },
                'mean_intensity': tuple([round(v, 2) for v in mean_val]) if isinstance(mean_val, tuple) else round(mean_val, 2),
                'color': colors[(i - 1) % len(colors)]
            }
            blobs.append(blob)

        colored_labels = np.zeros((labels.shape[0], labels.shape[1], 3), dtype=np.uint8)
        for blob in blobs:
            color = blob['color']
            mask = (labels == blob['index'])
            colored_labels[mask] = color

        result_image = cv2.addWeighted(image, 0.5, colored_labels, 0.5, 0)

        return result_image, {
            'total_blobs': len(blobs),
            'blobs': blobs,
            'algorithm_version': '1.0.0',
            'method': 'pyrMeanShiftFiltering + connectedComponentsWithStats'
        }

    def process(self, inputs=None):
        """
        处理节点逻辑

        Args:
            inputs: 输入图像

        Returns:
            dict: 包含输出图像和Blob信息的字典
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_error("未接收到输入图像")
                return {
                    '输出图像': None,
                    'Blob信息': None
                }

            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]

            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {
                    '输出图像': None,
                    'Blob信息': None
                }

            algorithm = self.get_property('algorithm')
            result_image = image.copy()
            blob_info = None

            if algorithm == 'PyrDown':
                levels = max(1, min(5, int(self.get_property('levels'))))
                border_type = self._get_border_type(self.get_property('border_type'))
                result_image = self._pyr_down(image, levels, border_type)
                self.log_success(f"PyrDown 完成 (层数: {levels})")

            elif algorithm == 'PyrUp':
                levels = max(1, min(5, int(self.get_property('levels'))))
                border_type = self._get_border_type(self.get_property('border_type'))
                result_image = self._pyr_up(image, levels, border_type)
                self.log_success(f"PyrUp 完成 (层数: {levels})")

            elif algorithm == 'PyrSegmentation':
                spatial_radius = max(1, int(self.get_property('spatial_radius')))
                color_radius = max(1, int(self.get_property('color_radius')))
                min_size = max(1, int(self.get_property('min_size')))
                connectivity = int(self.get_property('connectivity'))

                result_image, blob_info = self._pyr_segmentation(
                    image, spatial_radius, color_radius, min_size, connectivity
                )
                self.log_success(f"PyrSegmentation 完成 (检测到 {blob_info['total_blobs']} 个区域)")

            if len(result_image.shape) == 2:
                result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)

            return {
                '输出图像': result_image,
                'Blob信息': blob_info
            }

        except Exception as e:
            self.log_error(f"图像金字塔处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                '输出图像': None,
                'Blob信息': None
            }
