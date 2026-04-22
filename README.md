# OpenCV视觉系统

一个基于OpenCV的多语言图像处理系统,提供 **C++** 和 **Python** 两种实现版本。

## 📋 文档导航

- 📘 **本文档**: 项目总览、快速开始、功能说明
- 📗 [安装指南](#-安装指南): 详细的安装步骤
- 📙 [Python版本详解](src/python/README.md): Python模块化架构和使用说明
- 📕 [C++版本详解](src/CPP/README.md): C++版本编译和使用说明
- 📝 [贡献指南](CONTRIBUTING.md): 如何参与项目开发

---

## 🎯 项目简介

本项目是一个功能完整的图像处理与视觉分析系统,支持多种常见的图像处理算法,提供友好的用户界面和鼠标交互功能。**完全离线运行**,无需网络依赖,保护数据隐私。

### 核心特点

- ✅ **双语言实现**: Python（易上手）+ C++（高性能）
- ✅ **12种算法**: 覆盖基础处理、边缘检测、形态学等
- ✅ **交互式ROI**: 鼠标选择、裁剪感兴趣区域
- ✅ **完全离线**: 无需网络,本地化处理
- ✅ **模块化设计**: Python版本采用MVC架构,易于扩展

---

## ✨ 主要特性

### 📸 图像支持
- 常见格式: JPG, PNG, BMP, TIFF, WEBP
- 实时预览和处理
- 多格式保存

### 🎨 图像处理算法

| 类别 | 算法 | 应用场景 |
|------|------|----------|
| **基础处理** | 灰度化、高斯模糊、中值滤波 | 预处理、降噪 |
| **边缘检测** | Canny、Sobel、Laplacian | 轮廓提取、特征识别 |
| **二值化** | 固定阈值、自适应阈值 | OCR、目标分割 |
| **形态学** | 膨胀、腐蚀 | 填补空洞、去除噪声 |
| **增强** | 直方图均衡化 | 对比度提升 |

### 🖱️ 交互功能
- 鼠标选择ROI区域
- ROI实时裁剪
- 参数动态调整(Python版)
- 键盘快捷键(C++版)

### 💻 多版本对比

| 特性 | Python传统版 | Python图形化版 | C++版本 |
|------|-------------|---------------|---------|
| **UI框架** | tkinter | NodeGraphQt+PySide2 | OpenCV HighGUI |
| **编程方式** | 按钮点击 | 拖拽节点连线 | 键盘快捷键 |
| **架构模式** | MVC模块化 | 节点图引擎 | 单体式 |
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **性能** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **适用场景** | 学习/原型 | 工作流设计 | 生产环境 |
| **类似产品** | - | 海康VM/基恩士CV-X | - |

---

## 🚀 快速开始

### 方式一：Python图形化版本（🌟 推荐）

**✨ 类似海康、基恩士、康耐视的可视化编程体验！**

#### 1. 安装依赖
```bash
cd src/python_graph
pip install -r requirements.txt
```

#### 2. 运行程序
```bash
python main.py
```

#### 3. 使用说明
- 从左侧节点库拖拽节点到画布
- 连接节点的输入输出端口
- 双击节点调整参数
- 点击"▶ 运行"执行流程
- 保存/加载工作流（JSON格式）

**详细说明**: [Python图形化版本文档](src/python_graph/README.md)

---

### 方式二：Python传统版本

#### 1. 安装依赖
```bash
cd src/python
pip install -r requirements.txt
```

#### 2. 运行程序
```bash
python vision_system.py
```

#### 3. 测试模块（可选）
```bash
python test_modules.py  # 验证模块化架构
```

**详细说明**: [Python版本文档](src/python/README.md)

---

### 方式三：C++版本（高性能）

#### 1. 安装OpenCV
- **Windows**: 使用vcpkg或官方安装包
- **Linux**: `sudo apt-get install libopencv-dev`
- **macOS**: `brew install opencv`

#### 2. 编译项目
```bash
cd src/CPP
mkdir build && cd build
cmake ..
make  # Windows: cmake --build .
```

#### 3. 运行程序
```bash
./bin/vision_system <图片路径>
```

**详细说明**: [C++版本文档](src/CPP/README.md)

---

## 📁 项目结构

```
StduyOpenCV/
├── README.md                    # 本文档 - 项目总览
├── CONTRIBUTING.md              # 贡献指南
├── DOCUMENTATION_REORGANIZATION.md  # 文档整理说明
├── .gitignore                   # Git忽略配置
├── run_python.bat/sh            # Python启动脚本
├── build_cpp.bat/sh             # C++编译脚本
│
├── src/
│   ├── python_graph/            # 🌟 Python图形化版本（NEW!）
│   │   ├── main.py              # 程序入口
│   │   ├── requirements.txt     # 依赖清单
│   │   ├── README.md            # 📘 图形化版本详细说明
│   │   ├── nodes/               # 节点定义
│   │   │   ├── io_nodes.py      # IO节点
│   │   │   ├── processing_nodes.py  # 处理节点
│   │   │   └── display_nodes.py # 显示节点
│   │   ├── core/                # 核心引擎
│   │   │   ├── graph_engine.py  # 图执行引擎
│   │   │   └── node_registry.py # 节点注册表
│   │   └── ui/                  # 用户界面
│   │       └── main_window.py   # 主窗口
│   │
│   ├── python/                  # Python传统版本（模块化MVC架构）
│   │   ├── vision_system.py     # 主程序入口
│   │   ├── controller.py        # 应用控制器
│   │   ├── requirements.txt     # 依赖清单
│   │   ├── test_modules.py      # 模块测试
│   │   ├── create_test_image.py # 测试图片生成
│   │   ├── README.md            # 📗 Python传统版详细说明
│   │   ├── core/                # 核心算法模块
│   │   │   ├── __init__.py
│   │   │   └── image_processor.py
│   │   └── UI/                  # 用户界面模块
│   │       ├── __init__.py
│   │       └── main_window.py
│   │
│   └── CPP/                     # C++版本
│       ├── main.cpp             # 程序入口
│       ├── vision_system.h      # 头文件
│       ├── vision_system.cpp    # 实现文件
│       ├── CMakeLists.txt       # CMake配置
│       └── README.md            # 📕 C++版详细说明
```

---

## 📖 安装指南

### Python版本安装

#### Windows
```bash
# 方式1: 使用启动脚本（自动安装依赖）
run_python.bat

# 方式2: 手动安装
cd src\python
pip install -r requirements.txt
python vision_system.py
```

#### Linux/Mac
```bash
# 方式1: 使用启动脚本
chmod +x run_python.sh
./run_python.sh

# 方式2: 手动安装
cd src/python
pip3 install -r requirements.txt
python3 vision_system.py
```

### C++版本安装

#### Windows (使用vcpkg)
```powershell
# 安装vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装OpenCV
.\vcpkg install opencv:x64-windows
.\vcpkg integrate install

# 编译项目
cd path\to\StduyOpenCV\src\CPP
build_cpp.bat
```

#### Linux (Ubuntu/Debian)
```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y libopencv-dev cmake build-essential

# 编译项目
cd src/CPP
chmod +x build_cpp.sh
./build_cpp.sh
```

#### macOS
```bash
# 安装Homebrew和依赖
brew install opencv cmake

# 编译项目
cd src/CPP
chmod +x build_cpp.sh
./build_cpp.sh
```

**更多安装问题**: 查看各版本的README文档

---

## 🎮 使用说明

### Python版本操作

1. **打开图片**: 点击"打开图片"按钮
2. **应用算法**: 点击左侧算法按钮
3. **调整参数**: 拖动滑块实时调整
4. **ROI操作**: 
   - 点击"选择ROI"
   - 在图像上拖动鼠标
   - 点击"裁剪ROI"或"取消选择"
5. **保存结果**: 点击"保存图片"

### C++版本快捷键

| 按键 | 功能 | 按键 | 功能 |
|------|------|------|------|
| 1 | 原图 | 6 | 二值化 |
| 2 | 灰度化 | 7 | 自适应二值化 |
| 3 | 高斯模糊 | 8 | Sobel检测 |
| 4 | 中值滤波 | 9 | Laplacian检测 |
| 5 | Canny边缘 | 0 | 膨胀 |
| - | 腐蚀 | = | 直方图均衡化 |
| r | ROI选择 | c | 裁剪ROI |
| s | 保存图片 | ESC | 退出 |

---

## 🔧 技术栈

### Python版本
- **语言**: Python 3.7+
- **UI框架**: tkinter (内置)
- **图像处理**: OpenCV 4.5+, Pillow 8.0+
- **数值计算**: NumPy
- **架构模式**: MVC (Model-View-Controller)

### C++版本
- **语言**: C++11
- **构建系统**: CMake 3.10+
- **图像处理**: OpenCV 4.x
- **UI**: OpenCV HighGUI模块

---

## 💡 扩展示例

### Python版本添加新算法

```python
# 1. 在 core/image_processor.py 中添加
def apply_your_algorithm(self, image):
    """你的算法"""
    return result

# 2. 在 ALGORITHM_MAP 中注册
ALGORITHM_MAP = {
    "your_algo": lambda img, proc: proc.apply_your_algorithm(img),
}

# 3. 在 UI/main_window.py 中添加按钮
("你的算法", lambda: self.controller.apply_filter("your_algo")),
```

### C++版本添加新算法

```cpp
// 1. 在 vision_system.h 中声明
void applyYourAlgorithm();

// 2. 在 vision_system.cpp 中实现
void VisionSystem::applyYourAlgorithm() {
    // 实现逻辑
}

// 3. 在 run() 的switch中添加快捷键
case 'x': applyYourAlgorithm(); break;
```

---

## 🐛 常见问题

### Python版本

**Q: 提示找不到模块?**
```bash
pip install --upgrade opencv-python Pillow numpy
```

**Q: 界面无法显示?**
- 检查Python版本 >= 3.7
- 确保tkinter已安装

### C++版本

**Q: CMake找不到OpenCV?**
- 设置OpenCV_DIR环境变量
- 或使用pkg-config (Linux)

**Q: 运行时找不到库?**
- Linux: `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib`
- Windows: 将OpenCV bin目录加入PATH

---

## 📊 项目统计

- **代码量**: ~1550行 (Python ~630行 + C++ ~450行 + 其他)
- **文件数**: 25+ 个
- **支持平台**: Windows, Linux, macOS
- **支持语言**: Python, C++
- **算法数量**: 12种
- **许可证**: 学习和研究使用

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request! 详见 [CONTRIBUTING.md](CONTRIBUTING.md)

### 可以改进的方向
- 添加更多算法（特征检测、对象识别等）
- 视频处理支持
- 批量处理功能
- 撤销/重做功能
- 更美观的UI主题

---

## 📝 更新历史

### v2.0 (2026-04-22)
- ✨ Python版本重构为模块化MVC架构
- 📦 分离core算法模块和UI界面模块
- 🧪 添加模块测试脚本
- 📚 完善文档体系

### v1.0 (初始版本)
- 🎉 Python和C++双语言实现
- 🖼️ 12种图像处理算法
- 🖱️ ROI选择和裁剪功能
- 📱 图形界面支持

---

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**享受图像处理的乐趣!** 🎨📷✨
