"""YOLO 训练节点模块（重量级）"""

from .yolo_trainer import YOLOTrainerNode
from .yolo_quantizer import YOLOQuantizerNode

__all__ = ['YOLOTrainerNode', 'YOLOQuantizerNode']
