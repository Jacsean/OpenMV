"""
节点生命周期管理模块

提供统一的节点生命周期管理机制：
- 节点状态机
- 生命周期钩子
- 资源清理机制
- 订阅关系管理
- Worker线程管理

遵循《AI 模块资源隔离设计规范》
"""

import enum
import weakref
from typing import Dict, List, Callable, Optional, Any
from abc import ABC, abstractmethod

from utils.logger import logger


class NodeState(enum.Enum):
    """
    节点状态枚举
    
    状态转换规则：
    INITIALIZED -> ACTIVATED -> PROCESSING -> IDLE -> DEACTIVATED -> DESTROYED
                        ^                              |
                        |______________________________|
    """
    INITIALIZED = "initialized"    # 节点已创建但未激活
    ACTIVATED = "activated"        # 节点已激活，可接收数据
    PROCESSING = "processing"      # 节点正在处理数据
    IDLE = "idle"                  # 节点空闲
    DEACTIVATED = "deactivated"    # 节点已停用
    DESTROYED = "destroyed"        # 节点已销毁


class LifecycleHook(ABC):
    """
    生命周期钩子基类
    
    定义节点生命周期各阶段的回调接口：
    - on_create: 节点创建时调用
    - on_activate: 节点激活时调用（连接到图中）
    - on_deactivate: 节点停用时调用（从图中移除）
    - on_destroy: 节点销毁前调用
    - on_process_start: 处理开始时调用
    - on_process_end: 处理结束时调用
    """
    
    @abstractmethod
    def on_create(self):
        """节点创建时调用"""
        pass
    
    @abstractmethod
    def on_activate(self):
        """节点激活时调用（连接到图中）"""
        pass
    
    @abstractmethod
    def on_deactivate(self):
        """节点停用时调用（从图中移除）"""
        pass
    
    @abstractmethod
    def on_destroy(self):
        """节点销毁前调用"""
        pass
    
    @abstractmethod
    def on_process_start(self):
        """处理开始时调用"""
        pass
    
    @abstractmethod
    def on_process_end(self, success: bool, error: Optional[Exception] = None):
        """处理结束时调用"""
        pass


class DefaultLifecycleHook(LifecycleHook):
    """
    默认生命周期钩子实现
    
    提供空实现，子类可选择性覆盖需要的钩子
    """
    
    def on_create(self):
        pass
    
    def on_activate(self):
        pass
    
    def on_deactivate(self):
        pass
    
    def on_destroy(self):
        pass
    
    def on_process_start(self):
        pass
    
    def on_process_end(self, success: bool, error: Optional[Exception] = None):
        pass


class NodeLifecycleManager:
    """
    节点生命周期管理器
    
    负责管理所有节点的生命周期状态转换和资源清理
    
    清理流程（delete_node_with_cleanup）：
    1. 通知生命周期管理器执行销毁
    2. 清理预览窗口引用
    3. 清理相关监听器
    4. 从NodeGraph中删除节点
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._nodes = weakref.WeakSet()  # 使用弱引用避免内存泄漏
            cls._instance._state_listeners = {}
            cls._instance._preview_windows = weakref.WeakKeyDictionary()  # 预览窗口引用
        return cls._instance
    
    def register_node(self, node):
        """
        注册节点到生命周期管理器
        
        Args:
            node: 实现了 LifecycleHook 的节点对象
        """
        if hasattr(node, '_lifecycle_hook'):
            self._nodes.add(node)
            # 初始化状态
            if not hasattr(node, '_node_state'):
                node._node_state = NodeState.INITIALIZED
    
    def unregister_node(self, node):
        """
        从生命周期管理器注销节点
        
        Args:
            node: 要注销的节点对象
        """
        if node in self._nodes:
            self._nodes.discard(node)
    
    def add_state_listener(self, node_id: str, listener: Callable[[NodeState], None]):
        """
        添加节点状态监听器
        
        Args:
            node_id: 节点ID
            listener: 状态变化回调函数
        """
        if node_id not in self._state_listeners:
            self._state_listeners[node_id] = []
        self._state_listeners[node_id].append(listener)
    
    def remove_state_listener(self, node_id: str, listener: Callable[[NodeState], None]):
        """
        移除节点状态监听器
        
        Args:
            node_id: 节点ID
            listener: 要移除的回调函数
        """
        if node_id in self._state_listeners:
            self._state_listeners[node_id].remove(listener)
    
    def _notify_state_change(self, node_id: str, new_state: NodeState):
        """
        通知所有监听器节点状态变化
        
        Args:
            node_id: 节点ID
            new_state: 新状态
        """
        if node_id in self._state_listeners:
            for listener in self._state_listeners[node_id]:
                try:
                    listener(new_state)
                except Exception as e:
                    logger.error(f"状态监听器调用失败: {e}", module="lifecycle")
    
    def transition_state(self, node, new_state: NodeState):
        """
        执行状态转换
        
        Args:
            node: 节点对象
            new_state: 目标状态
        """
        if not hasattr(node, '_node_state'):
            node._node_state = NodeState.INITIALIZED
        
        current_state = node._node_state
        
        # 状态转换验证
        if not self._is_valid_transition(current_state, new_state):
            logger.warning(f"无效的状态转换: {current_state} -> {new_state}", module="lifecycle")
            return False
        
        # 执行状态转换
        node._node_state = new_state
        
        # 调用生命周期钩子
        self._invoke_hook(node, new_state)
        
        # 通知监听器
        node_id = getattr(node, 'id', str(id(node)))
        self._notify_state_change(node_id, new_state)
        
        return True
    
    def _is_valid_transition(self, current: NodeState, target: NodeState) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            current: 当前状态
            target: 目标状态
        
        Returns:
            bool: 转换是否合法
        """
        valid_transitions = {
            NodeState.INITIALIZED: [NodeState.ACTIVATED, NodeState.DESTROYED],
            NodeState.ACTIVATED: [NodeState.PROCESSING, NodeState.IDLE, NodeState.DEACTIVATED],
            NodeState.PROCESSING: [NodeState.IDLE, NodeState.DEACTIVATED],
            NodeState.IDLE: [NodeState.PROCESSING, NodeState.DEACTIVATED],
            NodeState.DEACTIVATED: [NodeState.ACTIVATED, NodeState.DESTROYED],
            NodeState.DESTROYED: []
        }
        return target in valid_transitions.get(current, [])
    
    def _invoke_hook(self, node, state: NodeState):
        """
        根据状态调用对应的生命周期钩子
        
        Args:
            node: 节点对象
            state: 当前状态
        """
        hook = getattr(node, '_lifecycle_hook', None)
        if hook is None:
            return
        
        try:
            if state == NodeState.INITIALIZED:
                hook.on_create()
            elif state == NodeState.ACTIVATED:
                hook.on_activate()
            elif state == NodeState.PROCESSING:
                hook.on_process_start()
            elif state == NodeState.IDLE:
                hook.on_process_end(success=True)
            elif state == NodeState.DEACTIVATED:
                hook.on_deactivate()
            elif state == NodeState.DESTROYED:
                hook.on_destroy()
        except Exception as e:
            logger.error(f"生命周期钩子调用失败: {e}", module="lifecycle")
    
    def destroy_node(self, node):
        """
        销毁节点并清理资源
        
        Args:
            node: 要销毁的节点对象
        """
        # 转换到销毁状态（会触发 on_destroy 钩子）
        self.transition_state(node, NodeState.DESTROYED)
        
        # 注销节点
        self.unregister_node(node)
    
    def cleanup_all_nodes(self):
        """
        清理所有注册的节点
        
        通常在应用关闭时调用
        """
        for node in list(self._nodes):
            try:
                self.destroy_node(node)
            except Exception as e:
                logger.error(f"销毁节点失败: {e}", module="lifecycle")
    
    def register_preview_window(self, node, window):
        """
        注册节点的预览窗口
        
        Args:
            node: 节点对象
            window: 预览窗口对象
        """
        self._preview_windows[node] = window
    
    def unregister_preview_window(self, node):
        """
        注销节点的预览窗口
        
        Args:
            node: 节点对象
        """
        if node in self._preview_windows:
            window = self._preview_windows[node]
            try:
                window.close()
            except Exception as e:
                logger.warning(f"关闭预览窗口失败: {e}", module="lifecycle")
            del self._preview_windows[node]
    
    def delete_node_with_cleanup(self, node, node_graph=None):
        """
        完整删除节点并清理所有相关资源
        
        清理流程：
        1. 通知生命周期管理器执行销毁（触发 on_destroy 钩子）
        2. 清理预览窗口引用
        3. 清理相关监听器
        4. 从NodeGraph中删除节点（如果提供）
        
        Args:
            node: 要删除的节点对象
            node_graph: NodeGraph实例（可选，用于从图中移除节点）
        
        Returns:
            bool: 是否成功删除
        """
        try:
            logger.info(f"🗑️ 开始删除节点: {getattr(node, 'name', str(node))}", module="lifecycle")
            
            # 1. 清理预览窗口
            self.unregister_preview_window(node)
            
            # 2. 移除所有状态监听器
            node_id = getattr(node, 'id', str(id(node)))
            if node_id in self._state_listeners:
                del self._state_listeners[node_id]
                logger.info(f"   清理状态监听器", module="lifecycle")
            
            # 3. 销毁节点（触发生命周期钩子）
            self.destroy_node(node)
            logger.info(f"   执行生命周期销毁", module="lifecycle")
            
            # 4. 从NodeGraph中删除（如果提供）
            if node_graph is not None:
                try:
                    node_graph.delete_node(node)
                    logger.info(f"   从NodeGraph删除", module="lifecycle")
                except Exception as e:
                    logger.warning(f"   从NodeGraph删除失败: {e}", module="lifecycle")
            
            logger.success(f"✅ 节点删除完成", module="lifecycle")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除节点失败: {e}", module="lifecycle")
            import traceback
            traceback.print_exc()
            return False


class LifecycleMixin:
    """
    生命周期混入类
    
    为节点类提供生命周期管理能力
    """
    
    def __init__(self):
        self._lifecycle_hook = DefaultLifecycleHook()
        self._node_state = NodeState.INITIALIZED
        
        # 注册到生命周期管理器
        NodeLifecycleManager().register_node(self)
    
    def set_lifecycle_hook(self, hook: LifecycleHook):
        """
        设置自定义生命周期钩子
        
        Args:
            hook: 生命周期钩子实现
        """
        self._lifecycle_hook = hook
    
    def activate(self):
        """激活节点"""
        NodeLifecycleManager().transition_state(self, NodeState.ACTIVATED)
    
    def deactivate(self):
        """停用节点"""
        NodeLifecycleManager().transition_state(self, NodeState.DEACTIVATED)
    
    def destroy(self):
        """销毁节点"""
        NodeLifecycleManager().destroy_node(self)
    
    def get_state(self) -> NodeState:
        """获取当前状态"""
        return self._node_state
    
    def is_processing(self) -> bool:
        """检查是否正在处理"""
        return self._node_state == NodeState.PROCESSING
    
    def is_active(self) -> bool:
        """检查是否处于激活状态"""
        return self._node_state in [NodeState.ACTIVATED, NodeState.PROCESSING]


# 创建全局实例
lifecycle_manager = NodeLifecycleManager()

__all__ = [
    'NodeState',
    'LifecycleHook',
    'DefaultLifecycleHook',
    'NodeLifecycleManager',
    'LifecycleMixin',
    'lifecycle_manager'
]
