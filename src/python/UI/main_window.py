"""
主窗口UI模块
基于tkinter的图形界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2


class MainWindow:
    """主窗口类，负责UI显示和交互"""
    
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # 初始化变量
        self.display_image = None
        
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
        
        ttk.Button(file_frame, text="打开图片", command=self.controller.open_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="保存图片", command=self.controller.save_image).pack(fill=tk.X, pady=2)
        
        # 图像处理算法
        algo_frame = ttk.LabelFrame(control_frame, text="图像处理算法", padding=5)
        algo_frame.pack(fill=tk.X, pady=5)
        
        algorithms = [
            ("原图", lambda: self.controller.apply_filter("original")),
            ("灰度化", lambda: self.controller.apply_filter("grayscale")),
            ("高斯模糊", lambda: self.controller.apply_filter("gaussian")),
            ("中值滤波", lambda: self.controller.apply_filter("median")),
            ("边缘检测(Canny)", lambda: self.controller.apply_filter("canny")),
            ("二值化", lambda: self.controller.apply_filter("threshold")),
            ("自适应二值化", lambda: self.controller.apply_filter("adaptive_threshold")),
            ("Sobel边缘检测", lambda: self.controller.apply_filter("sobel")),
            ("Laplacian边缘检测", lambda: self.controller.apply_filter("laplacian")),
            ("形态学-膨胀", lambda: self.controller.apply_filter("dilate")),
            ("形态学-腐蚀", lambda: self.controller.apply_filter("erode")),
            ("直方图均衡化", lambda: self.controller.apply_filter("equalize")),
        ]
        
        for name, command in algorithms:
            ttk.Button(algo_frame, text=name, command=command).pack(fill=tk.X, pady=2)
        
        # ROI操作
        roi_frame = ttk.LabelFrame(control_frame, text="ROI操作", padding=5)
        roi_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(roi_frame, text="选择ROI", command=self.controller.start_roi_selection).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="裁剪ROI", command=self.controller.crop_roi).pack(fill=tk.X, pady=2)
        ttk.Button(roi_frame, text="取消选择", command=self.controller.cancel_roi).pack(fill=tk.X, pady=2)
        
        # 参数调整
        param_frame = ttk.LabelFrame(control_frame, text="参数调整", padding=5)
        param_frame.pack(fill=tk.X, pady=5)
        
        # Canny阈值
        ttk.Label(param_frame, text="Canny低阈值:").pack(anchor=tk.W)
        self.canny_low = ttk.Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL, 
                                   command=lambda v: self.controller.update_params())
        self.canny_low.set(50)
        self.canny_low.pack(fill=tk.X)
        
        ttk.Label(param_frame, text="Canny高阈值:").pack(anchor=tk.W)
        self.canny_high = ttk.Scale(param_frame, from_=0, to=500, orient=tk.HORIZONTAL,
                                    command=lambda v: self.controller.update_params())
        self.canny_high.set(150)
        self.canny_high.pack(fill=tk.X)
        
        # 二值化阈值
        ttk.Label(param_frame, text="二值化阈值:").pack(anchor=tk.W)
        self.threshold_value = ttk.Scale(param_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                                         command=lambda v: self.controller.update_params())
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
        
        # 保存引用以便外部访问
        self.param_widgets = {
            'canny_low': self.canny_low,
            'canny_high': self.canny_high,
            'threshold_value': self.threshold_value
        }
    
    def on_mouse_press(self, event):
        """鼠标按下事件 - 转发给控制器"""
        self.controller.on_mouse_press(event)
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件 - 转发给控制器"""
        self.controller.on_mouse_drag(event)
    
    def on_mouse_release(self, event):
        """鼠标释放事件 - 转发给控制器"""
        self.controller.on_mouse_release(event)
    
    def update_display(self, image):
        """更新图像显示"""
        if image is None:
            return
        
        # 转换颜色空间 BGR -> RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
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
    
    def draw_roi_rectangle(self, start, end):
        """绘制ROI矩形框"""
        if start is None or end is None:
            return
        
        # 清除并重绘图像（由控制器负责）
        # 这里只绘制矩形
        x1, y1 = start
        x2, y2 = end
        self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete("all")
    
    def set_status(self, message):
        """设置状态栏消息"""
        self.status_var.set(message)
    
    def get_param_values(self):
        """获取参数值"""
        return {
            'canny_low': int(self.canny_low.get()),
            'canny_high': int(self.canny_high.get()),
            'threshold_value': int(self.threshold_value.get())
        }
    
    def show_error(self, title, message):
        """显示错误对话框"""
        messagebox.showerror(title, message)
    
    def show_warning(self, title, message):
        """显示警告对话框"""
        messagebox.showwarning(title, message)
    
    def show_info(self, title, message):
        """显示信息对话框"""
        messagebox.showinfo(title, message)
    
    def ask_open_file(self, title, filetypes):
        """打开文件对话框"""
        return filedialog.askopenfilename(title=title, filetypes=filetypes)
    
    def ask_save_file(self, title, defaultextension, filetypes):
        """保存文件对话框"""
        return filedialog.asksaveasfilename(
            title=title, 
            defaultextension=defaultextension, 
            filetypes=filetypes
        )
