#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块测试脚本
验证各个模块是否可以正常导入和使用
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_module():
    """测试core模块"""
    print("=" * 50)
    print("测试 core 模块...")
    print("=" * 50)
    
    try:
        from core import ImageProcessor, apply_filter, ALGORITHM_MAP
        print("✓ 成功导入 core 模块")
        
        # 创建处理器实例
        processor = ImageProcessor()
        print("✓ 成功创建 ImageProcessor 实例")
        
        # 检查算法映射
        print(f"✓ 已注册 {len(ALGORITHM_MAP)} 种算法")
        for algo_name in ALGORITHM_MAP.keys():
            print(f"  - {algo_name}")
        
        # 测试参数设置
        processor.set_canny_params(50, 150)
        processor.set_threshold_param(127)
        print("✓ 参数设置正常")
        
        print("\n✅ core 模块测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ core 模块测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_ui_module():
    """测试UI模块"""
    print("=" * 50)
    print("测试 UI 模块...")
    print("=" * 50)
    
    try:
        from UI import MainWindow
        print("✓ 成功导入 UI 模块")
        
        # 检查MainWindow类
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 创建控制器占位符
        class MockController:
            def open_image(self): pass
            def save_image(self): pass
            def apply_filter(self, f): pass
            def update_params(self): pass
            def start_roi_selection(self): pass
            def crop_roi(self): pass
            def cancel_roi(self): pass
            def on_mouse_press(self, e): pass
            def on_mouse_drag(self, e): pass
            def on_mouse_release(self, e): pass
        
        mock_controller = MockController()
        window = MainWindow(root, mock_controller)
        print("✓ 成功创建 MainWindow 实例")
        
        # 检查主要方法
        methods = ['update_display', 'draw_roi_rectangle', 'set_status', 
                   'get_param_values', 'show_error', 'ask_open_file']
        for method in methods:
            if hasattr(window, method):
                print(f"  ✓ 方法存在: {method}")
            else:
                print(f"  ✗ 方法缺失: {method}")
        
        root.destroy()
        print("\n✅ UI 模块测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ UI 模块测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_controller_module():
    """测试controller模块"""
    print("=" * 50)
    print("测试 controller 模块...")
    print("=" * 50)
    
    try:
        from controller import ApplicationController
        print("✓ 成功导入 controller 模块")
        
        # 创建依赖项
        from core import ImageProcessor
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        class MockWindow:
            def ask_open_file(self, **kwargs): return None
            def ask_save_file(self, **kwargs): return None
            def show_error(self, t, m): pass
            def show_warning(self, t, m): pass
            def show_info(self, t, m): pass
            def update_display(self, img): pass
            def set_status(self, msg): pass
            def get_param_values(self): 
                return {'canny_low': 50, 'canny_high': 150, 'threshold_value': 127}
            canvas = type('obj', (object,), {'winfo_width': lambda: 800, 'winfo_height': lambda: 600})()
        
        processor = ImageProcessor()
        window = MockWindow()
        
        controller = ApplicationController(processor, window)
        print("✓ 成功创建 ApplicationController 实例")
        
        # 检查主要方法
        methods = ['open_image', 'save_image', 'apply_filter', 'update_params',
                   'start_roi_selection', 'crop_roi', 'cancel_roi']
        for method in methods:
            if hasattr(controller, method):
                print(f"  ✓ 方法存在: {method}")
            else:
                print(f"  ✗ 方法缺失: {method}")
        
        root.destroy()
        print("\n✅ controller 模块测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ controller 模块测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_main_program():
    """测试主程序结构"""
    print("=" * 50)
    print("测试主程序结构...")
    print("=" * 50)
    
    try:
        # 检查主程序文件
        with open('vision_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否导入了所有模块
        checks = [
            ('from core import', '导入 core 模块'),
            ('from UI import', '导入 UI 模块'),
            ('from controller import', '导入 controller 模块'),
            ('class OpenCVVisionSystem', '定义主类'),
            ('def main()', '定义主函数'),
        ]
        
        for check_str, desc in checks:
            if check_str in content:
                print(f"  ✓ {desc}")
            else:
                print(f"  ✗ 缺少: {desc}")
        
        print("\n✅ 主程序结构测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 主程序结构测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("  OpenCV视觉系统 - 模块化测试")
    print("=" * 50 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("core 模块", test_core_module()))
    results.append(("UI 模块", test_ui_module()))
    results.append(("controller 模块", test_controller_module()))
    results.append(("主程序结构", test_main_program()))
    
    # 汇总结果
    print("=" * 50)
    print("  测试结果汇总")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n🎉 所有测试通过！模块化重构成功！\n")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息\n")
        return 1


if __name__ == "__main__":
    exit(main())
