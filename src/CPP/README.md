# OpenCV视觉系统 - C++版本

## 功能特性

- ✅ 支持常见图片格式 (JPG, PNG, BMP, TIFF, WEBP)
- ✅ 多种图像处理算法
  - 灰度化
  - 高斯模糊
  - 中值滤波
  - Canny边缘检测
  - 二值化/自适应二值化
  - Sobel/Laplacian边缘检测
  - 形态学操作(膨胀/腐蚀)
  - 直方图均衡化
- ✅ 鼠标交互ROI选择与裁剪
- ✅ 键盘快捷键操作
- ✅ 完全离线运行

## 环境要求

- C++11兼容编译器 (GCC, Clang, MSVC等)
- CMake 3.10+
- OpenCV 4.x

## 安装依赖

### Windows (使用vcpkg)
```bash
# 安装vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装OpenCV
.\vcpkg install opencv:x64-windows
.\vcpkg integrate install
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install libopencv-dev cmake
```

### macOS
```bash
brew install opencv cmake
```

## 编译项目

```bash
# 进入CPP目录
cd src/CPP

# 创建build目录
mkdir build
cd build

# 使用CMake配置
cmake ..

# 编译
make  # Linux/macOS
# 或在Windows上使用: cmake --build .
```

## 运行程序

```bash
# 方式1: 命令行指定图片
./bin/vision_system path/to/image.jpg

# 方式2: 运行后输入图片路径
./bin/vision_system
```

## 快捷键说明

| 按键 | 功能 |
|------|------|
| 1 | 原图 |
| 2 | 灰度化 |
| 3 | 高斯模糊 |
| 4 | 中值滤波 |
| 5 | Canny边缘检测 |
| 6 | 二值化 |
| 7 | 自适应二值化 |
| 8 | Sobel边缘检测 |
| 9 | Laplacian边缘检测 |
| 0 | 形态学-膨胀 |
| - | 形态学-腐蚀 |
| = | 直方图均衡化 |
| r | 开始ROI选择 |
| c | 裁剪ROI |
| s | 保存图片 |
| h | 显示帮助 |
| ESC | 退出程序 |

## ROI操作说明

1. 按 `r` 键开始ROI选择
2. 在图像窗口按住鼠标左键拖动选择区域
3. 松开鼠标完成选择
4. 按 `c` 键裁剪选中的区域
5. 按 `r` 键可重新选择

## 注意事项

- 所有处理均在本地完成,无需网络连接
- 支持实时预览处理效果
- ROI选择时显示红色矩形框
- 确保已正确安装OpenCV库
