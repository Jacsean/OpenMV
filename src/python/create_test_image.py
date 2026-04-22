"""
创建测试图片脚本
用于生成示例图片来测试视觉系统
"""

import cv2
import numpy as np

def create_test_image():
    """创建一张测试图片"""
    # 创建白色背景
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # 绘制一些图形
    # 红色矩形
    cv2.rectangle(img, (50, 50), (200, 200), (0, 0, 255), -1)
    
    # 绿色圆形
    cv2.circle(img, (400, 150), 80, (0, 255, 0), -1)
    
    # 蓝色三角形
    pts = np.array([[600, 50], [550, 200], [650, 200]], np.int32)
    cv2.fillPoly(img, [pts], (255, 0, 0))
    
    # 添加文字
    cv2.putText(img, 'OpenCV Vision System', (200, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # 添加渐变
    gradient = np.linspace(0, 255, 800, dtype=np.uint8)
    gradient = np.tile(gradient, (100, 1))
    img[400:500, :] = gradient[:, :, np.newaxis]
    
    # 添加噪声区域
    noise_region = img[520:580, 50:750].copy()
    noise = np.random.randn(*noise_region.shape[:2]) * 30
    for i in range(3):
        noise_region[:, :, i] = np.clip(noise_region[:, :, i].astype(np.int16) + noise.astype(np.int16), 0, 255).astype(np.uint8)
    img[520:580, 50:750] = noise_region
    
    return img

if __name__ == "__main__":
    print("正在创建测试图片...")
    test_img = create_test_image()
    
    filename = "test_image.png"
    cv2.imwrite(filename, test_img)
    print(f"测试图片已保存: {filename}")
    print(f"尺寸: {test_img.shape[1]}x{test_img.shape[0]}")
    print("\n可以使用此图片测试视觉系统的各项功能!")
