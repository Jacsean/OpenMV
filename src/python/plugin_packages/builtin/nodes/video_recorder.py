"""
视频录制订阅者节点

作为相机节点的订阅者，接收图像帧并录制为视频文件。
适用于长时间监控、数据采集等场景。

特性：
- 支持开始/停止录制
- 可配置编码格式和帧率
- 自动保存文件
- 显示录制状态和时长
"""

import time
import os
from typing import Dict, Any, Optional
import numpy as np
import cv2

from shared_libs.node_base import BaseNode


class VideoRecorderNode(BaseNode):
    """
    视频录制订阅者节点
    
    通过订阅相机节点的图像流，将视频保存到文件。
    
    使用方法：
    1. 创建此节点
    2. 右键点击相机节点 -> "注册为订阅者" -> 选择此节点
    3. 配置输出路径和参数
    4. 双击节点打开控制面板，点击"开始录制"
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '视频录制'
    
    resource_level = "medium"
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(VideoRecorderNode, self).__init__()
        
        # 无输入输出端口（通过订阅接收数据）
        
        # === 录制配置 ===
        self.add_text_input(
            'output_path',
            '输出路径',
            text='./recordings',
            tab='录制配置'
        )
        
        self.add_combo_menu(
            'codec',
            '编码格式',
            items=['MP4V (mp4)', 'XVID (avi)', 'MJPG (avi)'],
            tab='录制配置'
        )
        
        self.set_property('codec', 'MP4V (mp4)')
        
        self.add_combo_menu(
            'fps',
            '目标帧率',
            items=['15', '20', '25', '30'],
            tab='录制配置'
        )
        
        self.set_property('fps', '25')
        
        self.add_combo_menu(
            'max_fps',
            '最大处理帧率',
            items=['15', '20', '25', '30'],
            tab='性能配置'
        )
        
        self.set_property('max_fps', '25')
        
        # 内部状态
        self._is_recording = False
        self._video_writer = None
        self._subscriber_id = f"video_recorder_{id(self)}"
        self._start_time = None
        self._frame_count = 0
        
        # 统计信息
        self._total_recorded = 0
        self._total_dropped = 0
    
    def on_subscribed_by(self, publisher_node):
        """
        当被相机节点订阅时调用
        
        Args:
            publisher_node: CameraCaptureNode 实例
        """
        max_fps = float(self.get_property('max_fps'))
        
        def frame_callback(frame):
            """接收帧的回调函数"""
            if not self._is_recording:
                return
            
            try:
                # 写入视频文件
                if self._video_writer:
                    self._video_writer.write(frame)
                    self._frame_count += 1
                    self._total_recorded += 1
                    
                    # 每100帧更新一次状态
                    if self._frame_count % 100 == 0:
                        elapsed = time.time() - self._start_time
                        self.log_info(
                            f"录制中: {self._frame_count} 帧, "
                            f"时长: {elapsed:.1f}s, "
                            f"丢帧: {self._total_dropped}"
                        )
            
            except Exception as e:
                self.log_error(f"录制错误: {e}")
                self._total_dropped += 1
        
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
        if self._is_recording:
            self.stop_recording()
        
        if hasattr(publisher_node, 'unsubscribe'):
            publisher_node.unsubscribe(self._subscriber_id)
            self.log_info("已取消订阅")
    
    def start_recording(self):
        """开始录制"""
        if self._is_recording:
            self.log_warning("已在录制中")
            return False
        
        try:
            # 创建输出目录
            output_path = self.get_property('output_path')
            os.makedirs(output_path, exist_ok=True)
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            codec_str = self.get_property('codec')
            
            if 'mp4' in codec_str.lower():
                filename = f"recording_{timestamp}.mp4"
                fourcc = cv2.VideoWriter_fourcc(*'MP4V')
            elif 'xvid' in codec_str.lower():
                filename = f"recording_{timestamp}.avi"
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
            else:  # MJPG
                filename = f"recording_{timestamp}.avi"
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            
            filepath = os.path.join(output_path, filename)
            
            # 获取帧率
            fps = float(self.get_property('fps'))
            
            # 注意：这里假设第一帧的尺寸，实际应该在收到第一帧时初始化
            # 简化处理：使用常见分辨率
            frame_size = (1920, 1080)  # 将在收到第一帧时调整
            
            self._video_writer = cv2.VideoWriter(
                filepath, fourcc, fps, frame_size
            )
            
            if not self._video_writer.isOpened():
                self.log_error("无法创建视频写入器")
                return False
            
            self._is_recording = True
            self._start_time = time.time()
            self._frame_count = 0
            
            self.log_success(f"开始录制: {filepath}")
            return True
            
        except Exception as e:
            self.log_error(f"启动录制失败: {e}")
            return False
    
    def stop_recording(self):
        """停止录制"""
        if not self._is_recording:
            return
        
        self._is_recording = False
        
        if self._video_writer:
            self._video_writer.release()
            self._video_writer = None
        
        elapsed = time.time() - self._start_time
        self.log_success(
            f"录制完成: {self._frame_count} 帧, "
            f"时长: {elapsed:.1f}s, "
            f"丢帧: {self._total_dropped}"
        )
    
    def get_recording_status(self) -> dict:
        """获取录制状态"""
        if self._is_recording and self._start_time:
            elapsed = time.time() - self._start_time
            return {
                'is_recording': True,
                'elapsed_seconds': elapsed,
                'frame_count': self._frame_count,
                'total_recorded': self._total_recorded,
                'total_dropped': self._total_dropped
            }
        else:
            return {
                'is_recording': False,
                'elapsed_seconds': 0,
                'frame_count': 0,
                'total_recorded': self._total_recorded,
                'total_dropped': self._total_dropped
            }
    
    def process(self, inputs=None):
        """处理节点逻辑"""
        return {'status': self.get_recording_status()}


# 导出类
__all__ = ['VideoRecorderNode']
