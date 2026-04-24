# 用户界面模块 (UI)

## 📋 更新历史

### v1.0 - 初始版本 (2026-04-22)
- ✅ 实现主窗口框架 ([MainWindow](file://d:\example\projects\StduyOpenCV\src\python_graph\ui\main_window.py))
- ✅ 集成NodeGraphQt画布组件
- ✅ 实现节点库面板（左侧）
- ✅ 实现属性面板（右侧）
- ✅ 添加工具栏（运行、清空、保存、加载）
- ✅ 添加菜单栏（文件、编辑、帮助）
- ✅ 修复 `tab_widget` 访问问题（属性 vs 方法）
- ✅ 调整节点库标签位置为右侧显示（East）
- ✅ 实现图像预览对话框 ([ImagePreviewDialog](file://d:\example\projects\StduyOpenCV\src\python\ui\image_preview.py))
- ✅ 添加节点双击事件处理（打开图像预览）

### v1.1 - 代码重构 (2026-04-24)
- ✅ 将 ImagePreviewDialog 从 main_window.py 提取到独立的 image_preview.py
- ✅ 优化模块结构，提高代码可维护性
- ✅ 更新 ui/__init__.py 导出配置

---

## 🎯 概况

**用户界面模块**提供图形化视觉编程系统的交互界面，基于 **PySide2 (Qt)** 和 **NodeGraphQt** 框架构建。采用经典的三栏布局：左侧节点库、中间画布、右侧属性面板，类似工业视觉软件（海康VM、基恩士CV-X）的操作体验。

### 设计理念
- **直观易用**: 拖拽式节点编辑，所见即所得
- **模块化布局**: 可停靠的面板，支持自定义工作区
- **实时反馈**: 参数调整后即时查看效果
- **专业外观**: 深色主题，符合工业软件审美

---

## 💻 部署环境要求

### 技术栈
- **Python**: 3.7+
- **PySide2**: >=5.15.0
- **NodeGraphQt**: >=0.6.30
- **OpenCV**: >=4.5.0 (用于图像预览)
- **NumPy**: >=1.19.0, <2.0.0 (与PySide2兼容)

### 安装依赖
```bash
cd src/python_graph
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

---

## 📦 基本功能

### 模块结构
```
ui/
├── __init__.py              # 模块导出配置
├── main_window.py          # 主窗口实现
└── image_preview.py        # 图像预览对话框（独立模块）
```

### 核心类说明

#### 1. MainWindow ([main_window.py](file://d:\example\projects\StduyOpenCV\src\python_graph\ui\main_window.py))

主窗口类，继承自 `QtWidgets.QMainWindow`，整合所有UI组件。

**主要组件**:

##### 节点图画布 (NodeGraph Widget)
- **位置**: 中央区域
- **功能**: 
  - 显示节点图
  - 支持拖拽添加节点
  - 支持连线连接端口
  - 滚轮缩放、中键平移
  - 右键菜单操作

##### 节点库面板 (NodesPaletteWidget)
- **位置**: 左侧停靠面板
- **功能**:
  - 按分类显示可用节点
  - 拖拽节点到画布
  - 标签页垂直排列（East位置）
- **分类**:
  - `io`: 输入输出节点
  - `processing`: 处理算法节点
  - `display`: 显示节点
  - `nodeGraphQt.nodes`: NodeGraphQt内置节点（通常为空）

##### 属性面板 (PropertiesBinWidget)
- **位置**: 右侧停靠面板
- **功能**:
  - 显示选中节点的属性
  - 实时编辑参数
  - 查看节点信息

##### 工具栏 (Toolbar)
- **位置**: 顶部
- **按钮**:
  - ▶ 运行: 执行节点图
  - 🗑 清空: 清除所有节点
  - 💾 保存: 保存为JSON文件
  - 📂 加载: 从JSON文件加载
  - ⊞ 适应: 自动调整视图以适应所有节点

##### 菜单栏 (MenuBar)
- **文件菜单**:
  - 新建
  - 打开
  - 保存
  - 退出
- **编辑菜单**:
  - 撤销
  - 重做
  - 剪切
  - 复制
  - 粘贴
- **运行菜单**:
  - 执行节点图
- **帮助菜单**:
  - 关于

#### 2. ImagePreviewDialog ([image_preview.py](file://d:\example\projects\StduyOpenCV\src\python\ui\image_preview.py))

图像预览对话框，用于显示完整的图像内容。

**功能特性**:
- ✅ 非模态窗口，可同时打开多个预览
- ✅ 显示原始尺寸的图像
- ✅ 自动缩放以适应窗口大小
- ✅ 保持宽高比
- ✅ 支持滚动查看大图
- ✅ 鼠标拖拽平移（空格键切换）
- ✅ 滚轮缩放（Ctrl+滚轮或 +/- 快捷键）
- ✅ 显示图像详细信息（尺寸、通道、类型）
- ✅ 保存图像到文件
- ✅ BGR/RGB正确转换
- ✅ 与节点关联，支持手动刷新预览

**触发方式**:
- 双击 [ImageViewNode](file://d:\example\projects\StduyOpenCV\src\python_graph\nodes\display_nodes.py) 节点

**使用示例**:
```
from ui.image_preview import ImagePreviewDialog

# 在主窗口中调用（非模态）
dialog = ImagePreviewDialog(image, node=node_instance, title="图像预览", parent=self)
dialog.show()  # 使用 show() 而非 exec_()，保持非模态
```

---

## 🎨 界面布局

### 主界面结构

```
┌──────────────────────────────────────────────────────────────┐
│  菜单栏: 文件 | 编辑 | 运行 | 帮助                             │
├──────────────────────────────────────────────────────────────┤
│  工具栏: ▶ 运行 | 🗑 清空 | 💾 保存 | 📂 加载 | ⊞ 适应        │
├───────────┬──────────────────────────────┬───────────────────┤
│           │                              │                   │
│  节点库    │      节点图画布               │   属性面板         │
│  (左侧)    │      (中央区域)               │   (右侧)           │
│           │                              │                   │
│ ┌───────┐ │   ○ 图像加载                 │  节点属性:         │
│ │ IO    │ │      ↓                       │  - 文件路径: [...] │
│ │ ├加载 │ │   ○ 灰度化                   │  - 状态: ...       │
│ │ └保存 │ │      ↓                       │                   │
│ ├───────┤ │   ○ Canny边缘检测            │  节点信息:         │
│ │处理   │ │      ↓                       │  - 名称: xxx       │
│ │ ├灰度 │ │   ○ 图像显示 ← 双击预览      │  - 类型: xxx       │
│ │ ├模糊 │ │                              │                   │
│ │ └Canny│ │                              │                   │
│ ├───────┤ │                              │                   │
│ │显示   │ │                              │                   │
│ │ └显示 │ │                              │                   │
│ └───────┘ │                              │                   │
│           │                              │                   │
└───────────┴──────────────────────────────┴───────────────────┘
│  状态栏: 就绪 | 节点数: 4 | 连接数: 3                           │
└──────────────────────────────────────────────────────────────┘
```

### 节点库标签位置

当前配置为**右侧显示**（垂直排列），通过以下代码实现：
```
nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
```

可选位置：
- `North`: 顶部（默认）
- `South`: 底部
- `West`: 左侧
- `East`: 右侧（当前配置）

---

## 🔧 关键实现细节

### 1. UI初始化流程

```python
def _setup_ui(self):
    # 1. 创建中央部件
    central_widget = QtWidgets.QWidget()
    self.setCentralWidget(central_widget)
    
    # 2. 创建主布局
    main_layout = QtWidgets.QHBoxLayout(central_widget)
    
    # 3. 创建并添加节点库面板
    nodes_palette = NodesPaletteWidget(node_graph=self.node_graph)
    dock_nodes = QtWidgets.QDockWidget("节点库", self)
    dock_nodes.setWidget(nodes_palette)
    self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_nodes)
    
    # 4. 添加节点图画布
    graph_widget = self.node_graph.widget
    main_layout.addWidget(graph_widget, stretch=5)
    
    # 5. 创建并添加属性面板
    properties_bin = PropertiesBinWidget(node_graph=self.node_graph)
    dock_properties = QtWidgets.QDockWidget("属性面板", self)
    dock_properties.setWidget(properties_bin)
    self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_properties)
    
    # 6. 连接信号
    self.node_graph.node_created.connect(self._on_node_created)
    self.node_graph.node_double_clicked.connect(self._on_node_double_clicked)
    
    # 7. 创建工具栏和菜单栏
    self._create_toolbar()
    self._create_menu_bar()
```

### 2. 节点注册

```python
def _register_nodes(self):
    """注册所有节点类型到NodeGraph"""
    from nodes import (
        ImageLoadNode, ImageSaveNode,
        GrayscaleNode, GaussianBlurNode, 
        CannyEdgeNode, ThresholdNode,
        ImageViewNode
    )
    
    self.node_graph.register_node(ImageLoadNode)
    self.node_graph.register_node(ImageSaveNode)
    self.node_graph.register_node(GrayscaleNode)
    self.node_graph.register_node(GaussianBlurNode)
    self.node_graph.register_node(CannyEdgeNode)
    self.node_graph.register_node(ThresholdNode)
    self.node_graph.register_node(ImageViewNode)
```

### 3. 节点双击事件处理

```python
def _on_node_double_clicked(self, node):
    """处理节点双击事件，打开图像预览"""
    if isinstance(node, ImageViewNode):
        image = node.get_cached_image()
        if image is not None:
            dialog = ImagePreviewDialog(
                image, 
                title=f"图像预览 - {node.name()}",
                parent=self
            )
            dialog.exec_()
        else:
            QtWidgets.QMessageBox.information(
                self,
                "提示",
                "该节点尚未处理图像数据\n请先运行节点图"
            )
```

### 4. 图像预览对话框实现

**文件位置**: [image_preview.py](file://d:\example\projects\StduyOpenCV\src\python\ui\image_preview.py)

```python
class ImagePreviewDialog(QtWidgets.QDialog):
    def __init__(self, image, node=None, title="图像预览", parent=None):
        super().__init__(parent)
        self.image = image
        self.node = node  # 关联的节点实例
        
        # 缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # 使用 QGraphicsView 显示图像
        self.graphics_view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        
        # 启用拖拽平移
        self.graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
    
    def display_image(self):
        """将OpenCV图像转换为Qt格式并显示"""
        # BGR → RGB 转换
        rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
        # 创建QImage
        qt_image = QtGui.QImage(
            rgb_image.data, width, height, 
            width * 3, 
            QtGui.QImage.Format_RGB888
        )
        
        # 创建QPixmap并添加到场景
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 适应窗口显示
        self.fit_to_window()
    
    def zoom_in(self):
        """放大图像"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= 1.2
            self.apply_zoom()
    
    def zoom_out(self):
        """缩小图像"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= 1.2
            self.apply_zoom()
    
    def refresh_preview(self):
        """从关联节点刷新图像"""
        if self.node is not None:
            new_image = self.node.get_cached_image()
            if new_image is not None:
                self.image = new_image.copy()
                self.display_image()
```


---

## ⚠️ API陷阱与解决方案

根据项目开发经验，以下API使用需要特别注意：

### 1. NodesPaletteWidget的tab_widget访问

❌ **错误方式**:
```python
nodes_palette.tabWidget().setTabPosition(...)  # AttributeError
```

✅ **正确方式**:
```python
nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
```

**原因**: `tab_widget` 是属性而非方法。

### 2. 节点按钮事件绑定

❌ **不支持**:
```python
button = node.add_button('btn', '点击')
button.clicked.connect(handler)  # AttributeError: NodeButton无clicked信号
```

✅ **替代方案**:
```python
# 使用文本输入框让用户直接输入
node.add_text_input('file_path', '文件路径')
```

### 3. 节点滑块控件

❌ **不存在**:
```python
node.add_slider('param', '参数', 0, 100, 50)  # AttributeError
```

✅ **替代方案**:
```python
node.add_text_input('param', '参数')
# 在process()中进行数值验证
param = int(self.get_property('param'))
```

---

## 🚀 优化及改进计划

### 短期目标 (v1.x)
- [ ] 添加状态栏信息显示（节点数、连接数、执行状态）
- [ ] 实现撤销/重做功能
- [ ] 添加节点搜索框（快速定位节点）
- [ ] 优化深色主题配色
- [ ] 添加快捷键提示对话框

### 中期目标 (v2.x)
- [ ] 实现多文档界面（同时打开多个节点图）
- [ ] 添加节点缩略图预览（鼠标悬停显示）
- [ ] 实现工作区布局保存/加载
- [ ] 添加自定义节点图标支持
- [ ] 实现节点分组和折叠功能

### 长期目标 (v3.x)
- [ ] 插件系统（动态加载第三方节点）
- [ ] 云端同步（工作流共享）
- [ ] 协作编辑（多人同时编辑）
- [ ] VR/AR界面支持
- [ ] 语音控制接口

---

## 🐛 常见问题

### Q: 节点库标签显示在顶部，如何改为右侧？
**A**: 在 `_setup_ui()` 中修改：
``python
nodes_palette.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
```

### Q: 双击节点没有反应？
**A**: 检查是否已连接 `node_double_clicked` 信号：
```python
self.node_graph.node_double_clicked.connect(self._on_node_double_clicked)
```

### Q: 图像预览窗口显示颜色异常？
**A**: 确保进行了BGR到RGB的转换：
```python
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```

### Q: 如何添加新的工具栏按钮？
**A**: 在 `_create_toolbar()` 方法中添加：
```python
new_action = QtWidgets.QAction("新按钮", self)
new_action.triggered.connect(self.new_function)
toolbar.addAction(new_action)
```

---

## 📚 相关文档

- 📘 [项目总览](../../README.md) - 整体项目介绍
- 📗 [节点模块](../nodes/README.md) - 节点定义与开发
- 📕 [核心引擎模块](../core/README.md) - 图执行引擎说明
- 🔗 [PySide2官方文档](https://doc.qt.io/qtforpython/)
- 🔗 [NodeGraphQt文档](https://github.com/jchanvfx/NodeGraphQt)

---

## 🤝 贡献指南

如需改进UI模块，请遵循以下原则：
1. 保持界面简洁直观
2. 遵循Qt编码规范
3. 测试不同分辨率下的显示效果
4. 更新本文档
5. 添加必要的注释和文档字符串
