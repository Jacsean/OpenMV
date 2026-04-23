"""
主窗口 - 图形化视觉编程系统的主界面
"""

import sys
from PySide2 import QtWidgets, QtCore, QtGui
from NodeGraphQt import NodeGraph, PropertiesBinWidget, NodesPaletteWidget
import cv2
import numpy as np

from core.graph_engine import GraphEngine
from nodes import (
    ImageLoadNode, 
    ImageSaveNode,
    GrayscaleNode, 
    GaussianBlurNode, 
    CannyEdgeNode,
    ThresholdNode,
    ImageViewNode
)


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
    主窗口类
    """
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 设置窗口属性
        self.setWindowTitle("图形化视觉编程系统")
        self.setGeometry(100, 100, 1600, 900)
        
        # 创建节点图
        self.node_graph = NodeGraph()
        
        # 注册节点类型
        self._register_nodes()
        
        # 创建UI组件
        self._setup_ui()
        
        # 创建执行引擎
        self.engine = GraphEngine()
        
        # 管理打开的预览窗口（用于刷新）
        self.preview_windows = {}  # {node_id: ImagePreviewDialog}
        
    def _register_nodes(self):
        """
        注册所有节点类型
        """
        self.node_graph.register_node(ImageLoadNode)
        self.node_graph.register_node(ImageSaveNode)
        self.node_graph.register_node(GrayscaleNode)
        self.node_graph.register_node(GaussianBlurNode)
        self.node_graph.register_node(CannyEdgeNode)
        self.node_graph.register_node(ThresholdNode)
        self.node_graph.register_node(ImageViewNode)
        
    def _setup_ui(self):
        """
        设置用户界面
        """
        # 创建中央部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        
        # 左侧：节点库面板
        nodes_palette = NodesPaletteWidget(node_graph=self.node_graph)
        nodes_palette.setWindowTitle("节点库")
        
        # 设置标签位置为右侧显示
        try:
            # 尝试作为方法调用
            tab_widget = nodes_palette.tab_widget()
            if hasattr(tab_widget, 'setTabPosition'):
                tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        except (AttributeError, TypeError):
            # 如果tab_widget是属性而非方法，直接访问
            if hasattr(nodes_palette, 'tab_widget'):
                nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        
        dock_nodes = QtWidgets.QDockWidget("节点库", self)
        dock_nodes.setWidget(nodes_palette)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_nodes)
        
        # 中间：节点图画布（主要区域）
        graph_widget = self.node_graph.widget
        main_layout.addWidget(graph_widget, stretch=5)
        
        # 右侧：属性面板
        properties_bin = PropertiesBinWidget(node_graph=self.node_graph)
        properties_bin.setWindowTitle("属性面板")
        dock_properties = QtWidgets.QDockWidget("属性面板", self)
        dock_properties.setWidget(properties_bin)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_properties)
        
        # 连接节点创建信号，用于添加自定义右键菜单
        self.node_graph.node_created.connect(self._on_node_created)
        
        # 连接节点双击事件，用于图像预览
        self.node_graph.node_double_clicked.connect(self._on_node_double_clicked)
        
        # 设置节点上下文菜单（右键菜单）
        self._setup_context_menu()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建菜单栏
        self._create_menu_bar()
        
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
        创建工具栏
        """
        toolbar = self.addToolBar("主工具栏")
        
        # 运行按钮
        run_action = QtWidgets.QAction("▶ 运行", self)
        run_action.setStatusTip("执行节点图")
        run_action.triggered.connect(self.run_graph)
        toolbar.addAction(run_action)
        
        # 清空按钮
        clear_action = QtWidgets.QAction("🗑 清空", self)
        clear_action.setStatusTip("清空节点图")
        clear_action.triggered.connect(self.clear_graph)
        toolbar.addAction(clear_action)
        
        # 保存按钮
        save_action = QtWidgets.QAction("💾 保存", self)
        save_action.setStatusTip("保存节点图")
        save_action.triggered.connect(self.save_graph)
        toolbar.addAction(save_action)
        
        # 加载按钮
        load_action = QtWidgets.QAction("📂 加载", self)
        load_action.setStatusTip("加载节点图")
        load_action.triggered.connect(self.load_graph)
        toolbar.addAction(load_action)
        
        toolbar.addSeparator()
        
        # 缩放适应
        fit_all_action = QtWidgets.QAction("⊞ 适应", self)
        fit_all_action.setStatusTip("适应所有节点")
        fit_all_action.triggered.connect(lambda: self.node_graph.fit_to_selection())
        toolbar.addAction(fit_all_action)
        
    def _create_menu_bar(self):
        """
        创建菜单栏
        """
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        save_action = QtWidgets.QAction("保存", self)
        save_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_action)
        
        load_action = QtWidgets.QAction("加载", self)
        load_action.triggered.connect(self.load_graph)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        clear_action = QtWidgets.QAction("清空", self)
        clear_action.triggered.connect(self.clear_graph)
        edit_menu.addAction(clear_action)
        
        # 运行菜单
        run_menu = menubar.addMenu("运行")
        
        run_action = QtWidgets.QAction("执行", self)
        run_action.triggered.connect(self.run_graph)
        run_menu.addAction(run_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QtWidgets.QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def run_graph(self):
        """
        执行节点图
        """
        print("=" * 50)
        print("开始执行节点图...")
        print("=" * 50)
        
        try:
            # 执行节点图
            results = self.engine.execute_graph(self.node_graph)
            
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
        清空节点图
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认清空",
            "确定要清空当前节点图吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.node_graph.clear_session()
            print("节点图已清空")
            
    def save_graph(self):
        """
        保存节点图
        """
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "保存节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.node_graph.serialize_session(file_path)
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
        加载节点图
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "加载节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.node_graph.deserialize_session(file_path)
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
                
    def _on_node_created(self, node):
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
    
    def _on_node_double_clicked(self, node):
        """
        节点双击时的回调函数
        - IO节点: 弹出文件选择对话框
        - ImageViewNode: 显示图像预览对话框（非模态）
        """
        from nodes.io_nodes import ImageLoadNode, ImageSaveNode
        
        # 处理图像加载节点
        if isinstance(node, ImageLoadNode):
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
            "图形化视觉编程系统\n\n"
            "基于NodeGraphQt和OpenCV构建\n"
            "类似海康、基恩士、康耐视的视觉编程框架\n\n"
            "功能特性:\n"
            "- 可视化节点编程\n"
            "- 实时图像处理\n"
            "- 拖拽式工作流设计\n"
            "- 支持多种图像处理算法"
        )
        
    def closeEvent(self, event):
        """
        窗口关闭事件
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
