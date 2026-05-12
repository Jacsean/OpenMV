"""
通用节点基类模块

提供统一的节点基础框架，适用于：
- OpenCV算法节点
- AI推理节点
- 系统集成节点
- 用户自定义节点

核心功能：
- 性能监控
- 资源管理
- 错误处理
- 日志记录
"""

from .base_node import BaseNode
from .performance_monitor import PerformanceMonitor
from .parameter_container import ParameterContainerWidget

__all__ = ['BaseNode', 'PerformanceMonitor', 'ParameterContainerWidget']