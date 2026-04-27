"""
图像标注功能 UI 测试

使用方法:
1. 运行此脚本
2. 在弹出的窗口中测试标注功能
3. 按提示操作验证各项功能
"""

import sys
import os
import numpy as np
import cv2

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PySide2 import QtWidgets, QtGui


def create_test_image():
    """创建测试图像"""
    # 创建白色背景
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # 绘制一些参考图形
    cv2.rectangle(img, (100, 100), (300, 300), (0, 0, 255), 2)
    cv2.circle(img, (450, 200), 60, (255, 0, 0), 2)
    cv2.putText(img, "Test Image", (200, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return img


class SimpleAnnotationTest(QtWidgets.QDialog):
    """简化的标注测试对话框"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像标注功能测试")
        self.setMinimumSize(800, 600)
        
        # 创建测试图像
        self.test_image = create_test_image()
        
        # 主布局
        layout = QtWidgets.QVBoxLayout(self)
        
        # 说明标签
        info_label = QtWidgets.QLabel(
            "<h3>📝 图像标注功能测试</h3>"
            "<p><b>测试步骤:</b></p>"
            "<ol>"
            "<li>点击 <b>'▭ 矩形'</b> 按钮，在图像上拖拽绘制矩形</li>"
            "<li>点击 <b>'○ 圆形'</b> 按钮，在图像上拖拽绘制圆形</li>"
            "<li>点击 <b>'T 文字'</b> 按钮，点击位置输入文字</li>"
            "<li>点击 <b>'🗑 清除标注'</b> 按钮，清除所有标注</li>"
            "<li>使用缩放和平移功能，确认标注跟随图像</li>"
            "</ol>"
            "<p><b>预期结果:</b></p>"
            "<ul>"
            "<li>✅ 绘制的形状实时显示（绿色虚线预览）</li>"
            "<li>✅ 释放鼠标后形状固定显示（绿色实线）</li>"
            "<li>✅ 缩放/平移时标注位置正确</li>"
            "<li>✅ 清除按钮可以删除所有标注</li>"
            "</ul>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 图像预览区域（简化版，不使用完整的ImagePreviewDialog）
        self.graphics_view = QtWidgets.QGraphicsView()
        self.graphics_view.setStyleSheet("background-color: #2b2b2b;")
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)
        
        # 显示图像
        self.display_image()
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("就绪 - 请按照上述步骤测试")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        print("✅ 测试窗口已创建")
        print("📌 请在窗口中手动测试标注功能")
    
    def display_image(self):
        """显示测试图像"""
        self.scene.clear()
        
        height, width = self.test_image.shape[:2]
        rgb_image = cv2.cvtColor(self.test_image, cv2.COLOR_BGR2RGB)
        
        qt_image = QtGui.QImage(
            rgb_image.data,
            width,
            height,
            width * 3,
            QtGui.QImage.Format_RGB888
        )
        
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.scene.addPixmap(pixmap)
        
        self.graphics_view.fitInView(
            self.scene.items()[0],
            QtCore.Qt.KeepAspectRatio
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    print("=" * 60)
    print("🧪 图像标注功能 UI 测试")
    print("=" * 60)
    
    dialog = SimpleAnnotationTest()
    dialog.show()
    
    sys.exit(app.exec_())
