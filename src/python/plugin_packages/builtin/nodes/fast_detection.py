"""
快速检测订阅者节点

作为相机节点的订阅者，接收图像帧并执行快速目标检测。
适用于实时监控、质量控制等需要即时反馈的场景。

特性：
- 高频处理（默认15fps）
- 简单的边缘检测或颜色分割
- 显示检测结果叠加层
- 输出检测结果统计
"""

import time
from typing import Dict, Any, Optional
import numpy as np
import cv2

from shared_libs.node_base import BaseNode, ParameterContainerWidget


class FastDetectionNode(BaseNode):
    """
    快速检测订阅者节点
    
    通过订阅相机节点的图像流，执行快速目标检测算法。
    
    检测方法：
    1. Canny边缘检测
    2. 颜色阈值分割
    3. 轮廓提取和计数
    
    使用方法：
    1. 创建此节点
    2. 右键点击相机节点 -> "注册为订阅者" -> 选择此节点
    3. 双击此节点查看检测结果
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '快速检测'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(FastDetectionNode, self).__init__()
        
        # 输出端口（可选：输出检测结果）
        self.add_output('检测结果')
        
        # 创建自定义参数容器控件
        self._param_container = ParameterContainerWidget(self.view, 'detection_params', '')
        
        # === 检测参数 ===
        self._param_container.add_combobox('detection_method', '检测方法', 
                                          items=['Canny边缘', '颜色分割', '简单阈值'])
        self._param_container.add_spinbox('threshold_low', '低阈值', value=50, min_value=0, max_value=255)
        self._param_container.add_spinbox('threshold_high', '高阈值', value=150, min_value=0, max_value=255)
        self._param_container.add_combobox('max_fps', '最大帧率', 
                                          items=['10', '15', '20', '25', '30'])
        
        # 设置默认值
        self._param_container.set_value('max_fps', '15')
        
        # 设置值变化回调
        self._param_container.set_value_changed_callback(self._on_param_changed)
        
        # 添加到节点
        self.add_custom_widget(self._param_container, tab='properties')
    
    def _on_param_changed(self, name, value):
        """参数值变化回调"""
        self.set_property(name, str(value))
        
        # 内部状态
        self._latest_result = None
        self._subscriber_id = f"fast_detection_{id(self)}"
        
        # 统计信息
        self._frame_count = 0
        self._last_stats_time = time.time()
        self._current_fps = 0.0
        self._avg_object_count = 0.0
        
    def on_subscribed_by(self, publisher_node):
        """
        当被相机节点订阅时调用
        
        Args:
            publisher_node: CameraCaptureNode 实例
        """
        params = self._param_container.get_values_dict()
        max_fps = float(params.get('max_fps', '15'))
        
        def frame_callback(frame):
            """接收帧的回调函数"""
            try:
                # 执行检测
                result = self._detect(frame)
                self._latest_result = result
                
                # 更新统计
                self._frame_count += 1
                current_time = time.time()
                elapsed = current_time - self._last_stats_time
                
                if elapsed >= 1.0:
                    self._current_fps = self._frame_count / elapsed
                    self._frame_count = 0
                    self._last_stats_time = current_time
                    
                    # 每5秒打印一次统计
                    if int(current_time) % 5 == 0:
                        self.log_info(
                            f"检测统计: FPS={self._current_fps:.1f}, "
                            f"平均对象数={self._avg_object_count:.1f}"
                        )
            
            except Exception as e:
                self.log_error(f"检测错误: {e}")
        
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
    
    def _detect(self, frame: np.ndarray) -> dict:
        """
        执行目标检测
        
        Args:
            frame: 输入图像（BGR格式）
            
        Returns:
            dict: 检测结果
        """
        params = self._param_container.get_values_dict()
        method = params.get('detection_method', 'Canny边缘')
        low_thresh = int(params.get('threshold_low', 50))
        high_thresh = int(params.get('threshold_high', 150))
        
        result = {
            'original': frame.copy(),
            'method': method,
            'objects': [],
            'count': 0
        }
        
        if method == 'Canny边缘':
            # Canny边缘检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, low_thresh, high_thresh)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            result['edges'] = edges
            result['objects'] = contours
            result['count'] = len(contours)
            
            # 绘制结果
            output = frame.copy()
            cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
            result['output'] = output
            
        elif method == '颜色分割':
            # 转换到HSV空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 红色范围（示例）
            lower_red = np.array([0, 100, 100])
            upper_red = np.array([10, 255, 255])
            mask = cv2.inRange(hsv, lower_red, upper_red)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            result['mask'] = mask
            result['objects'] = contours
            result['count'] = len(contours)
            
            # 绘制结果
            output = frame.copy()
            cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
            result['output'] = output
            
        else:  # 简单阈值
            # 转换为灰度
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 阈值分割
            _, binary = cv2.threshold(gray, low_thresh, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            result['binary'] = binary
            result['objects'] = contours
            result['count'] = len(contours)
            
            # 绘制结果
            output = frame.copy()
            cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
            result['output'] = output
        
        # 更新平均对象数
        self._avg_object_count = (
            self._avg_object_count * 0.9 + result['count'] * 0.1
        )
        
        return result
    
    def get_latest_result(self):
        """获取最新的检测结果"""
        return self._latest_result
    
    def process(self, inputs=None):
        """处理节点逻辑"""
        return {'检测结果': self._latest_result}


# 导出类
__all__ = ['FastDetectionNode']
