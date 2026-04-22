"""
应用控制器模块
协调UI和核心算法的交互
"""

import cv2
import numpy as np
import os


class ApplicationController:
    """应用控制器，协调UI和图像处理"""
    
    def __init__(self, image_processor, main_window):
        self.processor = image_processor
        self.window = main_window
        
        # 图像数据
        self.original_image = None
        self.processed_image = None
        self.current_filter = "原图"
        
        # ROI相关
        self.roi_start = None
        self.roi_end = None
        self.drawing_roi = False
    
    def open_image(self):
        """打开图片文件"""
        file_path = self.window.ask_open_file(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 使用OpenCV读取图片
                self.original_image = cv2.imread(file_path)
                if self.original_image is None:
                    self.window.show_error("错误", "无法读取图片文件")
                    return
                
                self.processed_image = self.original_image.copy()
                self.current_filter = "原图"
                
                self.window.update_display(self.processed_image)
                
                filename = os.path.basename(file_path)
                self.window.set_status(f"已加载: {filename} | 尺寸: {self.original_image.shape[1]}x{self.original_image.shape[0]}")
                
            except Exception as e:
                self.window.show_error("错误", f"加载图片失败: {str(e)}")
    
    def save_image(self):
        """保存处理后的图片"""
        if self.processed_image is None:
            self.window.show_warning("警告", "没有可保存的图片")
            return
        
        file_path = self.window.ask_save_file(
            title="保存图片",
            defaultextension=".png",
            filetypes=[
                ("PNG图片", "*.png"),
                ("JPG图片", "*.jpg"),
                ("BMP图片", "*.bmp"),
                ("TIFF图片", "*.tiff"),
            ]
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.processed_image)
                self.window.set_status(f"已保存: {os.path.basename(file_path)}")
                self.window.show_info("成功", "图片保存成功")
            except Exception as e:
                self.window.show_error("错误", f"保存图片失败: {str(e)}")
    
    def apply_filter(self, filter_type):
        """应用图像处理算法"""
        if self.original_image is None:
            self.window.show_warning("警告", "请先打开图片")
            return
        
        try:
            from core.image_processor import apply_filter
            
            # 更新处理器参数
            params = self.window.get_param_values()
            self.processor.set_canny_params(params['canny_low'], params['canny_high'])
            self.processor.set_threshold_param(params['threshold_value'])
            
            # 应用滤镜
            self.processed_image = apply_filter(filter_type, self.original_image, self.processor)
            
            # 更新当前滤镜名称
            filter_names = {
                "original": "原图",
                "grayscale": "灰度化",
                "gaussian": "高斯模糊",
                "median": "中值滤波",
                "canny": "边缘检测(Canny)",
                "threshold": "二值化",
                "adaptive_threshold": "自适应二值化",
                "sobel": "Sobel边缘检测",
                "laplacian": "Laplacian边缘检测",
                "dilate": "形态学-膨胀",
                "erode": "形态学-腐蚀",
                "equalize": "直方图均衡化",
            }
            self.current_filter = filter_names.get(filter_type, "未知")
            
            self.window.update_display(self.processed_image)
            self.window.set_status(f"已应用: {self.current_filter}")
            
        except Exception as e:
            self.window.show_error("错误", f"应用滤镜失败: {str(e)}")
    
    def update_params(self):
        """更新参数并重新应用滤镜"""
        if self.current_filter != "原图":
            filter_map = {
                "边缘检测(Canny)": "canny",
                "二值化": "threshold",
            }
            if self.current_filter in filter_map:
                self.apply_filter(filter_map[self.current_filter])
    
    def start_roi_selection(self):
        """开始ROI选择"""
        if self.original_image is None:
            self.window.show_warning("警告", "请先打开图片")
            return
        
        self.drawing_roi = True
        self.roi_start = None
        self.roi_end = None
        self.window.set_status("请在图像上拖动鼠标选择ROI区域")
    
    def on_mouse_press(self, event):
        """鼠标按下事件"""
        if not self.drawing_roi:
            return
        
        self.roi_start = (event.x, event.y)
        self.roi_end = (event.x, event.y)
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        if not self.drawing_roi or self.roi_start is None:
            return
        
        self.roi_end = (event.x, event.y)
        self.draw_roi_rectangle()
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        if not self.drawing_roi:
            return
        
        self.roi_end = (event.x, event.y)
        self.window.set_status("ROI选择完成,可以裁剪或取消")
    
    def draw_roi_rectangle(self):
        """绘制ROI矩形框"""
        if self.roi_start is None or self.roi_end is None:
            return
        
        # 清除并重绘图像
        self.window.update_display(self.processed_image)
        
        # 绘制矩形
        self.window.draw_roi_rectangle(self.roi_start, self.roi_end)
    
    def crop_roi(self):
        """裁剪ROI区域"""
        if self.roi_start is None or self.roi_end is None:
            self.window.show_warning("警告", "请先选择ROI区域")
            return
        
        if self.processed_image is None:
            return
        
        # 计算实际坐标
        x1, y1 = min(self.roi_start[0], self.roi_end[0]), min(self.roi_start[1], self.roi_end[1])
        x2, y2 = max(self.roi_start[0], self.roi_end[0]), max(self.roi_start[1], self.roi_end[1])
        
        # 转换为图像坐标
        canvas_width = self.window.canvas.winfo_width()
        canvas_height = self.window.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        img_x1 = int(x1 * self.original_image.shape[1] / canvas_width)
        img_y1 = int(y1 * self.original_image.shape[0] / canvas_height)
        img_x2 = int(x2 * self.original_image.shape[1] / canvas_width)
        img_y2 = int(y2 * self.original_image.shape[0] / canvas_height)
        
        # 边界检查
        img_x1 = max(0, min(img_x1, self.original_image.shape[1]))
        img_y1 = max(0, min(img_y1, self.original_image.shape[0]))
        img_x2 = max(0, min(img_x2, self.original_image.shape[1]))
        img_y2 = max(0, min(img_y2, self.original_image.shape[0]))
        
        # 计算ROI矩形
        roi_rect = (img_x1, img_y1, img_x2 - img_x1, img_y2 - img_y1)
        
        # 裁剪
        cropped = self.processor.crop_roi(self.processed_image, roi_rect)
        
        if cropped.size > 0:
            self.processed_image = cropped.copy()
            self.original_image = self.processed_image.copy()
            self.window.update_display(self.processed_image)
            self.cancel_roi()
            self.window.set_status(f"已裁剪ROI: {cropped.shape[1]}x{cropped.shape[0]}")
        else:
            self.window.show_warning("警告", "ROI区域无效")
    
    def cancel_roi(self):
        """取消ROI选择"""
        self.drawing_roi = False
        self.roi_start = None
        self.roi_end = None
        self.window.update_display(self.processed_image)
        self.window.set_status("已取消ROI选择")
