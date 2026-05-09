
from core.event_bus import event_bus, Events
from ui.image_preview import ImagePreviewDialog
from plugins.plugin_ui_manager import PluginUIManager
from plugins.plugin_manager import PluginManager
from core.execution_ui_manager import ExecutionUIManager
from core.project_ui_manager import ProjectUIManager
from core.project_manager import project_manager
from core.graph_engine import GraphEngine
from core.node_lifecycle import lifecycle_manager
from NodeGraphQt import NodeGraph, NodesPaletteWidget, PropertiesBinWidget
from PySide2 import QtWidgets, QtCore, QtGui
import utils
from utils import logger
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

# os.environ["QT_NO_ANIMATION"] = "1"

# 导入核心引擎和工程管理
# 导入插件管理器
# 导入图像预览对话框
# 导入事件总线

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
        self.setWindowTitle("图形化视觉处理系统 v5.0")
        self.setGeometry(0, 0, 1600, 1024)
        
        # 禁用所有动画效果
        self._disable_all_animations()
       
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

        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self):
        """
        设置事件订阅 - 响应全局事件变化
        """
        event_bus.subscribe(Events.WORKFLOW_SELECTED,
                            self._on_workflow_selected)
        event_bus.subscribe(Events.WORKFLOW_EXECUTED,
                            self._on_workflow_executed)
        event_bus.subscribe(Events.WORKFLOW_EXECUTION_ERROR,
                            self._on_workflow_execution_error)
        event_bus.subscribe(Events.PREVIEW_REFRESH, self._on_preview_refresh)
        event_bus.subscribe(Events.PLUGIN_LOADED, self._on_plugin_loaded)

    def _load_plugins(self):
        """
        加载所有已安装的插件（简化版：仅扫描，延迟加载）
        """
        utils.logger.info("\n" + "=" * 60, module="main_window")
        utils.logger.info("正在加载插件...", module="main_window")
        utils.logger.info("=" * 60, module="main_window")

        # 扫描插件
        plugins = self.plugin_manager.scan_plugins()
        utils.logger.info(f"发现 {len(plugins)} 个插件\n", module="main_window")

        if not plugins:
            utils.logger.info(
                "💡 提示: 将插件文件夹放入 user_plugins/ 目录即可自动加载\n", module="main_window")
            utils.logger.info("=" * 60 + "\n", module="main_window")
            return

        # 由于此时还没有NodeGraph实例，延迟到第一个工作流创建时加载
        # 这里只记录需要加载的插件
        self._pending_plugins = plugins
        utils.logger.info(
            f"📦 待加载插件: {', '.join([p.name for p in plugins])}", module="main_window")
        utils.logger.info("=" * 60 + "\n", module="main_window")

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

    # def _on_tab_changed(self, index):
    #     """
    #     标签页切换时的回调（委托给ProjectUIManager）

    #     Args:
    #         index: 新的标签页索引
    #     """
    #     self.project_ui.on_tab_changed(index)
        
    #     # 更新共享组件的 NodeGraph 引用
    #     self._update_shared_components()
    
    def _update_shared_components(self):
        """
        更新共享组件（节点库、属性面板）指向当前工作流的 NodeGraph
        
        解决临时 Graph 实例问题：确保节点库和属性面板始终引用
        当前激活工作流的 NodeGraph，而不是过时的 temp_graph
        """
        if not hasattr(self, 'current_node_graph') or self.current_node_graph is None:
            return
        
        # 如果共享组件还未初始化，跳过
        if not self._shared_components_initialized:
            return
        
        # 检查是否是临时 Graph
        if hasattr(self, 'temp_graph') and self.current_node_graph == self.temp_graph:
            return
        
        # 尝试更新 nodes_palette
        if self.nodes_palette:
            try:
                if hasattr(self.nodes_palette, 'set_node_graph'):
                    self.nodes_palette.set_node_graph(self.current_node_graph)
                elif hasattr(self.nodes_palette, '_node_graph'):
                    self.nodes_palette._node_graph = self.current_node_graph
            except Exception as e:
                utils.logger.warning(f"更新 nodes_palette 失败: {e}", module="main_window")
        
        # 尝试更新 properties_bin
        if self.properties_bin:
            try:
                if hasattr(self.properties_bin, 'set_node_graph'):
                    self.properties_bin.set_node_graph(self.current_node_graph)
                elif hasattr(self.properties_bin, '_node_graph'):
                    self.properties_bin._node_graph = self.current_node_graph
            except Exception as e:
                utils.logger.warning(f"更新 properties_bin 失败: {e}", module="main_window")
        
        # 更新事件过滤器
        if hasattr(self.current_node_graph, 'widget'):
            try:
                self.current_node_graph.widget.removeEventFilter(self)
                self.current_node_graph.widget.installEventFilter(self)
            except Exception as e:
                utils.logger.warning(f"更新事件过滤器失败: {e}", module="main_window")

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

        # === 标签页容器（位置交换 - 现在在日志面板下方）===
        self.tab_widget = QtWidgets.QTabWidget()
        # self.tab_widget.setTabsClosable(True)  # 允许关闭标签页
        # self.tab_widget.setMovable(True)       # 允许拖动排序
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid #3c3c3c; }")
        # self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        # self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)

        # === 共享组件延迟初始化 ===
        # 不再创建临时Graph，避免后续切换工作流时的引用混乱
        self.nodes_palette = None
        self.properties_bin = None
        self._shared_components_initialized = False

        # === 左侧：节点库面板（共享）===
        # 暂时创建空的占位符，稍后初始化
        self._init_shared_components_placeholder()

        # === 左侧下方：节点说明面板 ===
        self.node_info_panel = self._create_node_info_panel()

        # 创建左侧垂直布局容器，实现节点说明固定在底部
        self._left_container = QtWidgets.QWidget()
        self._left_layout = QtWidgets.QVBoxLayout(self._left_container)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(0)

        # 节点库将在初始化后添加
        self.node_info_panel.setMaximumHeight(250)
        self.node_info_panel.setMinimumHeight(200)
        self._left_layout.addWidget(self.node_info_panel)

        # 将整个左侧容器作为一个DockWidget
        dock_left = QtWidgets.QDockWidget("节点库", self)
        dock_left.setWidget(self._left_container)
        dock_left.setFeatures(
            QtWidgets.QDockWidget.NoDockWidgetFeatures)
        # dock_left.setProperty("animated", False)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_left)

        # === 右侧：属性面板 ===
        # 暂时创建空的占位符
        self._init_right_dock_placeholder()

        # 创建工具栏
        self._create_toolbar()

        # 创建菜单栏
        self._create_menu_bar()
    
        # === 顶部：日志和状态面板（位置交换）===
        self.log_panel = self._create_log_panel()
        main_layout.addWidget(self.log_panel)

    def _init_shared_components_placeholder(self):
        """
        初始化共享组件占位符
        
        在首次工作流创建时会调用 _initialize_shared_components 进行真正的初始化
        """
        pass
    
    def _init_right_dock_placeholder(self):
        """
        初始化右侧 Dock 占位符
        """
        pass
    
    def _initialize_shared_components(self, node_graph):
        """
        初始化共享组件（节点库、属性面板）
        
        在首次工作流创建时调用，确保共享组件与工作流的 NodeGraph 正确关联
        
        Args:
            node_graph: NodeGraph 实例
        """
        if self._shared_components_initialized:
            return
        
        self._shared_components_initialized = True
        
        # 初始化节点库面板
        self.nodes_palette = NodesPaletteWidget(node_graph=node_graph)
        self.nodes_palette.setWindowTitle("节点库")
        
        try:
            tab_widget = self.nodes_palette.tab_widget()
            if hasattr(tab_widget, 'setTabPosition'):
                tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        except (AttributeError, TypeError):
            if hasattr(self.nodes_palette, 'tab_widget'):
                self.nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        
        self._customize_node_palette()
        
        # 将节点库面板添加到左侧布局（在节点说明面板之前）
        if hasattr(self, '_left_layout') and self._left_layout:
            # 在索引0位置插入节点库（节点说明面板之前）
            self._left_layout.insertWidget(0, self.nodes_palette)
        
        # 初始化属性面板
        self.properties_bin = PropertiesBinWidget(node_graph=node_graph)
        self.properties_bin.setWindowTitle("属性面板")
        
        dock_properties = QtWidgets.QDockWidget("属性面板", self)
        dock_properties.setWidget(self.properties_bin)
        dock_properties.setProperty("animated", False)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_properties)
        
        # 设置当前 NodeGraph
        self.current_node_graph = node_graph
        
        # 为 NodeGraph widget 安装事件过滤器
        node_graph.widget.installEventFilter(self)
        
        # 连接节点库的选择信号到说明面板
        self._connect_node_selection_signal()
        
        utils.logger.success("共享组件初始化完成", module="main_window")

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

    def _create_log_panel(self):
        """
        创建底部日志和状态面板

        Returns:
            QtWidgets.QWidget: 日志面板组件
        """
        from utils.logger import QtLogHandler

        # 创建容器widget
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === 标题栏（带折叠按钮）===
        header_layout = QtWidgets.QHBoxLayout()

        # 标题
        title_label = QtWidgets.QLabel("运行日志")
        title_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        header_layout.addWidget(title_label)

        # 弹簧，将按钮推到右侧
        header_layout.addStretch()

        # 清空按钮
        clear_btn = QtWidgets.QPushButton("清空")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self._clear_logs)
        header_layout.addWidget(clear_btn)

        # 折叠/展开按钮
        self.toggle_log_btn = QtWidgets.QPushButton("折叠")
        self.toggle_log_btn.setMaximumWidth(80)
        self.toggle_log_btn.clicked.connect(self._toggle_log_panel)
        header_layout.addWidget(self.toggle_log_btn)

        layout.addLayout(header_layout)

        # === 日志显示区域 ===
        self.log_text_browser = QtWidgets.QTextBrowser()
        self.log_text_browser.setFont(QtGui.QFont("Consolas", 9))
        self.log_text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
            }
        """)
        self.log_text_browser.setMinimumHeight(50)
        self.log_text_browser.setMaximumHeight(150)

        # 设置为只读
        self.log_text_browser.setReadOnly(True)

        # 启用富文本
        self.log_text_browser.setOpenExternalLinks(False)

        layout.addWidget(self.log_text_browser)

        # === 状态栏 ===
        status_layout = QtWidgets.QHBoxLayout()

        # 状态标签
        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        # 弹簧
        status_layout.addStretch()

        # 日志级别显示
        from utils.logger import logger
        level_text = f"日志级别: {logger.level.name}"
        self.level_label = QtWidgets.QLabel(level_text)
        self.level_label.setStyleSheet("color: #95a5a6;")
        status_layout.addWidget(self.level_label)

        layout.addLayout(status_layout)

        # === 集成QtLogHandler到Logger ===
        qt_handler = QtLogHandler(text_widget=self.log_text_browser)
        logger.add_handler(qt_handler)
        
        # 调试信息
        print(f"[DEBUG] QtLogHandler added. Total handlers: {len(logger.handlers)}")
        for i, h in enumerate(logger.handlers):
            print(f"[DEBUG]   handler[{i}]: {type(h).__name__}")

        # 保存handler引用，便于后续操作
        self.qt_log_handler = qt_handler

        # 初始状态：展开
        self.log_panel_expanded = True

        return panel

    def _toggle_log_panel(self):
        """
        切换日志面板的折叠/展开状态
        """
        if self.log_panel_expanded:
            # 折叠
            self.log_text_browser.setVisible(False)
            self.toggle_log_btn.setText("▶ 展开")
            self.log_panel_expanded = False
        else:
            # 展开
            self.log_text_browser.setVisible(True)
            self.toggle_log_btn.setText("▼ 折叠")
            self.log_panel_expanded = True

    def _clear_logs(self):
        """
        清空日志（仅清空UI面板，不影响终端和文件输出）
        """
        if hasattr(self, 'qt_log_handler'):
            self.qt_log_handler.clear()
            self.status_label.setText("日志已清空")

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
                # 为每个标签页的内容widget及其子组件安装事件过滤器
                for i in range(tab_widget.count()):
                    widget = tab_widget.widget(i)
                    if widget:
                        # 为该widget安装
                        widget.installEventFilter(self)

                        # 为该widget的所有子组件安装
                        from PySide2.QtWidgets import QWidget
                        for child in widget.findChildren(QWidget):
                            child.installEventFilter(self)

        except Exception as e:
            utils.logger.error(f"⚠️ 连接节点选择信号失败: {e}", module="main_window")

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
            utils.logger.error(f"⚠️ 刷新事件过滤器失败: {e}", module="main_window")

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

        # === 节点库点击事件处理 ===
        if event.type() == QEvent.MouseButtonPress:
            # 检查是否是节点库中的组件
            if hasattr(obj, 'parent') and obj.parent():
                parent = obj.parent()
                # 尝试从父级追溯到 nodes_palette
                depth = 0
                while parent and depth < 10:
                    if parent == self.nodes_palette:
                        # 这是节点库中的点击事件
                        # 延迟获取选中的节点信息（因为点击后才会更新选中状态）
                        QtCore.QTimer.singleShot(
                            50, self._update_node_info_from_selection)
                        break
                    parent = parent.parent() if hasattr(parent, 'parent') else None
                    depth += 1

        return False  # 不拦截其他事件

    def _update_node_info_from_selection(self):
        """
        从节点库的当前选中状态更新说明面板
        """
        try:
            # 获取 tab_widget
            tab_widget = self.nodes_palette.tab_widget()
            if not tab_widget:
                return

            # 遍历所有标签页，查找选中的项
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if widget:
                    # 尝试不同的方法获取选中项
                    selected_nodes = []
                    node_name = None

                    # 方法1: 如果有 selectedItems 方法（QTreeWidget/QListWidget）
                    if hasattr(widget, 'selectedItems'):
                        selected_nodes = widget.selectedItems()
                        if selected_nodes:
                            item = selected_nodes[0]
                            if hasattr(item, 'text'):
                                node_name = item.text(0) if hasattr(
                                    item, 'text') else str(item)

                    # 方法2: 如果是 NodesGridView，尝试其他方法
                    elif hasattr(widget, 'selectedNodes'):
                        selected_nodes = widget.selectedNodes()

                    # 方法3: 检查是否有 selectionModel（NodesGridView 使用此方法）
                    elif hasattr(widget, 'selectionModel'):
                        sel_model = widget.selectionModel()
                        if sel_model and hasattr(sel_model, 'selectedIndexes'):
                            indexes = sel_model.selectedIndexes()

                            if indexes:
                                # 从索引获取数据
                                index = indexes[0]
                                model = widget.model()
                                if model:
                                    # 尝试从模型中获取节点名称
                                    data = model.data(index)
                                    if data:
                                        node_name = str(data)

                                    # 如果上面没成功，尝试其他方式
                                    if not node_name and hasattr(model, 'itemFromIndex'):
                                        item = model.itemFromIndex(index)
                                        if item and hasattr(item, 'text'):
                                            node_name = item.text()

                    # 如果找到了节点名称，显示信息
                    if node_name:
                        # 尝试从 plugin_manager 获取节点详细信息
                        self._display_node_info_by_name(node_name)
                        return

        except Exception as e:
            utils.logger.error(f"⚠️ 更新节点信息失败: {e}", module="main_window")

    def _display_node_info_by_name(self, node_display_name):
        """
        根据节点显示名称查找并显示节点信息

        Args:
            node_display_name: 节点的显示名称
        """
        try:
            # 从 plugin_manager 中查找匹配的节点
            found = False
            if hasattr(self, 'plugin_manager') and self.plugin_manager:
                for plugin_name, plugin_info in self.plugin_manager.plugins.items():
                    for node_def in plugin_info.nodes:
                        if node_def.display_name == node_display_name:
                            # 找到匹配的节点，显示信息
                            description = ""
                            # 尝试从已加载的节点类中获取描述
                            node_key = f"{plugin_name}.{node_def.class_name}"
                            if node_key in self.plugin_manager.loaded_nodes:
                                node_class = self.plugin_manager.loaded_nodes[node_key]
                                if hasattr(node_class, '_node_description'):
                                    description = node_class._node_description

                            self.update_node_info(
                                node_class_name=node_def.class_name,
                                display_name=node_def.display_name,
                                category=node_def.category,
                                description=description
                            )
                            found = True
                            return

            # 如果没找到详细信息，至少显示名称
            if not found:
                self.info_name_label.setText(f"🔹 {node_display_name}")
                self.info_category_label.setText("分类: 未知")
                self.info_text.setPlainText("暂无详细说明")

        except Exception as e:
            utils.logger.error(f"⚠️ 显示节点信息失败: {e}", module="main_window")

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
        self.info_category_label.setText(
            f"分类: {category} | 类名: {node_class_name}")

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

        # === 调试控制 ===
        self.debug_mode_action = QtWidgets.QAction("🐛 调试模式", self)
        self.debug_mode_action.setStatusTip("启用/禁用节点调试模式")
        self.debug_mode_action.setCheckable(True)
        self.debug_mode_action.triggered.connect(self._toggle_debug_mode)
        toolbar.addAction(self.debug_mode_action)

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
        recent_menu.aboutToShow.connect(
            lambda: self._update_recent_projects_menu())

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

        # === 设置菜单 ===
        settings_menu = menubar.addMenu("设置(&S)")

        system_settings_action = QtWidgets.QAction("⚙️ 系统设置", self)
        system_settings_action.setStatusTip("配置系统参数")
        system_settings_action.setShortcut("Ctrl+,")
        system_settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(system_settings_action)

        # === 帮助菜单 ===
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QtWidgets.QAction("ℹ️ 关于", self)
        about_action.setStatusTip("关于本软件")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _toggle_debug_mode(self, checked):
        """
        切换调试模式
        
        Args:
            checked: 是否启用调试模式
        """
        from core.node_debugger import node_debugger
        
        node_debugger.debug_mode = checked
        
        if checked:
            utils.logger.info("🐛 节点调试模式已启用", module="main_window")
            utils.logger.info("   - 调试日志将显示在控制台", module="main_window")
            utils.logger.info("   - 节点执行将被追踪", module="main_window")
        else:
            utils.logger.info("🐛 节点调试模式已禁用", module="main_window")
    
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
            utils.logger.info(f"已选择图像: {file_path}", module="main_window")
            # 可选：显示提示信息
            # QtWidgets.QMessageBox.information(
            #     self,
            #     "文件已选择",
            #     f"已选择:\n{file_path}"
            # )

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
            utils.logger.info(f"保存路径: {file_path}", module="main_window")
            # 可选：显示提示信息
            # QtWidgets.QMessageBox.information(
            #     self,
            #     "路径已选择",
            #     f"保存路径:\n{file_path}"
            # )

    def _on_node_double_clicked(self, node, workflow=None):
        """
        节点双击时的回调函数
        - IO节点: 弹出文件选择对话框
        - ImageViewNode: 显示图像预览对话框（非模态）
        """
        # 获取节点类型标识（type_是属性，不是方法）
        node_type = node.type_ if hasattr(node, 'type_') else str(type(node))

        utils.logger.info(f"🔍 节点双击调试信息:", module="main_window")
        utils.logger.info(f"   节点类型: {node_type}", module="main_window")
        utils.logger.info(f"   节点名称: {node.name()}", module="main_window")
        utils.logger.info(
            f"   是否有file_path属性: {hasattr(node, 'file_path')}", module="main_window")
        utils.logger.info(
            f"   是否有save_path属性: {hasattr(node, 'save_path')}", module="main_window")
        utils.logger.info(
            f"   是否有get_cached_image方法: {hasattr(node, 'get_cached_image')}", module="main_window")

        # 处理图像加载节点 (ImageLoadNode)
        if "ImageLoadNode" in str(node_type) or hasattr(node, 'file_path'):
            utils.logger.success(
                f"   ✅ 识别为 ImageLoadNode，打开文件选择对话框", module="main_window")
            self._on_browse_image_file(node)

        # 处理图像保存节点 (ImageSaveNode)
        elif "ImageSaveNode" in str(node_type) or hasattr(node, 'save_path'):
            utils.logger.success(
                f"   ✅ 识别为 ImageSaveNode，打开保存路径选择对话框", module="main_window")
            self._on_select_save_path(node)

        # 处理工业相机采集节点 (CameraCaptureNode) - 必须在ImageViewNode之前检查
        elif "CameraCaptureNode" in str(node_type) or (hasattr(node, '__class__') and 'CameraCaptureNode' in node.__class__.__name__):
            utils.logger.success(
                f"   ✅ 识别为 CameraCaptureNode", module="main_window")
            utils.logger.info(
                f"   📋 节点完整类型: {type(node).__module__}.{type(node).__name__}", module="main_window")

            # 直接打开预览窗口（集成相机控制功能）
            self._open_camera_preview(node, None)

        # 处理图像显示节点 (ImageViewNode)
        elif "ImageViewNode" in str(node_type) or hasattr(node, 'get_cached_image'):
            utils.logger.success(
                f"   ✅ 识别为 ImageViewNode，尝试打开预览窗口", module="main_window")
            if hasattr(node, 'get_cached_image'):
                image = node.get_cached_image()
                if image is not None:
                    utils.logger.success(
                        f"   ✅ 获取到缓存图像，形状: {image.shape}", module="main_window")
                    # 检查是否已经打开了该节点的预览窗口
                    node_id = node.id  # id是属性，不是方法

                    # 修复问题1和3：检查窗口是否存在且可见
                    if node_id in self.preview_windows:
                        existing_dialog = self.preview_windows[node_id]
                        # 检查窗口是否仍然有效且可见
                        if existing_dialog.isVisible():
                            # 如果窗口已存在且可见，将其提到前面并刷新
                            existing_dialog.raise_()
                            existing_dialog.activateWindow()
                            existing_dialog.refresh_preview()
                            utils.logger.info(
                                f"   🔄 刷新已存在的预览窗口", module="main_window")
                        else:
                            # 窗口存在但已隐藏/关闭，需要重新创建
                            utils.logger.info(
                                f"   🗑️ 窗口已关闭，删除旧引用并创建新窗口", module="main_window")
                            del self.preview_windows[node_id]
                            self._create_new_preview_window(
                                node, image, node_id)
                    else:
                        # 创建新的预览对话框（非模态）
                        self._create_new_preview_window(node, image, node_id)

                    utils.logger.success(
                        f"✅ 成功打开预览窗口: {node.name()}", module="main_window")
                else:
                    utils.logger.warning(
                        f"   ⚠️ 节点中没有缓存图像", module="main_window")
                    QtWidgets.QMessageBox.information(
                        self,
                        "提示",
                        "该节点尚未处理图像数据\n请先运行节点图"
                    )
            else:
                utils.logger.error(
                    f"   ❌ 节点没有get_cached_image方法", module="main_window")
        else:
            utils.logger.info(f"   ℹ️ 未识别的节点类型，不执行任何操作", module="main_window")

    def _create_new_preview_window(self, node, image, node_id):
        """
        创建新的预览窗口

        Args:
            node: ImageViewNode实例
            image: 要显示的图像
            node_id: 节点ID
        """
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
        dialog.finished.connect(
            lambda nid=node_id: self._on_preview_window_closed(nid))

        # 显示非模态窗口
        dialog.show()
        utils.logger.info(f"   📷 打开新的预览窗口", module="main_window")

    def _on_preview_window_closed(self, node_id):
        """
        预览窗口关闭时的回调，清理引用
        """
        if node_id in self.preview_windows:
            del self.preview_windows[node_id]
            utils.logger.info(f"🗑️ 预览窗口已关闭，清理引用", module="main_window")

    def open_settings(self):
        """
        打开系统设置对话框
        """
        from ui.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self._apply_settings_changes()

    def _apply_settings_changes(self):
        """
        应用配置变更到界面
        """
        from core.theme_manager import theme_manager
        
        stylesheet = theme_manager.generate_stylesheet()
        self.setStyleSheet(stylesheet)
        
        utils.logger.info("⚙️ 系统设置已更新", module="main_window")

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
            self.project_ui.update_recent_projects_menu(
                self.recent_projects_menu)

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

    def keyPressEvent(self, event):
        """
        键盘事件处理 - 拦截 Delete 键实现节点删除确认

        Args:
            event: 键盘事件对象
        """
        from PySide2.QtCore import Qt

        # 检查是否是 Delete 键
        if event.key() == Qt.Key_Delete:
            # 检查是否有激活的 NodeGraph
            if hasattr(self, 'current_node_graph') and self.current_node_graph:
                # 获取当前选中的节点
                selected_nodes = self.current_node_graph.selected_nodes()

                if selected_nodes:
                    node_count = len(selected_nodes)
                    node_names = [node.name() for node in selected_nodes]

                    # 显示确认对话框
                    if node_count == 1:
                        message = f"确定要删除节点 '{node_names[0]}' 吗？"
                    else:
                        message = f"确定要删除 {node_count} 个节点吗？\n\n" + \
                            "\n".join([f"• {name}" for name in node_names[:5]])
                        if node_count > 5:
                            message += f"\n... 还有 {node_count - 5} 个节点"

                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "确认删除",
                        message,
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No
                    )

                    if reply == QtWidgets.QMessageBox.Yes:
                        # 用户确认，执行删除（使用完整清理流程）
                        for node in selected_nodes:
                            lifecycle_manager.delete_node_with_cleanup(node, self.current_node_graph)

                    return  # 拦截事件，阻止默认行为

        # 其他按键交给父类处理
        super().keyPressEvent(event)

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

    def _customize_node_palette(self):
        """
        自定义节点库面板：
        1. 根据 study OpenCV.md 的知识结构重新分组节点
        2. 隐藏 nodeGraphQt.nodes 默认标签（BackdropNode由NodeGraphQt自动注册）
        3. 添加刷新节点库按钮
        """
        if not self.nodes_palette:
            return

        try:
            # 1. 按知识结构重新分组节点
            self._regroup_nodes_by_knowledge_structure()
            
            # 2. 查找并移除 nodeGraphQt.nodes 标签
            tab_widget = self.nodes_palette.tab_widget()
            if tab_widget:
                for i in range(tab_widget.count()):
                    tab_text = tab_widget.tabText(i)
                    if tab_text == 'nodeGraphQt.nodes':
                        tab_widget.removeTab(i)
                        utils.logger.info("✅ nodeGraphQt.nodes 标签已隐藏", module="main_window")
                        break

        except Exception as e:
            utils.logger.error(f"❌ 自定义节点库失败: {e}", module="main_window")

    def _clear_node_factory(self):
        """
        强制清空 NodeFactory 中的所有节点类型（防止刷新时节点重复）
        """
        try:
            if not hasattr(self, 'current_node_graph') or not self.current_node_graph:
                return
            
            factory = self.current_node_graph._node_factory
            
            # 清空 __nodes 字典
            if hasattr(factory, '_NodeFactory__nodes'):
                getattr(factory, '_NodeFactory__nodes').clear()
            
            # 清空 __names 字典
            if hasattr(factory, '_NodeFactory__names'):
                getattr(factory, '_NodeFactory__names').clear()
            
            # 清空 __aliases 字典
            if hasattr(factory, '_NodeFactory__aliases'):
                getattr(factory, '_NodeFactory__aliases').clear()
            
            utils.logger.info("✅ NodeFactory 已清空", module="main_window")
            
        except Exception as e:
            utils.logger.error(f"❌ 清空 NodeFactory 失败: {e}", module="main_window")
    
    def _on_refresh_node_library(self):
        """
        刷新节点库的回调函数
        """
        try:
            utils.logger.info("🔄 开始刷新节点库...", module="main_window")

            if hasattr(self, 'current_node_graph') and self.current_node_graph:
                # 0. 强制清空 NodeFactory（防止节点重复）
                self._clear_node_factory()

                # 1. 重新加载所有插件（卸载旧节点，重新注册新节点）
                results = self.plugin_manager.reload_all_plugins(self.current_node_graph)

                # 2. 刷新节点库显示（强制重建标签）
                self._refresh_node_palette_display()

                # 3. 重新应用节点库定制
                self._customize_node_palette()

                # 统计结果
                success_count = sum(1 for v in results.values() if v)
                total_count = len(results)

                utils.logger.info(f"✅ 节点库刷新完成: {success_count}/{total_count} 个插件重载成功", module="main_window")

                # 显示提示
                self.statusBar().showMessage(f"节点库已刷新: {success_count}/{total_count} 个插件重载成功", 3000)
            else:
                utils.logger.warning("⚠️ current_node_graph 未初始化，无法刷新节点库", module="main_window")

        except Exception as e:
            utils.logger.error(f"❌ 刷新节点库失败: {e}", module="main_window")
            import traceback
            traceback.print_exc()
    
    def _refresh_node_palette_display(self):
        """
        刷新节点库显示（重新创建 NodesPaletteWidget，保留原有布局和标签位置）
        
        实现逻辑：
        1. 检查节点库和当前节点图是否有效
        2. 获取节点库的父布局，确保能正确替换组件
        3. 找到旧节点库在布局中的索引位置
        4. 保存旧节点库的标签位置（保持用户习惯的UI布局）
        5. 创建新的 NodesPaletteWidget 实例（使用最新注册的节点）
        6. 恢复标签位置（保持与旧节点库一致）
        7. 移除旧节点库并清理资源
        8. 在原位置插入新节点库
        9. 更新引用并记录日志
        """
        try:
            # 1. 检查有效性
            if not self.nodes_palette or not self.current_node_graph:
                return
            
            # 2. 获取父布局
            parent_layout = self.nodes_palette.parent().layout() if self.nodes_palette.parent() else None
            if not parent_layout:
                utils.logger.warning("⚠️ 无法找到节点库的父布局", module="main_window")
                return
            
            # 3. 找到旧节点库在布局中的索引
            old_index = -1
            for i in range(parent_layout.count()):
                if parent_layout.itemAt(i).widget() == self.nodes_palette:
                    old_index = i
                    break
            
            if old_index == -1:
                utils.logger.warning("⚠️ 无法找到节点库在布局中的位置", module="main_window")
                return
            
            # 4. 保存旧节点库的标签位置（左/右/上/下）
            old_tab_position = self.nodes_palette.tab_widget().tabPosition() if hasattr(self.nodes_palette, 'tab_widget') else None
            
            # 5. 创建新的节点库面板（自动加载 NodeFactory 中的所有节点）
            new_palette = NodesPaletteWidget(node_graph=self.current_node_graph)
            new_palette.setWindowTitle("节点库")
            
            # 6. 设置标签位置（保持与旧节点库一致，避免用户体验突兀）
            if old_tab_position is not None:
                new_palette.tab_widget().setTabPosition(old_tab_position)
            
            # 7. 移除旧节点库并清理资源
            parent_layout.removeWidget(self.nodes_palette)
            self.nodes_palette.deleteLater()
            
            # 8. 在原位置插入新节点库
            parent_layout.insertWidget(old_index, new_palette)
            
            # 9. 更新引用
            self.nodes_palette = new_palette
            
            utils.logger.info("✅ 节点库显示已刷新", module="main_window")
            
        except Exception as e:
            utils.logger.error(f"❌ 刷新节点库显示失败: {e}", module="main_window")
    
    def _regroup_nodes_by_knowledge_structure(self):
        """
        根据 study OpenCV.md 的知识结构重新组织节点库
        
        新分组：
        - 图像分析
        - 图像变换
        - 图像处理
        - 图像相机（不变）
        - 系统集成（不变）
        """
        if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
            return
        
        # 定义节点到新分组的映射
        node_category_map = {
            # 图像分析
            '高斯模糊': '图像分析',
            '中值模糊': '图像分析',
            '双边滤波': '图像分析',
            '形态学': '图像分析',
            '直方图均衡化': '图像分析',
            '轮廓分析': '图像分析',
            'Harris角点': '图像分析',
            
            # 图像变换
            '灰度化': '图像变换',
            'Canny算子': '图像变换',
            'Sobel算子': '图像变换',
            'Laplacian算子': '图像变换',
            'Hough直线': '图像变换',
            'Hough圆': '图像变换',
            'Resize': '图像变换',
            '旋转': '图像变换',
            '亮度对比度': '图像变换',
            
            # 图像处理
            '阈值': '图像处理',
            '自适应阈值': '图像处理',
            '模板匹配': '图像处理',
            '模板创建': '图像处理',
            '图像评估': '图像处理',
        }
        
        # 保持不变的分组
        preserved_categories = {'图像相机', '系统集成'}
        
        # 获取节点库的标签页控件
        tab_widget = self.nodes_palette.tab_widget()
        if not tab_widget:
            return
        
        # 收集所有节点信息并重新分配
        all_nodes = {}  # {新分组: [节点类]}
        node_instances = {}  # {节点名称: 节点实例}
        
        # 遍历所有现有标签页，收集节点
        for i in range(tab_widget.count()):
            tab_name = tab_widget.tabText(i)
            
            # 跳过空标签或默认标签
            if tab_name == 'nodeGraphQt.nodes':
                continue
                
            # 保留图像相机和系统集成分组
            if tab_name in preserved_categories:
                continue
                
            # 获取该标签页下的所有节点
            # 注意：这里需要根据实际的 NodeGraphQt API 来获取节点列表
            # 由于我们无法直接访问 NodeGraphQt 的内部结构，我们采用另一种方式
            # 暂时先通过重命名标签页的方式实现
        
        # 先重命名现有标签页作为过渡
        self._rename_palette_tabs_by_category(tab_widget)
        
        utils.logger.info("✅ 节点库按知识结构重新分组完成", module="main_window")
    
    def _rename_palette_tabs_by_category(self, tab_widget):
        """
        根据 plugin.json 的 group 数组和节点的 __identifier__ 重命名并重新排序节点库面板的标签页

        Args:
            tab_widget: QTabWidget 实例
        """
        if not hasattr(self, 'plugin_manager') or not self.plugin_manager:
            return

        # 构建 identifier 到中文显示名的映射
        identifier_display_map = {
            # 小写版本（来自 plugin.json）
            'image_source': '图像源',
            'image_analysis': '图像分析',
            'image_transform': '图像变换',
            'image_process': '图像处理',
            'integration': '系统集成',
            # 大写版本（可能来自其他地方）
            'Image_Source': '图像源',
            'Image_Analysis': '图像分析',
            'Image_Transform': '图像变换',
            'Image_Process': '图像处理',
            'Integration': '系统集成'
        }

        # 插件名称到中文名称的映射（用于 OCR、YOLO 等）
        plugin_display_map = {
            'ocr_vision': 'OCR',
            'yolo_vision': 'YOLO'
        }

        # 从插件的 group 字段获取排序顺序
        group_order = []
        for plugin_name, plugin_info in self.plugin_manager.plugins.items():
            if hasattr(plugin_info, 'group') and plugin_info.group:
                group_order = plugin_info.group
                utils.logger.info(f"📋 从插件 {plugin_name} 获取到 group 排序: {group_order}", module="main_window")
                break
        
        if not group_order:
            utils.logger.info("⚠️ 未找到 group 排序配置，使用默认顺序", module="main_window")

        # 收集所有标签信息
        tabs_info = []  # [(原始名称, 显示名称, 原始索引)]
        for i in range(tab_widget.count()):
            tab_text = tab_widget.tabText(i)
            display_name = tab_text  # 默认使用原始名称

            # 尝试从 identifier 映射中获取显示名
            if tab_text in identifier_display_map:
                display_name = identifier_display_map[tab_text]
                utils.logger.info(f"🔄 节点库标签重命名: '{tab_text}' -> '{display_name}'", module="main_window")
            # 尝试从插件映射中获取显示名
            elif tab_text in plugin_display_map:
                display_name = plugin_display_map[tab_text]
                utils.logger.info(f"🔄 节点库标签重命名: '{tab_text}' -> '{display_name}'", module="main_window")

            tabs_info.append((tab_text, display_name, i))

        # 根据 group_order 排序（大小写不敏感）
        def get_sort_key(item):
            original_name, display_name, index = item
            
            # 使用大小写不敏感的比较
            original_lower = original_name.lower()
            display_lower = display_name.lower()
            
            # 遍历 group_order 查找匹配
            for i, group_name in enumerate(group_order):
                group_lower = group_name.lower()
                if group_lower == original_lower or group_lower == display_lower:
                    return i
            
            # 否则放在最后
            return len(group_order)

        tabs_info.sort(key=get_sort_key)
        
        # 打印排序后的顺序（调试信息）
        sorted_names = [info[1] for info in tabs_info]
        utils.logger.info(f"🔄 排序后的标签顺序: {sorted_names}", module="main_window")

        # 先记录所有标签页的内容（使用原始名称）
        tab_contents = {}
        for i in range(tab_widget.count()):
            widget = tab_widget.widget(i)
            label = tab_widget.tabText(i)
            tab_contents[label] = widget
        
        # 清空所有标签
        while tab_widget.count() > 0:
            tab_widget.removeTab(0)
        
        # 按照排序后的顺序重新添加标签（同时重命名）
        for original_name, display_name, old_index in tabs_info:
            # 找到对应的标签内容
            if original_name in tab_contents:
                tab_widget.addTab(tab_contents[original_name], display_name)
            elif display_name in tab_contents:
                tab_widget.addTab(tab_contents[display_name], display_name)

        utils.logger.info("✅ 节点库标签重命名和排序完成", module="main_window")

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

        # 取消事件订阅，避免内存泄漏
        self._cleanup_event_subscriptions()

        event.accept()

    def _cleanup_event_subscriptions(self):
        """
        清理事件订阅
        """
        try:
            event_bus.unsubscribe(Events.WORKFLOW_SELECTED,
                                  self._on_workflow_selected)
            event_bus.unsubscribe(Events.WORKFLOW_EXECUTED,
                                  self._on_workflow_executed)
            event_bus.unsubscribe(
                Events.WORKFLOW_EXECUTION_ERROR, self._on_workflow_execution_error)
            event_bus.unsubscribe(Events.PREVIEW_REFRESH,
                                  self._on_preview_refresh)
            event_bus.unsubscribe(Events.PLUGIN_LOADED, self._on_plugin_loaded)
        except Exception as e:
            utils.logger.warning(f"清理事件订阅失败: {e}", module="main_window")

    def _disable_all_animations(self):
        """
        禁用所有 Qt 动画效果，提升窗口调整性能
        
        禁用以下组件的动画：
        - QSplitter 分割器动画
        - QTabWidget 标签切换动画
        - QDockWidget 停靠动画
        - 全局样式动画
        """
        # 注意：Qt 样式表不支持 CSS3 的 animation-duration 和 transition-duration 属性
        # 动画禁用通过组件的 setAnimated(False) 方法实现（如果支持）
        
        # 设置全局属性
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)

    def _camera_init(self, node):
        """初始化相机"""
        if hasattr(node, 'initialize_camera'):
            try:
                success = node.initialize_camera()
                if success:
                    from PySide2.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "成功",
                        f"相机初始化成功！\n\n请继续执行：\n② 打开相机 → ③ 开始采集"
                    )
                else:
                    from PySide2.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "失败",
                        "相机初始化失败，请检查Seat配置是否正确。"
                    )
            except Exception as e:
                utils.logger.error(f"   ❌ 初始化相机失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"初始化相机失败:\n{str(e)}")
        else:
            utils.logger.error(
                f"   ❌ 节点没有initialize_camera方法", module="main_window")

    def _camera_open(self, node):
        """打开相机"""
        if hasattr(node, 'open_camera'):
            try:
                success = node.open_camera()
                if success:
                    from PySide2.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "成功",
                        "相机已打开！\n\n请继续执行：\n③ 开始采集"
                    )
                else:
                    from PySide2.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "失败", "打开相机失败，请先初始化相机。")
            except Exception as e:
                utils.logger.error(f"   ❌ 打开相机失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"打开相机失败:\n{str(e)}")
        else:
            utils.logger.error(f"   ❌ 节点没有open_camera方法", module="main_window")

    def _camera_close(self, node):
        """关闭相机"""
        if hasattr(node, 'close_camera'):
            try:
                node.close_camera()
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.information(self, "提示", "相机已关闭。")
            except Exception as e:
                utils.logger.error(f"   ❌ 关闭相机失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"关闭相机失败:\n{str(e)}")
        else:
            utils.logger.error(f"   ❌ 节点没有close_camera方法",
                               module="main_window")

    def _camera_start(self, node):
        """开始采集"""
        if hasattr(node, 'start_acquisition'):
            try:
                node.start_acquisition()
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "成功",
                    "开始连续采集！\n\n现在可以：\n📺 打开实时预览查看图像"
                )
            except Exception as e:
                utils.logger.error(f"   ❌ 开始采集失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"开始采集失败:\n{str(e)}")
        else:
            utils.logger.error(
                f"   ❌ 节点没有start_acquisition方法", module="main_window")

    def _camera_stop(self, node):
        """停止采集"""
        if hasattr(node, 'stop_acquisition'):
            try:
                node.stop_acquisition()
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.information(self, "提示", "采集已停止。")
            except Exception as e:
                utils.logger.error(f"   ❌ 停止采集失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"停止采集失败:\n{str(e)}")
        else:
            utils.logger.error(
                f"   ❌ 节点没有stop_acquisition方法", module="main_window")

    def _open_camera_preview(self, node, option_dialog=None):
        """打开相机预览窗口"""
        # 检查相机是否正在采集，如果未采集则尝试自动启动
        if hasattr(node, '_is_acquiring') and not node._is_acquiring:
            utils.logger.info("   🔄 相机未启动，尝试自动初始化...", module="main_window")

            try:
                # 步骤1: 初始化相机
                if hasattr(node, 'initialize_camera'):
                    if node.initialize_camera():
                        utils.logger.success(
                            "   ✅ 相机初始化成功", module="main_window")
                    else:
                        utils.logger.warning(
                            "   ⚠️ 相机初始化失败，请手动检查Seat配置", module="main_window")

                # 步骤2: 打开相机
                if hasattr(node, 'open_camera'):
                    if node.open_camera():
                        utils.logger.success(
                            "   ✅ 相机已打开", module="main_window")
                    else:
                        utils.logger.warning(
                            "   ⚠️ 打开相机失败", module="main_window")

                # 步骤3: 开始采集
                if hasattr(node, 'start_acquisition'):
                    node.start_acquisition()
                    utils.logger.success("   ✅ 开始连续采集", module="main_window")

            except Exception as e:
                utils.logger.error(f"   ❌ 自动启动相机失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "错误",
                    f"自动启动相机失败:\n{str(e)}\n\n请在预览窗口中手动操作。"
                )

        # 打开预览窗口
        if hasattr(node, 'open_preview_window'):
            try:
                node.open_preview_window()
                utils.logger.success(
                    f"✅ 成功打开相机预览窗口: {node.name()}", module="main_window")
            except Exception as e:
                utils.logger.error(f"   ❌ 打开预览窗口失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "错误",
                    f"打开预览窗口失败:\n{str(e)}"
                )
        else:
            utils.logger.error(
                f"   ❌ 节点没有open_preview_window方法", module="main_window")

        # 关闭选项对话框（如果存在）
        if option_dialog is not None:
            option_dialog.close()

    def _on_workflow_selected(self, **kwargs):
        """
        响应工作流选中事件
        """
        workflow = kwargs.get('workflow')
        if workflow:
            self.status_label.setText(f"📂 {workflow.name}")

    def _on_workflow_executed(self, **kwargs):
        """
        响应工作流执行完成事件
        """
        workflow = kwargs.get('workflow')
        results = kwargs.get('results', {})
        if workflow:
            self.status_label.setText(f"✅ {workflow.name} 执行完成")
        if results:
            utils.logger.success(
                f"执行结果: {len(results)} 个节点输出", module="main_window")

    def _on_workflow_execution_error(self, **kwargs):
        """
        响应工作流执行错误事件
        """
        workflow = kwargs.get('workflow')
        error = kwargs.get('error')
        if workflow:
            self.status_label.setText(f"❌ {workflow.name} 执行失败")
        if error:
            utils.logger.error(f"执行错误: {error}", module="main_window")

    def _on_preview_refresh(self, **kwargs):
        """
        响应预览刷新事件 - 刷新所有打开的预览窗口
        """
        for node_id, preview_window in list(self.preview_windows.items()):
            if hasattr(preview_window, 'refresh'):
                try:
                    preview_window.refresh()
                except Exception as e:
                    utils.logger.error(f"刷新预览窗口失败: {e}", module="main_window")

    def _on_plugin_loaded(self, **kwargs):
        """
        响应插件加载完成事件
        """
        plugins = kwargs.get('plugins', [])
        categories = kwargs.get('categories', set())
        utils.logger.success(
            f"✅ 插件加载完成: {len(plugins)} 个插件, {len(categories)} 个分类", module="main_window")

    def _open_subscriber_manager(self, node, option_dialog=None):
        """打开订阅者管理对话框"""
        if hasattr(node, 'show_subscriber_manager'):
            try:
                node.show_subscriber_manager()
                utils.logger.success(
                    f"✅ 打开订阅者管理器: {node.name()}", module="main_window")
            except Exception as e:
                utils.logger.error(
                    f"   ❌ 打开订阅者管理器失败: {e}", module="main_window")
                from PySide2.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "错误",
                    f"打开订阅者管理器失败:\n{str(e)}"
                )
        else:
            utils.logger.error(
                f"   ❌ 节点没有show_subscriber_manager方法", module="main_window")

        # 关闭选项对话框（如果存在）
        if option_dialog is not None:
            option_dialog.close()
