"""
实时预览订阅者节点

作为相机节点的订阅者，接收高频推送的图像帧并实时显示。
适用于需要高帧率预览的场景（如实时监控、快速调试）。

特性：
- 高频刷新（默认30fps）
- 独立于主预览窗口
- 支持缩放、平移、保存
- 显示FPS和延迟统计
"""

import time
from typing import Dict, Any, Optional
import numpy as np
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QImage, QPixmap

from shared_libs.node_base import BaseNode, ParameterContainerWidget


class RealTimePreviewNode(BaseNode):
    """
    实时预览订阅者节点
    
    通过订阅相机节点的图像流，实现高频实时预览。
    
    使用方法：
    1. 创建此节点
    2. 右键点击相机节点 -> "注册为订阅者" -> 选择此节点
    3. 双击此节点打开预览窗口
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '实时预览'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(RealTimePreviewNode, self).__init__()
        
        # 无输入输出端口（通过订阅接收数据）
        
        # === 配置参数 ===
        self._param_container = ParameterContainerWidget(self.view, 'realtime_preview_params', '')
        self._param_container.add_combobox('max_fps', '最大帧率', items=['15', '20', '25', '30', '60'])
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='基本配置')
        
        # 内部状态
        self._latest_frame = None
        self._frame_lock = None  # 简化：不使用锁（单线程更新）
        self._preview_window = None
        self._subscriber_id = f"realtime_preview_{id(self)}"
        
        # 统计信息
        self._frame_count = 0
        self._last_stats_time = time.time()
        self._current_fps = 0.0
        
    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))
        
    def on_subscribed_by(self, publisher_node):
        """
        当被相机节点订阅时调用
        
        Args:
            publisher_node: CameraCaptureNode 实例
        """
        max_fps = float(self.get_property('max_fps'))
        
        def frame_callback(frame):
            """接收帧的回调函数"""
            self._latest_frame = frame
            self._frame_count += 1
            
            # 计算FPS
            current_time = time.time()
            elapsed = current_time - self._last_stats_time
            if elapsed >= 1.0:
                self._current_fps = self._frame_count / elapsed
                self._frame_count = 0
                self._last_stats_time = current_time
                
                # 更新预览窗口标题
                if self._preview_window and self._preview_window.isVisible():
                    self._preview_window.setWindowTitle(
                        f"实时预览 - FPS: {self._current_fps:.1f}"
                    )
        
        # 注册到相机节点
        if hasattr(publisher_node, 'subscribe'):
            success = publisher_node.subscribe(
                self._subscriber_id,
                frame_callback,
                max_fps=max_fps
            )
            if success:
                self.log_success(f"已订阅相机节点 (max_fps={max_fps})")
            else:
                self.log_error("订阅失败")
        else:
            self.log_warning("发布者不支持订阅接口")
    
    def on_unsubscribed_by(self, publisher_node):
        """
        当取消订阅时调用
        
        Args:
            publisher_node: CameraCaptureNode 实例
        """
        if hasattr(publisher_node, 'unsubscribe'):
            publisher_node.unsubscribe(self._subscriber_id)
            self.log_info("已取消订阅")
    
    def open_preview_window(self):
        """打开实时预览窗口"""
        if self._preview_window is None or not self._preview_window.isVisible():
            self._preview_window = RealTimePreviewDialog(self)
            self._preview_window.show()
            self.log_info("实时预览窗口已打开")
    
    def get_cached_image(self):
        """获取缓存的最新图像"""
        return self._latest_frame
    
    def process(self, inputs=None):
        """处理节点逻辑（本节点主要通过订阅接收数据）"""
        return {'output': self._latest_frame}


class RealTimePreviewDialog(QDialog):
    """
    实时预览对话框
    
    显示订阅的高频图像流，支持缩放、平移、保存等功能。
    """
    
    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.setWindowTitle("实时预览")
        self.setMinimumSize(640, 480)
        
        self.setup_ui()
        
        # 启动定时器刷新预览
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_preview)
        self.refresh_timer.start(33)  # ~30fps
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2b2b2b;")
        layout.addWidget(self.image_label)
        
        # 底部工具栏
        toolbar = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_image)
        toolbar.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("🗑️ 清除")
        self.clear_btn.clicked.connect(self.clear_image)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        self.fps_label = QLabel("FPS: --")
        toolbar.addWidget(self.fps_label)
        
        layout.addLayout(toolbar)
    
    def update_preview(self):
        """更新预览图像"""
        frame = self.node.get_cached_image()
        if frame is None:
            return
        
        try:
            # OpenCV BGR → RGB → QImage
            if len(frame.shape) == 3:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(
                    frame.data, width, height, bytes_per_line,
                    QImage.Format_RGB888
                ).rgbSwapped()
            else:
                height, width = frame.shape
                bytes_per_line = width
                q_image = QImage(
                    frame.data, width, height, bytes_per_line,
                    QImage.Format_Grayscale8
                )
            
            # 缩放到标签大小
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
            # 更新FPS显示
            self.fps_label.setText(f"FPS: {self.node._current_fps:.1f}")
            
        except Exception as e:
            print(f"[RealTimePreview] 更新失败: {e}")
    
    def save_image(self):
        """保存当前图像"""
        from PySide2.QtWidgets import QFileDialog
        frame = self.node.get_cached_image()
        if frame is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图像",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        
        if file_path:
            import cv2
            cv2.imwrite(file_path, frame)
            self.node.log_success(f"图像已保存: {file_path}")
    
    def clear_image(self):
        """清除显示的图像"""
        self.image_label.clear()
        self.node._latest_frame = None


# 导出类
__all__ = ['RealTimePreviewNode']
