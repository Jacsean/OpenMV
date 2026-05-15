---
name: 节点设计规范
description: 在增加、编辑、修改、调试节点相关功能时使用
---

# 项目设计规范

## 一、节点UI设计规范

### 1.1 节点尺寸规范
```
节点宽度：280px（固定）
节点高度：根据参数数量自动计算，建议最大不超过 300px
```

### 1.2 参数控件类型映射

| 参数类型 | 示例值 | 使用控件 | NodeGraphQt方法 |
|---------|-------|---------|----------------|
| 整数 | `100`, `255`, `50` | QSpinBox | `add_spinbox(name, label, value=100, min_value=0, max_value=255, tab='properties')` |
| 浮点数 | `0.5`, `1.5` | QDoubleSpinBox | `add_spinbox(name, label, value=0.5, min_value=0.0, max_value=1.0, double=True, tab='properties')` |
| 布尔值 | `True`, `False` | QCheckBox | `add_checkbox(name, label, text='', state=False, tab='properties')` |
| 枚举选项 | `'CHAIN_APPROX_SIMPLE'` | QComboBox | `add_combo_menu(name, label, items=['A', 'B', 'C'], tab='properties')` |
| 路径/字符串 | `'path/to/file'` | QLineEdit | `add_text_input(name, label, text='', tab='properties')` |

### 1.3 参数命名规范
- 整数参数：`xxx_value`, `xxx_size`, `xxx_count`, `xxx_threshold`
- 浮点参数：`xxx_ratio`, `xxx_scale`, `xxx_factor`
- 布尔参数：`enable_xxx`, `show_xxx`, `use_xxx`
- 枚举参数：`xxx_mode`, `xxx_method`, `xxx_type`

### 1.4 节点内参数容器规范

**容器设计要求：**
```
┌─────────────────────────────────────┐
│  QScrollArea (最大高度=两行参数)     │
│  ┌─────────────────────────────┐   │
│  │  透明容器                    │   │
│  │  ┌─────────────────────┐    │   │
│  │  │ [标签]    [控件]     │    │   │  ← 参数行1
│  │  ├─────────────────────┤    │   │
│  │  │ [标签]    [控件]     │    │   │  ← 参数行2
│  │  ├─────────────────────┤    │   │
│  │  │ [标签]    [控件]     │    │   │  ← 参数行3 (滚动显示)
│  │  └─────────────────────┘    │   │
│  └─────────────────────────────┘   │
│  │← 垂直滚动条（超出两行时显示）│   │
└─────────────────────────────────────┘
```

| 属性 | 要求 |
|-----|------|
| **容器宽度** | 自适应（=最大参数行宽度，不超过节点宽度） |
| **容器高度** | 显示两行参数为准 |
| **滚动条** | QScrollArea 包装，垂直滚动，按需显示 |
| **背景** | 透明 (`background-color: transparent`) |
| **标签宽度** | 固定 70px |
| **行间距** | 6px |
| **边距** | 4px |

**滚动条配置：**
```python
scroll_area = QScrollArea()
scroll_area.setMaximumHeight(两行参数的高度)
scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
scroll_area.setWidgetResizable(True)
```

### 1.5 自定义参数容器控件

**使用方式：**
```python
from shared_libs.node_base import ParameterContainerWidget

# 创建参数容器
param_container = ParameterContainerWidget()

# 添加参数控件
param_container.add_spinbox('threshold1', '低阈值', value=50, min_value=0, max_value=255)
param_container.add_spinbox('threshold2', '高阈值', value=150, min_value=0, max_value=255)
param_container.add_checkbox('enable_feature', '启用功能', state=True)
param_container.add_combobox('mode', '模式', items=['A', 'B', 'C'])
param_container.add_text_input('path', '路径', text='')

# 设置值变化回调
param_container.set_value_changed_callback(self._on_param_changed)

# 添加到节点
self.add_custom_widget(param_container, tab='properties')
```

**特性：**
- 垂直布局排列参数控件
- 背景透明，融入节点样式
- 标签固定宽度 70px，确保对齐
- 支持整数/浮点数值输入、布尔复选框、枚举下拉菜单、文本输入
- 统一的值变化回调机制
- 容器高度固定显示两行，超出部分滚动条翻找

---

## 二、代码命名规范

### 2.1 方法名拼写检查
```python
# 正确写法
self.add_spinbox()    # 无下划线
self.add_text_input() # 下划线分隔
self.add_combo_menu() # 下划线分隔
self.add_checkbox()   # 下划线分隔

# 错误写法（会导致 AttributeError）
self.add_spin_box()   # ❌ 有下划线
```

### 2.2 参数范围规范
```python
# 像素值类：0 - 999999
min_value=0, max_value=999999

# 比例/百分比类：0 - 1 或 0 - 100
min_value=0.0, max_value=1.0  # 浮点
min_value=0, max_value=100    # 百分比

# 阈值类：0 - 255
min_value=0, max_value=255
```

---

## 三、节点分类

### 3.1 图像处理类（16个）
| 文件 | 节点名称 | 优先级 |
|-----|---------|-------|
| grayscale.py | 灰度转换 | 高 |
| gaussian_blur.py | 高斯模糊 | 高 |
| median_blur.py | 中值滤波 | 高 |
| bilateral_filter.py | 双边滤波 | 高 |
| threshold.py | 阈值处理 | 高 |
| adaptive_threshold.py | 自适应阈值 | 中 |
| canny_edge.py | Canny算子 | 高 |
| sobel_edge.py | Sobel边缘 | 中 |
| resize.py | 图像缩放 | 高 |
| rotate.py | 图像旋转 | 高 |
| brightness_contrast.py | 亮度对比度 | 高 |
| histogram_equalization.py | 直方图均衡 | 中 |
| morphology.py | 形态学操作 | 中 |
| pyramid.py | 图像金字塔 | 中 |
| image_operation.py | 图像运算 | 中 |
| find_circle.py | 圆形检测 | 中 |

### 3.2 特征检测类（3个）
| 文件 | 节点名称 | 优先级 |
|-----|---------|-------|
| contours_analysis.py | 轮廓分析 | 高 |
| fast_detection.py | FAST角点检测 | 中 |
| template_match.py | 模板匹配 | 高 |

### 3.3 IO类（6个）
| 文件 | 节点名称 | 优先级 |
|-----|---------|-------|
| image_load.py | 图像读取 | 高 |
| image_save.py | 图像保存 | 高 |
| image_view.py | 图像显示 | 高 |
| camera_capture.py | 相机采集 | 中 |
| video_recorder.py | 视频录制 | 中 |
| realtime_preview.py | 实时预览 | 中 |

### 3.4 其他类（5个）
| 文件 | 节点名称 | 优先级 |
|-----|---------|-------|
| data_output_node.py | 数据输出 | 中 |
| json_display.py | JSON显示 | 低 |
| template_creator.py | 模板创建 | 中 |
| plc_node.py | PLC节点 | 低 |
| robot_node.py | 机器人节点 | 低 |

---

## 四、实施计划

### Phase 1: 修复现有错误
1. 修复 `contours_analysis.py` 中的拼写错误 ✅

### Phase 2: 逐个节点规范化
按优先级顺序改造节点，每个节点改造后验证

### Phase 3: 统一测试
检查所有节点是否符合规范

---

## 五、规范维护

### 5.1 修改规范
- 直接编辑本文件即可更新规范
- 修改后新建任务时会自动加载新规范

### 5.2 跨项目使用
- 复制本文件到目标项目的 `.trae/rules/` 目录
- 根据项目特点适当修改参数范围和控件映射