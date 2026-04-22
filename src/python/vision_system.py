#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCV视觉系统 - Python版本
基于tkinter和OpenCV的图像处理系统
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import os


class OpenCVVisionSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenCV视觉系统 - Python版")
        self.root.geometry("1400x900")
        
        # 初始化变量
        self.original_image = None
        self.processed_image = None
        self.display_image = None
        self.current_filter = "原图"
        self.roi_start = None
        self.roi_end = None
        self.drawing_roi = False
        
        # 创建UI
        self.create_ui()
        
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 文件操作
        file_frame = ttk.LabelFrame(control_frame, text="文件操作", padding=5)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="打开图片", command=self.open_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="保存图片", command=self.save_image).pack(fill=tk.X, pady=2)
        
        # 图像处理算法
        algo_frame = ttk.LabelFrame(control_frame, text="图像处理算法", padding=5)
        algo_frame.pack(fill=tk.X, pady=5)
        
        algorithms = [
            ("原图", lambda: self.apply_filter("original")),
            ("灰度化", lambda: self.apply_filter("grayscale")),
            ("高斯模糊", lambda: self.apply_filter("gaussian")),
            ("中值滤波", lambda: self.apply_filter("median")),
            ("边缘检测(Canny)", lambda: self.apply_filter("canny")),
            ("二值化", lambda: self.apply_filter("threshold")),
            ("自适应二值化", lambda: self.apply_filter("adaptive_threshold")),
            ("Sobel边缘检测", lambda: self.apply_filter("sobel")),
            ("Laplacian边缘检测", lambda: self.apply_filter("laplacian")),
            ("形态学-膨胀", lambda: self.apply_filter("dilate")),
            ("形态学-腐蚀", lambda: self.apply_filter("erode")),
            ("直方图均衡化", lambda: self.apply_filter("equalize")),
        ]
        
        for name, command in algorithms:
            ttk.Button(algo_frame, text=name, command=command).pack(fill=tk.X, pady=2)
        
        # ROI操作
        roi_frame = ttk.LabelFrame(control_frame, text="ROI操作", padding=5)
        roi_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(roi_frame, text="选择ROI", command=self.start_roi_selection).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="裁剪ROI", command=self.crop_roi).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="取消选择", command=self.cancel_roi).pack(fill=tk.X, pady=2)
        
        # 参数调整
        param_frame = ttk.LabelFrame(control_frame, text="参数调整", padding=5)
        param_frame.pack(fill=tk.X, pady=5)
        
        # Canny阈值
        ttk.Label(param_frame, text="Canny低阈值:").pack(anchor=tk.W)
        self.canny_low = ttk.Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.update_params)
        self.canny_low.set(50)
        self.canny_low.pack(fill=tk.X)
        
        ttk.Label(param_frame, text="Canny高阈值:").pack(anchor=tk.W)
        self.canny_high = ttk.Scale(param_frame, from_=0, to=500, orient=tk.HORIZONTAL, command=self.update_params)
        self.canny_high.set(150)
        self.canny_high.pack(fill=tk.X)
        
        # 二值化阈值
        ttk.Label(param_frame, text="二值化阈值:").pack(anchor=tk.W)
        self.threshold_value = ttk.Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.update_params)
        self.threshold_value.set(127)
        self.threshold_value.pack(fill=tk.X)
        
        # 右侧图像显示区域
        display_frame = ttk.LabelFrame(main_frame, text="图像显示", padding=10)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建Canvas用于显示图像
        self.canvas = tk.Canvas(display_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
    def open_image(self):
        """打开图片文件"""
        file_path = filedialog.askopenfilename(
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
                    messagebox.showerror("错误", "无法读取图片文件")
                    return
                
                # 转换颜色空间 BGR -> RGB
                self.original_image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                self.processed_image = self.original_image.copy()
                self.current_filter = "原图"
                
                self.display_image = self.original_image.copy()
                self.update_display()
                
                filename = os.path.basename(file_path)
                self.status_var.set(f"已加载: {filename} | 尺寸: {self.original_image.shape[1]}x{self.original_image.shape[0]}")
                
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {str(e)}")
    
    def save_image(self):
        """保存处理后的图片"""
        if self.processed_image is None:
            messagebox.showwarning("警告", "没有可保存的图片")
            return
        
        file_path = filedialog.asksaveasfilename(
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
                self.status_var.set(f"已保存: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", "图片保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存图片失败: {str(e)}")
    
    def apply_filter(self, filter_type):
        """应用图像处理算法"""
        if self.original_image is None:
            messagebox.showwarning("警告", "请先打开图片")
            return
        
        try:
            if filter_type == "original":
                self.processed_image = self.original_image.copy()
                self.current_filter = "原图"
                
            elif filter_type == "grayscale":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                self.processed_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                self.current_filter = "灰度化"
                
            elif filter_type == "gaussian":
                blurred = cv2.GaussianBlur(self.original_image, (5, 5), 0)
                self.processed_image = blurred.copy()
                self.current_filter = "高斯模糊"
                
            elif filter_type == "median":
                median = cv2.medianBlur(self.original_image, 5)
                self.processed_image = median.copy()
                self.current_filter = "中值滤波"
                
            elif filter_type == "canny":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                low = int(self.canny_low.get())
                high = int(self.canny_high.get())
                edges = cv2.Canny(gray, low, high)
                self.processed_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                self.current_filter = "边缘检测(Canny)"
                
            elif filter_type == "threshold":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                thresh_val = int(self.threshold_value.get())
                _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
                self.processed_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
                self.current_filter = "二值化"
                
            elif filter_type == "adaptive_threshold":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2)
                self.processed_image = cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR)
                self.current_filter = "自适应二值化"
                
            elif filter_type == "sobel":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
                sobel = cv2.magnitude(sobelx, sobely)
                sobel = np.uint8(255 * sobel / np.max(sobel))
                self.processed_image = cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)
                self.current_filter = "Sobel边缘检测"
                
            elif filter_type == "laplacian":
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                laplacian = np.uint8(np.absolute(laplacian))
                self.processed_image = cv2.cvtColor(laplacian, cv2.COLOR_GRAY2BGR)
                self.current_filter = "Laplacian边缘检测"
                
            elif filter_type == "dilate":
                kernel = np.ones((5, 5), np.uint8)
                dilated = cv2.dilate(self.original_image, kernel, iterations=1)
                self.processed_image = dilated.copy()
                self.current_filter = "形态学-膨胀"
                
            elif filter_type == "erode":
                kernel = np.ones((5, 5), np.uint8)
                eroded = cv2.erode(self.original_image, kernel, iterations=1)
                self.processed_image = eroded.copy()
                self.current_filter = "形态学-腐蚀"
                
            elif filter_type == "equalize":
                ycrcb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2YCrCb)
                channels = cv2.split(ycrcb)
                channels[0] = cv2.equalizeHist(channels[0])
                equalized = cv2.merge(channels)
                self.processed_image = cv2.cvtColor(equalized, cv2.COLOR_YCrCb2BGR)
                self.current_filter = "直方图均衡化"
            
            self.update_display()
            self.status_var.set(f"已应用: {self.current_filter}")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用滤镜失败: {str(e)}")
    
    def update_params(self, event=None):
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
            messagebox.showwarning("警告", "请先打开图片")
            return
        
        self.drawing_roi = True
        self.roi_start = None
        self.roi_end = None
        self.status_var.set("请在图像上拖动鼠标选择ROI区域")
    
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
        self.status_var.set("ROI选择完成,可以裁剪或取消")
    
    def draw_roi_rectangle(self):
        """绘制ROI矩形框"""
        if self.roi_start is None or self.roi_end is None:
            return
        
        # 清除并重绘图像
        self.update_display()
        
        # 绘制矩形
        x1, y1 = self.roi_start
        x2, y2 = self.roi_end
        self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
    
    def crop_roi(self):
        """裁剪ROI区域"""
        if self.roi_start is None or self.roi_end is None:
            messagebox.showwarning("警告", "请先选择ROI区域")
            return
        
        if self.processed_image is None:
            return
        
        # 计算实际坐标
        x1, y1 = min(self.roi_start[0], self.roi_end[0]), min(self.roi_start[1], self.roi_end[1])
        x2, y2 = max(self.roi_start[0], self.roi_end[0]), max(self.roi_start[1], self.roi_end[1])
        
        # 转换为图像坐标
        img_x1 = int(x1 * self.original_image.shape[1] / self.canvas.winfo_width())
        img_y1 = int(y1 * self.original_image.shape[0] / self.canvas.winfo_height())
        img_x2 = int(x2 * self.original_image.shape[1] / self.canvas.winfo_width())
        img_y2 = int(y2 * self.original_image.shape[0] / self.canvas.winfo_height())
        
        # 边界检查
        img_x1 = max(0, min(img_x1, self.original_image.shape[1]))
        img_y1 = max(0, min(img_y1, self.original_image.shape[0]))
        img_x2 = max(0, min(img_x2, self.original_image.shape[1]))
        img_y2 = max(0, min(img_y2, self.original_image.shape[0]))
        
        # 裁剪
        cropped = self.processed_image[img_y1:img_y2, img_x1:img_x2]
        
        if cropped.size > 0:
            self.processed_image = cropped.copy()
            self.original_image = self.processed_image.copy()
            self.update_display()
            self.cancel_roi()
            self.status_var.set(f"已裁剪ROI: {cropped.shape[1]}x{cropped.shape[0]}")
        else:
            messagebox.showwarning("警告", "ROI区域无效")
    
    def cancel_roi(self):
        """取消ROI选择"""
        self.drawing_roi = False
        self.roi_start = None
        self.roi_end = None
        self.update_display()
        self.status_var.set("已取消ROI选择")
    
    def update_display(self):
        """更新图像显示"""
        if self.processed_image is None:
            return
        
        # 转换颜色空间
        rgb_image = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
        
        # 调整图像大小以适应canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        img_height, img_width = rgb_image.shape[:2]
        
        # 计算缩放比例
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 调整图像大小
        resized = cv2.resize(rgb_image, (new_width, new_height))
        
        # 转换为PhotoImage
        pil_image = Image.fromarray(resized)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        # 在canvas上显示
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # 保持引用防止被垃圾回收


def main():
    root = tk.Tk()
    app = OpenCVVisionSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
