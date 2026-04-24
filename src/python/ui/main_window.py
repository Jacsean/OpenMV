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
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide2 import QtWidgets, QtCore, QtGui
from NodeGraphQt import NodeGraph, NodesPaletteWidget, PropertiesBinWidget
import cv2

# 导入核心引擎和工程管理
from core.graph_engine import GraphEngine
from core.project_manager import project_manager

# 导入插件管理器
from plugins.plugin_manager import PluginManager


class ImagePreviewDialog(QtWidgets.QDialog):
    """
    图像预览对话框（非模态）- 增强版
    用于显示OpenCV图像的完整预览
    
    特性:
    - 非模态窗口，可以同时打开多个
    - 支持手动刷新预览
    - 保持与ImageViewNode的关联
    - ✨ 图像缩放控制（原始大小/适应窗口/放大/缩小）
    - ✨ 滚动条支持超大图像
    - ✨ 鼠标拖拽平移
    - ✨ 滚轮缩放快捷键
    """
    
    def __init__(self, image, node=None, title="图像预览", parent=None):
        super(ImagePreviewDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.image = image
        self.node = node  # 关联的ImageViewNode实例
        
        # 缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1   # 最小10%
        self.max_zoom = 5.0   # 最大500%
        self.zoom_step = 1.2  # 缩放步长
        
        # 设置窗口属性
        self.setMinimumSize(800, 600)
        
        # 设置为非模态窗口
        self.setModal(False)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # === 工具栏：缩放控制 ===
        toolbar_layout = QtWidgets.QHBoxLayout()
        
        # 原始大小按钮
        self.original_btn = QtWidgets.QPushButton("📏 原始大小")
        self.original_btn.clicked.connect(self.fit_original)
        self.original_btn.setToolTip("显示图像原始尺寸 (100%)")
        toolbar_layout.addWidget(self.original_btn)
        
        # 适应窗口按钮
        self.fit_btn = QtWidgets.QPushButton("⊞ 适应窗口")
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.fit_btn.setToolTip("缩放图像以适应窗口大小")
        toolbar_layout.addWidget(self.fit_btn)
        
        toolbar_layout.addStretch()
        
        # 缩小按钮
        self.zoom_out_btn = QtWidgets.QPushButton("➖ 缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setToolTip("缩小视图 (快捷键: -)")
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        # 缩放比例显示
        self.zoom_label = QtWidgets.QLabel("100%")
        self.zoom_label.setAlignment(QtCore.Qt.AlignCenter)
        self.zoom_label.setMinimumWidth(60)
        self.zoom_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        toolbar_layout.addWidget(self.zoom_label)
        
        # 放大按钮
        self.zoom_in_btn = QtWidgets.QPushButton("➕ 放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setToolTip("放大视图 (快捷键: +)")
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # === 图像显示区域：QGraphicsView ===
        self.graphics_view = QtWidgets.QGraphicsView()
        self.graphics_view.setStyleSheet("background-color: #2b2b2b;")
        self.graphics_view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        
        # 启用鼠标拖拽平移
        self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        
        # 启用滚动条
        self.graphics_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.graphics_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        # 创建场景
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        
        # 创建图像项
        self.pixmap_item = None
        
        main_layout.addWidget(self.graphics_view)
        
        # === 信息栏 ===
        info_layout = QtWidgets.QHBoxLayout()
        
        # 图像信息标签
        self.info_label = QtWidgets.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignLeft)
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        # 提示标签
        self.hint_label = QtWidgets.QLabel("💡 提示: 滚轮缩放 | 空格+拖拽平移 | 修改参数后点击'▶ 运行'再刷新")
        self.hint_label.setAlignment(QtCore.Qt.AlignRight)
        self.hint_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(self.hint_label)
        
        main_layout.addLayout(info_layout)
        
        # === 底部按钮栏 ===
        button_layout = QtWidgets.QHBoxLayout()
        
        refresh_btn = QtWidgets.QPushButton("🔄 刷新预览")
        refresh_btn.clicked.connect(self.refresh_preview)
        refresh_btn.setToolTip("从关联节点获取最新图像并刷新显示")
        button_layout.addWidget(refresh_btn)
        
        save_btn = QtWidgets.QPushButton("💾 保存图像")
        save_btn.clicked.connect(self.save_image)
        button_layout.addWidget(save_btn)
        
        close_btn = QtWidgets.QPushButton("❌ 关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # 显示图像
        self.display_image()
        
        # 安装事件过滤器以捕获键盘事件
        self.graphics_view.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """
        事件过滤器：处理键盘快捷键
        """
        if obj == self.graphics_view and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Plus or event.key() == QtCore.Qt.Key_Equal:
                # + 键放大
                self.zoom_in()
                return True
            elif event.key() == QtCore.Qt.Key_Minus:
                # - 键缩小
                self.zoom_out()
                return True
            elif event.key() == QtCore.Qt.Key_0:
                # 0 键适应窗口
                self.fit_to_window()
                return True
            elif event.key() == QtCore.Qt.Key_1:
                # 1 键原始大小
                self.fit_original()
                return True
            elif event.key() == QtCore.Qt.Key_Space:
                # 空格键切换拖拽模式
                if self.graphics_view.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
                    self.graphics_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                else:
                    self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
                return True
        
        return super(ImagePreviewDialog, self).eventFilter(obj, event)
    
    def wheelEvent(self, event):
        """
        鼠标滚轮事件：缩放图像
        """
        if event.modifiers() == QtCore.Qt.ControlModifier:
            # Ctrl + 滚轮缩放
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # 正常滚动（由QGraphicsView处理）
            super(ImagePreviewDialog, self).wheelEvent(event)
    
    def zoom_in(self):
        """
        放大图像
        """
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= self.zoom_step
            self.zoom_factor = min(self.zoom_factor, self.max_zoom)
            self.apply_zoom()
    
    def zoom_out(self):
        """
        缩小图像
        """
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= self.zoom_step
            self.zoom_factor = max(self.zoom_factor, self.min_zoom)
            self.apply_zoom()
    
    def fit_original(self):
        """
        显示原始大小（100%）
        """
        self.zoom_factor = 1.0
        self.apply_zoom()
    
    def fit_to_window(self):
        """
        适应窗口大小
        """
        if self.pixmap_item is None:
            return
        
        # 重置缩放
        self.zoom_factor = 1.0
        
        # 使用QGraphicsView的fitInView方法
        self.graphics_view.fitInView(self.pixmap_item, QtCore.Qt.KeepAspectRatio)
        
        # 更新缩放因子为实际值
        transform = self.graphics_view.transform()
        self.zoom_factor = transform.m11()
        
        self.update_zoom_label()
    
    def apply_zoom(self):
        """
        应用缩放变换
        """
        if self.pixmap_item is None:
            return
        
        # 应用缩放变换
        transform = QtGui.QTransform()
        transform.scale(self.zoom_factor, self.zoom_factor)
        self.pixmap_item.setTransform(transform)
        
        # 更新缩放标签
        self.update_zoom_label()
        
        # 确保图像居中
        self.graphics_view.centerOn(self.pixmap_item)
    
    def update_zoom_label(self):
        """
        更新缩放比例显示
        """
        percentage = int(self.zoom_factor * 100)
        self.zoom_label.setText(f"{percentage}%")
    
    def refresh_preview(self):
        """
        刷新预览：从关联节点获取最新图像
        """
        if self.node is not None:
            # 从节点获取最新的缓存图像
            new_image = self.node.get_cached_image()
            if new_image is not None:
                self.image = new_image.copy()  # 复制图像数据
                self.display_image()
                print(f"✅ 预览已刷新: {self.windowTitle()}")
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "警告",
                    "节点中没有可显示的图像\n请先运行节点图"
                )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "提示",
                "此预览窗口未关联节点\n无法自动刷新"
            )
    
    def display_image(self):
        """
        显示图像（使用QGraphicsView）
        """
        # 清空场景
        self.scene.clear()
        
        if self.image is None:
            # 显示占位文本
            text_item = self.scene.addText("无图像数据")
            text_item.setDefaultTextColor(QtGui.QColor(255, 255, 255))
            return
        
        # 获取图像信息
        height, width = self.image.shape[:2]
        channels = self.image.shape[2] if len(self.image.shape) == 3 else 1
        
        # 更新信息标签
        info_text = f"尺寸: {width}x{height} | 通道: {channels} | 类型: {self.image.dtype}"
        self.info_label.setText(info_text)
        
        # 转换OpenCV图像(BGR)到Qt图像(RGB)
        if channels == 3:
            rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            qt_image = QtGui.QImage(
                rgb_image.data,
                width,
                height,
                width * 3,
                QtGui.QImage.Format_RGB888
            )
        elif channels == 1:
            qt_image = QtGui.QImage(
                self.image.data,
                width,
                height,
                width,
                QtGui.QImage.Format_Grayscale8
            )
        else:
            # 其他情况，转换为BGR再转RGB
            bgr = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            qt_image = QtGui.QImage(
                rgb.data,
                width,
                height,
                width * 3,
                QtGui.QImage.Format_RGB888
            )
        
        # 创建QPixmap
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        
        # 添加到场景
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 重置缩放因子
        self.zoom_factor = 1.0
        
        # 适应窗口显示
        self.fit_to_window()
    
    def save_image(self):
        """
        保存图像
        """
        if self.image is None:
            QtWidgets.QMessageBox.warning(self, "警告", "没有可保存的图像")
            return
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "保存图像",
            "",
            "PNG Files (*.png);;JPG Files (*.jpg);;BMP Files (*.bmp);;All Files (*)"
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.image)
                QtWidgets.QMessageBox.information(
                    self,
                    "成功",
                    f"图像已保存到:\n{file_path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "错误",
                    f"保存失败:\n{str(e)}"
                )
    
    def resizeEvent(self, event):
        """
        窗口大小改变时重新显示图像
        """
        super(ImagePreviewDialog, self).resizeEvent(event)
        self.display_image()


class MainWindow(QtWidgets.QMainWindow):
    """
    主窗口类（v3.0 - 支持多工作流）
    
    特性:
    - 使用QTabWidget管理多个工作流
    - 每个标签页独立的NodeGraph实例
    - 共享节点库和属性面板
    - 集成ProjectManager工程管理
    """
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 设置窗口属性
        self.setWindowTitle("图形化视觉编程系统 v4.0")
        self.setGeometry(100, 100, 1600, 900)
        
        # 初始化工程管理器
        self.project_manager = project_manager
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager()
        
        # 创建执行引擎
        self.engine = GraphEngine()
        
        # 管理打开的预览窗口（用于刷新）
        self.preview_windows = {}  # {node_id: ImagePreviewDialog}
        
        # UI组件引用（将在_setup_ui中创建）
        self.tab_widget = None
        self.nodes_palette = None
        self.properties_bin = None
        
        # 当前激活的NodeGraph（动态更新）
        self.current_node_graph = None
        
        # 创建UI组件
        self._setup_ui()
        
        # 加载插件
        self._load_plugins()
        
        # 创建默认工程和工作流
        self._initialize_default_project()
        
    def _initialize_default_project(self):
        """
        初始化默认工程和工作流
        """
        # 创建新工程
        project = self.project_manager.create_project("默认工程")
        
        # 为第一个工作流创建NodeGraph并添加到标签页
        if project.workflows:
            workflow = project.workflows[0]
            self._add_workflow_tab(workflow)
    
    def _load_plugins(self):
        """
        加载所有已安装的插件
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
    
    def _load_plugins_to_graph(self, node_graph):
        """
        将插件节点加载到指定的NodeGraph，并自动归类
        
        Args:
            node_graph: NodeGraph实例
        """
        if not hasattr(self, '_pending_plugins'):
            return
        
        print("\n🔌 加载插件节点到NodeGraph...")
        new_categories = set()
        
        for plugin_info in self._pending_plugins:
            if plugin_info.enabled:
                success = self.plugin_manager.load_plugin_nodes(
                    plugin_info.name,
                    node_graph
                )
                if success:
                    # 收集新分类
                    for node_def in plugin_info.nodes:
                        new_categories.add(node_def.category)
                    print(f"✅ 插件加载成功: {plugin_info.name}\n")
                else:
                    print(f"❌ 插件加载失败: {plugin_info.name}\n")
        
        # 自动归类插件节点
        if new_categories:
            print(f"\n💡 新增分类: {', '.join(new_categories)}")
            self._auto_categorize_nodes(new_categories)
        
        # 清除待加载标记，避免重复加载
        delattr(self, '_pending_plugins')
    
    def _auto_categorize_nodes(self, categories):
        """
        自动将节点归类到对应的分类标签页
        
        Args:
            categories: 分类名称集合
        """
        if not self.nodes_palette:
            print("⚠️ 节点库面板未初始化")
            return
        
        try:
            tab_widget = self.nodes_palette.tab_widget()
            if not tab_widget:
                print("⚠️ 无法获取标签页控件")
                return
            
            # 获取现有分类
            existing_categories = set()
            for i in range(tab_widget.count()):
                existing_categories.add(tab_widget.tabText(i))
            
            # 创建新分类标签
            for category in categories:
                if category not in existing_categories:
                    # 注意：NodeGraphQt的NodesPaletteWidget不直接支持动态添加分类
                    # 需要在下次启动时才能显示新分类
                    print(f"   ⚠️ 分类 '{category}' 将在下次启动时显示")
                    print(f"   💡 提示：NodeGraphQt限制，需要重启以显示新分类")
                else:
                    print(f"   ✅ 分类 '{category}' 已存在")
                    
        except Exception as e:
            print(f"⚠️ 自动归类失败: {e}")
    
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
        添加工作流标签页
        
        Args:
            workflow: Workflow对象
        """
        # 创建新的NodeGraph实例
        node_graph = NodeGraph()
        
        # 注册基础节点
        self._register_nodes(node_graph)
        
        # 加载插件节点（仅在第一个工作流时加载一次）
        if hasattr(self, '_pending_plugins') and self.tab_widget.count() == 0:
            self._load_plugins_to_graph(node_graph)
        
        # 关联到工作流
        workflow.node_graph = node_graph
        
        # 连接信号
        # 使用默认参数捕获当前的 workflow 对象，防止闭包问题
        node_graph.node_created.connect(lambda n, wf=workflow: self._on_node_created(n, wf))
        node_graph.node_double_clicked.connect(lambda n, wf=workflow: self._on_node_double_clicked(n, wf))
        
        # 获取NodeGraph的widget
        graph_widget = node_graph.widget
        
        # 添加到标签页
        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"
        tab_index = self.tab_widget.addTab(graph_widget, tab_title)
        
        # 如果是第一个标签页，设置为当前激活
        if self.tab_widget.count() == 1:
            self._on_tab_changed(0)
        
        print(f"✅ 添加工作流标签页: {workflow.name}")
        
    def _remove_workflow_tab(self, index):
        """
        移除工作流标签页
        
        Args:
            index: 标签页索引
        """
        if index < 0 or index >= self.tab_widget.count():
            return
            
        # 获取工作流
        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]
            
            # 从工程中移除
            self.project_manager.remove_workflow(index)
            
            # 移除标签页
            self.tab_widget.removeTab(index)
            
            print(f"🗑️ 移除工作流标签页: {workflow.name}")
            
    def _on_tab_changed(self, index):
        """
        标签页切换时的回调
        
        Args:
            index: 新的标签页索引
        """
        if index < 0:
            return
            
        # 更新当前激活的NodeGraph
        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]
            self.current_node_graph = workflow.node_graph
            
            # 注意：NodesPaletteWidget和PropertiesBinWidget不支持动态切换NodeGraph
            # 所以这里只更新引用，不尝试重新绑定
            
            # 更新工程激活索引
            project.set_active_workflow(index)
            
            print(f"🔄 切换到工作流: {workflow.name}")
        
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
        
    def _on_tab_close_requested(self, index):
        """
        标签页关闭请求
        
        Args:
            index: 要关闭的标签页索引
        """
        project = self.project_manager.current_project
        if not project:
            return
            
        workflow = project.get_workflow(index)
        if not workflow:
            return
            
        # 检查是否有未保存的修改
        if workflow.is_modified:
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认关闭",
                f"工作流 '{workflow.name}' 有未保存的修改\n是否保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                # TODO: 实现单个工作流的保存
                pass
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 移除标签页
        self._remove_workflow_tab(index)
        
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
        创建工具栏（v3.0 - 工程管理版本）
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
        创建菜单栏（v3.0 - 工程管理版本）
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
        执行当前激活的节点图
        """
        if not self.current_node_graph:
            QtWidgets.QMessageBox.warning(self, "警告", "没有激活的工作流")
            return

        print("=" * 50)
        print("开始执行节点图...")
        print("=" * 50)
        
        try:
            # 执行节点图
            results = self.engine.execute_graph(self.current_node_graph)
            
            print("=" * 50)
            print("节点图执行完成!")
            print("=" * 50)
            
            # 显示结果摘要
            if results:
                print(f"处理了 {len(results)} 个节点的输出")
                
            # 自动刷新所有打开的预览窗口
            self._refresh_all_previews()
                
        except Exception as e:
            print(f"执行错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 显示错误对话框
            QtWidgets.QMessageBox.critical(
                self,
                "执行错误",
                f"执行节点图时发生错误:\n{str(e)}"
            )
    
    def _refresh_all_previews(self):
        """
        刷新所有打开的预览窗口
        """
        if not self.preview_windows:
            return
        
        refreshed_count = 0
        for node_id, dialog in list(self.preview_windows.items()):
            # 检查窗口是否仍然有效
            if dialog.isVisible():
                dialog.refresh_preview()
                refreshed_count += 1
        
        if refreshed_count > 0:
            print(f"✅ 已自动刷新 {refreshed_count} 个预览窗口")
    
    def clear_graph(self):
        """
        清空当前激活的节点图
        """
        if not self.current_node_graph:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "确认清空",
            "确定要清空当前节点图吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.current_node_graph.clear_session()
            print("节点图已清空")
            
    def save_graph(self):
        """
        保存当前节点图
        """
        if not self.current_node_graph:
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "保存节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # 使用save_session()直接保存
                self.current_node_graph.save_session(file_path)
                
                print(f"节点图已保存到: {file_path}")
                
                QtWidgets.QMessageBox.information(
                    self,
                    "保存成功",
                    f"节点图已保存到:\n{file_path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "保存失败",
                    f"保存节点图时发生错误:\n{str(e)}"
                )
                
    def load_graph(self):
        """
        加载节点图到当前标签页
        """
        if not self.current_node_graph:
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "加载节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # 读取JSON文件，然后使用deserialize_session()
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                self.current_node_graph.deserialize_session(session_data)
                
                print(f"节点图已从 {file_path} 加载")
                
                QtWidgets.QMessageBox.information(
                    self,
                    "加载成功",
                    f"节点图已从:\n{file_path}\n加载"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "加载失败",
                    f"加载节点图时发生错误:\n{str(e)}"
                )
                
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
        # 使用插件系统中的节点类进行判断，或者通过节点类型名称判断
        # 这里为了保持兼容性和解耦，建议通过节点的 type_ 或者基类来判断
        # 假设插件系统中仍然导出了这些类用于类型检查，或者我们使用更通用的方式
        
        # 尝试从插件管理器获取节点类引用进行比较，或者简单地在节点上标记属性
        # 由于是纯插件化，我们可能需要依赖节点的类型字符串或特定属性
        # 这里暂时保留逻辑结构，但移除硬导入。
        # 实际项目中，插件节点通常会继承自特定的基类，或者我们可以通过 node.type_() 来判断
        
        # 获取节点类型标识
        node_type = node.type_()
        
        # 处理图像加载节点 (假设插件中注册的类型为 nodes.io.ImageLoadNode 等)
        if "ImageLoadNode" in node_type or hasattr(node, 'file_path'):
             # 简单的启发式判断：如果有 file_path 属性且是 IO 类节点
            self._on_browse_image_file(node)
            
        # 处理图像保存节点
        elif "ImageSaveNode" in node_type or hasattr(node, 'save_path'):
            self._on_select_save_path(node)
            
        # 处理图像显示节点（原有功能）
        elif "ImageViewNode" in node_type or hasattr(node, 'get_cached_image'):
            if hasattr(node, 'get_cached_image'):
                image = node.get_cached_image()
                if image is not None:
                    # 检查是否已经打开了该节点的预览窗口
                    node_id = node.id  # id是属性，不是方法
                    if node_id in self.preview_windows:
                        # 如果窗口已存在，将其提到前面并刷新
                        existing_dialog = self.preview_windows[node_id]
                        existing_dialog.raise_()
                        existing_dialog.activateWindow()
                        existing_dialog.refresh_preview()
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
                        
                    print(f"📷 打开预览窗口: {node.name()}")
                else:
                    QtWidgets.QMessageBox.information(
                        self,
                        "提示",
                        "该节点尚未处理图像数据\n请先运行节点图"
                    )
            else:
                # 如果不是 ImageViewNode 但也没有 get_cached_image，不做处理
                pass
        else:
            # 其他节点类型，如果需要特殊双击行为可在此扩展
            pass
            
        # 下面是被替换掉的旧代码块，确保逻辑完整
        if False:
            self._on_browse_image_file(node)
            
        # 处理图像保存节点
        elif isinstance(node, ImageSaveNode):
            self._on_select_save_path(node)
            
        # 处理图像显示节点（原有功能）
        elif isinstance(node, ImageViewNode):
            image = node.get_cached_image()
            if image is not None:
                # 检查是否已经打开了该节点的预览窗口
                node_id = node.id  # id是属性，不是方法
                if node_id in self.preview_windows:
                    # 如果窗口已存在，将其提到前面并刷新
                    existing_dialog = self.preview_windows[node_id]
                    existing_dialog.raise_()
                    existing_dialog.activateWindow()
                    existing_dialog.refresh_preview()
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
                    
                print(f"📷 打开预览窗口: {node.name()}")
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    "该节点尚未处理图像数据\n请先运行节点图"
                )
    
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
            "图形化视觉编程系统 v3.0\n\n"
            "基于NodeGraphQt和OpenCV构建\n"
            "类似海康、基恩士、康耐视的视觉编程框架\n\n"
            "功能特性:\n"
            "- 可视化节点编程\n"
            "- 实时图像处理\n"
            "- 拖拽式工作流设计\n"
            "- 多工作流管理\n"
            "- 支持多种图像处理算法"
        )
        
    def run_all_workflows(self):
        """
        执行所有工作流
        """
        project = self.project_manager.current_project
        if not project or not project.workflows:
            QtWidgets.QMessageBox.warning(self, "警告", "没有可执行的工作流")
            return
            
        print("=" * 50)
        print("开始执行所有工作流...")
        print("=" * 50)
        
        success_count = 0
        for i, workflow in enumerate(project.workflows):
            print(f"\n--- 执行工作流 [{i+1}/{len(project.workflows)}]: {workflow.name} ---")
            try:
                if workflow.node_graph:
                    self.engine.execute_graph(workflow.node_graph)
                    success_count += 1
            except Exception as e:
                print(f"❌ 工作流 '{workflow.name}' 执行失败: {e}")
                
        print("\n" + "=" * 50)
        print(f"所有工作流执行完毕. 成功: {success_count}/{len(project.workflows)}")
        print("=" * 50)
        
        # 刷新所有预览
        self._refresh_all_previews()
        
    # === 工程管理方法 ===
    
    def new_project(self):
        """
        创建新工程
        """
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.tab_widget.clear()
        
        # 创建新工程
        self._initialize_default_project()
        
    def open_project(self):
        """
        打开工程（支持单文件.proj格式）
        """
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 选择工程文件（.proj单文件）
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "打开工程",
            "",
            "Project Files (*.proj);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.tab_widget.clear()
        
        print(f"📂 开始打开工程: {file_path}")
        
        # 使用ProjectManager的import_project方法从单文件加载
        project = self.project_manager.import_project(file_path)
        
        if project:
            print(f"✅ 工程已打开: {project.name}")
            print(f"   工作流数量: {len(project.workflows)}")
            
            # 为每个工作流创建标签页
            for workflow in project.workflows:
                # 创建工作流的NodeGraph
                node_graph = NodeGraph()
                self._register_nodes(node_graph)
                workflow.node_graph = node_graph
                
                # 加载节点图数据
                if workflow.file_path:
                    # 注意：导入时工程被解压到临时目录
                    import tempfile
                    import glob
                    temp_base = tempfile.gettempdir()
                    temp_dirs = glob.glob(os.path.join(temp_base, 'proj_import_*'))
                    if temp_dirs:
                        latest_temp = max(temp_dirs, key=os.path.getmtime)
                        wf_full_path = os.path.join(latest_temp, workflow.file_path)
                        
                        if os.path.exists(wf_full_path):
                            try:
                                import json
                                with open(wf_full_path, 'r', encoding='utf-8') as f:
                                    session_data = json.load(f)
                                node_graph.deserialize_session(session_data)
                                print(f"✅ 加载工作流: {workflow.name}")
                            except Exception as e:
                                print(f"❌ 加载工作流失败: {e}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"⚠️ 工作流文件不存在: {wf_full_path}")
                
                # 连接信号
                node_graph.node_created.connect(lambda n, wf=workflow: self._on_node_created(n, wf))
                node_graph.node_double_clicked.connect(lambda n, wf=workflow: self._on_node_double_clicked(n, wf))
                
                # 添加到标签页
                self._add_workflow_tab_to_ui(workflow)
            
            # 激活第一个工作流
            if project.workflows:
                self.tab_widget.setCurrentIndex(0)
                self._on_tab_changed(0)
            
            # 添加到最近工程列表
            self._add_to_recent_projects(os.path.dirname(os.path.abspath(file_path)))
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "错误",
                "无法打开工程文件，请确认文件格式正确"
            )
    
    def save_project(self):
        """
        保存当前工程为单文件（.proj ZIP格式）
        """
        project = self.project_manager.current_project
        if not project:
            QtWidgets.QMessageBox.warning(self, "警告", "没有打开的工程")
            return False
        
        # 如果工程还没有路径，询问保存位置
        if not project.file_path or not project.file_path.endswith('.proj'):
            default_name = f"{project.name}.proj"
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "保存工程",
                default_name,
                "Project Files (*.proj);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # 确保文件扩展名为.proj
            if not file_path.endswith('.proj'):
                file_path += '.proj'
            
            project.file_path = file_path
        
        print(f"💾 开始保存工程: {project.name}")
        print(f"   目标文件: {project.file_path}")
        
        # 使用ProjectManager的export_project方法保存为单文件
        success = self.project_manager.export_project(project.file_path)
        
        if success:
            # 更新标签页标题（移除*号）
            for i in range(self.tab_widget.count()):
                tab_text = self.tab_widget.tabText(i)
                if tab_text.endswith(" *"):
                    self.tab_widget.setTabText(i, tab_text[:-2])
            
            # 添加到最近工程列表
            self._add_to_recent_projects(os.path.dirname(os.path.abspath(project.file_path)))
            
            # 获取文件大小
            try:
                size_bytes = os.path.getsize(project.file_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                print(f"✅ 工程已保存: {project.file_path} ({size_str})")
            except:
                print(f"✅ 工程已保存: {project.file_path}")
            
            QtWidgets.QMessageBox.information(
                self,
                "成功",
                f"工程已保存为单文件:\n{project.file_path}"
            )
            return True
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "错误",
                "保存工程失败，请查看控制台输出"
            )
            return False
    
    def _get_file_size_str(self, file_path: str) -> str:
        """
        获取文件大小的可读字符串
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件大小字符串（如 "2.5 MB"）
        """
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "未知大小"
    
    def _add_to_recent_projects(self, project_path):
        """
        添加工程到最近打开列表
        
        Args:
            project_path: 工程目录路径
        """
        from PySide2 import QtCore
        
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        
        # 获取现有的最近工程列表
        recent_projects = settings.value("recent_projects", [])
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        # 移除重复项
        if project_path in recent_projects:
            recent_projects.remove(project_path)
        
        # 添加到列表开头
        recent_projects.insert(0, project_path)
        
        # 限制最多保存10个
        recent_projects = recent_projects[:10]
        
        # 保存
        settings.setValue("recent_projects", recent_projects)
        print(f"📋 已添加到最近工程列表: {project_path}")
    
    def _get_recent_projects(self):
        """
        获取最近打开的工程列表
        
        Returns:
            list: 工程路径列表
        """
        from PySide2 import QtCore
        
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        recent_projects = settings.value("recent_projects", [])
        
        if isinstance(recent_projects, str):
            return [recent_projects]
        
        return recent_projects if recent_projects else []
    
    def _clear_recent_projects(self):
        """
        清空最近工程列表
        """
        from PySide2 import QtCore
        
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        settings.remove("recent_projects")
        print("🗑️ 已清空最近工程列表")
    
    def _update_recent_projects_menu(self):
        """
        更新最近工程菜单（动态刷新）
        """
        if hasattr(self, 'recent_projects_menu'):
            self.recent_projects_menu.clear()
            self._populate_recent_projects_menu(self.recent_projects_menu)
    
    def _populate_recent_projects_menu(self, recent_menu):
        """
        填充最近工程菜单
        
        Args:
            recent_menu: QMenu对象
        """
        recent_projects = self._get_recent_projects()
        
        if not recent_projects:
            no_recent_action = QtWidgets.QAction("(空)", self)
            no_recent_action.setEnabled(False)
            recent_menu.addAction(no_recent_action)
            return
        
        # 添加工程列表
        for i, project_path in enumerate(recent_projects):
            # 提取工程名称（目录名）
            project_name = os.path.basename(project_path)
            
            action = QtWidgets.QAction(f"{i+1}. {project_name}", self)
            action.setStatusTip(project_path)
            action.triggered.connect(lambda checked, path=project_path: self._open_recent_project(path))
            recent_menu.addAction(action)
        
        recent_menu.addSeparator()
        
        # 清空列表
        clear_action = QtWidgets.QAction("🗑 清空列表", self)
        clear_action.setStatusTip("清空最近工程列表")
        clear_action.triggered.connect(self._clear_recent_projects)
        recent_menu.addAction(clear_action)
    
    def _open_recent_project(self, project_path):
        """
        打开最近的工程
        
        Args:
            project_path: 工程目录路径
        """
        if not os.path.exists(project_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "工程不存在",
                f"工程路径不存在:\n{project_path}\n\n是否从最近列表中移除？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self._remove_from_recent_projects(project_path)
            return
        
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.tab_widget.clear()
        
        # 打开工程
        project = self.project_manager.open_project(project_path)
        
        if project:
            # 为每个工作流创建标签页
            for workflow in project.workflows:
                # 创建工作流的NodeGraph
                node_graph = NodeGraph()
                self._register_nodes(node_graph)
                workflow.node_graph = node_graph
                
                # 加载节点图数据
                if workflow.file_path:
                    wf_full_path = os.path.join(project_path, workflow.file_path)
                    if os.path.exists(wf_full_path):
                        try:
                            import json
                            with open(wf_full_path, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                            node_graph.deserialize_session(session_data)
                            print(f"✅ 加载工作流: {workflow.name}")
                        except Exception as e:
                            print(f"❌ 加载工作流失败: {e}")
                
                # 连接信号
                node_graph.node_created.connect(lambda n, wf=workflow: self._on_node_created(n, wf))
                node_graph.node_double_clicked.connect(lambda n, wf=workflow: self._on_node_double_clicked(n, wf))
                
                # 添加到标签页
                self._add_workflow_tab_to_ui(workflow)
            
            # 激活第一个工作流
            if project.workflows:
                self.tab_widget.setCurrentIndex(0)
                self._on_tab_changed(0)
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "错误",
                "无法打开工程"
            )
    
    def _remove_from_recent_projects(self, project_path):
        """
        从最近工程列表中移除指定工程
        
        Args:
            project_path: 工程目录路径
        """
        from PySide2 import QtCore
        
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        recent_projects = settings.value("recent_projects", [])
        
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        if project_path in recent_projects:
            recent_projects.remove(project_path)
            settings.setValue("recent_projects", recent_projects)
            print(f"🗑️ 已从最近列表中移除: {project_path}")
    
    def add_new_workflow(self):
        """
        添加新的工作流
        """
        project = self.project_manager.current_project
        if not project:
            QtWidgets.QMessageBox.warning(self, "警告", "没有打开的工程")
            return
        
        # 创建工作流
        workflow_name = f"工作流 {len(project.workflows) + 1}"
        workflow = self.project_manager.add_new_workflow(workflow_name)
        
        if workflow:
            # 创建NodeGraph
            node_graph = NodeGraph()
            self._register_nodes(node_graph)
            workflow.node_graph = node_graph
            
            # 连接信号
            node_graph.node_created.connect(lambda n, wf=workflow: self._on_node_created(n, wf))
            node_graph.node_double_clicked.connect(lambda n, wf=workflow: self._on_node_double_clicked(n, wf))
            
            # 添加到UI
            self._add_workflow_tab_to_ui(workflow)
            
            # 切换到新标签页
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
            self._on_tab_changed(self.tab_widget.count() - 1)
            
    def close_current_workflow(self):
        """
        关闭当前工作流
        """
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self._on_tab_close_requested(current_index)
            
    def rename_current_workflow(self):
        """
        重命名当前工作流
        """
        project = self.project_manager.current_project
        if not project:
            return
        
        current_index = self.tab_widget.currentIndex()
        workflow = project.get_workflow(current_index)
        
        if not workflow:
            return
        
        # 弹出输入对话框
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "重命名工作流",
            "请输入新的工作流名称:",
            QtWidgets.QLineEdit.Normal,
            workflow.name
        )
        
        if ok and new_name:
            old_name = workflow.name
            workflow.name = new_name
            workflow.mark_modified()
            
            # 更新标签页标题
            tab_title = new_name
            if workflow.is_modified:
                tab_title += " *"
            self.tab_widget.setTabText(current_index, tab_title)
            
            print(f"✅ 工作流已重命名: {old_name} -> {new_name}")
            
    def _add_workflow_tab_to_ui(self, workflow):
        """
        将工作流添加到UI标签页
        
        Args:
            workflow: Workflow对象
        """
        graph_widget = workflow.node_graph.widget
        
        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"
            
        self.tab_widget.addTab(graph_widget, tab_title)
        
    def fit_to_selection(self):
        """
        适应当前工作流的所有节点
        """
        if self.current_node_graph:
            self.current_node_graph.fit_to_selection()
    
    # === 插件管理方法 ===
    
    def install_plugin(self):
        """
        从ZIP文件安装插件
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择插件ZIP文件",
            "",
            "插件文件 (*.zip);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        print(f"\n📦 开始安装插件: {file_path}")
        
        # 执行安装
        success, message = self.plugin_manager.install_plugin_from_zip(file_path)
        
        if success:
            QtWidgets.QMessageBox.information(
                self,
                "安装成功",
                f"{message}\n\n请重启程序以加载新插件。"
            )
            print(f"✅ {message}")
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "安装失败",
                message
            )
            print(f"❌ {message}")
    
    def manage_plugins(self):
        """
        显示插件管理对话框
        """
        plugins = self.plugin_manager.get_installed_plugins()
        
        if not plugins:
            QtWidgets.QMessageBox.information(
                self,
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
        dialog = QtWidgets.QDialog(self)
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
        """
        plugin_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "卸载插件",
            "请输入要卸载的插件名称:"
        )
        
        if ok and plugin_name:
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认卸载",
                f"确定要卸载插件 '{plugin_name}' 吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                success, message = self.plugin_manager.uninstall_plugin(plugin_name)
                
                if success:
                    QtWidgets.QMessageBox.information(self, "成功", message)
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.critical(self, "失败", message)
    
    def reload_plugins(self):
        """
        重新扫描并加载插件
        """
        print("\n🔄 重新扫描插件...")
        
        # 停止所有热重载监听
        self.plugin_manager.hot_reloader.stop_all()
        
        # 重新扫描
        plugins = self.plugin_manager.scan_plugins()
        
        print(f"✅ 扫描到 {len(plugins)} 个插件")
        
        # 重新加载到当前NodeGraph
        if self.current_node_graph:
            for plugin_info in plugins:
                if plugin_info.enabled:
                    self.plugin_manager.load_plugin_nodes(
                        plugin_info.name,
                        self.current_node_graph
                    )
        
        QtWidgets.QMessageBox.information(
            self,
            "刷新完成",
            f"已重新加载 {len(plugins)} 个插件。\n\n注意：UI分类可能需要重启程序才能完全更新。"
        )
    
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