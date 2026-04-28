# 轮廓形状检测设计理念

## 一、设计目标

为轮廓分析节点增加**几何形状识别能力**，使其能够自动判断轮廓的几何类型（圆形、矩形、直线），并输出相应的特征参数和置信度。

---

## 二、核心设计原则

### 1. 单一综合模式
- **原则**: 在现有 `ContoursAnalysisNode` 中通过参数开关控制形状检测功能
- **理由**: 
  - 避免工作流碎片化（不需要额外的"圆形检测节点"、"矩形检测节点"）
  - 所有形状分析基于同一组轮廓，保证数据一致性
  - 用户一次配置即可完成多种形状检测

### 2. 按需计算
- **原则**: 通过参数开关选择性启用/禁用特定形状检测
- **实现**:
  ```python
  enable_circle_detection = True   # 是否检测圆形
  enable_rectangle_detection = True # 是否检测矩形
  enable_line_detection = True      # 是否检测直线
  ```
- **优势**: 用户只需某种形状时，关闭其他检测以提升性能

### 3. 置信度输出
- **原则**: 每个形状判断都附带置信度评分（0-1）
- **理由**:
  - 工业场景中形状可能不规则，需要量化判断可靠性
  - 用户可根据置信度阈值过滤低质量检测结果
  - 便于后续节点进行决策（如：仅处理置信度>0.9的圆形）

### 4. 可配置阈值
- **原则**: 所有形状判断的阈值参数均可调节
- **示例**:
  ```python
  circle_circularity_threshold = 0.85    # 圆度阈值
  rectangle_fill_ratio_threshold = 0.80  # 矩形填充率阈值
  line_straightness_threshold = 0.90     # 直线度阈值
  ```
- **优势**: 适应不同工业场景的精度要求

---

## 三、形状检测算法设计

### 1. 圆形检测

#### 算法原理
```
步骤1: 计算最小外接圆 (cv2.minEnclosingCircle)
步骤2: 计算理论圆面积 = π × radius²
步骤3: 计算实际轮廓面积 (cv2.contourArea)
步骤4: 圆度 = 实际面积 / 理论圆面积
步骤5: 若圆度 > 阈值 → 判定为圆形
```

#### 关键指标
- **圆心坐标**: `(center_x, center_y)`
- **半径**: `radius` (像素)
- **圆度**: `circularity` (0-1，越接近1越圆)
- **置信度**: `confidence = circularity`

#### 适用场景
- 螺栓孔检测
- 轴承内外圈测量
- 圆形零件定位

#### 注意事项
- 椭圆会被误判为圆形（圆度约0.7-0.9）
- 建议配合长宽比过滤（`aspect_ratio ≈ 1.0`）

---

### 2. 矩形检测

#### 算法原理
```
步骤1: 计算最小外接矩形 (cv2.minAreaRect)
步骤2: 获取矩形四顶点 (cv2.boxPoints)
步骤3: 计算矩形面积 = width × height
步骤4: 计算实际轮廓面积
步骤5: 填充率 = 实际面积 / 矩形面积
步骤6: 若填充率 > 阈值 → 判定为矩形
```

#### 关键指标
- **中心坐标**: `(center_x, center_y)`
- **宽度**: `width` (像素)
- **高度**: `height` (像素)
- **旋转角度**: `angle` (度，-90~0)
- **四顶点坐标**: `[(x1,y1), (x2,y2), (x3,y3), (x4,y4)]`
- **填充率**: `fill_ratio` (0-1，越接近1越规整)
- **置信度**: `confidence = fill_ratio`

#### 适用场景
- PCB板定位
- 包装盒检测
- 矩形零件测量

#### 注意事项
- 平行四边形也会被判定为矩形（填充率高）
- 建议配合角度约束（如：仅需0°或90°的矩形）

---

### 3. 直线检测

#### 算法原理
```
步骤1: 拟合直线 (cv2.fitLine)
步骤2: 获取直线方向向量 (vx, vy) 和基点 (x, y)
步骤3: 计算轮廓点到直线的距离
步骤4: 直线度 = 1 - (平均距离 / 轮廓长度)
步骤5: 若直线度 > 阈值 → 判定为直线
```

#### 关键指标
- **起点坐标**: `(start_x, start_y)`
- **终点坐标**: `(end_x, end_y)`
- **角度**: `angle` (度，相对于水平轴)
- **长度**: `length` (像素)
- **直线度**: `straightness` (0-1，越接近1越直)
- **置信度**: `confidence = straightness`

#### 适用场景
- 边缘对齐检测
- 焊缝跟踪
- 导轨直线度测量

#### 注意事项
- 开放轮廓才能准确检测直线
- 闭合轮廓（如矩形边）需先提取单边

---

## 四、数据结构设计

### 输出格式（扩展 Phase 1 的统计数据）

```python
{
    'total_count': 10,
    'filtered_count': 5,
    'contours': [
        {
            'index': 0,
            'area': 1234.5,
            'perimeter': 456.7,
            'bounding_rect': {'x': 10, 'y': 20, 'w': 100, 'h': 50},
            'centroid': {'x': 60, 'y': 45},
            
            # 新增：形状检测结果
            'shape_type': 'rectangle',  # circle / rectangle / line / unknown
            'shape_confidence': 0.92,   # 置信度 0-1
            
            # 圆形特征（仅当 shape_type='circle' 时有效）
            'circle': {
                'center': {'x': 60, 'y': 45},
                'radius': 20,
                'circularity': 0.95
            },
            
            # 矩形特征（仅当 shape_type='rectangle' 时有效）
            'rectangle': {
                'center': {'x': 60, 'y': 45},
                'width': 100,
                'height': 50,
                'angle': 15.5,
                'corners': [[10,20], [110,20], [110,70], [10,70]],
                'fill_ratio': 0.88
            },
            
            # 直线特征（仅当 shape_type='line' 时有效）
            'line': {
                'start_point': {'x': 10, 'y': 20},
                'end_point': {'x': 110, 'y': 20},
                'angle': 0.0,
                'length': 100.0,
                'straightness': 0.93
            }
        },
        ...
    ]
}
```

### 设计说明
1. **向后兼容**: 保留 Phase 1 的所有字段
2. **条件字段**: `circle`/`rectangle`/`line` 仅在对应形状检测启用且匹配时存在
3. **未知形状**: `shape_type='unknown'` 表示未匹配任何已知形状
4. **嵌套结构**: 便于下游节点按类型解析数据

---

## 五、参数配置设计

### 新增参数组（UI 标签页：properties）

```
【形状检测开关】
├─ ☑ 启用圆形检测
│   └─ 圆度阈值: [0.85      ]
├─ ☑ 启用矩形检测
│   └─ 填充率阈值: [0.80    ]
└─ ☑ 启用直线检测
    └─ 直线度阈值: [0.90    ]
```

### 参数说明
| 参数名 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| enable_circle_detection | bool | True | True/False | 是否检测圆形 |
| circle_circularity_threshold | float | 0.85 | 0.0-1.0 | 圆度阈值，越高要求越圆 |
| enable_rectangle_detection | bool | True | True/False | 是否检测矩形 |
| rectangle_fill_ratio_threshold | float | 0.80 | 0.0-1.0 | 填充率阈值，越高要求越规整 |
| enable_line_detection | bool | True | True/False | 是否检测直线 |
| line_straightness_threshold | float | 0.90 | 0.0-1.0 | 直线度阈值，越高要求越直 |

---

## 六、优先级策略

### 问题：一个轮廓可能同时满足多种形状条件

**示例**: 正方形既是矩形（填充率高），也可能被误判为圆形（圆度约0.78）

### 解决方案：优先级排序

```python
# 形状判断优先级（从高到低）
1. 矩形检测（最严格，填充率>0.8）
2. 圆形检测（次严格，圆度>0.85）
3. 直线检测（较宽松，直线度>0.9）
4. 未知形状（都不满足）
```

### 实现逻辑
```python
def classify_shape(contour, params):
    """
    按优先级判断形状
    
    Returns:
        tuple: (shape_type, confidence, shape_data)
    """
    # 1. 尝试矩形检测
    if params['enable_rectangle']:
        rect_result = detect_rectangle(contour)
        if rect_result['confidence'] >= params['rect_threshold']:
            return ('rectangle', rect_result['confidence'], rect_result)
    
    # 2. 尝试圆形检测
    if params['enable_circle']:
        circle_result = detect_circle(contour)
        if circle_result['confidence'] >= params['circle_threshold']:
            return ('circle', circle_result['confidence'], circle_result)
    
    # 3. 尝试直线检测
    if params['enable_line']:
        line_result = detect_line(contour)
        if line_result['confidence'] >= params['line_threshold']:
            return ('line', line_result['confidence'], line_result)
    
    # 4. 未知形状
    return ('unknown', 0.0, {})
```

### 优势
- ✅ 避免重复分类（一个轮廓只有一个 shape_type）
- ✅ 矩形优先（工业场景中最常见）
- ✅ 可解释性强（用户知道为何判定为某形状）

---

## 七、可视化增强

### 标注图像绘制规则

#### 1. 圆形标注
- 绘制外接圆（绿色）
- 标注圆心（红色小圆点）
- 显示半径文字（可选）

#### 2. 矩形标注
- 绘制最小外接矩形（蓝色）
- 标注四顶点（黄色小圆点）
- 显示角度文字（可选）

#### 3. 直线标注
- 绘制拟合直线（紫色）
- 标注起点和终点（橙色小圆点）
- 显示角度文字（可选）

#### 4. 未知形状
- 仅绘制轮廓本身（灰色）
- 不添加额外标注

### 颜色方案
| 形状类型 | 轮廓颜色 | 标记颜色 |
|---------|---------|---------|
| 圆形 | (0, 255, 0) 绿色 | (255, 0, 0) 红色 |
| 矩形 | (0, 0, 255) 蓝色 | (255, 255, 0) 黄色 |
| 直线 | (255, 0, 255) 紫色 | (255, 165, 0) 橙色 |
| 未知 | (128, 128, 128) 灰色 | 无 |

---

## 八、性能优化策略

### 1. 提前退出
```python
# 若用户关闭所有形状检测，直接跳过
if not (enable_circle or enable_rectangle or enable_line):
    return None  # 不执行形状检测
```

### 2. 面积预过滤
```python
# 过小轮廓跳过形状检测（噪声干扰大）
if area < min_shape_detection_area:  # 默认 50 像素²
    shape_type = 'unknown'
    continue
```

### 3. 并行计算（远期）
```python
# 大量轮廓时，使用多线程并行检测
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(classify_shape, contours))
```

---

## 九、异常处理

### 1. 退化轮廓处理
```python
# 点数过少无法拟合
if len(contour) < 3:
    return ('unknown', 0.0, {})

# 面积为0（共线点）
if area == 0:
    return ('unknown', 0.0, {})
```

### 2. 数值稳定性
```python
# 防止除零错误
circularity = actual_area / theoretical_area if theoretical_area > 0 else 0

# 防止浮点误差导致置信度>1
confidence = min(confidence, 1.0)
```

### 3. OpenCV 异常捕获
```python
try:
    rect = cv2.minAreaRect(contour)
except Exception as e:
    self.log_warning(f"矩形拟合失败: {e}")
    return ('unknown', 0.0, {})
```

---

## 十、测试用例设计

### 1. 标准形状测试
- **输入**: 完美圆形、正方形、直线段
- **预期**: 置信度 > 0.95，正确分类

### 2. 噪声干扰测试
- **输入**: 带噪声的形状（锯齿边缘）
- **预期**: 置信度降低，但仍能正确分类

### 3. 形变测试
- **输入**: 椭圆、平行四边形、曲线
- **预期**: 分类为最接近的形状或 unknown

### 4. 边界条件测试
- **输入**: 单点、两点、空轮廓
- **预期**: 返回 unknown，不崩溃

### 5. 性能测试
- **输入**: 1000+ 轮廓
- **预期**: 执行时间 < 1秒（light 资源等级）

---

## 十一、与后续阶段的衔接

### Phase 3: 模板匹配的基础
- 形状检测结果可作为模板匹配的预处理
- 例如：仅对判定为"圆形"的轮廓进行圆形模板匹配

### Phase 4: 数据导出的增强
- 形状类型和置信度应包含在 CSV/Excel 导出中
- 便于后续统计分析（如：圆形合格率统计）

---

## 十二、总结

本设计方案遵循以下核心理念：
1. **单一综合节点**: 通过参数开关控制，避免碎片化
2. **置信度驱动**: 量化判断可靠性，支持阈值过滤
3. **优先级策略**: 避免重复分类，提高可解释性
4. **可扩展性**: 预留接口支持未来新增形状类型（如椭圆、三角形）

此设计既满足当前需求（圆/矩形/直线检测），又为未来扩展（更多形状、更复杂算法）奠定基础。
