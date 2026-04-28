# 轮廓分析数据导出设计理念

## 一、设计目标

为轮廓分析节点增加**结构化数据导出能力**，支持将检测结果保存为多种格式（CSV/Excel/JSON），便于后续统计分析、报告生成和数据归档。

---

## 二、核心设计原则

### 1. 单一综合模式
- **原则**: 在现有 `ContoursAnalysisNode` 中通过参数控制导出行为
- **理由**: 
  - 避免工作流碎片化（不需要额外的"CSV导出节点"）
  - 导出数据与轮廓分析结果天然关联
  - 用户一次配置即可完成分析和导出

### 2. 按需导出
- **原则**: 通过参数开关选择性启用/禁用导出功能
- **实现**:
  ```python
  export_mode = 'memory_only'  # memory_only / csv / excel / json / all
  export_path = ''             # 可选的自定义导出路径
  ```
- **优势**: 默认仅内存输出，需要时才写入文件，减少I/O开销

### 3. 格式标准化
- **原则**: 所有导出格式遵循统一的数据结构
- **示例**:
  ```csv
  Index,Area,Perimeter,Centroid_X,Centroid_Y,BBox_X,BBox_Y,BBox_W,BBox_H,Shape_Type,Confidence
  0,1234.5,456.7,60,45,10,20,100,50,rectangle,0.92
  1,567.8,234.5,120,80,80,50,80,60,circle,0.95
  ```
- **优势**: 不同格式间可互相转换，便于后续处理

### 4. 路径灵活性
- **原则**: 支持相对路径和绝对路径，默认使用工程目录
- **实现**:
  ```python
  # 若未指定路径，使用工程目录下的 exports 文件夹
  default_path = os.path.join(project_dir, 'exports', 'contours_20260428_120000.csv')
  ```
- **优势**: 用户无需手动管理文件位置

---

## 三、导出格式设计

### 1. CSV格式（推荐）

#### 优势
- ✅ 轻量级，无需额外依赖
- ✅ 兼容性强（Excel、Python、MATLAB均可读取）
- ✅ 适合大规模数据（百万行级别）
- ✅ 文本格式，易于版本控制

#### 数据结构
```csv
Index,Area,Perimeter,Centroid_X,Centroid_Y,BBox_X,BBox_Y,BBox_W,BBox_H,Shape_Type,Shape_Confidence,Circle_Radius,Rectangle_Width,Rectangle_Height,Rectangle_Angle,Line_Length,Line_Angle
0,1234.5,456.7,60,45,10,20,100,50,rectangle,0.92,,,,,
1,567.8,234.5,120,80,80,50,80,60,circle,0.95,20,,,,
2,890.1,345.6,50,30,20,10,60,40,line,0.88,,,,,100,45
```

#### 字段说明
| 列名 | 类型 | 说明 | 条件存在 |
|------|------|------|---------|
| Index | int | 轮廓索引 | 始终存在 |
| Area | float | 面积（像素²） | 始终存在 |
| Perimeter | float | 周长（像素） | 始终存在 |
| Centroid_X | int | 质心X坐标 | 始终存在 |
| Centroid_Y | int | 质心Y坐标 | 始终存在 |
| BBox_X | int | 边界框左上角X | 始终存在 |
| BBox_Y | int | 边界框左上角Y | 始终存在 |
| BBox_W | int | 边界框宽度 | 始终存在 |
| BBox_H | int | 边界框高度 | 始终存在 |
| Shape_Type | str | 形状类型 | 始终存在 |
| Shape_Confidence | float | 置信度 | 始终存在 |
| Circle_Radius | int | 圆半径 | shape_type='circle' |
| Rectangle_Width | int | 矩形宽度 | shape_type='rectangle' |
| Rectangle_Height | int | 矩形高度 | shape_type='rectangle' |
| Rectangle_Angle | float | 矩形角度 | shape_type='rectangle' |
| Line_Length | float | 直线长度 | shape_type='line' |
| Line_Angle | float | 直线角度 | shape_type='line' |

#### 注意事项
- 条件字段在不匹配时留空
- 数值保留2位小数（面积、周长等）
- 整数类型不保留小数（坐标、尺寸）

---

### 2. Excel格式（高级）

#### 优势
- ✅ 支持多Sheet（原始数据 + 统计摘要）
- ✅ 内置图表功能（直方图、饼图）
- ✅ 格式化美观（颜色、边框、字体）
- ✅ 适合汇报展示

#### 数据结构
**Sheet 1: 原始数据**
| Index | Area | Perimeter | ... | Shape_Type | Confidence |
|-------|------|-----------|-----|------------|------------|
| 0 | 1234.5 | 456.7 | ... | rectangle | 0.92 |
| 1 | 567.8 | 234.5 | ... | circle | 0.95 |

**Sheet 2: 统计摘要**
| Metric | Value |
|--------|-------|
| Total Count | 10 |
| Filtered Count | 5 |
| Average Area | 890.2 |
| Max Area | 1234.5 |
| Min Area | 567.8 |
| Circle Count | 2 |
| Rectangle Count | 2 |
| Line Count | 1 |

**Sheet 3: 形状分布**
| Shape Type | Count | Percentage |
|------------|-------|------------|
| Circle | 2 | 40% |
| Rectangle | 2 | 40% |
| Line | 1 | 20% |

#### 依赖要求
- 需要安装 `openpyxl` 库
- 若未安装，降级为CSV格式并提示用户

#### 注意事项
- 文件大小较大（相比CSV）
- 不适合超大规模数据（>10万行）
- 需要额外依赖管理

---

### 3. JSON格式（程序化）

#### 优势
- ✅ 完整保留嵌套结构
- ✅ 适合程序间数据交换
- ✅ 支持复杂数据类型（列表、字典）
- ✅ 人类可读（格式化后）

#### 数据结构
```json
{
  "metadata": {
    "export_time": "2026-04-28T12:00:00",
    "total_count": 10,
    "filtered_count": 5,
    "algorithm_version": "1.2.0"
  },
  "contours": [
    {
      "index": 0,
      "area": 1234.5,
      "perimeter": 456.7,
      "bounding_rect": {"x": 10, "y": 20, "w": 100, "h": 50},
      "centroid": {"x": 60, "y": 45},
      "shape_type": "rectangle",
      "shape_confidence": 0.92,
      "rectangle": {
        "center": {"x": 60, "y": 45},
        "width": 100,
        "height": 50,
        "angle": 15.5,
        "corners": [[10,20], [110,20], [110,70], [10,70]],
        "fill_ratio": 0.88
      }
    },
    ...
  ]
}
```

#### 注意事项
- 文件体积较大（冗余键名）
- 不适合直接人工编辑
- 适合API接口数据传输

---

## 四、参数配置设计

### 新增参数组（UI 标签页：properties）

```
【数据导出】
├─ 导出模式: [内存数据 ▼]
│   ├─ 内存数据（默认）
│   ├─ CSV文件
│   ├─ Excel文件
│   ├─ JSON文件
│   └─ 全部格式
├─ 导出路径: (可选，留空则使用默认路径)
└─ 文件名前缀: contours_ (可自定义)
```

### 参数说明
| 参数名 | 类型 | 默认值 | 选项 | 说明 |
|--------|------|--------|------|------|
| export_mode | str | 'memory_only' | memory_only/csv/excel/json/all | 导出模式选择 |
| export_path | str | '' | 任意有效路径 | 自定义导出路径（留空使用默认） |
| filename_prefix | str | 'contours_' | 任意字符串 | 文件名前缀 |

---

## 五、文件命名策略

### 默认命名规则
```
{prefix}{timestamp}_{count}.{ext}

示例:
- contours_20260428_120000_5.csv
- contours_20260428_120000_5.xlsx
- contours_20260428_120000_5.json
```

### 时间戳格式
- 格式: `YYYYMMDD_HHMMSS`
- 示例: `20260428_120000` (2026年4月28日 12:00:00)

### 防冲突机制
- 若文件已存在，自动添加序号后缀
- 示例: `contours_20260428_120000_5_v2.csv`

---

## 六、路径管理策略

### 1. 默认路径计算
```python
def get_default_export_path(self, ext):
    """
    获取默认导出路径
    
    Args:
        ext: 文件扩展名 (.csv/.xlsx/.json)
    
    Returns:
        str: 完整的文件路径
    """
    # 尝试获取工程目录
    project_dir = self.get_project_directory()
    
    if not project_dir:
        # 若无工程目录，使用当前工作目录
        project_dir = os.getcwd()
    
    # 创建 exports 子目录
    export_dir = os.path.join(project_dir, 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    count = self.filtered_count
    filename = f"{self.filename_prefix}{timestamp}_{count}{ext}"
    
    return os.path.join(export_dir, filename)
```

### 2. 自定义路径处理
```python
def resolve_export_path(self, custom_path, ext):
    """
    解析自定义导出路径
    
    Args:
        custom_path: 用户指定的路径（可为相对或绝对）
        ext: 文件扩展名
    
    Returns:
        str: 完整的文件路径
    """
    if not custom_path:
        return self.get_default_export_path(ext)
    
    # 若是相对路径，转换为绝对路径
    if not os.path.isabs(custom_path):
        project_dir = self.get_project_directory() or os.getcwd()
        custom_path = os.path.join(project_dir, custom_path)
    
    # 确保目录存在
    dir_path = os.path.dirname(custom_path)
    os.makedirs(dir_path, exist_ok=True)
    
    # 若用户未指定扩展名，自动添加
    if not custom_path.endswith(ext):
        custom_path += ext
    
    return custom_path
```

### 3. 路径验证
```python
def validate_export_path(self, path):
    """
    验证导出路径是否合法
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # 检查父目录是否存在且可写
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        return False, f"目录不存在: {dir_path}"
    
    if not os.access(dir_path, os.W_OK):
        return False, f"目录不可写: {dir_path}"
    
    # 检查磁盘空间（可选）
    # ...
    
    return True, ""
```

---

## 七、异常处理策略

### 1. 依赖缺失处理
```python
def check_excel_dependency(self):
    """检查Excel导出依赖"""
    try:
        import openpyxl
        return True
    except ImportError:
        self.log_warning("⚠️ Excel导出需要安装openpyxl库")
        self.log_info("💡 安装命令: pip install openpyxl")
        self.log_info("🔄 已自动降级为CSV格式导出")
        return False
```

### 2. 磁盘空间不足
```python
def check_disk_space(self, path):
    """检查磁盘空间"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.path.dirname(path))
        
        # 预估文件大小（CSV约1KB/100行）
        estimated_size = self.filtered_count * 10
        
        if free < estimated_size * 1024:  # 预留10倍余量
            self.log_error(f"磁盘空间不足（剩余{free/1024/1024:.1f}MB）")
            return False
        
        return True
    except Exception as e:
        self.log_warning(f"无法检查磁盘空间: {e}")
        return True  # 保守策略：允许继续
```

### 3. 文件写入失败
```python
def safe_write_file(self, path, content):
    """安全写入文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log_success(f"✅ 文件已导出: {path}")
        return True
    
    except PermissionError:
        self.log_error(f"❌ 权限不足，无法写入: {path}")
        return False
    
    except OSError as e:
        self.log_error(f"❌ 文件写入失败: {e}")
        return False
```

---

## 八、性能优化策略

### 1. 延迟写入
```python
# 仅在process方法执行成功后才导出
result = self.analyze_contours(inputs)

if result and self.export_mode != 'memory_only':
    self.export_data(result)
```

### 2. 批量写入
```python
# CSV写入时使用缓冲
import csv

with open(path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, buffer_size=8192)  # 8KB缓冲
    writer.writerows(all_rows)
```

### 3. 异步导出（远期）
```python
# 大量数据时使用后台线程导出
from concurrent.futures import ThreadPoolExecutor

def export_async(self, data):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(self.export_to_csv, data)
        future.add_done_callback(self.on_export_complete)
```

---

## 九、用户体验设计

### 1. 日志反馈
```python
# 导出开始时
self.log_info(f"📤 开始导出数据 (模式: {self.export_mode})")

# 导出成功
self.log_success(f"✅ 数据已导出到: {export_path}")

# 导出失败
self.log_error(f"❌ 导出失败: {error_message}")
```

### 2. 进度提示（大数据量时）
```python
if self.filtered_count > 1000:
    self.log_info(f"正在导出 {self.filtered_count} 条记录...")
```

### 3. 文件打开提示
```python
# Windows系统自动打开文件
if platform.system() == 'Windows':
    os.startfile(export_path)
    self.log_info("📂 已自动打开文件")
```

---

## 十、测试用例设计

### 1. 基本功能测试
- **输入**: 10个轮廓，导出模式=CSV
- **预期**: 生成CSV文件，包含10行数据

### 2. 空数据处理
- **输入**: 0个轮廓，导出模式=CSV
- **预期**: 生成空CSV文件（仅表头），不报错

### 3. 路径测试
- **相对路径**: `exports/test.csv` → 正确解析
- **绝对路径**: `C:\data\test.csv` → 正确写入
- **无效路径**: `/invalid/path/test.csv` → 友好错误提示

### 4. 依赖缺失测试
- **场景**: 未安装openpyxl，导出模式=Excel
- **预期**: 自动降级为CSV，日志提示安装方法

### 5. 文件冲突测试
- **场景**: 同名文件已存在
- **预期**: 自动添加版本号后缀（_v2, _v3...）

### 6. 大数据量测试
- **输入**: 10000个轮廓
- **预期**: 
  - CSV导出时间 < 5秒
  - 文件大小 < 10MB
  - 内存占用稳定

---

## 十一、与后续阶段的衔接

### Phase 4: 模板创建的基础
- 导出的统计数据可作为模板匹配的参考依据
- 例如：筛选出高置信度的圆形作为模板候选

### Phase 5: 数据可视化的基础
- CSV/Excel文件可直接导入Excel进行图表制作
- JSON文件可用于Web前端可视化

---

## 十二、总结

本设计方案遵循以下核心理念：
1. **按需导出**: 默认仅内存输出，减少不必要的I/O开销
2. **格式灵活**: 支持CSV/Excel/JSON三种主流格式
3. **路径智能**: 自动管理默认路径，支持自定义覆盖
4. **容错性强**: 完善的异常处理和降级策略
5. **用户友好**: 清晰的日志反馈和自动化操作

此设计既满足日常数据分析需求，又为后续的高级功能（如云端同步、数据库存储）奠定基础。
