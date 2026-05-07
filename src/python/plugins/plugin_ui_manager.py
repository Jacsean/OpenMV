"""
插件UI管理器

负责处理与插件相关的UI交互逻辑，包括：
- 插件加载到NodeGraph
- 节点库面板刷新
- 插件安装/卸载/管理的对话框交互
- 插件重新扫描和热重载

本模块已重构为事件驱动：
- 通过 EventBus 发布事件通知插件加载状态变更
- UI响应逻辑由订阅者处理
"""

from PySide2 import QtWidgets, QtCore
from pathlib import Path
import json
import utils
from utils import logger

from core.event_bus import event_bus, Events


class PluginUIManager:
    """
    插件UI管理器

    职责：
    - 处理插件相关的UI交互
    - 发布事件而非直接操作UI
    - 管理插件加载、节点库更新

    事件发布：
    - PLUGIN_SCANNED: 插件扫描完成
    - PLUGIN_LOADED: 插件加载完成
    - PLUGIN_INSTALL: 插件安装请求
    - PLUGIN_UNINSTALL: 插件卸载请求
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
        utils.logger.info("\n" + "=" * 60, module="plugin_ui_manager")
        utils.logger.info("🔧 PluginUIManager.load_plugins_to_graph 开始执行", module="plugin_ui_manager")
        utils.logger.info("=" * 60, module="plugin_ui_manager")

        if not hasattr(self.main_window, '_pending_plugins'):
            utils.logger.warning("⚠️ main_window没有_pending_plugins属性", module="plugin_ui_manager")
            return set()

        if not self.main_window._pending_plugins:
            utils.logger.warning("⚠️ _pending_plugins为空列表", module="plugin_ui_manager")
            return set()

        utils.logger.info(f"📦 待加载插件数: {len(self.main_window._pending_plugins)}", module="plugin_ui_manager")

        new_categories = set()
        identifier_to_display_name = {}

        plugins_to_load = []
        for plugin_info in self.main_window._pending_plugins:
            if plugin_info.enabled:
                plugins_to_load.append(plugin_info)
                if hasattr(plugin_info, 'category_group') and plugin_info.category_group:
                    identifier_to_display_name[plugin_info.name] = plugin_info.category_group

        utils.logger.success(f"✅ 启用的插件数: {len(plugins_to_load)}", module="plugin_ui_manager")

        if not plugins_to_load:
            utils.logger.warning("⚠️ 没有启用的插件需要加载", module="plugin_ui_manager")
            return set()

        utils.logger.info(f"\n📊 步骤1: 加载到节点库Graph", module="plugin_ui_manager")
        utils.logger.info(f"   nodes_palette存在: {self.main_window.nodes_palette is not None}", module="plugin_ui_manager")
        utils.logger.info(f"   temp_graph存在: {hasattr(self.main_window, 'temp_graph')}", module="plugin_ui_manager")

        if self.main_window.nodes_palette and plugins_to_load:
            try:
                palette_graph = getattr(self.main_window, 'temp_graph', None)
                utils.logger.info(f"   palette_graph获取结果: {palette_graph is not None}", module="plugin_ui_manager")

                if palette_graph is None:
                    palette_graph = self.main_window.nodes_palette.node_graph
                    utils.logger.info(f"   回退到nodes_palette.node_graph: {palette_graph is not None}", module="plugin_ui_manager")

                utils.logger.info(f"   开始注册 {len(plugins_to_load)} 个插件到节点库Graph...", module="plugin_ui_manager")

                for plugin_info in plugins_to_load:
                    utils.logger.info(f"   📌 加载插件: {plugin_info.name} ({len(plugin_info.nodes)} 个节点)", module="plugin_ui_manager")
                    success = self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        palette_graph
                    )
                    if success:
                        for node_def in plugin_info.nodes:
                            new_categories.add(node_def.category)
                            utils.logger.success(f"      ✅ 节点: {node_def.display_name} (category={node_def.category})", module="plugin_ui_manager")
                    else:
                        utils.logger.error(f"      ❌ 插件加载失败: {plugin_info.name}", module="plugin_ui_manager")

                utils.logger.success(f"   ✅ 节点库Graph加载完成，共 {len(new_categories)} 个分类", module="plugin_ui_manager")

                if identifier_to_display_name:
                    utils.logger.info(f"   🏷️ 应用自定义标签页名称映射 ({len(identifier_to_display_name)} 个)", module="plugin_ui_manager")
                    self._apply_custom_tab_names(identifier_to_display_name)

                utils.logger.info(f"   📋 应用自定义标签页顺序", module="plugin_ui_manager")
                self._apply_custom_tab_order()

            except Exception as e:
                utils.logger.error(f"   ❌ 加载到节点库Graph时发生异常: {e}", module="plugin_ui_manager")
                import traceback
                traceback.print_exc()
        else:
            utils.logger.warning(f"   ⚠️ 跳过节点库Graph加载 (nodes_palette={self.main_window.nodes_palette is not None}, plugins_to_load={len(plugins_to_load)})", module="plugin_ui_manager")

        utils.logger.info(f"\n📊 步骤2: 加载到工作流Graph", module="plugin_ui_manager")
        for plugin_info in plugins_to_load:
            utils.logger.info(f"   📌 加载插件到工作流: {plugin_info.name}", module="plugin_ui_manager")
            self.plugin_manager.load_plugin_nodes(
                plugin_info.name,
                node_graph
            )

        utils.logger.info(f"\n🗑️ 清除_pending_plugins标记", module="plugin_ui_manager")
        delattr(self.main_window, '_pending_plugins')

        if hasattr(self.main_window, 'refresh_node_info_event_filters'):
            utils.logger.info(f"🔄 刷新节点库事件过滤器", module="plugin_ui_manager")
            self.main_window.refresh_node_info_event_filters()

        event_bus.publish(Events.PLUGIN_LOADED, plugins=plugins_to_load, categories=new_categories)

        utils.logger.success(f"\n✅ load_plugins_to_graph执行完成", module="plugin_ui_manager")
        utils.logger.info("=" * 60 + "\n", module="plugin_ui_manager")

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

            for i in range(tab_widget.count()):
                current_name = tab_widget.tabText(i)

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

            category_to_index = {}
            for i in range(tab_widget.count()):
                tab_text = tab_widget.tabText(i)
                category_to_index[tab_text] = i

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

            while tab_widget.count() > 0:
                tab_widget.removeTab(0)

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
