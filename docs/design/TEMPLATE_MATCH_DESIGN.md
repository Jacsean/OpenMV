# 轮廓模板匹配设计理念

## 一、设计目标

创建**模板匹配节点（TemplateMatchNode）**，基于预生成的模板数据在输入图像中搜索匹配的轮廓，实现形状识别和定位功能。

---

## 二、核心设计原则

### 1. 算法一致性
- **原则**: 匹配算法必须与模板创建时使用的算法一致
- **实现**: 从模板数据的 `metadata.algorithm` 字段读取算法类型
- **理由**: 
  - Hu矩模板只能用Hu矩匹配
  - Shape Context模板只能用Shape Context匹配
  - 避免算法不匹配导致的错误结果

### 2. 手动选择算法
- **原则**: 用户通过参数下拉菜单明确选择匹配算法
- **理由**: 
  - 保持简洁，不提供自动推荐功能
  - 用户根据场景需求自主选择
  - 符合"分阶段实施、手动选择算法"的设计要求

### 3. 相似度阈值控制
- **原则**: 提供可配置的相似度阈值过滤低质量匹配
- **实现**: 
  ```python
  similarity_threshold = 0.8  # 0.0-1.0
  ```
- **优势**: 平衡召回率和精确率

### 4. 多结果输出
- **原则**: 支持返回多个匹配结果，按相似度排序
- **实现**: 
  ```python
  max_results = 10  # 最多返回10个匹配
  ```
- **优势**: 适应复杂场景（多个相同形状的物体）

---

## 三、支持的匹配算法

### 1. Hu矩匹配（基础版）

#### 原理
- 计算模板Hu矩与候选轮廓Hu矩之间的距离
- 使用欧氏距离或相关系数度量相似度
- OpenCV API: `cv2.matchShapes()`

#### 相似度计算
```python
similarity = cv2.matchShapes(template_contour, candidate_contour, cv2.CONTOURS_MATCH_I1)
# 返回值越小表示越相似，需转换为0-1范围
normalized_similarity = 1 / (1 + distance)
```

#### 适用场景
- ✅ 形状规则、旋转/缩放不变性要求高
- ✅ 计算速度快（毫秒级）
- ✅ 适合实时检测

#### 性能特点
- 速度: ⚡⚡⚡ 极快
- 精度: ⭐⭐⭐ 中等
- 抗遮挡: ⭐⭐ 较弱
- 抗形变: ⭐⭐ 较弱

---

### 2. Shape Context匹配（高级版）

#### 原理
- 基于形状上下文的距离度量
- OpenCV contrib API: `cv2.xfeatures2d.ShapeContextDistanceExtractor`
- 类似Halcon的shape-based matching

#### 相似度计算
```python
sc_extractor = cv2.xfeatures2d.createShapeContextDistanceExtractor()
distance = sc_extractor.computeDistance(template_contour, candidate_contour)
# 距离值越小表示越相似
normalized_similarity = 1 / (1 + distance)
```

#### 适用场景
- ✅ 复杂形状、需要高精度匹配
- ✅ 对形变有一定容忍度
- ❌ 需要opencv-contrib-python依赖

#### 性能特点
- 速度: ⚡ 较慢（秒级）
- 精度: ⭐⭐⭐⭐⭐ 极高
- 抗遮挡: ⭐⭐⭐⭐ 强
- 抗形变: ⭐⭐⭐⭐ 强

---

### 3. Hausdorff距离匹配（进阶版）

#### 原理
- 基于点集之间的最大最小距离
- OpenCV API: `cv2.createHausdorffDistanceExtractor()`
- 对部分遮挡和噪声有较强鲁棒性

#### 相似度计算
```python
hd_extractor = cv2.createHausdorffDistanceExtractor()
distance = hd_extractor.computeDistance(template_points, candidate_points)
# 归一化处理
normalized_distance = distance / normalization_factor
normalized_similarity = 1 / (1 + normalized_distance)
```

#### 适用场景
- ✅ 部分遮挡情况
- ✅ 不完整轮廓匹配
- ✅ 不规则形状

#### 性能特点
- 速度: ⚡⚡ 较快
- 精度: ⭐⭐⭐⭐ 较高
- 抗遮挡: ⭐⭐⭐⭐⭐ 极强
- 抗形变: ⭐⭐⭐ 中等

---

## 四、匹配流程设计

### 1. 输入验证
```python
# 检查模板数据有效性
if not template_data or 'metadata' not in template_data:
    self.log_error("❌ 模板数据格式错误")
    return None

# 检查算法一致性
template_algorithm = template_data['metadata']['algorithm']
if template_algorithm != selected_algorithm:
    self.log_warning(f"⚠️ 模板算法({template_algorithm})与选择算法({selected_algorithm})不一致")
    self.log_info("🔄 已自动切换到模板算法")
    selected_algorithm = template_algorithm
```

### 2. 轮廓提取
```python
# 从输入图像提取轮廓
gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY) if len(input_image.shape) == 3 else input_image.copy()
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

### 3. 逐个匹配
```python
match_results = []

for contour in contours:
    # 面积过滤（可选）
    area = cv2.contourArea(contour)
    if area < min_area or area > max_area:
        continue
    
    # 执行匹配
    similarity = self._compute_similarity(template_data, contour, algorithm)
    
    # 阈值过滤
    if similarity >= similarity_threshold:
        match_results.append({
            'contour': contour,
            'similarity': similarity,
            'bounding_rect': cv2.boundingRect(contour),
            'centroid': self._compute_centroid(contour)
        })
```

### 4. 结果排序
```python
# 按相似度降序排序
match_results.sort(key=lambda x: x['similarity'], reverse=True)

# 限制返回数量
match_results = match_results[:max_results]
```

### 5. 标注图像绘制
```python
annotated_image = input_image.copy()

for i, result in enumerate(match_results):
    # 绘制轮廓
    color = self._get_color_by_rank(i)  # 不同排名不同颜色
    cv2.drawContours(annotated_image, [result['contour']], -1, color, 2)
    
    # 绘制质心
    centroid = result['centroid']
    cv2.circle(annotated_image, (int(centroid['x']), int(centroid['y'])), 5, color, -1)
    
    # 标注相似度
    text = f"{result['similarity']:.2f}"
    cv2.putText(annotated_image, text, (int(centroid['x'])+10, int(centroid['y'])),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
```

---

## 五、数据结构设计

### 输入端口
- **输入图像**（BGR彩色图像，绿色）
- **模板数据**（来自TemplateCreatorNode，黄色/JSON格式）

### 输出端口
- **标注图像**（绘制匹配结果的BGR图像，绿色）
- **匹配数量**（int类型，蓝色）
- **匹配结果列表**（结构化字典列表，黄色/JSON格式）

### 匹配结果数据格式

```json
{
  "match_count": 3,
  "matches": [
    {
      "rank": 1,
      "similarity": 0.95,
      "bounding_rect": {"x": 100, "y": 150, "w": 80, "h": 60},
      "centroid": {"x": 140, "y": 180},
      "area": 4500.5,
      "perimeter": 280.3
    },
    {
      "rank": 2,
      "similarity": 0.88,
      "bounding_rect": {"x": 300, "y": 200, "w": 75, "h": 55},
      "centroid": {"x": 337, "y": 227},
      "area": 4100.2,
      "perimeter": 265.8
    }
  ]
}
```

---

## 六、参数配置设计

### 参数组（UI 标签页：properties）

```
【匹配算法】
├─ 匹配算法: [Hu矩 ▼]
│   ├─ Hu矩 (快速，推荐)
│   ├─ Hausdorff距离 (抗遮挡)
│   └─ Shape Context (高精度)*
└─ * 需要安装opencv-contrib-python

【筛选条件】
├─ 相似度阈值: [0.8      ]  (0.0-1.0)
├─ 最小面积: [0          ]  (像素²)
├─ 最大面积: [999999     ]  (像素²)
└─ 最大匹配数: [10       ]  (1-100)

【显示选项】
├─ 绘制轮廓: [True      ]
├─ 绘制质心: [True      ]
├─ 标注相似度: [True    ]
├─ 第1名颜色-R: [0      ]  (默认绿色)
├─ 第1名颜色-G: [255    ]
├─ 第1名颜色-B: [0      ]
├─ 第2名颜色-R: [255    ]  (默认黄色)
├─ 第2名颜色-G: [255    ]
└─ 第2名颜色-B: [0      ]
```

### 参数说明
| 参数名 | 类型 | 默认值 | 选项 | 说明 |
|--------|------|--------|------|------|
| algorithm | str | 'hu_moments' | hu_moments/hausdorff/shape_context | 匹配算法 |
| similarity_threshold | float | 0.8 | 0.0-1.0 | 相似度阈值 |
| min_area | float | 0 | 0-999999 | 最小面积过滤 |
| max_area | float | 999999 | 0-999999 | 最大面积过滤 |
| max_results | int | 10 | 1-100 | 最多返回匹配数 |
| draw_contours | bool | True | True/False | 是否绘制轮廓 |
| draw_centroids | bool | True | True/False | 是否绘制质心 |
| annotate_similarity | bool | True | True/False | 是否标注相似度 |

---

## 七、异常处理策略

### 1. 模板数据缺失
```python
if not template_data:
    self.log_error("❌ 未接收到模板数据")
    return None
```

### 2. 算法依赖缺失
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

### 3. 无匹配结果
```python
if not match_results:
    self.log_warning("⚠️ 未找到符合条件的匹配")
    self.log_info(f"   相似度阈值: {similarity_threshold}")
    self.log_info(f"   共检测 {len(contours)} 个轮廓")
```

### 4. 模板与图像尺度差异过大
```python
template_area = template_data['reference_info']['area']
candidate_area = cv2.contourArea(contour)

scale_ratio = candidate_area / template_area if template_area > 0 else 1

if scale_ratio < 0.1 or scale_ratio > 10:
    self.log_warning(f"⚠️ 尺度差异过大 ({scale_ratio:.2f}x)，可能影响匹配精度")
```

---

## 八、可视化设计

### 标注图像绘制规则

#### 1. 匹配轮廓
- **第1名**: 绿色 (0, 255, 0)，线宽3
- **第2名**: 黄色 (255, 255, 0)，线宽2
- **第3名及以后**: 橙色 (255, 165, 0)，线宽2

#### 2. 质心标记
- 形状: 实心圆
- 半径: 5像素
- 颜色: 与轮廓颜色一致

#### 3. 相似度标注
- 位置: 质心右侧10像素
- 字体: 白色文字 + 黑色描边
- 格式: `0.95`（保留2位小数）

#### 4. 排名标识
- 第1名: 添加金色星标 ⭐
- 第2-3名: 添加银色星标
- 其他: 无标识

---

## 九、性能优化策略

### 1. 提前过滤
```python
# 面积预过滤，减少匹配计算量
for contour in contours:
    area = cv2.contourArea(contour)
    if area < min_area or area > max_area:
        continue  # 跳过，不进行匹配计算
```

### 2. 缓存中间结果
```python
# 缓存Hu矩计算结果
if not hasattr(self, '_hu_cache'):
    self._hu_cache = {}

contour_key = tuple(contour.flatten())
if contour_key in self._hu_cache:
    hu_moments = self._hu_cache[contour_key]
else:
    hu_moments = cv2.HuMoments(cv2.moments(contour))
    self._hu_cache[contour_key] = hu_moments
```

### 3. 并行匹配（远期）
```python
# 大量轮廓时使用多线程并行匹配
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    similarities = list(executor.map(compute_similarity, contours))
```

---

## 十、测试用例设计

### 1. 基本功能测试
- **输入**: 包含3个圆形的图像 + 圆形模板
- **配置**: algorithm=hu_moments, similarity_threshold=0.8
- **预期**: 返回3个匹配结果，相似度>0.8

### 2. 阈值过滤测试
- **输入**: 5个轮廓，相似度分别为0.95, 0.88, 0.75, 0.62, 0.50
- **配置**: similarity_threshold=0.8
- **预期**: 仅返回前2个匹配（0.95和0.88）

### 3. 算法切换测试
- **场景**: 同一模板分别用Hu矩/Hausdorff/Shape Context匹配
- **预期**: 
  - Hu矩: 速度快，精度中等
  - Hausdorff: 速度中等，精度高
  - Shape Context: 速度慢，精度最高

### 4. 依赖缺失测试
- **场景**: 未安装opencv-contrib，算法=shape_context
- **预期**: 自动降级为hu_moments，日志提示

### 5. 无匹配测试
- **输入**: 矩形图像 + 圆形模板
- **配置**: similarity_threshold=0.9
- **预期**: 返回空列表，警告日志

### 6. 多结果排序测试
- **输入**: 10个相同形状的轮廓
- **配置**: max_results=5
- **预期**: 返回相似度最高的5个，按降序排列

---

## 十一、与后续阶段的衔接

### Phase 6: Shape Context集成优化
- 当前Phase 5已预留Shape Context接口
- Phase 6将重点优化Shape Context的性能和精度
- 包括参数调优、采样策略改进等

### Phase 7: 示例工作流
- 创建完整的模板匹配工作流示例
- 展示从轮廓分析→模板创建→模板匹配的完整流程
- 提供典型应用场景的最佳实践

---

## 十二、总结

本设计方案遵循以下核心理念：
1. **算法一致性**: 匹配算法与模板创建算法保持一致
2. **手动选择**: 用户通过参数明确选择算法，无自动推荐
3. **阈值控制**: 提供相似度阈值过滤低质量匹配
4. **多结果输出**: 支持返回多个匹配结果并排序
5. **容错性强**: 完善的异常处理和降级策略

此设计既满足当前模板匹配需求，又为未来的Shape Context优化和示例工作流奠定基础。
