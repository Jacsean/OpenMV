"""
图像显示节点 - 用于显示图像，支持双击打开预览窗口
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np
import json


class ImageViewNode(BaseNode):
    """
    图像显示节点
    
    用于显示图像，支持双击打开预览窗口（在主窗口中实现）
    
    功能说明：
    - 接收图像数据输入
    - 缓存最后一张处理的图像
    - 双击节点可打开图像预览窗口（在主窗口中实现）
    - 显示图像尺寸、通道数等信息
    - 支持ROI和Mask数据的导出
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = '图像显示'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(ImageViewNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口（传递图像、ROI和Mask信息）
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('ROI数据', color=(255, 165, 0))  # 橙色端口
        self.add_output('Mask图像', color=(100, 100, 255))  # 蓝色端口
        
        # 状态信息显示
        self._param_container = ParameterContainerWidget(self.view, 'image_view_params', '')
        self._param_container.add_text_input('status', '状态信息', text='')
        self._param_container.add_text_input('roi_data', 'ROI数据(JSON)', text='')
        self._param_container.add_text_input('mask_status', 'Mask状态', text='无Mask')
        
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')
        
        # 缓存最后一张处理的图像（用于预览）
        self._cached_image = None
        
        # 缓存ROI数据
        self._roi_data = []
        
        # 缓存Mask图像
        self._mask_image = None
    
    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))

    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表，inputs[0]为第一个端口的输入
            
        Returns:
            dict: 输出端口名称 -> 数据
        """
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self._cached_image = None
                self.set_property('status', '无输入')
                return {'输出图像': None, 'ROI数据': None, 'Mask图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self._cached_image = None
                self.set_property('status', '无有效图像')
                return {'输出图像': None, 'ROI数据': None, 'Mask图像': None}
            
            # Step 1: 缓存图像用于预览
            self._cached_image = image.copy()
            
            # Step 2: 获取图像信息
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            
            # Step 3: 构建状态信息
            status_msg = f"图像尺寸: {width}x{height}"
            if channels > 1:
                status_msg += f", 通道数: {channels}"
            
            dtype = str(image.dtype)
            status_msg += f", 类型: {dtype}"
            
            # 添加ROI数量信息
            roi_count = len(self._roi_data)
            if roi_count > 0:
                status_msg += f", ROI数: {roi_count}"
            
            self.set_property('status', status_msg)
            
            # Step 4: 输出图像、ROI数据和Mask图像
            return {
                '输出图像': image,
                'ROI数据': self._roi_data if self._roi_data else None,
                'Mask图像': self._mask_image
            }

        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            self.set_property('status', error_msg)
            self.log_error(f"图像显示节点错误: {e}")
            return {'输出图像': None, 'ROI数据': None, 'Mask图像': None}
    
    def get_cached_image(self):
        """
        获取缓存的图像（用于预览）
        
        Returns:
            numpy.ndarray or None: 缓存的图像数据
        """
        return self._cached_image
    
    def set_roi_data(self, roi_data):
        """
        设置ROI数据（从预览窗口调用）
        
        Args:
            roi_data: ROI数据列表或JSON字符串
        """
        if isinstance(roi_data, str):
            # 如果是JSON字符串，解析它
            try:
                self._roi_data = json.loads(roi_data)
                self.set_property('roi_data', roi_data)
            except Exception as e:
                self.log_error(f"解析ROI数据失败: {e}")
                self._roi_data = []
        else:
            # 直接赋值
            self._roi_data = roi_data if roi_data else []
            # 更新属性显示
            roi_json = json.dumps(self._roi_data, ensure_ascii=False, indent=2)
            self.set_property('roi_data', roi_json)
        
        # 更新状态信息
        self._update_status_info()
    
    def set_mask_image(self, mask_image):
        """
        设置Mask图像（从预览窗口调用）
        
        Args:
            mask_image: 8位灰度图 (HxW, uint8)，区域内=255，区域外=0
        """
        if mask_image is not None and isinstance(mask_image, np.ndarray):
            self._mask_image = mask_image.copy()
            
            # 统计Mask覆盖面积
            mask_area = np.count_nonzero(mask_image)
            total_area = mask_image.shape[0] * mask_image.shape[1]
            coverage = (mask_area / total_area * 100) if total_area > 0 else 0
            
            mask_status = f"Mask面积: {mask_area:,}像素 ({coverage:.1f}%)"
            self.set_property('mask_status', mask_status)
        else:
            self._mask_image = None
            self.set_property('mask_status', '无Mask')
        
        # 更新状态信息
        self._update_status_info()
    
    def _update_status_info(self):
        """更新状态信息（包含ROI和Mask信息）"""
        if self._cached_image is None:
            return
        
        height, width = self._cached_image.shape[:2]
        channels = self._cached_image.shape[2] if len(self._cached_image.shape) == 3 else 1
        
        status_msg = f"图像尺寸: {width}x{height}"
        if channels > 1:
            status_msg += f", 通道数: {channels}"
        
        # 添加ROI数量信息
        roi_count = len(self._roi_data)
        if roi_count > 0:
            status_msg += f", ROI数: {roi_count}"
        
        # 添加Mask信息
        if self._mask_image is not None:
            mask_area = np.count_nonzero(self._mask_image)
            status_msg += f", Mask面积: {mask_area:,}像素"
        
        self.set_property('status', status_msg)