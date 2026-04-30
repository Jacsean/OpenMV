# 图形数据结构模块 (core.shapes)

## 概述

本模块将图像预览功能中的图形数据结构定义提取为独立的可复用模块，方便其他模块直接使用。

## 文件结构

```
src/python/core/
├── shapes.py                    # 图形数据结构定义
├── SHAPES_USAGE_GUIDE.md        # 使用指南
└── __init__.py                  # 模块导出配置
```

## 主要组件

### 1. 数据类 (Data Classes)

- **BaseShape**: 图形基类，包含所有图形的通用属性
- **AnnotationShape**: 普通标注（不导出，仅视觉辅助）
- **ROIShape**: ROI对象（仅矩形，可导出为JSON）
- **MaskShape**: Mask对象（矩形/圆/多边形，可导出为灰度图）

### 2. 容器类

- **ShapeContainer**: 图形容器管理器，提供增删改查、选择、移动、调整大小等功能

## 使用方式

### 方式一：直接导入

```python
from core.shapes import BaseShape, AnnotationShape, ROIShape, MaskShape, ShapeContainer
```

### 方式二：从core包导入

```python
from core import ROIShape, MaskShape, ShapeContainer
```

## 特性

✅ **类型安全**: 使用dataclass和类型注解  
✅ **自动ID生成**: 每个图形都有唯一的UUID标识  
✅ **模式管理**: 支持annotation/roi/mask三种模式  
✅ **位置检测**: 内置点在图形内判断算法（射线法）  
✅ **手柄系统**: 支持8个调整手柄（矩形）和1个半径手柄（圆形）  
✅ **移动和调整**: 完整的图形编辑功能  

## 兼容性

- ✅ 与 `ImagePreviewDialog` 完全兼容
- ✅ 保持原有的API接口不变
- ✅ 向后兼容，不影响现有功能

## 示例代码

```python
from core.shapes import ROIShape, ShapeContainer

# 创建容器
container = ShapeContainer()

# 添加ROI
roi = ROIShape(
    type='rect',
    points=[(10, 10), (200, 150)],
    name="检测区域"
)
container.add_roi(roi)

# 获取所有图形
shapes = container.get_all_shapes()
print(f"共有 {len(shapes)} 个图形")
```

详细使用指南请查看 [SHAPES_USAGE_GUIDE.md](./SHAPES_USAGE_GUIDE.md)

## 重构说明

### 改动前
图形数据结构定义在 `ui/image_preview.py` 文件中，与其他UI逻辑耦合。

### 改动后
- 图形数据结构独立为 `core/shapes.py` 模块
- `image_preview.py` 通过导入使用该模块
- 其他模块可以直接引用，无需依赖UI组件

### 优势
1. **解耦**: 数据模型与UI逻辑分离
2. **复用**: 其他模块可直接使用图形数据结构
3. **测试**: 可以独立测试数据模型
4. **维护**: 集中管理图形相关逻辑

## 未来扩展

计划添加的功能：
- [ ] 序列化/反序列化支持（JSON格式）
- [ ] 图形分组功能
- [ ] 撤销/重做支持
- [ ] 更多图形类型（箭头、自由曲线等）
