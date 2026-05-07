# 项目代码规范

本文档定义了 StduyOpenCV 项目的代码编写规范，所有开发者必须遵循。

## 1. 项目结构

### 1.1 目录树

```
StduyOpenCV/
├── src/python/                    # Python源码根目录
│   ├── core/                      # 核心引擎层（业务逻辑）
│   │   ├── graph_engine.py        # 图执行引擎
│   │   ├── node_registry.py       # 节点注册表
│   │   ├── project_manager.py     # 工程管理器
│   │   ├── project_ui_manager.py  # 工程UI管理器
│   │   └── execution_ui_manager.py # 执行UI管理器
│   ├── plugins/                   # 插件系统层
│   │   ├── plugin_manager.py      # 插件管理器
│   │   ├── plugin_ui_manager.py   # 插件UI管理器
│   │   ├── sandbox.py             # 沙箱环境
│   │   └── models.py              # 插件数据模型
│   ├── shared_libs/               # 共享库层
│   │   ├── node_base/             # 节点基类
│   │   │   ├── base_node.py       # 通用节点基类
│   │   │   └── performance_monitor.py # 性能监控
│   │   └── common_utils/          # 通用工具
│   ├── plugin_packages/           # 插件包目录
│   │   ├── builtin/               # 内置插件
│   │   │   ├── preprocessing/     # 预处理插件
│   │   │   ├── feature_extraction/ # 特征提取插件
│   │   │   ├── io_camera/         # IO和相机插件
│   │   │   └── ...
│   │   └── marketplace/           # 市场插件
│   ├── ui/                        # 视图层
│   │   ├── main_window.py         # 主窗口
│   │   ├── node_editor.py         # 节点编辑器
│   │   └── image_preview.py       # 图像预览
│   ├── utils/                     # 工具层
│   │   ├── logger.py              # 日志系统
│   │   └── qt_log_handler.py      # Qt日志处理器
│   └── user_plugins/              # 用户插件开发指南
├── tests/                         # 测试目录
├── tools/                         # 工具脚本
├── workspace/                     # 工作空间
└── docs/                          # 文档目录
```

### 1.2 模块职责划分

| 层级 | 目录 | 职责 | 示例 |
|------|------|------|------|
| **视图层 (View)** | `ui/` | UI界面、用户交互、事件处理 | MainWindow, ImagePreviewDialog |
| **控制器层 (Controller)** | `core/*_ui_manager.py` | UI与业务逻辑的桥接、用户操作响应 | ExecutionUIManager, ProjectUIManager |
| **服务层 (Service)** | `core/graph_engine.py`, `plugins/plugin_manager.py` | 核心业务逻辑、算法执行 | GraphEngine, PluginManager |
| **数据访问层 (DAO)** | `core/project_manager.py` | 数据持久化、文件读写 | Workflow.save(), Project.load() |
| **实体层 (Entity)** | `plugins/models.py`, `core/project_manager.py` | 数据模型、数据结构 | PluginInfo, Workflow, NodeDefinition |
| **共享库层** | `shared_libs/` | 可复用组件、基类 | BaseNode, PerformanceMonitor |

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

#### 模块级常量
```python
# 在模块顶部定义
__identifier__ = 'preprocessing'
NODE_NAME = '灰度化'
```

### 2.2 注释规范

#### 模块文档字符串
```python
"""
插件管理器 - 负责插件的扫描、加载和管理

提供插件元数据解析、节点动态加载、沙箱隔离等功能。
支持builtin和marketplace两种插件来源。
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
    """图执行引擎 - 核心业务逻辑"""
    
    def execute_graph(self, graph):
        """执行整个节点图"""
        self.graph = graph
        self.node_outputs.clear()
        
        # 构建依赖关系
        dependencies = self._build_dependency_graph(graph.all_nodes())
        
        # 拓扑排序
        ordered_nodes = self._topological_sort(dependencies, graph.all_nodes())
        
        # 顺序执行节点
        for node in ordered_nodes:
            self._execute_node(node)
            
        return self.node_outputs
```

### 3.3 DAO层（数据管理）

**职责**：
- 数据持久化（保存/加载）
- 文件读写操作
- 数据库操作（如有）
- 数据验证

**禁止**：
- 包含业务逻辑
- 直接操作UI
- 调用Service层

**示例**：[`Workflow`](src/python/core/project_manager.py)
```python
class Workflow:
    """工作流数据实体 - 负责自身数据的持久化"""
    
    def save_to_file(self, file_path: str) -> bool:
        """保存工作流到JSON文件"""
        try:
            data = self.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.file_path = file_path
            self.mark_saved()
            return True
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return False
    
    @staticmethod
    def load_from_file(file_path: str) -> Optional['Workflow']:
        """从JSON文件加载工作流"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            workflow = Workflow(name=data.get('name', '未命名'))
            workflow.from_dict(data)
            workflow.file_path = file_path
            return workflow
        except Exception as e:
            logger.error(f"加载失败: {e}")
            return None
```

### 3.4 Entity层（数据模型）

**职责**：
- 定义数据结构
- 数据验证
- 简单的数据转换方法

**禁止**：
- 包含业务逻辑
- 直接操作文件或数据库
- 依赖外部服务

**示例**：[`PluginInfo`](src/python/plugins/models.py)
```python
@dataclass
class PluginInfo:
    """插件信息数据模型"""
    name: str
    version: str
    author: str
    description: str
    category_group: str
    nodes: List[NodeDefinition]
    dependencies: List[str] = field(default_factory=list)
    min_app_version: str = "3.1.0"
    path: str = ""
    source: str = "builtin"
    priority: int = 1
    
    def is_compatible(self, app_version: str) -> bool:
        """检查是否与当前应用版本兼容"""
        return parse_version(app_version) >= parse_version(self.min_app_version)
```

---

## 4. 固定模式

### 4.1 返回值规范

#### 成功/失败模式
```python
def process_data(self, data) -> Optional[Dict]:
    """
    处理数据
    
    Returns:
        dict: 成功时返回结果字典
        None: 失败时返回None（同时记录错误日志）
    """
    try:
        result = self._do_processing(data)
        logger.success("处理成功")
        return result
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return None
```

#### 布尔值模式
```python
def save_to_file(self, file_path: str) -> bool:
    """
    保存到文件
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        # 执行保存操作
        return True
    except Exception as e:
        logger.error(f"保存失败: {e}")
        return False
```

#### 异常抛出模式
```python
def critical_operation(self):
    """
    关键操作 - 失败时抛出异常
    
    Raises:
        ValueError: 参数无效
        RuntimeError: 执行失败
    """
    if not self.is_valid():
        raise ValueError("参数无效")
    
    try:
        # 执行操作
        pass
    except Exception as e:
        raise RuntimeError(f"操作失败: {e}") from e
```

### 4.2 异常处理模式

#### 标准异常处理
```python
def process_image(self, image):
    """处理图像"""
    try:
        # 业务逻辑
        result = self._transform(image)
        logger.success("图像处理成功")
        return result
        
    except cv2.error as e:
        logger.error(f"OpenCV错误: {e}")
        return None
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return None
        
    except Exception as e:
        logger.error(f"未知错误: {e}")
        import traceback
        traceback.print_exc()
        return None
```

#### 资源清理模式
```python
def process_with_resource(self):
    """使用资源的处理"""
    resource = None
    try:
        resource = self._acquire_resource()
        result = self._process(resource)
        return result
    except Exception as e:
        logger.error(f"处理失败: {e}")
        return None
    finally:
        if resource:
            self._release_resource(resource)
```

### 4.3 参数校验模式

#### 输入验证
```python
def process(self, inputs=None):
    """处理节点逻辑"""
    try:
        # Step 1: 参数校验
        if not inputs or len(inputs) == 0 or inputs[0] is None:
            self.log_warning("未接收到输入图像")
            return {'输出图像': None}
        
        image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
        
        if image is None or not isinstance(image, np.ndarray):
            self.log_error("输入图像格式错误")
            return {'输出图像': None}
        
        # Step 2: 业务逻辑
        result = self._transform(image)
        
        # Step 3: 返回结果
        return {'输出图像': result}
        
    except Exception as e:
        self.log_error(f"处理错误: {e}")
        return {'输出图像': None}
```

#### 类型检查
```python
def validate_input(self, data) -> bool:
    """验证输入数据类型"""
    if not isinstance(data, dict):
        logger.error("输入必须是字典类型")
        return False
    
    required_keys = ['width', 'height', 'data']
    for key in required_keys:
        if key not in data:
            logger.error(f"缺少必需字段: {key}")
            return False
    
    return True
```

### 4.4 日志使用规范

#### 日志级别选择
```python
from utils.logger import logger

# INFO: 正常流程的关键信息
logger.info("应用启动成功", module="main")
logger.info("插件加载完成", module="plugin_manager")

# SUCCESS: 重要操作完成
logger.success("工作流保存成功", module="project_manager")
logger.success("节点图执行完成", module="execution_ui")

# WARNING: 警告但不影响运行
logger.warning("配置文件不存在，使用默认配置", module="config")
logger.warning("未接收到输入图像", module="node_processor")

# ERROR: 错误导致操作失败
logger.error("保存文件失败", module="file_io")
logger.error("节点执行错误", module="graph_engine")

# DEBUG: 调试信息（仅DEBUG模式输出）
logger.debug("详细参数: width=1920, height=1080", module="image_loader")
```

#### 模块化日志
```python
# 始终指定module参数，便于过滤
logger.info("消息内容", module="plugin_loader")
logger.error("错误信息", module="ui_manager")
```

### 4.5 装饰器使用

#### 性能监控装饰器
```python
class YOLODetectNode(BaseNode):
    @BaseNode.measure_performance("yolo_detect")
    def process(self, inputs):
        """带性能监控的处理方法"""
        # 自动记录执行时间
        pass
```

---

## 5. 标准代码示例

### 5.1 Entity层示例

```python
"""
工作流数据模型

定义工作流的数据结构和基本操作方法。
"""

import uuid
from datetime import datetime
from typing import Optional


class Workflow:
    """
    工作流实体类
    
    表示一个独立的节点图和执行流程。
    
    Attributes:
        id: 工作流唯一标识符
        name: 工作流名称
        description: 工作流描述
        created_time: 创建时间
        modified_time: 最后修改时间
    """
    
    def __init__(self, name: str = "新工作流"):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
        """
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = ""
        self.created_time = datetime.now().isoformat()
        self.modified_time = self.created_time
        self.is_modified = False
    
    def mark_modified(self):
        """标记为已修改"""
        self.is_modified = True
        self.modified_time = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_time': self.created_time,
            'modified_time': self.modified_time
        }
    
    def from_dict(self, data: dict):
        """从字典加载"""
        self.id = data.get('id', self.id)
        self.name = data.get('name', self.name)
        self.description = data.get('description', '')
        self.created_time = data.get('created_time', self.created_time)
        self.modified_time = data.get('modified_time', self.modified_time)
```

### 5.2 DAO层示例

```python
"""
工作流数据访问对象

负责工作流的持久化操作。
"""

import json
from pathlib import Path
from typing import Optional
from utils.logger import logger


class WorkflowDAO:
    """工作流数据访问对象"""
    
    @staticmethod
    def save(workflow, file_path: str) -> bool:
        """
        保存工作流到文件
        
        Args:
            workflow: Workflow实例
            file_path: 文件路径
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            # 参数校验
            if not workflow:
                logger.error("工作流对象为空")
                return False
            
            if not file_path:
                logger.error("文件路径为空")
                return False
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 序列化并保存
            data = workflow.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.success(f"工作流已保存: {file_path}", module="workflow_dao")
            return True
            
        except PermissionError:
            logger.error(f"权限不足，无法写入: {file_path}", module="workflow_dao")
            return False
            
        except Exception as e:
            logger.error(f"保存失败: {e}", module="workflow_dao")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def load(file_path: str, workflow_class) -> Optional:
        """
        从文件加载工作流
        
        Args:
            file_path: 文件路径
            workflow_class: Workflow类
            
        Returns:
            Workflow实例或None
        """
        try:
            # 参数校验
            if not file_path or not Path(file_path).exists():
                logger.error(f"文件不存在: {file_path}", module="workflow_dao")
                return None
            
            # 读取并反序列化
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建实例
            workflow = workflow_class()
            workflow.from_dict(data)
            workflow.file_path = file_path
            
            logger.info(f"工作流已加载: {file_path}", module="workflow_dao")
            return workflow
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON格式错误: {e}", module="workflow_dao")
            return None
            
        except Exception as e:
            logger.error(f"加载失败: {e}", module="workflow_dao")
            return None
```

### 5.3 Service层示例

```python
"""
图执行引擎

负责节点图的执行逻辑。
"""

from collections import defaultdict, deque
from utils.logger import logger


class GraphEngine:
    """
    图执行引擎
    
    职责：
    - 分析节点依赖关系
    - 执行拓扑排序
    - 按顺序执行节点
    """
    
    def __init__(self):
        """初始化引擎"""
        self.graph = None
        self.node_outputs = {}
    
    def execute_graph(self, graph) -> dict:
        """
        执行整个节点图
        
        Args:
            graph: NodeGraph实例
            
        Returns:
            dict: 节点输出结果
            
        Raises:
            ValueError: 检测到循环依赖
        """
        try:
            # Step 1: 初始化
            self.graph = graph
            self.node_outputs.clear()
            all_nodes = graph.all_nodes()
            
            if not all_nodes:
                logger.warning("节点图为空", module="graph_engine")
                return {}
            
            # Step 2: 构建依赖关系
            dependencies = self._build_dependency_graph(all_nodes)
            
            # Step 3: 拓扑排序
            ordered_nodes = self._topological_sort(dependencies, all_nodes)
            
            # Step 4: 执行节点
            for node in ordered_nodes:
                self._execute_node(node)
            
            logger.success(f"节点图执行完成，共{len(ordered_nodes)}个节点", 
                          module="graph_engine")
            return self.node_outputs
            
        except ValueError as e:
            logger.error(f"依赖错误: {e}", module="graph_engine")
            raise
            
        except Exception as e:
            logger.error(f"执行失败: {e}", module="graph_engine")
            import traceback
            traceback.print_exc()
            raise
    
    def _build_dependency_graph(self, all_nodes) -> dict:
        """构建依赖关系图"""
        dependencies = defaultdict(list)
        
        for node in all_nodes:
            for input_port in node.input_ports():
                connected_ports = input_port.connected_ports()
                for connected_port in connected_ports:
                    source_node = connected_port.node()
                    dependencies[node].append(source_node)
        
        return dependencies
    
    def _topological_sort(self, dependencies: dict, all_nodes: list) -> list:
        """
        拓扑排序
        
        Raises:
            ValueError: 存在循环依赖
        """
        in_degree = {node: 0 for node in all_nodes}
        
        for node in all_nodes:
            for dep_node in dependencies[node]:
                in_degree[node] += 1
        
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
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
    
    def _execute_node(self, node):
        """执行单个节点"""
        try:
            inputs = self._get_node_inputs(node)
            outputs = node.process(inputs)
            
            if outputs:
                self.node_outputs[node.id] = outputs
                
        except Exception as e:
            logger.error(f"节点执行失败 [{node.NODE_NAME}]: {e}", 
                        module="graph_engine")
            raise
```

### 5.4 Controller层示例

```python
"""
执行UI管理器

处理与节点图执行相关的UI交互。
"""

from PySide2 import QtWidgets
from utils.logger import logger


class ExecutionUIManager:
    """
    执行UI管理器
    
    职责：
    - 响应用户执行请求
    - 调用引擎执行业务逻辑
    - 显示执行结果和错误提示
    """
    
    def __init__(self, graph_engine, main_window):
        """
        初始化
        
        Args:
            graph_engine: GraphEngine实例（Service层）
            main_window: MainWindow实例（View层）
        """
        self.graph_engine = graph_engine
        self.main_window = main_window
    
    def run_current_graph(self):
        """执行当前工作流（UI触发）"""
        # Step 1: 前置校验
        if not self.main_window.current_node_graph:
            QtWidgets.QMessageBox.warning(
                self.main_window, 
                "警告", 
                "没有激活的工作流"
            )
            return
        
        logger.info("=" * 50, module="execution_ui")
        logger.info("开始执行节点图...", module="execution_ui")
        
        # Step 2: 调用Service层执行
        try:
            results = self.graph_engine.execute_graph(
                self.main_window.current_node_graph
            )
            
            # Step 3: 处理结果
            logger.success("节点图执行完成!", module="execution_ui")
            
            if results:
                logger.info(
                    f"处理了 {len(results)} 个节点的输出", 
                    module="execution_ui"
                )
            
            # Step 4: 更新UI
            self.refresh_all_previews()
            
        except Exception as e:
            logger.error(f"执行错误: {e}", module="execution_ui")
            import traceback
            traceback.print_exc()
            
            # 显示错误对话框
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "执行错误",
                f"执行节点图时发生错误:\n{str(e)}"
            )
    
    def refresh_all_previews(self):
        """刷新所有预览窗口"""
        # UI更新逻辑
        pass
```

### 5.5 节点实现示例（业务逻辑）

```python
"""
灰度化节点 - 将彩色图像转换为灰度图像
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class GrayscaleNode(BaseNode):
    """
    灰度化节点
    
    将彩色图像转换为灰度图像。
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '灰度化'
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含输出图像的字典
        """
        try:
            # Step 1: 参数校验
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            # Step 2: 业务逻辑
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # Step 3: 返回结果
            self.log_success("灰度化完成")
            return {'输出图像': gray_bgr}
            
        except Exception as e:
            self.log_error(f"灰度化处理错误: {e}")
            return {'输出图像': None}
```

---

## 6. 最佳实践

### 6.1 设计原则

1. **单一职责**: 每个类/方法只负责一项功能
2. **开闭原则**: 对扩展开放，对修改关闭
3. **依赖倒置**: 依赖抽象，不依赖具体实现
4. **接口隔离**: 使用细粒度接口

### 6.2 代码质量

1. **DRY (Don't Repeat Yourself)**: 避免重复代码
2. **KISS (Keep It Simple, Stupid)**: 保持简单
3. **YAGNI (You Aren't Gonna Need It)**: 不要过度设计

### 6.3 性能优化

1. 避免在循环中进行I/O操作
2. 使用缓存减少重复计算
3. 及时释放不再使用的资源
4. 异步处理耗时操作

### 6.4 安全性

1. 所有外部输入必须校验
2. 敏感信息不得硬编码
3. 文件操作需检查权限
4. 异常信息不得泄露敏感数据

---

## 7. 检查清单

提交代码前请确认：

- [ ] 遵循命名规范
- [ ] 添加必要的文档字符串
- [ ] 正确处理异常
- [ ] 进行参数校验
- [ ] 使用统一的日志系统
- [ ] 无硬编码的配置
- [ ] 代码通过静态检查
- [ ] 单元测试通过
- [ ] 无冗余代码和注释

---

**版本**: v1.0  
**最后更新**: 2026-05-05  
**维护者**: 项目开发团队
