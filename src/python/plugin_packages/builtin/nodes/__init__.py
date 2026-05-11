"""
内置节点包 - 所有节点统一在此导入
"""

# 预处理节点
from .grayscale import GrayscaleNode
from .image_operation import ImageOperationNode
from .gaussian_blur import GaussianBlurNode
from .median_blur import MedianBlurNode
from .bilateral_filter import BilateralFilterNode
from .brightness_contrast import BrightnessContrastNode
from .histogram_equalization import HistogramEqualizationNode
from .threshold import ThresholdNode
from .adaptive_threshold import AdaptiveThresholdNode
from .morphology import MorphologyNode
from .resize import ResizeNode
from .rotate import RotateNode
from .image_evaluation import ImageEvaluationNode

# 特征提取节点
from .canny_edge import CannyEdgeNode
from .sobel_edge import SobelEdgeNode
from .contours_analysis import ContoursAnalysisNode
from .other_features import LaplacianNode, HarrisCornerNode, HoughLinesNode, HoughCirclesNode
from .find_circle import FindCircleNode

# 匹配定位节点
from .template_creator import TemplateCreatorNode
from .template_match import TemplateMatchNode

# IO相机节点
from .image_load import ImageLoadNode
from .image_save import ImageSaveNode
from .image_view import ImageViewNode
from .camera_capture import CameraCaptureNode
from .realtime_preview import RealTimePreviewNode
from .video_recorder import VideoRecorderNode
from .fast_detection import FastDetectionNode
from .json_display import JsonDisplayNode

# 集成节点
from .plc_node import PLCNode
from .data_output_node import DataOutputNode
from .robot_node import RobotNode

# 导出所有节点类
__all__ = [
    # 预处理
    'GrayscaleNode',
    'ImageOperationNode',
    'GaussianBlurNode',
    'MedianBlurNode',
    'BilateralFilterNode',
    'BrightnessContrastNode',
    'HistogramEqualizationNode',
    'ThresholdNode',
    'AdaptiveThresholdNode',
    'MorphologyNode',
    'ResizeNode',
    'RotateNode',
    'ImageEvaluationNode',
    # 特征提取
    'CannyEdgeNode',
    'SobelEdgeNode',
    'ContoursAnalysisNode',
    'LaplacianNode',
    'HarrisCornerNode',
    'HoughLinesNode',
    'HoughCirclesNode',
    'FindCircleNode',
    # 匹配定位
    'TemplateCreatorNode',
    'TemplateMatchNode',
    # IO相机
    'ImageLoadNode',
    'ImageSaveNode',
    'ImageViewNode',
    'CameraCaptureNode',
    'RealTimePreviewNode',
    'VideoRecorderNode',
    'FastDetectionNode',
    'JsonDisplayNode',
    # 集成
    'PLCNode',
    'DataOutputNode',
    'RobotNode',
]