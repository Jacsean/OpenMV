# StduyOpenCV 项目代码规范

本文档定义了 StduyOpenCV 项目的代码编写规范，所有开发者必须遵循。

## 1. 项目结构

### 1.1 目录树

```
StduyOpenCV/
├── src/python/                    # Python源码根目录
│   ├── core/                      # 核心业务层
│   │   ├── event_bus.py           # 事件总线（模块间通信基础设施）
│   │   ├── graph_engine.py        # 图执行引擎（Service层）
│   │   ├── node_registry.py       # 节点注册表
│   │   ├── project_manager.py      # 工程管理器（DAO层）
│   │   ├── project_ui_manager.py  # 工程UI控制器（Controller层）
│   │   └── execution_ui_manager.py # 执行UI控制器（Controller层）
│   ├── plugins/                    # 插件系统层
│   │   ├── plugin_manager.py      # 插件管理器（Service层）
│   │   ├── plugin_ui_manager.py   # 插件UI管理器（Controller层）
│   │   ├── models.py              # 数据模型（Entity层）
│   │   ├── sandbox.py             # 沙箱隔离
│   │   ├── hot_reloader.py        # 热重载
│   │   ├── dependency_resolver.py # 依赖解析
│   │   └── plugin_installer.py    # 插件安装器
│   ├── shared_libs/               # 共享库层
│   │   ├── node_base/
│   │   │   ├── base_node.py      # 节点基类
│   │   │   └── performance_monitor.py # 性能监控
│   │   └── common_utils/
│   ├── ui/                        # 视图层
│   │   ├── main_window.py         # 主窗口
│   │   ├── node_editor.py         # 节点编辑器
│   │   └── image_preview.py       # 图像预览
│   ├── utils/                     # 工具层
│   │   ├── logger.py              # 日志系统
│   │   └── qt_log_handler.py      # Qt日志处理器
│   └── user_plugins/              # 用户插件开发指南
├── plugin_packages/               # 插件包目录
│   ├── builtin/                   # 内置插件
│   └── marketplace/installed/     # 市场已安装插件
├── tools/                         # 工具脚本
└── tests/                         # 测试目录
```

### 1.2 模块职责划分

| 层级                            | 目录                                                    | 职责                             | 示例                                 |
| ------------------------------- | ------------------------------------------------------- | -------------------------------- | ------------------------------------ |
| **视图层 (View)**         | `ui/`                                                 | UI界面、用户交互、事件处理       | MainWindow, ImagePreviewDialog       |
| **控制器层 (Controller)** | `core/*_ui_manager.py`                                | UI与业务逻辑的桥接、用户操作响应 | ExecutionUIManager, ProjectUIManager |
| **服务层 (Service)**      | `core/graph_engine.py`, `plugins/plugin_manager.py` | 核心业务逻辑、算法执行           | GraphEngine, PluginManager           |
| **数据访问层 (DAO)**      | `core/project_manager.py`                             | 数据持久化、文件读写             | Workflow.save(), Project.load()      |
| **实体层 (Entity)**       | `plugins/models.py`                                   | 数据模型、数据结构               | PluginInfo, NodeDefinition, Workflow |
| **共享库层**              | `shared_libs/`                                        | 可复用组件、基类                 | BaseNode, PerformanceMonitor         |

---

## 2. 代码风格

### 2.1 命名规范

#### 类命名（PascalCase）

```python
# ✅ 正确
class GraphEngine:
class PluginManager:
class BaseNode:
class ImagePreviewDialog:

# ❌ 错误
class graph_engine:
class plugin_manager:
```

#### 方法/函数命名（snake_case）

```python
# ✅ 正确
def execute_graph(self):
def scan_plugins(self):
def _build_dependency_graph(self):  # 私有方法以下划线开头
def check_dependencies(self):

# ❌ 错误
def executeGraph(self):
def ScanPlugins(self):
```

#### 变量命名（snake_case）

```python
# ✅ 正确
node_count = 0
is_modified = False
plugin_info = None
hardware_requirements = {}

# ❌ 错误
nodeCount = 0
isModified = False
```

#### 常量命名（UPPER_SNAKE_CASE）

```python
# ✅ 正确
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_LOG_LEVEL = "NORMAL"
SUPPORTED_FORMATS = ['jpg', 'png', 'bmp']

# ❌ 错误
maxFileSize = 50 * 1024 * 1024
```

### 2.2 注释规范

#### 模块文档字符串

```python
"""
图执行引擎 - 执行节点图的处理流程
"""
```

#### 类文档字符串

```python
class GraphEngine:
    """
    图执行引擎

    负责执行节点图的处理流程，包括：
    - 依赖关系分析
    - 拓扑排序
    - 节点顺序执行

    Attributes:
        graph: 当前执行的节点图
        node_outputs: 节点输出缓存
    """
```

#### 方法文档字符串

```python
def execute_graph(self, graph):
    """
    执行整个节点图

    Args:
        graph: NodeGraph实例

    Returns:
        dict: 节点输出结果字典

    Raises:
        ValueError: 当检测到循环依赖时
    """
```

#### 行内注释

```python
# Step 1: 获取输入图像
image = inputs[0]

# Step 2: 执行灰度化转换
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# TODO: 优化性能，考虑使用GPU加速
```

### 2.3 格式规范

#### 导入顺序

```python
# 1. 标准库
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# 2. 第三方库
import cv2
import numpy as np
from PySide2 import QtWidgets

# 3. 本地模块
from core.graph_engine import GraphEngine
from plugins.plugin_manager import PluginManager
from utils.logger import logger
```

#### 空行规范

```python
# 模块级别：2个空行
import os


class MyClass:
    # 类内部方法：1个空行
    def method1(self):
        pass

    def method2(self):
        pass


# 类之间：2个空行
class AnotherClass:
    pass
```

#### 缩进

- 使用 **4个空格** 缩进
- 禁止使用Tab字符

#### 行长限制

- 每行不超过 **100个字符**
- 长参数列表换行对齐：

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[Dict] = None
) -> bool:
    pass
```

---

## 3. 架构分层职责

### 3.1 Controller层（UI管理器）

**职责**：

- 处理用户交互事件
- 调用Service层执行业务逻辑
- 更新UI显示
- 显示对话框和提示信息

**禁止**：

- 直接操作数据库或文件
- 包含复杂业务逻辑
- 直接调用底层API

**示例**：[`ExecutionUIManager`](src/python/core/execution_ui_manager.py)

```python
class ExecutionUIManager:
    """执行UI管理器 - 处理执行相关的UI交互"""

    def __init__(self, graph_engine, main_window):
        self.graph_engine = graph_engine  # Service层
        self.main_window = main_window    # View层

    def run_current_graph(self):
        """执行当前工作流（UI触发）"""
        if not self.main_window.current_node_graph:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有激活的工作流")
            return

        try:
            # 调用Service层执行
            results = self.graph_engine.execute_graph(self.main_window.current_node_graph)

            # 更新UI
            logger.success("节点图执行完成!")
            self.refresh_all_previews()

        except Exception as e:
            logger.error(f"执行错误: {e}")
            QtWidgets.QMessageBox.critical(self.main_window, "执行错误", str(e))
```

### 3.2 Service层（业务引擎）

**职责**：

- 实现核心业务逻辑
- 算法执行和数据处理
- 协调多个DAO操作
- 返回处理结果

**禁止**：

- 直接操作UI组件
- 包含UI相关代码
- 直接读写文件（应通过DAO层）

**示例**：[`GraphEngine`](src/python/core/graph_engine.py)

```python
class GraphEngine:
    """
    图执行引擎

    负责执行节点图的处理流程
    """

    def __init__(self):
        self.graph = None
        self.node_outputs = {}

    def execute_graph(self, graph):
        """
        执行整个节点图
        """
        self.graph = graph
        self.node_outputs.clear()

        all_nodes = graph.all_nodes()
        dependencies = self._build_dependency_graph(all_nodes)
        ordered_nodes = self._topological_sort(dependencies, all_nodes)

        for node in ordered_nodes:
            self._execute_node(node)

        return self.node_outputs

    def _build_dependency_graph(self, all_nodes):
        """构建节点依赖关系图"""
        dependencies = defaultdict(list)

        for node in all_nodes:
            for input_port in node.input_ports():
                connected_ports = input_port.connected_ports()
                for connected_port in connected_ports:
                    source_node = connected_port.node()
                    dependencies[node].append(source_node)

        return dependencies

    def _topological_sort(self, dependencies, all_nodes):
        """拓扑排序，确定节点执行顺序"""
        in_degree = {node: 0 for node in all_nodes}

        for node in all_nodes:
            for dep_node in dependencies[node]:
                in_degree[node] += 1

        queue = deque()
        for node in all_nodes:
            if in_degree[node] == 0:
                queue.append(node)

        sorted_nodes = []
        while queue:
            current_node = queue.popleft()
            sorted_nodes.append(current_node)

            for node in all_nodes:
                if current_node in dependencies[node]:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)

        if len(sorted_nodes) != len(all_nodes):
            raise ValueError("节点图中存在循环依赖")

        return sorted_nodes
```

### 3.3 DAO层（数据访问）

**职责**：

- 数据持久化（保存/加载）
- 文件读写操作
- 数据格式转换

**禁止**：

- 包含业务逻辑
- 直接操作UI

**示例**：[`ProjectManager`](src/python/core/project_manager.py)

```python
class ProjectManager:
    """工程管理器（单例）"""

    def __init__(self):
        self.current_project = None

    def save_project(self, project: 'Project', project_dir: str):
        """
        保存工程到目录

        Args:
            project: 工程对象
            project_dir: 工程目录路径
        """
        project_path = Path(project_dir)

        project_file = project_path / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, indent=4, ensure_ascii=False)

        workflows_dir = project_path / "workflows"
        workflows_dir.mkdir(exist_ok=True)

        for workflow in project.workflows:
            workflow_file = workflows_dir / f"{workflow.id}.json"
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow.to_dict(), f, indent=4, ensure_ascii=False)

    def load_project(self, project_dir: str) -> 'Project':
        """
        从目录加载工程

        Args:
            project_dir: 工程目录路径

        Returns:
            Project: 工程对象
        """
        project_path = Path(project_dir)

        project_file = project_path / "project.json"
        with open(project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        project = Project.from_dict(data)
        return project
```

### 3.4 Entity层（数据模型）

**职责**：

- 定义数据结构
- 提供序列化/反序列化方法
- 数据校验

**示例**：[`models.py`](src/python/plugins/models.py)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class NodeDefinition:
    """节点定义"""
    class_name: str
    display_name: str
    category: str
    icon: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    description: str = ""
    color: Optional[List[int]] = None
    resource_level: str = "light"
    hardware_requirements: Dict[str, Any] = field(default_factory=lambda: {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    })
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    author: str
    description: str
    category_group: str = ""
    nodes: List[NodeDefinition] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    path: str = ""
    enabled: bool = True
    installed_at: Optional[datetime] = None
    source: str = "builtin"
    priority: int = 1
```

---

## 4. 固定模式

### 4.1 返回值模式

```python
# Service层返回实际数据或None
def get_node_definition(self, node_id: str) -> Optional[NodeDefinition]:
    """获取节点定义"""
    if node_id in self.nodes:
        return self.nodes[node_id]
    return None

# Controller层处理None情况
def on_node_selected(self, node_id: str):
    """节点选中事件"""
    node_def = self.plugin_manager.get_node_definition(node_id)
    if node_def is None:
        logger.warning(f"节点定义不存在: {node_id}")
        return
    self.properties_bin.update(node_def)
```

### 4.2 异常处理模式

```python
# 业务逻辑层抛出明确异常
def execute_node(self, node):
    """执行单个节点"""
    if not self._validate_node(node):
        raise ValueError(f"节点验证失败: {node.id}")

    try:
        result = node.process(inputs)
        return result
    except Exception as e:
        logger.error(f"节点执行失败: {node.name}, 错误: {e}")
        raise NodeExecutionError(f"节点 {node.name} 执行失败") from e

# Controller层捕获并转换
def on_run_clicked(self):
    """运行按钮点击"""
    try:
        self.engine.execute_graph(self.current_graph)
    except ValueError as e:
        QtWidgets.QMessageBox.warning(self, "警告", str(e))
    except NodeExecutionError as e:
        QtWidgets.QMessageBox.critical(self, "执行错误", str(e))
```

### 4.3 参数校验模式

```python
# Service层校验
def register_plugin(self, plugin_info: PluginInfo) -> bool:
    """注册插件"""
    if not plugin_info.name:
        raise ValueError("插件名称不能为空")

    if not plugin_info.version:
        raise ValueError("插件版本不能为空")

    if plugin_info.name in self.plugins:
        logger.warning(f"插件已存在: {plugin_info.name}")
        return False

    self.plugins[plugin_info.name] = plugin_info
    return True

# 使用assert进行开发期校验
def _validate_inputs(self, inputs: list):
    assert inputs is not None, "输入不能为None"
    assert len(inputs) > 0, "输入列表不能为空"
```

### 4.4 注解使用

```python
# 使用dataclass作为Entity
from dataclasses import dataclass, field

@dataclass
class PluginInfo:
    name: str
    version: str
    nodes: List[NodeDefinition] = field(default_factory=list)

# 使用type hint
from typing import Dict, List, Optional

def scan_plugins(self) -> List[PluginInfo]:
    """扫描插件目录"""
    pass

def get_plugin(self, name: str) -> Optional[PluginInfo]:
    """获取插件信息"""
    pass

# 使用property进行封装
class Workflow:
    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @property
    def name(self) -> str:
        return self._name
```

### 4.5 单例模式

```python
class PluginManager:
    """插件管理器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.plugins: Dict[str, PluginInfo] = {}
```

---

## 5. 示例代码

### 5.1 Entity层示例

```python
"""
插件系统数据模型
定义插件元数据结构和节点定义
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class NodeDefinition:
    """节点定义"""
    class_name: str
    display_name: str
    category: str
    icon: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    description: str = ""
    color: Optional[List[int]] = None
    resource_level: str = "light"
    hardware_requirements: Dict[str, Any] = field(default_factory=lambda: {
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    })
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    author: str
    description: str
    category_group: str = ""
    nodes: List[NodeDefinition] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    path: str = ""
    enabled: bool = True
    installed_at: Optional[datetime] = None
    source: str = "builtin"
    priority: int = 1
```

### 5.2 Service层示例

```python
"""
图执行引擎 - 执行节点图的处理流程
"""

import cv2
import numpy as np
from collections import defaultdict, deque


class GraphEngine:
    """图执行引擎"""

    def __init__(self):
        self.graph = None
        self.node_outputs = {}

    def execute_graph(self, graph):
        """执行整个节点图"""
        self.graph = graph
        self.node_outputs.clear()

        all_nodes = graph.all_nodes()
        dependencies = self._build_dependency_graph(all_nodes)
        ordered_nodes = self._topological_sort(dependencies, all_nodes)

        for node in ordered_nodes:
            self._execute_node(node)

        return self.node_outputs

    def _build_dependency_graph(self, all_nodes):
        """构建节点依赖关系图"""
        dependencies = defaultdict(list)

        for node in all_nodes:
            for input_port in node.input_ports():
                for connected_port in input_port.connected_ports():
                    source_node = connected_port.node()
                    dependencies[node].append(source_node)

        return dependencies

    def _topological_sort(self, dependencies, all_nodes):
        """拓扑排序"""
        in_degree = {node: 0 for node in all_nodes}

        for node in all_nodes:
            for dep_node in dependencies[node]:
                in_degree[node] += 1

        queue = deque()
        for node in all_nodes:
            if in_degree[node] == 0:
                queue.append(node)

        sorted_nodes = []
        while queue:
            current_node = queue.popleft()
            sorted_nodes.append(current_node)

            for node in all_nodes:
                if current_node in dependencies[node]:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)

        if len(sorted_nodes) != len(all_nodes):
            raise ValueError("节点图中存在循环依赖")

        return sorted_nodes
```

### 5.3 Controller层示例

```python
"""
工程UI管理器 - 处理工程相关的UI交互
"""

from PySide2 import QtWidgets
from pathlib import Path


class ProjectUIManager:
    """工程UI管理器"""

    def __init__(self, project_manager, main_window):
        self.project_manager = project_manager
        self.main_window = main_window

    def on_new_project(self):
        """新建工程"""
        project = self.project_manager.create_project("未命名工程")
        self.main_window.update_project_tree(project)
        logger.success(f"已创建新工程: {project.name}")

    def on_save_project(self):
        """保存工程"""
        if not self.project_manager.current_project:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有打开的工程")
            return

        try:
            self.project_manager.save_project(
                self.project_manager.current_project,
                self.project_manager.current_project.path
            )
            logger.success("工程已保存")
        except Exception as e:
            logger.error(f"保存失败: {e}")
            QtWidgets.QMessageBox.critical(self.main_window, "错误", f"保存失败: {e}")

    def on_load_project(self, project_dir: str):
        """加载工程"""
        try:
            project = self.project_manager.load_project(project_dir)
            self.main_window.update_project_tree(project)
            logger.success(f"已加载工程: {project.name}")
        except Exception as e:
            logger.error(f"加载失败: {e}")
            QtWidgets.QMessageBox.critical(self.main_window, "错误", f"加载失败: {e}")
```

---

## 6. 日志规范

```python
from utils.logger import logger

# 使用logger进行日志输出
logger.info("正在扫描插件...")
logger.success("插件加载成功")
logger.warning("插件已存在，将被覆盖")
logger.error(f"加载失败: {e}")

# 日志格式
# [时间] [级别] [模块] 消息
# 2026-05-06 10:30:15 [INFO] [plugin_manager] 正在扫描插件...
```

---

## 7. 依赖注入规范

```python
class ExecutionUIManager:
    """执行UI管理器"""

    def __init__(self, graph_engine, main_window):
        self.graph_engine = graph_engine  # 通过构造函数注入
        self.main_window = main_window

    def run(self):
        # 使用注入的依赖
        results = self.graph_engine.execute_graph(...)
```

---

## 8. 事件总线模式（Event Bus）

### 8.1 概述

事件总线是模块间通信的核心基础设施，采用发布-订阅模式。所有跨模块通信必须通过事件总线，禁止直接调用其他模块的方法。

### 8.2 核心组件

**文件位置**: `core/event_bus.py`

**Events枚举**: 定义系统中的所有事件类型

```python
class Events(Enum):
    WORKFLOW_CREATED = auto()
    WORKFLOW_ADDED = auto()
    WORKFLOW_REMOVED = auto()
    WORKFLOW_SELECTED = auto()
    WORKFLOW_EXECUTING = auto()
    WORKFLOW_EXECUTED = auto()
    WORKFLOW_EXECUTION_ERROR = auto()
    PROJECT_CREATED = auto()
    PROJECT_OPENED = auto()
    PROJECT_SAVED = auto()
    PLUGIN_SCANNED = auto()
    PLUGIN_LOADED = auto()
    PLUGIN_INSTALL = auto()
    TAB_CHANGED = auto()
    PREVIEW_REFRESH = auto()
    SETTINGS_CHANGED = auto()
```

### 8.3 使用方式

**订阅事件**:

```python
from core.event_bus import event_bus, Events

def on_workflow_executed(**kwargs):
    workflow = kwargs.get('workflow')
    results = kwargs.get('results', {})
    logger.success(f"工作流 {workflow.name} 执行完成")

event_bus.subscribe(Events.WORKFLOW_EXECUTED, on_workflow_executed)
```

**发布事件**:

```python
from core.event_bus import event_bus, Events

event_bus.publish(Events.WORKFLOW_EXECUTED, workflow=workflow, results=results)
```

### 8.4 事件命名规范

- 命名格式: `{主体}_{动作}`
- 示例: `WORKFLOW_EXECUTED`, `PROJECT_SAVED`, `PLUGIN_LOADED`
- 使用动词过去式表示事件已完成
- 使用动词现在分词表示事件进行中

### 8.5 架构原则

1. **发布者不知道订阅者**: 发布者只关心发布事件，不关心谁会响应
2. **订阅者不知道发布者**: 订阅者只关心响应事件，不关心事件从哪来
3. **单向依赖**: Manager → EventBus ← Subscribers，形成星型拓扑
4. **避免循环依赖**: 如果两个模块需要互相通信，考虑合并或使用回调接口

### 8.6 MainWindow事件订阅示例

```python
def _setup_event_subscriptions(self):
    """设置事件订阅 - 响应全局事件变化"""
    event_bus.subscribe(Events.WORKFLOW_SELECTED, self._on_workflow_selected)
    event_bus.subscribe(Events.WORKFLOW_EXECUTED, self._on_workflow_executed)
    event_bus.subscribe(Events.WORKFLOW_EXECUTION_ERROR, self._on_workflow_execution_error)
    event_bus.subscribe(Events.PREVIEW_REFRESH, self._on_preview_refresh)
    event_bus.subscribe(Events.PLUGIN_LOADED, self._on_plugin_loaded)

def _on_workflow_executed(self, **kwargs):
    """响应工作流执行完成事件"""
    workflow = kwargs.get('workflow')
    results = kwargs.get('results', {})
    if workflow:
        self.status_label.setText(f"✅ {workflow.name} 执行完成")
```

### 8.7 事件驱动UI更新模式

```
┌─────────────────┐     发布事件      ┌─────────────────┐
│  ExecutionUI    │ ───────────────→ │                 │
│  Manager        │                  │   EventBus      │
└─────────────────┘                  │                 │
                                      └────────┬────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
           │ MainWindow      │      │ PreviewManager  │      │ StatusBar       │
           │ (状态栏更新)    │      │ (刷新预览)      │      │ (显示状态)      │
           └─────────────────┘      └─────────────────┘      └─────────────────┘
```
