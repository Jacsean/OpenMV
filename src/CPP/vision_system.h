#ifndef VISION_SYSTEM_H
#define VISION_SYSTEM_H

#include <opencv2/opencv.hpp>
#include <string>
#include <vector>
#include <functional>

class VisionSystem {
private:
    cv::Mat originalImage;
    cv::Mat processedImage;
    cv::Mat displayImage;
    
    // ROI相关
    cv::Rect roiRect;
    bool selectingROI;
    bool drawingROI;
    cv::Point roiStart;
    cv::Point roiEnd;
    
    // 当前窗口
    std::string windowName;
    
    // 回调函数
    static void onMouse(int event, int x, int y, int flags, void* userdata);
    
public:
    VisionSystem();
    ~VisionSystem();
    
    // 文件操作
    bool loadImage(const std::string& filename);
    bool saveImage(const std::string& filename);
    
    // 图像处理算法
    void applyGrayscale();
    void applyGaussianBlur();
    void applyMedianBlur();
    void applyCanny();
    void applyThreshold();
    void applyAdaptiveThreshold();
    void applySobel();
    void applyLaplacian();
    void applyDilate();
    void applyErode();
    void applyEqualizeHist();
    
    // ROI操作
    void startROISelection();
    void cropROI();
    void cancelROI();
    
    // 显示
    void showImage(const std::string& title = "OpenCV视觉系统");
    void updateDisplay();
    
    // 获取图像
    cv::Mat getProcessedImage() { return processedImage; }
    cv::Mat getOriginalImage() { return originalImage; }
    
    // 运行主循环
    void run();
};

#endif // VISION_SYSTEM_H
