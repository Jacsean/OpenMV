# OpenCV视觉系统 - C++版本

基于OpenCV HighGUI的C++图像处理系统，提供高性能的图像处理能力。

## 📋 文档导航

- 📘 **本文档**: C++版本完整使用说明
- 🔙 [返回主项目文档](../../README.md)
- 📗 [Python版本详解](../python/README.md) - Python模块化架构

---

## 🎯 版本特色

- ⚡ **高性能**: C++原生性能，适合生产环境
- 🎮 **快捷键操作**: 高效的键盘交互
- 🖱️ **鼠标ROI**: 直观的区域选择
- 💾 **轻量级**: 无需Python环境依赖
- 🔧 **易编译**: CMake构建系统

---

## ✨ 功能特性

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

---

## 🛠️ 环境要求

- C++11兼容编译器 (GCC, Clang, MSVC等)
- CMake 3.10+
- OpenCV 4.x

---

## 📦 安装依赖

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

---

## 🔨 编译项目

### 快速编译（推荐）

**Windows:**
```bash
build_cpp.bat
```

**Linux/Mac:**
```bash
chmod +x build_cpp.sh
./build_cpp.sh
```

### 手动编译

```bash
cd src/CPP
mkdir build
cd build

# 配置
cmake ..

# 编译
make  # Linux/Mac
# 或 Windows: cmake --build . --config Release
```

**编译输出:**
- Windows: `build/bin/Release/vision_system.exe`
- Linux/Mac: `build/bin/vision_system`

---

## 🎮 运行程序

### 方式一：命令行指定图片

```bash
# Windows
src\CPP\build\bin\Release\vision_system.exe path\to\image.jpg

# Linux/Mac
src/CPP/build/bin/vision_system path/to/image.jpg
```

### 方式二：交互式输入

```bash
./vision_system
# 然后根据提示输入图片路径
```

---

## ⌨️ 快捷键说明

### 图像处理算法

| 按键 | 功能 | 说明 |
|------|------|------|
| `1` | 原图 | 恢复原始图像 |
| `2` | 灰度化 | 彩色转黑白 |
| `3` | 高斯模糊 | 平滑去噪 |
| `4` | 中值滤波 | 去除椒盐噪声 |
| `5` | Canny边缘 | 边缘检测 |
| `6` | 二值化 | 固定阈值分割 |
| `7` | 自适应二值化 | 局部阈值分割 |
| `8` | Sobel | 梯度边缘检测 |
| `9` | Laplacian | 二阶导数边缘检测 |
| `0` | 膨胀 | 形态学扩张 |
| `-` | 腐蚀 | 形态学收缩 |
| `=` | 直方图均衡化 | 对比度增强 |

### ROI操作

| 按键 | 功能 | 说明 |
|------|------|------|
| `r` | 开始ROI选择 | 进入选择模式 |
| `c` | 裁剪ROI | 裁剪选中区域 |

### 其他功能

| 按键 | 功能 | 说明 |
|------|------|------|
| `s` | 保存图片 | 保存当前图像 |
| `h` | 显示帮助 | 查看快捷键 |
| `ESC` | 退出 | 关闭程序 |

---

## 🖱️ ROI操作指南

### 选择ROI区域

1. 按 `r` 键进入ROI选择模式
2. 在图像窗口按住鼠标左键
3. 拖动鼠标绘制矩形框
4. 松开鼠标完成选择
5. 红色矩形框显示选中区域

### 裁剪ROI

1. 选择ROI后，按 `c` 键裁剪
2. 图像将更新为裁剪后的区域
3. 可以继续进行其他处理

### 重新选择

- 按 `r` 键可重新选择ROI
- 之前的选择会被清除

---

## 💾 保存图片

### 保存步骤

1. 按 `s` 键
2. 输入保存路径（或直接回车使用默认 `output.png`）
3. 支持的格式：PNG, JPG, BMP, TIFF

### 示例

```
输入保存路径 (默认: output.png): result.jpg
图片保存成功: result.jpg
```

---

## 📊 代码结构

```
CPP/
├── main.cpp                 # 程序入口
├── vision_system.h          # VisionSystem类声明
├── vision_system.cpp        # VisionSystem类实现
├── CMakeLists.txt           # CMake配置文件
└── README.md                # 本文档
```

### 主要类：VisionSystem

**成员变量：**
- `originalImage`: 原始图像
- `processedImage`: 处理后图像
- `roiRect`: ROI矩形区域
- `selectingROI`: ROI选择状态

**主要方法：**
```cpp
// 文件操作
bool loadImage(const std::string& filename);
bool saveImage(const std::string& filename);

// 图像处理
void applyGrayscale();
void applyGaussianBlur();
void applyCanny();
// ... 其他算法

// ROI操作
void startROISelection();
void cropROI();
void cancelROI();

// 显示
void showImage(const std::string& title);
void run();  // 主循环
```

---

## 🐛 常见问题

### Q: CMake找不到OpenCV?

**Windows:**
```bash
cmake -DOpenCV_DIR=C:/path/to/opencv/build ..
```

**Linux:**
```bash
sudo apt-get install pkg-config
cmake .. `pkg-config --cflags --libs opencv4`
```

### Q: 编译时找不到头文件?

确保已正确安装OpenCV开发包：
```bash
# Ubuntu/Debian
sudo apt-get install libopencv-dev

# CentOS/RHEL
sudo yum install opencv-devel
```

### Q: 运行时找不到动态库?

**Linux:**
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
```

或在 `/etc/ld.so.conf.d/opencv.conf` 中添加：
```
/usr/local/lib
```

然后执行：
```bash
sudo ldconfig
```

**Windows:**
将OpenCV的bin目录添加到PATH环境变量。

### Q: 如何修改默认参数?

编辑 `vision_system.cpp` 中的算法实现方法，例如修改Canny阈值：

```cpp
void VisionSystem::applyCanny() {
    // 修改这里的50和150
    cv::Canny(gray, edges, 50, 150);
}
```

---

## 💡 扩展示例

### 添加新算法：双边滤波

**步骤1：** 在 `vision_system.h` 中声明

```cpp
void applyBilateralFilter();
```

**步骤2：** 在 `vision_system.cpp` 中实现

```cpp
void VisionSystem::applyBilateralFilter() {
    if (originalImage.empty()) return;
    
    cv::bilateralFilter(originalImage, processedImage, 9, 75, 75);
    updateDisplay();
    std::cout << "已应用: 双边滤波" << std::endl;
}
```

**步骤3：** 在 `run()` 方法的switch中添加

```cpp
case 'b':
    applyBilateralFilter();
    break;
```

**步骤4：** 更新帮助信息

```cpp
std::cout << "  b - 双边滤波" << std::endl;
```

---

## 📝 更新历史

### v1.0 - 初始版本 (2026-04-22)

**功能特性：**
- 🎉 C++和OpenCV实现
- 🖼️ 12种图像处理算法
- 🖱️ 鼠标ROI选择和裁剪
- ⌨️ 完整的键盘快捷键
- 💾 图片保存功能

**技术特点：**
- 基于OpenCV HighGUI
- CMake构建系统
- 跨平台支持
- 高性能处理

---

## 🔗 相关文档

- 📘 [主项目文档](../../README.md) - 项目总览和双语言对比
- 📗 [Python版本文档](../python/README.md) - Python模块化架构
- 📝 [贡献指南](../../CONTRIBUTING.md) - 如何参与开发

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request！详见 [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**享受高性能图像处理的乐趣！** ⚡📷✨
