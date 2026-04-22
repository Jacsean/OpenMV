#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCV视觉系统 - Python版本（模块化重构版）
基于tkinter和OpenCV的图像处理系统

模块结构：
- core/: 核心图像处理算法
- UI/: 用户界面组件
- controller.py: 应用控制器
"""

import tkinter as tk
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import ImageProcessor
from UI import MainWindow
from controller import ApplicationController


class OpenCVVisionSystem:
    """OpenCV视觉系统主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("OpenCV视觉系统 - Python版")
        self.root.geometry("1400x900")
        
        # 初始化核心组件
        self.processor = ImageProcessor()
        
        # 创建UI
        self.window = MainWindow(root, self)
        
        # 创建控制器
        self.controller = ApplicationController(self.processor, self.window)
        
        # 将控制器的方法暴露给窗口
        self.open_image = self.controller.open_image
        self.save_image = self.controller.save_image
        self.apply_filter = self.controller.apply_filter
        self.update_params = self.controller.update_params
        self.start_roi_selection = self.controller.start_roi_selection
        self.crop_roi = self.controller.crop_roi
        self.cancel_roi = self.controller.cancel_roi
        self.on_mouse_press = self.controller.on_mouse_press
        self.on_mouse_drag = self.controller.on_mouse_drag
        self.on_mouse_release = self.controller.on_mouse_release


def main():
    """主函数"""
    root = tk.Tk()
    app = OpenCVVisionSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
