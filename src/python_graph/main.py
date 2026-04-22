#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形化视觉编程系统 - 主程序入口

类似海康VM、基恩士CV-X、康耐视VisionPro的可视化编程框架
基于NodeGraphQt和OpenCV实现
"""

import sys
from PySide2 import QtWidgets

# 添加项目根目录到路径
sys.path.insert(0, '.')

from ui.main_window import MainWindow


def main():
    """
    主函数
    """
    # 创建Qt应用
    app = QtWidgets.QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
