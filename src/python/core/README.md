# 核心引擎模块 (Core)

## 📋 更新历史

### v1.0 - 初始版本 (2026-04-22)
- ✅ 实现图执行引擎 (`GraphEngine`)
- ✅ 实现拓扑排序算法
- ✅ 实现依赖关系图构建
- ✅ 支持节点按依赖顺序执行
- ✅ 实现节点输出缓存机制

---

## 🎯 概况

**核心引擎模块**是图形化视觉编程系统的"大脑"，负责解析节点图的连接关系，构建执行顺序，并依次调用各节点的 `process()` 方法完成图像处理流程。

### 设计理念
- **自动化依赖管理**: 自动分析节点连接关系，确定执行顺序
- **拓扑排序**: 使用Kahn算法确保无环依赖的正确执行
- **数据流驱动**: 基于端口连接的隐式数据传递
- **高效执行**: 缓存中间结果，避免重复计算

---

## 💻 部署环境要求

### 技术栈
- **Python**: 3.7+
- **NumPy**: >=1.19.0, <2.0.0
- **OpenCV**: >=4.5.0
- **标准库**: `collections` (defaultdict, deque)

### 安装依赖
```bash
cd src/python_graph
pip install -r requirements.txt
```

---

## 📦 基本功能

### 模块结构
```
core/
├── __init__.py              # 模块导出配置
├── graph_engine.py         # 图执行引擎（核心）
└── node_registry.py        # 节点注册表（已废弃，改用直接注册）
```

### 核心类说明

#### 1. GraphEngine ([graph_engine.py](file://d:\example\projects\StduyOpenCV\src\python_graph\core\graph_engine.py))

图执行引擎，负责整个节点图的解析和执行。

**主要方法**:

##### `execute_graph(graph)`
执行整个节点图的处理流程。

**参数**:
- `graph`: NodeGraph实例

**返回值**:
- `dict`: 所有节点的输出数据字典

**执行流程**:
1. 获取所有节点
2. 构建依赖关系图
3. 拓扑排序确定执行顺序
4. 按顺序执行每个节点
5. 返回所有节点的输出

**示例**:
```python
from core.graph_engine import GraphEngine

engine = GraphEngine()
outputs = engine.execute_graph(node_graph)
```

##### `_build_dependency_graph(all_nodes)`
构建节点间的依赖关系图。

**原理**:
- 遍历所有节点的输入端口
- 查找连接到该端口的其他节点
- 建立 "节点A -> 节点B" 的依赖关系

**返回值**:
- `defaultdict(list)`: 键为节点，值为该节点依赖的前置节点列表

##### `_topological_sort(dependencies, all_nodes)`
对节点进行拓扑排序，确定执行顺序。

**算法**: Kahn算法（基于入度的BFS）

**步骤**:
1. 计算每个节点的入度（依赖数量）
2. 将入度为0的节点加入队列
3. 从队列取出节点，减少其后继节点的入度
4. 重复直到队列为空

**返回值**:
- `list`: 按执行顺序排列的节点列表

**异常处理**:
- 如果存在循环依赖，抛出异常并提示

##### `_execute_node(node)`
执行单个节点的处理逻辑。

**流程**:
1. 收集该节点所有输入端口的数据
2. 调用节点的 `process(inputs)` 方法
3. 缓存输出结果到 `self.node_outputs`

**数据传递**:
```python
# 从上游节点获取输入
inputs = []
for input_port in node.input_ports():
    connected_ports = input_port.connected_ports()
    for port in connected_ports:
        source_node = port.node()
        output_data = self.node_outputs.get(source_node.id())
        if output_data:
            inputs.append(output_data)

# 执行节点并缓存结果
output = node.process(inputs)
self.node_outputs[node.id()] = output
```

#### 2. BaseVisualNode ([node_registry.py](file://d:\example\projects\StduyOpenCV\src\python_graph\core\node_registry.py))

**状态**: ⚠️ 已废弃

原计划作为所有节点的基类，但实际开发中直接使用 `NodeGraphQt.BaseNode`。此文件中的代码仅供参考，不建议使用。

**建议**: 
- 新节点直接继承 `NodeGraphQt.BaseNode`
- 在 [nodes/](file://d:\example\projects\StduyOpenCV\src\python_graph\nodes) 目录下定义节点类

---

## 🔧 使用示例

### 完整执行流程

```python
from PySide2 import QtWidgets
from NodeGraphQt import NodeGraph
from core.graph_engine import GraphEngine
from nodes import ImageLoadNode, GrayscaleNode, ImageViewNode

# 1. 创建节点图
graph = NodeGraph()
graph.register_node(ImageLoadNode)
graph.register_node(GrayscaleNode)
graph.register_node(ImageViewNode)

# 2. 创建节点并连接
load_node = graph.create_node('io.ImageLoadNode')
load_node.set_property('file_path', 'test.jpg')

gray_node = graph.create_node('processing.GrayscaleNode')
view_node = graph.create_node('display.ImageViewNode')

# 连接节点
load_node.set_output(0, gray_node.input(0))
gray_node.set_output(0, view_node.input(0))

# 3. 执行节点图
engine = GraphEngine()
try:
    outputs = engine.execute_graph(graph)
    print(f"执行成功！处理了 {len(outputs)} 个节点")
except Exception as e:
    print(f"执行失败: {e}")
```

### 错误处理

```python
try:
    outputs = engine.execute_graph(graph)
except ValueError as e:
    # 循环依赖错误
    print(f"检测到循环依赖: {e}")
except Exception as e:
    # 其他执行错误
    print(f"执行错误: {e}")
```

---

## 📊 执行流程图

```
用户点击"运行"
    ↓
GraphEngine.execute_graph()
    ↓
_build_dependency_graph()
    ├─ 遍历所有节点
    ├─ 检查输入端口连接
    └─ 构建依赖关系图
    ↓
_topological_sort()
    ├─ 计算每个节点的入度
    ├─ BFS遍历（Kahn算法）
    └─ 生成执行顺序列表
    ↓
按顺序执行节点
    ├─ _execute_node(node_1)
    │   ├─ 收集输入数据
    │   ├─ 调用 node.process(inputs)
    │   └─ 缓存输出结果
    ├─ _execute_node(node_2)
    └─ ...
    ↓
返回所有节点的输出
```

---

## ⚙️ 技术细节

### 拓扑排序算法

**Kahn算法伪代码**:
```
L ← 空列表（存储排序结果）
S ← 所有入度为0的节点集合

while S 非空:
    从 S 中移除节点 n
    将 n 添加到 L
    
    for each 节点 m (n 指向 m):
        移除边 n → m
        if m 的入度变为 0:
            将 m 添加到 S

if 图中还有边:
    return error (图中有环)
else:
    return L (拓扑排序结果)
```

**时间复杂度**: O(V + E)，其中V是节点数，E是连接数

### 数据传递机制

节点间的数据通过 **端口连接** 隐式传递：

```python
# 节点A的输出
output_A = {'image': image_data}

# 节点B的输入（通过连接自动获取）
inputs_B = [output_A]  # 列表形式，支持多输入

# 节点B处理
result_B = node_B.process(inputs_B)
```

---

## 🚀 优化及改进计划

### 短期目标 (v1.x)
- [ ] 添加执行日志记录（每个节点的执行时间）
- [ ] 实现部分执行功能（仅执行选中的节点）
- [ ] 优化错误提示（明确指出哪个节点出错）
- [ ] 添加执行进度条

### 中期目标 (v2.x)
- [ ] 支持并行执行（独立分支同时执行）
- [ ] 实现增量执行（只重新执行修改过的节点）
- [ ] 添加执行历史回溯（查看每一步的中间结果）
- [ ] 性能分析工具（找出瓶颈节点）

### 长期目标 (v3.x)
- [ ] GPU加速支持（CUDA节点自动调度到GPU）
- [ ] 分布式执行（跨机器执行大型工作流）
- [ ] 实时执行模式（参数调整时自动重新执行）
- [ ] 执行计划可视化（图形化展示执行顺序）

---

## 🐛 常见问题

### Q: 为什么节点执行顺序不正确？
**A**: 检查是否有未连接的输入端口。引擎会根据连接关系自动排序，如果某个节点缺少输入，可能导致排序错误。

### Q: 如何调试节点执行过程？
**A**: 在节点的 `process()` 方法中添加 `print()` 语句，或在引擎中添加日志：
```python
def _execute_node(self, node):
    print(f"正在执行: {node.name()}")
    # ... 执行逻辑
    print(f"执行完成: {node.name()}")
```

### Q: 检测到循环依赖怎么办？
**A**: 拓扑排序会检测循环依赖并抛出异常。检查节点连接，确保没有形成环路（如 A→B→C→A）。

---

## 📚 相关文档

- 📘 [项目总览](../../README.md) - 整体项目介绍
- 📗 [节点模块](../nodes/README.md) - 节点定义与开发
- 📕 [用户界面模块](../ui/README.md) - UI组件文档
- 🔗 [拓扑排序算法详解](https://en.wikipedia.org/wiki/Topological_sorting)

---

## 🤝 贡献指南

如需优化执行引擎，请遵循以下原则：
1. 保持向后兼容性
2. 添加单元测试
3. 更新本文档
4. 性能优化需提供基准测试数据
