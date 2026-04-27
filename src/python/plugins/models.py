"""
插件系统数据模型
定义插件元数据结构和节点定义
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
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
    
    # AI 节点扩展字段（遵循《AI 模块资源隔离设计规范》）
    resource_level: str = "light"  # 资源等级: light/medium/heavy
    hardware_requirements: Dict[str, Any] = field(default_factory=lambda: {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    })  # 硬件要求
    dependencies: List[str] = field(default_factory=list)  # 节点级依赖
    optional_dependencies: Dict[str, List[str]] = field(default_factory=dict)  # 可选依赖


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
    source: str = "builtin"   # 插件来源: 'builtin' 或 'marketplace'
    priority: int = 1         # 加载优先级（数字越小优先级越高）
    
    # AI 插件扩展字段
    resource_level: str = "light"  # 资源等级: light/medium/heavy
    installation_guide: Dict[str, Any] = field(default_factory=dict)  # 安装指南
    hardware_recommendations: Dict[str, Any] = field(default_factory=dict)  # 硬件推荐
