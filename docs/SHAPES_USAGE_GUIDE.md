"""
图形数据结构使用指南

本模块提供了统一的图形数据模型，用于管理图像上的标注、ROI和Mask。

## 快速开始

### 1. 导入模块

```python
from core.shapes import BaseShape, AnnotationShape, ROIShape, MaskShape, ShapeContainer
```

或者从 core 包直接导入：

```python
from core import ROIShape, MaskShape, ShapeContainer
```

### 2. 基本用法

#### 创建图形容器

```python
# 创建容器来管理所有图形
container = ShapeContainer()
```

#### 添加ROI（感兴趣区域）

```python
# ROI仅支持矩形类型
roi = ROIShape(
    type='rect',
    points=[(10, 10), (200, 150)],  # 左上角和右下角坐标
    name="检测区域1"
)
container.add_roi(roi)
```

#### 添加Mask（掩码区域）

```python
# Mask支持矩形、圆形、多边形

# 矩形Mask
mask_rect = MaskShape(
    type='rect',
    points=[(50, 50), (150, 150)],
    name="矩形掩码"
)

# 圆形Mask
mask_circle = MaskShape(
    type='circle',
    points=[(100, 100), 50],  # 圆心坐标和半径
    name="圆形掩码"
)

# 多边形Mask
mask_polygon = MaskShape(
    type='polygon',
    points=[(10, 10), (100, 10), (100, 100), (10, 100)],
    name="多边形掩码"
)

container.add_mask(mask_rect)
container.add_mask(mask_circle)
container.add_mask(mask_polygon)
```

#### 添加普通标注

```python
# 普通标注用于临时标记，不会被导出
annotation = AnnotationShape(
    type='rect',
    points=[(30, 30), (80, 80)],
    border_color=(0, 255, 0),  # BGR格式：绿色
    thickness=2,
    name="临时标注"
)
container.add_annotation(annotation)
```

### 3. 图形操作

#### 选择和删除

```python
# 选中ROI
container.select_roi(roi)

# 选中Mask
container.select_mask(mask_rect)

# 清除选中
container.clear_selection()

# 删除图形（通过ID）
container.remove_roi(roi.id)
container.remove_mask(mask_rect.id)
container.remove_annotation(annotation.id)
```

#### 模式切换

```python
# 切换到ROI模式（仅显示ROI相关工具）
container.switch_mode('roi')

# 切换到Mask模式
container.switch_mode('mask')

# 切换到普通绘图模式
container.switch_mode('annotation')
```

#### 获取图形列表

```python
# 获取所有可见图形
all_shapes = container.get_all_shapes()

# 遍历并处理
for shape in all_shapes:
    print(f"图形: {shape.name}, 类型: {shape.type}")
```

### 4. 高级功能

#### 位置检测

```python
from PySide2 import QtCore

# 检查点是否在图形内
scene_pos = QtCore.QPointF(50, 50)
shape = container.get_shape_at_position(scene_pos)

if shape:
    print(f"点击了图形: {shape.name}")
```

#### 移动图形

```python
# 移动图形（相对偏移）
container.move_shape(roi, delta_x=10, delta_y=20)
```

#### 调整图形大小

```python
# 获取手柄位置
handles = container.get_resize_handles(roi)
print(handles)  # {'top-left': (10, 10), 'top-right': (200, 10), ...}

# 调整大小
new_pos = QtCore.QPointF(250, 200)
container.resize_shape(roi, 'bottom-right', new_pos)
```

### 5. 图形属性

每个图形对象都有以下属性：

```python
shape = ROIShape(type='rect', points=[(10, 10), (100, 100)])

# 基本信息
print(shape.id)          # 唯一标识符（自动生成）
print(shape.type)        # 图形类型
print(shape.points)      # 顶点坐标列表
print(shape.name)        # 名称

# 视觉属性
print(shape.border_color)  # 边框颜色 (BGR)
print(shape.fill_color)    # 填充颜色 (BGR)，None表示不填充
print(shape.thickness)     # 线条粗细
print(shape.line_style)    # 线条样式 ('solid', 'dashed', 'dotted')

# 元数据
print(shape.visible)       # 是否可见
print(shape.locked)        # 是否锁定
print(shape.created_at)    # 创建时间
```

### 6. 在ImagePreviewDialog中使用

```python
from ui.image_preview import ImagePreviewDialog
import cv2

# 加载图像
image = cv2.imread("test.jpg")

# 创建预览对话框
dialog = ImagePreviewDialog(image=image, node=None, title="测试预览")

# 通过对话框的container访问图形管理器
container = dialog.container

# 添加ROI
roi = ROIShape(type='rect', points=[(50, 50), (200, 150)])
container.add_roi(roi)

# 显示对话框
dialog.show()
```

## 注意事项

1. **ROI限制**：ROI只能是矩形类型，尝试创建其他类型会抛出 `ValueError`
2. **Mask类型**：Mask支持矩形、圆形、多边形三种类型
3. **坐标系统**：所有坐标使用像素单位，原点为左上角
4. **颜色格式**：使用BGR格式（OpenCV标准），而非RGB
5. **线程安全**：图形容器不是线程安全的，多线程环境下需要加锁

## 扩展开发

如果需要添加新的图形类型，可以继承 `BaseShape`：

```python
@dataclass
class ArrowShape(BaseShape):
    """箭头形状"""
    def __post_init__(self):
        self.type = 'arrow'
        # 自定义初始化逻辑
```

然后在 `ShapeContainer` 中添加相应的处理方法。
"""
