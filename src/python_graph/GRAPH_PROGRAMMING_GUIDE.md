# 图形化视觉编程系统 - 项目说明

## 🎯 项目概述

本项目成功将原有的OpenCV视觉系统升级为**图形化编程框架**，实现了类似海康VM、基恩士CV-X、康耐视VisionPro等工业视觉软件的可视化编程体验。

---

## ✨ 核心特性

### 1. 可视化节点编程
- **拖拽式编辑**: 从节点库拖拽节点到画布
- **端口连接**: 点击并拖动连接线建立数据流
- **直观界面**: 清晰的工作流可视化

### 2. 模块化架构
```
nodes/          # 节点定义（算法封装）
core/           # 核心引擎（执行逻辑）
ui/             # 用户界面（交互展示）
```

### 3. 实时执行引擎
- **拓扑排序**: 自动计算节点执行顺序
- **依赖管理**: 处理节点间的数据依赖
- **错误处理**: 完善的异常捕获机制

### 4. 工作流管理
- **保存**: 导出为JSON格式
- **加载**: 导入已保存的工作流
- **复用**: 快速重用已有流程

---

## 📦 技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **节点图框架** | NodeGraphQt | 0.6.30+ | 可视化节点编辑 |
| **GUI框架** | PySide2 | 5.15.0+ | 图形界面 |
| **图像处理** | OpenCV | 4.5.0+ | 图像算法 |
| **数值计算** | NumPy | 1.19.0+ | 数组操作 |
| **图像IO** | Pillow | 8.0.0+ | 图像显示 |

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│          UI Layer (PySide2)             │
│  ┌──────────┬──────────┬──────────────┐ │
│  │ 节点库   │ 节点画布  │  属性面板     │ │
│  └──────────┴──────────┴──────────────┘ │
└────────────────┬────────────────────────┘
                 │ 用户交互
┌────────────────▼────────────────────────┐
│      Graph Engine (执行引擎)            │
│  ┌──────────────────────────────────┐   │
│  │  拓扑排序 → 节点调度 → 数据流    │   │
│  └──────────────────────────────────┘   │
└────────────────┬────────────────────────┘
                 │ 调用
┌────────────────▼────────────────────────┐
│       Nodes (节点层)                     │
│  ┌──────┬──────────┬─────────────────┐  │
│  │ IO   │Processing│   Display       │  │
│  │节点  │  节点     │   节点          │  │
│  └──────┴──────────┴─────────────────┘  │
└────────────────┬────────────────────────┘
                 │ 使用
┌────────────────▼────────────────────────┐
│      OpenCV (算法层)                     │
│  灰度化、模糊、边缘检测、二值化等         │
└─────────────────────────────────────────┘
```

### 数据流示例

```
[图像加载] 
    ↓ (输出: image_data)
[灰度化]
    ↓ (输出: gray_image)
[Canny边缘检测]
    ↓ (输出: edge_image)
[图像显示]
    ↓ (输出: status_text)
```

---

## 📊 节点类型

### 1. IO节点（输入输出）

#### ImageLoadNode - 图像加载
- **输入**: 无
- **输出**: 图像数据 (numpy.ndarray)
- **属性**: 文件路径

#### ImageSaveNode - 图像保存
- **输入**: 图像数据
- **输出**: 状态文本
- **属性**: 保存路径

### 2. Processing节点（处理）

#### GrayscaleNode - 灰度化
- **输入**: 彩色图像
- **输出**: 灰度图像
- **算法**: `cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`

#### GaussianBlurNode - 高斯模糊
- **输入**: 原始图像
- **输出**: 模糊图像
- **参数**: 核大小、Sigma X
- **算法**: `cv2.GaussianBlur()`

#### CannyEdgeNode - Canny边缘检测
- **输入**: 原始图像
- **输出**: 边缘图像
- **参数**: 低阈值、高阈值
- **算法**: `cv2.Canny()`

#### ThresholdNode - 二值化
- **输入**: 原始图像
- **输出**: 二值化图像
- **参数**: 阈值、类型
- **算法**: `cv2.threshold()`

### 3. Display节点（显示）

#### ImageViewNode - 图像显示
- **输入**: 图像数据
- **输出**: 状态信息
- **功能**: 显示图像尺寸等信息

---

## 🔧 执行引擎工作原理

### 1. 构建依赖图

```python
dependencies = {
    Node_C: [Node_A, Node_B],  # C依赖A和B
    Node_B: [Node_A],          # B依赖A
    Node_A: []                  # A无依赖
}
```

### 2. 拓扑排序

使用Kahn算法确定执行顺序：
```
执行顺序: [Node_A, Node_B, Node_C]
```

### 3. 按序执行

```python
for node in execution_order:
    inputs = collect_inputs(node)  # 收集输入数据
    outputs = node.process(inputs) # 执行节点
    cache_outputs(node, outputs)   # 缓存输出
```

---

## 💡 扩展示例

### 添加Sobel边缘检测节点

```python
from NodeGraphQt import BaseNode
import cv2

class SobelEdgeNode(BaseNode):
    __identifier__ = 'processing'
    NODE_NAME = 'Sobel边缘检测'
    
    def __init__(self):
        super(SobelEdgeNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_slider('ksize', '核大小', 1, 7, 3, tab='properties')
        
    def process(self, inputs):
        if inputs and len(inputs) > 0:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                ksize = int(self.get_property('ksize'))
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
                sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
                sobel = cv2.magnitude(sobelx, sobely)
                sobel = cv2.normalize(sobel, None, 0, 255, cv2.NORM_MINMAX)
                sobel = cv2.convertScaleAbs(sobel)
                return {'输出图像': cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)}
            except Exception as e:
                print(f"Sobel处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
```

**注册节点：**
```python
# 在 ui/main_window.py 的 _register_nodes() 中添加
from nodes.processing_nodes import SobelEdgeNode
self.node_graph.register_node(SobelEdgeNode)
```

---

## 📈 性能优化建议

### 1. 节点缓存
```python
# 在节点中实现输出缓存
class CachedNode(BaseNode):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._cache_valid = False
        
    def process(self, inputs):
        if self._cache_valid and inputs_unchanged():
            return self._cache
        
        result = self._compute(inputs)
        self._cache = result
        self._cache_valid = True
        return result
```

### 2. 异步执行
```python
# 使用线程池并行执行独立节点
from concurrent.futures import ThreadPoolExecutor

def execute_parallel(nodes):
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(node.process): node for node in nodes}
        for future in futures:
            result = future.result()
```

### 3. GPU加速
```python
# 使用OpenCV的CUDA模块
import cv2.cuda as cuda

class GPUNode(BaseNode):
    def process(self, inputs):
        gpu_image = cuda_GpuMat.upload(image)
        gpu_result = cuda_function(gpu_image)
        return gpu_result.download()
```

---

## 🎓 学习价值

通过本项目可以学习：

1. **节点图架构**
   - NodeGraphQt框架使用
   - 节点-端口-连接模型
   - 可视化编程原理

2. **图算法**
   - 拓扑排序
   - 依赖关系分析
   - 有向无环图(DAG)

3. **软件设计模式**
   - 工厂模式（节点创建）
   - 观察者模式（事件通知）
   - 命令模式（执行引擎）

4. **GUI开发**
   - PySide2/Qt编程
   - 自定义控件
   - 事件处理

5. **图像处理**
   - OpenCV算法应用
   - 数据流处理
   - 实时预览

---

## 🔄 与传统版本对比

| 维度 | 传统版本 | 图形化版本 |
|------|---------|-----------|
| **编程方式** | 代码编写 | 拖拽连线 |
| **学习曲线** | 中等 | 低 |
| **灵活性** | 高 | 中 |
| **可视化** | 弱 | 强 |
| **调试难度** | 中 | 低 |
| **适用人群** | 开发者 | 工程师/技术员 |
| **扩展方式** | 修改代码 | 添加节点 |
| **复用性** | 中 | 高（JSON保存） |

---

## 🚀 未来规划

### 短期目标（v1.x）
- [ ] 添加更多算法节点（形态学、直方图等）
- [ ] 实现实时预览功能
- [ ] 优化执行性能
- [ ] 添加节点搜索功能

### 中期目标（v2.x）
- [ ] 支持视频流处理
- [ ] 添加节点分组功能
- [ ] 实现撤销/重做
- [ ] 插件系统支持

### 长期目标（v3.x）
- [ ] GPU加速支持
- [ ] 分布式执行
- [ ] 云端协作
- [ ] AI模型集成

---

## 📝 更新历史

### v1.0 - 初始版本 (2026-04-22)

**核心功能：**
- ✅ NodeGraphQt集成
- ✅ 6种基础节点
- ✅ 图执行引擎
- ✅ 工作流保存/加载
- ✅ 直观的图形界面

**节点类型：**
- IO节点: 2个
- 处理节点: 4个
- 显示节点: 1个

**技术亮点：**
- 拓扑排序算法
- 模块化节点设计
- 完善的数据流管理

---

## 🎉 总结

本项目成功实现了：

✅ **工业级可视化编程框架** - 类似海康、基恩士、康耐视  
✅ **完整的节点生态系统** - IO、处理、显示三类节点  
✅ **强大的执行引擎** - 自动依赖管理和拓扑排序  
✅ **友好的用户体验** - 拖拽式编辑、实时参数调整  
✅ **良好的可扩展性** - 易于添加新节点和算法  

为工业视觉应用开发提供了**零代码门槛**的解决方案！🚀

---

**开始你的可视化编程之旅！** 🎨🔧✨
