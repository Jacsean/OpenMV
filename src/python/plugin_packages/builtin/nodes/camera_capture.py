"""
工业相机采集节点

从工业相机采集图像，支持：
- 多相机同时工作（通过Seat索引选择）
- 后台线程连续采集
- 单帧触发 + 连续流双输出模式
- 模拟相机支持（无硬件时测试）
- 实时预览窗口（双击节点打开）
- 【Phase 3】环形缓冲区 + 发布-订阅机制（>15fps高速处理）
"""

import threading
import time
from typing import Dict, Any, Optional, Callable
import numpy as np

from shared_libs.node_base import BaseNode
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from camera_manager import CameraManager
except ImportError:
    from plugin_packages.builtin.camera_manager import CameraManager

try:
    from circular_buffer import CircularBuffer
except ImportError:
    try:
        from plugin_packages.builtin.circular_buffer import CircularBuffer
    except ImportError:
        CircularBuffer = None

try:
    from pubsub_manager import PubSubManager
except ImportError:
    try:
        from plugin_packages.builtin.pubsub_manager import PubSubManager
    except ImportError:
        PubSubManager = None


class CameraCaptureNode(BaseNode):
    """
    工业相机采集节点
    
    从配置的工业相机采集图像数据，支持连续采集和单帧触发两种模式。
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 2GB+（取决于分辨率）
    - GPU: 不需要
    - 相机硬件: GigE/USB3.0 工业相机（可选，支持模拟模式）
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '相机采集'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(CameraCaptureNode, self).__init__()
        
        # 输出端口
        self.add_output('单帧图像')
        self.add_output('连续图像流')
        
        # === 基本配置标签页 ===
        self.add_combo_menu(
            'seat_index', 
            'Seat索引', 
            items=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],  # 支持最多10个Seat
            tab='基本配置'
        )
        
        self.add_text_input(
            'serial_number', 
            '相机序列号', 
            text='',
            tab='基本配置'
        )
        
        self.add_text_input(
            'magnification', 
            '镜头倍率', 
            text='1.0',
            tab='基本配置'
        )
        
        self.add_combo_menu(
            'acquisition_mode', 
            '采集模式', 
            items=['连续采集', '软件触发', '外部触发'],
            tab='基本配置'
        )
        
        # === 图像参数标签页 ===
        self.add_text_input(
            'exposure_us', 
            '曝光时间(μs)', 
            text='10000',
            tab='图像参数'
        )
        
        self.add_text_input(
            'gain', 
            '增益', 
            text='0',
            tab='图像参数'
        )
        
        self.add_combo_menu(
            'white_balance_mode', 
            '白平衡模式', 
            items=['Auto', 'Manual', 'Once'],
            tab='图像参数'
        )
        
        # 内部状态
        self._camera_manager = CameraManager.get_instance()
        self._camera_id = None
        self._is_acquiring = False
        self._acquisition_thread = None
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._preview_window = None
        
        # === Phase 3: 环形缓冲区（支持高速采集）===
        if CircularBuffer:
            self._frame_buffer = CircularBuffer(capacity=10, max_age_seconds=5.0)
            print(f"[CameraCaptureNode] 环形缓冲区已启用 (capacity=10)")
        else:
            self._frame_buffer = None
            print(f"[CameraCaptureNode] 环形缓冲区不可用（降级到简单缓存）")
        
        # === Phase 3: 发布-订阅管理器 ===
        if PubSubManager:
            self._pubsub = PubSubManager()
            print(f"[CameraCaptureNode] 发布-订阅管理器已启用")
        else:
            self._pubsub = None
            print(f"[CameraCaptureNode] 发布-订阅管理器不可用")
        
        # 初始化Seat列表（已移除动态更新，使用固定选项）
        # self._update_seat_list()  # NodeGraphQt不支持动态修改combo_menu items
    
    def _on_seat_index_changed(self):
        """Seat索引变化时的回调"""
        try:
            seat_index = int(self.get_property('seat_index'))
            seat_count = self._camera_manager.get_seat_count()
            
            # 验证索引是否有效
            if seat_index >= seat_count:
                self.log_warning(f"Seat索引 {seat_index} 超出范围 (可用: 0-{seat_count-1})")
                self.set_property('serial_number', '无效索引')
                return
            
            seat_info = self._camera_manager.get_seat_info(seat_index)
            
            if seat_info:
                sn = seat_info.get('sn', '')
                mag = float(seat_info.get('Magnification', '1.0'))
                
                self.set_property('serial_number', sn)
                self.set_property('magnification', str(mag))
                
                self.log_info(f"已选择 Seat {seat_index}: SN={sn}")
            else:
                self.set_property('serial_number', '')
                self.log_warning(f"无效的Seat索引: {seat_index}")
        except Exception as e:
            self.log_error(f"更新Seat信息失败: {e}")
    
    def initialize_camera(self):
        """初始化相机设备"""
        try:
            seat_index = int(self.get_property('seat_index'))
            camera_id = self._camera_manager.initialize_camera(seat_index)
            
            if camera_id:
                self._camera_id = camera_id
                self.log_success(f"相机初始化成功: {camera_id}")
                return True
            else:
                self.log_error("相机初始化失败")
                return False
        except Exception as e:
            self.log_error(f"初始化异常: {e}")
            return False
    
    def open_camera(self):
        """打开相机"""
        if not self._camera_id:
            self.log_error("请先初始化相机")
            return False
        
        camera = self._camera_manager.get_camera(self._camera_id)
        if camera and hasattr(camera, 'open'):
            if camera.open():
                self.log_success("相机已打开")
                return True
            else:
                self.log_error("打开相机失败")
                return False
        else:
            self.log_error("相机实例不存在")
            return False
    
    def close_camera(self):
        """关闭相机"""
        if self._camera_id:
            self.stop_acquisition()
            self._camera_manager.release_camera(self._camera_id)
            self._camera_id = None
            self.log_info("相机已关闭")
    
    def start_acquisition(self):
        """启动后台采集线程"""
        if self._is_acquiring:
            self.log_warning("采集已在运行")
            return
        
        if not self._camera_id:
            self.log_error("请先初始化并打开相机")
            return
        
        self._is_acquiring = True
        self._acquisition_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"Camera_{self.id}_Acquisition"
        )
        self._acquisition_thread.start()
        self.log_success("开始连续采集")
    
    def stop_acquisition(self):
        """停止采集"""
        if not self._is_acquiring:
            return
        
        self._is_acquiring = False
        if self._acquisition_thread:
            self._acquisition_thread.join(timeout=2.0)
            self._acquisition_thread = None
        
        self.log_info("采集已停止")
    
    def _capture_loop(self):
        """后台采集循环"""
        camera = self._camera_manager.get_camera(self._camera_id)
        if not camera:
            self.log_error("相机实例不存在")
            self._is_acquiring = False
            return
        
        framerate = 30  # 可从配置读取
        
        while self._is_acquiring:
            try:
                frame = camera.grab_frame()
                
                if frame is not None:
                    # === Phase 1: 更新简单缓存（兼容旧代码）===
                    with self._frame_lock:
                        self._latest_frame = frame.copy()
                    
                    # === Phase 3: 放入环形缓冲区 ===
                    if self._frame_buffer:
                        self._frame_buffer.put(frame)
                    
                    # === Phase 3: 发布给所有订阅者 ===
                    if self._pubsub:
                        subscriber_count = self._pubsub.publish(frame)
                        if subscriber_count > 0 and self._is_acquiring:
                            # 每100帧打印一次统计
                            if self._frame_buffer.total_produced % 100 == 0:
                                stats = self._frame_buffer.get_stats()
                                pubsub_stats = self._pubsub.get_all_stats()
                                self.log_info(
                                    f"采集统计: "
                                    f"生产={stats['total_produced']}, "
                                    f"消费={stats['total_consumed']}, "
                                    f"丢帧={stats['total_dropped']} "
                                    f"({stats['drop_rate']:.1f}%), "
                                    f"订阅者={pubsub_stats['active_subscribers']}"
                                )
                
                # 控制帧率
                time.sleep(1.0 / framerate)
                
            except Exception as e:
                self.log_error(f"采集错误: {e}")
                break
        
        self._is_acquiring = False
        self.log_info("采集线程退出")
    
    def grab_once(self):
        """单次采集（软件触发模式）"""
        if not self._camera_id:
            self.log_error("请先初始化相机")
            return None
        
        camera = self._camera_manager.get_camera(self._camera_id)
        if not camera:
            self.log_error("相机实例不存在")
            return None
        
        try:
            frame = camera.grab_frame()
            if frame is not None:
                with self._frame_lock:
                    self._latest_frame = frame.copy()
                self.log_success("单次采集成功")
                return frame
            else:
                self.log_error("采集失败")
                return None
        except Exception as e:
            self.log_error(f"单次采集异常: {e}")
            return None
    
    def get_cached_image(self):
        """获取缓存的最新图像（供预览窗口调用）"""
        with self._frame_lock:
            return self._latest_frame
    
    def open_preview_window(self):
        """打开实时预览窗口"""
        if self._preview_window is None or not self._preview_window.isVisible():
            # 使用绝对导入避免相对导入路径问题
            try:
                from plugin_packages.builtin.io_camera.camera_preview_dialog import CameraPreviewDialog
            except ImportError:
                # 兼容旧版本或测试环境
                from .camera_preview_dialog import CameraPreviewDialog
            
            self._preview_window = CameraPreviewDialog(self, parent=None)
            self._preview_window.show()
            self.log_info("预览窗口已打开")
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据（本节点无输入）
            
        Returns:
            dict: 包含输出图像的字典
        """
        try:
            with self._frame_lock:
                frame = self._latest_frame
            
            if frame is not None:
                return {
                    '单帧图像': frame,
                    '连续图像流': frame
                }
            else:
                self.log_warning("暂无图像数据")
                return {
                    '单帧图像': None,
                    '连续图像流': None
                }
                
        except Exception as e:
            self.log_error(f"处理错误: {e}")
            return {
                '单帧图像': None,
                '连续图像流': None
            }
    
    def subscribe(self, subscriber_id: str, callback: Callable[[np.ndarray], None], 
                  max_fps: float = 30.0) -> bool:
        """
        注册订阅者
        
        Args:
            subscriber_id: 订阅者唯一标识
            callback: 回调函数，接收一帧图像
            max_fps: 最大处理帧率
            
        Returns:
            bool: 是否成功注册
        """
        if not self._pubsub:
            self.log_warning("发布-订阅管理器不可用")
            return False
        
        success = self._pubsub.subscribe(subscriber_id, callback, max_fps)
        if success:
            self.log_info(f"订阅者已注册: {subscriber_id} (max_fps={max_fps})")
        return success
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscriber_id: 订阅者标识
            
        Returns:
            bool: 是否成功取消
        """
        if not self._pubsub:
            return False
        
        success = self._pubsub.unsubscribe(subscriber_id)
        if success:
            self.log_info(f"订阅者已取消: {subscriber_id}")
        return success
    
    def get_pubsub_stats(self) -> dict:
        """
        获取发布-订阅统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self._pubsub:
            return {}
        
        return self._pubsub.get_all_stats()
    
    def get_buffer_stats(self) -> dict:
        """
        获取环形缓冲区统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self._frame_buffer:
            return {}
        
        return self._frame_buffer.get_stats()
    
    # === UI集成：订阅者管理对话框 ===
    
    def show_subscriber_manager(self):
        """
        显示订阅者管理对话框
        
        允许用户注册/取消订阅者节点
        """
        from PySide2.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout
        from PySide2.QtCore import Qt
        
        dialog = QDialog(None)
        dialog.setWindowTitle("订阅者管理")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel("已注册的订阅者:")
        layout.addWidget(title_label)
        
        # 订阅者列表
        subscriber_list = QListWidget()
        
        if self._pubsub:
            stats = self._pubsub.get_all_stats()
            for sub_id, sub_info in stats.get('subscribers', {}).items():
                item_text = f"{sub_id} (FPS: {sub_info['max_fps']}, 帧数: {sub_info['frame_count']})"
                subscriber_list.addItem(item_text)
        else:
            subscriber_list.addItem("发布-订阅管理器不可用")
        
        layout.addWidget(subscriber_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        register_btn = QPushButton("➕ 注册新订阅者")
        register_btn.clicked.connect(lambda: self._show_register_dialog(dialog))
        button_layout.addWidget(register_btn)
        
        unregister_btn = QPushButton("➖ 取消选中订阅")
        unregister_btn.clicked.connect(lambda: self._unselected_subscriber(subscriber_list, dialog))
        button_layout.addWidget(unregister_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def _show_register_dialog(self, parent_dialog):
        """显示注册订阅者对话框"""
        from PySide2.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QHBoxLayout
        from PySide2.QtCore import Qt
        
        reg_dialog = QDialog(parent_dialog)
        reg_dialog.setWindowTitle("注册订阅者")
        reg_dialog.setMinimumSize(350, 200)
        
        layout = QVBoxLayout(reg_dialog)
        
        # 说明
        info_label = QLabel("注意：此功能需要在画布上创建对应的订阅者节点后使用。\n当前版本支持手动调用节点的 on_subscribed_by 方法。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 可用订阅者类型
        type_label = QLabel("可用的订阅者节点类型:")
        layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItem("RealTimePreviewNode - 实时预览 (30fps)")
        type_combo.addItem("FastDetectionNode - 快速检测 (15fps)")
        type_combo.addItem("VideoRecorderNode - 视频录制 (25fps)")
        layout.addWidget(type_combo)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(lambda: self._register_selected_subscriber(type_combo, reg_dialog))
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(reg_dialog.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        reg_dialog.exec_()
    
    def _register_selected_subscriber(self, type_combo, dialog):
        """注册选中的订阅者类型（占位实现）"""
        selected_type = type_combo.currentText()
        self.log_info(f"请从节点库拖拽 '{selected_type.split(' - ')[0]}' 到画布，然后双击该节点进行配置。")
        dialog.close()
    
    def _unselected_subscriber(self, subscriber_list, dialog):
        """取消选中的订阅者"""
        current_item = subscriber_list.currentItem()
        if not current_item:
            self.log_warning("请先选择一个订阅者")
            return
        
        sub_id = current_item.text().split(' (')[0]
        
        if self._pubsub:
            success = self._pubsub.unsubscribe(sub_id)
            if success:
                self.log_success(f"已取消订阅: {sub_id}")
                dialog.accept()  # 关闭并刷新
            else:
                self.log_error(f"取消订阅失败: {sub_id}")
        else:
            self.log_warning("发布-订阅管理器不可用")

    def on_delete(self):
        """节点删除时的清理"""
        self.close_camera()
        if self._preview_window:
            self._preview_window.close()
