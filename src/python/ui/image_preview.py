"""
图像预览对话框模块

提供增强版的图像预览功能，支持：
- 非模态窗口，可同时打开多个
- 图像缩放控制（原始大小/适应窗口/放大/缩小）
- 滚动条支持超大图像
- 鼠标拖拽平移
- 滚轮缩放快捷键
- 与ImageViewNode关联，支持实时刷新
- ✨ 交互式标注功能（矩形、圆形、文字等）
- ✨ ROI和Mask管理模式
"""


import cv2
import numpy as np
import json
from PySide2 import QtWidgets, QtCore, QtGui
from .image_annotation import Annotation, AnnotationLayer

# 导入图形数据结构
from core.shapes import BaseShape, AnnotationShape, ROIShape, MaskShape, ShapeContainer

# 导入翻译管理器
from language.translator import TranslatorManager


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
    - ✨ 交互式标注工具（矩形、圆形、文字）
    """
    
    def __init__(self, image, node=None, title="图像预览", parent=None):
        super(ImagePreviewDialog, self).__init__(parent)
        self._translator = TranslatorManager()
        self.setWindowTitle(self._translator.get_ui("dialogs.image_preview.title", "图像预览"))
        self.image = image
        self.node = node  # 关联的ImageViewNode实例
        
        # 缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1   # 最小10%
        self.max_zoom = 5.0   # 最大500%
        self.zoom_step = 1.2  # 缩放步长
        
        # === 图形容器管理 BEGIN ===
        self.container = ShapeContainer()
        # === 图形容器管理 END ===
        
        # 兼容旧代码：保留annotation_layer引用（后续逐步迁移）
        self.annotation_layer = AnnotationLayer()

        # 绘图与交互状态
        self.current_pen_color = (255, 0, 0)  # BGR格式：red
        self.current_drawing_rect = None  # 当前正在绘制的形状（用于实时预览）
        self.drawing_start_pos = None  # 绘制起始位置（用于矩形/圆形绘制）
        self.HANDLE_SIZE = 8  # 手柄大小（像素）
        self.is_drawing_polygon = False  # 是否正在绘制多边形
        self.polygon_points = []  # 多边形顶点列表（场景坐标）
        self.polygon_temp_lines = []  # 临时线段列表（用于橡皮筋效果）
        self.temp_text_dialog = None  # 文本输入对话框
        
        # === 工具状态管理 BEGIN ===
        self.current_tool = None  # 当前激活的工具: 'rect', 'circle', 'polygon', 'text'
        self.current_mode = 'annotations'  # 当前模式: 'annotations', 'rois', 'masks'
        # === 工具状态管理 END ===
        
        # 设置窗口属性
        self.setMinimumSize(1024, 768)
        
        # 设置为非模态窗口
        self.setModal(False)
        
        # 创建主布局（保存为实例属性）
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # 创建工具栏
        self._Create_toolbar()

        # 创建图像显示区域
        self._Create_graphics_view()
      
        # 创建信息栏
        self._Create_info_bar()
        
        # 安装事件过滤器以捕获键盘事件
        self.graphics_view.installEventFilter(self)

        # 显示图像
        self.display_image()
    
    def _Create_toolbar(self):
        """
        工具栏布局：缩放控制
        """
        t = self._translator.get_ui

        # === 工具栏：缩放控制 BEGIN===
        toolbar_layout = QtWidgets.QHBoxLayout()
       
        save_btn = QtWidgets.QPushButton("💾 " + t("dialogs.image_preview.save", "保存图像"))
        save_btn.clicked.connect(self.save_image)
        save_btn.setToolTip(t("dialogs.image_preview.save_tip", "保存当前图像"))        
        save_btn.setStyleSheet("width: 100px;")
        toolbar_layout.addWidget(save_btn)

        refresh_btn = QtWidgets.QPushButton("🔄 " + t("dialogs.image_preview.refresh", "刷新预览"))
        refresh_btn.clicked.connect(self.refresh_preview)
        refresh_btn.setToolTip(t("dialogs.image_preview.refresh_tip", "从关联节点获取最新图像并刷新显示"))
        toolbar_layout.addWidget(refresh_btn)
     
        # 分隔线
        separator_window = QtWidgets.QFrame()
        separator_window.setFrameShape(QtWidgets.QFrame.VLine)
        separator_window.setFrameShadow(QtWidgets.QFrame.Sunken)
        toolbar_layout.addWidget(separator_window)
                  
        # 适应窗口按钮
        self.fit_btn = QtWidgets.QPushButton("⊞ " + t("dialogs.image_preview.fit_window", "适应窗口"))
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.fit_btn.setToolTip(t("dialogs.image_preview.fit_window_tip", "缩放图像以适应窗口大小"))
        toolbar_layout.addWidget(self.fit_btn)
        
        # 原始大小按钮
        self.original_btn = QtWidgets.QPushButton("📏 " + t("dialogs.image_preview.original_size", "原始大小"))
        self.original_btn.clicked.connect(self.fit_original)
        self.original_btn.setToolTip(t("dialogs.image_preview.original_size_tip", "显示图像原始尺寸 (100%)"))
        toolbar_layout.addWidget(self.original_btn)
        
        # 缩小按钮
        self.zoom_out_btn = QtWidgets.QPushButton("➖ " + t("dialogs.image_preview.zoom_out", "缩小"))
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setToolTip(t("dialogs.image_preview.zoom_out_tip", "缩小视图 (快捷键: -)"))
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        # 缩放比例显示
        self.zoom_label = QtWidgets.QLabel("100%")
        self.zoom_label.setAlignment(QtCore.Qt.AlignCenter)
        self.zoom_label.setMinimumWidth(60)
        self.zoom_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        toolbar_layout.addWidget(self.zoom_label)
        
        # 放大按钮
        self.zoom_in_btn = QtWidgets.QPushButton("➕ " + t("dialogs.image_preview.zoom_in", "放大"))
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setToolTip(t("dialogs.image_preview.zoom_in_tip", "放大视图 (快捷键: +)"))
        toolbar_layout.addWidget(self.zoom_in_btn)
     
        # 分隔线
        separator_window = QtWidgets.QFrame()
        separator_window.setFrameShape(QtWidgets.QFrame.VLine)
        separator_window.setFrameShadow(QtWidgets.QFrame.Sunken)
        toolbar_layout.addWidget(separator_window)
               
        # 添加一个可伸缩的空白空间，通常用来将其他控件推向布局的一端
        toolbar_layout.addStretch()
        
        # 最大化按钮
        self.maximize_btn = QtWidgets.QPushButton("⬜ " + t("dialogs.image_preview.maximize", "最大化"))
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.maximize_btn.setToolTip(t("dialogs.image_preview.maximize_tip", "切换窗口最大化/恢复"))
        toolbar_layout.addWidget(self.maximize_btn)
     
        # 主布局中加入工具栏：缩放控制
        self.main_layout.addLayout(toolbar_layout)
        # === 工具栏：缩放控制 END===


        # === 模式选择工具栏 BEGIN ===
        mode_toolbar = QtWidgets.QHBoxLayout()
        
        # 显示控制下拉菜单（唯一的模式选择方式）
        self.visibility_btn = QtWidgets.QPushButton("✏️ " + t("dialogs.image_preview.annotations", "标注"))
        self.visibility_menu = QtWidgets.QMenu()
        
        # 使用 QActionGroup 实现单选互斥
        self.mode_action_group = QtWidgets.QActionGroup(self)
        self.mode_action_group.setExclusive(True)
        
        self.show_annotations_action = self.visibility_menu.addAction("✏️ " + t("dialogs.image_preview.annotations", "标注"))
        self.show_annotations_action.setCheckable(True)
        self.show_annotations_action.setChecked(True)
        self.show_annotations_action.setActionGroup(self.mode_action_group)
        self.show_annotations_action.triggered.connect(lambda: self.switch_mode('annotations'))
        
        self.show_rois_action = self.visibility_menu.addAction("📐 ROI")
        self.show_rois_action.setCheckable(True)
        self.show_rois_action.setActionGroup(self.mode_action_group)
        self.show_rois_action.triggered.connect(lambda: self.switch_mode('rois'))
        
        self.show_masks_action = self.visibility_menu.addAction("🎭 Mask")
        self.show_masks_action.setCheckable(True)
        self.show_masks_action.setActionGroup(self.mode_action_group)
        self.show_masks_action.triggered.connect(lambda: self.switch_mode('masks'))
        
        self.visibility_btn.setMenu(self.visibility_menu)
        self.visibility_btn.setToolTip(t("dialogs.image_preview.mode_tip", "选择绘图模式（标注/ROI/Mask）"))
        mode_toolbar.addWidget(self.visibility_btn)

        # 分隔线
        separator_mode = QtWidgets.QFrame()
        separator_mode.setFrameShape(QtWidgets.QFrame.VLine)
        separator_mode.setFrameShadow(QtWidgets.QFrame.Sunken)
        mode_toolbar.addWidget(separator_mode)
        
        # 形状工具按钮
        self.rect_tool_btn = QtWidgets.QPushButton("▭ " + t("dialogs.image_preview.rect", "矩形"))
        self.rect_tool_btn.setCheckable(True)
        self.rect_tool_btn.clicked.connect(lambda: self.activate_tool('rect'))
        self.rect_tool_btn.setToolTip(t("dialogs.image_preview.rect_tip", "绘制矩形"))
        mode_toolbar.addWidget(self.rect_tool_btn)
        
        self.circle_tool_btn = QtWidgets.QPushButton("○ " + t("dialogs.image_preview.circle", "圆形"))
        self.circle_tool_btn.setCheckable(True)
        self.circle_tool_btn.clicked.connect(lambda: self.activate_tool('circle'))
        self.circle_tool_btn.setToolTip(t("dialogs.image_preview.circle_tip", "绘制圆形"))
        mode_toolbar.addWidget(self.circle_tool_btn)
        
        self.polygon_tool_btn = QtWidgets.QPushButton("◇ " + t("dialogs.image_preview.polygon", "多边形"))
        self.polygon_tool_btn.setCheckable(True)
        self.polygon_tool_btn.clicked.connect(lambda: self.activate_tool('polygon'))
        self.polygon_tool_btn.setToolTip(t("dialogs.image_preview.polygon_tip", "绘制多边形（逐点点击，双击闭合）"))
        mode_toolbar.addWidget(self.polygon_tool_btn)
        
        self.text_tool_btn = QtWidgets.QPushButton("T " + t("dialogs.image_preview.text", "文字"))
        self.text_tool_btn.setCheckable(True)
        self.text_tool_btn.clicked.connect(lambda: self.activate_tool('text'))
        self.text_tool_btn.setToolTip(t("dialogs.image_preview.text_tip", "添加文字标注"))
        mode_toolbar.addWidget(self.text_tool_btn)
        
        # 添加一个可伸缩的空白空间，通常用来将其他控件推向布局的一端
        mode_toolbar.addStretch()

        # 清除所有图形按钮
        self.clear_all_btn = QtWidgets.QPushButton("🗑 " + t("dialogs.image_preview.clear", "清除"))
        self.clear_all_btn.clicked.connect(self.clear_all_shapes)
        self.clear_all_btn.setToolTip(t("dialogs.image_preview.clear_tip", "清除所有图形（标注/ROI/Mask）"))
        # self.clear_all_btn.setStyleSheet("color: #f44336;")
        mode_toolbar.addWidget(self.clear_all_btn)
        
        # 颜色选择器
        self.color_btn = QtWidgets.QPushButton("🎨 " + t("dialogs.image_preview.color", "颜色"))
        self.color_btn.clicked.connect(self.show_color_picker)
        self.color_btn.setToolTip(t("dialogs.image_preview.color_tip", "选择画笔颜色"))
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(255, 0, 0);
                color: white;
                font-weight: bold;
            }
        """)
        mode_toolbar.addWidget(self.color_btn)
        
        # # 当前颜色显示标签
        # self.current_color_label = QtWidgets.QLabel("RGB(255,0,0)")
        # self.current_color_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.current_color_label.setMinimumWidth(100)
        # self.current_color_label.setStyleSheet("font-size: 10px; color: #888;")
        # mode_toolbar.addWidget(self.current_color_label)
        
        self.main_layout.addLayout(mode_toolbar)

        # === 模式选择工具栏 END ===
        
        # === 属性工具栏 BEGIN ===
        # property_toolbar = QtWidgets.QHBoxLayout()
        
        
        # # 分隔线
        # separator_prop = QtWidgets.QFrame()
        # separator_prop.setFrameShape(QtWidgets.QFrame.VLine)
        # separator_prop.setFrameShadow(QtWidgets.QFrame.Sunken)
        # property_toolbar.addWidget(separator_prop)
        
        # 显示控制下拉菜单
        # self.visibility_btn = QtWidgets.QPushButton("👁 显示")
        # self.visibility_menu = QtWidgets.QMenu()
        # self.show_annotations_action = self.visibility_menu.addAction("☑ 标注")
        # self.show_annotations_action.setCheckable(True)
        # self.show_annotations_action.setChecked(True)
        # self.show_annotations_action.triggered.connect(lambda: self.toggle_visibility('annotations'))
        
        # self.show_rois_action = self.visibility_menu.addAction("☑ ROI")
        # self.show_rois_action.setCheckable(True)
        # self.show_rois_action.setChecked(True)
        # self.show_rois_action.triggered.connect(lambda: self.toggle_visibility('rois'))
        
        # self.show_masks_action = self.visibility_menu.addAction("☑ Mask")
        # self.show_masks_action.setCheckable(True)
        # self.show_masks_action.setChecked(True)
        # self.show_masks_action.triggered.connect(lambda: self.toggle_visibility('masks'))
        
        # self.visibility_btn.setMenu(self.visibility_menu)
        # self.visibility_btn.setToolTip("控制各类图形的可见性")
        # property_toolbar.addWidget(self.visibility_btn)
        
        # # 导出按钮
        # self.export_btn = QtWidgets.QPushButton("📤 导出")
        # self.export_btn.clicked.connect(self.export_to_node)
        # self.export_btn.setToolTip("将ROI和Mask数据导出到节点")
        # self.export_btn.setStyleSheet("color: #4CAF50; font-weight: bold;")
        # property_toolbar.addWidget(self.export_btn)
        
        # # 清除所有图形按钮
        # self.clear_all_btn = QtWidgets.QPushButton("🗑 清除")
        # self.clear_all_btn.clicked.connect(self.clear_all_shapes)
        # self.clear_all_btn.setToolTip("清除所有图形（标注/ROI/Mask）")
        # self.clear_all_btn.setStyleSheet("color: #f44336;")
        # property_toolbar.addWidget(self.clear_all_btn)
        
        # property_toolbar.addStretch()
        
        # self.main_layout.addLayout(property_toolbar)
        # === 属性工具栏 END ===
        
        # === 底部按钮栏 ===
        # button_layout = QtWidgets.QHBoxLayout()
        
        
        # export_roi_btn = QtWidgets.QPushButton("📤 导出")
        # export_roi_btn.clicked.connect(self.export_to_node)
        # export_roi_btn.setToolTip("导出ROI和Mask数据到关联的ImageViewNode")
        # export_roi_btn.setStyleSheet("color: #2196F3; font-weight: bold;")
        # button_layout.addWidget(export_roi_btn)
        
        # close_btn = QtWidgets.QPushButton("❌ 关闭")
        # close_btn.clicked.connect(self.close)
        # button_layout.addWidget(close_btn)
        
        # self.main_layout.addLayout(button_layout)

    def _Create_graphics_view(self):
      
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
        
        # 在scene上安装事件过滤器以捕获鼠标事件
        self.scene.installEventFilter(self)
        
        # 创建图像项
        self.pixmap_item = None
        
        self.main_layout.addWidget(self.graphics_view)
        
    def _Create_info_bar(self):
        t = self._translator.get_ui
        
        # === 信息栏 ===
        info_layout = QtWidgets.QHBoxLayout()
        
        # 图像信息标签
        self.info_label = QtWidgets.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignLeft)
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        # 提示标签
        self.hint_label = QtWidgets.QLabel("💡 " + t("dialogs.image_preview.hint", "提示: 滚轮缩放 | 空格+拖拽平移 | 修改参数后点击'▶ 运行'再刷新"))
        self.hint_label.setAlignment(QtCore.Qt.AlignRight)
        self.hint_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(self.hint_label)
        
        self.main_layout.addLayout(info_layout)
    
    def eventFilter(self, obj, event):
        """
        事件过滤器：处理键盘快捷键和鼠标事件
        """
        # 处理graphics_view的键盘事件
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
            elif event.key() == QtCore.Qt.Key_Escape:
                # Esc 键取消多边形绘制或关闭工具
                if self.is_drawing_polygon:
                    self.cancel_polygon_drawing()
                else:
                    self.deactivate_current_tool()
                return True
        
        # 处理scene的鼠标事件（ROI和标注工具）
        if obj == self.scene:
            if event.type() == QtCore.QEvent.GraphicsSceneMousePress:
                # ✅ 将场景坐标转换为视图坐标
                scene_pos = event.scenePos()
                view_pos = self.graphics_view.mapFromScene(scene_pos)
                
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseButtonPress,
                    view_pos,
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                self.mousePressEvent(mouse_event)
                return True
            
            elif event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
                # ✅ 将场景坐标转换为视图坐标
                scene_pos = event.scenePos()
                view_pos = self.graphics_view.mapFromScene(scene_pos)
                
                # 构造 QMouseEvent，使用视图坐标作为 local position
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseMove,
                    view_pos,  # local position (view coordinates)
                    QtCore.Qt.LeftButton if event.buttons() & QtCore.Qt.LeftButton else QtCore.Qt.NoButton,
                    event.buttons(),
                    event.modifiers()
                )
                self.mouseMoveEvent(mouse_event)
                return True
            
            elif event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
                # ✅ 将场景坐标转换为视图坐标
                scene_pos = event.scenePos()
                view_pos = self.graphics_view.mapFromScene(scene_pos)
                
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseButtonRelease,
                    view_pos,
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                self.mouseReleaseEvent(mouse_event)
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
        if self.pixmap_item is None:
            return
        
        # 重置缩放因子
        self.zoom_factor = 1.0
        
        # 重置图像项的变换
        self.pixmap_item.resetTransform()
        
        # 重置视图的变换（清除平移等）
        self.graphics_view.resetTransform()
        
        # 重新应用100%缩放
        transform = QtGui.QTransform()
        transform.scale(self.zoom_factor, self.zoom_factor)
        self.pixmap_item.setTransform(transform)
        
        # 更新缩放标签
        self.update_zoom_label()
        
        # 确保图像居中显示
        self.graphics_view.centerOn(self.pixmap_item)
    
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
        t = self._translator.get_ui
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
                    t("dialogs.image_preview.warning", "警告"),
                    t("dialogs.image_preview.no_image", "节点中没有可显示的图像\n请先运行节点图")
                )
        else:
            QtWidgets.QMessageBox.information(
                self,
                t("dialogs.image_preview.info", "提示"),
                t("dialogs.image_preview.no_node", "此预览窗口未关联节点\n无法自动刷新")
            )
    
    def display_image(self):
        """
        显示图像到场景中
        """
        if self.image is None:
            return
        
        # 清除场景中的所有内容
        self.scene.clear()
        
        # 转换OpenCV图像(BGR)为Qt图像(RGB)
        height, width = self.image.shape[:2]
        
        if len(self.image.shape) == 3:
            # 彩色图像
            bytes_per_line = 3 * width
            qt_image = QtGui.QImage(
                self.image.data,
                width,
                height,
                bytes_per_line,
                QtGui.QImage.Format_RGB888
            ).rgbSwapped()  # BGR -> RGB
        else:
            # 灰度图像
            bytes_per_line = width
            qt_image = QtGui.QImage(
                self.image.data,
                width,
                height,
                bytes_per_line,
                QtGui.QImage.Format_Grayscale8
            )
        
        # 创建pixmap
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        
        # 添加到场景
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 更新信息标签
        channels = self.image.shape[2] if len(self.image.shape) == 3 else 1
        self.info_label.setText(f"图像尺寸: {width}x{height} | 通道数: {channels}")
        
        # 适应窗口显示
        self.fit_to_window()
        
        # 重绘所有图形
        self.redraw_all_shapes()
    
    def save_image(self):
        """
        保存当前显示的图像到文件
        """
        t = self._translator.get_ui
        if self.image is None:
            QtWidgets.QMessageBox.warning(
                self,
                t("dialogs.image_preview.warning", "警告"),
                t("dialogs.image_preview.no_save_image", "没有可保存的图像")
            )
            return
        
        # 打开文件保存对话框
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            t("dialogs.image_preview.save", "保存图像"),
            "",
            t("dialogs.image_preview.image_filter", "图像文件 (*.png *.jpg *.bmp *.tif);;PNG文件 (*.png);;JPEG文件 (*.jpg);;BMP文件 (*.bmp);;TIFF文件 (*.tif)")
        )
        
        if file_path:
            try:
                # 使用OpenCV保存图像
                success = cv2.imwrite(file_path, self.image)
                
                if success:
                    QtWidgets.QMessageBox.information(
                        self,
                        t("dialogs.image_preview.save_success", "保存成功"),
                        t("dialogs.image_preview.saved_to", "图像已保存到：") + f"\n{file_path}"
                    )
                    print(f"✅ 图像已保存: {file_path}")
                else:
                    QtWidgets.QMessageBox.critical(
                        self,
                        t("dialogs.image_preview.save_failed", "保存失败"),
                        t("dialogs.image_preview.save_failed_msg", "图像保存失败，请检查文件格式和路径")
                    )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    t("dialogs.image_preview.save_error", "保存错误"),
                    t("dialogs.image_preview.save_error_msg", "保存图像时发生错误：") + f"\n{str(e)}"
                )
                print(f"❌ 保存图像失败: {e}")
    
    def toggle_maximize(self):
        """
        切换窗口最大化/恢复
        """
        t = self._translator.get_ui
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("⬜ " + t("dialogs.image_preview.maximize", "最大化"))
            self.maximize_btn.setToolTip(t("dialogs.image_preview.maximize_tip", "切换窗口最大化"))
        else:
            self.showMaximized()
            self.maximize_btn.setText("🔲 " + t("dialogs.image_preview.restore", "恢复"))
            self.maximize_btn.setToolTip(t("dialogs.image_preview.restore_tip", "恢复窗口大小"))
    
    def switch_mode(self, mode: str):
        """
        切换模式（绘图/ROI/Mask）
        
        Args:
            mode: 'annotations', 'rois', 'masks'
        """
        # 统一模式名称：将旧格式转换为新格式
        mode_map = {
            'annotation': 'annotations',
            'roi': 'rois',
            'mask': 'masks'
        }
        normalized_mode = mode_map.get(mode, mode)
        
        # 更新容器模式
        self.container.switch_mode(normalized_mode)
        self.current_mode = normalized_mode
        
        # 更新下拉菜单选中状态
        if hasattr(self, 'show_annotations_action'):
            self.show_annotations_action.setChecked(normalized_mode == 'annotations')
        if hasattr(self, 'show_rois_action'):
            self.show_rois_action.setChecked(normalized_mode == 'rois')
        if hasattr(self, 'show_masks_action'):
            self.show_masks_action.setChecked(normalized_mode == 'masks')
        
        # 更新按钮文本显示当前模式
        t = self._translator.get_ui
        if hasattr(self, 'visibility_btn'):
            mode_labels = {
                'annotations': '✏️ ' + t("dialogs.image_preview.annotations", "标注"),
                'rois': '📐 ROI',
                'masks': '🎭 Mask'
            }
            self.visibility_btn.setText(mode_labels.get(normalized_mode, '✏️ ' + t("dialogs.image_preview.annotations", "标注")))
        
        # 清除当前选中的对象
        self.container.clear_selection()
        
        # 关闭当前激活的工具
        self.current_tool = None
        if hasattr(self, 'rect_tool_btn'):
            self.rect_tool_btn.setChecked(False)
        if hasattr(self, 'circle_tool_btn'):
            self.circle_tool_btn.setChecked(False)
        if hasattr(self, 'polygon_tool_btn'):
            self.polygon_tool_btn.setChecked(False)
        if hasattr(self, 'text_tool_btn'):
            self.text_tool_btn.setChecked(False)
        
        # 根据模式更新工具可用性
        self.update_tool_availability(normalized_mode)
        
        # 恢复拖拽模式和光标
        self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
        
        # 重绘
        self.redraw_all_shapes()
    
    def update_tool_availability(self, mode: str):
        """
        根据模式更新工具按钮的可用性
        
        Args:
            mode: 'annotations', 'rois', 'masks'
        """
        # 确保按钮存在
        if not hasattr(self, 'rect_tool_btn'):
            return
            
        if mode == 'annotations':
            # 绘图模式：所有工具可用
            self.rect_tool_btn.setEnabled(True)
            self.circle_tool_btn.setEnabled(True)
            self.polygon_tool_btn.setEnabled(True)
            self.text_tool_btn.setEnabled(True)
            
        elif mode == 'rois':
            # ROI模式：仅矩形可用
            self.rect_tool_btn.setEnabled(True)
            self.circle_tool_btn.setEnabled(False)
            self.polygon_tool_btn.setEnabled(False)
            self.text_tool_btn.setEnabled(False)
            
        elif mode == 'masks':
            # Mask模式：矩形、圆形、多边形可用
            self.rect_tool_btn.setEnabled(True)
            self.circle_tool_btn.setEnabled(True)
            self.polygon_tool_btn.setEnabled(True)
            self.text_tool_btn.setEnabled(False)
    
    def toggle_visibility(self, shape_type: str):
        """
        切换某类图形的可见性
        
        Args:
            shape_type: 'annotations', 'rois', 'masks'
        """
        if shape_type == 'annotations':
            visible = self.show_annotations_action.isChecked()
            for ann in self.container.annotations:
                ann.visible = visible
        elif shape_type == 'rois':
            visible = self.show_rois_action.isChecked()
            for roi in self.container.rois:
                roi.visible = visible
        elif shape_type == 'masks':
            visible = self.show_masks_action.isChecked()
            for mask in self.container.masks:
                mask.visible = visible
        
        self.redraw_all_shapes()
    
    def export_to_node(self):
        """
        导出ROI和Mask数据到节点（Phase 4实现）
        """
        t = self._translator.get_ui
        if not self.node:
            QtWidgets.QMessageBox.warning(
                self,
                t("dialogs.image_preview.warning", "警告"),
                t("dialogs.image_preview.no_node_export", "此预览窗口未关联节点\n无法导出数据")
            )
            return
        
        try:
            # === 1. 导出ROI数据为JSON格式 ===
            roi_json = self._export_roi_to_json()
            self.node.set_roi_data(roi_json)
            
            # === 2. 生成并导出Mask图像 ===
            if self._cached_image is not None:
                mask_image = self._generate_mask_image(self._cached_image.shape[:2])
                self.node.set_mask_image(mask_image)
            else:
                self.node.set_mask_image(None)
            
            # === 3. 显示成功提示 ===
            roi_count = len(self.container.rois)
            mask_count = len(self.container.masks)
            
            message = f"✅ " + t("dialogs.image_preview.export_success", "导出成功！") + "\n\n"
            message += t("dialogs.image_preview.roi_count", "• ROI数量:") + f" {roi_count}\n"
            if roi_count > 0:
                roi_names = [r.name for r in self.container.rois]
                message += f"  - {', '.join(roi_names)}\n"
            
            message += t("dialogs.image_preview.mask_count", "• Mask数量:") + f" {mask_count}\n"
            if mask_count > 0:
                mask_types = [f"{m.type}({m.name})" for m in self.container.masks]
                message += f"  - {', '.join(mask_types)}\n"
            
            message += "\n" + t("dialogs.image_preview.exported_to", "数据已输出到节点端口：") + "\n"
            message += t("dialogs.image_preview.roi_port", "• 'ROI数据' → JSON字符串") + "\n"
            message += t("dialogs.image_preview.mask_port", "• 'Mask图像' → 8位灰度图")
            
            QtWidgets.QMessageBox.information(
                self,
                t("dialogs.image_preview.export_complete", "导出完成"),
                message
            )
            
            print(f"✅ 导出完成: {roi_count}个ROI, {mask_count}个Mask")
            
        except Exception as e:
            error_msg = t("dialogs.image_preview.export_failed", "导出失败:") + f" {str(e)}"
            QtWidgets.QMessageBox.critical(
                self,
                t("dialogs.image_preview.export_error", "导出错误"),
                error_msg
            )
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _export_roi_to_json(self):
        """
        导出ROI数据为JSON字符串
        
        Returns:
            str: JSON格式的ROI数据
        """
        if not self.container.rois:
            return json.dumps([])
        
        rois_data = []
        for roi in self.container.rois:
            if roi.type != 'rect' or len(roi.points) < 2:
                continue
            
            # 计算边界框
            x1, y1 = roi.points[0]
            x2, y2 = roi.points[1]
            
            bbox = {
                'x': min(x1, x2),
                'y': min(y1, y2),
                'width': abs(x2 - x1),
                'height': abs(y2 - y1)
            }
            
            rois_data.append({
                'id': roi.id,
                'name': roi.name,
                'type': 'rect',
                'bbox': bbox
            })
        
        return json.dumps(rois_data, ensure_ascii=False, indent=2)
    
    def _generate_mask_image(self, image_size):
        """
        生成Mask灰度图
        
        Args:
            image_size: (height, width) 元组
        
        Returns:
            np.ndarray: HxW的uint8数组，区域=255，背景=0
        """
        height, width = image_size[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        if not self.container.masks:
            return mask
        
        # 绘制所有Mask形状
        for mask_shape in self.container.masks:
            if mask_shape.type == 'rect' and len(mask_shape.points) >= 2:
                pt1 = (int(mask_shape.points[0][0]), int(mask_shape.points[0][1]))
                pt2 = (int(mask_shape.points[1][0]), int(mask_shape.points[1][1]))
                cv2.rectangle(mask, pt1, pt2, 255, -1)  # -1表示填充
                
            elif mask_shape.type == 'circle' and len(mask_shape.points) >= 2:
                center = (int(mask_shape.points[0][0]), int(mask_shape.points[0][1]))
                edge = (int(mask_shape.points[1][0]), int(mask_shape.points[1][1]))
                radius = int(np.sqrt((edge[0]-center[0])**2 + (edge[1]-center[1])**2))
                cv2.circle(mask, center, radius, 255, -1)
                
            elif mask_shape.type == 'polygon' and len(mask_shape.points) >= 3:
                pts = np.array(mask_shape.points, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)
        
        return mask
    
    def clear_all_shapes(self):
        """
        清除所有图形
        """
        t = self._translator.get_ui
        reply = QtWidgets.QMessageBox.question(
            self,
            t("dialogs.image_preview.confirm_clear", "确认清除"),
            t("dialogs.image_preview.clear_confirm_msg", "确定要清除所有标注、ROI和Mask吗？\n此操作不可撤销。"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.container.annotations.clear()
            self.container.rois.clear()
            self.container.masks.clear()
            self.container.clear_selection()
            self.redraw_all_shapes()
            print("✅ 已清除所有图形")
    
    def redraw_all_shapes(self):
        """
        重绘所有图形
        """
        # 清除场景中的所有图形项（保留背景图像）
        items_to_remove = []
        for item in self.scene.items():
            if hasattr(item, 'is_shape') or hasattr(item, 'is_handle'):
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.scene.removeItem(item)
        
        # 重绘所有图形
        for ann in self.container.annotations:
            if ann.visible:
                self.draw_annotation(ann)
        
        for roi in self.container.rois:
            if roi.visible:
                self.draw_roi(roi)
        
        for mask in self.container.masks:
            if mask.visible:
                self.draw_mask(mask)
    
    def draw_annotation(self, annotation: AnnotationShape):
        """绘制普通标注"""
        color = QtGui.QColor(
            annotation.border_color[2],  # R
            annotation.border_color[1],  # G
            annotation.border_color[0]   # B
        )
        pen = QtGui.QPen(color, annotation.thickness)
        
        if annotation.line_style == 'dashed':
            pen.setStyle(QtCore.Qt.DashLine)
        elif annotation.line_style == 'dotted':
            pen.setStyle(QtCore.Qt.DotLine)
        
        if annotation.type == 'rect' and len(annotation.points) >= 2:
            pt1 = QtCore.QPointF(*annotation.points[0])
            pt2 = QtCore.QPointF(*annotation.points[1])
            rect_item = self.scene.addRect(QtCore.QRectF(pt1, pt2).normalized(), pen)
            rect_item.is_shape = True
            rect_item.shape_id = annotation.id
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_shape and self.container.selected_shape.id == annotation.id:
                self.draw_shape_handles(annotation)
            
        elif annotation.type == 'circle' and len(annotation.points) >= 2:
            center = QtCore.QPointF(*annotation.points[0])
            edge = QtCore.QPointF(*annotation.points[1])
            radius = ((edge.x() - center.x())**2 + (edge.y() - center.y())**2)**0.5
            circle_rect = QtCore.QRectF(
                center.x() - radius, center.y() - radius,
                radius * 2, radius * 2
            )
            circle_item = self.scene.addEllipse(circle_rect, pen)
            circle_item.is_shape = True
            circle_item.shape_id = annotation.id
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_shape and self.container.selected_shape.id == annotation.id:
                self.draw_shape_handles(annotation)
            
        elif annotation.type == 'polygon' and len(annotation.points) >= 3:
            polygon = QtGui.QPolygonF([QtCore.QPointF(*p) for p in annotation.points])
            polygon_item = self.scene.addPolygon(polygon, pen)
            polygon_item.is_shape = True
            polygon_item.shape_id = annotation.id
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_shape and self.container.selected_shape.id == annotation.id:
                self.draw_shape_handles(annotation)
    
    def draw_roi(self, roi: ROIShape):
        """绘制ROI（橙色粗线框）"""
        if roi.type != 'rect' or len(roi.points) < 2:
            return
        
        color = QtGui.QColor(
            roi.border_color[2],  # R
            roi.border_color[1],  # G
            roi.border_color[0]   # B
        )
        pen = QtGui.QPen(color, roi.thickness)
        pen.setStyle(QtCore.Qt.SolidLine)
        
        pt1 = QtCore.QPointF(*roi.points[0])
        pt2 = QtCore.QPointF(*roi.points[1])
        rect_item = self.scene.addRect(QtCore.QRectF(pt1, pt2).normalized(), pen)
        rect_item.is_shape = True
        rect_item.shape_id = roi.id
        rect_item.shape_type = 'roi'
        
        # 如果选中，添加控制点
        if self.container.selected_roi and self.container.selected_roi.id == roi.id:
            self.draw_roi_handles(roi)
    
    def draw_mask(self, mask: MaskShape):
        """绘制Mask（半透明红色覆盖）"""
        border_color = QtGui.QColor(
            mask.border_color[2],  # R
            mask.border_color[1],  # G
            mask.border_color[0]   # B
        )
        fill_color = QtGui.QColor(
            mask.fill_color[2],  # R
            mask.fill_color[1],  # G
            mask.fill_color[0],  # B
            128  # Alpha通道：50%透明度
        )
        
        pen = QtGui.QPen(border_color, mask.thickness)
        brush = QtGui.QBrush(fill_color)
        
        if mask.type == 'rect' and len(mask.points) >= 2:
            pt1 = QtCore.QPointF(*mask.points[0])
            pt2 = QtCore.QPointF(*mask.points[1])
            rect_item = self.scene.addRect(QtCore.QRectF(pt1, pt2).normalized(), pen, brush)
            rect_item.is_shape = True
            rect_item.shape_id = mask.id
            rect_item.shape_type = 'mask'
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_mask and self.container.selected_mask.id == mask.id:
                self.draw_shape_handles(mask)
            
        elif mask.type == 'circle' and len(mask.points) >= 2:
            center = QtCore.QPointF(*mask.points[0])
            edge = QtCore.QPointF(*mask.points[1])
            radius = ((edge.x() - center.x())**2 + (edge.y() - center.y())**2)**0.5
            circle_rect = QtCore.QRectF(
                center.x() - radius, center.y() - radius,
                radius * 2, radius * 2
            )
            circle_item = self.scene.addEllipse(circle_rect, pen, brush)
            circle_item.is_shape = True
            circle_item.shape_id = mask.id
            circle_item.shape_type = 'mask'
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_mask and self.container.selected_mask.id == mask.id:
                self.draw_shape_handles(mask)
            
        elif mask.type == 'polygon' and len(mask.points) >= 3:
            polygon = QtGui.QPolygonF([QtCore.QPointF(*p) for p in mask.points])
            polygon_item = self.scene.addPolygon(polygon, pen, brush)
            polygon_item.is_shape = True
            polygon_item.shape_id = mask.id
            polygon_item.shape_type = 'mask'
            
            # ✅ 如果选中，添加控制点
            if self.container.selected_mask and self.container.selected_mask.id == mask.id:
                self.draw_shape_handles(mask)
    
    def draw_shape_handles(self, shape):
        """
        通用图形手柄绘制方法（支持 rect、circle、polygon）
        
        Args:
            shape: 图形对象（AnnotationShape/ROIShape/MaskShape）
        """
        if shape.type == 'rect' and len(shape.points) >= 2:
            x1, y1 = shape.points[0]
            x2, y2 = shape.points[1]
            
            # 计算8个控制点位置
            handles = {
                'top-left': (min(x1, x2), min(y1, y2)),
                'top-right': (max(x1, x2), min(y1, y2)),
                'bottom-left': (min(x1, x2), max(y1, y2)),
                'bottom-right': (max(x1, x2), max(y1, y2)),
                'top': ((x1 + x2) / 2, min(y1, y2)),
                'bottom': ((x1 + x2) / 2, max(y1, y2)),
                'left': (min(x1, x2), (y1 + y2) / 2),
                'right': (max(x1, x2), (y1 + y2) / 2),
            }
            
        elif shape.type == 'circle' and len(shape.points) >= 2:
            cx, cy = shape.points[0]
            edge_x, edge_y = shape.points[1]
            radius = ((edge_x - cx)**2 + (edge_y - cy)**2)**0.5
            
            # 圆形只有4个控制点（上下左右）
            handles = {
                'top': (cx, cy - radius),
                'bottom': (cx, cy + radius),
                'left': (cx - radius, cy),
                'right': (cx + radius, cy),
            }
            
        elif shape.type == 'polygon' and len(shape.points) >= 3:
            # 多边形在每个顶点处显示控制点
            handles = {}
            for i, (px, py) in enumerate(shape.points):
                handles[f'vertex_{i}'] = (px, py)
        else:
            return
        
        handle_color = QtGui.QColor(255, 255, 0)  # 黄色
        handle_pen = QtGui.QPen(handle_color, 2)
        handle_brush = QtGui.QBrush(handle_color)
        
        for handle_name, (hx, hy) in handles.items():
            handle_size = self.HANDLE_SIZE / self.zoom_factor
            handle_rect = QtCore.QRectF(
                hx - handle_size/2, hy - handle_size/2,
                handle_size, handle_size
            )
            handle_item = self.scene.addRect(handle_rect, handle_pen, handle_brush)
            handle_item.is_handle = True
            handle_item.handle_name = handle_name
    
    def draw_roi_handles(self, roi: ROIShape):
        """绘制ROI的控制点手柄"""
        if len(roi.points) < 2:
            return
        
        x1, y1 = roi.points[0]
        x2, y2 = roi.points[1]
        
        # 计算8个控制点位置
        handles = {
            'top-left': (min(x1, x2), min(y1, y2)),
            'top-right': (max(x1, x2), min(y1, y2)),
            'bottom-left': (min(x1, x2), max(y1, y2)),
            'bottom-right': (max(x1, x2), max(y1, y2)),
            'top': ((x1 + x2) / 2, min(y1, y2)),
            'bottom': ((x1 + x2) / 2, max(y1, y2)),
            'left': (min(x1, x2), (y1 + y2) / 2),
            'right': (max(x1, x2), (y1 + y2) / 2),
        }
        
        handle_color = QtGui.QColor(255, 255, 0)  # 黄色
        handle_pen = QtGui.QPen(handle_color, 2)
        handle_brush = QtGui.QBrush(handle_color)
        
        for handle_name, (hx, hy) in handles.items():
            handle_size = self.HANDLE_SIZE / self.zoom_factor
            handle_rect = QtCore.QRectF(
                hx - handle_size/2, hy - handle_size/2,
                handle_size, handle_size
            )
            handle_item = self.scene.addRect(handle_rect, handle_pen, handle_brush)
            handle_item.is_handle = True
            handle_item.handle_name = handle_name
    
    # === 标注功能方法 BEGIN ===
    
    def show_color_picker(self):
        """
        显示颜色选择器对话框
        """
        # 获取当前颜色
        current_color = QtGui.QColor(
            self.current_pen_color[2],  # R
            self.current_pen_color[1],  # G
            self.current_pen_color[0]   # B
        )
        
        # 打开颜色对话框
        t = self._translator.get_ui
        color = QtWidgets.QColorDialog.getColor(current_color, self, t("dialogs.image_preview.select_color", "选择画笔颜色"))
        
        if color.isValid():
            # 更新当前颜色（转换为BGR格式）
            self.current_pen_color = (color.blue(), color.green(), color.red())
            
            # 更新按钮背景色
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                    color: white;
                    font-weight: bold;
                }}
            """)
            
            # 更新颜色标签
            self.current_color_label.setText(f"RGB({color.red()},{color.green()},{color.blue()})")
            
            print(f"✅ 画笔颜色已更改为: RGB({color.red()}, {color.green()}, {color.blue()})")
    
    def activate_tool(self, tool_name: str):
        """
        激活绘图工具
        
        Args:
            tool_name: 'rect', 'circle', 'polygon', 'text'
        """
        # 检查当前模式是否允许使用该工具
        mode = self.current_mode
        
        t = self._translator.get_ui
        if mode == 'rois' and tool_name != 'rect':
            QtWidgets.QMessageBox.warning(
                self,
                t("dialogs.image_preview.info", "提示"),
                t("dialogs.image_preview.roi_only_rect", "ROI模式下仅支持矩形工具")
            )
            return
        elif mode == 'masks' and tool_name not in ['rect', 'circle', 'polygon']:
            QtWidgets.QMessageBox.warning(
                self,
                t("dialogs.image_preview.info", "提示"),
                t("dialogs.image_preview.mask_only_shapes", "Mask模式下仅支持矩形、圆形、多边形工具")
            )
            return
        
        # 如果点击已激活的工具，则取消激活
        if self.current_tool == tool_name:
            self.current_tool = None
            if hasattr(self, 'rect_tool_btn'):
                self.rect_tool_btn.setChecked(False)
            if hasattr(self, 'circle_tool_btn'):
                self.circle_tool_btn.setChecked(False)
            if hasattr(self, 'polygon_tool_btn'):
                self.polygon_tool_btn.setChecked(False)
            if hasattr(self, 'text_tool_btn'):
                self.text_tool_btn.setChecked(False)
            # 恢复拖拽模式和光标
            self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
            print(f"✅ 工具已关闭")
        else:
            # 激活新工具
            self.current_tool = tool_name
            if hasattr(self, 'rect_tool_btn'):
                self.rect_tool_btn.setChecked(tool_name == 'rect')
            if hasattr(self, 'circle_tool_btn'):
                self.circle_tool_btn.setChecked(tool_name == 'circle')
            if hasattr(self, 'polygon_tool_btn'):
                self.polygon_tool_btn.setChecked(tool_name == 'polygon')
            if hasattr(self, 'text_tool_btn'):
                self.text_tool_btn.setChecked(tool_name == 'text')
            # 禁用拖拽模式，允许绘制
            self.graphics_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            
            # 根据工具类型设置光标（绘制时必须是十字光标）
            if tool_name in ['rect', 'circle', 'polygon']:
                self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
            elif tool_name == 'text':
                self.graphics_view.setCursor(QtCore.Qt.IBeamCursor)
            
            mode_name = self.container._get_mode_name(mode)
            print(f"✅ 已激活工具: {tool_name} ({mode_name}模式)")
    
    def deactivate_current_tool(self):
        """
        取消当前激活的工具，进入空闲模式（可拖动图形）
        """
        if self.current_tool is None:
            return
        
        tool_name = self.current_tool
        self.current_tool = None
        
        # 更新按钮状态
        if hasattr(self, 'rect_tool_btn'):
            self.rect_tool_btn.setChecked(False)
        if hasattr(self, 'circle_tool_btn'):
            self.circle_tool_btn.setChecked(False)
        if hasattr(self, 'polygon_tool_btn'):
            self.polygon_tool_btn.setChecked(False)
        if hasattr(self, 'text_tool_btn'):
            self.text_tool_btn.setChecked(False)
        
        # 恢复拖拽模式和光标
        self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
        
        print(f"✅ 工具已关闭，进入空闲模式（可拖动图形）")
    
    def clear_all_annotations(self):
        """清除所有标注"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认",
            "确定要清除所有标注吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.annotation_layer.clear_all()
            self.redraw_annotations()
            print("✅ 已清除所有标注")
    
    def redraw_annotations(self):
        """重绘所有标注（在场景上）"""
        # 移除旧的标注图形项
        for item in self.scene.items():
            if hasattr(item, 'is_annotation'):
                self.scene.removeItem(item)
        
        # 绘制所有可见标注
        for ann in self.annotation_layer.get_visible_annotations():
            self.draw_annotation_on_scene(ann)
    
    def draw_annotation_on_scene(self, annotation: Annotation):
        """
        在场景上绘制单个标注
        
        Args:
            annotation: 标注对象
        """
        color = QtGui.QColor(*annotation.properties['color'][::-1])  # BGR -> RGB
        thickness = annotation.properties['thickness']
        
        if annotation.type == 'rect' and len(annotation.points) >= 2:
            # 绘制矩形
            start_pos = QtCore.QPointF(*annotation.points[0])
            end_pos = QtCore.QPointF(*annotation.points[1])
            rect = QtCore.QRectF(start_pos, end_pos).normalized()
            
            pen = QtGui.QPen(color, thickness)
            pen.setStyle(QtCore.Qt.SolidLine)
            
            rect_item = self.scene.addRect(rect, pen)
            rect_item.is_annotation = True
            rect_item.annotation_id = annotation.id
            
        elif annotation.type == 'circle' and len(annotation.points) >= 2:
            # 绘制圆形（使用椭圆近似）
            start_pos = QtCore.QPointF(*annotation.points[0])
            end_pos = QtCore.QPointF(*annotation.points[1])
            
            # 计算半径
            radius = ((end_pos.x() - start_pos.x())**2 + (end_pos.y() - start_pos.y())**2)**0.5
            
            pen = QtGui.QPen(color, thickness)
            pen.setStyle(QtCore.Qt.SolidLine)
            
            # 创建椭圆项（中心点 + 半径）
            circle_rect = QtCore.QRectF(
                start_pos.x() - radius,
                start_pos.y() - radius,
                radius * 2,
                radius * 2
            )
            circle_item = self.scene.addEllipse(circle_rect, pen)
            circle_item.is_annotation = True
            circle_item.annotation_id = annotation.id
            
        elif annotation.type == 'text' and len(annotation.points) >= 1:
            # 绘制文字
            pos = QtCore.QPointF(*annotation.points[0])
            text = annotation.properties.get('text', '')
            font_size = annotation.properties.get('font_size', 16)
            
            text_item = self.scene.addText(text)
            text_item.setPos(pos)
            text_item.setDefaultTextColor(color)
            
            font = QtGui.QFont()
            font.setPointSize(font_size)
            text_item.setFont(font)
            
            text_item.is_annotation = True
            text_item.annotation_id = annotation.id
    
    def mousePressEvent(self, event):
        """
        鼠标按下事件：处理图形绘制、选择和编辑
        """
        if not self.graphics_view.underMouse():
            super(ImagePreviewDialog, self).mousePressEvent(event)
            return
        
        view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
        scene_pos = self.graphics_view.mapToScene(view_pos)
        
        # === 多边形绘制逻辑 ===
        if self.current_tool == 'polygon':
            if event.button() == QtCore.Qt.LeftButton:
                if not self.is_drawing_polygon:
                    self.is_drawing_polygon = True
                    self.polygon_points = [scene_pos]
                    print(f"🎨 开始绘制多边形，第1个点: ({int(scene_pos.x())}, {int(scene_pos.y())})")
                else:
                    self.polygon_points.append(scene_pos)
                    print(f"   添加顶点: ({int(scene_pos.x())}, {int(scene_pos.y())})")
                event.accept()
                return
            elif event.button() == QtCore.Qt.RightButton:
                # 右键结束多边形绘制
                if self.is_drawing_polygon and len(self.polygon_points) >= 3:
                    self.finish_polygon_drawing()
                    event.accept()
                    return
        
        # === 文字工具逻辑 ===
        elif self.current_tool == 'text':
            if event.button() == QtCore.Qt.LeftButton:
                self.show_text_input_dialog(view_pos)
                event.accept()
                return
        
        # === 通用图形编辑逻辑 ===
        elif event.button() == QtCore.Qt.LeftButton:
            # 检查是否点击了选中图形的手柄
            if self.container.selected_shape:
                handle = self.container.get_handle_at_position(
                    self.container.selected_shape, scene_pos
                )
                if handle:
                    # 开始调整大小
                    self.container.resize_handle = handle
                    self.container.resize_start_pos = scene_pos
                    print(f"🔧 开始调整图形大小: {handle}")
                    event.accept()
                    return
            
            # 检查是否点击了现有图形
            clicked_shape = self.container.get_shape_at_position(scene_pos)
            if clicked_shape:
                print(f"🔍 点击到图形: {clicked_shape.type} (ID: {clicked_shape.id})")
                # 选中图形
                self.container.select_shape(clicked_shape)
                
                # 检查是否在图形内部（用于移动）
                if self.container.is_point_in_shape(clicked_shape, scene_pos):
                    self.container.is_moving_shape = True
                    # 记录初始鼠标位置（不是偏移量）
                    self.container.shape_move_offset = (scene_pos.x(), scene_pos.y())
                    self.graphics_view.setCursor(QtCore.Qt.ClosedHandCursor)
                    print(f"   → 开始移动图形")
                
                self.redraw_all_shapes()  # ✅ 修复：重绘所有图形（包括container中的）
                event.accept()
                return
            else:
                # 取消选中
                self.container.clear_selection()
                
                # 开始绘制新图形
                if self.current_tool in ['rect', 'circle']:
                    self.drawing_start_pos = view_pos
                    self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
                    print(f"🎨 开始绘制新{self.current_tool}")
                    event.accept()
                    return
        
        super(ImagePreviewDialog, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件：处理实时预览、拖动和调整大小
        """
        if not self.graphics_view.underMouse():
            super(ImagePreviewDialog, self).mouseMoveEvent(event)
            return
        
        view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
        scene_pos = self.graphics_view.mapToScene(view_pos)
        
        # === 调整图形大小 ===
        if self.container.resize_handle and self.container.selected_shape:
            self.container.resize_shape(
                self.container.selected_shape,
                self.container.resize_handle,
                scene_pos
            )
            self.redraw_annotations()
            event.accept()
            return
        
        # === 移动图形 ===
        elif self.container.is_moving_shape and self.container.selected_shape:
            # 计算本次移动的增量（相对于上一次位置）
            if self.container.selected_shape.type in ['rect', 'circle']:
                prev_offset_x, prev_offset_y = self.container.shape_move_offset
                current_x, current_y = scene_pos.x(), scene_pos.y()
                
                # 计算增量
                delta_x = current_x - prev_offset_x
                delta_y = current_y - prev_offset_y
                
                # 应用增量移动
                self.container.move_shape(self.container.selected_shape, delta_x, delta_y)
                
                # 更新偏移量为当前位置
                self.container.shape_move_offset = (current_x, current_y)
            
            # 立即重绘
            self.redraw_all_shapes()  # ✅ 修复：重绘所有图形（包括container中的）
            event.accept()
            return
        
        # === 多边形绘制实时预览 ===
        elif self.is_drawing_polygon and len(self.polygon_points) > 0:
            # 清除旧的临时线
            for line in self.polygon_temp_lines:
                if line.scene() == self.scene:
                    self.scene.removeItem(line)
            self.polygon_temp_lines.clear()
            
            # 绘制橡皮筋线
            last_point = self.polygon_points[-1]
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0), 2)
            pen.setStyle(QtCore.Qt.DashLine)
            
            line_item = self.scene.addLine(
                last_point.x(), last_point.y(),
                scene_pos.x(), scene_pos.y(),
                pen
            )
            self.polygon_temp_lines.append(line_item)
            event.accept()
            return
        
        # === 矩形/圆形绘制实时预览 ===
        elif self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
            # 清除旧预览
            for item in self.scene.items():
                if hasattr(item, 'is_temp_preview'):
                    self.scene.removeItem(item)
            
            color = QtGui.QColor(
                self.current_pen_color[2],
                self.current_pen_color[1],
                self.current_pen_color[0]
            )
            pen = QtGui.QPen(color, 2)
            pen.setStyle(QtCore.Qt.DashLine)
            
            start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
            
            if self.current_tool == 'rect':
                temp_item = self.scene.addRect(
                    QtCore.QRectF(start_scene_pos, scene_pos).normalized(),
                    pen
                )
            elif self.current_tool == 'circle':
                radius = ((scene_pos.x() - start_scene_pos.x())**2 + 
                         (scene_pos.y() - start_scene_pos.y())**2)**0.5
                circle_rect = QtCore.QRectF(
                    start_scene_pos.x() - radius,
                    start_scene_pos.y() - radius,
                    radius * 2,
                    radius * 2
                )
                temp_item = self.scene.addEllipse(circle_rect, pen)
            
            temp_item.is_temp_preview = True
            event.accept()
            return
        
        # === 光标管理 ===
        else:
            # 检查是否悬停在手柄上
            if self.container.selected_shape:
                handle = self.container.get_handle_at_position(
                    self.container.selected_shape, scene_pos
                )
                if handle:
                    self.graphics_view.setCursor(QtCore.Qt.SizeAllCursor)
                elif self.container.is_point_in_shape(self.container.selected_shape, scene_pos):
                    self.graphics_view.setCursor(QtCore.Qt.OpenHandCursor)
                else:
                    self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
            else:
                self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
        
        super(ImagePreviewDialog, self).mouseMoveEvent(event)
    
    def cancel_polygon_drawing(self):
        """
        取消多边形绘制
        """
        # 清除临时线
        for line in self.polygon_temp_lines:
            if line.scene() == self.scene:
                self.scene.removeItem(line)
        self.polygon_temp_lines.clear()
        
        # 重置状态
        self.is_drawing_polygon = False
        self.polygon_points.clear()
        
        print("❌ 已取消多边形绘制")
    
    def finish_polygon_drawing(self):
        """
        完成多边形绘制（右键触发）
        """
        if len(self.polygon_points) < 3:
            QtWidgets.QMessageBox.warning(
                self,
                "提示",
                "多边形至少需要3个顶点"
            )
            return
        
        # 清除临时线
        for line in self.polygon_temp_lines:
            if line.scene() == self.scene:
                self.scene.removeItem(line)
        self.polygon_temp_lines.clear()
        
        # 转换点坐标为整数
        points = [(int(p.x()), int(p.y())) for p in self.polygon_points]
        
        mode = self.container.current_mode
        
        if mode == 'masks':
            # 创建Mask对象
            mask_shape = MaskShape(
                type='polygon',
                points=points,
                border_color=(255, 0, 0),
                fill_color=(255, 0, 0),
                thickness=2
            )
            self.container.add_mask(mask_shape)
            print(f"✅ 已创建Mask多边形: {mask_shape.name}")
        else:
            # 创建普通标注
            annotation = AnnotationShape(
                type='polygon',
                points=points,
                border_color=self.current_pen_color,
                thickness=2
            )
            self.container.add_annotation(annotation)
            print(f"✅ 已创建标注多边形")
        
        # 重置状态
        self.is_drawing_polygon = False
        self.polygon_points.clear()
        
        # ✅ 关键改进：绘制完成后自动取消工具选择
        self.deactivate_current_tool()
        
        self.redraw_all_shapes()
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件：结束拖动、调整或绘制操作
        """
        # === 结束调整大小 ===
        if self.container.resize_handle:
            self.container.resize_handle = None
            self.container.resize_start_pos = None
            print("✅ 调整大小完成")
        
        # === 结束移动 ===
        elif self.container.is_moving_shape:
            self.container.is_moving_shape = False
            self.container.shape_move_offset = None
            self.graphics_view.setCursor(QtCore.Qt.OpenHandCursor)
            print("✅ 移动完成，状态已重置")
        
        # === 结束矩形/圆形绘制 ===
        elif self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
            
            # 清除临时预览
            for item in self.scene.items():
                if hasattr(item, 'is_temp_preview'):
                    self.scene.removeItem(item)
            
            points = [
                (int(start_scene_pos.x()), int(start_scene_pos.y())),
                (int(scene_pos.x()), int(scene_pos.y()))
            ]
            
            mode = self.container.current_mode
            
            if mode == 'rois' and self.current_tool == 'rect':
                # 创建ROI对象（ID自动生成）
                roi_shape = ROIShape(type='rect', points=points)
                self.container.add_roi(roi_shape)
                self.container.select_roi(roi_shape)
                
                # ✅ 先重绘，再显示对话框
                self.redraw_all_shapes()
                
                # ✅ 关键改进：在显示对话框前先取消工具，避免阻塞
                self.deactivate_current_tool()
                
                self.show_roi_name_dialog(roi_shape)
                print(f"✅ 已创建ROI: {roi_shape.name}")
                
            elif mode == 'masks':
                # 创建Mask对象（ID自动生成）
                mask_shape = MaskShape(
                    type=self.current_tool,
                    points=points,
                    border_color=(255, 0, 0),
                    fill_color=(255, 0, 0),
                    thickness=2
                )
                self.container.add_mask(mask_shape)
                print(f"✅ 已创建Mask{self.current_tool}: {mask_shape.name}")
                
            else:
                # 创建普通标注（ID自动生成）
                annotation = AnnotationShape(
                    type=self.current_tool,
                    points=points,
                    border_color=self.current_pen_color,
                    thickness=2
                )
                self.container.add_annotation(annotation)
                print(f"✅ 已创建标注{self.current_tool}")
            
            # 重置绘制状态
            self.drawing_start_pos = None
            
            # ✅ 关键改进：绘制完成后自动取消工具选择，进入空闲模式
            self.deactivate_current_tool()
            
            self.redraw_all_shapes()
