"""
相机预览对话框模块

提供实时相机预览窗口，支持：
- 实时图像显示（定时器刷新）
- 快速控制按钮（初始化、打开、开始/停止采集）
- 图像缩放（滚轮）、平移（拖拽）
- 自动滚动条
- 状态信息显示（帧率、连接状态等）
- 保存当前帧
"""

import os
import time
from datetime import datetime
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGraphicsView, QGraphicsScene, QMessageBox,
    QFileDialog
)
from PySide2.QtCore import Qt, QTimer, QPoint
from PySide2.QtGui import QImage, QPixmap, QPainter, QFont
import numpy as np


class CameraPreviewDialog(QDialog):
    """
    相机实时预览窗口
    
    非模态对话框，支持多窗口并存。
    显示相机实时画面，提供快速控制和状态监控。
    """
    
    def __init__(self, camera_node, parent=None):
        """
        初始化预览窗口
        
        Args:
            camera_node: CameraCaptureNode 实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.camera_node = camera_node
        self.setWindowTitle(f"相机预览 - {camera_node.NODE_NAME}")
        self.setMinimumSize(800, 600)
        
        # 状态变量
        self.last_frame_time = None
        self.frame_count = 0
        self.fps = 0.0
        
        # 设置UI
        self._setup_ui()
        
        # 启动刷新定时器
        self._start_refresh_timer()
    
    def _setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === 顶部工具栏 ===
        toolbar = QHBoxLayout()
        
        self.btn_init = QPushButton("🔧 初始化")
        self.btn_init.clicked.connect(self._on_init_clicked)
        toolbar.addWidget(self.btn_init)
        
        self.btn_open = QPushButton("📡 打开")
        self.btn_open.clicked.connect(self._on_open_clicked)
        toolbar.addWidget(self.btn_open)
        
        self.btn_start = QPushButton("▶️ 开始采集")
        self.btn_start.clicked.connect(self._on_start_clicked)
        toolbar.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏸️ 停止")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)
        
        toolbar.addStretch()
        
        self.btn_save = QPushButton("💾 保存当前帧")
        self.btn_save.clicked.connect(self._on_save_clicked)
        toolbar.addWidget(self.btn_save)
        
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        toolbar.addWidget(self.btn_refresh)
        
        main_layout.addLayout(toolbar)
        
        # === 中部图像显示区 ===
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)  # 空格+拖拽平移
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setBackgroundBrush(Qt.black)
        
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        # 重写滚轮事件实现缩放
        self.graphics_view.wheelEvent = self._on_wheel_event
        
        main_layout.addWidget(self.graphics_view)
        
        # === 底部状态栏 ===
        status_bar = QHBoxLayout()
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        status_bar.addWidget(self.status_label)
        
        status_bar.addStretch()
        
        # Phase 3: 性能监控标签
        self.buffer_size_label = QLabel("缓冲: 0/10")
        self.buffer_size_label.setStyleSheet("color: purple;")
        status_bar.addWidget(self.buffer_size_label)
        
        self.drop_rate_label = QLabel("丢帧: 0.0%")
        self.drop_rate_label.setStyleSheet("color: green;")
        status_bar.addWidget(self.drop_rate_label)
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("color: blue;")
        status_bar.addWidget(self.fps_label)
        
        self.frame_count_label = QLabel("帧数: 0")
        self.frame_count_label.setStyleSheet("color: green;")
        status_bar.addWidget(self.frame_count_label)
        
        main_layout.addLayout(status_bar)
    
    def _start_refresh_timer(self):
        """启动预览刷新定时器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_preview)
        self.refresh_timer.start(100)  # 每100ms刷新一次（10fps）
    
    def _update_preview(self):
        """更新预览图像"""
        try:
            frame = self.camera_node.get_cached_image()
            
            if frame is not None and isinstance(frame, np.ndarray):
                # 计算FPS
                current_time = time.time()
                if self.last_frame_time:
                    delta = current_time - self.last_frame_time
                    if delta > 0:
                        self.fps = 1.0 / delta
                self.last_frame_time = current_time
                self.frame_count += 1
                
                # OpenCV BGR → RGB → QImage
                if len(frame.shape) == 3:
                    height, width, channel = frame.shape
                    bytes_per_line = 3 * width
                    q_image = QImage(
                        frame.data, width, height, bytes_per_line, 
                        QImage.Format_RGB888
                    ).rgbSwapped()
                else:
                    # 灰度图像
                    height, width = frame.shape
                    q_image = QImage(
                        frame.data, width, height, width, 
                        QImage.Format_Grayscale8
                    )
                
                # 清除旧项，添加新项
                self.scene.clear()
                pixmap = QPixmap.fromImage(q_image)
                self.scene.addPixmap(pixmap)
                
                # 首次加载时适应视图
                if self.frame_count == 1:
                    self.graphics_view.fitInView(
                        self.scene.itemsBoundingRect(), 
                        Qt.KeepAspectRatio
                    )
                
                # 更新状态栏
                self._update_status_bar()
                
        except Exception as e:
            print(f"[CameraPreview] 更新预览失败: {e}")
    
    def _update_status_bar(self):
        """更新状态栏信息"""
        # FPS
        self.fps_label.setText(f"FPS: {self.fps:.1f}")
        
        # 帧数
        self.frame_count_label.setText(f"帧数: {self.frame_count}")
        
        # Phase 3: 更新性能统计
        if hasattr(self.camera_node, 'get_buffer_stats'):
            buffer_stats = self.camera_node.get_buffer_stats()
            if buffer_stats:
                # 缓冲区大小
                current_size = buffer_stats.get('current_size', 0)
                capacity = buffer_stats.get('capacity', 10)
                self.buffer_size_label.setText(f"缓冲: {current_size}/{capacity}")
                
                # 丢帧率
                drop_rate = buffer_stats.get('drop_rate', 0.0)
                self.drop_rate_label.setText(f"丢帧: {drop_rate:.1f}%")
                
                # 丢帧率警告（>10%时红色）
                if drop_rate > 10.0:
                    self.drop_rate_label.setStyleSheet("color: red; font-weight: bold;")
                elif drop_rate > 5.0:
                    self.drop_rate_label.setStyleSheet("color: orange;")
                else:
                    self.drop_rate_label.setStyleSheet("color: green;")
        
        # 连接状态（简化版，实际应从相机节点获取）
        if self.camera_node._is_acquiring:
            self.status_label.setText("🟢 采集中")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif self.camera_node._camera_id:
            self.status_label.setText("🟡 已连接")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setText("⚪ 未连接")
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")
    
    def _on_wheel_event(self, event):
        """滚轮缩放"""
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.2 if event.angleDelta().y() > 0 else 1/1.2
            self.graphics_view.scale(factor, factor)
        else:
            # 默认行为：滚动
            QGraphicsView.wheelEvent(self.graphics_view, event)
    
    def _on_init_clicked(self):
        """初始化相机"""
        success = self.camera_node.initialize_camera()
        if success:
            QMessageBox.information(self, "成功", "相机初始化成功")
        else:
            QMessageBox.warning(self, "失败", "相机初始化失败")
    
    def _on_open_clicked(self):
        """打开相机"""
        success = self.camera_node.open_camera()
        if success:
            QMessageBox.information(self, "成功", "相机已打开")
        else:
            QMessageBox.warning(self, "失败", "打开相机失败")
    
    def _on_start_clicked(self):
        """开始采集"""
        self.camera_node.start_acquisition()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def _on_stop_clicked(self):
        """停止采集"""
        self.camera_node.stop_acquisition()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    def _on_save_clicked(self):
        """保存当前帧"""
        frame = self.camera_node.get_cached_image()
        if frame is None:
            QMessageBox.warning(self, "警告", "暂无图像可保存")
            return
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图像",
            f"camera_frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Images (*.png);;JPEG Images (*.jpg);;BMP Images (*.bmp)"
        )
        
        if file_path:
            try:
                import cv2
                cv2.imwrite(file_path, frame)
                QMessageBox.information(self, "成功", f"图像已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def _on_refresh_clicked(self):
        """手动刷新预览"""
        self._update_preview()
    
    def closeEvent(self, event):
        """关闭窗口时的清理"""
        self.refresh_timer.stop()
        super().closeEvent(event)
