# 节点模块 (Nodes)

## 📋 更新历史

### v1.0 - 初始版本 (2026-04-22)
- ✅ 创建基础节点架构
- ✅ 实现IO节点（图像加载、保存）
- ✅ 实现处理节点（灰度化、高斯模糊、Canny边缘检测、二值化）
- ✅ 实现显示节点（图像信息显示与预览）
- ✅ 修复 `add_slider` API兼容性问题，改用 `add_text_input`
- ✅ 添加图像缓存机制和双击预览功能

---

## 🎯 概况

**节点模块**是图形化视觉编程系统的核心组件，负责封装OpenCV算法为可视化的处理单元。每个节点代表一个独立的图像处理操作，通过输入/输出端口与其他节点连接，形成完整的数据流处理链。

### 设计理念
- **模块化**: 每个算法独立封装，易于扩展和维护
- **可视化**: 通过NodeGraphQt框架提供拖拽式编程体验
- **数据流驱动**: 基于端口的数据传递，自动管理依赖关系
- **参数可调**: 支持运行时动态调整算法参数

---

## 💻 部署环境要求

### 技术栈
- **Python**: 3.7+
- **NodeGraphQt**: >=0.6.30
- **OpenCV**: >=4.5.0
- **NumPy**: >=1.19.0, <2.0.0 (与PySide2兼容)

### 安装依赖
```bash
cd src/python_graph
pip install -r requirements.txt
```

---

## 📦 基本功能

### 模块结构
```
nodes/
├── __init__.py              # 模块导出配置
├── io_nodes.py             # 输入输出节点
├── processing_nodes.py     # 图像处理算法节点
└── display_nodes.py        # 显示节点
```

### 节点分类

#### 1. IO节点 (`io_nodes.py`)
负责图像的输入输出操作。

**ImageLoadNode** - 图像加载节点
- **标识符**: `io`
- **功能**: 从文件路径加载图像
- **输入**: 无
- **输出**: 图像数据 (numpy.ndarray)
- **属性**:
  - `file_path`: 图像文件路径
- **使用方法**:
  1. **双击节点（推荐）✨**: 
     - 双击"图像加载"节点
     - 弹出文件选择对话框
     - 选择图像文件后自动填充路径
  2. **直接输入**: 在"文件路径"文本框中直接输入完整路径
  3. **复制粘贴**: 
     - 在文件资源管理器中右键文件 → "复制为路径"
     - 双击节点的"文件路径"文本框，Ctrl+V 粘贴
- **使用示例**:
  ```python
  # 方式1: 双击节点选择文件（推荐）
  # 双击节点 → 选择 D:/images/test.jpg → 自动填充
  
  # 方式2: 直接输入路径
  file_path = "D:/images/test.jpg"        # 推荐：使用正斜杠
  file_path = "D:\\images\\test.jpg"      # 或使用双反斜杠
  
  # Linux/Mac路径示例
  file_path = "/home/user/images/test.jpg"
  ```

**💡 快速输入路径的技巧**:
1. **Windows**: 在文件资源管理器中按住 Shift + 右键文件 → 选择"复制为路径"
2. **粘贴到节点**: 双击"文件路径"文本框，按 Ctrl+V 粘贴
3. **双击节点**: 直接双击节点打开文件选择对话框（最方便）

**ImageSaveNode** - 图像保存节点
- **标识符**: `io`
- **功能**: 将图像保存到指定路径
- **输入**: 图像数据
- **输出**: 状态文本
- **属性**:
  - `save_path`: 保存文件路径（需包含文件名和扩展名）
  - `status`: 保存状态信息
- **使用方法**:
  1. **双击节点（推荐）✨**: 
     - 双击"图像保存"节点
     - 弹出文件保存对话框
     - 选择保存位置和文件名后自动填充路径
  2. **直接输入**: 在"保存路径"文本框中输入完整路径
  3. **支持的格式**: .png, .jpg, .bmp, .tiff, .webp
- **使用示例**:
  ```python
  # 方式1: 双击节点选择保存路径（推荐）
  # 双击节点 → 选择 D:/output/result.png → 自动填充
  
  # 方式2: 直接输入路径
  save_path = "D:/output/result.png"      # 保存为PNG
  save_path = "D:/output/result.jpg"      # 保存为JPG
  ```

**⚠️ API限制说明**:
根据 NodeGraphQt 框架的设计，**不支持在节点上添加自定义右键菜单项或按钮控件**。这是框架的API限制，而非实现缺陷。

**替代方案**:
- ✅ 使用文本输入框直接输入路径（当前方案）
- ✅ 利用操作系统的"复制为路径"功能快速输入
- ❌ 不使用 `add_button()` + `clicked.connect()` （NodeButton不支持标准Qt信号）
- ❌ 不使用 `build_menu()` （BaseNode不支持此方法）

#### 2. 处理节点 (`processing_nodes.py`)
封装OpenCV图像处理算法。

**GrayscaleNode** - 灰度化节点
- **标识符**: `processing`
- **算法**: `cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`
- **输入**: BGR图像
- **输出**: 灰度图像

**GaussianBlurNode** - 高斯模糊节点
- **标识符**: `processing`
- **算法**: `cv2.GaussianBlur()`
- **输入**: 图像数据
- **输出**: 模糊后的图像
- **参数**:
  - `kernel_size`: 核大小（奇数，如3, 5, 7）

**CannyEdgeNode** - Canny边缘检测节点
- **标识符**: `processing`
- **算法**: `cv2.Canny()`
- **输入**: 图像数据
- **输出**: 边缘检测结果
- **参数**:
  - `threshold1`: 低阈值
  - `threshold2`: 高阈值

**ThresholdNode** - 二值化节点
- **标识符**: `processing`
- **算法**: `cv2.threshold()`
- **输入**: 图像数据
- **输出**: 二值化图像
- **参数**:
  - `threshold`: 阈值 (0-255)
  - `type`: 二值化类型 (BINARY, BINARY_INV, TRUNC等)

#### 3. 显示节点 (`display_nodes.py`)
提供图像信息展示和预览功能。

**ImageViewNode** - 图像显示节点
- **标识符**: `display`
- **功能**: 
  - 显示图像尺寸、通道数、数据类型等信息
  - 缓存最后一张处理的图像
  - 双击节点可打开完整预览窗口（**非模态**）
- **输入**: 图像数据
- **输出**: 状态文本
- **特性**:
  - 图像缓存机制 (`_cached_image`)
  - 双击弹出 [ImagePreviewDialog](file://d:\example\projects\StduyOpenCV\src\python\ui\main_window.py#L22-L135)（非模态窗口）
  - 支持保存预览图像
  - **✨ 支持手动刷新预览**：点击"🔄 刷新预览"按钮
  - **✨ 自动刷新**：运行节点图后自动更新所有打开的预览窗口
  - **✨ 多窗口支持**：可以同时打开多个节点的预览窗口
- **使用方法**:
  1. 双击节点打开预览窗口（非模态，可同时打开多个）
  2. 修改处理节点参数后，点击工具栏"▶ 运行"
  3. 预览窗口自动更新，或手动点击"🔄 刷新预览"按钮

### 节点开发规范

#### 创建新节点
``python
from NodeGraphQt import BaseNode
import cv2

class YourCustomNode(BaseNode):
    """
    自定义节点文档字符串
    """
    
    __identifier__ = 'category'  # 节点分类标识
    NODE_NAME = '节点名称'
    
    def __init__(self):
        super(YourCustomNode, self).__init__()
        
        # 添加输入端口
        self.add_input('输入名称', color=(R, G, B))
        
        # 添加输出端口
        self.add_output('输出名称', color=(R, G, B))
        
        # 添加属性控件（使用支持的API）
        self.add_text_input('param_name', '参数标签', tab='properties')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表
            
        Returns:
            dict: 输出数据字典，键为输出端口名称
        """
        if inputs and len(inputs) > 0:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            try:
                # 获取参数
                param = int(self.get_property('param_name'))
                
                # 执行算法
                result = cv2.your_algorithm(image, param)
                
                return {'输出名称': result}
            except Exception as e:
                print(f"处理错误: {e}")
                return {'输出名称': None}
        
        return {'输出名称': None}
```

#### 注册节点
在 [ui/main_window.py](file://d:\example\projects\StduyOpenCV\src\python_graph\ui\main_window.py) 的 `_register_nodes()` 方法中：
```
from nodes.your_module import YourCustomNode

def _register_nodes(self):
    # ... 现有节点
    self.node_graph.register_node(YourCustomNode)
```

---

## ⚠️ API限制与注意事项

### NodeGraphQt API陷阱
根据项目经验总结，以下API**不支持**：

1. ❌ **`add_slider()`** - 不存在此方法
   - ✅ 替代方案: 使用 `add_text_input()` 并添加数值验证

2. ❌ **`NodeButton.clicked` 信号** - 自定义按钮不支持标准Qt信号
   - ✅ 替代方案: 让用户直接在文本框中输入路径或参数

3. ❌ **直接访问 `_properties`** - 私有属性不应直接操作
   - ✅ 正确方式: 使用 `get_property()` 和 `set_property()`

4. ❌ **节点本体显示图像缩略图** - BaseNode不支持动态嵌入图像
   - ✅ 替代方案: 双击节点弹出独立预览对话框

---

## 🚀 优化及改进计划

### 短期目标 (v1.x)
- [ ] 添加更多形态学操作节点（膨胀、腐蚀、开闭运算）
- [ ] 实现直方图均衡化节点
- [ ] 添加色彩空间转换节点（HSV、LAB等）
- [ ] 优化参数输入验证（范围检查、类型转换）

### 中期目标 (v2.x)
- [ ] 支持视频流输入节点
- [ ] 添加ROI裁剪节点
- [ ] 实现特征检测节点（角点、轮廓等）
- [ ] 节点参数预设功能（常用配置快速加载）

### 长期目标 (v3.x)
- [ ] GPU加速节点（CUDA支持）
- [ ] AI模型集成节点（YOLO、OCR等）
- [ ] 节点分组与子图功能
- [ ] 实时预览模式（边修改边查看效果）

---

## 📚 相关文档

- 📘 [项目总览](../../README.md) - 整体项目介绍
- 📗 [核心引擎模块](../core/README.md) - 图执行引擎说明
- 📕 [用户界面模块](../ui/README.md) - UI组件文档
- 🔗 [NodeGraphQt官方文档](https://github.com/jchanvfx/NodeGraphQt)

---

## 🤝 贡献指南

欢迎提交新的节点实现！请遵循以下规范：
1. 继承 `BaseNode` 类
2. 实现 `process()` 方法
3. 添加完整的文档字符串
4. 在 `__init__.py` 中导出节点
5. 更新本README的节点列表
