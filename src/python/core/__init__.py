"""
图形数据结构模块

提供统一的图形数据模型，支持标注、ROI和Mask三种类型的图形对象。

使用示例:
    from core.shapes import BaseShape, AnnotationShape, ROIShape, MaskShape, ShapeContainer
    
    # 创建图形容器
    container = ShapeContainer()
    
    # 添加ROI
    roi = ROIShape(type='rect', points=[(10, 10), (100, 100)])
    container.add_roi(roi)
    
    # 添加Mask
    mask = MaskShape(type='circle', points=[(50, 50), 30])
    container.add_mask(mask)
"""

from .shapes import BaseShape, AnnotationShape, ROIShape, MaskShape, ShapeContainer

__all__ = [
    'BaseShape',
    'AnnotationShape', 
    'ROIShape',
    'MaskShape',
    'ShapeContainer'
]
