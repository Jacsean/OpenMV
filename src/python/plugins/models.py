"""
插件系统数据模型
定义插件元数据结构和节点定义
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class NodeDefinition:
    """节点定义"""
    class_name: str           # 节点类名
    display_name: str         # 显示名称
    category: str             # 分类（如"形态学"）
    icon: Optional[str] = None # 图标路径（Unicode emoji）
    width: Optional[int] = None  # 节点宽度（像素）
    height: Optional[int] = None # 节点高度（像素）
    description: str = ""     # 节点详细描述
    color: Optional[List[int]] = None  # 节点颜色 RGB [R, G, B]


@dataclass
class PluginInfo:
    """插件信息"""
    name: str                 # 插件ID（唯一）
    version: str              # 版本号
    author: str               # 作者
    description: str          # 描述
    category_group: str = ""  # 分类组名称（用于节点库标签页显示）
    nodes: List[NodeDefinition] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    min_app_version: str = "3.1.0"
    path: str = ""            # 插件路径
    enabled: bool = True
    installed_at: Optional[datetime] = None
