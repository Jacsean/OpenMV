"""
节点注册表 - 统一管理节点注册机制

提供明确的节点注册时机和统一的注册接口：
1. 在应用启动时扫描插件（仅扫描元数据）
2. 在工作流创建时注册节点到 NodeGraph 和工作流注册表
3. 避免重复注册
4. 支持热重载
5. 工作流级节点命名空间隔离

遵循《AI 模块资源隔离设计规范》
"""

import utils
from utils.logger import logger
from typing import Dict, Set, Optional, Type


class NodeRegistry:
    """
    节点注册表 - 单例模式
    
    职责：
    - 管理插件节点的注册
    - 确保每个 NodeGraph 只注册一次节点
    - 提供统一的注册接口
    - 支持热重载
    - 支持工作流级节点命名空间隔离
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
        
        # 已注册节点类型的 NodeGraph 集合（避免重复注册）
        self._registered_graphs: Set[int] = set()
        
        # 插件管理器引用（延迟初始化）
        self._plugin_manager = None
        
        # 注册状态追踪
        self._registration_completed = False
    
    def set_plugin_manager(self, plugin_manager):
        """
        设置插件管理器
        
        Args:
            plugin_manager: PluginManager实例
        """
        self._plugin_manager = plugin_manager
    
    def is_registered(self, node_graph) -> bool:
        """
        检查 NodeGraph 是否已注册过节点
        
        Args:
            node_graph: NodeGraph实例
        
        Returns:
            bool: 是否已注册
        """
        return id(node_graph) in self._registered_graphs
    
    def register_nodes_to_graph(self, node_graph, workflow=None, force=False):
        """
        注册所有插件节点到指定的 NodeGraph
        
        Args:
            node_graph: NodeGraph实例
            workflow: Workflow实例（可选，用于工作流级节点注册表）
            force: 是否强制重新注册（用于热重载）
        
        Returns:
            bool: 注册是否成功
        """
        if not self._plugin_manager:
            logger.error("插件管理器未设置，无法注册节点", module="node_registry")
            return False
        
        # 检查是否已注册
        if self.is_registered(node_graph) and not force:
            logger.info(f"NodeGraph 已注册过节点，跳过", module="node_registry")
            return True
        
        logger.info(f"\n{'='*60}", module="node_registry")
        logger.info("📦 开始注册节点到 NodeGraph", module="node_registry")
        logger.info(f"{'='*60}", module="node_registry")
        
        try:
            # 获取所有已加载的插件
            plugins = self._plugin_manager.get_installed_plugins()
            logger.info(f"发现 {len(plugins)} 个插件", module="node_registry")
            
            registered_count = 0
            
            for plugin_info in plugins:
                logger.info(f"\n--- 处理插件: {plugin_info.name} ---", module="node_registry")
                
                # 加载插件节点
                success = self._plugin_manager.load_plugin_nodes(plugin_info.name, node_graph)
                
                if success:
                    # 如果提供了工作流，同时注册到工作流级别
                    if workflow:
                        for node_def in plugin_info.nodes:
                            class_name = node_def.class_name
                            node_key = f"{plugin_info.name}.{class_name}"
                            if node_key in self._plugin_manager.loaded_nodes:
                                node_class = self._plugin_manager.loaded_nodes[node_key]
                                workflow.register_node(node_class)
                                logger.info(f"   📋 注册到工作流: {node_def.display_name}", module="node_registry")
                    
                    registered_count += len(plugin_info.nodes)
                    logger.success(f"✅ 插件 {plugin_info.name} 注册完成", module="node_registry")
                else:
                    logger.warning(f"⚠️ 插件 {plugin_info.name} 注册失败", module="node_registry")
            
            # 标记该 NodeGraph 已注册
            self._registered_graphs.add(id(node_graph))
            
            logger.info(f"\n{'='*60}", module="node_registry")
            logger.success(f"✅ 节点注册完成，共注册 {registered_count} 个节点类型", module="node_registry")
            logger.info(f"{'='*60}", module="node_registry")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 节点注册失败: {e}", module="node_registry")
            import traceback
            traceback.print_exc()
            return False
    
    def unregister_nodes_from_graph(self, node_graph, workflow=None):
        """
        从 NodeGraph 注销节点（主要用于清理）
        
        Args:
            node_graph: NodeGraph实例
            workflow: Workflow实例（可选，用于清理工作流级别注册表）
        """
        graph_id = id(node_graph)
        if graph_id in self._registered_graphs:
            self._registered_graphs.remove(graph_id)
            logger.info(f"已从注册表移除 NodeGraph", module="node_registry")
        
        # 如果提供了工作流，同时清理工作流级别注册表
        if workflow:
            workflow.node_registry.clear()
            logger.info(f"已清理工作流节点注册表", module="node_registry")
    
    def reload_nodes(self, node_graph, workflow=None):
        """
        重新加载所有节点（用于热重载）
        
        Args:
            node_graph: NodeGraph实例
            workflow: Workflow实例（可选）
        
        Returns:
            bool: 是否成功
        """
        logger.info(f"\n🔄 开始重新加载节点", module="node_registry")
        
        # 先注销
        self.unregister_nodes_from_graph(node_graph, workflow)
        
        # 强制重新注册
        return self.register_nodes_to_graph(node_graph, workflow, force=True)
    
    def get_registered_graph_count(self) -> int:
        """
        获取已注册的 NodeGraph 数量
        
        Returns:
            int: 数量
        """
        return len(self._registered_graphs)


# 创建全局实例
node_registry = NodeRegistry()


def register_nodes_on_workflow_create(node_graph, workflow=None, plugin_manager=None):
    """
    在工作流创建时注册节点的便捷函数
    
    支持工作流级节点命名空间隔离：
    - 将节点注册到 NodeGraph（供 UI 使用）
    - 将节点注册到 Workflow.node_registry（工作流级别隔离）
    
    Args:
        node_graph: NodeGraph实例
        workflow: Workflow实例（可选，用于工作流级节点注册表）
        plugin_manager: PluginManager实例（可选，用于初始化注册表）
    
    Returns:
        bool: 是否成功
    """
    # 如果提供了 plugin_manager，设置到注册表
    if plugin_manager:
        node_registry.set_plugin_manager(plugin_manager)
    
    # 注册节点（支持工作流级别隔离）
    return node_registry.register_nodes_to_graph(node_graph, workflow)


__all__ = [
    'NodeRegistry',
    'node_registry',
    'register_nodes_on_workflow_create'
]