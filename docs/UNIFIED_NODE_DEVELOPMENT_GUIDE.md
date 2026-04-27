from ....base_nodes import BaseNode
import cv2


class MyOpenCVNode(BaseNode):
    """我的 OpenCV 节点"""
    
    __identifier__ = 'my_plugin'
    NODE_NAME = '我的节点'
    
    def __init__(self):
        super(MyOpenCVNode, self).__init__()
        # 定义输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        # 定义输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        # 定义参数
        self.add_text_input('param1', '参数1', tab='properties')
        self.set_property('param1', 'default_value')
    
    def process(self, inputs=None):
        """处理逻辑"""
        try:
            # 1. 获取输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 2. 获取参数
            param1 = self.get_property('param1')
            
            # 3. 执行处理
            result = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 4. 返回结果
            return {'输出图像': result}
        
        except Exception as e:
            print(f"错误: {e}")
            return {'输出图像': None}
```

### 4.2 AIBaseNode（AI 节点）

**适用场景**：
- 轻量级 AI 推理（OCR、目标检测等）
- 模型训练、量化等重量级任务

**特点**：
- ✅ 依赖检查（自动验证 Python 包）
- ✅ 硬件检查（CPU/GPU/内存）
- ✅ 模型缓存管理
- ✅ 统一日志输出
- ✅ 资源等级声明

**示例**：

```python
from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class MyAINode(AIBaseNode):
    """我的 AI 节点"""
    
    __identifier__ = 'my_plugin'
    NODE_NAME = 'AI 推理节点'
    resource_level = "light"  # light / medium / heavy
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(MyAINode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_text_input('model_path', '模型路径', tab='properties')
        self.set_property('model_path', '')
    
    def process(self, inputs=None):
        """处理逻辑"""
        try:
            # 1. 前置检查（自动执行）
            # - 依赖检查
            # - 硬件检查
            
            # 2. 获取输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("无输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 3. 加载模型（带缓存）
            model_path = self.get_property('model_path')
            model = self.load_model(model_path)
            
            # 4. 执行推理
            self.log_info("开始推理...")
            result = model.predict(image)
            
            # 5. 返回结果
            self.log_success("推理完成")
            return {'输出图像': result}
        
        except Exception as e:
            self.log_error(f"推理失败: {e}")
            return {'输出图像': None}
```

### 4.3 AsyncAINode（异步 AI 节点）

**适用场景**：
- 耗时 AI 推理（> 1s）
- 需要支持取消的任务

**特点**：
- ✅ 继承 `AIBaseNode` 所有功能
- ✅ 异步执行（不阻塞 UI）
- ✅ 支持任务取消
- ✅ 进度回调

**示例**：

```python
from ....base_nodes import AsyncAINode
import asyncio


class MyAsyncNode(AsyncAINode):
    """我的异步 AI 节点"""
    
    __identifier__ = 'my_plugin'
    NODE_NAME = '异步 AI 节点'
    resource_level = "heavy"
    hardware_requirements = {
        'cpu_cores': 8,
        'memory_gb': 16,
        'gpu_required': True,
        'gpu_memory_gb': 8
    }
    
    async def async_process(self, inputs=None):
        """异步处理逻辑"""
        try:
            # 1. 获取输入
            image = inputs[0][0] if inputs and inputs[0] else None
            
            # 2. 执行耗时任务（支持取消）
            for i in range(100):
                if self.is_cancelled():
                    self.log_warning("任务已取消")
                    return {'输出图像': None}
                
                # 模拟耗时操作
                await asyncio.sleep(0.1)
                
                # 更新进度
                self.update_progress(i + 1, 100)
            
            # 3. 返回结果
            return {'输出图像': image}
        
        except Exception as e:
            self.log_error(f"任务失败: {e}")
            return {'输出图像': None}
```

---

## 5. 开发传统 OpenCV 节点

### 5.1 节点类结构

```python
from ....base_nodes import BaseNode
import cv2
import numpy as np


class GrayscaleNode(BaseNode):
    """灰度化节点"""
    
    # 必需：插件标识符
    __identifier__ = 'preprocessing'
    
    # 必需：节点显示名称
    NODE_NAME = '灰度化'
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        
        # 定义输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 定义输出端口
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        """
        处理逻辑
        
        Args:
            inputs: 输入数据列表，每个元素是一个端口的数据
        
        Returns:
            dict: 输出端口名称 -> 数据的映射
        """
        try:
            # 1. 验证输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            # 2. 提取图像数据
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 3. 执行灰度化
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 4. 转换为 BGR 格式（保持兼容性）
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # 5. 返回结果
            return {'输出图像': gray_bgr}
        
        except Exception as e:
            print(f"灰度化处理错误: {e}")
            return {'输出图像': None}
```

### 5.2 添加参数控件

```python
def __init__(self):
    super().__init__()
    
    # 文本输入框
    self.add_text_input('threshold', '阈值', tab='properties')
    self.set_property('threshold', '127')
    
    # 下拉选择框
    items = ['固定阈值', '自适应阈值']
    self.add_combo_menu('method', '方法', items=items, tab='properties')
    
    # 滑块（需要自定义 Widget）
    # 参考 NodeGraphQt 文档
```

### 5.3 多输入/多输出

```python
def __init__(self):
    super().__init__()
    
    # 多个输入
    self.add_input('图像1', color=(100, 255, 100))
    self.add_input('图像2', color=(100, 255, 100))
    
    # 多个输出
    self.add_output('混合结果', color=(100, 255, 100))
    self.add_output('差异图', color=(100, 255, 100))

def process(self, inputs=None):
    image1 = inputs[0][0] if inputs and inputs[0] else None
    image2 = inputs[1][0] if inputs and len(inputs) > 1 and inputs[1] else None
    
    # 处理逻辑...
    
    return {
        '混合结果': blended,
        '差异图': diff
    }
```

---

## 6. 开发 AI 节点

### 6.1 AIBaseNode 核心功能

#### 6.1.1 依赖检查

在 `plugin.json` 中声明依赖：

```json
{
  "dependencies": [
    "opencv-python>=4.5.0",
    "numpy>=1.20.0"
  ],
  "optional_dependencies": {
    "gpu": [
      "torch --index-url https://download.pytorch.org/whl/cu118"
    ]
  }
}
```

节点会自动检查依赖是否安装。

#### 6.1.2 硬件检查

在节点类中声明硬件要求：

```python
resource_level = "medium"
hardware_requirements = {
    'cpu_cores': 4,
    'memory_gb': 8,
    'gpu_required': True,
    'gpu_memory_gb': 4,
    'cuda_version': '11.8'  # 可选
}
```

系统会在运行前检查硬件是否满足要求。

#### 6.1.3 模型缓存

使用 `load_model()` 方法自动管理模型缓存：

```python
def process(self, inputs=None):
    model_path = self.get_property('model_path')
    
    # 自动缓存，第二次调用直接返回
    model = self.load_model(model_path)
    
    # 使用模型...
```

#### 6.1.4 统一日志

```python
self.log_info("信息消息")
self.log_warning("警告消息")
self.log_error("错误消息")
self.log_success("成功消息")
```

### 6.2 完整示例：YOLO 目标检测

```python
from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class YOLODetectNode(AIBaseNode):
    """YOLO 目标检测节点"""
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 目标检测'
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(YOLODetectNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('检测结果', color=(100, 255, 100))
        
        self.add_text_input('model_path', '模型路径', tab='properties')
        self.set_property('model_path', 'yolov8n.pt')
        
        self.add_text_input('confidence', '置信度阈值', tab='properties')
        self.set_property('confidence', '0.5')
    
    def process(self, inputs=None):
        try:
            # 1. 获取输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("无输入图像")
                return {'输出图像': None, '检测结果': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 2. 加载模型
            model_path = self.get_property('model_path')
            confidence = float(self.get_property('confidence'))
            
            from ultralytics import YOLO
            model = self.load_model(model_path, lambda: YOLO(model_path))
            
            # 3. 执行推理
            self.log_info(f"开始检测 (conf={confidence})...")
            results = model(image, conf=confidence, verbose=False)
            
            # 4. 解析结果
            annotated_image = results[0].plot()
            detections = []
            for box in results[0].boxes:
                detections.append({
                    'class': int(box.cls[0]),
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                })
            
            # 5. 返回结果
            self.log_success(f"检测到 {len(detections)} 个目标")
            return {
                '输出图像': annotated_image,
                '检测结果': detections
            }
        
        except Exception as e:
            self.log_error(f"检测失败: {e}")
            return {'输出图像': None, '检测结果': None}
```

### 6.3 AsyncAINode 示例：模型训练

```python
from ....base_nodes import AsyncAINode
import asyncio


class YOLOTrainerNode(AsyncAINode):
    """YOLO 模型训练节点"""
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 模型训练'
    resource_level = "heavy"
    hardware_requirements = {
        'cpu_cores': 8,
        'memory_gb': 16,
        'gpu_required': True,
        'gpu_memory_gb': 8
    }
    
    async def async_process(self, inputs=None):
        try:
            # 1. 获取参数
            dataset_path = self.get_property('dataset_path')
            epochs = int(self.get_property('epochs'))
            
            # 2. 初始化训练器
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')
            
            # 3. 执行训练（支持取消和进度更新）
            self.log_info(f"开始训练 ({epochs} epochs)...")
            
            for epoch in range(epochs):
                if self.is_cancelled():
                    self.log_warning("训练已取消")
                    return {'训练结果': None}
                
                # 训练一个 epoch
                results = model.train(
                    data=dataset_path,
                    epochs=1,
                    resume=(epoch > 0)
                )
                
                # 更新进度
                self.update_progress(epoch + 1, epochs)
                self.log_info(f"Epoch {epoch + 1}/{epochs} 完成")
            
            # 4. 返回结果
            self.log_success("训练完成")
            return {'训练结果': results}
        
        except Exception as e:
            self.log_error(f"训练失败: {e}")
            return {'训练结果': None}
```

---

## 7. plugin.json 配置规范

### 7.1 完整示例

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "插件功能描述",
  "category_group": "分类组名称",
  
  "nodes": [
    {
      "class": "MyNodeClass",
      "display_name": "节点显示名称",
      "category": "子分类",
      "color": [255, 200, 100],
      
      "resource_level": "light",
      "hardware_requirements": {
        "cpu_cores": 2,
        "memory_gb": 2,
        "gpu_required": false,
        "gpu_memory_gb": 0
      },
      
      "dependencies": [
        "opencv-python>=4.5.0"
      ],
      "optional_dependencies": {}
    }
  ],
  
  "dependencies": [],
  "min_app_version": "4.0.0",
  
  "resource_level": "light",
  "hardware_recommendations": {
    "factory_deployment": "适合工厂现场部署",
    "office_workstation": "适合办公室工作站",
    "cloud_training": "是否需要云端训练"
  }
}
```

### 7.2 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 插件唯一标识符 |
| `version` | string | ✅ | 版本号（语义化版本） |
| `author` | string | ✅ | 作者名称 |
| `description` | string | ✅ | 插件功能描述 |
| `category_group` | string | ✅ | 节点分类组 |
| `nodes` | array | ✅ | 节点列表 |
| `nodes[].class` | string | ✅ | 节点类名 |
| `nodes[].display_name` | string | ✅ | 节点显示名称 |
| `nodes[].category` | string | ✅ | 节点子分类 |
| `nodes[].color` | array | ✅ | RGB 颜色值 [R, G, B] |
| `nodes[].resource_level` | string | 推荐 | 资源等级：light/medium/heavy |
| `nodes[].hardware_requirements` | object | 推荐 | 硬件要求 |
| `dependencies` | array | 推荐 | 全局依赖列表 |
| `min_app_version` | string | 推荐 | 最低应用版本 |

### 7.3 资源等级定义

| 等级 | CPU | 内存 | GPU | 典型场景 |
|------|-----|------|-----|---------|
| `light` | 1-2 核 | 1-2 GB | 不需要 | 图像处理、轻量推理 |
| `medium` | 4 核 | 4-8 GB | 可选 | 中等模型推理 |
| `heavy` | 8+ 核 | 16+ GB | 必需 | 模型训练、量化 |

---

## 8. 最佳实践

### 8.1 代码组织

✅ **推荐**：
```
plugin_name/
├── nodes/
│   ├── inference/      # 推理节点
│   ├── training/       # 训练节点
│   └── annotation/     # 标注节点
```

❌ **不推荐**：
```
plugin_name/
└── nodes.py            # 所有节点在一个文件
```

### 8.2 错误处理

✅ **推荐**：
```python
def process(self, inputs=None):
    try:
        # 验证输入
        if not inputs or not inputs[0]:
            self.log_warning("无输入数据")
            return {'output': None}
        
        # 处理逻辑
        result = self.do_something(inputs[0])
        
        # 验证输出
        if result is None:
            self.log_error("处理结果为空")
            return {'output': None}
        
        return {'output': result}
    
    except Exception as e:
        self.log_error(f"处理失败: {e}")
        return {'output': None}
```

❌ **不推荐**：
```python
def process(self, inputs=None):
    # 没有任何错误处理
    result = do_something(inputs[0])
    return {'output': result}
```

### 8.3 日志使用

✅ **推荐**：
```python
self.log_info("开始处理...")
self.log_info(f"参数: threshold={threshold}")
self.log_warning("输入图像为空，跳过处理")
self.log_error(f"处理失败: {str(e)}")
self.log_success("处理完成，耗时: 0.5s")
```

❌ **不推荐**：
```python
print("开始处理")
print("出错了:", e)
```

### 8.4 性能优化

✅ **推荐**：
```python
# 使用模型缓存
model = self.load_model(path, loader_func)

# 避免重复计算
if hasattr(self, '_cached_result'):
    return self._cached_result
```

❌ **不推荐**：
```python
# 每次都重新加载模型
model = load_model(path)

# 重复计算
result = expensive_computation()
result = expensive_computation()
```

---

## 9. 常见问题

### Q1: 如何调试节点？

**A**: 在节点的 `process()` 方法中添加日志：

```python
def process(self, inputs=None):
    self.log_info(f"输入类型: {type(inputs)}")
    self.log_info(f"输入形状: {inputs[0].shape if inputs else 'None'}")
    
    # ... 处理逻辑
    
    self.log_info(f"输出形状: {result.shape}")
    return {'output': result}
```

### Q2: 如何处理大图像？

**A**: 使用分块处理或降采样：

```python
def process(self, inputs=None):
    image = inputs[0][0]
    
    # 如果图像太大，先降采样
    if image.shape[0] > 2000 or image.shape[1] > 2000:
        scale = 2000 / max(image.shape[:2])
        image = cv2.resize(image, None, fx=scale, fy=scale)
    
    # 处理...
```

### Q3: 如何添加自定义 UI 控件？

**A**: 参考 NodeGraphQt 文档，创建自定义 Widget：

```python
from NodeGraphQt import NodeWidget

class MyCustomWidget(NodeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建自定义 UI...
```

### Q4: 节点加载失败怎么办？

**A**: 检查以下几点：
1. `plugin.json` 格式是否正确
2. 节点类是否在 `__init__.py` 中导出
3. 是否有语法错误
4. 依赖是否已安装

查看控制台日志获取详细错误信息。

---

## 10. 迁移指南

### 10.1 从旧体系迁移到新体系

**步骤 1**：创建目录结构

```bash
mkdir my_plugin/nodes
```

**步骤 2**：拆分 `nodes.py` 为独立文件

```
nodes.py → nodes/node1.py, nodes/node2.py, ...
```

**步骤 3**：创建 `nodes/__init__.py`

```python
from .node1 import NodeClass1
from .node2 import NodeClass2

__all__ = ['NodeClass1', 'NodeClass2']
```

**步骤 4**：创建插件根目录的 `__init__.py`

```python
from .nodes import *
```

**步骤 5**：删除旧的 `nodes.py`

```bash
rm my_plugin/nodes.py
```

**步骤 6**：验证迁移

```bash
python tests/verify_all_plugins_migration.py
```

### 10.2 从 BaseNode 升级到 AIBaseNode

**步骤 1**：修改导入

```python
# 旧
from ....base_nodes import BaseNode

# 新
from ....base_nodes import AIBaseNode
```

**步骤 2**：添加资源声明

```python
class MyNode(AIBaseNode):
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
```

**步骤 3**：使用统一日志

```python
# 旧
print("信息")

# 新
self.log_info("信息")
```

**步骤 4**：更新 plugin.json

在节点配置中添加：

```json
{
  "resource_level": "light",
  "hardware_requirements": {...},
  "dependencies": [...]
}
```

---

## 📚 相关文档

- [插件迁移教程](PLUGIN_MIGRATION_TUTORIAL.md)
- [端到端工作流指南](END_TO_END_WORKFLOW_GUIDE.md)
- [AI 模块资源隔离设计](AI_MODULE_RESOURCE_ISOLATION.md)

---

**最后更新**: 2026-04-27  
**维护者**: StduyOpenCV 开发团队
