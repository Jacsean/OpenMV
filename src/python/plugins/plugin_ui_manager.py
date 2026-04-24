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
            print("⚠️ 警告：_pending_plugins 属性不存在")
            return set()
        
        if not self.main_window._pending_plugins:
            print("⚠️ 警告：_pending_plugins 为空列表")
            return set()
        
        print("\n🔌 加载插件节点到NodeGraph...")
        print(f"   待加载插件数量: {len(self.main_window._pending_plugins)}")
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
            print("⚠️ 没有启用的插件需要加载")
            return set()
        
        print(f"   启用的插件: {[p.name for p in plugins_to_load]}")
        
        # 先加载到节点库的Graph（用于UI显示）
        if self.main_window.nodes_palette and plugins_to_load:
            try:
                # 使用保存的temp_graph引用，确保注册到正确的Graph
                palette_graph = getattr(self.main_window, 'temp_graph', None)
                if palette_graph is None:
                    # 降级方案：尝试从nodes_palette获取
                    palette_graph = self.main_window.nodes_palette.node_graph
                    print("⚠️ 使用nodes_palette.node_graph（可能不是预期的Graph）")
                else:
                    print("✅ 使用temp_graph引用")
                
                print(f"   节点库Graph ID: {id(palette_graph)}")
                print(f"   工作流Graph ID: {id(node_graph)}")
                print(f"   是否为同一对象: {palette_graph is node_graph}")
                
                for plugin_info in plugins_to_load:
                    print(f"\n   📦 加载插件: {plugin_info.name}")
                    self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        palette_graph
                    )
                    for node_def in plugin_info.nodes:
                        new_categories.add(node_def.category)
                        
                print(f"\n✅ 已注册 {len(new_categories)} 个分类到节点库")
                
                # 应用自定义标签页名称映射
                if identifier_to_display_name:
                    print(f"\n🔍 准备应用标签页名称映射...")
                    print(f"   映射表内容: {identifier_to_display_name}")
                    self._apply_custom_tab_names(identifier_to_display_name)
                else:
                    print(f"\n⚠️ 跳过标签页重命名：映射表为空")
            except Exception as e:
                print(f"⚠️ 加载到节点库失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ 跳过节点库加载：nodes_palette 不存在或没有插件")
            if not self.main_window.nodes_palette:
                print("   原因：nodes_palette 为 None")
        
        # 再加载到工作流Graph（用于实际执行）
        print(f"\n   🔄 加载到工作流Graph...")
        for plugin_info in plugins_to_load:
            success = self.plugin_manager.load_plugin_nodes(
                plugin_info.name,
                node_graph
            )
            if success:
                print(f"   ✅ 插件加载成功: {plugin_info.name}")
            else:
                print(f"   ❌ 插件加载失败: {plugin_info.name}")
        
        # 清除待加载标记，避免重复加载
        delattr(self.main_window, '_pending_plugins')
        
        # 提示用户关于NodeGraphQt限制
        if new_categories:
            print(f"\n💡 新增分类: {', '.join(sorted(new_categories))}")
            print(f"   ✅ 节点功能完全可用，可直接拖拽使用")
            
            # 尝试刷新节点库面板
            self.refresh_nodes_palette()
        
        return new_categories
    
    def _apply_custom_tab_names(self, identifier_to_display_name):
        """
        应用自定义标签页名称映射
        
        Args:
            identifier_to_display_name: dict, 标识符到显示名称的映射
        """
        print(f"\n{'='*80}")
        print(f"🏷️  [_apply_custom_tab_names] 开始执行")
        print(f"{'='*80}")
        print(f"   输入映射表: {identifier_to_display_name}")
        
        if not self.main_window.nodes_palette:
            print("⚠️ 跳过标签页重命名：nodes_palette 不存在")
            print(f"   nodes_palette 值: {self.main_window.nodes_palette}")
            return
        
        print(f"✅ nodes_palette 存在")
        print(f"   类型: {type(self.main_window.nodes_palette)}")
        print(f"   是否有 tab_widget 方法: {hasattr(self.main_window.nodes_palette, 'tab_widget')}")
        
        try:
            # tab_widget是方法而非属性，需要调用
            tab_widget = self.main_window.nodes_palette.tab_widget()
            
            print(f"✅ tab_widget() 调用成功")
            print(f"   返回对象类型: {type(tab_widget)}")
            print(f"   是否为 QTabWidget: {tab_widget.__class__.__name__ == 'QTabWidget'}")
            
            if not tab_widget:
                print("⚠️ 跳过标签页重命名：tab_widget() 返回 None")
                return
            
            print(f"\n📊 当前标签页状态:")
            print(f"   标签页数量: {tab_widget.count()}")
            
            if tab_widget.count() == 0:
                print("⚠️ 警告：当前没有任何标签页！")
                print("   可能原因：节点尚未注册到Graph，或NodeGraphQt未自动创建标签页")
                return
            
            # 遍历所有标签页，根据映射修改名称
            renamed_count = 0
            for i in range(tab_widget.count()):
                current_name = tab_widget.tabText(i)
                print(f"   [{i}] 当前标签名: '{current_name}'")
                
                # 查找是否有匹配的映射
                for identifier, display_name in identifier_to_display_name.items():
                    # NodeGraphQt使用__identifier__作为标签页名称
                    if current_name == identifier:
                        print(f"      ✅ 找到匹配，准备重命名...")
                        tab_widget.setTabText(i, display_name)
                        new_name = tab_widget.tabText(i)
                        print(f"      ✅ 重命名完成: '{identifier}' → '{display_name}' (验证: '{new_name}')")
                        renamed_count += 1
                        break
                else:
                    print(f"      ℹ️  无匹配映射，保持原名")
            
            print(f"\n✅ 共重命名 {renamed_count} 个标签页")
            print(f"{'='*80}\n")
                    
        except AttributeError as e:
            print(f"❌ AttributeError: {e}")
            print(f"   nodes_palette类型: {type(self.main_window.nodes_palette)}")
            print(f"   nodes_palette可用属性: {[attr for attr in dir(self.main_window.nodes_palette) if not attr.startswith('_')][:30]}")
        except Exception as e:
            print(f"❌ 应用自定义标签名失败: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_nodes_palette(self):
        """
        刷新节点库面板以显示新注册的节点
        
        由于NodeGraphQt限制，需要重新创建NodesPaletteWidget
        """
        if not self.main_window.nodes_palette or not hasattr(self.main_window, 'current_node_graph'):
            return
        
        try:
            print("🔄 正在刷新节点库面板...")
            
            # 获取当前停靠窗口的位置
            parent_dock = self.main_window.nodes_palette.parent()
            dock_area = self.main_window.dockWidgetArea(parent_dock) if parent_dock else QtCore.Qt.LeftDockWidgetArea
            
            # 删除旧的节点库dock
            if parent_dock:
                self.main_window.removeDockWidget(parent_dock)
                parent_dock.deleteLater()
            
            # 用当前工作流的Graph重新创建节点库
            from NodeGraphQt import NodesPaletteWidget
            self.main_window.nodes_palette = NodesPaletteWidget(node_graph=self.main_window.current_node_graph)
            self.main_window.nodes_palette.setWindowTitle("节点库")
            
            # 设置标签位置
            try:
                tab_widget = self.main_window.nodes_palette.tab_widget()
                if hasattr(tab_widget, 'setTabPosition'):
                    tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
            except Exception:
                pass
            
            # 重新添加到停靠窗口
            dock_nodes = QtWidgets.QDockWidget("节点库", self.main_window)
            dock_nodes.setWidget(self.main_window.nodes_palette)
            self.main_window.addDockWidget(dock_area, dock_nodes)
            
            print("✅ 节点库面板已刷新")
            
        except Exception as e:
            print(f"⚠️ 刷新节点库失败: {e}")
            import traceback
            traceback.print_exc()
    
    def auto_categorize_nodes(self, categories):
        """
        自动将节点归类到对应的分类标签页
        
        Args:
            categories: 分类名称集合
        """
        if not self.main_window.nodes_palette:
            print("⚠️ 节点库面板未初始化")
            return
        
        try:
            tab_widget = self.main_window.nodes_palette.tab_widget()
            if not tab_widget:
                print("⚠️ 无法获取标签页控件")
                return
            
            # 获取现有分类
            existing_categories = set()
            for i in range(tab_widget.count()):
                existing_categories.add(tab_widget.tabText(i))
            
            # 检查新分类
            new_cats = categories - existing_categories
            if new_cats:
                print(f"\n   ⚠️  {len(new_cats)} 个新分类需要重启应用才能在节点库中显示：")
                for cat in sorted(new_cats):
                    print(f"      • {cat}")
                    
        except Exception as e:
            print(f"⚠️ 自动归类失败: {e}")
    
    def open_node_editor(self):
        """
        打开节点编辑器
        """
        from ui.node_editor import NodeEditorDialog
        from pathlib import Path
        
        # 获取插件目录路径
        plugins_dir = Path(__file__).parent.parent / "user_plugins"
        
        # 创建并显示节点编辑器（非模态）
        editor = NodeEditorDialog(self.main_window, plugins_dir)
        editor.show()
    
    def install_plugin_from_ui(self):
        """
        从ZIP文件安装插件（UI触发）
        
        Returns:
            tuple: (success: bool, message: str)
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window,
            "选择插件ZIP文件",
            "",
            "插件文件 (*.zip);;所有文件 (*)"
        )
        
        if not file_path:
            return False, "用户取消操作"
        
        print(f"\n📦 开始安装插件: {file_path}")
        
        # 执行安装
        success, message = self.plugin_manager.install_plugin_from_zip(file_path)
        
        if success:
            QtWidgets.QMessageBox.information(
                self.main_window,
                "安装成功",
                f"{message}\n\n请重启程序以加载新插件。"
            )
            print(f"✅ {message}")
        else:
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "安装失败",
                message
            )
            print(f"❌ {message}")
        
        return success, message
    
    def manage_plugins_dialog(self):
        """
        显示插件管理对话框
        """
        plugins = self.plugin_manager.get_installed_plugins()
        
        if not plugins:
            QtWidgets.QMessageBox.information(
                self.main_window,
                "插件管理",
                "当前没有安装任何插件。"
            )
            return
        
        # 构建插件列表信息
        info_text = "已安装的插件:\n\n"
        for plugin in plugins:
            info_text += f"📦 {plugin.name} v{plugin.version}\n"
            info_text += f"   作者: {plugin.author}\n"
            info_text += f"   描述: {plugin.description}\n"
            info_text += f"   节点数: {len(plugin.nodes)}\n"
            info_text += f"   状态: {'✅ 已启用' if plugin.enabled else '❌ 已禁用'}\n"
            info_text += "\n"
        
        # 创建对话框
        dialog = QtWidgets.QDialog(self.main_window)
        dialog.setWindowTitle("插件管理")
        dialog.setMinimumWidth(600)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # 文本显示
        text_edit = QtWidgets.QTextEdit()
        text_edit.setPlainText(info_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        uninstall_btn = QtWidgets.QPushButton("卸载选中插件")
        uninstall_btn.clicked.connect(lambda: self._uninstall_selected_plugin(dialog))
        button_layout.addWidget(uninstall_btn)
        
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def _uninstall_selected_plugin(self, dialog):
        """
        卸载选中的插件（简化版：弹出输入框）
        
        Args:
            dialog: 插件管理对话框
        """
        plugin_name, ok = QtWidgets.QInputDialog.getText(
            self.main_window,
            "卸载插件",
            "请输入要卸载的插件名称:"
        )
        
        if ok and plugin_name:
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认卸载",
                f"确定要卸载插件 '{plugin_name}' 吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                success, message = self.plugin_manager.uninstall_plugin(plugin_name)
                
                if success:
                    QtWidgets.QMessageBox.information(self.main_window, "成功", message)
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.critical(self.main_window, "失败", message)
    
    def reload_plugins_from_ui(self):
        """
        重新扫描并加载插件（UI触发）
        """
        print("\n🔄 重新扫描插件...")
        
        # 停止所有热重载监听
        self.plugin_manager.hot_reloader.stop_all()
        
        # 重新扫描
        plugins = self.plugin_manager.scan_plugins()
        
        print(f"✅ 扫描到 {len(plugins)} 个插件")
        
        # 重新加载到当前NodeGraph
        if self.main_window.current_node_graph:
            for plugin_info in plugins:
                if plugin_info.enabled:
                    self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        self.main_window.current_node_graph
                    )
        
        QtWidgets.QMessageBox.information(
            self.main_window,
            "刷新完成",
            f"已重新加载 {len(plugins)} 个插件。\n\n注意：UI分类可能需要重启程序才能完全更新。"
        )
