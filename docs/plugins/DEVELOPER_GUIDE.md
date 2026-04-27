# 统一插件体系开发指南

## 📋 概述

本指南介绍如何在新的统一插件体系架构下开发和管理插件。

## 🏗️ 架构概览

### 三层插件目录结构
```
plugin_packages/
├── builtin/                ← 预置节点（随应用发布）
├── marketplace/            ← 市场插件（动态加载）
└── user_custom/            ← 用户自定义（git忽略）
```

### 共享库目录
```
shared_libs/
├── ai_base/                ← AI节点基类
├── common_utils/           ← 通用工具
└── cpp_wrappers/           ← C++封装层
```

## 🚀 快速开始

### 1. 创建新插件包

#### Python源码插件
```bash
# 在user_custom目录下创建新插件
mkdir -p src/python/plugin_packages/user_custom/my_plugin
cd src/python/plugin_packages/user_custom/my_plugin

# 创建必要文件
touch plugin.json nodes.py README.md
```

#### plugin.json模板
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "My custom plugin",
  "category_group": "自定义",
  "nodes": [
    {
      "class": "MyNode",
      "display_name": "我的节点",
      "category": "自定义处理",
      "color": [200, 200, 200]
    }
  ],
  "dependencies": ["numpy>=1.20"],
  "min_app_version": "4.0.0"
}
```

#### nodes.py模板
```python
"""
我的自定义插件
"""

from NodeGraphQt import BaseNode


class MyNode(BaseNode):
    """
    我的自定义节点
    
    功能描述...
    """
    
    __identifier__ = 'my_plugin'
    NODE_NAME = '我的节点'
    
    def __init__(self):
        super(MyNode, self).__init__()
        # 添加输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 添加输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 添加参数控件
        self.add_text_input('param1', '参数1', tab='properties')
    
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                # 你的处理逻辑
                result = image
                return {'输出图像': result}
            except Exception as e:
                print(f"处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
```

### 2. 测试插件

1. **重启应用**以加载新插件
2. **检查节点库**是否显示新节点
3. **创建工作流**测试节点功能

## 📦 插件类型

### Python源码插件
- **适用场景**: 预置节点、用户自定义
- **加载方式**: 动态import
- **优点**: 易于开发和调试
- **缺点**: 性能相对较低

### ZIP打包插件
- **适用场景**: 市场分发、离线安装
- **加载方式**: 解压后按Python加载
- **优点**: 便于分发和版本管理
- **缺点**: 需要解压步骤

### 二进制插件 (DLL/SO)
- **适用场景**: 高性能算法、商业插件
- **加载方式**: ctypes/cffi加载
- **优点**: 性能优异，可保护源码
- **缺点**: 开发复杂，跨平台兼容性差

## 🔧 高级功能

### 使用共享库

#### 导入AI基类
```python
from shared_libs.ai_base import AIBaseNode

class MyAINode(AIBaseNode):
    __identifier__ = 'my_ai_plugin'
    NODE_NAME = 'AI节点'
    
    def __init__(self):
        super().__init__()
        # AI节点特有的初始化
```

#### 使用性能监控
```python
from shared_libs.ai_base import PerformanceMonitor

monitor = PerformanceMonitor()

@monitor.measure_time("my_function")
def my_function():
    # 你的代码
    pass
```

### 依赖管理

#### 声明依赖
```json
{
  "dependencies": [
    "opencv-python>=4.5",
    "numpy>=1.20",
    "@builtin/shared_libs.ai_base>=1.0"
  ]
}
```

#### 内部依赖引用
- `@builtin/`: 引用预置插件
- `@marketplace/`: 引用市场插件
- `@shared_libs/`: 引用共享库

## 🛠️ 插件管理

### 节点操作

#### 移动节点到不同包
1. 在节点编辑器中选择节点
2. 右键 → "移动到..." → 选择目标包
3. **重启应用**生效

#### 重命名节点包
1. 在节点包列表中右键
2. 选择"重命名节点包"
3. 输入新名称
4. **重启应用**生效

### 插件排序
1. 点击工具栏"🔀 管理标签顺序"
2. 拖拽调整顺序
3. 保存配置

## ⚠️ 注意事项

### 安全限制
- 禁止导入os/subprocess/socket/requests等模块
- 禁止调用eval/exec/open('w')
- 文件系统访问受限

### 命名规范
- 插件目录名必须与plugin.json中的name字段一致
- 使用小写字母和下划线
- 避免使用特殊字符

### 热重载
- 文件保存后0.5秒触发重载
- 仅支持Python源码插件
- 二进制插件需重启

### 分类更新
- 新增分类需重启程序才能在UI中完全显示
- 修改category_group后必须重启

## 📚 相关文档

- [PLUGIN_ARCHITECTURE.md](PLUGIN_ARCHITECTURE.md) - 架构设计规范
- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) - 迁移计划
- [NODE_DEVELOPMENT_GUIDE.md](NODE_DEVELOPMENT_GUIDE.md) - 节点开发指南
- [NODE_API_REFERENCE.md](NODE_API_REFERENCE.md) - API参考手册

## 🆘 常见问题

### Q: 插件加载失败怎么办？
A: 检查控制台错误信息，确认plugin.json格式正确，节点类存在。

### Q: 节点库不显示新节点？
A: 确认节点已注册到正确的Graph实例，重启应用。

### Q: 如何调试插件？
A: 在节点代码中添加print语句，查看控制台输出。

### Q: 二进制插件如何开发？
A: 参考cpp_wrappers目录下的示例，实现标准C接口。