"""
图像处理核心算法模块
封装各种OpenCV图像处理算法
"""

import cv2
import numpy as np


class ImageProcessor:
    """图像处理类，封装各种OpenCV算法"""
    
    def __init__(self):
        # 默认参数
        self.canny_low = 50
        self.canny_high = 150
        self.threshold_value = 127
    
    def set_canny_params(self, low, high):
        """设置Canny边缘检测参数"""
        self.canny_low = low
        self.canny_high = high
    
    def set_threshold_param(self, value):
        """设置二值化阈值参数"""
        self.threshold_value = value
    
    def apply_grayscale(self, image):
        """灰度化"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def apply_gaussian_blur(self, image):
        """高斯模糊"""
        return cv2.GaussianBlur(image, (5, 5), 0)
    
    def apply_median_blur(self, image):
        """中值滤波"""
        return cv2.medianBlur(image, 5)
    
    def apply_canny(self, image):
        """Canny边缘检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, self.canny_low, self.canny_high)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def apply_threshold(self, image):
        """二值化"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, self.threshold_value, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    
    def apply_adaptive_threshold(self, image):
        """自适应二值化"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR)
    
    def apply_sobel(self, image):
        """Sobel边缘检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel = cv2.magnitude(sobelx, sobely)
        sobel = np.uint8(255 * sobel / np.max(sobel))
        return cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)
    
    def apply_laplacian(self, image):
        """Laplacian边缘检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        return cv2.cvtColor(laplacian, cv2.COLOR_GRAY2BGR)
    
    def apply_dilate(self, image):
        """形态学膨胀"""
        kernel = np.ones((5, 5), np.uint8)
        return cv2.dilate(image, kernel, iterations=1)
    
    def apply_erode(self, image):
        """形态学腐蚀"""
        kernel = np.ones((5, 5), np.uint8)
        return cv2.erode(image, kernel, iterations=1)
    
    def apply_equalize_hist(self, image):
        """直方图均衡化"""
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        channels = cv2.split(ycrcb)
        channels[0] = cv2.equalizeHist(channels[0])
        equalized = cv2.merge(channels)
        return cv2.cvtColor(equalized, cv2.COLOR_YCrCb2BGR)
    
    def crop_roi(self, image, roi_rect):
        """根据ROI矩形裁剪图像"""
        x, y, w, h = roi_rect
        # 确保ROI在图像范围内
        height, width = image.shape[:2]
        x = max(0, min(x, width))
        y = max(0, min(y, height))
        w = max(0, min(w, width - x))
        h = max(0, min(h, height - y))
        
        if w > 0 and h > 0:
            return image[y:y+h, x:x+w]
        else:
            return image


# 图像处理算法映射
ALGORITHM_MAP = {
    "original": lambda img, proc: img.copy(),
    "grayscale": lambda img, proc: proc.apply_grayscale(img),
    "gaussian": lambda img, proc: proc.apply_gaussian_blur(img),
    "median": lambda img, proc: proc.apply_median_blur(img),
    "canny": lambda img, proc: proc.apply_canny(img),
    "threshold": lambda img, proc: proc.apply_threshold(img),
    "adaptive_threshold": lambda img, proc: proc.apply_adaptive_threshold(img),
    "sobel": lambda img, proc: proc.apply_sobel(img),
    "laplacian": lambda img, proc: proc.apply_laplacian(img),
    "dilate": lambda img, proc: proc.apply_dilate(img),
    "erode": lambda img, proc: proc.apply_erode(img),
    "equalize": lambda img, proc: proc.apply_equalize_hist(img),
}


def apply_filter(filter_type, image, processor):
    """应用图像处理滤镜"""
    if filter_type in ALGORITHM_MAP:
        return ALGORITHM_MAP[filter_type](image, processor)
    else:
        return image