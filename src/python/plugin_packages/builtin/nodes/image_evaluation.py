"""
图像质量分析节点 - 评估图像的清晰度、亮度、对比度、噪声等质量指标
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np
import json


class ImageEvaluationNode(BaseNode):
    """
    图像质量分析节点

    支持多种图像质量评估算法：
    - 清晰度评估（拉普拉斯方差）
    - 亮度评估（平均亮度）
    - 对比度评估（像素标准差）
    - 噪声评估（高斯模糊差分）
    - 色彩丰富度（RGB通道统计）

    输出格式：JSON 字符串，包含所有选定的评估指标

    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """

    __identifier__ = 'preprocessing'
    NODE_NAME = '图像评估'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    def __init__(self):
        super(ImageEvaluationNode, self).__init__()

        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('评估结果(JSON)', color=(100, 100, 255))

        self._param_container = ParameterContainerWidget(self.view, 'image_eval_params', '')
        self._param_container.add_checkbox('sharpness', '清晰度', state=True)
        self._param_container.add_checkbox('brightness', '亮度', state=True)
        self._param_container.add_checkbox('contrast', '对比度', state=True)
        self._param_container.add_checkbox('noise', '噪声', state=True)
        self._param_container.add_checkbox('colorfulness', '色彩丰富度', state=True)
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')

    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))

    def _evaluate_sharpness(self, image):
        """
        评估图像清晰度（基于拉普拉斯方差）

        Args:
            image: BGR图像

        Returns:
            float: 清晰度分数，值越高越清晰
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return round(float(laplacian_var), 2)

    def _evaluate_brightness(self, image):
        """
        评估图像亮度

        Args:
            image: BGR图像

        Returns:
            float: 平均亮度（0-255）
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return round(float(mean_brightness), 2)

    def _evaluate_contrast(self, image):
        """
        评估图像对比度（基于像素标准差）

        Args:
            image: BGR图像

        Returns:
            float: 对比度分数，值越高对比度越强
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        return round(float(contrast), 2)

    def _evaluate_noise(self, image):
        """
        评估图像噪声水平（通过高斯模糊差分）

        Args:
            image: BGR图像

        Returns:
            float: 噪声水平，值越低越好
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        noise = cv2.absdiff(gray, blurred)
        noise_level = np.mean(noise)
        return round(float(noise_level), 2)

    def _evaluate_colorfulness(self, image):
        """
        评估图像色彩丰富度（基于RGB通道统计）

        Args:
            image: BGR图像

        Returns:
            float: 色彩丰富度分数，值越高色彩越丰富
        """
        b, g, r = cv2.split(image.astype(np.float32))

        rg = np.abs(r - g)
        yb = np.abs(0.5 * (r + g) - b)

        rg_mean, rg_std = np.mean(rg), np.std(rg)
        yb_mean, yb_std = np.mean(yb), np.std(yb)

        colorfulness = np.sqrt(rg_std**2 + yb_std**2) + 0.3 * np.sqrt(rg_mean**2 + yb_mean**2)
        return round(float(colorfulness), 2)

    def process(self, inputs=None):
        """
        执行图像质量评估

        Args:
            inputs: 输入数据列表，期望包含一个BGR图像

        Returns:
            dict: 包含评估结果的字典，键为'评估结果(JSON)'
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                empty_result = json.dumps({}, ensure_ascii=False, indent=2)
                return {'评估结果(JSON)': empty_result}

            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]

            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                empty_result = json.dumps({}, ensure_ascii=False, indent=2)
                return {'评估结果(JSON)': empty_result}

            params = self._param_container.get_values_dict()
            selected_metrics = []
            if params.get('sharpness'):
                selected_metrics.append('sharpness')
            if params.get('brightness'):
                selected_metrics.append('brightness')
            if params.get('contrast'):
                selected_metrics.append('contrast')
            if params.get('noise'):
                selected_metrics.append('noise')
            if params.get('colorfulness'):
                selected_metrics.append('colorfulness')

            if not selected_metrics:
                self.log_warning("未选择任何评估算法")
                empty_result = json.dumps({}, ensure_ascii=False, indent=2)
                return {'评估结果(JSON)': empty_result}

            results_dict = {}

            if 'sharpness' in selected_metrics:
                results_dict['清晰度'] = self._evaluate_sharpness(image)

            if 'brightness' in selected_metrics:
                results_dict['亮度'] = self._evaluate_brightness(image)

            if 'contrast' in selected_metrics:
                results_dict['对比度'] = self._evaluate_contrast(image)

            if 'noise' in selected_metrics:
                results_dict['噪声'] = self._evaluate_noise(image)

            if 'colorfulness' in selected_metrics:
                results_dict['色彩丰富度'] = self._evaluate_colorfulness(image)

            json_result = json.dumps(results_dict, ensure_ascii=False, indent=2)

            self.log_success(f"图像评估完成，共计算 {len(results_dict)} 个指标")
            return {'评估结果(JSON)': json_result}

        except Exception as e:
            self.log_error(f"图像评估处理错误: {e}")
            error_result = json.dumps({'error': str(e)}, ensure_ascii=False, indent=2)
            return {'评估结果(JSON)': error_result}
