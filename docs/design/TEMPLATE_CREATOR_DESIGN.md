# 轮廓模板创建设计理念

## 一、设计目标

创建**模板创建节点（TemplateCreatorNode）**，用于从已分析的轮廓中提取特征描述符并生成可复用的模板数据，为后续的模板匹配功能奠定基础。

---

## 二、核心设计原则

### 1. 单一职责
- **原则**: TemplateCreatorNode 专注于模板数据的生成和序列化
- **理由**: 
  - 与 ContoursAnalysisNode 分离，保持功能边界清晰
  - 模板创建是独立的操作，不应与轮廓分析耦合
  - 便于单独测试和调试

### 2. 算法可扩展性
- **原则**: 支持多种特征提取算法（Hu矩、Shape Context等）
- **实现**:
  ```python
  algorithm = 'hu_moments'  # hu_moments / shape_context / hausdorff
  ```
- **优势**: 用户可根据场景选择最合适的算法

### 3. 目标轮廓灵活选择
- **原则**: 支持多种方式选择目标轮廓
- **方式**:
  - 按索引选择：`target_index = 0`
  - 按形状类型筛选：`shape_filter = 'circle'`
  - 按面积范围筛选：`area_min=100, area_max=1000`
  - 按置信度筛选：`confidence_min=0.9`
- **优势**: 适应不同应用场景的选择需求

### 4. 模板数据标准化
- **原则**: 所有算法生成的模板数据遵循统一的JSON格式
- **示例**:
  ```json
  {
    "algorithm": "hu_moments",
    "hu_moments": [0.1, 0.2, ...],
    "reference_area": 1234.5,
    "reference_perimeter": 456.7,
    "created_at": "2026-04-28T12:00:00"
  }
  ```
- **优势**: 下游节点（TemplateMatchNode）无需关心算法细节

---

## 三、支持的算法清单

### 1. Hu矩算法（基础版）

#### 原理
- OpenCV API: `cv2.HuMoments(cv2.moments(contour))`
- 返回7个不变矩值，对旋转、缩放、平移具有不变性

#### 适用场景
- ✅ 形状规则、旋转/缩放不变性要求高
- ✅ 计算速度快（毫秒级）
- ✅ 实现简单，无需额外依赖

#### 数据结构
```json
{
  "algorithm": "hu_moments",
  "hu_moments": [
    0.001234,
    0.000567,
    0.000089,
    0.000012,
    0.000003,
    0.000001,
    0.000000
  ],
  "reference_area": 1234.5,
  "reference_perimeter": 456.7,
  "created_at": "2026-04-28T12:00:00"
}
```

#### 注意事项
- Hu矩值为对数尺度，可能为负数
- 需配合参考面积/周长用于尺度归一化

---

### 2. Shape Context算法（高级版）

#### 原理
- OpenCV contrib API: `cv2.xfeatures2d.ShapeContextDistanceExtractor`
- 基于形状上下文的距离度量，类似Halcon的shape-based matching

#### 适用场景
- ✅ 复杂形状、需要高精度匹配
- ✅ 对形变有一定容忍度
- ❌ 需要opencv-contrib-python依赖

#### 数据结构
```json
{
  "algorithm": "shape_context",
  "shape_context_descriptor": {
    "n_points": 100,
    "inner_radius": 0.1,
    "outer_radius": 2.0,
    "n_radial_bins": 4,
    "n_angular_bins": 12
  },
  "sampled_points": [[x1,y1], [x2,y2], ...],
  "reference_area": 1234.5,
  "reference_perimeter": 456.7,
  "created_at": "2026-04-28T12:00:00"
}
```

#### 注意事项
- 需要对轮廓点进行采样（默认100点）
- 参数调优复杂（bins数量、半径范围等）
- 计算速度较慢（秒级）

---

### 3. Hausdorff距离算法（进阶版）

#### 原理
- OpenCV API: `cv2.createHausdorffDistanceExtractor()`
- 基于点集之间的最大最小距离

#### 适用场景
- ✅ 部分遮挡情况
- ✅ 不完整轮廓匹配
- ✅ 不规则形状

#### 数据结构
```json
{
  "algorithm": "hausdorff",
  "contour_points": [[x1,y1], [x2,y2], ...],
  "normalization_factor": 100.0,
  "reference_area": 1234.5,
  "reference_perimeter": 456.7,
  "created_at": "2026-04-28T12:00:00"
}
```

#### 注意事项
- 需保存原始轮廓点集
- 距离值需归一化处理
- 对噪声敏感

---

## 四、目标轮廓选择策略

### 1. 按索引选择（精确模式）

#### 参数配置
```python
selection_mode = 'by_index'
target_index = 0  # 第0个轮廓
```

#### 适用场景
- 已知目标轮廓在列表中的位置
- 工作流中前序节点已确定轮廓顺序

#### 优点
- ✅ 简单直接
- ✅ 性能最优（O(1)查找）

#### 缺点
- ❌ 轮廓顺序变化时会失效
- ❌ 不具鲁棒性

---

### 2. 按形状类型筛选（语义模式）

#### 参数配置
```python
selection_mode = 'by_shape'
shape_filter = 'circle'  # circle / rectangle / line
confidence_min = 0.9     # 最小置信度
```

#### 适用场景
- 需要特定形状的轮廓作为模板
- 轮廓数量较多，手动选择不现实

#### 优点
- ✅ 语义清晰（"我要圆形模板"）
- ✅ 鲁棒性强（不受顺序影响）

#### 缺点
- ❌ 可能匹配到多个轮廓（需进一步筛选）
- ❌ 依赖前序节点的形状检测准确性

#### 多结果处理
```python
# 若匹配多个轮廓，选择置信度最高的
candidates = [c for c in contours if c['shape_type'] == 'circle' and c['shape_confidence'] >= 0.9]
if candidates:
    target = max(candidates, key=lambda x: x['shape_confidence'])
```

---

### 3. 按面积范围筛选（尺寸模式）

#### 参数配置
```python
selection_mode = 'by_area'
area_min = 100    # 最小面积（像素²）
area_max = 1000   # 最大面积（像素²）
```

#### 适用场景
- 目标轮廓具有特定的尺寸范围
- 需要排除过大或过小的干扰轮廓

#### 优点
- ✅ 过滤噪声和小干扰
- ✅ 适应不同尺度的图像

#### 缺点
- ❌ 需要预先知道目标的大致尺寸
- ❌ 可能匹配到多个轮廓

---

### 4. 综合筛选（高级模式）

#### 参数配置
```python
selection_mode = 'advanced'
shape_filter = 'circle'
area_min = 100
area_max = 1000
confidence_min = 0.9
```

#### 逻辑
```python
def filter_contours(contours, params):
    """综合筛选轮廓"""
    filtered = []
    
    for contour in contours:
        # 形状过滤
        if params.get('shape_filter'):
            if contour['shape_type'] != params['shape_filter']:
                continue
        
        # 面积过滤
        area = contour.get('area', 0)
        if area < params.get('area_min', 0) or area > params.get('area_max', float('inf')):
            continue
        
        # 置信度过滤
        confidence = contour.get('shape_confidence', 0)
        if confidence < params.get('confidence_min', 0):
            continue
        
        filtered.append(contour)
    
    return filtered
```

#### 优点
- ✅ 灵活性最高
- ✅ 精确控制选择条件

#### 缺点
- ❌ 参数配置复杂
- ❌ 可能无匹配结果

---

## 五、数据结构设计

### 输入端口
- **统计数据**（来自ContoursAnalysisNode）：包含完整轮廓信息的字典

### 输出端口
- **模板数据**（结构化字典，黄色/JSON格式）
- **模板预览图像**（标注目标轮廓的BGR图像，绿色）

### 模板数据格式（统一标准）

```json
{
  "metadata": {
    "algorithm": "hu_moments",
    "created_at": "2026-04-28T12:00:00",
    "version": "1.0.0"
  },
  "template_data": {
    "hu_moments": [...],           // 算法特定数据
    "shape_context": {...},        // 或其他算法数据
    "contour_points": [...]        // 原始轮廓点（可选）
  },
  "reference_info": {
    "area": 1234.5,
    "perimeter": 456.7,
    "bounding_rect": {"x": 10, "y": 20, "w": 100, "h": 50},
    "centroid": {"x": 60, "y": 45}
  },
  "source_info": {
    "index": 0,
    "shape_type": "circle",
    "shape_confidence": 0.95
  }
}
```

### 设计说明
1. **分层结构**: metadata（元信息）+ template_data（核心数据）+ reference_info（参考信息）+ source_info（来源信息）
2. **算法无关**: 下游节点通过 `metadata.algorithm` 判断使用哪种匹配算法
3. **向后兼容**: 新增算法时只需扩展 `template_data` 字段

---

## 六、参数配置设计

### 参数组（UI 标签页：properties）

```
【算法选择】
├─ 特征算法: [Hu矩 ▼]
│   ├─ Hu矩 (快速，推荐)
│   ├─ Shape Context (高精度)*
│   └─ Hausdorff距离 (抗遮挡)
└─ * 需要安装opencv-contrib-python

【目标选择】
├─ 选择模式: [按索引 ▼]
│   ├─ 按索引
│   ├─ 按形状类型
│   ├─ 按面积范围
│   └─ 综合筛选
├─ 目标索引: [0          ]  (仅按索引模式)
├─ 形状类型: [circle     ]  (仅按形状模式)
│   ├─ circle
│   ├─ rectangle
│   └─ line
├─ 最小置信度: [0.9      ]  (仅按形状模式)
├─ 最小面积: [100        ]  (仅按面积/综合模式)
├─ 最大面积: [1000       ]  (仅按面积/综合模式)
└─ 最小置信度: [0.9      ]  (仅综合模式)

【高级选项】
├─ 轮廓点采样数: [100     ]  (仅Shape Context)
├─ 径向bins数量: [4       ]  (仅Shape Context)
├─ 角度bins数量: [12      ]  (仅Shape Context)
└─ 内半径比例: [0.1       ]  (仅Shape Context)
```

### 参数说明
| 参数名 | 类型 | 默认值 | 选项 | 说明 |
|--------|------|--------|------|------|
| algorithm | str | 'hu_moments' | hu_moments/shape_context/hausdorff | 特征提取算法 |
| selection_mode | str | 'by_index' | by_index/by_shape/by_area/advanced | 目标选择模式 |
| target_index | int | 0 | 0-999 | 目标轮廓索引 |
| shape_filter | str | 'circle' | circle/rectangle/line | 形状类型过滤 |
| confidence_min | float | 0.9 | 0.0-1.0 | 最小置信度 |
| area_min | float | 100 | 0-999999 | 最小面积 |
| area_max | float | 1000 | 0-999999 | 最大面积 |
| n_sample_points | int | 100 | 50-500 | 轮廓点采样数 |
| n_radial_bins | int | 4 | 2-10 | 径向bins数量 |
| n_angular_bins | int | 12 | 6-36 | 角度bins数量 |
| inner_radius_ratio | float | 0.1 | 0.01-1.0 | 内半径比例 |

---

## 七、异常处理策略

### 1. 无匹配轮廓
```python
if not target_contours:
    self.log_error("❌ 未找到符合条件的轮廓")
    self.log_info("💡 请检查筛选条件是否过于严格")
    return None
```

### 2. 多匹配轮廓
```python
if len(target_contours) > 1:
    self.log_warning(f"⚠️ 找到 {len(target_contours)} 个符合条件的轮廓")
    self.log_info("🔄 自动选择置信度最高的轮廓")
    target = max(target_contours, key=lambda x: x.get('shape_confidence', 0))
```

### 3. 算法依赖缺失
```python
if algorithm == 'shape_context':
    try:
        import cv2.xfeatures2d
    except ImportError:
        self.log_error("❌ Shape Context需要安装opencv-contrib-python")
        self.log_info("💡 安装命令: pip install opencv-contrib-python")
        self.log_info("🔄 已自动切换到Hu矩算法")
        algorithm = 'hu_moments'
```

### 4. 轮廓退化
```python
if len(contour) < 3:
    self.log_error("❌ 轮廓点数不足（至少3个点）")
    return None

if cv2.contourArea(contour) == 0:
    self.log_error("❌ 轮廓面积为0（可能是共线点）")
    return None
```

---

## 八、可视化设计

### 模板预览图像绘制规则

#### 1. 目标轮廓高亮
- 颜色: 红色 (255, 0, 0)
- 线宽: 3（加粗显示）
- 填充: 半透明红色覆盖层（alpha=0.3）

#### 2. 质心标记
- 形状: 十字标记
- 颜色: 黄色 (255, 255, 0)
- 大小: 10像素

#### 3. 信息标注
- 显示内容: 索引、面积、形状类型、置信度
- 位置: 轮廓上方
- 字体: 白色文字 + 黑色背景框

#### 4. 其他轮廓淡化
- 颜色: 灰色 (128, 128, 128)
- 线宽: 1
- 目的: 突出目标轮廓

---

## 九、性能优化策略

### 1. 提前退出
```python
# 若按索引选择且索引无效，直接返回
if selection_mode == 'by_index':
    if target_index >= len(contours):
        self.log_error(f"索引 {target_index} 超出范围（共{len(contours)}个轮廓）")
        return None
```

### 2. 缓存中间结果
```python
# 避免重复计算Hu矩
if not hasattr(self, '_hu_cache'):
    self._hu_cache = {}

contour_key = tuple(contour.flatten())
if contour_key in self._hu_cache:
    return self._hu_cache[contour_key]

hu = cv2.HuMoments(cv2.moments(contour))
self._hu_cache[contour_key] = hu
```

### 3. 并行处理（远期）
```python
# 大量轮廓筛选时使用多线程
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(check_condition, contours))
```

---

## 十、测试用例设计

### 1. 基本功能测试
- **输入**: 10个轮廓的统计数据，选择模式=by_index，target_index=0
- **预期**: 生成Hu矩模板数据，输出非空

### 2. 形状筛选测试
- **输入**: 包含2个圆形、3个矩形、5个直线
- **配置**: selection_mode=by_shape, shape_filter='circle'
- **预期**: 选择置信度最高的圆形

### 3. 面积筛选测试
- **输入**: 轮廓面积分别为50, 200, 500, 1500
- **配置**: selection_mode=by_area, area_min=100, area_max=1000
- **预期**: 选择面积为200和500的轮廓中的一个

### 4. 依赖缺失测试
- **场景**: 未安装opencv-contrib，算法=shape_context
- **预期**: 自动降级为hu_moments，日志提示

### 5. 边界条件测试
- **输入**: 空轮廓列表
- **预期**: 返回None，错误日志提示

### 6. 多结果冲突测试
- **输入**: 3个圆形轮廓，置信度分别为0.85, 0.92, 0.88
- **配置**: confidence_min=0.8
- **预期**: 选择置信度0.92的轮廓

---

## 十一、与后续阶段的衔接

### Phase 5: 模板匹配的基础
- TemplateCreatorNode 生成的模板数据将作为 TemplateMatchNode 的输入
- 模板数据中的 `metadata.algorithm` 决定匹配算法
- 参考信息用于尺度归一化和相似度计算

### Phase 6: 模板库管理（远期）
- 多个模板可保存到文件形成模板库
- 支持模板的分类、检索、批量匹配

---

## 十二、总结

本设计方案遵循以下核心理念：
1. **单一职责**: 专注于模板数据生成，不与轮廓分析耦合
2. **算法可扩展**: 支持Hu矩/Shape Context/Hausdorff三种算法
3. **选择灵活**: 提供4种目标轮廓选择模式
4. **数据标准化**: 统一的JSON格式，便于下游节点解析
5. **容错性强**: 完善的异常处理和降级策略

此设计既满足当前模板创建需求，又为未来的模板库管理和批量匹配功能奠定基础。
