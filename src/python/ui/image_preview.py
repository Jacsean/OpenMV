"""
图像预览对话框模块

提供增强版的图像预览功能，支持：
- 非模态窗口，可同时打开多个
- 图像缩放控制（原始大小/适应窗口/放大/缩小）
- 滚动条支持超大图像
- 鼠标拖拽平移
- 滚轮缩放快捷键
- 与ImageViewNode关联，支持实时刷新
"""

import cv2
from PySide2 import QtWidgets, QtCore, QtGui


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
