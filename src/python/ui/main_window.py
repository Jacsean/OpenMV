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
    图像预览对话框
    用于显示OpenCV图像的完整预览
    """
    
    def __init__(self, image, title="图像预览", parent=None):
        super(ImagePreviewDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.image = image
        
        # 设置窗口属性
        self.setMinimumSize(800, 600)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout(self)
        
        # 创建图像标签
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2b2b2b;")
        
        # 添加滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        
        layout.addWidget(scroll_area)
        
        # 添加信息标签
        self.info_label = QtWidgets.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 添加按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("保存图像")
        save_btn.clicked.connect(self.save_image)
        button_layout.addWidget(save_btn)
        
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 显示图像
        self.display_image()
    
    def display_image(self):
        """
        显示图像
        """
        if self.image is None:
            self.image_label.setText("无图像数据")
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
        
        # 缩放图像以适应标签大小，同时保持宽高比
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
    
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
        
        # 连接节点创建信号，用于添加按钮事件处理
        self.node_graph.node_created.connect(self._on_node_created)
        
        # 连接节点双击事件，用于图像预览
        self.node_graph.node_double_clicked.connect(self._on_node_double_clicked)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建菜单栏
        self._create_menu_bar()
        
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
    
    def _on_node_double_clicked(self, node):
        """
        节点双击时的回调函数
        用于显示图像预览对话框
        """
        if isinstance(node, ImageViewNode):
            image = node.get_cached_image()
            if image is not None:
                # 创建并显示预览对话框
                dialog = ImagePreviewDialog(
                    image, 
                    title=f"图像预览 - {node.name()}",
                    parent=self
                )
                dialog.exec_()
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    "该节点尚未处理图像数据\n请先运行节点图"
                )
        
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
