#include "vision_system.h"
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    VisionSystem vs;
    
    std::string imagePath;
    
    if (argc > 1) {
        imagePath = argv[1];
    } else {
        std::cout << "=== OpenCV视觉系统 - C++版 ===" << std::endl;
        std::cout << "请输入图片路径: ";
        std::getline(std::cin, imagePath);
    }
    
    if (imagePath.empty()) {
        std::cerr << "错误: 未指定图片路径" << std::endl;
        return -1;
    }
    
    if (!vs.loadImage(imagePath)) {
        std::cerr << "错误: 加载图片失败" << std::endl;
        return -1;
    }
    
    // 运行主循环
    vs.run();
    
    return 0;
}
