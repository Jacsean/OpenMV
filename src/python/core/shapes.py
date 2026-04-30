"""
图形数据结构定义模块

提供统一的图形数据模型，支持标注、ROI和Mask三种类型的图形对象。
其他模块可以直接导入使用这些数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from datetime import datetime
import uuid


@dataclass
class BaseShape:
    """图形基类
    
    所有图形类型的基础类，包含通用的属性和方法。
    
    Attributes:
        id: 唯一标识符（自动生成）
        type: 图形类型 ('rect', 'circle', 'polygon', 'point', 'line', 'text', 'arrow')
        points: 顶点坐标列表 [(x1, y1), (x2, y2), ...]
        border_color: 边框颜色 (BGR格式)
        fill_color: 填充颜色 (BGR格式)，None表示不填充
        thickness: 线条粗细（像素）
        line_style: 线条样式 ('solid', 'dashed', 'dotted')
        name: 图形名称
        visible: 是否可见
        locked: 是否锁定（不可编辑）
        created_at: 创建时间
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = ""  # 'rect', 'circle', 'polygon', 'point', 'line', 'text', 'arrow'
    points: List[Tuple[int, int]] = field(default_factory=list)
    
    # 视觉属性
    border_color: Tuple[int, int, int] = (0, 255, 0)  # BGR格式
    fill_color: Optional[Tuple[int, int, int]] = None
    thickness: int = 2
    line_style: str = 'solid'  # 'solid', 'dashed', 'dotted'
    
    # 元数据
    name: str = ""
    visible: bool = True
    locked: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnnotationShape(BaseShape):
    """普通标注形状（不导出，仅视觉辅助）
    
    用于在图像上添加临时标注，不会被导出到节点。
    适用于调试、说明等场景。
    """
    pass


@dataclass
class ROIShape(BaseShape):
    """ROI（Region of Interest）形状
    
    仅支持矩形类型，可导出为JSON格式到节点。
    用于定义感兴趣的区域，供后续处理使用。
    
    固定样式：
    - 边框颜色：橙色 (255, 100, 0)
    - 线条粗细：3像素
    - 线条样式：实线
    - 无填充
    """
    def __post_init__(self):
        if self.type and self.type != 'rect':
            raise ValueError("ROI只能是矩形")
        # ROI固定样式
        self.border_color = (255, 100, 0)  # 橙色
        self.thickness = 3
        self.line_style = 'solid'
        self.fill_color = None


@dataclass
class MaskShape(BaseShape):
    """Mask（掩码）形状
    
    支持矩形、圆形、多边形类型，可导出为灰度图到节点。
    用于定义需要处理的区域，生成二值掩码图像。
    
    默认样式：
    - 边框颜色：红色 (255, 0, 0)
    - 填充颜色：红色 (255, 0, 0)，半透明显示
    - 线条粗细：2像素
    - 线条样式：实线
    """
    def __post_init__(self):
        if self.type and self.type not in ['rect', 'circle', 'polygon']:
            raise ValueError("Mask支持矩形、圆形、多边形")
        # Mask默认样式
        self.border_color = (255, 0, 0)    # 红色边框
        self.fill_color = (255, 0, 0)      # 红色填充（半透明）
        self.thickness = 2
        self.line_style = 'solid'


class ShapeContainer:
    """图形容器管理器
    
    统一管理三种类型的图形对象（标注、ROI、Mask），
    提供增删改查、选择、移动、调整大小等功能。
    
    Attributes:
        annotations: 普通标注列表
        rois: ROI对象列表
        masks: Mask对象列表
        current_mode: 当前模式 ('annotation', 'roi', 'mask')
        current_tool: 当前激活的工具
        selected_roi: 当前选中的ROI
        selected_mask: 当前选中的Mask
        selected_shape: 当前选中的图形（通用）
        is_moving_shape: 是否正在移动图形
        shape_move_offset: 移动偏移量
        resize_handle: 当前激活的调整手柄
        resize_start_pos: 调整大小起始位置
    """
    
    def __init__(self):
        # 三种图形容器
        self.annotations = []  # List[AnnotationShape] - 普通标注
        self.rois = []         # List[ROIShape] - ROI对象
        self.masks = []        # List[MaskShape] - Mask对象
        
        # 当前状态
        self.current_mode = 'annotation'  # 'annotation', 'roi', 'mask'
        self.current_tool = None          # 当前激活的工具
        
        # 当前选中的对象（互斥）
        self.selected_roi = None
        self.selected_mask = None
        
        # === 通用编辑状态 ===
        self.selected_shape = None       # 当前选中的图形（任意类型）
        self.is_moving_shape = False     # 是否正在移动图形
        self.shape_move_offset = None    # 移动偏移量
        self.resize_handle = None        # 当前激活的调整手柄
        self.resize_start_pos = None     # 调整大小起始位置
    
    def switch_mode(self, mode: str):
        """切换模式，清空互斥的选中状态
        
        Args:
            mode: 目标模式 ('annotation', 'roi', 'mask')
        """
        old_mode = self.current_mode
        self.current_mode = mode
        
        if mode == 'roi':
            self.selected_mask = None  # 取消Mask选中
        elif mode == 'mask':
            self.selected_roi = None  # 取消ROI选中
        
        print(f"✅ 切换到{self._get_mode_name(mode)}模式")
    
    def select_roi(self, roi: ROIShape):
        """选中ROI，自动取消Mask选中
        
        Args:
            roi: ROI对象
        """
        self.selected_roi = roi
        self.selected_mask = None
        print(f"✅ 选中ROI: {roi.name or roi.id}")
    
    def select_mask(self, mask: MaskShape):
        """选中Mask，自动取消ROI选中
        
        Args:
            mask: Mask对象
        """
        self.selected_mask = mask
        self.selected_roi = None
        print(f"✅ 选中Mask: {mask.name or mask.id}")
    
    def clear_selection(self):
        """清除所有选中状态"""
        self.selected_roi = None
        self.selected_mask = None
        self.selected_shape = None
    
    def add_annotation(self, shape: AnnotationShape):
        """添加普通标注
        
        Args:
            shape: AnnotationShape对象
        """
        self.annotations.append(shape)
    
    def add_roi(self, shape: ROIShape):
        """添加ROI
        
        Args:
            shape: ROIShape对象
        """
        if not shape.name:
            shape.name = f"检测区域_{len(self.rois) + 1}"
        self.rois.append(shape)
    
    def add_mask(self, shape: MaskShape):
        """添加Mask
        
        Args:
            shape: MaskShape对象
        """
        if not shape.name:
            shape.name = f"Mask区域_{len(self.masks) + 1}"
        self.masks.append(shape)
    
    def remove_annotation(self, shape_id: str):
        """删除普通标注
        
        Args:
            shape_id: 图形ID
        """
        self.annotations = [a for a in self.annotations if a.id != shape_id]
    
    def remove_roi(self, shape_id: str):
        """删除ROI
        
        Args:
            shape_id: 图形ID
        """
        self.rois = [r for r in self.rois if r.id != shape_id]
        if self.selected_roi and self.selected_roi.id == shape_id:
            self.selected_roi = None
    
    def remove_mask(self, shape_id: str):
        """删除Mask
        
        Args:
            shape_id: 图形ID
        """
        self.masks = [m for m in self.masks if m.id != shape_id]
        if self.selected_mask and self.selected_mask.id == shape_id:
            self.selected_mask = None
    
    def get_all_shapes(self):
        """获取所有可见图形
        
        Returns:
            List: 包含所有可见图形的列表
        """
        shapes = []
        shapes.extend([a for a in self.annotations if a.visible])
        shapes.extend([r for r in self.rois if r.visible])
        shapes.extend([m for m in self.masks if m.visible])
        return shapes
    
    def _get_mode_name(self, mode: str) -> str:
        """获取模式的中文名称
        
        Args:
            mode: 模式标识
            
        Returns:
            str: 中文模式名称
        """
        mode_names = {
            'annotation': '绘图',
            'roi': 'ROI',
            'mask': 'Mask'
        }
        return mode_names.get(mode, mode)
    
    def select_shape(self, shape):
        """通用图形选择方法（支持所有类型）
        
        Args:
            shape: 要选中的图形对象
        """
        self.clear_selection()
        
        if isinstance(shape, ROIShape):
            self.selected_roi = shape
            self.selected_shape = shape
        elif isinstance(shape, MaskShape):
            self.selected_mask = shape
            self.selected_shape = shape
        elif isinstance(shape, AnnotationShape):
            self.selected_shape = shape
        
        print(f"✅ 选中图形: {shape.name or shape.id} (类型: {shape.type})")
    
    def get_shape_at_position(self, scene_pos, shapes_list=None):
        """获取指定位置的图形
        
        Args:
            scene_pos: 场景坐标 (QPointF)
            shapes_list: 可选的图形列表，默认为所有可见图形
            
        Returns:
            BaseShape或None: 找到的图形对象，未找到返回None
        """
        if shapes_list is None:
            shapes_list = self.get_all_shapes()
        
        for shape in reversed(shapes_list):
            if self.is_point_in_shape(shape, scene_pos):
                return shape
        return None
    
    def is_point_in_shape(self, shape, scene_pos):
        """判断点是否在图形内部（使用射线法）
        
        Args:
            shape: 图形对象
            scene_pos: 场景坐标 (QPointF)
            
        Returns:
            bool: 点是否在图形内部
        """
        x, y = int(scene_pos.x()), int(scene_pos.y())
        
        if shape.type == 'rect' and len(shape.points) >= 2:
            x1, y1 = shape.points[0]
            x2, y2 = shape.points[1]
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            return min_x <= x <= max_x and min_y <= y <= max_y
        
        elif shape.type == 'circle' and len(shape.points) >= 2:
            cx, cy = shape.points[0]
            radius = shape.points[1]
            distance = ((x - cx)**2 + (y - cy)**2)**0.5
            return distance <= radius
        
        elif shape.type == 'polygon' and len(shape.points) >= 3:
            # 使用射线法判断点是否在多边形内
            n = len(shape.points)
            inside = False
            p1x, p1y = shape.points[0]
            for i in range(1, n + 1):
                p2x, p2y = shape.points[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            return inside
        
        return False
    
    def get_resize_handles(self, shape):
        """获取图形的调整大小手柄位置
        
        Args:
            shape: 图形对象
            
        Returns:
            dict: 手柄名称到位置的映射
                - 矩形: 8个手柄 (top-left, top-right, bottom-left, bottom-right, top, bottom, left, right)
                - 圆形: 1个手柄 (radius)
        """
        handles = {}
        
        if shape.type == 'rect' and len(shape.points) >= 2:
            x1, y1 = shape.points[0]
            x2, y2 = shape.points[1]
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            handles['top-left'] = (min_x, min_y)
            handles['top-right'] = (max_x, min_y)
            handles['bottom-left'] = (min_x, max_y)
            handles['bottom-right'] = (max_x, max_y)
            handles['top'] = ((min_x + max_x) // 2, min_y)
            handles['bottom'] = ((min_x + max_x) // 2, max_y)
            handles['left'] = (min_x, (min_y + max_y) // 2)
            handles['right'] = (max_x, (min_y + max_y) // 2)
        
        elif shape.type == 'circle' and len(shape.points) >= 2:
            cx, cy = shape.points[0]
            radius = shape.points[1]
            handles['radius'] = (cx + radius, cy)
        
        return handles
    
    def get_handle_at_position(self, shape, scene_pos, handle_size=10):
        """获取指定位置的手柄名称
        
        Args:
            shape: 图形对象
            scene_pos: 场景坐标 (QPointF)
            handle_size: 手柄检测范围（像素）
            
        Returns:
            str或None: 手柄名称，未找到返回None
        """
        handles = self.get_resize_handles(shape)
        x, y = int(scene_pos.x()), int(scene_pos.y())
        
        for handle_name, (hx, hy) in handles.items():
            if abs(x - hx) <= handle_size and abs(y - hy) <= handle_size:
                return handle_name
        
        return None
    
    def move_shape(self, shape, delta_x, delta_y):
        """移动图形位置
        
        Args:
            shape: 图形对象
            delta_x: X轴偏移量
            delta_y: Y轴偏移量
        """
        if shape.type in ['rect', 'circle', 'polygon', 'text']:
            shape.points = [(int(x + delta_x), int(y + delta_y)) for x, y in shape.points]
    
    def resize_shape(self, shape, handle_name, new_pos):
        """调整图形大小
        
        Args:
            shape: 图形对象
            handle_name: 手柄名称
            new_pos: 新的位置坐标 (QPointF)
        """
        x, y = int(new_pos.x()), int(new_pos.y())
        
        if shape.type == 'rect' and len(shape.points) >= 2:
            if handle_name == 'top-left':
                shape.points[0] = (x, y)
            elif handle_name == 'top-right':
                shape.points[1] = (x, shape.points[0][1])
                shape.points[0] = (shape.points[1][0], y)
            elif handle_name == 'bottom-left':
                shape.points[0] = (x, shape.points[1][1])
                shape.points[1] = (shape.points[0][0], y)
            elif handle_name == 'bottom-right':
                shape.points[1] = (x, y)
            elif handle_name == 'top':
                shape.points[0] = (shape.points[0][0], y)
                shape.points[1] = (shape.points[1][0], shape.points[0][1])
            elif handle_name == 'bottom':
                shape.points[1] = (shape.points[1][0], y)
            elif handle_name == 'left':
                shape.points[0] = (x, shape.points[0][1])
            elif handle_name == 'right':
                shape.points[1] = (x, shape.points[1][1])
        
        elif shape.type == 'circle' and len(shape.points) >= 2:
            if handle_name == 'radius':
                cx, cy = shape.points[0]
                radius = int(((x - cx)**2 + (y - cy)**2)**0.5)
                shape.points[1] = radius
