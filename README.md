# OpenCV视觉系统

一个基于OpenCV的多语言图像处理系统,提供 **C++** 和 **Python** 两种实现版本。

## 🎯 项目简介

本项目是一个功能完整的图像处理与视觉分析系统,支持多种常见的图像处理算法,提供友好的的用户界面和鼠标交互功能。完全离线运行,无需网络依赖。

## ✨ 主要特性

### 📸 图像支持
- ✅ 支持常见图片格式: JPG, PNG, BMP, TIFF, WEBP
- ✅ 实时图像预览
- ✅ 图像保存功能

### 🎨 图像处理算法
- **基础处理**: 灰度化、高斯模糊、中值滤波
- **边缘检测**: Canny、Sobel、Laplacian
- **二值化**: 固定阈值、自适应阈值
- **形态学**: 膨胀、腐蚀
- **增强**: 直方图均衡化

### 🖱️ 交互功能
- ✅ 鼠标选择ROI(感兴趣区域)
- ✅ ROI裁剪功能
- ✅ 实时参数调整(Python版)
- ✅ 键盘快捷键(C++版)

### 💻 双语言支持
- **Python版本**: 基于tkinter的图形界面,适合快速开发和原型验证
- **C++版本**: 基于OpenCV HighGUI,性能更优,适合生产环境

### 🔒 完全离线
- 所有处理均在本地完成
- 无需网络连接
- 无需注册或登录

## 📁 项目结构

```
StduyOpenCV/
├── src/
│   ├── python/              # Python版本
│   │   ├── vision_system.py # 主程序
│   │   ├── requirements.txt # Python依赖
│   │   └── README.md        # Python版说明
│   └── CPP/                 # C++版本
│       ├── main.cpp         # 入口文件
│       ├── vision_system.h  # 头文件
│       ├── vision_system.cpp# 实现文件
│       ├── CMakeLists.txt   # CMake配置
│       └── README.md        # C++版说明
└── README.md                # 项目总说明
```

## 🚀 快速开始

### Python版本

#### 1. 安装依赖
```bash
cd src/python
pip install -r requirements.txt
```

#### 2. 运行程序
```bash
python vision_system.py
```

#### 3. 使用说明
- 点击"打开图片"加载图像
- 选择左侧的算法按钮应用滤镜
- 使用ROI工具选择和裁剪区域
- 拖动滑块调整参数
- 点击"保存图片"导出结果

### C++版本

#### 1. 安装OpenCV
- **Windows**: 使用vcpkg或下载安装包
- **Linux**: `sudo apt-get install libopencv-dev`
- **macOS**: `brew install opencv`

#### 2. 编译项目
```bash
cd src/CPP
mkdir build && cd build
cmake ..
make  # 或在Windows上: cmake --build .
```

#### 3. 运行程序
```bash
./bin/vision_system path/to/image.jpg
```

#### 4. 快捷键
- 数字键 1-9, 0, -, = : 应用不同算法
- `r`: 开始ROI选择
- `c`: 裁剪ROI
- `s`: 保存图片
- `ESC`: 退出

## 📋 详细功能说明

### 图像处理算法

| 算法 | 用途 | 适用场景 |
|------|------|----------|
| 灰度化 | 彩色转黑白 | 预处理、特征提取 |
| 高斯模糊 | 平滑去噪 | 降噪、预处理 |
| 中值滤波 | 非线性滤波 | 去除椒盐噪声 |
| Canny边缘检测 | 边缘提取 | 轮廓检测、特征识别 |
| Sobel边缘检测 | 梯度计算 | 边缘强化 |
| Laplacian边缘检测 | 二阶导数 | 细节增强 |
| 二值化 | 图像分割 | OCR、目标分离 |
| 自适应二值化 | 局部阈值 | 光照不均场景 |
| 膨胀 | 形态学扩张 | 填补空洞、连接断裂 |
| 腐蚀 | 形态学收缩 | 去除小物体、细化 |
| 直方图均衡化 | 对比度增强 | 低对比度图像增强 |

### ROI操作

**ROI (Region of Interest)** - 感兴趣区域选择

1. **选择模式**:
   - Python: 点击"选择ROI"按钮
   - C++: 按 `r` 键

2. **绘制矩形**:
   - 在图像上按住鼠标左键并拖动
   - 显示红色矩形框

3. **完成操作**:
   - Python: 点击"裁剪ROI"或"取消选择"
   - C++: 按 `c` 裁剪或 `r` 重新选择

## 🔧 技术栈

### Python版本
- **语言**: Python 3.7+
- **UI框架**: tkinter (内置)
- **图像处理**: OpenCV (opencv-python)
- **图像处理**: Pillow (PIL)
- **数值计算**: NumPy

### C++版本
- **语言**: C++11
- **构建系统**: CMake 3.10+
- **图像处理**: OpenCV 4.x
- **UI**: OpenCV HighGUI模块

## 📖 开发指南

### 添加新算法 (Python)

在 `vision_system.py` 的 `apply_filter` 方法中添加:

```python
elif filter_type == "your_algorithm":
    # 你的算法实现
    result = cv2.your_function(self.original_image)
    self.processed_image = result.copy()
    self.current_filter = "算法名称"
```

### 添加新算法 (C++)

1. 在 `vision_system.h` 中声明方法:
```cpp
void applyYourAlgorithm();
```

2. 在 `vision_system.cpp` 中实现:
```cpp
void VisionSystem::applyYourAlgorithm() {
    // 你的算法实现
}
```

3. 在 `run()` 方法的switch语句中添加快捷键

## 🐛 常见问题

### Python版本
**Q: 提示找不到模块?**  
A: 确保已安装依赖: `pip install -r requirements.txt`

**Q: 界面显示异常?**  
A: 检查Python版本是否>=3.7,timer为最新版本

### C++版本
**Q: CMake找不到OpenCV?**  
A: 确保已正确安装OpenCV,设置OpenCV_DIR环境变量

**Q: 编译错误?**  
A: 检查编译器是否支持C++11标准

## 📝 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📧 联系方式

如有问题或建议,请通过GitHub Issues联系。

---

**享受图像处理的乐趣!** 🎉
