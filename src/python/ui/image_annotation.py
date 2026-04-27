"""
图像标注模块

提供交互式图像标注功能：
- 基础图形：矩形、圆形、多边形、文字、箭头
- 非破坏性编辑：标注作为独立图层叠加显示
- 实时预览：绘制过程中虚线反馈
- 样式自定义：颜色、线宽、透明度
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import time
import uuid


@dataclass
class Annotation:
    """
    单个标注对象
    
    Attributes:
        id: 唯一标识符
        type: 标注类型 (rect/circle/polygon/text/arrow)
        points: 坐标点列表 [(x1,y1), (x2,y2), ...]
        properties: 样式属性 {color, thickness, text, font_size, ...}
        timestamp: 创建时间戳
        layer: 图层名称（用于分组管理）
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = "rect"  # rect, circle, polygon, text, arrow
    points: List[Tuple[int, int]] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=lambda: {
        'color': (0, 255, 0),      # BGR格式
        'thickness': 2,             # 线宽
        'text': '',                 # 文本内容（仅text类型）
        'font_size': 16,            # 字体大小
        'filled': False,            # 是否填充
        'fill_color': (0, 255, 0, 128)  # 填充颜色（含透明度）
    })
    timestamp: float = field(default_factory=time.time)
    layer: str = "default"
    
    def to_dict(self) -> Dict:
        """转换为字典（用于JSON序列化）"""
        return {
            'id': self.id,
            'type': self.type,
            'points': self.points,
            'properties': self.properties.copy(),
            'timestamp': self.timestamp,
            'layer': self.layer
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Annotation':
        """从字典创建标注对象"""
        ann = Annotation(
            id=data.get('id', str(uuid.uuid4())[:8]),
            type=data.get('type', 'rect'),
            points=[tuple(p) for p in data.get('points', [])],
            properties=data.get('properties', {}),
            timestamp=data.get('timestamp', time.time()),
            layer=data.get('layer', 'default')
        )
        return ann


class AnnotationLayer:
    """
    标注层管理器
    
    负责管理所有标注对象的增删改查和渲染
    
    Features:
        - 支持多个图层（通过layer字段区分）
        - 可控制图层的可见性
        - 提供标注的CRUD操作
        - 支持撤销/重做（Phase 2实现）
    """
    
    def __init__(self):
        self.annotations: Dict[str, Annotation] = {}  # id -> Annotation
        self.visible_layers: set = {"default"}         # 可见图层集合
        self.selected_id: Optional[str] = None          # 当前选中的标注ID
        
        # 历史记录（Phase 2实现）
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
    
    def add_annotation(self, annotation: Annotation) -> str:
        """
        添加标注
        
        Args:
            annotation: 标注对象
            
        Returns:
            标注ID
        """
        self.annotations[annotation.id] = annotation
        return annotation.id
    
    def remove_annotation(self, annotation_id: str) -> bool:
        """
        删除标注
        
        Args:
            annotation_id: 标注ID
            
        Returns:
            是否成功删除
        """
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]
            if self.selected_id == annotation_id:
                self.selected_id = None
            return True
        return False
    
    def update_annotation(self, annotation_id: str, **kwargs) -> bool:
        """
        更新标注属性
        
        Args:
            annotation_id: 标注ID
            **kwargs: 要更新的属性
            
        Returns:
            是否成功更新
        """
        if annotation_id in self.annotations:
            ann = self.annotations[annotation_id]
            for key, value in kwargs.items():
                if hasattr(ann, key):
                    setattr(ann, key, value)
            return True
        return False
    
    def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """获取标注对象"""
        return self.annotations.get(annotation_id)
    
    def get_visible_annotations(self) -> List[Annotation]:
        """获取所有可见图层的标注"""
        return [
            ann for ann in self.annotations.values()
            if ann.layer in self.visible_layers
        ]
    
    def clear_all(self):
        """清空所有标注"""
        self.annotations.clear()
        self.selected_id = None
    
    def clear_layer(self, layer_name: str):
        """清空指定图层"""
        self.annotations = {
            aid: ann for aid, ann in self.annotations.items()
            if ann.layer != layer_name
        }
    
    def toggle_layer_visibility(self, layer_name: str):
        """切换图层可见性"""
        if layer_name in self.visible_layers:
            self.visible_layers.discard(layer_name)
        else:
            self.visible_layers.add(layer_name)
    
    def select_annotation(self, annotation_id: Optional[str]):
        """选中/取消选中标注"""
        if annotation_id is None or annotation_id in self.annotations:
            self.selected_id = annotation_id
    
    def get_count(self) -> int:
        """获取标注总数"""
        return len(self.annotations)
    
    def export_to_json(self) -> List[Dict]:
        """导出所有标注为JSON兼容格式"""
        return [ann.to_dict() for ann in self.annotations.values()]
    
    def import_from_json(self, data: List[Dict]):
        """从JSON数据导入标注"""
        self.clear_all()
        for item in data:
            ann = Annotation.from_dict(item)
            self.annotations[ann.id] = ann
