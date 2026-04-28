# 算法节点开发快速参考

> 5分钟速查表 - 常用API、规范和最佳实践

---

## 🚀 快速开始（3步创建节点）

### 1️⃣ 创建目录结构
```bash
mkdir -p src/python/plugin_packages/builtin/my_package/nodes
touch src/python/plugin_packages/builtin/my_package/nodes/__init__.py
touch src/python/plugin_packages/builtin/my_package/plugin.json
touch src/python/plugin_packages/builtin/my_package/nodes/my_node.py
```

### 2️⃣ 编写最小化节点
```python
from shared_libs.node_base import BaseNode
import cv2

class MyNode(BaseNode):
    __identifier__ = 'my_package'  # ⚠️ 与plugin.json的name一致
    NODE_NAME = '我的节点'
    
    def __init__(self):
        super().__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        try:
            if not inputs or not inputs[0]:
                return {'输出图像': None}
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            result = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 你的算法
            return {'输出图像': result}
        except Exception as e:
            self.log_error(f"错误: {e}")
            return {'输出图像': None}
```

### 3️⃣ 配置plugin.json
```json
{
  "name": "my_package",
  "version": "1.0.0",
  "category_group": "预处理",
  "nodes": [{
    "class": "MyNode",
    "display_name": "我的节点",
    "category": "色彩转换"
  }],
  "dependencies": ["opencv-python>=4.5"]
}
```

**刷新插件**: 菜单 → 插件 → 🔄 刷新插件 → **重启应用**

---

## 📚 核心API速查

### 端口操作
```python
# 添加输入端口
self.add_input('端口名称', color=(R, G, B))

# 添加输出端口
self.add_output('端口名称', color=(R, G, B))

# 端口颜色规范
(100, 255, 100)  # 绿色 - 图像数据（最常用）
(100, 100, 255)  # 蓝色 - 数值数据
(255, 255, 100)  # 黄色 - 文本数据
(255, 100, 100)  # 红色 - 布尔/状态
```

### 参数控件
```python
# 添加文本输入框（推荐）
self.add_text_input('param_name', '显示标签', tab='properties')
self.set_property('param_name', '默认值')

# 获取参数值（返回字符串，需转换类型）
value_str = self.get_property('param_name')
value_int = int(self.get_property('param_name'))
value_float = float(self.get_property('param_name'))
```

### 日志输出
```python
self.log_info("信息消息")      # ℹ️ 普通信息
self.log_warning("警告消息")   # ⚠️ 警告
self.log_error("错误消息")     # ❌ 错误
self.log_success("成功消息")   # ✅ 成功
```

### 依赖检查（AI节点）
```python
# 检查Python包
if not self.check_dependencies(['torch', 'ultralytics']):
    return None

# 检查硬件
if not self.check_hardware():
    return None

# 模型缓存
model = self.get_or_load_model('model_key', lambda: load_model())
```

---

## ⚙️ 常用OpenCV算法模板

### 灰度化
```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

### 高斯模糊
```python
blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x)
# kernel_size必须是奇数: 3, 5, 7, 9...
```

### Canny边缘检测
```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, threshold1, threshold2)
edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)  # 转回BGR显示
```

### 阈值二值化
```python
_, binary = cv2.threshold(gray, thresh, maxval, cv2.THRESH_BINARY)
# 其他类型: THRESH_BINARY_INV, THRESH_TRUNC, THRESH_TOZERO
```

### 形态学操作
```python
kernel = np.ones((5, 5), np.uint8)
dilated = cv2.dilate(binary, kernel, iterations=1)   # 膨胀
eroded = cv2.erode(binary, kernel, iterations=1)     # 腐蚀
opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)   # 开运算
closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # 闭运算
```

### 图像缩放
```python
resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
# 插值方法: INTER_NEAREST, INTER_LINEAR, INTER_CUBIC, INTER_AREA
```

### 图像旋转
```python
center = (image.shape[1] // 2, image.shape[0] // 2)
matrix = cv2.getRotationMatrix2D(center, angle, scale)
rotated = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))
```

### 亮度对比度调整
```python
adjusted = cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)
# alpha: 对比度 (0.0-3.0), beta: 亮度 (-100-100)
```

### 轮廓检测
```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = image.copy()
cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
```

---

## 🐛 常见错误与解决

### 错误1: 节点不显示
```
原因: __identifier__ 与 plugin.json 的 name 不一致
解决: 确保两者完全相同（包括大小写）
验证: print(node.__identifier__)  # 应等于 plugin.json["name"]
```

### 错误2: 修改后未生效
```
原因: NodeGraphQt不支持动态刷新
解决: 必须重启应用程序
提示: 新增节点或修改 __identifier__ 后必重启
```

### 错误3: 工程打开后节点丢失
```
原因: 反序列化前节点未注册
解决: 确保 load_plugin_nodes() 在 deserialize_session() 之前调用
检查: 控制台应有 "✅ 注册节点: XXX" 日志
```

### 错误4: 导入错误
```
原因: 模块路径不正确
解决: 
  - 新体系: from user_plugins.package.nodes import MyClass
  - 旧体系: from plugin_package_name_nodes import MyClass
验证: python -m py_compile nodes/my_node.py
```

### 错误5: 参数获取失败
```
原因: get_property() 返回字符串
解决: 手动转换类型
示例: value = int(self.get_property('param'))
```

---

## ✅ 代码检查清单

### 必需项（缺一不可）
- [ ] 继承 `BaseNode`（不是 `NodeGraphQt.BaseNode`）
- [ ] 定义 `__identifier__`（与plugin.json的name一致）
- [ ] 定义 `NODE_NAME`（与plugin.json的display_name一致）
- [ ] 实现 `__init__()` 方法
- [ ] 实现 `process()` 方法
- [ ] process包含try-except
- [ ] 失败时返回None而非抛出异常

### 推荐项（提升质量）
- [ ] 定义 `resource_level` 和 `hardware_requirements`
- [ ] 完整的docstring文档
- [ ] 输入验证（检查None和类型）
- [ ] 参数范围限制
- [ ] 使用 `self.log_*()` 记录日志
- [ ] 端口颜色符合规范

### 禁止项（避免陷阱）
- [ ] ❌ 不要直接修改输入图像（使用 `.copy()`）
- [ ] ❌ 不要在process中抛出异常
- [ ] ❌ 不要硬编码文件路径
- [ ] ❌ 不要忽略输入验证
- [ ] ❌ 不要使用废弃的 `add_slider()`

---

## 📦 节点分类速查

| 分类 | category_group | 典型节点 |
|------|----------------|----------|
| 📷 图像相机 | `"图像相机"` | ImageLoad, ImageSave, CameraCapture |
| 🎨 预处理 | `"预处理"` | Grayscale, GaussianBlur, Resize |
| 🔍 特征提取 | `"特征提取"` | CannyEdge, SobelEdge, BlobDetect |
| 📏 测量分析 | `"测量分析"` | ContourStats, BoundingBox, Distance |
| 🧠 识别分类 | `"识别分类"` | TemplateMatch, OCR, QRCode |
| 🔌 系统集成 | `"系统集成"` | DataExport, PLCComm, MQTT |

---

## 🔧 调试技巧

### 1. 查看节点属性
```python
# 在process方法中添加
print(f"输入类型: {type(inputs)}")
print(f"图像形状: {image.shape}")
print(f"图像 dtype: {image.dtype}")
print(f"参数值: {self.get_property('param')}")
```

### 2. 验证端口连接
```python
# 检查inputs是否为空
if not inputs:
    self.log_warning("没有输入连接")
    return {...}

# 检查具体端口
if inputs[0] is None:
    self.log_warning("第一个端口无数据")
```

### 3. 性能分析
```python
import time
start = time.time()
# ... 你的算法 ...
elapsed = time.time() - start
self.log_info(f"处理耗时: {elapsed*1000:.2f}ms")
```

### 4. 保存中间结果
```python
# 调试时保存图像到文件
cv2.imwrite('/tmp/debug_step1.png', intermediate_result)
```

---

## 🎯 最佳实践总结

### ✅ 应该做的
1. **单一职责**: 每个节点只做一件事
2. **清晰命名**: 类名CamelCase，变量snake_case
3. **完整文档**: docstring说明功能、参数、返回值
4. **防御编程**: 始终验证输入，限制参数范围
5. **友好日志**: 使用log_*()输出关键信息

### ❌ 不应该做的
1. **阻塞UI**: 耗时操作考虑异步处理
2. **内存泄漏**: 及时释放大对象，避免深拷贝
3. **硬编码**: 路径、参数都应可配置
4. **忽略异常**: 捕获并记录所有错误
5. **过度复杂**: 保持节点简单，复杂逻辑拆分为多节点

---

## 📖 相关文档

- 📘 [完整开发指南](NODE_DEVELOPMENT_GUIDE.md)
- 📗 [API参考手册](NODE_API_REFERENCE.md)
- 📙 [开发检查清单](ALGORITHM_NODE_CHECKLIST.md)
- 💡 [高级示例](example_advanced_nodes/)

---

**记住**: 遇到问题先查看控制台日志，90%的问题都能从日志中找到答案！🔍
