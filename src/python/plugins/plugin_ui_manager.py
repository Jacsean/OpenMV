"""
插件UI管理器

负责处理与插件相关的UI交互逻辑，包括：
- 插件加载到NodeGraph
- 节点库面板刷新
- 插件安装/卸载/管理的对话框交互
- 插件重新扫描和热重载
"""

from PySide2 import QtWidgets, QtCore


class PluginUIManager:
    """
    插件UI管理器
    
    职责：
    - 封装所有插件相关的UI交互逻辑
    - 提供简洁的API供MainWindow调用
    - 处理插件加载、安装、卸载、管理的用户界面
    """
    
    def __init__(self, plugin_manager, main_window):
        """
        初始化插件UI管理器
        
        Args:
            plugin_manager: PluginManager实例
            main_window: MainWindow实例（用于访问UI组件）
        """
        self.plugin_manager = plugin_manager
        self.main_window = main_window
    
    def load_plugins_to_graph(self, node_graph):
        """
        将插件节点加载到指定的NodeGraph，并自动归类
        
        Args:
            node_graph: NodeGraph实例（工作流Graph）
            
        Returns:
            set: 新增的分类名称集合
        """
        if not hasattr(self.main_window, '_pending_plugins'):
            return set()
        
        if not self.main_window._pending_plugins:
            return set()
        
        print("\n" + "="*80)
        print("【阶段1】构建 category_group 映射表")
        print("="*80)
        
        new_categories = set()
        # 构建标识符到显示名称的映射
        identifier_to_display_name = {}
        
        # 收集所有需要加载的插件
        plugins_to_load = []
        for plugin_info in self.main_window._pending_plugins:
            if plugin_info.enabled:
                plugins_to_load.append(plugin_info)
                # 记录标识符映射（使用plugin.json的name作为identifier，category_group作为显示名）
                if hasattr(plugin_info, 'category_group') and plugin_info.category_group:
                    identifier_to_display_name[plugin_info.name] = plugin_info.category_group
                    print(f"  {plugin_info.name:30s} → {plugin_info.category_group}")
        
        print(f"\n映射表共 {len(identifier_to_display_name)} 项\n")
        
        if not plugins_to_load:
            return set()
        
        # 先加载到节点库的Graph（用于UI显示）
        if self.main_window.nodes_palette and plugins_to_load:
            try:
                # 使用保存的temp_graph引用，确保注册到正确的Graph
                palette_graph = getattr(self.main_window, 'temp_graph', None)
                if palette_graph is None:
                    palette_graph = self.main_window.nodes_palette.node_graph
                
                print("="*80)
                print("【阶段2】注册节点到节点库 Graph")
                print("="*80)
                
                for plugin_info in plugins_to_load:
                    self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        palette_graph
                    )
                    for node_def in plugin_info.nodes:
                        new_categories.add(node_def.category)
                
                print(f"\n已注册 {len(new_categories)} 个节点分类\n")
                
                # 应用自定义标签页名称映射
                if identifier_to_display_name:
                    print("="*80)
                    print("【阶段3】应用 category_group 重命名标签页")
                    print("="*80)
                    self._apply_custom_tab_names(identifier_to_display_name)
                else:
                    print("\n⚠️ 映射表为空，跳过重命名\n")
            except Exception as e:
                import traceback
                traceback.print_exc()
        
        # 再加载到工作流Graph（用于实际执行）
        for plugin_info in plugins_to_load:
            self.plugin_manager.load_plugin_nodes(
                plugin_info.name,
                node_graph
            )
        
        # 清除待加载标记，避免重复加载
        delattr(self.main_window, '_pending_plugins')
        
        return new_categories
    
    def _apply_custom_tab_names(self, identifier_to_display_name):
        """
        应用自定义标签页名称映射
        
        Args:
            identifier_to_display_name: dict, 标识符到显示名称的映射
        """
        if not self.main_window.nodes_palette:
            print("❌ nodes_palette 不存在")
            return
        
        try:
            tab_widget = self.main_window.nodes_palette.tab_widget()
            
            if not tab_widget:
                print("❌ tab_widget 为 None")
                return
            
            print(f"\n当前标签页数量: {tab_widget.count()}")
            print("\n重命名前:")
            for i in range(tab_widget.count()):
                print(f"  [{i}] {tab_widget.tabText(i)}")
            
            # 遍历所有标签页，根据映射修改名称
            renamed_count = 0
            for i in range(tab_widget.count()):
                current_name = tab_widget.tabText(i)
                
                # 查找是否有匹配的映射
                for identifier, display_name in identifier_to_display_name.items():
                    if current_name == identifier:
                        tab_widget.setTabText(i, display_name)
                        print(f"  ✅ {identifier:30s} → {display_name}")
                        renamed_count += 1
                        break
            
            print(f"\n重命名后:")
            for i in range(tab_widget.count()):
                print(f"  [{i}] {tab_widget.tabText(i)}")
            
            print(f"\n共重命名 {renamed_count}/{tab_widget.count()} 个标签页\n")
            print("="*80 + "\n")
                    
        except Exception as e:
            print(f"❌ 重命名失败: {e}")
            import traceback
            traceback.print_exc()
