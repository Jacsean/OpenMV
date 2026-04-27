# 插件迁移教程

> **文档说明**: 本教程详细介绍如何将旧体系插件（单文件 `nodes.py`）迁移到新体系（目录结构 `nodes/`）。

---

## 📋 目录

- [1. 迁移概述](#1-迁移概述)
- [2. 迁移前准备](#2-迁移前准备)
- [3. 迁移步骤详解](#3-迁移步骤详解)
- [4. 自动化迁移工具](#4-自动化迁移工具)
- [5. 迁移验证](#5-迁移验证)
- [6. 常见问题](#6-常见问题)
- [7. 迁移案例](#7-迁移案例)

---

## 1. 迁移概述

### 1.1 为什么要迁移？

**旧体系问题**：
- ❌ 所有节点在一个文件中，难以维护
- ❌ 无法按功能分组
- ❌ 导入路径混乱
- ❌ 不支持子模块

**新体系优势**：
- ✅ 每个节点独立文件，易于维护
- ✅ 支持子目录分组（inference/training/annotation）
- ✅ 清晰的导入结构
- ✅ 便于扩展和协作

### 1.2 迁移前后对比

**旧体系**：
```
my_plugin/
├── plugin.json
└── nodes.py          # 包含所有节点类（可能上千行）
```

**新体系**：
```
my_plugin/
├── __init__.py       # 新增：插件入口
├── plugin.json       # 保持不变
└── nodes/            # 新增：节点目录
    ├── __init__.py   # 导出所有节点
    ├── node1.py      # 节点 1
    ├── node2.py      # 节点 2
    └── subfolder/    # 可选：子目录
        ├── __init__.py
        └── node3.py
```

### 1.3 迁移影响评估

| 项目 | 影响 | 说明 |
|------|------|------|
| **节点功能** | ✅ 无影响 | 节点逻辑完全不变 |
| **工作流文件** | ✅ 兼容 | 现有工作流可正常加载 |
| **plugin.json** | ✅ 无需修改 | 配置保持不变 |
| **节点标识符** | ✅ 保持不变 | `__identifier__` 不变 |
| **节点名称** | ✅ 保持不变 | `NODE_NAME` 不变 |

---

## 2. 迁移前准备

### 2.1 备份原插件

```bash
# 备份整个插件目录
cp -r my_plugin my_plugin_backup
```

### 2.2 检查节点数量

```python
# 查看 nodes.py 中有多少个节点类
import ast

with open('my_plugin/nodes.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
print(f"节点数量: {len(classes)}")
print(f"节点列表: {classes}")
```

### 2.3 确认依赖关系

检查节点之间是否有相互调用：

```bash
# 搜索节点间的引用
grep -n "from.*nodes import" my_plugin/nodes.py
grep -n "import.*Node" my_plugin/nodes.py
```

如果有相互依赖，需要在迁移时注意导入顺序。

---

## 3. 迁移步骤详解

### 步骤 1：创建目录结构

```bash
cd my_plugin
mkdir nodes
```

### 步骤 2：拆分节点文件

对于每个节点类，创建独立的 Python 文件：

**示例**：将 `GrayscaleNode` 提取到 `nodes/grayscale.py`

**原代码**（nodes.py）：
```python
class GrayscaleNode(BaseNode):
    __identifier__ = 'preprocessing'
    NODE_NAME = '灰度化'
    
    def __init__(self):
        super().__init__()
        self.add_input('输入图像')
        self.add_output('输出图像')
    
    def process(self, inputs=None):
        # ... 处理逻辑
        return {'输出图像': result}
```

**新文件**（nodes/grayscale.py）：
```python
"""
灰度化节点

功能：将彩色图像转换为灰度图像
"""

from ....base_nodes import BaseNode  # 注意：保持原有的导入层级
import cv2


class GrayscaleNode(BaseNode):
    """灰度化节点"""
    
    __identifier__ = 'preprocessing'
    NODE_NAME = '灰度化'
    
    def __init__(self):
        super(GrayscaleNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
    
    def process(self, inputs=None):
        """处理逻辑"""
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 执行灰度化
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            return {'输出图像': gray_bgr}
        
        except Exception as e:
            print(f"灰度化处理错误: {e}")
            return {'输出图像': None}
```

**关键点**：
1. ✅ 添加文档字符串
2. ✅ 保持导入路径不变（`....base_nodes`）
3. ✅ 保留完整的类定义
4. ✅ 添加错误处理

### 步骤 3：创建 nodes/__init__.py

```python
"""
预处理节点包
"""

from .grayscale import GrayscaleNode
from .gaussian_blur import GaussianBlurNode
from .median_blur import MedianBlurNode
# ... 导入所有节点

__all__ = [
    'GrayscaleNode',
    'GaussianBlurNode',
    'MedianBlurNode',
    # ... 所有节点类名
]
```

**注意**：
- 必须导出所有在 `plugin.json` 中声明的节点类
- 使用 `__all__` 明确指定导出的类

### 步骤 4：创建插件根目录的 __init__.py

```python
"""
预处理插件包 - 图像预处理节点集合
"""

from .nodes import *
```

### 步骤 5：删除旧的 nodes.py

```bash
rm nodes.py
```

**重要**：删除前确保新结构已正确创建并测试通过。

### 步骤 6：验证迁移

运行验证脚本：

```bash
python tests/verify_all_plugins_migration.py
```

预期输出：
```
✅ 通过: my_plugin
   • JSON结构: ✅ 结构完整 (N 个节点)
   • 目录结构: ✅ 目录结构正确
   • 节点类导入: ✅ 所有节点类已声明 (N 个)
```

---

## 4. 自动化迁移工具

### 4.1 使用 migrate_plugins.py

项目提供了自动化迁移脚本：

```bash
python tools/migrate_plugins.py --plugin my_plugin
```

**功能**：
- ✅ 自动检测节点类
- ✅ 自动创建目录结构
- ✅ 自动生成节点文件
- ✅ 自动更新 __init__.py

### 4.2 手动迁移脚本

如果自动化工具不适用，可以使用以下脚本辅助：

```python
"""
手动迁移辅助脚本
"""

import ast
import os
from pathlib import Path


def extract_classes(nodes_py_path):
    """从 nodes.py 中提取所有节点类"""
    with open(nodes_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # 获取类的源代码
            start_line = node.lineno - 1
            end_line = node.end_lineno
            
            lines = content.split('\n')[start_line:end_line]
            class_code = '\n'.join(lines)
            
            classes.append({
                'name': node.name,
                'code': class_code,
                'line': node.lineno
            })
    
    return classes


def create_node_file(class_info, output_dir):
    """创建单个节点文件"""
    filename = f"{class_info['name'].lower()}.py"
    filepath = output_dir / filename
    
    # 添加头部注释和导入
    header = f'''"""
{class_info['name']} 节点

自动生成于迁移过程
"""

# TODO: 检查并修正导入路径
from ....base_nodes import BaseNode
import cv2
import numpy as np


'''
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(class_info['code'])
    
    print(f"✅ 创建: {filepath}")


def generate_init_py(classes, output_dir):
    """生成 __init__.py"""
    init_path = output_dir / "__init__.py"
    
    imports = []
    all_list = []
    
    for cls in classes:
        module_name = cls['name'].lower()
        imports.append(f"from .{module_name} import {cls['name']}")
        all_list.append(f"'{cls['name']}'")
    
    content = f'''"""
节点模块
"""

{chr(10).join(imports)}

__all__ = [{', '.join(all_list)}]
'''
    
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 创建: {init_path}")


if __name__ == "__main__":
    # 配置
    plugin_dir = Path("my_plugin")
    nodes_py = plugin_dir / "nodes.py"
    nodes_dir = plugin_dir / "nodes"
    
    # 创建目录
    nodes_dir.mkdir(exist_ok=True)
    
    # 提取类
    classes = extract_classes(nodes_py)
    print(f"找到 {len(classes)} 个节点类")
    
    # 创建节点文件
    for cls in classes:
        create_node_file(cls, nodes_dir)
    
    # 生成 __init__.py
    generate_init_py(classes, nodes_dir)
    
    print("\n✅ 迁移完成！请手动检查和修正导入路径")
```

---

## 5. 迁移验证

### 5.1 结构验证

```bash
# 检查目录结构
tree my_plugin/
```

预期输出：
```
my_plugin/
├── __init__.py
├── plugin.json
└── nodes/
    ├── __init__.py
    ├── node1.py
    ├── node2.py
    └── ...
```

### 5.2 语法验证

```bash
# 检查 Python 语法
python -m py_compile my_plugin/nodes/*.py
```

### 5.3 导入验证

```python
# 测试导入
import sys
sys.path.insert(0, 'src/python')

try:
    from user_plugins.my_plugin import *
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
```

### 5.4 功能验证

1. **重启应用程序**
2. **检查控制台日志**：
   ```
   ✅ 安全检查通过: my_plugin
   ✅ 模块加载成功: my_plugin
   ✅ 注册节点: 节点1
   ✅ 注册节点: 节点2
   ...
   ```
3. **打开现有工作流**：确认节点能正常加载和执行

---

## 6. 常见问题

### Q1: 导入路径错误怎么办？

**错误示例**：
```
ModuleNotFoundError: No module named 'user_plugins'
```

**解决方案**：
检查相对导入的层级数：

```python
# 如果节点文件在: my_plugin/nodes/node1.py
# base_nodes 在: user_plugins/base_nodes.py

# 需要向上 3 层：nodes -> my_plugin -> user_plugins
from ...base_nodes import BaseNode  # 3个点

# 如果需要向上 4 层（如嵌套子目录）
from ....base_nodes import BaseNode  # 4个点
```

**计算方法**：
```
当前文件位置: my_plugin/nodes/subfolder/node.py
目标文件位置: user_plugins/base_nodes.py

路径: subfolder -> nodes -> my_plugin -> user_plugins
层级数: 4 个点 (....)
```

### Q2: 节点类找不到怎么办？

**错误**：
```
❌ 未找到节点类: MyNode
```

**解决方案**：
1. 检查 `nodes/__init__.py` 是否导出了该类
2. 检查类名是否与 `plugin.json` 中一致
3. 检查是否有拼写错误

```python
# nodes/__init__.py
from .mynode import MyNode  # 确保类名正确

__all__ = ['MyNode']  # 确保在 __all__ 中
```

### Q3: 迁移后工作流打不开？

**可能原因**：
1. 节点标识符改变（不应该改变）
2. 节点名称改变（不应该改变）
3. 端口名称改变（不应该改变）

**解决方案**：
检查节点的以下属性是否保持不变：

```python
class MyNode(BaseNode):
    __identifier__ = 'my_plugin'  # ✅ 必须保持不变
    NODE_NAME = '我的节点'         # ✅ 必须保持不变
    
    def __init__(self):
        self.add_input('输入图像')  # ✅ 端口名称必须保持不变
        self.add_output('输出图像') # ✅ 端口名称必须保持不变
```

### Q4: 如何处理节点间的依赖？

如果节点 A 调用了节点 B 的方法：

**方案 1**：将共享代码提取到工具模块

```
my_plugin/
├── nodes/
│   ├── utils.py      # 共享工具函数
│   ├── node_a.py
│   └── node_b.py
```

```python
# nodes/utils.py
def shared_function():
    pass

# nodes/node_a.py
from .utils import shared_function

# nodes/node_b.py
from .utils import shared_function
```

**方案 2**：在 `__init__.py` 中处理循环导入

```python
# nodes/__init__.py
from . import node_a
from . import node_b

# 延迟导入
def get_node_b():
    from .node_b import NodeB
    return NodeB
```

---

## 7. 迁移案例

### 案例 1: preprocessing 插件（8个节点）

**迁移前**：
```
preprocessing/
├── plugin.json
└── nodes.py  (500+ 行)
```

**迁移后**：
```
preprocessing/
├── __init__.py
├── plugin.json
└── nodes/
    ├── __init__.py
    ├── grayscale.py
    ├── gaussian_blur.py
    ├── median_blur.py
    ├── bilateral_filter.py
    ├── resize.py
    ├── rotate.py
    ├── brightness_contrast.py
    └── threshold.py
```

**耗时**：约 2 小时  
**难点**：无（节点间无依赖）

### 案例 2: yolo_vision 插件（7个节点，含子目录）

**迁移前**：
```
yolo_vision/
├── plugin.json
└── nodes.py  (1000+ 行)
```

**迁移后**：
```
yolo_vision/
├── __init__.py
├── plugin.json
└── nodes/
    ├── __init__.py
    ├── inference/
    │   ├── __init__.py
    │   ├── yolo_detect.py
    │   ├── yolo_classify.py
    │   ├── yolo_segment.py
    │   └── yolo_pose.py
    ├── training/
    │   ├── __init__.py
    │   ├── yolo_trainer.py
    │   └── yolo_quantizer.py
    └── annotation/
        ├── __init__.py
        └── yolo_annotator.py
```

**耗时**：约 3 小时  
**难点**：
1. 需要按功能分组到子目录
2. 导入路径层级较深（`....base_nodes`）
3. 需要更新多处 `__init__.py`

### 案例 3: match_location 插件（修复类缺失）

**问题**：`nodes.py` 为空，但 `plugin.json` 定义了 3 个节点

**解决方案**：
1. 根据 `plugin.json` 中的节点定义，重新实现节点类
2. 修复重复的类名问题
3. 创建完整的目录结构

**耗时**：约 1.5 小时  
**难点**：需要从零实现节点逻辑

---

## 📚 相关文档

- [统一节点开发指南](UNIFIED_NODE_DEVELOPMENT_GUIDE.md)
- [插件系统架构文档](../ARCHITECTURE_EVOLUTION.md)

---

**最后更新**: 2026-04-27  
**维护者**: StduyOpenCV 开发团队
