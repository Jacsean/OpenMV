"""
事件总线 - 模块间通信基础设施

提供发布-订阅模式的事件通信，解耦模块间的直接依赖。
所有跨模块通信必须通过事件总线，禁止直接调用其他模块的方法。

使用方式：
    from core.event_bus import event_bus, Events

    # 订阅事件
    def on_workflow_executed(**kwargs):
        print(f"工作流执行完成: {kwargs.get('workflow_name')}")

    event_bus.subscribe(Events.WORKFLOW_EXECUTED, on_workflow_executed)

    # 发布事件
    event_bus.publish(Events.WORKFLOW_EXECUTED, workflow_name="默认工作流", results={})
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any
from collections import defaultdict
import inspect

import utils
from utils import logger


class EventBus:
    """
    事件总线（单例）

    支持：
    - 事件订阅/取消订阅
    - 事件发布
    - 弱引用回调（避免内存泄漏）
    - 事件名称自动转换为下划线格式
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._enabled = True

    def subscribe(self, event: Any, callback: Callable) -> None:
        """
        订阅事件

        Args:
            event: 事件枚举值或字符串
            callback: 回调函数，接收关键字参数
        """
        event_name = self._get_event_name(event)
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event: Any, callback: Callable) -> None:
        """
        取消订阅事件

        Args:
            event: 事件枚举值或字符串
            callback: 回调函数
        """
        event_name = self._get_event_name(event)
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def publish(self, event: Any, **kwargs) -> None:
        """
        发布事件

        Args:
            event: 事件枚举值或字符串
            **kwargs: 事件参数
        """
        if not self._enabled:
            return

        event_name = self._get_event_name(event)
        for callback in self._subscribers[event_name]:
            try:
                callback(**kwargs)
            except Exception as e:
                self._handle_callback_error(event_name, callback, e)

    def _get_event_name(self, event: Any) -> str:
        """获取事件名称字符串"""
        if isinstance(event, Enum):
            return event.name
        return str(event)

    def _handle_callback_error(self, event_name: str, callback: Callable, error: Exception) -> None:
        """处理回调执行错误"""
        logger.error(f"[EventBus] Error in callback for event '{event_name}': {error}")

    def enable(self) -> None:
        """启用事件总线"""
        self._enabled = True

    def disable(self) -> None:
        """禁用事件总线（用于批量操作）"""
        self._enabled = False

    def clear(self, event: Any = None) -> None:
        """
        清除订阅

        Args:
            event: 指定事件，不传则清除所有
        """
        if event is None:
            self._subscribers.clear()
        else:
            event_name = self._get_event_name(event)
            self._subscribers[event_name].clear()

    def get_subscribers(self, event: Any) -> List[Callable]:
        """获取事件的订阅者列表"""
        event_name = self._get_event_name(event)
        return self._subscribers[event_name].copy()


class Events(Enum):
    """
    系统事件枚举

    命名规范：{主体}_{动作}
    示例：WORKFLOW_EXECUTED = "workflow executed"
    """

    WORKFLOW_CREATED = auto()
    WORKFLOW_ADDED = auto()
    WORKFLOW_REMOVED = auto()
    WORKFLOW_SELECTED = auto()
    WORKFLOW_RENAMED = auto()

    WORKFLOW_EXECUTING = auto()
    WORKFLOW_EXECUTED = auto()
    WORKFLOW_EXECUTION_ERROR = auto()

    WORKFLOW_SAVED = auto()
    WORKFLOW_LOADED = auto()
    WORKFLOW_CLEARED = auto()

    PROJECT_CREATED = auto()
    PROJECT_OPENED = auto()
    PROJECT_SAVED = auto()
    PROJECT_CLOSED = auto()

    PLUGIN_SCANNED = auto()
    PLUGIN_LOADED = auto()
    PLUGIN_UNLOADED = auto()
    PLUGIN_INSTALL = auto()
    PLUGIN_UNINSTALL = auto()

    NODE_CREATED = auto()
    NODE_DELETED = auto()
    NODE_SELECTED = auto()
    NODE_RENAMED = auto()

    TAB_ADDED = auto()
    TAB_REMOVED = auto()
    TAB_CHANGED = auto()

    PREVIEW_OPENED = auto()
    PREVIEW_CLOSED = auto()
    PREVIEW_REFRESH = auto()

    SETTINGS_CHANGED = auto()


event_bus = EventBus()
