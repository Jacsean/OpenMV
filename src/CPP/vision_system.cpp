#include "vision_system.h"
#include <iostream>
#include <fstream>

VisionSystem::VisionSystem() 
    : selectingROI(false), drawingROI(false) {
    windowName = "OpenCV视觉系统 - C++版";
}

VisionSystem::~VisionSystem() {
    cv::destroyAllWindows();
}

void VisionSystem::onMouse(int event, int x, int y, int flags, void* userdata) {
    VisionSystem* vs = static_cast<VisionSystem*>(userdata);
    
    if (!vs->selectingROI) return;
    
    switch (event) {
        case cv::EVENT_LBUTTONDOWN:
            vs->roiStart = cv::Point(x, y);
            vs->roiEnd = cv::Point(x, y);
            vs->drawingROI = true;
            break;
            
        case cv::EVENT_MOUSEMOVE:
            if (vs->drawingROI) {
                vs->roiEnd = cv::Point(x, y);
                vs->updateDisplay();
                
                // 绘制ROI矩形
                cv::Mat temp = vs->displayImage.clone();
                cv::Rect rect(vs->roiStart, vs->roiEnd);
                rect = rect & cv::Rect(0, 0, temp.cols, temp.rows);
                cv::rectangle(temp, rect, cv::Scalar(0, 0, 255), 2);
                cv::imshow(vs->windowName, temp);
            }
            break;
            
        case cv::EVENT_LBUTTONUP:
            if (vs->drawingROI) {
                vs->roiEnd = cv::Point(x, y);
                vs->drawingROI = false;
                
                // 确保rect有效
                vs->roiRect.x = std::min(vs->roiStart.x, vs->roiEnd.x);
                vs->roiRect.y = std::min(vs->roiStart.y, vs->roiEnd.y);
                vs->roiRect.width = std::abs(vs->roiEnd.x - vs->roiStart.x);
                vs->roiRect.height = std::abs(vs->roiEnd.y - vs->roiStart.y);
                
                std::cout << "ROI选择完成: " << vs->roiRect << std::endl;
            }
            break;
    }
}

bool VisionSystem::loadImage(const std::string& filename) {
    originalImage = cv::imread(filename);
    if (originalImage.empty()) {
        std::cerr << "无法读取图片文件: " << filename << std::endl;
        return false;
    }
    
    processedImage = originalImage.clone();
    displayImage = originalImage.clone();
    
    std::cout << "图片加载成功: " << filename << std::endl;
    std::cout << "尺寸: " << originalImage.cols << "x" << originalImage.rows << std::endl;
    
    return true;
}

bool VisionSystem::saveImage(const std::string& filename) {
    if (processedImage.empty()) {
        std::cerr << "没有可保存的图片" << std::endl;
        return false;
    }
    
    bool success = cv::imwrite(filename, processedImage);
    if (success) {
        std::cout << "图片保存成功: " << filename << std::endl;
    } else {
        std::cerr << "图片保存失败" << std::endl;
    }
    
    return success;
}

void VisionSystem::applyGrayscale() {
    if (originalImage.empty()) return;
    
    cv::Mat gray;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    cv::cvtColor(gray, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: 灰度化" << std::endl;
}

void VisionSystem::applyGaussianBlur() {
    if (originalImage.empty()) return;
    
    cv::GaussianBlur(originalImage, processedImage, cv::Size(5, 5), 0);
    updateDisplay();
    std::cout << "已应用: 高斯模糊" << std::endl;
}

void VisionSystem::applyMedianBlur() {
    if (originalImage.empty()) return;
    
    cv::medianBlur(originalImage, processedImage, 5);
    updateDisplay();
    std::cout << "已应用: 中值滤波" << std::endl;
}

void VisionSystem::applyCanny() {
    if (originalImage.empty()) return;
    
    cv::Mat gray, edges;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    cv::Canny(gray, edges, 50, 150);
    cv::cvtColor(edges, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: Canny边缘检测" << std::endl;
}

void VisionSystem::applyThreshold() {
    if (originalImage.empty()) return;
    
    cv::Mat gray, thresh;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    cv::threshold(gray, thresh, 127, 255, cv::THRESH_BINARY);
    cv::cvtColor(thresh, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: 二值化" << std::endl;
}

void VisionSystem::applyAdaptiveThreshold() {
    if (originalImage.empty()) return;
    
    cv::Mat gray, adaptive;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    cv::adaptiveThreshold(gray, adaptive, 255, cv::ADAPTIVE_THRESH_GAUSSIAN_C,
                         cv::THRESH_BINARY, 11, 2);
    cv::cvtColor(adaptive, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: 自适应二值化" << std::endl;
}

void VisionSystem::applySobel() {
    if (originalImage.empty()) return;
    
    cv::Mat gray, sobelx, sobely, sobel;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    
    cv::Sobel(gray, sobelx, CV_64F, 1, 0, 3);
    cv::Sobel(gray, sobely, CV_64F, 0, 1, 3);
    cv::magnitude(sobelx, sobely, sobel);
    
    cv::normalize(sobel, sobel, 0, 255, cv::NORM_MINMAX);
    sobel.convertTo(sobel, CV_8U);
    cv::cvtColor(sobel, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: Sobel边缘检测" << std::endl;
}

void VisionSystem::applyLaplacian() {
    if (originalImage.empty()) return;
    
    cv::Mat gray, laplacian;
    cv::cvtColor(originalImage, gray, cv::COLOR_BGR2GRAY);
    cv::Laplacian(gray, laplacian, CV_64F);
    
    cv::convertScaleAbs(laplacian, laplacian);
    cv::cvtColor(laplacian, processedImage, cv::COLOR_GRAY2BGR);
    
    updateDisplay();
    std::cout << "已应用: Laplacian边缘检测" << std::endl;
}

void VisionSystem::applyDilate() {
    if (originalImage.empty()) return;
    
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(5, 5));
    cv::dilate(originalImage, processedImage, kernel);
    
    updateDisplay();
    std::cout << "已应用: 形态学-膨胀" << std::endl;
}

void VisionSystem::applyErode() {
    if (originalImage.empty()) return;
    
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(5, 5));
    cv::erode(originalImage, processedImage, kernel);
    
    updateDisplay();
    std::cout << "已应用: 形态学-腐蚀" << std::endl;
}

void VisionSystem::applyEqualizeHist() {
    if (originalImage.empty()) return;
    
    cv::Mat ycrcb, equalized;
    cv::cvtColor(originalImage, ycrcb, cv::COLOR_BGR2YCrCb);
    
    std::vector<cv::Mat> channels;
    cv::split(ycrcb, channels);
    cv::equalizeHist(channels[0], channels[0]);
    cv::merge(channels, ycrcb);
    
    cv::cvtColor(ycrcb, processedImage, cv::COLOR_YCrCb2BGR);
    
    updateDisplay();
    std::cout << "已应用: 直方图均衡化" << std::endl;
}

void VisionSystem::startROISelection() {
    if (originalImage.empty()) {
        std::cerr << "请先加载图片" << std::endl;
        return;
    }
    
    selectingROI = true;
    drawingROI = false;
    std::cout << "请在图像窗口拖动鼠标选择ROI区域" << std::endl;
    std::cout << "按 'c' 键裁剪, 按 'r' 键重新选择, 按 'q' 键退出选择" << std::endl;
}

void VisionSystem::cropROI() {
    if (roiRect.width == 0 || roiRect.height == 0) {
        std::cerr << "请先选择ROI区域" << std::endl;
        return;
    }
    
    // 边界检查
    roiRect = roiRect & cv::Rect(0, 0, processedImage.cols, processedImage.rows);
    
    cv::Mat cropped = processedImage(roiRect).clone();
    
    if (!cropped.empty()) {
        processedImage = cropped;
        originalImage = processedImage.clone();
        roiRect = cv::Rect();
        selectingROI = false;
        
        updateDisplay();
        std::cout << "ROI裁剪完成: " << cropped.cols << "x" << cropped.rows << std::endl;
    }
}

void VisionSystem::cancelROI() {
    selectingROI = false;
    drawingROI = false;
    roiRect = cv::Rect();
    updateDisplay();
    std::cout << "已取消ROI选择" << std::endl;
}

void VisionSystem::showImage(const std::string& title) {
    if (processedImage.empty()) {
        std::cerr << "没有可显示的图片" << std::endl;
        return;
    }
    
    cv::namedWindow(title, cv::WINDOW_AUTOSIZE);
    cv::setMouseCallback(title, onMouse, this);
    cv::imshow(title, processedImage);
}

void VisionSystem::updateDisplay() {
    if (processedImage.empty()) return;
    
    displayImage = processedImage.clone();
    cv::imshow(windowName, displayImage);
}

void VisionSystem::run() {
    if (originalImage.empty()) {
        std::cout << "请先使用 loadImage() 加载图片" << std::endl;
        return;
    }
    
    showImage(windowName);
    
    std::cout << "\n=== OpenCV视觉系统 - C++版 ===" << std::endl;
    std::cout << "快捷键说明:" << std::endl;
    std::cout << "  1 - 原图          2 - 灰度化       3 - 高斯模糊" << std::endl;
    std::cout << "  4 - 中值滤波      5 - Canny边缘    6 - 二值化" << std::endl;
    std::cout << "  7 - 自适应二值化  8 - Sobel        9 - Laplacian" << std::endl;
    std::cout << "  0 - 膨胀          - - 腐蚀         = - 直方图均衡化" << std::endl;
    std::cout << "  r - 开始ROI选择   c - 裁剪ROI      ESC - 退出" << std::endl;
    std::cout << "  s - 保存图片      h - 显示帮助" << std::endl;
    std::cout << "================================\n" << std::endl;
    
    while (true) {
        int key = cv::waitKey(0) & 0xFF;
        
        switch (key) {
            case 27: // ESC
                std::cout << "退出程序" << std::endl;
                return;
                
            case '1':
                processedImage = originalImage.clone();
                updateDisplay();
                std::cout << "已应用: 原图" << std::endl;
                break;
                
            case '2':
                applyGrayscale();
                break;
                
            case '3':
                applyGaussianBlur();
                break;
                
            case '4':
                applyMedianBlur();
                break;
                
            case '5':
                applyCanny();
                break;
                
            case '6':
                applyThreshold();
                break;
                
            case '7':
                applyAdaptiveThreshold();
                break;
                
            case '8':
                applySobel();
                break;
                
            case '9':
                applyLaplacian();
                break;
                
            case '0':
                applyDilate();
                break;
                
            case '-':
                applyErode();
                break;
                
            case '=':
                applyEqualizeHist();
                break;
                
            case 'r':
                startROISelection();
                break;
                
            case 'c':
                cropROI();
                break;
                
            case 's': {
                std::string savePath = "output.png";
                std::cout << "输入保存路径 (默认: output.png): ";
                std::getline(std::cin, savePath);
                if (savePath.empty()) savePath = "output.png";
                saveImage(savePath);
                break;
            }
                
            case 'h':
                std::cout << "\n=== 帮助信息 ===" << std::endl;
                std::cout << "支持的文件格式: JPG, PNG, BMP, TIFF, WEBP" << std::endl;
                std::cout << "使用数字键选择滤镜,ESC退出" << std::endl;
                std::cout << "===============\n" << std::endl;
                break;
        }
    }
}
