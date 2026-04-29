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
"""

import cv2
from PySide2 import QtWidgets, QtCore, QtGui
from .image_annotation import Annotation, AnnotationLayer


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
        self.setWindowTitle(title)
        self.image = image
        self.node = node  # 关联的ImageViewNode实例
        
        # 缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1   # 最小10%
        self.max_zoom = 5.0   # 最大500%
        self.zoom_step = 1.2  # 缩放步长
        
        # === 标注系统初始化 BEGIN ===
        self.annotation_layer = AnnotationLayer()
        self.current_tool = None  # 当前激活的工具: 'rect', 'circle', 'text', 'roi_rect', 'roi_circle', None
        self.drawing_start_pos = None  # 绘制起始位置（Qt坐标）
        self.current_drawing_rect = None  # 当前正在绘制的形状（用于实时预览）
        self.temp_text_dialog = None  # 文本输入对话框
        
        # 画笔颜色设置（默认为绿色）
        self.current_pen_color = (0, 255, 0)  # BGR格式：绿色
        
        # ROI相关状态
        self.roi_mode = False  # 是否处于ROI模式
        self.selected_roi = None  # 当前选中的ROI
        self.roi_resize_handle = None  # ROI调整手柄: None, 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right'
        self.resize_start_pos = None  # 调整大小起始位置
        self.HANDLE_SIZE = 8  # 手柄大小（像素）
        # === 标注系统初始化 END ===
        
        # 设置窗口属性
        self.setMinimumSize(1024, 768)
        
        # 设置为非模态窗口
        self.setModal(False)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # === 工具栏：缩放控制 BEGIN===
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
        
        # 分隔线
        separator_window = QtWidgets.QFrame()
        separator_window.setFrameShape(QtWidgets.QFrame.VLine)
        separator_window.setFrameShadow(QtWidgets.QFrame.Sunken)
        toolbar_layout.addWidget(separator_window)
        
        # 最大化按钮
        self.maximize_btn = QtWidgets.QPushButton("⬜ 最大化")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.maximize_btn.setToolTip("切换窗口最大化/恢复")
        toolbar_layout.addWidget(self.maximize_btn)
        
        toolbar_layout.addStretch()
        
        # === 标注工具栏 BEGIN ===
        annotation_toolbar = QtWidgets.QHBoxLayout()
        
        # ROI模式切换按钮
        self.roi_mode_btn = QtWidgets.QPushButton("📐 ROI模式")
        self.roi_mode_btn.setCheckable(True)
        self.roi_mode_btn.clicked.connect(self.toggle_roi_mode)
        self.roi_mode_btn.setToolTip("切换到ROI编辑模式（绘制和调整ROI区域）")
        self.roi_mode_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
        """)
        annotation_toolbar.addWidget(self.roi_mode_btn)
        
        # 分隔线
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.VLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Sunken)
        annotation_toolbar.addWidget(separator1)
        
        # 颜色选择器
        self.color_btn = QtWidgets.QPushButton("🎨 颜色")
        self.color_btn.clicked.connect(self.show_color_picker)
        self.color_btn.setToolTip("选择画笔颜色")
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(0, 255, 0);
                color: white;
                font-weight: bold;
            }
        """)
        annotation_toolbar.addWidget(self.color_btn)
        
        # 当前颜色显示标签
        self.current_color_label = QtWidgets.QLabel("RGB(0,255,0)")
        self.current_color_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_color_label.setMinimumWidth(100)
        self.current_color_label.setStyleSheet("font-size: 10px; color: #888;")
        annotation_toolbar.addWidget(self.current_color_label)
        
        # 分隔线
        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.VLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        annotation_toolbar.addWidget(separator2)
        
        # 矩形工具
        self.rect_tool_btn = QtWidgets.QPushButton("▭ 矩形")
        self.rect_tool_btn.setCheckable(True)
        self.rect_tool_btn.clicked.connect(lambda: self.activate_tool('rect'))
        self.rect_tool_btn.setToolTip("绘制矩形标注")
        annotation_toolbar.addWidget(self.rect_tool_btn)
        
        # 圆形工具
        self.circle_tool_btn = QtWidgets.QPushButton("○ 圆形")
        self.circle_tool_btn.setCheckable(True)
        self.circle_tool_btn.clicked.connect(lambda: self.activate_tool('circle'))
        self.circle_tool_btn.setToolTip("绘制圆形标注")
        annotation_toolbar.addWidget(self.circle_tool_btn)
        
        # 文字工具
        self.text_tool_btn = QtWidgets.QPushButton("T 文字")
        self.text_tool_btn.setCheckable(True)
        self.text_tool_btn.clicked.connect(lambda: self.activate_tool('text'))
        self.text_tool_btn.setToolTip("添加文字标注")
        annotation_toolbar.addWidget(self.text_tool_btn)
        
        annotation_toolbar.addStretch()
        
        # 清除所有标注按钮
        self.clear_annotations_btn = QtWidgets.QPushButton("🗑 清除标注")
        self.clear_annotations_btn.clicked.connect(self.clear_all_annotations)
        self.clear_annotations_btn.setToolTip("清除所有标注")
        self.clear_annotations_btn.setStyleSheet("color: #f44336;")
        annotation_toolbar.addWidget(self.clear_annotations_btn)
        
        main_layout.addLayout(annotation_toolbar)
        # === 标注工具栏 END ===
        
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
        # === 工具栏：缩放控制 END===
        
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
        
        export_roi_btn = QtWidgets.QPushButton("📐 导出ROI")
        export_roi_btn.clicked.connect(self.export_roi_to_node)
        export_roi_btn.setToolTip("将ROI数据导出到关联的ImageViewNode")
        export_roi_btn.setStyleSheet("color: #2196F3; font-weight: bold;")
        button_layout.addWidget(export_roi_btn)
        
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
        
        # 处理scene的鼠标事件（ROI和标注工具）
        if obj == self.scene:
            if event.type() == QtCore.QEvent.GraphicsSceneMousePress:
                # 将QGraphicsSceneMouseEvent转换为QMouseEvent并调用mousePressEvent
                screen_pos = event.screenPos()
                # 安全转换：如果已经是QPoint则直接使用，否则调用toPoint()
                pos_point = screen_pos.toPoint() if hasattr(screen_pos, 'toPoint') else screen_pos
                
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseButtonPress,
                    pos_point,
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                self.mousePressEvent(mouse_event)
                return True
            
            elif event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
                screen_pos = event.screenPos()
                pos_point = screen_pos.toPoint() if hasattr(screen_pos, 'toPoint') else screen_pos
                
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseMove,
                    pos_point,
                    QtCore.Qt.NoButton,
                    event.buttons(),
                    event.modifiers()
                )
                self.mouseMoveEvent(mouse_event)
                return True
            
            elif event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
                screen_pos = event.screenPos()
                pos_point = screen_pos.toPoint() if hasattr(screen_pos, 'toPoint') else screen_pos
                
                mouse_event = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseButtonRelease,
                    pos_point,
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
    
    def toggle_maximize(self):
        """
        切换窗口最大化/恢复
        """
        if self.isMaximized():
            # 当前是最大化状态，恢复正常大小
            self.showNormal()
            self.maximize_btn.setText("⬜ 最大化")
            print("✅ 窗口已恢复正常大小")
        else:
            # 当前是正常状态，最大化窗口
            self.showMaximized()
            self.maximize_btn.setText("🔲 恢复")
            print("✅ 窗口已最大化")
    
    def show_color_picker(self):
        """
        显示颜色选择器
        """
        # 将BGR转换为RGB用于Qt颜色对话框
        current_rgb = (
            self.current_pen_color[2],  # R
            self.current_pen_color[1],  # G
            self.current_pen_color[0]   # B
        )
        
        # 创建初始颜色
        initial_color = QtGui.QColor(*current_rgb)
        
        # 打开颜色对话框
        color_dialog = QtWidgets.QColorDialog(self)
        color_dialog.setCurrentColor(initial_color)
        color_dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, False)
        color_dialog.setWindowTitle("选择画笔颜色")
        
        if color_dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_color = color_dialog.selectedColor()
            
            # 将RGB转换回BGR存储
            self.current_pen_color = (
                selected_color.blue(),
                selected_color.green(),
                selected_color.red()
            )
            
            # 更新颜色按钮的背景色
            rgb_tuple = (selected_color.red(), selected_color.green(), selected_color.blue())
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb{rgb_tuple};
                    color: white;
                    font-weight: bold;
                }}
            """)
            
            # 更新颜色标签
            self.current_color_label.setText(f"RGB({selected_color.red()},{selected_color.green()},{selected_color.blue()})")
            
            print(f"✅ 画笔颜色已更改为: RGB{rgb_tuple}")
    
    # === 标注功能方法 BEGIN ===
    
    def activate_tool(self, tool_name: str):
        """
        激活标注工具
        
        Args:
            tool_name: 工具名称 ('rect', 'circle', 'text')
        """
        # 如果点击已激活的工具，则取消激活
        if self.current_tool == tool_name:
            self.current_tool = None
            self.rect_tool_btn.setChecked(False)
            self.circle_tool_btn.setChecked(False)
            self.text_tool_btn.setChecked(False)
            # 恢复拖拽模式和光标
            self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
            print(f"✅ 标注工具已关闭")
        else:
            # 激活新工具
            self.current_tool = tool_name
            self.rect_tool_btn.setChecked(tool_name == 'rect')
            self.circle_tool_btn.setChecked(tool_name == 'circle')
            self.text_tool_btn.setChecked(tool_name == 'text')
            # 禁用拖拽模式，允许绘制
            self.graphics_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            
            # 根据工具类型设置光标（绘制时必须是十字光标）
            if tool_name in ['rect', 'circle']:
                self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
            elif tool_name == 'text':
                self.graphics_view.setCursor(QtCore.Qt.IBeamCursor)
            
            print(f"✅ 已激活工具: {tool_name}")
    
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
        鼠标按下事件：处理ROI选择和调整
        """
        # 检查是否点击了graphics_view内部
        if self.graphics_view.underMouse():
            # 获取相对于graphics_view的位置（已经是QPoint）
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            
            if self.roi_mode:
                # ROI模式下
                if event.button() == QtCore.Qt.LeftButton:
                    # 检查是否点击了现有ROI的手柄
                    if self.selected_roi:
                        handle = self.get_resize_handle(self.selected_roi, scene_pos)
                        if handle:
                            # 开始调整大小 - 保持十字光标
                            self.roi_resize_handle = handle
                            self.resize_start_pos = scene_pos
                            print(f"🔧 开始调整ROI大小: {handle}")
                            event.accept()
                            return
                    
                    # 检查是否点击了现有ROI
                    clicked_roi = self.get_roi_at_position(scene_pos)
                    if clicked_roi:
                        # 选中ROI - 显示手型光标
                        self.selected_roi = clicked_roi
                        self.graphics_view.setCursor(QtCore.Qt.OpenHandCursor)
                        print(f"✅ 选中ROI: {clicked_roi.id}")
                        self.redraw_annotations()
                        event.accept()
                        return
                    else:
                        # 取消选中 - 开始绘制，显示十字光标
                        self.selected_roi = None
                        self.drawing_start_pos = view_pos
                        self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
                        print("🎨 开始绘制新ROI")
                        event.accept()
                        return
            
            elif self.current_tool in ['rect', 'circle']:
                # 普通标注模式 - 保持十字光标
                self.drawing_start_pos = view_pos
                event.accept()
                return
                
            elif self.current_tool == 'text':
                # 文字工具
                self.show_text_input_dialog(view_pos)
                event.accept()
                return
        
        super(ImagePreviewDialog, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件：处理ROI调整和实时预览
        """
        if self.graphics_view.underMouse():
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            
            if self.roi_mode:
                # ROI模式下的光标控制
                if self.roi_resize_handle and self.selected_roi:
                    # 正在调整ROI大小 - 保持十字光标
                    delta_x = scene_pos.x() - self.resize_start_pos.x()
                    delta_y = scene_pos.y() - self.resize_start_pos.y()
                    
                    # 根据手柄类型调整ROI
                    self.resize_roi(self.selected_roi, self.roi_resize_handle, delta_x, delta_y)
                    
                    # 更新起始位置
                    self.resize_start_pos = scene_pos
                    
                    # 重绘
                    self.redraw_annotations()
                    event.accept()
                    return
                
                elif self.selected_roi:
                    # 检查是否悬停在控制点上 - 显示手型光标
                    handle = self.get_resize_handle(self.selected_roi, scene_pos)
                    if handle:
                        self.graphics_view.setCursor(QtCore.Qt.SizeAllCursor)  # 手型光标（调整大小）
                    else:
                        # 检查是否在ROI内部 - 显示手型光标
                        if self.is_point_in_roi(self.selected_roi, scene_pos):
                            self.graphics_view.setCursor(QtCore.Qt.OpenHandCursor)  # 手型光标（移动）
                        else:
                            self.graphics_view.setCursor(QtCore.Qt.CrossCursor)  # 十字光标（绘制）
                else:
                    # 没有选中ROI - 十字光标（准备绘制）
                    self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
            
            elif self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
                # 普通标注模式的实时预览 - 保持十字光标
                for item in self.scene.items():
                    if hasattr(item, 'is_temp_preview'):
                        self.scene.removeItem(item)
                
                color = QtGui.QColor(
                    self.current_pen_color[2],  # R
                    self.current_pen_color[1],  # G
                    self.current_pen_color[0]   # B
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
        
        super(ImagePreviewDialog, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件：完成绘制
        """
        if self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
            # 获取结束位置
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            
            # 转换为场景坐标（view_pos已经是QPoint，不需要.toPoint()）
            start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
            end_scene_pos = self.graphics_view.mapToScene(view_pos)

            # 创建标注对象 - 使用当前选择的颜色
            annotation = Annotation(
                type=self.current_tool,
                points=[
                    (int(start_scene_pos.x()), int(start_scene_pos.y())),
                    (int(end_scene_pos.x()), int(end_scene_pos.y()))
                ],
                properties={
                    'color': self.current_pen_color,  # 使用当前选择的颜色 BGR
                    'thickness': 2
                }
            )
            
            # 添加到标注层
            self.annotation_layer.add_annotation(annotation)
            
            # 清除临时预览
            for item in self.scene.items():
                if hasattr(item, 'is_temp_preview'):
                    self.scene.removeItem(item)
            
            # 重绘所有标注
            self.redraw_annotations()
            
            # 重置状态
            self.drawing_start_pos = None
            
            print(f"✅ 已创建{self.current_tool}标注")
            event.accept()
            return
        
        super(ImagePreviewDialog, self).mouseReleaseEvent(event)
    
    def show_text_input_dialog(self, view_pos):
        """
        显示文本输入对话框
        
        Args:
            view_pos: 视图坐标位置（QPoint类型）
        """
        # 转换为场景坐标（view_pos已经是QPoint，不需要.toPoint()）
        scene_pos = self.graphics_view.mapToScene(view_pos)

        # 创建输入对话框
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "添加文字标注",
            "请输入文字内容:",
            QtWidgets.QLineEdit.Normal,
            "标注文字"
        )
        
        if ok and text:
            # 创建文字标注
            annotation = Annotation(
                type='text',
                points=[(int(scene_pos.x()), int(scene_pos.y()))],
                properties={
                    'color': (0, 255, 0),  # 绿色 BGR
                    'thickness': 2,
                    'text': text,
                    'font_size': 16
                }
            )
            
            # 添加到标注层
            self.annotation_layer.add_annotation(annotation)
            
            # 重绘所有标注
            self.redraw_annotations()
            
            print(f"✅ 已创建文字标注: {text}")
    
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
        
        # 重绘标注（如果有）
        self.redraw_annotations()
    
    # === 标注功能方法 END ===

    # === ROI功能方法 BEGIN ===
    
    def toggle_roi_mode(self):
        """
        切换ROI模式
        """
        self.roi_mode = self.roi_mode_btn.isChecked()
        
        if self.roi_mode:
            # 进入ROI模式：禁用其他工具
            self.current_tool = None
            self.rect_tool_btn.setChecked(False)
            self.circle_tool_btn.setChecked(False)
            self.text_tool_btn.setChecked(False)
            
            # 设置光标为十字形
            self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
            
            print("✅ ROI模式已启用：点击绘制ROI，拖动调整大小")
        else:
            # 退出ROI模式
            self.selected_roi = None
            self.roi_resize_handle = None
            
            # 恢复默认光标
            self.graphics_view.setCursor(QtCore.Qt.ArrowCursor)
            
            # 恢复拖拽模式
            self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            
            print("✅ ROI模式已关闭")
        
        # 重绘以更新显示
        self.redraw_annotations()
    
    def get_roi_at_position(self, scene_pos):
        """
        获取指定位置的ROI
        
        Args:
            scene_pos: 场景坐标 QPointF
            
        Returns:
            Annotation or None: ROI对象，如果未找到则返回None
        """
        # 遍历所有ROI标注（假设type为'roi_rect'或'roi_circle'）
        for ann in reversed(self.annotation_layer.annotations):
            if ann.type in ['roi_rect', 'roi_circle']:
                if self.is_point_in_roi(ann, scene_pos):
                    return ann
        return None
    
    def is_point_in_roi(self, roi, point):
        """
        判断点是否在ROI内
        
        Args:
            roi: ROI标注对象
            point: QPointF坐标
            
        Returns:
            bool: 是否在ROI内
        """
        if roi.type == 'roi_rect' and len(roi.points) >= 2:
            # 矩形ROI
            x1, y1 = roi.points[0]
            x2, y2 = roi.points[1]
            rect = QtCore.QRectF(
                min(x1, x2), min(y1, y2),
                abs(x2 - x1), abs(y2 - y1)
            )
            return rect.contains(point)
            
        elif roi.type == 'roi_circle' and len(roi.points) >= 2:
            # 圆形ROI
            center_x, center_y = roi.points[0]
            edge_x, edge_y = roi.points[1]
            radius = ((edge_x - center_x)**2 + (edge_y - center_y)**2)**0.5
            
            distance = ((point.x() - center_x)**2 + (point.y() - center_y)**2)**0.5
            return distance <= radius
        
        return False
    
    def get_resize_handle(self, roi, scene_pos):
        """
        获取ROI的调整手柄位置
        
        Args:
            roi: ROI标注对象
            scene_pos: 场景坐标
            
        Returns:
            str or None: 手柄名称 ('top-left', 'top-right', etc.) 或 None
        """
        if roi.type != 'roi_rect' or len(roi.points) < 2:
            return None
        
        x1, y1 = roi.points[0]
        x2, y2 = roi.points[1]
        
        # 计算矩形的8个控制点
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
        
        # 检查鼠标是否在手柄附近
        for handle_name, (hx, hy) in handles.items():
            distance = ((scene_pos.x() - hx)**2 + (scene_pos.y() - hy)**2)**0.5
            if distance <= self.HANDLE_SIZE / self.zoom_factor:
                return handle_name
        
        return None
    
    def mousePressEvent(self, event):
        """
        鼠标按下事件：处理ROI选择和调整
        """
        # 检查是否点击了graphics_view内部
        if self.graphics_view.underMouse():
            # 获取相对于graphics_view的位置（已经是QPoint）
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            
            if self.roi_mode:
                # ROI模式下
                if event.button() == QtCore.Qt.LeftButton:
                    # 检查是否点击了现有ROI的手柄
                    if self.selected_roi:
                        handle = self.get_resize_handle(self.selected_roi, scene_pos)
                        if handle:
                            # 开始调整大小 - 保持十字光标
                            self.roi_resize_handle = handle
                            self.resize_start_pos = scene_pos
                            print(f"🔧 开始调整ROI大小: {handle}")
                            event.accept()
                            return
                    
                    # 检查是否点击了现有ROI
                    clicked_roi = self.get_roi_at_position(scene_pos)
                    if clicked_roi:
                        # 选中ROI - 显示手型光标
                        self.selected_roi = clicked_roi
                        self.graphics_view.setCursor(QtCore.Qt.OpenHandCursor)
                        print(f"✅ 选中ROI: {clicked_roi.id}")
                        self.redraw_annotations()
                        event.accept()
                        return
                    else:
                        # 取消选中 - 开始绘制，显示十字光标
                        self.selected_roi = None
                        self.drawing_start_pos = view_pos
                        self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
                        print("🎨 开始绘制新ROI")
                        event.accept()
                        return
            
            elif self.current_tool in ['rect', 'circle']:
                # 普通标注模式 - 保持十字光标
                self.drawing_start_pos = view_pos
                event.accept()
                return
                
            elif self.current_tool == 'text':
                # 文字工具
                self.show_text_input_dialog(view_pos)
                event.accept()
                return
        
        super(ImagePreviewDialog, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件：处理ROI调整和实时预览
        """
        if self.graphics_view.underMouse():
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            
            if self.roi_mode and self.roi_resize_handle and self.selected_roi:
                # 正在调整ROI大小
                delta_x = scene_pos.x() - self.resize_start_pos.x()
                delta_y = scene_pos.y() - self.resize_start_pos.y()
                
                # 根据手柄类型调整ROI
                self.resize_roi(self.selected_roi, self.roi_resize_handle, delta_x, delta_y)
                
                # 更新起始位置
                self.resize_start_pos = scene_pos
                
                # 重绘
                self.redraw_annotations()
                event.accept()
                return
            
            elif self.roi_mode and self.drawing_start_pos is not None:
                # 正在绘制新ROI
                # 移除旧的临时预览
                for item in self.scene.items():
                    if hasattr(item, 'is_temp_preview'):
                        self.scene.removeItem(item)
                
                # 绘制临时ROI预览（蓝色虚线）
                color = QtGui.QColor(0, 100, 255)  # 蓝色
                pen = QtGui.QPen(color, 2)
                pen.setStyle(QtCore.Qt.DashLine)
                
                start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
                
                temp_item = self.scene.addRect(
                    QtCore.QRectF(start_scene_pos, scene_pos).normalized(),
                    pen
                )
                temp_item.is_temp_preview = True
            
            elif self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
                # 普通标注模式的实时预览
                for item in self.scene.items():
                    if hasattr(item, 'is_temp_preview'):
                        self.scene.removeItem(item)
                
                color = QtGui.QColor(0, 255, 0)  # 绿色
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
        
        super(ImagePreviewDialog, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件：完成ROI绘制或调整
        """
        if self.graphics_view.underMouse():
            view_pos = self.graphics_view.mapFromGlobal(event.globalPos())
            scene_pos = self.graphics_view.mapToScene(view_pos)
            
            if self.roi_mode:
                if self.roi_resize_handle:
                    # 完成调整 - 恢复十字光标
                    self.roi_resize_handle = None
                    self.resize_start_pos = None
                    self.graphics_view.setCursor(QtCore.Qt.CrossCursor)
                    print("✅ ROI调整完成")
                    event.accept()
                    return
                
                elif self.drawing_start_pos is not None:
                    # 完成绘制新ROI - 保持十字光标
                    start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
                    
                    # 清除临时预览
                    for item in self.scene.items():
                        if hasattr(item, 'is_temp_preview'):
                            self.scene.removeItem(item)
                    
                    # 创建矩形ROI
                    annotation = Annotation(
                        type='roi_rect',
                        points=[
                            (int(start_scene_pos.x()), int(start_scene_pos.y())),
                            (int(scene_pos.x()), int(scene_pos.y()))
                        ],
                        properties={
                            'color': (255, 100, 0),  # 橙色 BGR
                            'thickness': 3,
                            'name': f'ROI_{len(self.annotation_layer.annotations) + 1}'
                        }
                    )
                    
                    self.annotation_layer.add_annotation(annotation)
                    self.selected_roi = annotation
                    
                    self.drawing_start_pos = None
                    
                    self.redraw_annotations()
                    print(f"✅ 已创建ROI: {annotation.properties['name']}")
                    event.accept()
                    return
            
            elif self.drawing_start_pos is not None and self.current_tool in ['rect', 'circle']:
                # 普通标注模式完成绘制 - 保持十字光标
                start_scene_pos = self.graphics_view.mapToScene(self.drawing_start_pos)
                
                annotation = Annotation(
                    type=self.current_tool,
                    points=[
                        (int(start_scene_pos.x()), int(start_scene_pos.y())),
                        (int(scene_pos.x()), int(scene_pos.y()))
                    ],
                    properties={
                        'color': self.current_pen_color,  # 使用当前选择的颜色 BGR
                        'thickness': 2
                    }
                )
                
                self.annotation_layer.add_annotation(annotation)
                
                for item in self.scene.items():
                    if hasattr(item, 'is_temp_preview'):
                        self.scene.removeItem(item)
                
                self.redraw_annotations()
                self.drawing_start_pos = None
                
                print(f"✅ 已创建{self.current_tool}标注")
                event.accept()
                return
        
        super(ImagePreviewDialog, self).mouseReleaseEvent(event)
    
    def resize_roi(self, roi, handle, delta_x, delta_y):
        """
        调整ROI大小
        
        Args:
            roi: ROI标注对象
            handle: 手柄名称
            delta_x: X方向偏移
            delta_y: Y方向偏移
        """
        if roi.type != 'roi_rect' or len(roi.points) < 2:
            return
        
        x1, y1 = roi.points[0]
        x2, y2 = roi.points[1]
        
        # 根据手柄类型调整坐标
        if 'left' in handle:
            x1 += delta_x
        if 'right' in handle:
            x2 += delta_x
        if 'top' in handle:
            y1 += delta_y
        if 'bottom' in handle:
            y2 += delta_y
        
        roi.points[0] = (int(x1), int(y1))
        roi.points[1] = (int(x2), int(y2))
    
    def draw_annotation_on_scene(self, annotation: Annotation):
        """
        在场景上绘制单个标注（重写以支持ROI）
        
        Args:
            annotation: 标注对象
        """
        color = QtGui.QColor(*annotation.properties['color'][::-1])  # BGR -> RGB
        thickness = annotation.properties['thickness']
        
        # ROI使用特殊样式
        is_roi = annotation.type in ['roi_rect', 'roi_circle']
        if is_roi:
            # ROI边框更粗，颜色不同
            thickness = max(thickness, 3)
            if annotation == self.selected_roi:
                # 选中的ROI用亮色高亮
                color = QtGui.QColor(0, 255, 255)  # 黄色
        
        if annotation.type in ['rect', 'roi_rect'] and len(annotation.points) >= 2:
            # 绘制矩形
            start_pos = QtCore.QPointF(*annotation.points[0])
            end_pos = QtCore.QPointF(*annotation.points[1])
            rect = QtCore.QRectF(start_pos, end_pos).normalized()
            
            pen = QtGui.QPen(color, thickness)
            pen.setStyle(QtCore.Qt.SolidLine)
            
            rect_item = self.scene.addRect(rect, pen)
            rect_item.is_annotation = True
            rect_item.annotation_id = annotation.id
            
            # 如果是选中的ROI，绘制调整手柄
            if is_roi and annotation == self.selected_roi:
                self.draw_roi_handles(rect)
            
        elif annotation.type in ['circle', 'roi_circle'] and len(annotation.points) >= 2:
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
    
    def draw_roi_handles(self, rect):
        """
        绘制ROI调整手柄
        
        Args:
            rect: QRectF矩形
        """
        handle_color = QtGui.QColor(255, 255, 255)  # 白色
        handle_pen = QtGui.QPen(handle_color, 1)
        handle_brush = QtGui.QBrush(handle_color)
        
        handle_size = self.HANDLE_SIZE / self.zoom_factor
        
        # 8个手柄位置
        handles = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight(),
            QtCore.QPointF(rect.center().x(), rect.top()),
            QtCore.QPointF(rect.center().x(), rect.bottom()),
            QtCore.QPointF(rect.left(), rect.center().y()),
            QtCore.QPointF(rect.right(), rect.center().y()),
        ]
        
        for pos in handles:
            handle_rect = QtCore.QRectF(
                pos.x() - handle_size/2,
                pos.y() - handle_size/2,
                handle_size,
                handle_size
            )
            handle_item = self.scene.addRect(handle_rect, handle_pen, handle_brush)
            handle_item.is_annotation = True  # 标记为标注的一部分
    
    # === ROI功能方法 END ===

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
                # QtWidgets.QMessageBox.information(
                #     self,
                #     "成功",
                #     f"图像已保存到:\n{file_path}"
                # )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "错误",
                    f"保存失败:\n{str(e)}"
                )
    
    def get_roi_data(self):
        """
        获取所有ROI数据（用于传递给模板创建节点）
        
        Returns:
            list: ROI数据列表，每个元素包含type, points, properties
        """
        roi_list = []
        for ann in self.annotation_layer.annotations:
            if ann.type in ['roi_rect', 'roi_circle']:
                roi_data = {
                    'type': ann.type,
                    'points': ann.points,
                    'properties': ann.properties
                }
                roi_list.append(roi_data)
        return roi_list
    
    def export_roi_to_node(self):
        """
        导出ROI数据到关联的ImageViewNode
        
        Returns:
            dict or None: ROI数据字典，如果没有关联节点则返回None
        """
        if self.node is None:
            print("⚠️ 预览窗口未关联节点")
            return None
        
        roi_data = self.get_roi_data()
        
        if not roi_data:
            print("⚠️ 没有ROI数据可导出")
            QtWidgets.QMessageBox.information(
                self,
                "提示",
                "当前没有ROI数据\n请先绘制ROI区域"
            )
            return None
        
        # 调用节点的set_roi_data方法
        if hasattr(self.node, 'set_roi_data'):
            self.node.set_roi_data(roi_data)
            print(f"✅ 已导出 {len(roi_data)} 个ROI到节点")
            
            # 显示确认对话框
            QtWidgets.QMessageBox.information(
                self,
                "导出成功",
                f"已导出 {len(roi_data)} 个ROI数据到节点\n\n"
                f"可以在属性面板中查看和编辑\n"
                f"ROI数据将通过'ROI数据'端口输出"
            )
        else:
            print("⚠️ 节点不支持ROI数据设置")
            QtWidgets.QMessageBox.warning(
                self,
                "警告",
                "关联的节点不支持ROI功能"
            )
        
        return roi_data

    def resizeEvent(self, event):
        """
        窗口大小改变时重新显示图像
        """
        super(ImagePreviewDialog, self).resizeEvent(event)
        self.display_image()
