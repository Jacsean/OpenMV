"""
图形化视觉编程系统 - 主窗口

v3.0更新:
- 支持多工作流管理（QTabWidget）
- 集成ProjectManager工程管理
- 每个标签页独立的NodeGraph实例

v4.0更新:
- 集成插件系统
- 支持动态加载插件节点
- 节点完全插件化（6大分类体系）

v4.1更新:
- 模块化重构：将业务逻辑分离到专门的管理器
- PluginUIManager: 插件相关UI交互
- ProjectUIManager: 工程/工作流相关UI交互
- ExecutionUIManager: 执行相关UI交互
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide2 import QtWidgets, QtCore, QtGui
from NodeGraphQt import NodeGraph, NodesPaletteWidget, PropertiesBinWidget

# 导入核心引擎和工程管理
from core.graph_engine import GraphEngine
from core.project_manager import project_manager
from core.project_ui_manager import ProjectUIManager
from core.execution_ui_manager import ExecutionUIManager

# 导入插件管理器
from plugins.plugin_manager import PluginManager
from plugins.plugin_ui_manager import PluginUIManager

# 导入图像预览对话框
from ui.image_preview import ImagePreviewDialog


class MainWindow(QtWidgets.QMainWindow):
    """
    主窗口类（v4.1 - 模块化版本）
    
    特性:
    - 使用QTabWidget管理多个工作流
    - 每个标签页独立的NodeGraph实例
    - 共享节点库和属性面板
    - 集成ProjectManager工程管理
    - 模块化设计：业务逻辑委托给专门的管理器
    """
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 设置窗口属性
        self.setWindowTitle("图形化视觉处理系统 v4.1")
        self.setGeometry(0, 0, 1600, 1024)
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager()
        
        # 初始化工程管理器
        self.project_manager = project_manager
        
        # 创建执行引擎
        self.engine = GraphEngine()
        
        # 创建UI管理器（模块化）
        self.plugin_ui = PluginUIManager(self.plugin_manager, self)
        self.project_ui = ProjectUIManager(self.project_manager, self)
        self.execution_ui = ExecutionUIManager(self.engine, self)
        
        # 管理打开的预览窗口（用于刷新）
        self.preview_windows = {}  # {node_id: ImagePreviewDialog}
        
        # UI组件引用（将在_setup_ui中创建）
        self.tab_widget = None
        self.nodes_palette = None
        self.properties_bin = None
        
        # 当前激活的NodeGraph（动态更新）
        self.current_node_graph = None
        
        # 加载插件（仅扫描元数据，不注册节点）
        self._load_plugins()

        # 创建UI组件（必须先于工程初始化，因为需要 tab_widget）
        self._setup_ui()        
        
        # 创建默认工程和工作流（此时 UI 已就绪）
        self.project_ui.initialize_default_project()
   
        
    def _load_plugins(self):
        """
        加载所有已安装的插件（简化版：仅扫描，延迟加载）
        """
        print("\n" + "=" * 60)
        print("正在加载插件...")
        print("=" * 60)
        
        # 扫描插件
        plugins = self.plugin_manager.scan_plugins()
        print(f"发现 {len(plugins)} 个插件\n")
        
        if not plugins:
            print("💡 提示: 将插件文件夹放入 user_plugins/ 目录即可自动加载\n")
            print("=" * 60 + "\n")
            return
        
        # 由于此时还没有NodeGraph实例，延迟到第一个工作流创建时加载
        # 这里只记录需要加载的插件
        self._pending_plugins = plugins
        print(f"📦 待加载插件: {', '.join([p.name for p in plugins])}")
        print("=" * 60 + "\n")
    
    def _register_nodes(self, node_graph):
        """
        为指定的NodeGraph注册节点类型（已废弃，改用插件系统）
        
        Args:
            node_graph: NodeGraph实例
        
        Note:
            所有节点现在通过插件系统动态加载
            此方法保留仅用于兼容性，不再注册任何节点
        """
        pass
    
    def _add_workflow_tab(self, workflow):
        """
        添加工作流标签页（委托给ProjectUIManager）
        
        Args:
            workflow: Workflow对象
        """
        self.project_ui.add_workflow_tab(workflow)
        
    def _remove_workflow_tab(self, index):
        """
        移除工作流标签页（委托给ProjectUIManager）
        
        Args:
            index: 标签页索引
        """
        self.project_ui.remove_workflow_tab(index)
            
    def _on_tab_changed(self, index):
        """
        标签页切换时的回调（委托给ProjectUIManager）
        
        Args:
            index: 新的标签页索引
        """
        self.project_ui.on_tab_changed(index)
        
    def _setup_ui(self):
        """
        设置用户界面（v3.0 - 多标签页版本）
        """
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === 标签页容器 ===
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)  # 允许关闭标签页
        self.tab_widget.setMovable(True)       # 允许拖动排序
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)
        
        # 创建临时NodeGraph用于初始化共享组件
        temp_graph = NodeGraph()
        self._register_nodes(temp_graph)
        
        # 保存临时Graph引用，用于后续插件节点注册
        self.temp_graph = temp_graph
        
        # === 左侧：节点库面板（共享）===
        self.nodes_palette = NodesPaletteWidget(node_graph=temp_graph)
        self.nodes_palette.setWindowTitle("节点库")
        
        # 设置标签位置为右侧显示
        try:
            tab_widget = self.nodes_palette.tab_widget()
            if hasattr(tab_widget, 'setTabPosition'):
                tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        except (AttributeError, TypeError):
            if hasattr(self.nodes_palette, 'tab_widget'):
                self.nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        
        dock_nodes = QtWidgets.QDockWidget("节点库", self)
        dock_nodes.setWidget(self.nodes_palette)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_nodes)
        
        # === 左侧下方：节点说明面板 ===
        self.node_info_panel = self._create_node_info_panel()
        dock_info = QtWidgets.QDockWidget("节点说明", self)
        dock_info.setWidget(self.node_info_panel)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_info)
        
        # 连接节点库的选择信号到说明面板
        self._connect_node_selection_signal()
        
        # === 右侧：属性面板（共享）===
        self.properties_bin = PropertiesBinWidget(node_graph=temp_graph)
        self.properties_bin.setWindowTitle("属性面板")
        dock_properties = QtWidgets.QDockWidget("属性面板", self)
        dock_properties.setWidget(self.properties_bin)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_properties)
        
        # 设置当前NodeGraph
        self.current_node_graph = temp_graph
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建菜单栏
        self._create_menu_bar()
    
    def _create_node_info_panel(self):
        """
        创建节点说明面板
        
        Returns:
            QtWidgets.QWidget: 节点说明面板组件
        """
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 标题
        title_label = QtWidgets.QLabel("📋 节点说明")
        title_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addWidget(title_label)
        
        # 分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)
        
        # 节点名称
        self.info_name_label = QtWidgets.QLabel("未选择节点")
        self.info_name_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        self.info_name_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.info_name_label)
        
        # 节点分类
        self.info_category_label = QtWidgets.QLabel("")
        self.info_category_label.setFont(QtGui.QFont("Arial", 8))
        self.info_category_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.info_category_label)
        
        # 说明文本框（只读）
        self.info_text = QtWidgets.QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QtGui.QFont("Consolas", 9))
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.info_text.setPlaceholderText("点击节点库中的节点查看说明...")
        layout.addWidget(self.info_text)
        
        # 占位符，让文本框填充剩余空间
        layout.addStretch()
        
        return panel
    
    def _connect_node_selection_signal(self):
        """
        连接节点库的选择信号到说明面板更新函数
        
        由于 NodeGraphQt 的 NodesPaletteWidget 没有公开的节点选择信号，
        我们采用事件过滤器的方式监听鼠标点击事件
        """
        try:
            # 获取 tab_widget
            tab_widget = self.nodes_palette.tab_widget()
            
            if tab_widget:
                print(f"🔍 开始为 {tab_widget.count()} 个标签页安装事件过滤器")
                # 为每个标签页的内容widget安装事件过滤器
                for i in range(tab_widget.count()):
                    widget = tab_widget.widget(i)
                    if widget:
                        widget.installEventFilter(self)
                        print(f"   ✅ 已为标签页 {i} ({tab_widget.tabText(i)}) 安装事件过滤器")
                        
        except Exception as e:
            print(f"⚠️ 连接节点选择信号失败: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_node_info_event_filters(self):
        """
        刷新节点库的事件过滤器（在插件加载后调用）
        """
        # 先移除旧的事件过滤器
        try:
            tab_widget = self.nodes_palette.tab_widget()
            if tab_widget:
                for i in range(tab_widget.count()):
                    widget = tab_widget.widget(i)
                    if widget:
                        widget.removeEventFilter(self)
                
                # 重新安装
                self._connect_node_selection_signal()
        except Exception as e:
            print(f"⚠️ 刷新事件过滤器失败: {e}")
    
    def eventFilter(self, obj, event):
        """
        事件过滤器 - 捕获节点库中的鼠标点击事件
        
        Args:
            obj: 事件目标对象
            event: 事件对象
            
        Returns:
            bool: 是否拦截事件
        """
        from PySide2.QtCore import QEvent
        
        # 监听鼠标按下事件
        if event.type() == QEvent.MouseButtonPress:
            # 检查是否是节点库中的组件
            if hasattr(obj, 'parent') and obj.parent():
                parent = obj.parent()
                # 尝试从父级追溯到 nodes_palette
                depth = 0
                while parent and depth < 10:
                    if parent == self.nodes_palette:
                        # 这是节点库中的点击事件
                        print(f"🖱️ 检测到节点库点击事件 (深度={depth})")
                        # 延迟获取选中的节点信息（因为点击后才会更新选中状态）
                        QtCore.QTimer.singleShot(50, self._update_node_info_from_selection)
                        break
                    parent = parent.parent() if hasattr(parent, 'parent') else None
                    depth += 1
        
        return False  # 不拦截事件，让事件继续传递
    
    def _update_node_info_from_selection(self):
        """
        从节点库的当前选中状态更新说明面板
        """
        try:
            print("🔄 开始更新节点信息...")
            # 获取 tab_widget
            tab_widget = self.nodes_palette.tab_widget()
            if not tab_widget:
                print("   ❌ 无法获取 tab_widget")
                return
            
            print(f"   📋 检查 {tab_widget.count()} 个标签页")
            # 遍历所有标签页，查找选中的项
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if widget and hasattr(widget, 'selectedItems'):
                    selected = widget.selectedItems()
                    if selected:
                        # 找到了选中的项
                        print(f"   ✅ 在标签页 {i} 中找到 {len(selected)} 个选中项")
                        item = selected[0]
                        if hasattr(item, 'text'):
                            node_name = item.text(0) if hasattr(item, 'text') else str(item)
                            print(f"   📌 选中节点名称: {node_name}")
                            # 尝试从 plugin_manager 获取节点详细信息
                            self._display_node_info_by_name(node_name)
                            return
                        else:
                            print(f"   ⚠️ 选中项没有 text 属性: {type(item)}")
            
            print("   ⚠️ 未找到任何选中项")
                        
        except Exception as e:
            print(f"   ❌ 更新节点信息失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_node_info_by_name(self, node_display_name):
        """
        根据节点显示名称查找并显示节点信息
        
        Args:
            node_display_name: 节点的显示名称
        """
        try:
            print(f"🔎 查找节点: {node_display_name}")
            # 从 plugin_manager 中查找匹配的节点
            if hasattr(self, 'plugin_manager') and self.plugin_manager:
                print(f"   📦 检查 {len(self.plugin_manager.plugins)} 个插件")
                for plugin_name, plugin_info in self.plugin_manager.plugins.items():
                    for node_def in plugin_info.nodes:
                        if node_def.display_name == node_display_name:
                            # 找到匹配的节点，显示信息
                            print(f"   ✅ 找到匹配节点: {plugin_name}.{node_def.class_name}")
                            description = ""
                            # 尝试从已加载的节点类中获取描述
                            node_key = f"{plugin_name}.{node_def.class_name}"
                            if node_key in self.plugin_manager.loaded_nodes:
                                node_class = self.plugin_manager.loaded_nodes[node_key]
                                if hasattr(node_class, '_node_description'):
                                    description = node_class._node_description
                                    print(f"   📝 获取到描述信息 ({len(description)} 字符)")
                                else:
                                    print(f"   ⚠️ 节点类没有 _node_description 属性")
                            else:
                                print(f"   ⚠️ 节点未在 loaded_nodes 中注册")
                            
                            self.update_node_info(
                                node_class_name=node_def.class_name,
                                display_name=node_def.display_name,
                                category=node_def.category,
                                description=description
                            )
                            print(f"   ✅ 已更新节点说明面板")
                            return
            
            # 如果没找到详细信息，至少显示名称
            print(f"   ⚠️ 未在 plugin_manager 中找到节点信息")
            self.info_name_label.setText(f"🔹 {node_display_name}")
            self.info_category_label.setText("分类: 未知")
            self.info_text.setPlainText("暂无详细说明")
            
        except Exception as e:
            print(f"   ❌ 显示节点信息失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_node_info(self, node_class_name, display_name, category, description=""):
        """
        更新节点说明面板的内容
        
        Args:
            node_class_name: 节点类名
            display_name: 显示名称
            category: 分类
            description: 描述文本
        """
        self.info_name_label.setText(f"🔹 {display_name}")
        self.info_category_label.setText(f"分类: {category} | 类名: {node_class_name}")
        
        if description:
            self.info_text.setPlainText(description)
        else:
            self.info_text.setPlainText("暂无详细说明")
    
    def _on_node_selected_in_palette(self):
        """
        当在节点库中选择节点时调用
        """
        # 这里需要根据 NodesPaletteWidget 的实际实现来获取选中的节点信息
        # 暂时显示提示信息
        self.info_name_label.setText("节点选择功能开发中...")
        self.info_text.setPlainText("此功能需要与 NodesPaletteWidget 的内部实现集成")
    
    def _on_tab_close_requested(self, index):
        """
        标签页关闭请求（委托给ProjectUIManager）
        
        Args:
            index: 要关闭的标签页索引
        """
        self.project_ui.on_tab_close_requested(index)
        
    def _setup_context_menu(self):
        """
        设置节点右键菜单
        
        注意: NodeGraphQt的BaseNode不支持自定义右键菜单项
        文件选择功能通过以下方式实现:
        1. 直接在文本框中输入或粘贴路径
        2. 使用操作系统的"复制为路径"功能
        """
        pass
    
    def _create_toolbar(self):
        """
        创建工具栏（v4.1 - 模块化版本）
        """
        toolbar = self.addToolBar("主工具栏")
        
        # === 工程管理 ===
        new_project_action = QtWidgets.QAction("📄 新建", self)
        new_project_action.setStatusTip("创建新工程")
        new_project_action.triggered.connect(self.new_project)
        toolbar.addAction(new_project_action)
        
        open_project_action = QtWidgets.QAction("📂 打开", self)
        open_project_action.setStatusTip("打开工程(.proj)")
        open_project_action.triggered.connect(self.open_project)
        toolbar.addAction(open_project_action)
        
        save_project_action = QtWidgets.QAction("💾 保存", self)
        save_project_action.setStatusTip("保存工程为单文件")
        save_project_action.triggered.connect(self.save_project)
        toolbar.addAction(save_project_action)
        
        toolbar.addSeparator()
        
        # === 工作流管理 ===
        add_workflow_action = QtWidgets.QAction("➕ 添加工作流", self)
        add_workflow_action.setStatusTip("添加新的工作流")
        add_workflow_action.triggered.connect(self.add_new_workflow)
        toolbar.addAction(add_workflow_action)
        
        toolbar.addSeparator()
        
        # === 执行控制 ===
        run_action = QtWidgets.QAction("▶ 运行", self)
        run_action.setStatusTip("执行当前工作流")
        run_action.triggered.connect(self.run_graph)
        toolbar.addAction(run_action)
        
        run_all_action = QtWidgets.QAction("⏩ 运行全部", self)
        run_all_action.setStatusTip("执行所有工作流")
        run_all_action.triggered.connect(self.run_all_workflows)
        toolbar.addAction(run_all_action)
        
        clear_action = QtWidgets.QAction("🗑 清空", self)
        clear_action.setStatusTip("清空当前工作流")
        clear_action.triggered.connect(self.clear_graph)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        # === 视图控制 ===
        fit_all_action = QtWidgets.QAction("⊞ 适应", self)
        fit_all_action.setStatusTip("适应所有节点")
        fit_all_action.triggered.connect(self.fit_to_selection)
        toolbar.addAction(fit_all_action)
        
    def _create_menu_bar(self):
        """
        创建菜单栏（v4.1 - 模块化版本）
        """
        menubar = self.menuBar()
        
        # === 文件菜单 ===
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建工程
        new_project_action = QtWidgets.QAction("📄 新建工程", self)
        new_project_action.setShortcut("Ctrl+Shift+N")
        new_project_action.setStatusTip("创建新工程")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        # 打开工程
        open_project_action = QtWidgets.QAction("📂 打开工程", self)
        open_project_action.setShortcut("Ctrl+Shift+O")
        open_project_action.setStatusTip("打开已有工程")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        # 保存工程
        save_project_action = QtWidgets.QAction("💾 保存工程", self)
        save_project_action.setShortcut("Ctrl+Shift+S")
        save_project_action.setStatusTip("保存当前工程为单文件(.proj)")
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        # === 最近工程子菜单 ===
        recent_menu = file_menu.addMenu("📋 最近工程")
        self.recent_projects_menu = recent_menu  # 保存引用以便后续更新
        
        # 连接菜单显示信号以动态更新
        recent_menu.aboutToShow.connect(lambda: self._update_recent_projects_menu())
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QtWidgets.QAction("❌ 退出", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # === 工作流菜单 ===
        workflow_menu = menubar.addMenu("工作流(&W)")
        
        # 添加工作流
        add_workflow_action = QtWidgets.QAction("➕ 添加工作流", self)
        add_workflow_action.setShortcut("Ctrl+N")
        add_workflow_action.setStatusTip("添加新的工作流")
        add_workflow_action.triggered.connect(self.add_new_workflow)
        workflow_menu.addAction(add_workflow_action)
        
        # 关闭当前工作流
        close_workflow_action = QtWidgets.QAction("❌ 关闭当前工作流", self)
        close_workflow_action.setShortcut("Ctrl+W")
        close_workflow_action.setStatusTip("关闭当前工作流标签页")
        close_workflow_action.triggered.connect(self.close_current_workflow)
        workflow_menu.addAction(close_workflow_action)
        
        workflow_menu.addSeparator()
        
        # 重命名当前工作流
        rename_workflow_action = QtWidgets.QAction("✏️ 重命名", self)
        rename_workflow_action.setStatusTip("重命名当前工作流")
        rename_workflow_action.triggered.connect(self.rename_current_workflow)
        workflow_menu.addAction(rename_workflow_action)
        
        # === 执行菜单 ===
        run_menu = menubar.addMenu("执行(&R)")
        
        # 运行当前工作流
        run_action = QtWidgets.QAction("▶ 运行当前工作流", self)
        run_action.setShortcut("F5")
        run_action.setStatusTip("执行当前工作流")
        run_action.triggered.connect(self.run_graph)
        run_menu.addAction(run_action)
        
        # 运行所有工作流
        run_all_action = QtWidgets.QAction("⏩ 运行所有工作流", self)
        run_all_action.setShortcut("Shift+F5")
        run_all_action.setStatusTip("执行所有工作流")
        run_all_action.triggered.connect(self.run_all_workflows)
        run_menu.addAction(run_all_action)
        
        run_menu.addSeparator()
        
        # 清空当前工作流
        clear_action = QtWidgets.QAction("🗑 清空当前工作流", self)
        clear_action.setStatusTip("清空当前工作流的所有节点")
        clear_action.triggered.connect(self.clear_graph)
        run_menu.addAction(clear_action)
        
        # === 帮助菜单 ===
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QtWidgets.QAction("ℹ️ 关于", self)
        about_action.setStatusTip("关于本软件")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # === 插件管理菜单 ===
        plugin_menu = menubar.addMenu("插件(&P)")
        
        # 节点编辑器
        node_editor_action = QtWidgets.QAction("🛠️ 节点编辑器", self)
        node_editor_action.setStatusTip("创建、编辑和管理节点")
        node_editor_action.triggered.connect(self.open_node_editor)
        plugin_menu.addAction(node_editor_action)
        
        plugin_menu.addSeparator()
        
        # 安装插件
        install_plugin_action = QtWidgets.QAction("📦 安装插件", self)
        install_plugin_action.setStatusTip("从ZIP文件安装插件")
        install_plugin_action.triggered.connect(self.install_plugin)
        plugin_menu.addAction(install_plugin_action)
        
        # 管理插件
        manage_plugins_action = QtWidgets.QAction("⚙️ 管理插件", self)
        manage_plugins_action.setStatusTip("查看和管理已安装插件")
        manage_plugins_action.triggered.connect(self.manage_plugins)
        plugin_menu.addAction(manage_plugins_action)
        
        plugin_menu.addSeparator()
        
        # 刷新插件
        reload_plugins_action = QtWidgets.QAction("🔄 刷新插件", self)
        reload_plugins_action.setStatusTip("重新扫描并加载插件")
        reload_plugins_action.triggered.connect(self.reload_plugins)
        plugin_menu.addAction(reload_plugins_action)
        
    def run_graph(self):
        """
        执行当前激活的节点图（委托给ExecutionUIManager）
        """
        self.execution_ui.run_current_graph()
    
    def clear_graph(self):
        """
        清空当前激活的节点图（委托给ExecutionUIManager）
        """
        self.execution_ui.clear_graph_with_confirmation()
            
    def save_graph(self):
        """
        保存当前节点图（委托给ExecutionUIManager）
        """
        self.execution_ui.save_graph_to_file()
                
    def load_graph(self):
        """
        加载节点图到当前标签页（委托给ExecutionUIManager）
        """
        self.execution_ui.load_graph_from_file()
                
    def _on_node_created(self, node, workflow=None):
        """
        节点创建时的回调函数
        预留用于未来扩展
        """
        pass
    
    def _on_browse_image_file(self, node):
        """
        浏览并选择图像文件
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;All Files (*)"
        )
        
        if file_path:
            # 设置文件路径到节点的text_input
            node.set_property('file_path', file_path)
            print(f"已选择图像: {file_path}")
            # 可选：显示提示信息
            QtWidgets.QMessageBox.information(
                self,
                "文件已选择",
                f"已选择:\n{file_path}"
            )
    
    def _on_select_save_path(self, node):
        """
        选择图像保存路径
        """
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "保存图像",
            "",
            "PNG Files (*.png);;JPG Files (*.jpg);;BMP Files (*.bmp);;All Files (*)"
        )
        
        if file_path:
            # 设置保存路径到节点的text_input
            node.set_property('save_path', file_path)
            print(f"保存路径: {file_path}")
            # 可选：显示提示信息
            QtWidgets.QMessageBox.information(
                self,
                "路径已选择",
                f"保存路径:\n{file_path}"
            )
    
    def _on_node_double_clicked(self, node, workflow=None):
        """
        节点双击时的回调函数
        - IO节点: 弹出文件选择对话框
        - ImageViewNode: 显示图像预览对话框（非模态）
        """
        # 获取节点类型标识（type_是属性，不是方法）
        node_type = node.type_ if hasattr(node, 'type_') else str(type(node))
        
        print(f"🔍 节点双击调试信息:")
        print(f"   节点类型: {node_type}")
        print(f"   节点名称: {node.name()}")
        print(f"   是否有file_path属性: {hasattr(node, 'file_path')}")
        print(f"   是否有save_path属性: {hasattr(node, 'save_path')}")
        print(f"   是否有get_cached_image方法: {hasattr(node, 'get_cached_image')}")
        
        # 处理图像加载节点 (ImageLoadNode)
        if "ImageLoadNode" in str(node_type) or hasattr(node, 'file_path'):
            print(f"   ✅ 识别为 ImageLoadNode，打开文件选择对话框")
            self._on_browse_image_file(node)
            
        # 处理图像保存节点 (ImageSaveNode)
        elif "ImageSaveNode" in str(node_type) or hasattr(node, 'save_path'):
            print(f"   ✅ 识别为 ImageSaveNode，打开保存路径选择对话框")
            self._on_select_save_path(node)
            
        # 处理图像显示节点 (ImageViewNode)
        elif "ImageViewNode" in str(node_type) or hasattr(node, 'get_cached_image'):
            print(f"   ✅ 识别为 ImageViewNode，尝试打开预览窗口")
            if hasattr(node, 'get_cached_image'):
                image = node.get_cached_image()
                if image is not None:
                    print(f"   ✅ 获取到缓存图像，形状: {image.shape}")
                    # 检查是否已经打开了该节点的预览窗口
                    node_id = node.id  # id是属性，不是方法
                    if node_id in self.preview_windows:
                        # 如果窗口已存在，将其提到前面并刷新
                        existing_dialog = self.preview_windows[node_id]
                        existing_dialog.raise_()
                        existing_dialog.activateWindow()
                        existing_dialog.refresh_preview()
                        print(f"   🔄 刷新已存在的预览窗口")
                    else:
                        # 创建新的预览对话框（非模态）
                        dialog = ImagePreviewDialog(
                            image, 
                            node=node,  # 传递节点引用用于刷新
                            title=f"图像预览 - {node.name()}",
                            parent=self
                        )
                        
                        # 保存窗口引用
                        self.preview_windows[node_id] = dialog
                        
                        # 监听窗口关闭事件，清理引用
                        dialog.finished.connect(lambda nid=node_id: self._on_preview_window_closed(nid))
                        
                        # 显示非模态窗口
                        dialog.show()
                        print(f"   📷 打开新的预览窗口")
                        
                    print(f"✅ 成功打开预览窗口: {node.name()}")
                else:
                    print(f"   ⚠️ 节点中没有缓存图像")
                    QtWidgets.QMessageBox.information(
                        self,
                        "提示",
                        "该节点尚未处理图像数据\n请先运行节点图"
                    )
            else:
                print(f"   ❌ 节点没有get_cached_image方法")
        else:
            print(f"   ℹ️ 未识别的节点类型，不执行任何操作")

    def _on_preview_window_closed(self, node_id):
        """
        预览窗口关闭时的回调，清理引用
        """
        if node_id in self.preview_windows:
            del self.preview_windows[node_id]
            print(f"🗑️ 预览窗口已关闭，清理引用")
    
    def show_about(self):
        """
        显示关于对话框
        """
        QtWidgets.QMessageBox.about(
            self,
            "关于",
            "图形化视觉编程系统 v4.1\n\n"
            "基于NodeGraphQt和OpenCV构建\n"
            "类似海康、基恩士、康耐视的视觉编程框架\n\n"
            "功能特性:\n"
            "- 可视化节点编程\n"
            "- 实时图像处理\n"
            "- 拖拽式工作流设计\n"
            "- 多工作流管理\n"
            "- 模块化架构设计\n"
            "- 支持多种图像处理算法"
        )
        
    def run_all_workflows(self):
        """
        执行所有工作流（委托给ExecutionUIManager）
        """
        self.execution_ui.run_all_workflows()
        
    # === 工程管理方法（委托给ProjectUIManager）===
    
    def new_project(self):
        """
        创建新工程（委托给ProjectUIManager）
        """
        self.project_ui.new_project_from_ui()
        
    def open_project(self):
        """
        打开工程（委托给ProjectUIManager）
        """
        self.project_ui.open_project_from_ui()
    
    def save_project(self):
        """
        保存当前工程为单文件（委托给ProjectUIManager）
        """
        self.project_ui.save_project_from_ui()
    
    def _update_recent_projects_menu(self):
        """
        更新最近工程菜单（委托给ProjectUIManager）
        """
        if hasattr(self, 'recent_projects_menu'):
            self.project_ui.update_recent_projects_menu(self.recent_projects_menu)
    
    def add_new_workflow(self):
        """
        添加新的工作流（委托给ProjectUIManager）
        """
        self.project_ui.add_new_workflow_from_ui()
        
    def close_current_workflow(self):
        """
        关闭当前工作流（委托给ProjectUIManager）
        """
        self.project_ui.close_current_workflow_from_ui()
            
    def rename_current_workflow(self):
        """
        重命名当前工作流（委托给ProjectUIManager）
        """
        self.project_ui.rename_workflow_from_ui()
            
    def fit_to_selection(self):
        """
        适应当前工作流的所有节点
        """
        if self.current_node_graph:
            self.current_node_graph.fit_to_selection()
    
    # === 插件管理方法（委托给PluginUIManager）===
    
    def open_node_editor(self):
        """
        打开节点编辑器（委托给PluginUIManager）
        """
        self.plugin_ui.open_node_editor()
    
    def install_plugin(self):
        """
        从ZIP文件安装插件（委托给PluginUIManager）
        """
        self.plugin_ui.install_plugin_from_ui()
    
    def manage_plugins(self):
        """
        显示插件管理对话框（委托给PluginUIManager）
        """
        self.plugin_ui.manage_plugins_dialog()
    
    def reload_plugins(self):
        """
        重新扫描并加载插件（委托给PluginUIManager）
        """
        self.plugin_ui.reload_plugins_from_ui()
    
    def closeEvent(self, event):
        """
        窗口关闭事件
        """
        # 检查是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认退出",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
        
        event.accept()
