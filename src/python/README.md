# OpenCV视觉系统 - Python版本

基于tkinter和OpenCV的模块化图像处理系统，采用MVC架构设计。

## 📋 文档导航

- 📘 **本文档**: 完整的使用说明、架构详解、扩展指南
- 🔙 [返回主项目文档](../../README.md)

---

## 🎯 版本特色

### ✨ 模块化MVC架构

```
┌─────────────────────────────────┐
│     View (UI/main_window.py)    │  ← 用户界面层
└──────────────┬──────────────────┘
               │ 调用
┌──────────────▼──────────────────┐
│ Controller (controller.py)      │  ← 控制层
└──────┬───────────────┬──────────┘
       │ 调用          │ 调用
┌──────▼──────┐  ┌────▼──────────┐
│ Model       │  │ 外部服务      │
│ (core/)     │  │  - cv2        │
└─────────────┘  └───────────────┘
```

**优势：**
- ✅ 职责清晰，易于维护
- ✅ 模块独立，便于测试
- ✅ 高内聚低耦合
- ✅ 易于扩展新功能

---

## 📁 项目结构

```
python/
├── vision_system.py          # 主程序入口 (~60行)
├── controller.py             # 应用控制器 (~200行)
├── requirements.txt          # Python依赖
├── create_test_image.py      # 测试图片生成
├── test_modules.py           # 模块测试脚本
├── README.md                 # 本文档
│
├── core/                     # 核心算法模块 (Model)
│   ├── __init__.py           # 模块导出
│   └── image_processor.py    # 图像处理算法 (~150行)
│
└── UI/                       # 用户界面模块 (View)
    ├── __init__.py           # 模块导出
    └── main_window.py        # 主窗口UI (~220行)
```

---

## 🏗️ 架构详解

### 1. core/ - 核心算法模块（Model）

**职责：** 封装所有OpenCV图像处理算法

**主要组件：**

#### ImageProcessor 类
```python
from core import ImageProcessor

processor = ImageProcessor()

# 设置参数
processor.set_canny_params(50, 150)
processor.set_threshold_param(127)

# 应用算法
result = processor.apply_grayscale(image)
result = processor.apply_canny(image)
result = processor.apply_gaussian_blur(image)
```

**支持的算法：**
- 灰度化 (`apply_grayscale`)
- 高斯模糊 (`apply_gaussian_blur`)
- 中值滤波 (`apply_median_blur`)
- Canny边缘检测 (`apply_canny`)
- 固定阈值二值化 (`apply_threshold`)
- 自适应二值化 (`apply_adaptive_threshold`)
- Sobel边缘检测 (`apply_sobel`)
- Laplacian边缘检测 (`apply_laplacian`)
- 形态学膨胀 (`apply_dilate`)
- 形态学腐蚀 (`apply_erode`)
- 直方图均衡化 (`apply_equalize_hist`)
- ROI裁剪 (`crop_roi`)

#### 统一接口
```python
from core import apply_filter

# 统一的滤镜调用方式
result = apply_filter("canny", image, processor)
result = apply_filter("gaussian", image, processor)
```

**特点：**
- ✅ 无UI依赖，可独立使用
- ✅ 可在其他项目中复用
- ✅ 易于单元测试
- ✅ 支持动态参数调整

---

### 2. UI/ - 用户界面模块（View）

**职责：** 创建和管理图形界面

#### MainWindow 类
```python
from UI import MainWindow
import tkinter as tk

root = tk.Tk()
window = MainWindow(root, controller)
```

**主要功能：**
- 创建tkinter界面（按钮、滑块、Canvas等）
- 显示和处理图像
- 捕获鼠标事件
- 提供文件对话框
- 显示状态信息

**核心方法：**
```python
# 显示图像
window.update_display(image)

# 绘制ROI矩形
window.draw_roi_rectangle(start_point, end_point)

# 状态管理
window.set_status("消息文本")
window.show_error("标题", "内容")
window.show_warning("标题", "内容")

# 文件操作
path = window.ask_open_file(title="...", filetypes=[...])
path = window.ask_save_file(title="...", defaultextension=".png")

# 获取参数
params = window.get_param_values()
# 返回: {'canny_low': 50, 'canny_high': 150, 'threshold_value': 127}
```

**特点：**
- ✅ 专注UI显示，不含业务逻辑
- ✅ 可替换为其他UI框架（PyQt、wxPython等）
- ✅ 易于定制界面样式
- ✅ 事件转发给Controller处理

---

### 3. controller.py - 应用控制器（Controller）

**职责：** 协调Model和View，处理业务逻辑

#### ApplicationController 类
```python
from controller import ApplicationController
from core import ImageProcessor
from UI import MainWindow

processor = ImageProcessor()
window = MainWindow(root, None)  # 先创建
controller = ApplicationController(processor, window)
window.controller = controller  # 再绑定
```

**主要功能：**
- 处理用户操作（打开/保存图片、应用滤镜）
- 管理应用状态（当前图像、ROI等）
- 协调数据流（UI → Algorithm → UI）
- 异常处理和错误提示

**核心方法：**
```python
# 文件操作
controller.open_image()
controller.save_image()

# 应用滤镜
controller.apply_filter("canny")
controller.apply_filter("gaussian")

# 参数更新
controller.update_params()

# ROI操作
controller.start_roi_selection()
controller.crop_roi()
controller.cancel_roi()

# 鼠标事件（由UI转发）
controller.on_mouse_press(event)
controller.on_mouse_drag(event)
controller.on_mouse_release(event)
```

**工作流程示例：**

**打开图片流程：**
```
用户点击"打开图片"
    ↓
MainWindow: 显示文件对话框
    ↓
ApplicationController: 读取路径
    ↓
cv2.imread(): 加载图片
    ↓
ApplicationController: 保存图像
    ↓
MainWindow: 显示图像 + 更新状态栏
```

**应用滤镜流程：**
```
用户点击滤镜按钮
    ↓
ApplicationController: 获取参数
    ↓
ImageProcessor: 设置参数
    ↓
ImageProcessor: 执行算法
    ↓
ApplicationController: 保存结果
    ↓
MainWindow: 更新显示 + 更新状态
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖清单：**
- `opencv-python>=4.5.0`: 图像处理
- `Pillow>=8.0.0`: 图像显示
- `numpy>=1.19.0`: 数值计算

### 2. 运行程序

```bash
python vision_system.py
```

### 3. 测试模块（可选）

```bash
python test_modules.py
```

**测试内容：**
- ✅ core模块导入和功能
- ✅ UI模块导入和功能
- ✅ controller模块导入和功能
- ✅ 主程序结构完整性

---

## 🎮 使用说明

### 基本操作流程

1. **打开图片**
   - 点击"打开图片"按钮
   - 选择图片文件（JPG/PNG/BMP/TIFF/WEBP）
   - 图像自动显示在右侧

2. **应用算法**
   - 在左侧控制面板选择算法
   - 实时预览处理效果
   - 可随时切换不同算法

3. **调整参数**
   - 拖动"Canny低阈值"滑块
   - 拖动"Canny高阈值"滑块
   - 拖动"二值化阈值"滑块
   - 参数实时生效（针对当前算法）

4. **ROI操作**
   - 点击"选择ROI"进入选择模式
   - 在图像上按住鼠标拖动选择区域
   - 红色矩形框显示选择范围
   - 点击"裁剪ROI"进行裁剪
   - 或点击"取消选择"放弃操作

5. **保存结果**
   - 点击"保存图片"按钮
   - 选择保存路径和格式
   - 支持PNG/JPG/BMP/TIFF

### 界面布局

```
┌─────────────────────────────────────────────────┐
│              OpenCV视觉系统 - Python版            │
├──────────────────┬──────────────────────────────┤
│  控制面板         │      图像显示区域             │
│                  │                              │
│ ┌─文件操作─┐     │                              │
│ │打开图片  │     │                              │
│ │保存图片  │     │      [Canvas显示图像]         │
│ └──────────┘     │                              │
│                  │                              │
│ ┌─算法选择─┐     │                              │
│ │原图      │     │                              │
│ │灰度化    │     │                              │
│ │高斯模糊  │     │                              │
│ │Canny边缘 │     │                              │
│ │...       │     │                              │
│ └──────────┘     │                              │
│                  │                              │
│ ┌─ROI操作──┐     │                              │
│ │选择ROI   │     │                              │
│ │裁剪ROI   │     │                              │
│ │取消选择  │     │                              │
│ └──────────┘     │                              │
│                  │                              │
│ ┌─参数调整─┐     │                              │
│ │Canny低值 │====│                              │
│ │Canny高值 │====│                              │
│ │二值化阈值│====│                              │
│ └──────────┘     │                              │
├──────────────────┴──────────────────────────────┤
│ 状态栏: 已加载: test.png | 尺寸: 800x600         │
└─────────────────────────────────────────────────┘
```

---

## 💡 扩展示例

### 添加新算法：直方图均衡化（彩色）

**步骤1：** 在 `core/image_processor.py` 中添加方法

```python
def apply_color_equalize(self, image):
    """彩色直方图均衡化"""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
```

**步骤2：** 在 `ALGORITHM_MAP` 中注册

```python
ALGORITHM_MAP = {
    # ... 现有算法
    "color_equalize": lambda img, proc: proc.apply_color_equalize(img),
}
```

**步骤3：** 在 `UI/main_window.py` 中添加按钮

```python
algorithms = [
    # ... 现有算法
    ("彩色直方图均衡化", lambda: self.controller.apply_filter("color_equalize")),
]
```

**完成！** 无需修改其他代码。

---

### 更换UI框架：从tkinter到PyQt5

**步骤1：** 创建 `UI/pyqt_window.py`

```python
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
import cv2

class PyQtMainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加按钮
        btn = QPushButton("打开图片")
        btn.clicked.connect(self.controller.open_image)
        layout.addWidget(btn)
        
        # 添加图像标签
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
    
    def update_display(self, image):
        """显示图像"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))
```

**步骤2：** 修改 `vision_system.py`

```python
# 原来
from UI import MainWindow

# 改为
from UI.pyqt_window import PyQtMainWindow

class OpenCVVisionSystem:
    def __init__(self):
        self.processor = ImageProcessor()
        self.window = PyQtMainWindow(self)  # 使用新窗口
        self.controller = ApplicationController(self.processor, self.window)
```

**完成！** 核心算法和控制器无需修改。

---

## 🧪 测试与验证

### 运行测试脚本

```bash
python test_modules.py
```

**测试覆盖：**
- ✅ core模块导入和实例化
- ✅ 12种算法注册情况
- ✅ 参数设置功能
- ✅ UI模块窗口创建
- ✅ UI主要方法存在性
- ✅ Controller模块创建
- ✅ Controller主要方法存在性
- ✅ 主程序结构完整性

### 手动测试清单

- [ ] 打开不同格式图片（JPG/PNG/BMP）
- [ ] 应用所有12种算法
- [ ] 调整Canny和二值化参数
- [ ] ROI选择和裁剪
- [ ] 保存图片到不同格式
- [ ] 大图片性能（>5MB）
- [ ] 错误处理（打开非图片文件）

---

## 📊 代码统计

| 模块 | 文件数 | 代码行数 | 职责 |
|------|--------|----------|------|
| core/ | 2 | ~150 | 算法实现 |
| UI/ | 2 | ~220 | 界面显示 |
| controller.py | 1 | ~200 | 业务逻辑 |
| vision_system.py | 1 | ~60 | 程序入口 |
| **总计** | **6** | **~630** | - |

---

## 🎓 学习价值

通过本项目可以学习：

1. **MVC架构模式**
   - Model-View-Controller的职责划分
   - 实际项目中的应用实践

2. **Python模块化设计**
   - 包和模块的组织
   - `__init__.py` 的作用
   - 模块间接口设计

3. **OpenCV图像处理**
   - 12种常用算法
   - 颜色空间转换
   - 图像变换和操作

4. **tkinter GUI编程**
   - 控件创建和布局
   - 事件绑定和处理
   - Canvas图像显示

5. **软件工程实践**
   - 代码组织和重构
   - 文档编写
   - 测试用例设计

---

## 🐛 常见问题

### Q: 提示"No module named 'cv2'"?
```bash
pip install opencv-python
```

### Q: 提示"No module named 'PIL'"?
```bash
pip install Pillow
```

### Q: 界面中文乱码?
tkinter默认支持中文，如仍有问题检查系统字体设置。

### Q: 如何处理超大图片?
程序会自动缩放显示，但处理时使用原图。建议图片<10MB以获得良好性能。

### Q: 如何自定义界面样式?
修改 `UI/main_window.py` 中的 `create_ui()` 方法，调整控件样式和布局。

### Q: 能否批量处理图片?
当前版本不支持，可以扩展controller添加批量处理功能。

---

## 📝 更新历史

### v2.0 - 模块化重构 (2026-04-22)

**重大变更：**
- ✨ 重构为MVC模块化架构
- 📦 分离core算法模块和UI界面模块
- 🎯 添加ApplicationController协调层
- 🧪 新增模块测试脚本
- 📚 完善文档体系

**技术改进：**
- 采用Model-View-Controller设计模式
- 核心算法完全独立，可复用
- UI层可替换（支持tkinter/PyQt等）
- 统一的滤镜接口 `apply_filter()`
- 完善的异常处理机制

**代码质量：**
- 详细的文档注释
- 清晰的模块边界
- 良好的命名规范
- 完整的测试覆盖

**向后兼容：**
- ✅ 用法完全相同：`python vision_system.py`
- ✅ 所有功能保持不变
- ✅ 新增测试和扩展能力

---

### v1.0 - 初始版本 (2026-04-22)

**功能特性：**
- 🎉 Python和OpenCV实现
- 🖼️ 12种图像处理算法
- 🖱️ 鼠标ROI选择和裁剪
- 📱 tkinter图形界面
- 🎚️ 参数实时调整

**初始架构：**
- 单文件实现（~400行）
- 所有功能集中在一个类
- 适合学习和原型开发

---

## 🔗 相关文档

- 📘 [主项目文档](../../README.md) - 项目总览和双语言对比
- 📕 [C++版本文档](../CPP/README.md) - C++版本使用说明
- 📝 [贡献指南](../../CONTRIBUTING.md) - 如何参与开发
- 🏗️ [架构详细说明](MODULE_ARCHITECTURE.md) - MVC架构深度解析
- 🔄 [重构总结](REFACTORING_SUMMARY.md) - 模块化重构过程

> **注意**: MODULE_ARCHITECTURE.md 和 REFACTORING_SUMMARY.md 包含更详细的技术细节，适合深入学习架构设计。

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request！

**可以改进的方向：**
- 添加更多图像处理算法
- 视频处理支持
- 批量处理功能
- 撤销/重做功能
- 更美观的UI主题
- 插件系统设计

详见 [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**享受图像处理的乐趣！** 🎨📷✨
