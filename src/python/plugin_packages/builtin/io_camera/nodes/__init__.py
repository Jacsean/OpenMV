"""
IO Camera 插件节点模块

导出所有图像相机相关节点。
"""

from .image_load import ImageLoadNode
from .image_save import ImageSaveNode
from .image_view import ImageViewNode
from .json_display import JsonDisplayNode
from .camera_capture import CameraCaptureNode

# Phase 3: 订阅者节点
try:
    from .realtime_preview import RealTimePreviewNode
except ImportError:
    RealTimePreviewNode = None

try:
    from .fast_detection import FastDetectionNode
except ImportError:
    FastDetectionNode = None

try:
    from .video_recorder import VideoRecorderNode
except ImportError:
    VideoRecorderNode = None
