"""
工业相机采集节点

从工业相机采集图像，支持：
- 多相机同时工作（通过Seat索引选择）
- 后台线程连续采集
- 单帧触发 + 连续流双输出模式
- 模拟相机支持（无硬件时测试）
- 实时预览窗口（双击节点打开）
"""

import threading
import time
from typing import Dict, Any, Optional
import numpy as np

from shared_libs.node_base import BaseNode
from .camera_manager import CameraManager


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
    NODE_NAME = '工业相机采集'
    
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
            items=['0', '1', '2', '3', '4'],  # 动态加载
            tab='基本配置'
        )
        
        self.add_text_input(
            'serial_number', 
            '相机序列号', 
            text='',
            tab='基本配置'
        )
        
        self.add_float_input(
            'magnification', 
            '镜头倍率', 
            value=1.0,
            tab='基本配置'
        )
        
        self.add_combo_menu(
            'acquisition_mode', 
            '采集模式', 
            items=['连续采集', '软件触发', '外部触发'],
            tab='基本配置'
        )
        
        # === 图像参数标签页 ===
        self.add_slider(
            'exposure_us', 
            '曝光时间(μs)', 
            start=10000, 
            range=(100, 100000),
            tab='图像参数'
        )
        
        self.add_slider(
            'gain', 
            '增益', 
            start=0, 
            range=(0, 100),
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
        
        # 初始化Seat列表
        self._update_seat_list()
    
    def _update_seat_list(self):
        """更新Seat索引下拉列表"""
        seat_count = self._camera_manager.get_seat_count()
        items = [str(i) for i in range(seat_count)]
        if items:
            self.set_property('seat_index_items', items)
    
    def _on_seat_index_changed(self):
        """Seat索引变化时的回调"""
        try:
            seat_index = int(self.get_property('seat_index'))
            seat_info = self._camera_manager.get_seat_info(seat_index)
            
            if seat_info:
                sn = seat_info.get('sn', '')
                mag = float(seat_info.get('Magnification', '1.0'))
                
                self.set_property('serial_number', sn)
                self.set_property('magnification', mag)
                
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
                    with self._frame_lock:
                        self._latest_frame = frame.copy()  # 深拷贝避免竞争
                
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
    
    def on_delete(self):
        """节点删除时的清理"""
        self.close_camera()
        if self._preview_window:
            self._preview_window.close()
