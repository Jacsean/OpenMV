"""
插件UI管理器

负责处理与插件相关的UI交互逻辑，包括：
- 插件加载到NodeGraph
- 节点库面板刷新
- 插件安装/卸载/管理的对话框交互
- 插件重新扫描和热重载
"""

from PySide2 import QtWidgets, QtCore
from pathlib import Path
import json


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
        
        if not plugins_to_load:
            return set()
        
        # 先加载到节点库的Graph（用于UI显示）
        if self.main_window.nodes_palette and plugins_to_load:
            try:
                # 使用保存的temp_graph引用，确保注册到正确的Graph
                palette_graph = getattr(self.main_window, 'temp_graph', None)
                if palette_graph is None:
                    palette_graph = self.main_window.nodes_palette.node_graph
                
                for plugin_info in plugins_to_load:
                    self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        palette_graph
                    )
                    for node_def in plugin_info.nodes:
                        new_categories.add(node_def.category)
                
                # 应用自定义标签页名称映射
                if identifier_to_display_name:
                    self._apply_custom_tab_names(identifier_to_display_name)
                
                # 应用自定义标签页顺序
                self._apply_custom_tab_order()
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
        
        # 刷新节点库的事件过滤器（使新加载的插件标签页也能响应点击）
        if hasattr(self.main_window, 'refresh_node_info_event_filters'):
            self.main_window.refresh_node_info_event_filters()
        
        return new_categories
    
    def _apply_custom_tab_names(self, identifier_to_display_name):
        """
        应用自定义标签页名称映射
        
        Args:
            identifier_to_display_name: dict, 标识符到显示名称的映射
        """
        if not self.main_window.nodes_palette:
            return
        
        try:
            tab_widget = self.main_window.nodes_palette.tab_widget()
            
            if not tab_widget:
                return
            
            # 遍历所有标签页，根据映射修改名称
            for i in range(tab_widget.count()):
                current_name = tab_widget.tabText(i)
                
                # 查找是否有匹配的映射
                for identifier, display_name in identifier_to_display_name.items():
                    if current_name == identifier:
                        tab_widget.setTabText(i, display_name)
                        break
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _apply_custom_tab_order(self):
        """
        应用自定义标签页顺序
        
        从 workspace/tab_order.json 读取用户定义的顺序，并重新排列标签页
        """
        if not self.main_window.nodes_palette:
            return
        
        try:
            # 加载保存的顺序
            config_file = Path(__file__).parent.parent / "workspace" / "tab_order.json"
            if not config_file.exists():
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_order = json.load(f)
            
            if not custom_order:
                return
            
            tab_widget = self.main_window.nodes_palette.tab_widget()
            if not tab_widget:
                return
            
            # 构建 category_group 到索引的映射
            category_to_index = {}
            for i in range(tab_widget.count()):
                tab_text = tab_widget.tabText(i)
                category_to_index[tab_text] = i
            
            # 按照自定义顺序重新排列标签页
            # QTabWidget 不支持直接移动，需要通过移除再添加的方式
            tabs_data = []
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                tab_text = tab_widget.tabText(i)
                icon = tab_widget.tabIcon(i)
                tooltip = tab_widget.tabToolTip(i)
                tabs_data.append({
                    'widget': widget,
                    'text': tab_text,
                    'icon': icon,
                    'tooltip': tooltip
                })
            
            # 清除所有标签页
            while tab_widget.count() > 0:
                tab_widget.removeTab(0)
            
            # 按自定义顺序添加标签页
            # 首先添加自定义顺序中的标签页
            added_indices = set()
            for category_group in custom_order:
                if category_group in category_to_index:
                    idx = category_to_index[category_group]
                    if idx < len(tabs_data):
                        data = tabs_data[idx]
                        tab_index = tab_widget.addTab(data['widget'], data['icon'], data['text'])
                        if data['tooltip']:
                            tab_widget.setTabToolTip(tab_index, data['tooltip'])
                        added_indices.add(idx)
            
            # 然后添加未在自定义顺序中的标签页（保持原有顺序）
            for i, data in enumerate(tabs_data):
                if i not in added_indices:
                    tab_index = tab_widget.addTab(data['widget'], data['icon'], data['text'])
                    if data['tooltip']:
                        tab_widget.setTabToolTip(tab_index, data['tooltip'])
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def open_node_editor(self):
        """
        打开节点编辑器对话框
        """
        from ui.node_editor import NodeEditorDialog
        
        plugins_dir = Path(__file__).parent.parent / "user_plugins"
        dialog = NodeEditorDialog(parent=self.main_window, plugins_dir=plugins_dir)
        dialog.exec_()
